# Tasks: claude-kit System — Component Manager for Claude Code

**Input**: Design documents from `/specs/001-claude-kit-system/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included. plan.md's Testing section and the constitution's idempotency-review gate commit this project to pytest contract/unit/integration tests and a Textual `Pilot` harness, so test tasks are generated alongside implementation for every phase.

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
