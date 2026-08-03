"""Surgical `mcpServers` block editor (research.md #3, FR-038): locates the
top-level "mcpServers" key's exact value span in the raw settings file text
via a hand-rolled JSON tokenizer (not a regex, not a full parse-and-redump),
and replaces only that span. Every other byte of the file — whitespace, key
order, formatting elsewhere — is left untouched.
"""

from __future__ import annotations

import json


class SettingsPatchError(Exception):
    """Raised when the settings file's top-level JSON object cannot be located."""


def _skip_whitespace(text: str, index: int) -> int:
    while index < len(text) and text[index] in " \t\r\n":
        index += 1
    return index


def _skip_string(text: str, index: int) -> int:
    """`index` must point at the opening quote. Returns the index just past
    the closing quote."""
    i = index + 1
    while True:
        if i >= len(text):
            raise SettingsPatchError("unterminated string in settings file")
        ch = text[i]
        if ch == "\\":
            i += 2
            continue
        if ch == '"':
            return i + 1
        i += 1


def _skip_value(text: str, index: int) -> int:
    """`index` points at the first character of a JSON value. Returns the
    index just past the end of that value."""
    index = _skip_whitespace(text, index)
    if index >= len(text):
        raise SettingsPatchError("unexpected end of settings file while reading a value")
    ch = text[index]
    if ch == '"':
        return _skip_string(text, index)
    if ch in "{[":
        depth = 1
        i = index + 1
        while depth > 0:
            if i >= len(text):
                raise SettingsPatchError("unterminated object/array in settings file")
            c = text[i]
            if c == '"':
                i = _skip_string(text, i)
                continue
            if c in "{[":
                depth += 1
            elif c in "}]":
                depth -= 1
            i += 1
        return i
    # number / true / false / null — scan until a structural delimiter
    i = index
    while i < len(text) and text[i] not in ",}] \t\r\n":
        i += 1
    return i


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
