"""Character-level JSON scanning primitives.

Each function takes raw text plus an offset and returns the offset just past
the construct it consumed. Nothing here understands JSON *structure* — that is
`json_span.py`'s job — and nothing parses; these only measure.
"""

from __future__ import annotations


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
