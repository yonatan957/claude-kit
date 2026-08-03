# Tasks: claude-kit System — Component Manager for Claude Code

**Input**: Design documents from `/specs/001-claude-kit-system/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included. plan.md's Testing section and the constitution's idempotency-review gate commit this project to pytest contract/unit/integration tests, so test tasks are generated alongside implementation for every phase. **As of the Phase 2 refinement the Textual `Pilot` harness is replaced by (a) direct unit tests against the framework-free `PickerState` and (b) `prompt_toolkit`'s `create_pipe_input()`/`DummyOutput()` for end-to-end key handling.**

**Status**: Phases 1–8 (T001–T064) are complete — that is the original build. **Phases 9–14 (T065–T101) are the Phase 2 refinement** described in plan.md's "Revision" note: the inline `prompt_toolkit` TUI, the `Tab`/`Enter` interaction model, installed-only `list`, and Principle VI compliance. Existing task IDs and their completion state are preserved as the historical record and MUST NOT be renumbered.

**Organization**: Tasks are grouped by user story (from spec.md, priorities P1–P5) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Every task includes an exact file path

## Path Conventions

Single project, per plan.md's Project Structure:

```text
src/{core,installers,commands,ui,notify}/, src/cli.py
tests/{contract,integration,unit}/
npm/
```

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project scaffolding and shared test fixtures

- [X] T001 Create the full project skeleton per plan.md's Project Structure: `src/core/`, `src/installers/`, `src/commands/`, `src/ui/`, `src/notify/`, `src/cli.py`, `tests/contract/`, `tests/integration/`, `tests/unit/`, each with an `__init__.py` where it's a package
- [X] T002 Initialize `pyproject.toml` for a Python 3.11+ project with dependencies: `typer`, `textual`, `pydantic>=2`, `pytest`, `pytest-asyncio` (for Textual `Pilot` tests)
- [X] T003 [P] Configure ruff + black lint/format settings in `pyproject.toml`
- [X] T004 [P] Create a fixture Catalog Repo in `tests/fixtures/registry_repo/registry.json` containing one `content`-handler skill, one `script`-handler tool with a non-secret input, one `script`-handler MCP server with a secret input, and one `marketplace`-handler plugin, matching `contracts/registry-schema.json`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared engine (path resolution, the three JSON-engine models, registry parsing, diffing, catalog sync, and the CLI skeleton) that every user story installs against or reads from

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement local path constants/resolvers (`~/.claude-kit/`, `~/.claude-kit-repo/`, `~/.claude/skills/`, `~/.claude/agents/`, `claude_settings.json`, `CLAUDE.md`, `~/.claude-kit/env.d/`) in `src/core/paths.py`
- [X] T006 [P] Implement Pydantic v2 models for all three JSON engines (`registry.json`, `installed.json`, `state.json`) per data-model.md's field tables in `src/core/state_model.py`
- [X] T007 Implement registry parsing/validation and the `min_cli_version` comparison gate (FR-022) in `src/core/registry.py` (depends on T006)
- [X] T008 Implement diff computation — desired selection vs. `installed.json` → add/remove/update plan — in `src/core/diffing.py` (depends on T006)
- [X] T009 [P] Implement catalog sync via system `git` (`clone`/`pull` into `~/.claude-kit-repo`, per research.md #5) in `src/installers/catalog_sync.py` (depends on T005)
- [X] T010 Create the Typer CLI app skeleton wiring empty `init`/`config`/`update`/`add`/`remove`/`list`/`check` subcommands in `src/cli.py` (depends on T007)
- [X] T011 [P] Contract test: validate the fixture `registry.json` against `contracts/registry-schema.json` in `tests/contract/test_registry_schema.py`
- [X] T012 [P] Contract test: validate a generated `installed.json` shape against `contracts/installed-schema.json` in `tests/contract/test_installed_schema.py`
- [X] T013 [P] Contract test: validate a generated `state.json` shape against `contracts/state-schema.json` in `tests/contract/test_state_schema.py`
- [X] T014 [P] Unit tests for `src/core/registry.py` (handler validation, `min_cli_version` gate) in `tests/unit/test_registry.py`
- [X] T015 [P] Unit tests for `src/core/diffing.py` (add/remove/update plan correctness) in `tests/unit/test_diffing.py`

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 - First-Time Setup and Interactive Configuration (Priority: P1) 🎯 MVP

**Goal**: A developer runs `claude-kit init`, is walked into the two-step picker/configure TUI, selects components across categories (including one requiring a credential), approves, and ends up with those components active and configured — without hand-editing any file.

**Independent Test**: On a machine with no prior claude-kit state, run `init` then the interactive configuration flow, select a mix of components (including one requiring a credential), approve, and verify the components are active and credentials were collected — all without directly editing JSON/markdown.

### Tests for User Story 1

- [X] T016 [P] [US1] Integration test: `claude-kit init` verifies the environment, creates dirs/baseline files, deploys `genie-claude.md`, appends the `CLAUDE.md` reference line exactly once (re-running `init` adds no duplicate) in `tests/integration/test_init.py`
- [X] T017 [P] [US1] Integration test (Textual `Pilot`): picker Step 1 — toggle selections update live per-category counts, search mode filters and pins selections, deselecting an active component flags it as pending removal, cancel applies zero changes in `tests/integration/test_story1_picker.py`
- [X] T018 [P] [US1] Integration test: Step 2 sequential configure — masked secret entry, `installed.json` shows `config.status = "done"`, `env.d/<name>.env` holds the real secret, `installed.json`'s `answers` field is the literal string `"<set>"` in `tests/integration/test_story1_configure.py`
- [X] T019 [P] [US1] Integration test: `claude_settings.json` is byte-for-byte identical outside the `mcpServers` key before vs. after an MCP install in `tests/integration/test_settings_preservation.py`
- [X] T020 [P] [US1] Integration test: selecting a component name that collides with an existing `"user"`-sourced (manually placed) entry is refused without explicit, distinct confirmation in `tests/integration/test_naming_collision.py`
- [X] T021 [P] [US1] Unit test: `src/installers/settings_patch.py`'s surgical `mcpServers` editor preserves every untouched byte/key of a fixture settings file in `tests/unit/test_settings_patch.py`
- [X] T022 [P] [US1] Unit test: `src/installers/content.py` and `src/installers/script.py` produce no duplicate entries/files/registrations when install or remove is run twice consecutively in `tests/unit/test_installers_idempotency.py`

### Implementation for User Story 1

- [X] T023 [P] [US1] Implement the content-handler installer (copy/delete declared files for skills/agents; record `source`, `installed_hash`, `installed_at`) in `src/installers/content.py` per FR-033/FR-041
- [X] T024 [P] [US1] Implement the marketplace-handler installer (delegate install/remove to the catalog's `plugin_marketplace` command templates) in `src/installers/marketplace.py` per FR-034
- [X] T025 [P] [US1] Implement the surgical `mcpServers` block editor (locate the key's exact span via a JSON tokenizer, replace only that span) in `src/installers/settings_patch.py` per research.md #3/FR-038
- [X] T026 [P] [US1] Implement the restricted secret file writer/deleter (`chmod 600` on POSIX, owner-only ACL on Windows, one shared function so callers never branch on OS) in `src/installers/secrets.py` per FR-016/FR-039/research.md #7
- [X] T027 [US1] Implement the script-handler install sequence — accepting already-collected `inputs[]` answers as parameters (collection itself happens only in `commands/`/`ui/tui.py`, never in this module, per script-lifecycle.md): `install.sh` → `config.sh` with `<UPPER_SNAKE_CASE>` env vars → merge `mcp_config` via T025 → `verify.sh`; on verify failure, deregister `mcp_config` immediately and mark `"failed"` — in `src/installers/script.py` per script-lifecycle.md/FR-035/FR-042 (depends on T025, T026)
- [X] T028 [US1] Implement the script-handler removal sequence (strip `mcp_config` first → `uninstall.sh` → delete `env.d/<name>.env` → delete the `installed.json` entry) in `src/installers/script.py` per FR-036 (depends on T027)
- [X] T029 [P] [US1] Implement `claude-kit init` (verify a valid Claude Code environment, create local dirs/baseline files idempotently, deploy `genie-claude.md`, append the `CLAUDE.md` reference line only if absent, then launch `config`) in `src/commands/init_cmd.py` per FR-001–FR-005 (depends on T005, T009)
- [X] T030 [P] [US1] Implement Textual picker Step 1 — one scrollable list across all declared categories, live per-category selection counts, up/down navigation + toggle, cancel with zero changes, a dedicated search mode filtering the catalog (plus configured external sources) that pins newly-selected items to the top on return, deselected-active items flagged as pending removal, optional category pre-filter, and a single "Approve & install" action — in `src/ui/tui.py` per FR-006–FR-013
- [X] T031 [US1] Implement Textual Step 2 sequential configure prompts (one input at a time, masked entry when `secret: true`) in `src/ui/tui.py` per FR-014/FR-015 (depends on T030)
- [X] T032 [US1] Implement `claude-kit config [type]` (run picker Step 1, apply the full add/remove diff plan in one pass through the installers, then run Step 2 for every newly selected component with declared `inputs[]`; refuse with a clear error, no hang, if not run in a TTY) in `src/commands/config_cmd.py` per FR-006–FR-016/cli-commands.md (depends on T007, T008, T009, T023, T024, T027, T030, T031)
- [X] T033 [US1] Implement the naming-collision confirmation path (refuse to silently overwrite a `"user"`-sourced component; require an explicit, distinct confirmation before proceeding) in `src/commands/config_cmd.py` and `src/ui/tui.py` per FR-043 (depends on T032)
- [X] T034 [US1] Wire `init` and `config` into `src/cli.py` (depends on T010, T029, T032)

**Checkpoint**: User Story 1 is fully functional and independently testable (MVP)

---

## Phase 4: User Story 2 - Scripted Add and Remove for Automation (Priority: P2)

**Goal**: A developer or script installs/removes one named component in a single non-interactive command with a reliable exit code.

**Independent Test**: Run the add command with a known component name and confirm it becomes active; run the remove command for the same name and confirm it's fully uninstalled; verify exit codes reflect success/failure.

### Tests for User Story 2

- [X] T035 [P] [US2] Integration test: `claude-kit add <type> <name>` installs with no picker shown, drives Step 2 configure prompts when inputs are required, and exits `0` in `tests/integration/test_add.py`
- [X] T036 [P] [US2] Integration test: `claude-kit remove <type> <name>` removes all files/registrations and is a no-op success (exit `0`) when run a second time in `tests/integration/test_remove.py`
- [X] T037 [P] [US2] Integration test: add/remove failures (unknown name, failing lifecycle script) exit non-zero with a clear message and leave no partial/unlabeled state in `tests/integration/test_add_remove_failures.py`
- [X] T037B [P] [US2] Integration test: `claude-kit add <type> <name>` on a name colliding with an existing `"user"`-sourced entry is refused without explicit, distinct confirmation in `tests/integration/test_add_naming_collision.py`

### Implementation for User Story 2

- [X] T038 [US2] Implement `claude-kit add <type> <name>` (non-interactive install via the type's installer, then Step 2 configure if `inputs[]` is declared, clear non-zero-exit errors on unknown type/name/handler failure; refuse to silently overwrite a `"user"`-sourced naming collision — print the same distinct-confirmation prompt used by T033 rather than proceeding silently) in `src/commands/add_remove_cmd.py` per FR-017/FR-019/FR-020/FR-043 (depends on T007, T009, T023, T024, T027, T031, T033)
- [X] T039 [US2] Implement `claude-kit remove <type> <name>` (non-interactive removal via the type's installer, idempotent no-op if already removed, clear non-zero-exit errors on handler failure) in `src/commands/add_remove_cmd.py` per FR-018/FR-020/FR-037 (depends on T023, T024, T028)
- [X] T040 [US2] Wire `add` and `remove` into `src/cli.py` (depends on T010, T038, T039)

**Checkpoint**: User Stories 1 AND 2 both work independently

---

## Phase 5: User Story 3 - Keeping Installed Components in Sync (Priority: P3)

**Goal**: `claude-kit update` refreshes all installed components against the latest catalog without ever prompting, preserving existing credentials.

**Independent Test**: With a component already installed/configured, advance the catalog, run `update`, and verify content refreshes, credentials are preserved and not re-prompted, and the command never waits on input.

### Tests for User Story 3

- [X] T041 [P] [US3] Integration test: `update` syncs the catalog, refreshes installed components, reuses existing credentials without re-prompting, and never reads stdin in `tests/integration/test_update.py`
- [X] T042 [P] [US3] Integration test: `update` halts with a non-zero exit and applies no changes when the catalog's `min_cli_version` exceeds the running CLI version in `tests/integration/test_update_version_gate.py`
- [X] T043 [P] [US3] Integration test: running `update` twice consecutively with an unchanged catalog produces a byte-identical `installed.json` (aside from timestamps) in `tests/integration/test_update_idempotency.py`
- [X] T044 [P] [US3] Integration test: an update that introduces a new required input marks that component `"pending"` and lists it in the end-of-run summary, without pausing in `tests/integration/test_update_new_input.py`
- [X] T045 [P] [US3] Integration test: `update` re-running `verify.sh` for a component whose credential is no longer valid marks it `"pending"` again and reports it, without pausing to collect a new value in `tests/integration/test_update_reverify_failure.py`

### Implementation for User Story 3

- [X] T046 [US3] Implement `claude-kit update` (sync catalog via T009, check the `min_cli_version` gate via T007 and halt with no changes if violated, re-run install/config/verify for every installed component reusing stored answers, never read stdin, print an end-of-run summary of anything `"pending"`/`"failed"`) in `src/commands/update_cmd.py` per FR-021–FR-025/FR-044 (depends on T007, T008, T009, T023, T024, T027)
- [X] T047 [US3] Wire `update` into `src/cli.py` (depends on T010, T046)

**Checkpoint**: User Stories 1, 2, AND 3 all work independently

---

## Phase 6: User Story 4 - Discovering Current State (Priority: P4)

**Goal**: `claude-kit list` shows every catalog component's install/freshness/config/active status in one place.

**Independent Test**: With a mix of installed/not-installed/current/outdated/configured/pending components, run `list` and verify every field is shown clearly and correctly.

### Tests for User Story 4

- [X] T048 [P] [US4] Integration test: `claude-kit list` shows every catalog component's category, installed/not, current-vs-outdated (hash/version compare), config status (done/pending/failed/n-a), and active/inactive state, with pending visually distinguished from done in `tests/integration/test_list.py`

### Implementation for User Story 4

- [X] T049 [US4] Implement `claude-kit list` (read-only render combining the synced catalog with `installed.json`: category, installed, up-to-date vs. outdated, config status, active/inactive; pending visually distinct) in `src/commands/list_cmd.py` per FR-026/FR-027 (depends on T007, T008)
- [X] T050 [US4] Wire `list` into `src/cli.py` (depends on T010, T049)

**Checkpoint**: User Stories 1–4 all work independently

---

## Phase 7: User Story 5 - Passive Awareness of Updates at Session Start (Priority: P5)

**Goal**: A single pre-rendered notice appears instantly at session start when something's worth attention, without ever slowing startup, and is never repeated once shown.

**Independent Test**: Trigger a background check with a newer catalog and a pending config both present, start a session, and verify a single already-rendered notice appears immediately and isn't repeated once seen.

### Tests for User Story 5

- [X] T051 [P] [US5] Unit test: `src/core/notice.py`'s pure findings→message rendering, including producing a null message when nothing is new beyond `announced`, in `tests/unit/test_notice.py`
- [X] T052 [P] [US5] Integration test: `claude-kit check` writes `state.json` with a non-null `message` and matching `findings`, exits `0`, and produces no interactive stdout in `tests/integration/test_check.py`
- [X] T053 [P] [US5] Integration test: the notify hook prints the stored `message` verbatim with zero network/git/subprocess calls on that path in `tests/integration/test_notify_hook.py`
- [X] T054 [P] [US5] Integration test: a finding already recorded in `announced` is not shown again on a later hook read; a genuinely new finding after another `check` run is still shown in `tests/integration/test_notify_dedup.py`

### Implementation for User Story 5

- [X] T055 [P] [US5] Implement the pure notice-rendering function (`findings` dict → single message string, or `null` when nothing new) in `src/core/notice.py` per data-model.md's Notification Snapshot section
- [X] T056 [US5] Implement `claude-kit check` (compare local vs. remote catalog commit and local vs. latest CLI version, count `"pending"` configs, render+write `message`/`findings`/`announced` to `state.json`, non-zero exit only if the write itself fails) in `src/commands/check_cmd.py` per FR-028–FR-032 (depends on T007, T009, T055)
- [X] T057 [P] [US5] Implement the minimal notify hook — a fast, local-only read of `state.json` that prints `message` verbatim if present, with **zero imports from `core/`, `installers/`, or anything network/git-touching** (per Principle V, do not import `src/core/state_model.py` or `src/core/paths.py`; inline the `state.json` path and a minimal JSON read instead) — in `src/notify/hook.py` per FR-030/FR-031/Principle V
- [X] T058 [US5] Implement the detached launch of `claude-kit check` from the notify hook (`subprocess.Popen` with `start_new_session=True` on POSIX, `CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS` on Windows, never awaited) in `src/notify/hook.py` per research.md #6 (depends on T057)
- [X] T059 [US5] Wire `check` into `src/cli.py` (depends on T010, T056)

**Checkpoint**: All five user stories are independently functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation and packaging, spanning all user stories

- [X] T060 [P] Full-system idempotency pass: run quickstart.md's entire Story 1–5 sequence twice end-to-end from the same populated state and diff `installed.json`/`state.json`/`claude_settings.json` (only timestamps may differ) in `tests/integration/test_full_idempotency.py`
- [X] T061 [P] Configure the PyInstaller `--onedir` build spec for `src/cli.py` per research.md #8
- [X] T062 [P] Create `npm/package.json`, `npm/bin/claude-kit.js` (platform-binary exec shim), and `npm/postinstall.js` (fetch/unpack the matching platform build) per research.md #8
- [X] T063 [P] Write `README.md` covering `npm install -g claude-kit` and the `init`/`config`/`add`/`remove`/`update`/`list`/`check` command surface
- [X] T064 Run quickstart.md's full validation walkthrough end-to-end against the fixture Catalog Repo and record the results

---

# Phase 2 Refinement (T065–T101)

Everything below implements plan.md's Phase 2 revision. Read plan.md's "TUI Architecture (Phase 2)", "`list` Refinement (FR-026)", and "Principle VI Remediation" sections before starting.

**Hard rule for every task below**: no Python file in `src/` may exceed **90 total physical lines** (blanks, comments, and docstrings all count — research.md §1b). Verify with:

```bash
python -c "import pathlib;[print(len(p.read_text(encoding='utf-8').splitlines()),p) for p in pathlib.Path('src').rglob('*.py') if len(p.read_text(encoding='utf-8').splitlines())>90]"
```

---

## Phase 9: Phase 2 Setup (Dependency Swap & Guardrail)

**Purpose**: Put the new UI library and the line-limit guardrail in place before any code moves

- [X] T065 Add `prompt_toolkit>=3.0` to `[project.dependencies]` and remove `textual>=0.58` in `pyproject.toml` (Textual becomes unused after T080; removing it also shrinks the PyInstaller bundle per plan.md Technical Context)
- [X] T066 Write the Principle VI guardrail in `tests/contract/test_file_line_limit.py`: walk `src/**/*.py`, fail any file over 90 total physical lines, and report every offender with its count in one assertion message. Seed it with an explicit `DEFERRED_OVER_LIMIT` allowlist containing exactly the 8 files from plan.md's Complexity Tracking table (`installers/script.py`, `core/state_model.py`, `commands/update_cmd.py`, `installers/settings_patch.py`, `commands/add_remove_cmd.py`, `core/diffing.py`, `commands/check_cmd.py`, `notify/hook.py`) so the test lands green and guards every new file; add a comment pointing at Phase 14 for allowlist removal
- [X] T067 Verify T066 fails correctly by temporarily appending 100 blank lines to a non-allowlisted file (e.g. `src/core/paths.py`), running the test, then reverting — a guardrail that cannot fail is not a guardrail

**Checkpoint**: `pytest tests/contract/test_file_line_limit.py` passes and blocks any new over-limit file

---

## Phase 10: User Story 1 — Dismantle the Monolithic TUI (Priority: P1)

**Goal**: Replace the 245-line full-screen Textual `src/ui/tui.py` with an inline `prompt_toolkit` UI decomposed across `src/ui/`, every file ≤90 lines (FR-045/FR-046/FR-047)

**Independent test**: Launch `claude-kit config` in a real terminal; the picker renders below the shell prompt, prior scrollback is still reachable by scrolling up, no full-screen frame is drawn, and only the counts line / list / one-line key hint are visible

**Build order**: strictly bottom-up along plan.md's layering rule (`tui_app` → `keys`/`render` → `screens` → `widgets` → `entry`), so every task compiles against already-written modules

- [X] T068 [US1] Create `src/ui/entry.py`: move the `PickerEntry` dataclass out of `tui.py` (fields `category`, `name`, `component`, `currently_installed`, `selected`, `pinned`, `naming_collision`) and add a `SelectionState` enum (`UNSELECTED`/`SELECTED`/`PENDING_REMOVAL`) plus a `selection_state(entry)` helper implementing data-model.md's derived-state table. No `prompt_toolkit` import
- [X] T069 [P] [US1] Create `src/ui/style.py`: a `prompt_toolkit` `Style` mapping `class:selected` → green, `class:removal` → red, `class:cursor` → reverse-video, `class:dim` → the key-hint/counts styling. Colors defined once here and nowhere else
- [X] T070 [P] [US1] Create `src/ui/widgets/checkbox.py`: `glyph_for(state) -> tuple[str, str]` returning `("[ ]", "")` / `("[✓]", "class:selected")` / `("[X]", "class:removal")`. Assert all three glyphs are equal display width so rows never shift horizontally (FR-047)
- [X] T071 [US1] Create `src/ui/widgets/row.py`: render one `PickerEntry` to styled fragments — checkbox glyph (from T070) + `[category] name - description`, prefixed with the FR-043 collision warning when `naming_collision`, and the cursor background applied by position, **never** by mutating the glyph (depends on T068, T070)
- [X] T072 [US1] Create `src/ui/widgets/approve_row.py`: render the sentinel "Approve & Install" row with its own styling, visually separated from entry rows and carrying no checkbox glyph (FR-012)
- [X] T073 [US1] Create `src/ui/screens/picker.py`: browse-mode view model — order entries pinned-first (FR-010), then append the single sentinel approve row, and compute per-category selection counts honoring `category_filter` (FR-006, depends on T068)
- [X] T074 [US1] Create `src/ui/screens/search.py`: search-mode view model — hold the `query` buffer and filter entries by substring match against name and description, with **no** approve row appended (depends on T068)
- [X] T075 [US1] Create `src/ui/state.py`: the `PickerState` machine — `entries`, `mode` (`BROWSE`/`SEARCH`), `query`, `cursor`; a derived `visible_rows()` delegating to T073/T074; `move(delta)` clamping without wraparound; `toggle_search()` implementing the `Tab` edge in both directions (clearing `query` on entry, pinning search-selected entries on exit, resetting `cursor` to 0 both ways); `activate()` returning `TOGGLED` or `APPROVED` by cursor position; and `desired_selection()` returning `dict[category, set[name]]`. **Zero `prompt_toolkit` imports** — this file must be testable with no terminal (depends on T073, T074)
- [X] T076 [US1] Write pure unit tests for the state machine in `tests/unit/test_picker_state.py`, with no terminal and no `prompt_toolkit`: cursor clamping at both ends; `Tab` round-trip returning to browse with search-selected entries pinned first; `activate()` on an entry returning `TOGGLED` and flipping `selected`; `activate()` on the last row returning `APPROVED`; `selection_state` transitions for a currently-installed entry being deselected (→ `PENDING_REMOVAL`); `desired_selection()` contents after a mixed sequence (depends on T075)
- [X] T077 [US1] Create `src/ui/keys.py`: a `KeyBindings` factory binding exactly the contract in `contracts/cli-commands.md` — `up`/`down` → `state.move(±1)`; `enter` → `state.activate()` (exiting the app with the desired selection on `APPROVED`); `tab` → `state.toggle_search()`; printable + `backspace` → edit `query` **in search mode only**; `escape` → leave search, or cancel from browse; `c-c` → cancel. Bind **no** other key — specifically no `a` and no `space` (FR-007/FR-009/FR-012) (depends on T075)
- [X] T078 [US1] Create `src/ui/render.py`: build the full viewport `FormattedText` — counts line, bounded list window scrolled to keep `cursor` visible, and the one-line key hint `↑↓ move · Enter select · Tab search · Esc cancel`. Nothing else may be drawn (FR-046) (depends on T071, T072, T073)
- [X] T079 [US1] Create `src/ui/tui_app.py`: assemble `Application(full_screen=False, ...)` over a single `Window`/`FormattedTextControl` with a bounded `Dimension`, wire in T077's bindings and T069's style, and expose `run_picker(registry, installed, category_filter, naming_collisions) -> dict[str, set[str]] | None` returning `None` on cancel (FR-008). This is the only file permitted to import `Application` (depends on T077, T078)
- [X] T080 [US1] Rewrite Step 2 as `src/ui/configure.py`: sequential per-component prompts via `prompt_toolkit.shortcuts.prompt(..., is_password=input.secret)`, returning collected answers or `None` on cancel, preserving the existing `ConfigureApp` call contract used by `config_cmd`/`add_remove_cmd` (FR-014/FR-015)
- [X] T081 [US1] Delete `src/ui/tui.py` and update every import of `PickerApp`/`ConfigureApp` to the new entry points (`src/commands/config_cmd.py:40`, plus any in `src/commands/add_remove_cmd.py`) (depends on T079, T080)
- [X] T082 [US1] Rewrite `tests/integration/test_story1_picker.py` against `prompt_toolkit`'s `create_pipe_input()` + `DummyOutput()`, replacing the Textual `Pilot` harness: feed `Enter` to toggle and assert live counts; feed `Tab`/query/`Tab` and assert filtering then pinning; feed `Enter` on a currently-installed entry and assert `PENDING_REMOVAL`; feed `Esc` and assert a `None` return with zero changes. **Delete the old `pilot.press("tab")` focus-shift step at line 66 — `Tab` no longer moves focus** (depends on T079)
- [X] T083 [US1] Add regression tests in `tests/integration/test_tui_inline.py` for the requirements most likely to silently regress: assert the rendered output contains no alternate-screen (`?1049h`) or clear-screen (`2J`) sequence (FR-045/SC-010); assert `a` does not approve and `space` does not toggle (FR-007/FR-012); assert the checkbox glyph for a given entry is byte-identical before and after moving the cursor onto and off it (FR-047)

**Checkpoint**: `claude-kit config` runs inline with the new key model; `src/ui/tui.py` is gone; every file under `src/ui/` is ≤90 lines

---

## Phase 11: User Story 1 — In-Scope Complexity Debt (`config_cmd.py`)

**Goal**: Bring `src/commands/config_cmd.py` (282 lines) under the Principle VI cap by extracting the two cohesive units identified in plan.md's Project Structure

- [X] T084 [US1] Create `src/commands/config_collision.py`: move `_has_naming_collision`, `_record_user_sourced`, and `_default_confirm_collision` out of `config_cmd.py` verbatim (FR-043 logic is unchanged — this is a pure move), along with the `_CONTENT_TARGET_DIRS` map they depend on
- [X] T085 [US1] Create `src/commands/config_apply.py`: move `_apply_add`, `_apply_remove`, and `_apply_plan` out of `config_cmd.py`, importing collision helpers from T084 and `ui/configure.py` for the Step 2 prompt callback; keep `NamingCollisionRefused` and `NoTTYError` importable from their original module path to avoid breaking callers (depends on T084)
- [X] T086 [US1] Slim `src/commands/config_cmd.py` to orchestration only — load installed → sync/parse registry → detect collisions → `run_picker` → `compute_selection_diff` → `_apply_plan` → save → report — re-exporting the moved names for backward compatibility, and confirm it is ≤90 lines (depends on T085)
- [X] T087 [US1] Run the existing suites that cover this code unchanged (`tests/integration/test_story1_configure.py`, `test_naming_collision.py`, `test_add_naming_collision.py`) and confirm they pass with no edits — proving T084–T086 were behavior-preserving moves (depends on T086)

**Checkpoint**: `config_cmd.py`, `config_apply.py`, `config_collision.py` all ≤90 lines with the FR-043 test suite green and unmodified

---

## Phase 12: User Story 4 — Installed-Only `list` (Priority: P4)

**Goal**: `claude-kit list` shows only what is actually installed (FR-026), per plan.md's "`list` Refinement" section and the revised `contracts/cli-commands.md`

**Independent test**: With a catalog containing components that were never installed, run `claude-kit list` and confirm none of them appear, while every installed component does

- [X] T088 [US4] Invert `build_rows()` in `src/commands/list_cmd.py` to iterate the five category maps of `installed.json` and look up each entry's catalog component for the freshness comparison, emitting nothing for catalog components absent from `installed.json` (FR-026)
- [X] T089 [US4] Handle orphaned entries in `src/commands/list_cmd.py`: an installed component with no matching catalog component still emits a row, with `current` set to `None` rendering as `unknown` — it must not raise and must not be skipped
- [X] T090 [US4] Update the row formatter and header in `src/commands/list_cmd.py`: drop the now-meaningless `INSTALLED` column and render `CATEGORY · NAME · VERSION · CURRENT · CONFIG · ACTIVE`, keeping pending config visually distinct from done (FR-027)
- [X] T091 [US4] Add the empty-state branch to `run_list()` in `src/commands/list_cmd.py`: with zero installed components across all five categories, print `No components installed. Run 'claude-kit config' to add some.` and return exit `0` (spec.md's new edge case)
- [X] T092 [US4] Rewrite `tests/integration/test_list.py` for the new contract: assert `fixture-plugin` (in the catalog, never installed) is **absent** from output — replacing the existing assertions at lines 87–88 that require it to be present; assert an installed-but-not-in-catalog component renders with `unknown`; assert the empty state prints the guidance line and exits `0`; update `test_list_rows_reflect_installed_current_config_active` since `build_rows` no longer emits a `fixture-mcp` row when it is not installed (depends on T088–T091)
- [X] T093 [US4] Confirm `src/commands/list_cmd.py` is ≤90 lines after the rewrite (plan.md budgets ~60); if over, extract the formatter into `src/commands/list_format.py` (depends on T090)

**Checkpoint**: `claude-kit list` is a projection of `installed.json`; catalog-only components never appear

---

## Phase 13: Phase 2 Polish & Cross-Cutting

- [X] T094 [P] Update `README.md`'s command-surface section for the new picker key model (`Tab` search toggle, `Enter` select/approve, no `a`, no `Space`) and for `list` now showing only installed components
- [ ] T095 [P] ⚠️ NEEDS HUMAN VERIFICATION (agent cannot allocate a TTY; the automatable assertions are covered by `tests/integration/test_tui_inline.py`) — Re-run quickstart.md's Story 1 walkthrough in a real terminal and confirm each newly added assertion: inline rendering with scrollback intact, marker stability while moving the cursor, `Tab`-only search entry/exit, `a`/`Space` being inert, and approval only via the bottom row (validates FR-045/FR-046/FR-047/SC-010)
- [X] T096 [P] Re-run quickstart.md's Story 4 walkthrough and confirm all three `list` cases: installed-only output, the orphaned component rendering `unknown`, and the empty state exiting `0`
- [X] T097 Re-run the full suite (`pytest`) plus `ruff check src tests` and `black --check src tests`, and confirm `tests/contract/test_file_line_limit.py` passes with the allowlist unchanged (depends on all prior Phase 2 tasks)
- [X] T098 Run the full-system idempotency pass (`tests/integration/test_full_idempotency.py`) to confirm the TUI and `list` changes did not disturb Principle IV (depends on T097)

**Checkpoint**: Phase 2 refinement complete; Principles I–V still green and Principle VI green for every file this phase touched

---

## Phase 14: Deferred — Remaining Principle VI Debt

**Not part of the Phase 2 refinement.** These are the 8 files from plan.md's Complexity Tracking table that exceed the 90-line cap but that Phase 2 has no reason to open. plan.md recommends landing them as one focused follow-up. Each task ends by removing that file from `tests/contract/test_file_line_limit.py`'s `DEFERRED_OVER_LIMIT` allowlist, so the guardrail tightens with every completed split.

- [X] T099 [P] Split `src/installers/script.py` (214) into `script.py` (lifecycle orchestration) + `script_steps.py` (install/config/verify subprocess runners) + `script_env.py` (env assembly); re-run `tests/unit/test_installers_idempotency.py` and the script-lifecycle contract before removing it from the allowlist
- [X] T100 [P] Split `src/core/state_model.py` (159) into `models_registry.py` + `models_installed.py` + `models_state.py`, re-exported from `state_model.py` so no import site changes; then remove from the allowlist
- [X] T101 [P] Split the remaining six: `commands/update_cmd.py` (148) → `+ update_reverify.py`; `installers/settings_patch.py` (144) → `+ json_span.py`; `commands/add_remove_cmd.py` (105) → reuse `commands/config_apply.py` from T085; `core/diffing.py` (99) → `+ plan_items.py`; `commands/check_cmd.py` (96) → `+ core/version_check.py`; `notify/hook.py` (95) → fold its formatting helper into `core/notice.py` **while preserving Principle V's minimal import graph**. Remove each from the allowlist as it lands, and delete the allowlist entirely once empty

**Checkpoint**: ✅ DONE — `DEFERRED_OVER_LIMIT` is empty; Principle VI is fully mechanical with zero exceptions. Largest file in `src/` is 81 lines of code (was 282). Note the splits went further than planned: `script.py` needed 6 modules (not 3) and `settings_patch.py` needed 3 (not 2), because the corrected metric was applied to the *results* of each split, not just its input.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends only on Foundational
- **User Story 2 (Phase 4)**: Depends on Foundational; reuses US1's installers (T023, T024, T027, T028, T031) and, for the naming-collision confirmation path (FR-043), also depends on US1's T033
- **User Story 3 (Phase 5)**: Depends only on Foundational; reuses US1's installers (T023, T024, T027)
- **User Story 4 (Phase 6)**: Depends only on Foundational
- **User Story 5 (Phase 7)**: Depends only on Foundational
- **Polish (Phase 8)**: Depends on all five user stories being complete

### User Story Dependencies

All five stories depend solely on the Foundational phase, not on each other — each is independently testable per its Independent Test above. In practice, US2 and US3 share installer modules with US1 (content.py/marketplace.py/script.py), so implementing those installer tasks once in Phase 3 unblocks Phase 4 and Phase 5 without rework.

### Within Each User Story

- Tests are written first and should fail before their corresponding implementation task lands
- Installers before commands; commands before CLI wiring
- Story complete before moving to the next priority (if working sequentially)

### Parallel Opportunities

- All Setup tasks marked [P] can run together
- All Foundational tasks marked [P] can run together (T005, T006, T009 first; T007/T008 after T006; T011–T015 anytime after their target module exists)
- Once Foundational completes, Phases 3–7 (US1–US5) can be staffed and run in parallel — they share only already-built installer/core modules, not in-progress files
- Within Phase 3, all test tasks (T016–T022) can run in parallel; T023–T026 (four distinct installer files) can run in parallel before T027 depends on T025/T026

---

## Phase 2 Refinement: Dependencies & Execution Order

### Phase Dependencies

- **Phase 9 (Setup)**: Start immediately. T065 (dependency swap) blocks all of Phase 10; T066/T067 (guardrail) block nothing but should land first so every later file is checked as it is written
- **Phase 10 (Dismantle TUI)**: Depends on T065. Strictly bottom-up — see the build chain below
- **Phase 11 (`config_cmd` split)**: Depends on Phase 10 completing (T081 rewires the imports that T086 then slims)
- **Phase 12 (`list` refactor)**: Depends only on Phase 9. **Fully independent of Phases 10–11** — different files, different command, no shared code. Can be staffed in parallel with the entire TUI workstream
- **Phase 13 (Polish)**: Depends on Phases 10, 11, and 12
- **Phase 14 (Deferred debt)**: Depends on Phase 13. Explicitly out of scope for this refinement; T101's `add_remove_cmd.py` item also depends on T085

### Phase 10 build chain (strictly sequential where noted)

```text
T068 (entry.py) ─┬─▶ T071 (row) ─┐
T069 (style) ────┤               ├─▶ T078 (render) ─┐
T070 (checkbox) ─┘               │                  ├─▶ T079 (tui_app) ─▶ T081 (delete tui.py) ─▶ T082, T083
T068 ─▶ T073 (screens/picker) ───┤                  │
T068 ─▶ T074 (screens/search) ───┴─▶ T075 (state) ──┴─▶ T077 (keys)
                                     └─▶ T076 (state unit tests)
