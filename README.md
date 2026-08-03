# claude-kit

A component manager for [Claude Code](https://claude.com/claude-code) — discover, configure,
install, update, and remove Skills, Agents, Plugins, Tools, and MCP servers from a versioned
Catalog Repo, without hand-editing any configuration file.

claude-kit is a local CLI/TUI tool distributed as a frozen binary via npm.

## Install

```sh
npm install -g claude-kit
```

## Quick start

```sh
claude-kit init
```

`init` verifies your Claude Code environment, sets up claude-kit's local state, and walks you
straight into the interactive picker so you can select what you want and configure any
credentials it needs — all without touching a JSON or Markdown file by hand.

## Commands

| Command | What it does |
|---|---|
| `claude-kit init` | First-run setup: verify the environment, create local state, then launch `config`. |
| `claude-kit config [type]` | Interactive two-step flow — a picker across every category (optionally pre-filtered to `type`), then sequential configuration prompts for anything newly selected that needs input. |
| `claude-kit add <type> <name>` | Non-interactively install one named component (for scripts/CI). Drives the same configuration prompts if the component needs input. |
| `claude-kit remove <type> <name>` | Non-interactively remove one named, installed component. Idempotent — a no-op if it's already gone. |
| `claude-kit update` | Refreshes every installed component against the latest catalog, reusing stored credentials. Never prompts, never blocks — safe for CI/unattended runs. |
| `claude-kit list` | Read-only view of the components you have **installed**: version, current or outdated, configuration status, active or inactive. To browse what's *available*, use `config`. |
| `claude-kit check` | Background check (normally launched detached by the session-start hook) that refreshes the notice shown at the next session start. |

Every command exits `0` on success and non-zero with a clear message on failure, so `add`/
`remove`/`update` are safe to script and gate on.

## Using the picker

`claude-kit config` runs **inline** in your terminal — it doesn't take over the screen or
clear your scrollback, and its final frame stays in your history like any other command's
output.

| Key | What it does |
|---|---|
| `↑` / `↓` | Move between rows. |
| `Enter` | Select or deselect the highlighted component. On the **Approve & Install** row at the bottom of the list, applies everything at once. |
| `Tab` | Toggle search on and off — the only way in, and the only way out. |
| `Esc` | Leave search, or cancel the picker with no changes applied. |

Selection is shown with a stable marker that never moves or disappears as you navigate:

| Marker | Meaning |
|---|---|
| `[ ]` | Not selected. |
| `[✓]` | Selected — will be installed (green). |
| `[X]` | Currently installed, now deselected — will be removed (red). |

Approval is deliberately reachable only from the bottom row: there is no single-key
shortcut that can commit changes by accident.

## How it works

- **Catalog** — a versioned Catalog Repo (git), synced locally, describing every available
  component: its category, handler, declared files/inputs, and version.
- **Installed Record** (`~/.claude-kit/installed.json`) — the local ground truth for what's
  actually installed, keyed by component name, so every install/remove is a safe upsert.
- **Credentials** — secret inputs (like API keys) are masked on screen, stored only in a
  restricted local file (`~/.claude-kit/env.d/`), and never written in cleartext to
  `installed.json`.
- **Settings preservation** — claude-kit edits only the `mcpServers` key of your shared
  `settings.json`, byte-for-byte preserving everything else in the file.

See [`specs/001-claude-kit-system/`](specs/001-claude-kit-system/) for the full spec, data
model, and CLI contract this implementation is built against.

## Development

```sh
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"
.venv/Scripts/python -m pytest
```

Run the CLI directly during development with `python -m src.cli <command>`.

See [`DEVELOPMENT.md`](DEVELOPMENT.md) for the full guide: trying the
interactive picker yourself in a sandboxed demo environment, building a
frozen binary, and packaging/publishing the npm distribution.
