"""Diff computation — desired selection vs. installed.json → add/remove/update plan.

Pure functions only — no I/O (Principle I).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from src.core.state_model import CategoryName, Component, InstalledRecord, Registry

_CATEGORIES: tuple[CategoryName, ...] = ("skills", "agents", "plugins", "tools", "mcps")
_CONTENT_CATEGORIES = ("skills", "agents")


def content_hash(component: Component) -> str:
    """Deterministic combined hash of a content-handler component's declared
    files. Used both to record `installed_hash` at install time (installers/
    content.py) and to detect drift against the latest catalog content here."""
    joined = "\n".join(f"{f.path}:{f.hash}" for f in sorted(component.files, key=lambda f: f.path))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PlanItem:
    category: CategoryName
    name: str
    component: Component


@dataclass
class DiffPlan:
    to_add: list[PlanItem] = field(default_factory=list)
    to_remove: list[PlanItem] = field(default_factory=list)
    to_update: list[PlanItem] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.to_add or self.to_remove or self.to_update)


def _installed_names(installed: InstalledRecord, category: CategoryName) -> set[str]:
    return set(getattr(installed, category).keys())


def compute_selection_diff(
    registry: Registry,
    installed: InstalledRecord,
    desired: dict[CategoryName, set[str]],
) -> DiffPlan:
    """Diff a developer's desired selection (e.g. from the picker) against
    installed.json, for a `config`/`add`/`remove` apply pass."""
    plan = DiffPlan()
    components_by_category = registry.components_by_category()

    for category in _CATEGORIES:
        desired_names = desired.get(category, set())
        currently_installed = _installed_names(installed, category)
        components = components_by_category[category]

        for name in sorted(desired_names - currently_installed):
            plan.to_add.append(PlanItem(category=category, name=name, component=components[name]))

        for name in sorted(currently_installed - desired_names):
            component = components.get(name)
            if component is None:
                continue
            plan.to_remove.append(PlanItem(category=category, name=name, component=component))

    return plan


def _is_outdated(category: CategoryName, entry: object, component: Component) -> bool:
    if category in _CONTENT_CATEGORIES:
        return entry.installed_hash != content_hash(component)
    return entry.version != component.version


def compute_refresh_plan(registry: Registry, installed: InstalledRecord) -> DiffPlan:
    """Diff every currently-installed component against the latest catalog
    content, for `update`'s refresh-in-place pass. Never produces additions or
    removals — those only ever happen through a deliberate developer selection
    via `config`/`add`/`remove`."""
    plan = DiffPlan()
    components_by_category = registry.components_by_category()

    for category in _CATEGORIES:
        components = components_by_category[category]
        entries = getattr(installed, category)
        for name in sorted(entries.keys()):
            component = components.get(name)
            if component is None:
                # No longer present in the catalog; leave it installed as-is.
                continue
            if _is_outdated(category, entries[name], component):
                plan.to_update.append(PlanItem(category=category, name=name, component=component))

    return plan
