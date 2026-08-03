"""Pure findings -> message rendering (data-model.md's Notification Snapshot
section). No I/O (Principle I) — commands/check_cmd.py and notify/hook.py own
reading/writing state.json.
"""

from __future__ import annotations

from src.core.state_model import Findings


def _finding_identifiers(findings: Findings) -> list[tuple[str, str]]:
    """Every individual finding as (identifier, human-readable line), in a
    stable order, so callers can diff each one against `announced`."""
    items: list[tuple[str, str]] = []
    if findings.latest_cli_version and findings.latest_cli_version != findings.local_cli_version:
        items.append(
            (
                f"cli:{findings.latest_cli_version}",
                f"claude-kit {findings.latest_cli_version} is available "
                f"(you have {findings.local_cli_version})",
            )
        )
    if findings.remote_commit and findings.remote_commit != findings.local_commit:
        items.append(
            (
                f"catalog:{findings.remote_commit}",
                "A newer catalog is available — run `claude-kit update`",
            )
        )
    if findings.pending_config_count > 0:
        items.append(
            (
                f"pending:{findings.pending_config_count}",
                f"{findings.pending_config_count} component(s) awaiting configuration",
            )
        )
    return items


def render_notice(findings: Findings, announced: list[str]) -> tuple[str | None, list[str]]:
    """Renders a single pre-rendered notice string from `findings`, skipping
    any finding identifier already present in `announced` (FR-032/SC-009).

    Returns `(message, updated_announced)`: `message` is `None` when there is
    nothing new to show; `updated_announced` includes every currently-true
    finding's identifier (so the hook's "is there a message?" check needs no
    comparison logic of its own — Principle V).
    """
    already = set(announced)
    all_items = _finding_identifiers(findings)
    new_items = [(identifier, line) for identifier, line in all_items if identifier not in already]

    updated_announced = list(announced) + [identifier for identifier, _ in new_items]

    if not new_items:
        return None, list(announced)

    message = "claude-kit: " + "; ".join(line for _, line in new_items)
    return message, updated_announced
