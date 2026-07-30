---

description: "Task list for the Config Picker & Configure Flow feature"
---

# Tasks: Config Picker & Configure Flow

**Input**: Design documents from `specs/001-config-picker-tui/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/core-interface.md, quickstart.md

**Tests**: Per the constitution's Test-Before-Mutation principle (NON-NEGOTIABLE), any function
that writes to a user-owned file — `core.apply` (installed.json, settings) and `core.submit`
(secrets, settings) — MUST have a failing test written before its implementation; those tasks
below are marked accordingly and are not optional. Tests for pure/read-only core functions
(`core.plan`, `core.pending`) and the per-story integration scenarios from `quickstart.md` are
included as well, since they anchor the "independently testable" requirement each user story
carries in spec.md.

**Organization**: Tasks are grouped by user story (spec.md) to enable independent implementation
and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Every task includes its exact file path

## Path Conventions

Single project, per plan.md's Project Structure:
`src/core/`, `src/commands/`, `src/ui/`, `src/registry/`, `tests/unit/`, `tests/integration/`, `tests/contract/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization

- [ ] T001 Create the project skeleton per plan.md: `src/core/`, `src/commands/`, `src/ui/`, `src/registry/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, each with an `__init__.py`
- [ ] T002 Initialize the Python project (`pyproject.toml`) with dependencies `typer`, `rich`, `prompt_toolkit`, and dev dependency `pytest`, per plan.md's Technical Context
- [ ] T003 [P] Configure linting/formatting (e.g. `ruff`) for `src/` and `tests/` in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The `core/` interface every user story depends on (Constitution Principle II — Core
Has No Voice) and the registry-driven type discovery every story renders through (Constitution
Principle III — Types Are Data, Not Code)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Define core data models and the `ComponentState` state machine (`Component`, `ComponentType`, `SelectionPlan`, `ConfigStep`, `ConfigurationInput`, `ApplyResult`, `VerifyResult`) per data-model.md in `src/core/models.py`
- [ ] T005 [P] Implement the registry/catalog loader — reads `registry.json` and `installed.json`, exposes the declared `types[]` as the only source of component types (Constitution III) — in `src/registry/catalog.py`
- [ ] T006 [P] Write unit tests for `core.plan` covering install-only, removal-only, mixed, and no-op diffs in `tests/unit/test_plan.py` (write first, must fail before T007)
- [ ] T007 Implement `core.plan(state, registry, selections) -> SelectionPlan` as a pure function with no I/O in `src/core/plan.py` (depends on: T004, T005, T006)
- [ ] T008 [P] Write unit tests for `core.apply` covering install transactions, removal transactions, and FR-014 (a configuration failure later must not roll back a completed install) in `tests/unit/test_apply.py` — MANDATORY per constitution Test-Before-Mutation (write first, must fail before T009)
- [ ] T009 Implement `core.apply(plan: SelectionPlan) -> list[ApplyResult]`, calling into the install/removal transaction dependency (snapshot → apply → health-check → commit/revert, per research.md §2) in `src/core/apply.py` (depends on: T004, T005, T008)
- [ ] T010 [P] Write unit tests for `core.pending` and `core.submit` covering `newly_installed` vs. `user_requested_reconfigure` reasons, masked-input handling, and FR-014 (failed `verify.sh` leaves the component `PENDING_CONFIGURATION`, install untouched) in `tests/unit/test_configure.py` — MANDATORY per constitution Test-Before-Mutation for `submit` (write first, must fail before T011)
- [ ] T011 Implement `core.pending(state, registry) -> list[ConfigStep]` and `core.submit(step, answers) -> VerifyResult` in `src/core/configure.py` (depends on: T004, T005, T010)
- [ ] T012 [P] Write a contract test asserting `core.plan` / `core.apply` / `core.pending` / `core.submit` signatures and return shapes match `contracts/core-interface.md` in `tests/contract/test_core_interface.py` (depends on: T007, T009, T011)
- [ ] T013 [P] Scaffold the `config` typer command entrypoint (routing only, no story behavior yet) in `src/commands/config.py`
- [ ] T014 [P] Scaffold the `prompt_toolkit` `Application` shell with the global key bindings (↑↓ move, enter select/act, tab toggle search, ctrl-c quit) in `src/ui/tui.py`, per research.md §1

**Checkpoint**: Foundation ready — `core/` is fully testable in isolation and user story work can begin.

---

## Phase 3: User Story 1 - First-time setup lands a working baseline (Priority: P1) 🎯 MVP

**Goal**: A developer on a fresh machine runs `config`, chooses Recommended, approves once, and
ends with every recommended component installed and — where needed — configured, with no
further commands required.

**Independent Test**: Run the flow against an empty `installed.json`, choose Recommended, approve,
and confirm every recommended component ends installed and (if it declares inputs) configured and
verified, matching quickstart.md Scenario 1.

### Tests for User Story 1

- [ ] T015 [P] [US1] Integration test for the fresh-machine recommended flow (quickstart.md Scenario 1) in `tests/integration/test_fresh_machine_setup.py` (write first, must fail)
- [ ] T016 [P] [US1] Integration test confirming a configuration failure does not undo a completed install (quickstart.md Scenario 6 / spec.md US1 Acceptance Scenario 6 / FR-014) in `tests/integration/test_config_failure_no_rollback.py` (write first, must fail)

### Implementation for User Story 1

- [ ] T017 [US1] Implement first-use detection (true iff `installed.json` has no claude-kit-managed components) in `src/core/plan.py` (depends on: T007)
- [ ] T018 [US1] Implement the Recommended/Custom choice screen, shown only when first-use is detected, in `src/ui/tui.py` (depends on: T014, T017)
- [ ] T019 [US1] Implement the picker screen: one section per registry-declared type, live per-section selection counters, installed items pre-checked, "Approve & install" as the fixed final row, in `src/ui/tui.py` (depends on: T018)
- [ ] T020 [US1] Wire the Approve action to call `core.apply(plan)` and render a per-component install result line for each entry in `src/ui/tui.py` (depends on: T009, T019)
- [ ] T021 [US1] Implement the automatic post-install configure wizard: call `core.pending`, prompt for each `ConfigStep`'s inputs (masking `sensitive` fields), call `core.submit`, loop until nothing is pending, in `src/ui/tui.py` (depends on: T011, T020)
- [ ] T022 [US1] Implement the end-of-run summary distinguishing installed / configured / pending counts (FR-013) in `src/ui/tui.py` (depends on: T021)
- [ ] T023 [US1] Wire the `config` command entrypoint to launch the first-use-aware flow in `src/commands/config.py` (depends on: T013, T018)

**Checkpoint**: User Story 1 is fully functional and independently testable — a fresh machine can reach a fully installed and configured baseline in one run.

---

## Phase 4: User Story 2 - Returning user adjusts what's installed (Priority: P2)

**Goal**: A developer with an existing setup opens the picker pre-checked with current state, adds
one component and removes another, and approves — only those two changes take effect.

**Independent Test**: Open the flow against a machine with existing installs, select one new item
and deselect one installed item, approve, and confirm the resulting state reflects exactly that
one addition and one removal (quickstart.md Scenario 2).

### Tests for User Story 2

- [ ] T024 [P] [US2] Integration test for the returning-user add + remove flow (quickstart.md Scenario 2) in `tests/integration/test_returning_user_add_remove.py` (write first, must fail)
- [ ] T025 [P] [US2] Integration test confirming a no-op selection skips straight to configuration (quickstart.md Scenario 3, FR-011) in `tests/integration/test_noop_skips_to_configure.py` (write first, must fail)
- [ ] T026 [P] [US2] Integration test for re-selecting an already-configured component to reconfigure it (quickstart.md Scenario 4, FR-015) in `tests/integration/test_reconfigure.py` (write first, must fail)

### Implementation for User Story 2

- [ ] T027 [US2] Implement the pending-removal visual flag on unchecked, currently-installed rows and the removal count on the approve row (FR-004) in `src/ui/tui.py` (depends on: T019)
- [ ] T028 [US2] Implement the skip-to-configure branch when `SelectionPlan.is_noop` is true (FR-011) in `src/ui/tui.py` (depends on: T007, T011, T021)
- [ ] T029 [US2] Implement the re-select-to-reconfigure toggle for already-`CONFIGURED` components (FR-015) in `src/ui/tui.py` and `src/core/configure.py` (depends on: T011, T021)
- [ ] T030 [US2] Ensure the `config` entrypoint skips the Recommended/Custom prompt whenever any managed component is already installed in `src/commands/config.py` and `src/ui/tui.py` (depends on: T023)

**Checkpoint**: User Stories 1 and 2 both work independently — installs, removals, no-ops, and reconfiguration all behave correctly.

---

## Phase 5: User Story 3 - Narrowing to a single component type (Priority: P3)

**Goal**: `config <type>` presents the identical picker/approve/configure experience filtered to
one catalog-declared component type.

**Independent Test**: Invoke the flow scoped to one declared type and confirm only that type's
items appear, with components of other types unaffected (quickstart.md Scenario 5).

### Tests for User Story 3

- [ ] T031 [P] [US3] Integration test confirming a scoped-by-type run leaves all other types untouched (quickstart.md Scenario 5) in `tests/integration/test_scoped_by_type.py` (write first, must fail)

### Implementation for User Story 3

- [ ] T032 [US3] Implement the `config <type>` argument, validated against the registry's declared types with a clear error for an unknown type (edge case) in `src/commands/config.py` (depends on: T005, T013)
- [ ] T033 [US3] Implement picker filtering to a single `ComponentType` section, reusing the existing render/approve/configure code paths in `src/ui/tui.py` (depends on: T019, T032)

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Search (FR-007/FR-008 — not tied to a single prioritized story) and final validation

- [ ] T034 [P] Implement catalog search plus optional delegation to any `enabled` `skill_sources` entry's declared `search` command, tagging each result's origin (research.md §3) in `src/registry/catalog.py`
- [ ] T035 [P] Implement the search overlay: `tab` toggles into and out of it, results are labeled by origin, and any selection made there is reflected in the main list on return (FR-007, FR-008) in `src/ui/tui.py` (depends on: T034, T019)
- [ ] T036 [P] Integration test confirming search surfaces catalog and external-source results tagged by origin and that selections persist back to the main list in `tests/integration/test_search_and_select.py` (write first, must fail before T035 is considered complete)
- [ ] T037 [P] Execute every scenario in `quickstart.md` end-to-end and record pass/fail results in `specs/001-config-picker-tui/quickstart.md`
- [ ] T038 Review the implementation against the Constitution Check table in `plan.md` (core/ purity, registry-driven types, `mcpServers`-only settings scope) and correct any drift found, across `src/core/`, `src/ui/`, `src/commands/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational only
- **User Story 2 (Phase 4)**: Depends on Foundational; builds on the picker/apply/configure screens User Story 1 adds to `src/ui/tui.py`, so implement after Phase 3 even though it has no *data* dependency on US1
- **User Story 3 (Phase 5)**: Depends on Foundational; builds on the picker screen from Phase 3 the same way Phase 4 does
- **Polish (Phase 6)**: Depends on all desired user story phases being complete