T080 (configure.py) ─────────────────────────────────▶ T081
```

- T069, T070 are `[P]` with each other and with T068
- T072 (`approve_row`) is `[P]` with T071
- T076 (pure state tests) can be written the moment T075 lands and runs in parallel with T077/T078
- T080 (`configure.py`) is independent of the whole picker chain and can be done any time after T065

### Parallel Opportunities

- **Two-track split**: one person on Phases 10→11 (TUI), another on Phase 12 (`list`). They converge at Phase 13
- Phase 9's T066/T067 can proceed alongside anything
- Phase 13's T094, T095, T096 are all `[P]`
- Phase 14's T099, T100, T101 are `[P]` with each other (distinct files)

### Independent test criteria

- **Phase 10**: `claude-kit config` renders inline with scrollback intact; `Tab` is the only search edge; `Enter` toggles and (on the bottom row) approves; `a`/`Space` inert
- **Phase 11**: the FR-043 collision suite passes **unmodified** — the proof that the split was behavior-preserving
- **Phase 12**: a catalog component that was never installed never appears in `claude-kit list`

---

## Parallel Example: User Story 1

```bash
# Tests, launched together:
Task: "Integration test: claude-kit init in tests/integration/test_init.py"
Task: "Integration test: picker Step 1 in tests/integration/test_story1_picker.py"
Task: "Integration test: Step 2 configure in tests/integration/test_story1_configure.py"
Task: "Integration test: settings preservation in tests/integration/test_settings_preservation.py"
Task: "Integration test: naming collision in tests/integration/test_naming_collision.py"
Task: "Unit test: settings_patch.py in tests/unit/test_settings_patch.py"
Task: "Unit test: installer idempotency in tests/unit/test_installers_idempotency.py"

