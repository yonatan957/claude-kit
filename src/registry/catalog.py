"""Loads registry.json (what exists) and installed.json (what this machine chose).

Constitution III (Types Are Data, Not Code): the set of component types is whatever
`registry["types"]` declares — nothing here hardcodes a type name.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.core.models import Component, ComponentState, ComponentType


class CatalogError(Exception):
    pass


def load_registry(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_installed(path: Path) -> dict:
    if not Path(path).exists():
        return {"schema_version": 2}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def list_component_types(registry: dict) -> list[ComponentType]:
    return [ComponentType(name=t["name"], handler=t["handler"]) for t in registry.get("types", [])]


def component_type_names(registry: dict) -> set[str]:
    return {t.name for t in list_component_types(registry)}


def _component_state(type_name: str, name: str, installed: dict) -> ComponentState:
    entry = installed.get(type_name, {}).get(name)
    if entry is None:
        return ComponentState.NOT_INSTALLED
    config = entry.get("config")
    if config is None:
        return ComponentState.INSTALLED
    status = config.get("status")
    if status == "pending":
        return ComponentState.PENDING_CONFIGURATION
    if status == "done":
        return ComponentState.CONFIGURED
    return ComponentState.INSTALLED


def list_components(registry: dict, installed: dict, type_name: str | None = None) -> list[Component]:
    """All catalog components, in their current (non-transient) state.

    PENDING_INSTALL/PENDING_REMOVAL are not computed here — they only exist as the
    result of diffing against a user's in-progress selections (see core.plan).
    """
    valid_types = component_type_names(registry)
    if type_name is not None and type_name not in valid_types:
        raise CatalogError(
            f"Unknown component type '{type_name}'. Known types: {', '.join(sorted(valid_types))}"
        )

    types_to_scan = [type_name] if type_name is not None else sorted(valid_types)
    components: list[Component] = []
    for t in types_to_scan:
        for name, meta in registry.get(t, {}).items():
            components.append(
                Component(
                    type=t,
                    name=name,
                    description=meta.get("description", ""),
                    category=meta.get("category"),
                    recommended=bool(meta.get("recommended", False)),
                    version=meta.get("version"),
                    state=_component_state(t, name, installed),
                )
            )
    return components


def has_managed_components(installed: dict) -> bool:
    """True iff installed.json contains at least one claude-kit-managed component."""
    for type_name, entries in installed.items():
        if type_name in ("schema_version", "version", "min_cli_version", "hash_algo"):
            continue
        if not isinstance(entries, dict):
            continue
        for meta in entries.values():
            if isinstance(meta, dict) and meta.get("source") == "claude-kit":
                return True
    return False


def search_components(
    query: str,
    registry: dict,
    installed: dict,
    skill_sources: list[dict] | None = None,
    search_runner=None,
) -> list[Component]:
    """Catalog matches (origin="catalog") plus, for each enabled skill_source, its
    declared search command's matches (origin=<source name>). See research.md §3.
    """
    query_lower = query.lower()
    results = [
        Component(
            type=c.type,
            name=c.name,
            description=c.description,
            category=c.category,
            recommended=c.recommended,
            version=c.version,
            state=c.state,
            origin="catalog",
        )
        for c in list_components(registry, installed)
        if query_lower in c.name.lower() or query_lower in c.description.lower()
    ]

    if skill_sources and search_runner is not None:
        for source in skill_sources:
            if not source.get("enabled", False):
                continue
            for hit in search_runner(source, query):
                results.append(
                    Component(
                        type="skills",
                        name=hit["name"],
                        description=hit.get("description", ""),
                        category=hit.get("category"),
                        recommended=False,
                        version=hit.get("version"),
                        state=ComponentState.NOT_INSTALLED,
                        origin=source["name"],
                    )
                )
    return results
