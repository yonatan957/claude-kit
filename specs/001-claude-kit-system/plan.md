# Implementation Plan: claude-kit System — Component Manager for Claude Code

**Branch**: `001-claude-kit-system` | **Date**: 2026-08-03 | **Spec**: [spec.md](./spec.md)

**Revision**: Phase 2 refinement (2026-08-03) — replaces the full-screen Textual TUI with a lightweight inline `prompt_toolkit` UI (FR-045–FR-047), redefines the picker's interaction model (`Tab`/`Enter`, FR-007/FR-009/FR-012), narrows `list` to installed-only (FR-026), and brings the codebase under Constitution Principle VI (90-line cap).

**Input**: Feature specification from `/specs/001-claude-kit-system/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

claude-kit is a local, frozen-binary CLI/TUI tool (distributed via npm) that lets a developer discover, configure, install, update, and remove Claude Code components — Skills, Agents, Plugins, Tools, and MCP servers — through three cooperating JSON engines (a remote-synced `registry.json` catalog, a local `installed.json` ground-truth lockfile, and a `state.json` async notification cache) and a strict frontend/core separation so all install logic stays testable, non-blocking, and idempotent. The technical approach is a single Python 3.11+ project: a pure `core/` + `installers/` engine, a Typer-based `commands/` CLI frontend, a **lightweight inline `prompt_toolkit` UI decomposed across `ui/` screens and widgets**, a minimal fast-path `notify/` module for the session-start hook, surgical (non-destructive) text-level editing of the developer's shared settings file and `CLAUDE.md`, and PyInstaller `--onedir` packaging wrapped by an npm `bin` shim for distribution.

**Phase 2 refinement.** The picker no longer runs as a full-screen application. It renders inline beneath the shell prompt in the terminal's normal buffer — never entering the alternate screen, never clearing scrollback (FR-045) — and shows only the list, the per-category counts, and a one-line key hint (FR-046). Selection state is drawn with stable glyphs `[ ]` / `[✓]` / `[X]` (FR-047). The interaction model collapses to two keys: `Tab` purely toggles search mode (FR-009) and `Enter` toggles the highlighted row or, on the final "Approve & Install" row, commits the plan (FR-007/FR-012). `claude-kit list` becomes a projection of `installed.json` rather than of the catalog (FR-026).

## Technical Context

**Language/Version**: Python 3.11+ (frozen via PyInstaller; matches the `core/`, `installers/`, `ui/tui.py` module layout implied by the project's own constitution)

**Primary Dependencies**: Typer (CLI argument parsing/subcommands), **`prompt_toolkit` ≥3.0 (inline picker, search mode, sequential configure prompts — replaces Textual; see research.md §1)**, Pydantic v2 (typed models + validation for the three JSON engines), a minimal JSON-block surgical editor for `claude_settings.json`'s `mcpServers` key (see research.md — not a generic JSON dump, to satisfy byte-for-byte preservation of untouched keys), system `git` invoked via `subprocess` for catalog repo sync (no embedded git library). **Textual is dropped from `[project.dependencies]`** — it is unused after this refinement, and removing it also shrinks the PyInstaller bundle.

**Storage**: Local JSON files only — `~/.claude-kit-repo/registry.json` (synced catalog cache), `~/.claude-kit/installed.json` (lockfile), `~/.claude-kit/state.json` (notification cache), `~/.claude-kit/env.d/*.env` (restricted per-component secret files) — plus the developer's existing `~/.claude/skills/`, `~/.claude/agents/`, `claude_settings.json`, and `CLAUDE.md`. No database, no network service.

**Testing**: pytest for `core/`/`installers/` unit tests (pure-function, no mocks needed since there's no I/O to mock in `core/`) and integration tests (real CLI invocations against a temp `$HOME`); **TUI interaction tests split in two — the picker's state machine (`ui/state.py`) is a pure, synchronous object tested directly with no terminal at all, and end-to-end key handling is tested through `prompt_toolkit`'s `PipeInput` + `DummyOutput` harness (`create_pipe_input()`), which replaces Textual's `Pilot`**; contract tests validating the three JSON schemas and CLI exit-code/output contracts; **plus a new contract test enforcing Constitution Principle VI's 90-line cap across `src/`**.

**Target Platform**: Cross-platform developer workstation CLI (macOS, Linux, Windows terminal/PowerShell/Git Bash), each shipped as a platform-specific PyInstaller `--onedir` build

**Project Type**: Single project — local CLI/TUI developer tool (no client/server split)

**Performance Goals**: Session-start notification hook reads `state.json` and prints in well under 100ms with zero network/subprocess calls on that path (Principle V, instant boot); TUI picker navigation and toggle response feels instantaneous (no perceptible input lag, i.e., re-render well within a single terminal frame). **The inline picker's rendered height is bounded (a fixed viewport window over the entry list) so redraw cost is independent of catalog size.**

**Constraints**: `core/` and `installers/` modules MUST perform no stdout/stderr writes, prompts, or process exits (Principle I); `update` MUST never block for input (Principle II); the CLI MUST NOT self-upgrade (Principle III); every command/script MUST be idempotent (Principle IV); the startup hook MUST do no synchronous network/git/subprocess work (Principle V); **no Python file in `src/` may exceed 90 lines (Principle VI)**; edits to `claude_settings.json` MUST touch only the `mcpServers` block, leaving every other byte untouched; edits to `CLAUDE.md` MUST be limited to appending one reference line; secrets MUST NOT appear in `installed.json`. **The picker MUST NOT enter the terminal's alternate screen buffer or emit any clear-screen/scrollback-reset sequence (FR-045); `Tab` MUST be bound exclusively to the search toggle and MUST NOT perform focus traversal (FR-009); no single-letter approval shortcut may exist (FR-012).**

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
| VI. Python File Line Limit | No Python file in `src/` exceeds 90 lines | **FAIL (pre-existing)** — 11 of 20 source files currently exceed the cap, the worst being `commands/config_cmd.py` (282) and `ui/tui.py` (245). The rule was ratified (constitution v1.1.0, 2026-08-03) *after* this code was written and has never been mechanically enforced. See "Principle VI Remediation" below and the Complexity Tracking table. |

**One gate fails.** Principle VI is violated by the existing codebase, not by anything this refinement introduces — but the constitution admits no grandfathering, so the plan below brings every file it touches into compliance and records the remainder as tracked, scheduled debt rather than silently passing the gate.

### Principle VI Remediation

**Measurement definition** (resolved in research.md §1d; constitution v1.2.0): the cap counts **lines of code** — physical lines that are neither blank nor comment-only. Docstrings count; blanks and `#` comments do not. An earlier revision counted total physical lines and was abandoned after it deleted docstrings to fit and mismeasured four well-commented files. It is enforced by a new contract test, `tests/contract/test_file_line_limit.py`, which walks `src/**/*.py` and fails with a per-file report — making the gate mechanical from here on instead of a review-time judgment call.

Current state, measured:

| File | Lines | In this phase's scope? |
|---|---:|---|
| `commands/config_cmd.py` | 282 | **Yes** — split (drives the picker; must change anyway) |
| `ui/tui.py` | 245 | **Yes** — deleted and replaced by the `ui/` tree below |
| `installers/script.py` | 214 | No — tracked debt |
| `core/state_model.py` | 159 | No — tracked debt |
| `commands/update_cmd.py` | 148 | No — tracked debt |
| `installers/settings_patch.py` | 144 | No — tracked debt |
| `commands/list_cmd.py` | 115 | **Yes** — rewritten for FR-026; lands at ~60 |
| `commands/add_remove_cmd.py` | 105 | No — tracked debt |
| `core/diffing.py` | 99 | No — tracked debt |
| `commands/check_cmd.py` | 96 | No — tracked debt |
| `notify/hook.py` | 95 | No — tracked debt |

The three in-scope files reach compliance as part of this work. The eight out-of-scope files are listed in Complexity Tracking with a proposed split for each; the line-limit contract test should be introduced **together with** those splits (one task per file) so it never lands red.

**Post-Phase 1 re-check (Phase 2 refinement)**: Principles I–V are unaffected by this refinement and remain **PASS** — the new `ui/` package performs terminal I/O, which is exactly where the constitution permits it (Principle I names `ui/` as a frontend location), and it imports only `core.state_model` for types, never `installers/`. Principle VI moves from **FAIL** to **PASS for all files this phase touches**, with the residual eight files tracked below. Principle VI's own rationale explicitly names "splitting screens and widgets out of a monolithic TUI file" as the intended remedy, which is precisely the decomposition adopted here.

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
│   ├── config_cmd.py         #   orchestration only: load → picker → diff → apply → save (~70)
│   ├── config_apply.py       #   NEW: _apply_add/_apply_remove/_apply_plan handler dispatch (~85)
│   ├── config_collision.py   #   NEW: FR-043 detection + "user"-sourced recording (~70)
│   ├── update_cmd.py
│   ├── add_remove_cmd.py
│   ├── list_cmd.py           #   FR-026: projects installed.json, not the catalog (~60)
│   └── check_cmd.py          #   detached-process entry point
├── ui/                        # Inline prompt_toolkit UI — the ONLY package that draws to the
│   │                          #   terminal interactively. No file here exceeds 90 lines.
│   ├── tui_app.py             #   assembles Application(full_screen=False) + runs it (~55)
│   ├── entry.py               #   PickerEntry + SelectionState enum (~45)
│   ├── state.py               #   PickerState: pure, terminal-free state machine (~85)
│   ├── keys.py                #   KeyBindings: Tab / Enter / arrows / cancel (~60)
│   ├── render.py              #   PickerState -> FormattedText for the whole viewport (~65)
│   ├── style.py               #   prompt_toolkit Style: green/red/dim class definitions (~30)
│   ├── configure.py           #   Step 2 sequential prompts, masked when secret (~50)
│   ├── screens/
│   │   ├── picker.py          #     main-list view model: ordering, pinning, counts (~60)
│   │   └── search.py          #     search view model: query buffer + filtering (~55)
│   └── widgets/
│       ├── checkbox.py        #     [ ] / [✓] / [X] glyph + style class per state (~30)
│       ├── row.py             #     one entry -> styled fragments (~50)
│       └── approve_row.py     #     the terminal "Approve & Install" row (~35)
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

**Layering rule inside `ui/`** (what keeps every file small and each one testable in isolation): dependencies point strictly downward, `tui_app.py` → `keys.py`/`render.py` → `screens/` → `widgets/` → `entry.py`. Only `tui_app.py` touches `prompt_toolkit.Application`; only `render.py` and `widgets/` produce styled output; `state.py` imports nothing from `prompt_toolkit` at all. That last point is the important one — **the entire interaction model is testable without a terminal**, because `state.py` is a plain object with plain methods, and `keys.py` is a thin adapter that maps a keypress to one `state.py` call.

## TUI Architecture (Phase 2)

### Inline rendering (FR-045/FR-046)

`prompt_toolkit.Application(full_screen=False)` draws into the normal terminal buffer directly below the shell prompt and, on exit, leaves the rendered output in scrollback like any ordinary command's output. It never emits the alternate-screen sequences (`smcup`/`rmcup`) that a full-screen app uses, which is exactly what FR-045 forbids. The layout is a single `Window` over a `FormattedTextControl`, with `height=Dimension(min=…, max=…)` bounding the viewport; the entry list scrolls *within* that window rather than growing the frame.

Chrome is limited to three regions (FR-046): the counts line, the viewport, and a one-line key hint (`↑↓ move · Enter select · Tab search · Esc cancel`). There is no header, no footer widget, no theme control, and no mouse-driven buttons.

### Interaction state machine (FR-007/FR-009/FR-012)

`PickerState` holds `entries`, `cursor` (an index into the currently visible rows), `mode` (`BROWSE` | `SEARCH`), and `query`. Two modes, with `Tab` as the only edge between them in either direction:

```text
        ┌──────────────── Tab ───────────────┐
        ▼                                    │
   ┌─────────┐                          ┌─────────┐
   │ BROWSE  │                          │ SEARCH  │
   │         │──────────── Tab ────────▶│         │
   └─────────┘                          └─────────┘
   rows: pinned-first entry list        rows: entries matching `query`
   + trailing "Approve & Install" row   (no approve row shown)
