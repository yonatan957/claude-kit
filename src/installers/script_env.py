"""Persisting and recovering a component's declared answers (research.md #7).

*Every* declared answer is stored, not just `secret: true` ones — `installed.json`
can only ever hold the `"<set>"` placeholder (FR-039), so this restricted file is
the only place `update` can recover an input's real value and re-run `config.sh`
without re-prompting (FR-023).

Keyed by the input's own declared name rather than the derived env var name, so
values read back unambiguously.
"""

from __future__ import annotations

from pathlib import Path

from src.core.state_model import Component
from src.installers.secrets import read_secret_file, write_secret_file


def persist_answers(
    name: str, component: Component, answers: dict[str, str], env_dir: Path
) -> None:
    if not component.inputs:
        return
    contents = "\n".join(
        f"{declared.name}={answers[declared.name]}"
        for declared in component.inputs
        if declared.name in answers
    )
    write_secret_file(env_dir / f"{name}.env", contents + "\n")


def load_stored_answers(name: str, env_dir: Path) -> dict[str, str]:
    """Read back a component's persisted answers, keyed by input name, for
    reuse during `update` without re-prompting."""
    contents = read_secret_file(env_dir / f"{name}.env")
    if contents is None:
        return {}
    answers: dict[str, str] = {}
    for line in contents.splitlines():
        if not line or "=" not in line:
            continue
        key, _, value = line.partition("=")
        answers[key] = value
    return answers
