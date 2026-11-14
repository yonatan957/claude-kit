"""The genie manifest: the example parses, and anything wrong with it is one SourceError."""

import json
from pathlib import Path

import pytest

from claude_kit.components import ComponentKind
from claude_kit.helpers import SourceError
from claude_kit.sources.genie.manifest import load_manifest

MANIFEST_FILE = Path(__file__).parent / "data" / "genie" / "manifest.json"


def test_the_example_manifest_parses_into_three_entries():
    manifest = load_manifest(MANIFEST_FILE)
    assert [(entry.kind, entry.name) for entry in manifest.entries] == [
        (ComponentKind.MCP, "gitlab"),
        (ComponentKind.MCP, "k8s"),
        (ComponentKind.TOOL, "kubectl"),
    ]
    assert manifest.manifest_dir == MANIFEST_FILE.parent
    gitlab = manifest.entries[0]
    assert gitlab.inputs[0].secret and gitlab.inputs[0].required
    assert gitlab.inputs[1].default == "https://gitlab.internal"


def entry(**fields):
    return {"kind": "mcp", "name": "x", "version": "1", "mcp": {}, **fields}


def manifest_of(*entries, version=1):
    return json.dumps({"manifest_version": version, "entries": list(entries)})


@pytest.mark.parametrize(
    "text",
    [
        "{ not json",
        manifest_of(version=2),
        manifest_of(entry(kind="hook")),
        manifest_of(entry(kind="skill")),
        manifest_of(entry(kind="tool", mcp=None)),
        manifest_of(entry(install={"linux": "install.sh"})),
        manifest_of(entry(mcp=None)),
        manifest_of(entry(inputs=[{"key": "A", "colour": "red"}])),
        manifest_of({"kind": "mcp", "name": "x"}),
        manifest_of("not an object"),
    ],
)
def test_a_bad_manifest_is_one_source_error(tmp_path, text):
    path = tmp_path / "manifest.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(SourceError):
        load_manifest(path)
