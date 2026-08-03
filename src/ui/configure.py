"""Step 2: sequential configure prompts (FR-014/FR-015).

One input at a time, masked when the catalog marks it `secret: true`. These
are ordinary inline prompts — no application, no alternate screen — so they
compose naturally with the picker that ran just before them.
"""

from __future__ import annotations

from prompt_toolkit import prompt as pt_prompt

from src.core.state_model import ComponentInput


def collect_inputs(
    component_name: str, inputs: list[ComponentInput]
) -> dict[str, str] | None:
    """Returns the collected answers, or `None` if the developer cancelled."""
    answers: dict[str, str] = {}
    for declared in inputs:
        try:
            answers[declared.name] = pt_prompt(
                f"{component_name} · {declared.label}: ",
                is_password=declared.secret,
            )
        except (EOFError, KeyboardInterrupt):
            return None
    return answers
