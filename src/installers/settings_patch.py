"""Surgical `mcpServers` block editor (research.md #3, FR-038).

Replaces only the `mcpServers` key's value span, located by `json_span`, so
every other byte of the user's settings file is left untouched. The scanning
primitives live in `json_span.py`; this module owns just the mcpServers policy.
"""

from __future__ import annotations

import json

from src.installers.json_span import (
    SettingsPatchError,
    _find_top_level_key_span,
    _object_span,
)

__all__ = ["SettingsPatchError", "get_mcp_servers", "patch_mcp_servers"]


def get_mcp_servers(raw_text: str) -> dict:
    """Read-only: the current `mcpServers` object, or `{}` if the key is absent."""
    span = _find_top_level_key_span(raw_text, "mcpServers")
    if span is None:
        return {}
    value_start, value_end = span
    return json.loads(raw_text[value_start:value_end])


def patch_mcp_servers(raw_text: str, new_mcp_servers: dict) -> str:
    """Replace (or insert) the top-level "mcpServers" key's value with
    `new_mcp_servers`, leaving every other byte of `raw_text` untouched."""
    serialized = json.dumps(new_mcp_servers, indent=2)
    span = _find_top_level_key_span(raw_text, "mcpServers")

    if span is not None:
        value_start, value_end = span
        return raw_text[:value_start] + serialized + raw_text[value_end:]

    # Key absent: insert it as a new top-level key, just before the closing brace.
    obj_start, obj_end = _object_span(raw_text)
    closing_brace_index = obj_end - 1
    j = closing_brace_index - 1
    while j > obj_start and raw_text[j] in " \t\r\n":
        j -= 1
    has_existing_keys = raw_text[j] != "{"

    if has_existing_keys:
        insertion = f',\n  "mcpServers": {serialized}\n'
    else:
        insertion = f'\n  "mcpServers": {serialized}\n'
    return raw_text[:closing_brace_index] + insertion + raw_text[closing_brace_index:]