```

Key handling, in full:

| Key | `BROWSE` | `SEARCH` |
|---|---|---|
| `Tab` | → `SEARCH`; clear `query`; cursor to 0 | → `BROWSE`; pin anything selected while searching (FR-010); cursor to 0 |
| `Enter` | on an entry row → toggle its selection; on the **"Approve & Install"** row → exit, returning the desired selection | toggle the highlighted result's selection (stays in `SEARCH`) |
| `↑` / `↓` | move cursor within the visible rows (clamped, no wraparound) | same |
| printable | ignored | append to `query`; re-filter; cursor to 0 |
| `Backspace` | ignored | delete last char of `query`; re-filter |
| `Esc` / `Ctrl-C` | exit returning `None` (FR-008, zero changes) | → `BROWSE` (does not quit from search) |

Three details this pins down, each traceable to a requirement:

- **`Tab` is a pure toggle** (FR-009). In `prompt_toolkit`, `Tab` is only special if you bind it — there is no implicit focus traversal to fight. This is the decisive reason for the framework switch: the previous Textual implementation *could not* honor FR-009, because Textual reserves `Tab` for focus movement (the old test at `tests/integration/test_story1_picker.py:66` presses `tab` specifically to move focus off the search input). There is exactly one focusable control in the new design, so focus traversal is meaningless and `Tab` is free.
- **`Enter` is overloaded by cursor position, not by mode** (FR-007/FR-012). `state.activate()` returns either `TOGGLED` or `APPROVED` depending on whether the cursor sits on the sentinel approve row. Approval is therefore reachable *only* by navigating to that row — there is no key that approves from anywhere else, which is what FR-012 requires when it forbids the legacy `a` shortcut.
- **The approve row is a real row in the model**, appended by `screens/picker.py` after the entries, not a separately-rendered footer. That way cursor movement, clamping, and rendering all treat it uniformly, and it is impossible for the cursor to skip past it.

### Checkbox stability (FR-047)

`widgets/checkbox.py` maps a `SelectionState` to a `(glyph, style_class)` pair — `UNSELECTED → ("[ ]", "")`, `SELECTED → ("[✓]", "class:selected")`, `PENDING_REMOVAL → ("[X]", "class:removal")` — with green/red defined once in `style.py`. Because the glyph is derived purely from selection state and never from cursor position, the marker cannot change or disappear as the highlight moves; the cursor is indicated by the row's background style instead. All three glyphs are the same display width, so rows never shift horizontally when state changes.

## `list` Refinement (FR-026)

`build_rows()` inverts its iteration: it walks the five category maps of `installed.json` and, for each installed entry, looks up the matching catalog component to decide current-vs-outdated. Components present in the catalog but absent from `installed.json` are never emitted.

- The `INSTALLED` column is dropped — every row is installed by definition, so the column carried no information. Columns become `CATEGORY · NAME · VERSION · CURRENT · CONFIG · ACTIVE`.
- An installed component **missing from the catalog** (removed upstream, or installed from an older catalog) still renders, with `CURRENT` shown as `unknown`. Dropping the row would hide something the developer actually has on disk, which is the opposite of what FR-026 asks for.
- Zero installed components prints a single empty-state line — `No components installed. Run 'claude-kit config' to add some.` — and still exits `0` (the new edge case added to spec.md).
- A missing/corrupt catalog cache remains a hard error exiting `1`, unchanged; the freshness column cannot be computed without it.

## Complexity Tracking

Principle VI is currently violated by eight files that this phase does not otherwise touch. They are recorded here rather than fixed opportunistically, because splitting a file the phase has no other reason to open risks regressions with no offsetting benefit and would make this change's diff unreviewable. Each carries a proposed split so the follow-up is mechanical:

**Status: resolved.** All four were split (commits `fc15eea`, `4b8c1b9`, `4bd1c13`, `6280b22`). `DEFERRED_OVER_LIMIT` is now empty, so Principle VI applies to `src/` with no exceptions and the largest file is 81 lines of code, down from 282.

| File | Was (LOC) | Split into | Now |
|---|---:|---|---:|
| `installers/script.py` | 169 | `script` (facade) + `script_install` + `script_remove` + `script_runner` + `script_mcp` + `script_env` | ≤81 |
| `commands/update_cmd.py` | 125 | `update_cmd` (run) + `update_refresh` (one component) | ≤81 |
| `installers/settings_patch.py` | 121 | `settings_patch` (policy) + `json_span` (spans) + `json_scan` (chars) | ≤52 |
| `core/state_model.py` | 114 | facade + `models_common` / `models_registry` / `models_installed` / `models_state` | ≤66 |

Two of these needed more modules than proposed above — `script.py` took six rather than three, `settings_patch.py` three rather than two — because the corrected metric was applied to each split's *outputs*, not just its input. Every public API was preserved through a re-exporting facade, so no call site outside the split modules changed.

**Recommended sequencing**: land this phase's TUI/`list` work first, then the eight splits above as one focused follow-up, introducing `tests/contract/test_file_line_limit.py` in the same follow-up so the gate turns green and stays green. Until that test lands, Principle VI remains review-enforced and will drift again.
