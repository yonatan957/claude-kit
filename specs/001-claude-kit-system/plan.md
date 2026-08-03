# Implementation Plan: claude-kit System — Component Manager for Claude Code

**Branch**: `001-claude-kit-system` | **Date**: 2026-08-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-claude-kit-system/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

claude-kit is a local, frozen-binary CLI/TUI tool (distributed via npm) that lets a developer discover, configure, install, update, and remove Claude Code components — Skills, Agents, Plugins, Tools, and MCP servers — through three cooperating JSON engines (a remote-synced `registry.json` catalog, a local `installed.json` ground-truth lockfile, and a `state.json` async notification cache) and a strict frontend/core separation so all install logic stays testable, non-blocking, and idempotent. The technical approach is a single Python 3.11+ project: a pure `core/` + `installers/` engine, a Typer-based `commands/` CLI frontend, a Textual-based two-step TUI (`ui/tui.py`), a minimal fast-path `notify/` module for the session-start hook, surgical (non-destructive) text-level editing of the developer's shared settings file and `CLAUDE.md`, and PyInstaller `--onedir` packaging wrapped by an npm `bin` shim for distribution.

## Technical Context

**Language/Version**: Python 3.11+ (frozen via PyInstaller; matches the `core/`, `installers/`, `ui/tui.py` module layout implied by the project's own constitution)

**Primary Dependencies**: Typer (CLI argument parsing/subcommands), Textual (two-step TUI: picker, search mode, sequential configure prompts), Pydantic v2 (typed models + validation for the three JSON engines), a minimal JSON-block surgical editor for `claude_settings.json`'s `mcpServers` key (see research.md — not a generic JSON dump, to satisfy byte-for-byte preservation of untouched keys), system `git` invoked via `subprocess` for catalog repo sync (no embedded git library)

**Storage**: Local JSON files only — `~/.claude-kit-repo/registry.json` (synced catalog cache), `~/.claude-kit/installed.json` (lockfile), `~/.claude-kit/state.json` (notification cache), `~/.claude-kit/env.d/*.env` (restricted per-component secret files) — plus the developer's existing `~/.claude/skills/`, `~/.claude/agents/`, `claude_settings.json`, and `CLAUDE.md`. No database, no network service.

**Testing**: pytest for `core/`/`installers/` unit tests (pure-function, no mocks needed since there's no I/O to mock in `core/`) and integration tests (real CLI invocations against a temp `$HOME`); Textual's built-in `Pilot` harness for TUI interaction tests; contract tests validating the three JSON schemas and CLI exit-code/output contracts.

**Target Platform**: Cross-platform developer workstation CLI (macOS, Linux, Windows terminal/PowerShell/Git Bash), each shipped as a platform-specific PyInstaller `--onedir` build

**Project Type**: Single project — local CLI/TUI developer tool (no client/server split)

**Performance Goals**: Session-start notification hook reads `state.json` and prints in well under 100ms with zero network/subprocess calls on that path (Principle V, instant boot); TUI picker navigation and toggle response feels instantaneous (no perceptible input lag, i.e., re-render well within a single terminal frame)

**Constraints**: `core/` and `installers/` modules MUST perform no stdout/stderr writes, prompts, or process exits (Principle I); `update` MUST never block for input (Principle II); the CLI MUST NOT self-upgrade (Principle III); every command/script MUST be idempotent (Principle IV); the startup hook MUST do no synchronous network/git/subprocess work (Principle V); edits to `claude_settings.json` MUST touch only the `mcpServers` block, leaving every other byte untouched; edits to `CLAUDE.md` MUST be limited to appending one reference line; secrets MUST NOT appear in `installed.json`

**Scale/Scope**: Single developer, single machine at a time; a catalog on the order of tens to a few hundred components spread across 5 categories (skills, agents, plugins, tools, mcps); five interactive/scripted CLI verbs (`init`, `config`, `update`, `add`/`remove`, `list`, `check`) plus the passive startup hook

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I. Strict Architectural Separation | `core/` and `installers/` contain no `print`/`input`/`sys.exit`; all output/prompting lives in `commands/` and `ui/tui.py` | **PASS** — project structure below dedicates separate top-level packages; contract tests in Phase 1 will assert this via static/lint check plus unit tests instantiating `core`/`installers` functions with no stdout capture expected |
| II. Non-Interactive and Uninterrupted Updates | `update` never prompts; new-input components are flagged `"pending"` | **PASS** — FR-021/FR-024 drive `update`'s design in data-model.md; no TUI/prompt import is reachable from the `update` command path |
| III. User-Controlled Upgrades | No self-upgrade code path exists anywhere in the CLI | **PASS** — `check`/`list`/startup hook only ever render a notice string; no package-manager invocation is ever issued by the tool itself |
| IV. Strict Idempotency | Repeated command/script runs produce no duplicate entries or drift | **PASS** — `installed.json` is keyed by component name (map, not list) so re-installation is an overwrite-in-place upsert by construction; script lifecycle contract (Phase 1) requires each install/config/verify/remove script to be re-runnable |
| V. Fast-Path Session Startup Hook | Startup hook does a fast local read only; all network/catalog work happens in the detached `claude-kit check` subprocess | **PASS** — `notify/` module is a separate, minimal-import package with zero dependency on `core`, `installers`, network, or git; `check` is the only place those are invoked, always launched detached |

No violations identified. Complexity Tracking table is not needed.

**Post-Phase 1 re-check**: data-model.md, contracts/, and quickstart.md were reviewed against the same five gates after design. No new violations were introduced — notably, the `mcpServers` surgical-edit approach (research.md #3) and the append-only `CLAUDE.md` approach (research.md #4) make Principle II's settings-preservation guarantee (FR-038/SC-007) structural rather than best-effort, and the `notify/` package's exclusion from the `core`/`installers`/network dependency graph (data-model.md's Notification Snapshot section) keeps Principle V's instant-boot guarantee intact. Gate status is unchanged: **PASS** on all five principles.

## Project Structure

### Documentation (this feature)

```text
specs/001-claude-kit-system/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── core/                    # Pure functions only — no I/O, no printing, no prompting, no exit
│   ├── registry.py          #   parse/validate registry.json, resolve min_cli_version gate
│   ├── diffing.py           #   compute add/remove/update plans from desired vs. installed state
│   ├── state_model.py       #   Pydantic models for the 3 JSON engines
│   └── notice.py            #   pure rendering of a findings dict → a single notice string
├── installers/               # Perform actual install/remove I/O; return results or raise typed
│   │                         #   exceptions — never print, prompt, or exit
│   ├── content.py            #   skills/agents: copy/delete files
│   ├── marketplace.py        #   plugins: delegate to `claude plugin install/uninstall`
│   ├── script.py             #   tools/mcps: install.sh → inputs → config.sh → mcp_config → verify.sh
│   ├── settings_patch.py     #   surgical mcpServers block editor (byte-preserving)
│   └── secrets.py            #   write/delete restricted per-component secret files
├── commands/                 # Frontend: argument parsing, printing, exit codes
│   ├── init_cmd.py
│   ├── config_cmd.py         #   drives ui/tui.py, then Step 2 configure prompts
│   ├── update_cmd.py
│   ├── add_remove_cmd.py
│   ├── list_cmd.py
│   └── check_cmd.py          #   detached-process entry point
├── ui/
│   └── tui.py                 # Textual app: picker (Step 1) + sequential configure prompts (Step 2)
├── notify/
│   └── hook.py                 # Minimal, dependency-light: read state.json, print message, exit
└── cli.py                      # Typer app wiring commands/ subcommands together

tests/
├── contract/                  # JSON schema + CLI exit-code/output contract tests
├── integration/                # Full command flows against a temp $HOME (init→config→update→list→remove)
└── unit/                       # Pure-function tests for core/ and installers/

npm/
├── package.json                 # publishes the `claude-kit` npm package
├── bin/claude-kit.js             # shim: locates/execs the platform PyInstaller binary
└── postinstall.js                # selects/unpacks the correct platform build

dist/                              # PyInstaller --onedir build output (generated, not committed)
```

**Structure Decision**: Single project (Option 1), specialized into the frontend/core split the constitution mandates. `core/` and `installers/` are separated from each other (not merged) because `core/` must remain 100% I/O-free and unit-testable with zero mocking, while `installers/` inherently performs file/subprocess I/O but must still never talk directly to the terminal. `notify/` is its own minimal package (not part of `commands/`) so the session-start hook's import graph stays tiny and fast, per Principle V. `npm/` and `dist/` are packaging concerns, kept out of `src/` and `tests/`.

## Complexity Tracking

*No Constitution Check violations were identified; this table is intentionally empty.*
