# Implementation Plan: Config Picker & Configure Flow

**Branch**: `001-config-picker-tui` | **Date**: 2026-07-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-config-picker-tui/spec.md`

## Summary

Build the `claude-kit config [<type>]` flow: a single interactive screen that lists every
component type the catalog declares, pre-checked with what's installed, lets the user toggle
selections with one consistent keybinding scheme, and ends in one "Approve & install" action.
Approving applies installs/removals and then automatically walks the user through configuring
anything that needs input. The technical approach is a strict split between a pure `core/`
(diffing state vs. selections, applying changes, tracking pending configuration — no I/O) and a
`ui/tui.py` frontend built on `prompt_toolkit` that renders that core state as the picker,
search, and configure screens, per the constitution's Core Has No Voice principle.

## Technical Context

**Language/Version**: Python 3.11+ (matches the declared `claude-kit-cli` stack; frozen to a
standalone binary for distribution — packaging is out of scope for this feature)

**Primary Dependencies**: `typer` (CLI command routing for `config` / `config <type>`), `rich`
(non-interactive output: install/approval summaries), `prompt_toolkit` (the interactive picker,
search, and configure screens — see research.md for the prompt_toolkit-vs-Textual decision)

**Storage**: Local files only — reads `registry.json` (synced separately, out of scope here) and
`installed.json` (read at picker-open, written at approval and after each configuration step);
no database

**Testing**: `pytest`; per constitution Principle I (Test-Before-Mutation, NON-NEGOTIABLE), the
`core` functions that apply installs/removals or write configuration MUST have tests written and
failing before implementation

**Target Platform**: Developer workstations (Linux/macOS/Windows) inside a restricted/air-gapped
corporate network; terminal-based, no network calls during selection/approval beyond what
individual components' own `install.sh`/`config.sh` scripts perform

**Project Type**: Single project — CLI with an interactive terminal frontend

**Performance Goals**: Picker interaction must feel instant — no perceptible key-to-redraw lag
during scrolling, selection, or search-as-you-type, consistent with the "the picker never delays
you" experience described in the spec; no hard numeric target since this is UX-behavioral, not a
throughput system

**Constraints**: `core/` MUST NOT print, prompt, or exit (Constitution Principle II — Core Has No
Voice); the manageable component-type list MUST come from `registry.json`'s `types[]`, never be
hardcoded (Constitution Principle III); only the single approval action may mutate installed
state (spec FR-005); the `mcpServers` settings block is the only part of Claude Code settings
ever touched (Constitution Principle V)

**Scale/Scope**: Five component types today (skills, agents, plugins, tools, MCP servers), each
with catalog entries numbering in the tens to low hundreds — an internally curated catalog, not
an open marketplace; scope is the picker/search/approve/configure flow only, not catalog sync
(`update`) or the install/removal transaction engine itself (relied on as a dependency)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Section | Check | Result |
|---|---|---|
| I. Test-Before-Mutation | Approval and configuration steps are the only paths that mutate `installed.json`/settings; both will be built test-first with a snapshot→apply→verify→commit-or-revert transaction, per FR-005/FR-014 | PASS |
| II. Core Has No Voice | Design puts diffing (`plan`), applying (`apply`), and configuring (`pending`/`submit`) in `core/` as pure input→object functions; all prompting/rendering lives in `ui/tui.py` | PASS |
| III. Types Are Data, Not Code | Picker sections and `config <type>` scoping are both driven by iterating `registry.json`'s `types[]`; no type name is hardcoded in `core/` or `commands/` | PASS |
| IV. Delegate, Don't Rebuild | Uses `prompt_toolkit` directly for the terminal UI rather than hand-rolling a renderer; skill/agent search delegates to the catalog (and optional external `skill_sources`) rather than reimplementing search | PASS |
| V. Sacred User Files | Only the `mcpServers` block is written for MCP components; no other settings keys are touched by this feature | PASS |
| Catalog Integrity | Feature only reads `registry.json`/`installed.json`; it does not alter the CI validation gate or hashing scheme | PASS (no interaction) |
| Two-Repo Workflow | Feature lives entirely in `claude-kit-cli`; it does not require catalog-repo changes | PASS (no interaction) |

No violations — Complexity Tracking is not needed for this feature.

**Post-Phase 1 re-check**: `data-model.md` and `contracts/core-interface.md` keep `core/` limited
to pure functions returning data (`SelectionPlan`, `ApplyResult`, `ConfigStep`, `VerifyResult`) and
push all masking/rendering/prompting into the frontend contract notes — no drift from the
pre-design table above. Still PASS on all rows.

## Project Structure

### Documentation (this feature)

```text
specs/001-config-picker-tui/
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
├── core/
│   ├── models.py         # Component, ComponentType, SelectionPlan, ConfigStep, ApplyResult, VerifyResult
│   ├── plan.py            # plan(state, registry, selections) -> ChangePlan  (pure diff, no I/O)
│   ├── apply.py           # apply(plan) -> list[ApplyResult]  (runs installs/removals as transactions)
│   └── configure.py       # pending(state, registry) -> list[ConfigStep]; submit(step, answers) -> VerifyResult
├── commands/
│   └── config.py          # typer command: `config` and `config <type>` — wires core to ui
├── ui/
│   └── tui.py              # prompt_toolkit screens: picker, search overlay, approve row, configure wizard
└── registry/
    └── catalog.py          # loads registry.json + installed.json, exposes declared types[]

tests/
├── unit/
│   ├── test_plan.py         # selection diff → ChangePlan correctness (installs, removals, no-op)
│   └── test_configure.py    # pending-config detection, submit() transaction behavior
├── integration/
│   └── test_config_flow.py  # end-to-end: fresh machine, returning user, scoped-by-type, reconfigure
└── contract/
    └── test_core_interface.py  # core function signatures/shapes match contracts/core-interface.md
```

**Structure Decision**: Single project (Option 1). The constitution's Core Has No Voice principle
is the reason `core/`, `commands/`, and `ui/` are separate top-level packages rather than one flat
`cli/` module — `core/` must stay importable and testable with zero terminal dependency, since a
future `web/` frontend (out of scope here) will call the exact same `core.plan` / `core.apply` /
`core.pending` / `core.submit` functions that `ui/tui.py` calls today.

## Complexity Tracking

*No violations — table intentionally omitted.*
