"""Locating a top-level key's value span in raw JSON text (research.md #3).

Built on `json_scan`'s character primitives. This exists so `settings_patch.py`
can replace exactly one key's bytes and leave every other byte of the user's
settings file — whitespace, key order, indentation, trailing newline — exactly
as it found it (FR-038/SC-007). A json.load -> mutate -> json.dump round-trip
cannot make that guarantee.

Offsets in, offsets out: nothing here knows about `mcpServers` or settings.
"""

from __future__ import annotations

import json

from src.installers.json_scan import (
    SettingsPatchError,
    _skip_string,
    _skip_value,
    _skip_whitespace,
)

__all__ = ["SettingsPatchError", "_find_top_level_key_span", "_object_span"]


def _find_top_level_key_span(text: str, key: str) -> tuple[int, int] | None:
    """Returns (value_start, value_end) for `key` at the top level of the
    JSON object in `text`, or None if the key is absent."""
    i = _skip_whitespace(text, 0)
    if i >= len(text) or text[i] != "{":
        raise SettingsPatchError("settings file's top-level value is not a JSON object")
    i += 1
    while True:
        i = _skip_whitespace(text, i)
        if i >= len(text):
            raise SettingsPatchError("unterminated settings file")
        if text[i] == "}":
            return None
        if text[i] != '"':
            raise SettingsPatchError(f"expected a JSON object key at offset {i}")
        key_end = _skip_string(text, i)
        found_key = json.loads(text[i:key_end])
        i = _skip_whitespace(text, key_end)
        if i >= len(text) or text[i] != ":":
            raise SettingsPatchError(f"expected ':' after key at offset {i}")
        i = _skip_whitespace(text, i + 1)
        value_start = i
        value_end = _skip_value(text, i)
        if found_key == key:
            return (value_start, value_end)
        i = _skip_whitespace(text, value_end)
        if i < len(text) and text[i] == ",":
            i += 1
            continue
        if i < len(text) and text[i] == "}":
            return None
        raise SettingsPatchError(f"expected ',' or '}}' after value at offset {i}")


def _object_span(text: str) -> tuple[int, int]:
    i = _skip_whitespace(text, 0)
    if i >= len(text) or text[i] != "{":
        raise SettingsPatchError("settings file's top-level value is not a JSON object")
    end = _skip_value(text, i)
    return (i, end)
