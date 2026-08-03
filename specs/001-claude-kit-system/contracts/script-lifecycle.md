# Contract: `script`-Handler Lifecycle (Tools & MCP Servers)

This is the contract between claude-kit's `installers/script.py` and a component author's own lifecycle scripts (`install.sh`, `config.sh`, `verify.sh`, `uninstall.sh`), all optional except where noted.

## Install sequence (`claude-kit add`, `claude-kit config` Step 2 apply, or `update` re-sync)

1. **`install.sh`** (optional) — run with no arguments, no stdin. Non-zero exit aborts the sequence; nothing further runs, and the component's `installed.json` entry is not created.
2. **Collect inputs** — for every entry in the component's declared `inputs[]`, the frontend (never `installers/script.py` itself) prompts the developer (masked if `secret: true`) or, for `update`, reuses previously stored answers without re-prompting.
3. **`config.sh`** (required if `inputs[]` is non-empty) — invoked with each input passed as an environment variable named after `inputs[].name` (uppercased). `config.sh` is solely responsible for persisting any secret value to `~/.claude-kit/env.d/<name>.env`; claude-kit itself never writes a raw secret value anywhere.
4. **`mcp_config` injection** (mcps only) — the component's declared `mcp_config` block is merged into `claude_settings.json`'s `mcpServers.<name>` key via the surgical block editor (see research.md #3). Skipped entirely for `tools`.
5. **`verify.sh`** (optional but strongly recommended; required for the component to ever reach `"done"`) — run with no arguments. Exit code `0` → `installed.json` entry's `config.status = "done"`, `verified_at` set. Non-zero exit → if step 4 ran, immediately deregister the `mcp_config` (FR-042) and set `config.status = "failed"`; if step 4 did not apply (plain `tools`), set `config.status = "pending"` and surface the failure.

## Removal sequence (`claude-kit remove`)

1. Strip the component's `mcp_config` from `claude_settings.json` (mcps only) — always first, so a partially-broken component can never leave a dangling live connection.
2. **`uninstall.sh`** (optional) — run with no arguments.
3. Delete `~/.claude-kit/env.d/<name>.env` if present.
4. Delete the component's entry from `installed.json`.

## Idempotency requirements (Principle IV)

- Running the full install sequence twice with identical inputs MUST leave `installed.json` with exactly one entry for the component (upsert, never append) and MUST NOT invoke `config.sh`/`verify.sh` in a way that duplicates external side effects (e.g., re-registering the same MCP server must be a no-op or overwrite, never a duplicate registration).
- Running the removal sequence on a component that is already fully removed MUST succeed with no error (no-op).
- All four scripts are expected by contract to be idempotent themselves; claude-kit re-running any of them (e.g., during `update`) is a supported, expected usage pattern, not an edge case component authors can opt out of.

## Environment variable contract

- Every declared input is passed to `config.sh` as `<UPPER_SNAKE_CASE_NAME>`.
- No other claude-kit internal state (file paths, other components' answers, credentials) is ever exposed via environment variables to any lifecycle script beyond what that component itself declared.