### Within Each Phase

- Tests marked "write first, must fail" MUST exist and fail before their corresponding implementation task
- `src/core/models.py` and `src/registry/catalog.py` (T004, T005) before anything that imports them
- `core.plan` before `core.apply` before `core.pending`/`core.submit` (each layer's tests precede its implementation)
- Within `src/ui/tui.py`, tasks are edited in the listed order (same file — not parallelizable with each other, even where a story label is shared)

### Parallel Opportunities

- All Setup [P] tasks (T003) alongside T001/T002 once the directories exist
- T004, T005 in parallel (different files)
- T006, T008, T010, T012 are each independent test files and can be written in parallel once the models they assert against (T004) exist
- T013, T014 in parallel (different files, no shared dependency)
- Every story's "Tests for User Story N" block (e.g., T015+T016, or T024+T025+T026) can be written in parallel — each is its own file
- T034, T036, T037 in Polish can proceed in parallel with each other

---

## Parallel Example: Foundational Phase

```bash
# Launch T004 and T005 together (different files):
Task: "Define core data models and ComponentState in src/core/models.py"
Task: "Implement registry/catalog loader in src/registry/catalog.py"

# Once T004/T005 land, launch the four unit/contract test-writing tasks together:
Task: "Unit tests for core.plan in tests/unit/test_plan.py"
Task: "Unit tests for core.apply in tests/unit/test_apply.py"
Task: "Unit tests for core.pending/core.submit in tests/unit/test_configure.py"
Task: "Contract test for core interface in tests/contract/test_core_interface.py"
```

## Parallel Example: User Story 1 tests

```bash
Task: "Integration test for fresh-machine recommended flow in tests/integration/test_fresh_machine_setup.py"
Task: "Integration test for config-failure-doesn't-undo-install in tests/integration/test_config_failure_no_rollback.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (blocks everything else)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: run quickstart.md Scenarios 1 and 6 against the implementation
5. This is the smallest slice a real user could adopt: fresh machine → fully installed, configured baseline

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. Add User Story 1 → validate independently → this is the MVP
3. Add User Story 2 → validate independently → returning users can safely adjust their setup
4. Add User Story 3 → validate independently → scoped, focused runs become available
5. Polish (search + full quickstart pass) → the feature as specified is complete

## Notes

- [P] tasks touch different files and have no incomplete-task dependency
- [Story] labels map every Phase 3+ task back to spec.md's prioritized user stories
- Every "write first, must fail" test task must actually fail before its implementation task starts — this is not optional for T008/T010 (mutation paths) per the constitution, and is treated as equally load-bearing for the other test tasks since each anchors a story's independent-test requirement
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently before moving to the next
