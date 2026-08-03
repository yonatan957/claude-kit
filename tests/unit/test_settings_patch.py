"""Unit tests for src/installers/settings_patch.py's surgical `mcpServers`
editor: every untouched byte/key of a fixture settings file must survive a
patch unchanged (FR-038/SC-007)."""

from src.installers.settings_patch import get_mcp_servers, patch_mcp_servers

FIXTURE_SETTINGS = """{
  "theme":   "dark",
  "mcpServers": {
    "old-server": { "command": "foo" }
  },
  "customKey": [1, 2, 3],
  "nested": { "a": { "b": "c" } }
}
"""

NEW_MCP_SERVERS = {"fixture-mcp": {"command": "node", "args": ["server.js"]}}


def test_patch_preserves_every_other_key_byte_for_byte():
    patched = patch_mcp_servers(FIXTURE_SETTINGS, NEW_MCP_SERVERS)

    assert '"theme":   "dark",' in patched
    assert '"customKey": [1, 2, 3],' in patched
    assert '"nested": { "a": { "b": "c" } }' in patched
    assert patched.startswith("{\n")
    assert patched.rstrip("\n").endswith("}")


def test_patch_replaces_mcp_servers_value():
    patched = patch_mcp_servers(FIXTURE_SETTINGS, NEW_MCP_SERVERS)

    assert get_mcp_servers(patched) == NEW_MCP_SERVERS
    assert "old-server" not in patched


def test_patch_is_idempotent_reapplying_same_value():
    once = patch_mcp_servers(FIXTURE_SETTINGS, NEW_MCP_SERVERS)
    twice = patch_mcp_servers(once, NEW_MCP_SERVERS)

    assert once == twice


def test_patch_inserts_key_when_absent():
    no_mcp = '{\n  "theme": "dark"\n}\n'

    patched = patch_mcp_servers(no_mcp, NEW_MCP_SERVERS)

    assert '"theme": "dark"' in patched
    assert get_mcp_servers(patched) == NEW_MCP_SERVERS


def test_patch_inserts_key_into_empty_object():
    patched = patch_mcp_servers("{}", NEW_MCP_SERVERS)

    assert get_mcp_servers(patched) == NEW_MCP_SERVERS


def test_get_mcp_servers_returns_empty_dict_when_absent():
    no_mcp = '{\n  "theme": "dark"\n}\n'

    assert get_mcp_servers(no_mcp) == {}


def test_patch_survives_string_values_containing_braces_and_commas():
    tricky = '{\n  "note": "a {tricky, value} with braces",\n  "mcpServers": {}\n}\n'

    patched = patch_mcp_servers(tricky, NEW_MCP_SERVERS)

    assert '"note": "a {tricky, value} with braces"' in patched
    assert get_mcp_servers(patched) == NEW_MCP_SERVERS