# Installers, launched together (independent files):
Task: "Content-handler installer in src/installers/content.py"
Task: "Marketplace-handler installer in src/installers/marketplace.py"
Task: "Surgical mcpServers editor in src/installers/settings_patch.py"
Task: "Secret file writer/deleter in src/installers/secrets.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (blocks everything)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: run Story 1's Independent Test from spec.md end-to-end against the fixture catalog
5. Demo: a developer goes from nothing configured to a working, personalized Claude Code setup

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. US1 → validate independently → MVP demo
3. US2 → validate independently (scriptable add/remove for CI)
4. US3 → validate independently (safe unattended sync)
5. US4 → validate independently (discovery view)
6. US5 → validate independently (passive session-start notice)
7. Polish → full idempotency pass, packaging, docs

### Parallel Team Strategy

Once Foundational is done, US1–US5 can be split across developers since each only reads from the Foundational engine and, for US2/US3, from US1's already-built installer modules — no story's command/UI code is a dependency of another story's command/UI code.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps each task to its user story for traceability
- Tests are written before their corresponding implementation task and should fail first
- Commit after each task or logical group (per this repo's `CLAUDE.md` Git Workflow: stage and commit after completing each task)
- Stop at any checkpoint to validate a story independently before moving on
- Avoid: vague tasks, two tasks touching the same file marked `[P]`, cross-story dependencies that would break independent testability
