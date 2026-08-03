# Feature Specification: claude-kit System — Component Manager for Claude Code

**Feature Branch**: `001-claude-kit-system`

**Created**: 2026-08-02

**Last Updated**: 2026-08-03 (Phase 2 refinement — lightweight inline TUI, installed-only `list`)

**Status**: Draft

**Input**: User description: "Define the complete, end-to-end system specification for 'claude-kit' covering the CLI Command Set, the Two-Step TUI, the Three JSON State engines, and installation lifecycles"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - First-Time Setup and Interactive Configuration (Priority: P1)

A developer who has just installed claude-kit runs it for the first time. The tool prepares their local environment, then walks them through an interactive, two-step picker-and-configure experience so they can browse everything available (skills, agents, plugins, tools, MCP servers), select what they want, and supply any required credentials — without hand-editing any configuration files.

**Why this priority**: This is the on-ramp for every other capability. Without a working first-run setup and interactive configuration flow, no developer can benefit from anything else claude-kit offers. It is the smallest slice that delivers complete, standalone value (a developer goes from nothing configured to a working, personalized Claude Code setup).

**Independent Test**: On a machine with no prior claude-kit state, run the initialization command followed by the interactive configuration flow, select a mix of components (including at least one that requires a credential), approve, and verify the selected components are active in Claude Code and any credential prompts were completed successfully — all without directly editing any JSON or markdown file by hand.

**Acceptance Scenarios**:

1. **Given** a developer has never run claude-kit before, **When** they run the initialization command, **Then** the tool confirms a valid Claude Code environment is present, creates the local directories and baseline files it needs, links its baseline guidance into the developer's existing project guidance file without altering the developer's own content, and immediately proceeds into the interactive configuration flow.
2. **Given** the interactive picker is open, **When** the developer scrolls through the single combined list of categories and toggles selections on and off, **Then** the running total of selected items per category updates live and the display never leaves the developer uncertain which items are currently selected.
3. **Given** the developer enters search mode from the picker, **When** they type a query, **Then** matching items from the catalog (and any configured external sources) are shown and any items the developer selects while searching are pinned to the top of the main list when they return to browsing.
4. **Given** the developer deselects a component that is currently active, **When** the list redraws, **Then** that component is visually flagged as a pending removal (e.g., highlighted) before the developer approves anything.
5. **Given** the developer has finished adjusting selections, **When** they choose "Approve & install," **Then** the tool applies every addition and removal in one pass and, for any newly selected component that needs input, immediately continues into a sequential configuration prompt.
6. **Given** the configuration prompt is asking for a sensitive value (such as an API key), **When** the developer types it, **Then** the value is masked on screen, stored only in a restricted local location, and never written in cleartext to the shared component-tracking file.
7. **Given** the developer presses the cancel/quit input at any point before approving, **When** the picker closes, **Then** no changes are made to the developer's installed components or settings.

---

### User Story 2 - Scripted Add and Remove for Automation (Priority: P2)

A developer (or a setup script / CI job) who already knows the exact name of a component wants to add or remove it in one command, without navigating any interactive screen, and wants a reliable success/failure signal.

**Why this priority**: Power users and automated environments need a fast, scriptable path that doesn't depend on an interactive terminal. This extends the value of Story 1 to non-interactive contexts (onboarding scripts, CI) but depends on the same underlying install/remove machinery, so it is ranked second.

**Independent Test**: From a terminal (or a non-interactive script), run the add command with a known component name and confirm the component becomes active; run the remove command for the same component and confirm it is fully uninstalled. Verify the command's exit code reflects success or failure so it can gate a script.

**Acceptance Scenarios**:

1. **Given** a developer knows the exact type and name of a catalog component, **When** they run the add command with that type and name, **Then** the component is installed without any interactive picker appearing, and the command reports clear success or failure.
2. **Given** the added component requires configuration inputs, **When** the add command finishes installing it, **Then** the developer is walked through the same sequential configuration prompts used in the interactive flow before the command exits.
3. **Given** a developer runs the remove command for an installed component, **When** the command completes, **Then** the component's files/registrations are gone and it no longer appears as active.
4. **Given** an add or remove operation fails for any reason (unknown name, failed script step, network failure), **When** the command exits, **Then** it exits with a non-zero status and a clear error message, and no partial, unlabeled state is left behind.

---

### User Story 3 - Keeping Installed Components in Sync (Priority: P3)

A developer wants their installed skills, agents, plugins, tools, and MCP servers to stay current with the latest catalog content without ever being interrupted by a prompt, and without losing credentials they already entered.

**Why this priority**: Sync/update is what keeps the value from Stories 1 and 2 fresh over time. It's ranked third because it operates on components that must already exist (installed via Story 1 or 2), and because its defining constraint (never block for input) is what makes it safe to run unattended in the background or in CI.

**Independent Test**: With at least one component already installed and configured, modify or advance the catalog content, run the update command, and verify installed content is refreshed, previously entered credentials are preserved and not re-prompted, and the command returns without ever waiting on terminal input.

**Acceptance Scenarios**:

1. **Given** a developer runs the update command, **When** it starts, **Then** it proceeds without any prompt or pause for user input at any point, from start to finish.
2. **Given** the catalog source has newer content than what is installed, **When** update runs, **Then** installed components are refreshed to match, while previously supplied credentials continue to work without being re-collected.
3. **Given** the installed CLI is older than the minimum version the catalog now requires, **When** update runs, **Then** the update halts before making changes and clearly tells the developer they must upgrade the tool itself before proceeding.
4. **Given** a refreshed component now requires a new input it didn't need before, **When** update completes, **Then** that component is marked as awaiting configuration and is called out in the run's summary, rather than the update stopping to ask for it.
5. **Given** a developer runs update twice in a row with no catalog changes in between, **When** the second run completes, **Then** the resulting local state is identical to after the first run (no duplicate entries, no drift).

---

### User Story 4 - Discovering Current State (Priority: P4)

A developer wants a single place to see everything they currently have installed via claude-kit: whether it's current, whether it's configured, and whether it's active — so they can decide what to remove or fix. Components they have never installed are not part of this view; that role stays with the interactive picker's browsing/search experience.

**Why this priority**: This is a read-only convenience that makes Stories 1–3 easier to use correctly, but the system delivers value without it (a developer could otherwise infer state from the interactive picker). It's ranked fourth as a supporting, non-blocking capability.

**Independent Test**: With a mix of installed components in various freshness/configuration states, plus at least one additional catalog component that has never been installed, run the list command and verify only the installed components appear, each showing its category, version status, configuration status, and active/inactive state, clearly and correctly.

**Acceptance Scenarios**:

1. **Given** a developer has a mix of installed components and additional components that exist in the catalog but were never installed, **When** they run the list command, **Then** only the installed components are shown, each with its category, whether the installed copy matches the latest catalog version, whether its configuration is complete or pending, and whether it is currently active.
2. **Given** a component's configuration is incomplete, **When** it appears in the list, **Then** it is clearly distinguishable from fully configured components.
3. **Given** a component exists in the catalog but has never been installed, **When** the developer runs the list command, **Then** that component does not appear in the output at all.

---

### User Story 5 - Passive Awareness of Updates at Session Start (Priority: P5)

A developer starts a normal Claude Code session and, without doing anything extra, sees a short, already-prepared note if there's something worth their attention (a newer CLI version, newer catalog content, or components still awaiting configuration) — without that check ever slowing down the start of their session.

**Why this priority**: This is a passive convenience layered on top of everything else; it improves discoverability of Stories 3 and 4 but the system is fully usable without it. It's ranked last because it depends on the other engines already existing and because its only hard requirement (never slow down startup) makes it a pure addition, not a dependency for anything else.

**Independent Test**: Trigger a background check while a newer catalog version and a pending configuration both exist, then start a new session and verify a single, already-rendered notice appears immediately (no noticeable delay) and is not repeated on the next session once already seen.

**Acceptance Scenarios**:

1. **Given** a background check has found a newer CLI version, newer catalog content, or pending configurations, **When** a new session starts, **Then** a single, pre-written notice describing what was found appears immediately, with no noticeable startup delay.
2. **Given** nothing has changed since the last background check, **When** a new session starts, **Then** no notice is shown.
3. **Given** a notice for a specific update has already been shown once, **When** subsequent sessions start with no new findings, **Then** that same notice is not shown again.
4. **Given** the background check is running, **When** a developer starts or uses a session at the same time, **Then** the developer experiences no interruption or slowdown from the check.

---

### Edge Cases

- What happens when the developer runs the interactive configuration flow while an add/remove command or a background check is already running?
- What happens when a component the developer wants to remove was never installed by claude-kit in the first place (e.g., it was placed there manually)?
- What happens when the catalog is unreachable (no network) during `update` or `check` — does the system report clear degraded status rather than failing silently or crashing?
- What happens when a required credential the developer already entered is no longer valid (e.g., a revoked key) and a downstream verification step fails?
- What happens when two components declare configuration inputs with the same name — are their stored answers kept separate?
- What happens when a developer's project guidance file already contains the baseline reference line — does initialization avoid adding a duplicate?
- What happens when the developer's shared settings file is missing entirely, or is not valid at all, when claude-kit tries to update only its managed section?
- What happens if a developer cancels out of the sequential configuration prompts partway through (some components configured, others not)?
- What happens when the same component name exists under two different types (e.g., a tool and an MCP server share a name)?
- What happens when disk space or file permissions prevent writing to the restricted local credential storage?
- What happens when the developer runs the list command and has zero installed components — is a clear, empty-state message shown rather than a blank or confusing output?

## Requirements *(mandatory)*

### Setup & Initialization

- **FR-001**: System MUST provide a first-run initialization action that verifies a valid Claude Code environment is present before making any changes, and MUST report clearly if it is not.
- **FR-002**: System MUST create all local directories and baseline files it depends on during initialization, and MUST be safe to run again later without creating duplicates or overwriting developer changes to those baseline files.
- **FR-003**: System MUST deploy its own baseline guidance content separately from the developer's personal project guidance file, and MUST reference the baseline from the developer's file via a single added line, only if that reference line is not already present.
- **FR-004**: System MUST NOT rewrite, reformat, or otherwise alter any existing content of the developer's personal project guidance file beyond adding the single reference line described in FR-003.
- **FR-005**: System MUST transition the developer directly into the interactive configuration flow immediately after a successful first-run initialization.

### Interactive Configuration (Two-Step Flow)

- **FR-006**: System MUST present a single, scrollable list covering every declared component category, showing a live count of current selections per category.
- **FR-007**: System MUST support keyboard navigation (moving the highlighted item up and down) and MUST toggle selection of the highlighted item using the `Enter` key; no other key (e.g., Space) toggles selection.
- **FR-008**: System MUST support cancelling out of the configuration flow at any point before approval, leaving no changes applied.
- **FR-009**: System MUST support a search mode entered and exited solely by pressing `Tab`, acting as a pure, immediate toggle between the main picker and search results — with no separate "exit search" button, row, or control of any kind — that lets the developer filter the combined catalog (and any configured external sources) by typed text.
- **FR-010**: System MUST pin any items selected while in search mode to the top of the main list once the developer returns to browsing.
- **FR-011**: System MUST visually flag any currently-active component that the developer deselects as a pending removal, distinct from a never-installed item.
- **FR-012**: System MUST offer a single, unambiguous final action ("Approve & Install") represented as a dedicated row at the bottom of the list, invoked only by navigating the highlight to that row and pressing `Enter`; this action applies every pending addition and removal from the current session in one pass. No other keyboard shortcut (e.g., a single-letter shortcut such as `a`) MAY trigger this action.
- **FR-013**: System MUST support narrowing the initial list to a single requested category when the developer specifies one, without hiding the ability to still act on other categories' existing state.
- **FR-014**: System MUST, immediately after approval, sequentially prompt the developer for any input a newly selected component requires, one component at a time.
- **FR-015**: System MUST mask on-screen entry of any input value marked sensitive (e.g., API keys, tokens) during configuration prompts.
- **FR-016**: System MUST store sensitive input values only in a restricted, developer-local location that is not part of the shared component-tracking record, and MUST record only a masked placeholder (never the real value) in that shared record.

### Scripted Add & Remove

- **FR-017**: System MUST provide a non-interactive way to install a single named component by specifying its category and exact name, without displaying the interactive picker.
- **FR-018**: System MUST provide a non-interactive way to remove a single named, installed component by specifying its category and exact name.
- **FR-019**: System MUST, when a component added via the scripted path requires configuration input, immediately continue into the same sequential configuration prompts used by the interactive flow.
- **FR-020**: System MUST exit with a non-zero status and a clear, actionable error message whenever a scripted add or remove operation fails for any reason.

### Update & Sync

- **FR-021**: System MUST perform the update action without ever pausing for, or requiring, interactive input at any point during the run.
- **FR-022**: System MUST refuse to apply an update whose catalog content declares a minimum tool version newer than the version currently running, and MUST clearly instruct the developer to upgrade the tool before proceeding, making no other changes in that run.
- **FR-023**: System MUST refresh already-installed components' content to match the current catalog during update while preserving previously supplied configuration inputs, without re-collecting them.
- **FR-024**: System MUST, when an update introduces a new required input for an already-installed component, mark that component's configuration as incomplete/pending and report it in the update's end-of-run summary, rather than pausing to collect it.
- **FR-025**: System MUST produce an identical resulting state when the update action is run multiple times consecutively against unchanged catalog content (no duplicate entries, no drift).

### Discovery (Listing State)

- **FR-026**: System MUST provide an action that displays only the components currently installed on the developer's machine — never the full catalog of available-but-not-installed components — along with, for each: its category, whether the installed copy is current relative to the latest catalog content, whether its configuration is complete or pending, and whether it is presently active.
- **FR-027**: System MUST visually distinguish components with incomplete/pending configuration from those that are fully configured within this view.

### Background Update Awareness

- **FR-028**: System MUST provide a background check action that runs without displaying interactive prompts, completes on its own, and requires no developer interaction.
- **FR-029**: System MUST have the background check compare local state against the latest available tool version and catalog content, and account for how many installed components currently have incomplete/pending configuration.
- **FR-030**: System MUST have the background check produce one ready-to-display notice summarizing anything worth the developer's attention, for instant, unprocessed display at the next session start.
- **FR-031**: System MUST NOT perform any slow or blocking operation (network access, synchronization, or waiting on another process) as part of displaying a session-start notice; only a fast local read of the most recently prepared notice is permitted at that moment.
- **FR-032**: System MUST avoid re-showing a notice for the same finding once the developer has already been shown it in a prior session, until something new is found.

### Installation Lifecycles

- **FR-033**: System MUST, for content-style components (skills and agents), install by copying the component's declared files into the developer's local skills or agents area, and MUST remove them by deleting exactly those copied files.
- **FR-034**: System MUST, for marketplace-style components (plugins), install and remove by delegating to the existing plugin installation and removal mechanism, without duplicating or re-implementing that mechanism.
- **FR-035**: System MUST, for script-style components (tools and MCP servers), follow this sequence when installing: run any declared install step, collect any required developer inputs, run a declared configuration step with those inputs, register any required server connection, then run a declared verification step to confirm the component works.
- **FR-036**: System MUST, for script-style components (tools and MCP servers), follow this sequence when removing: deregister any server connection first, run any declared removal step, delete any stored credentials for that component, then remove its tracking entry.
- **FR-037**: System MUST make every install and removal lifecycle safe to run again: repeating the same install or removal action on a component already in the target state MUST NOT create duplicate entries, duplicate file copies, duplicate server registrations, or errors that block the run.

### Data Integrity & Security

- **FR-038**: System MUST modify only the specific section of the developer's shared settings file that it owns (server connection entries), and MUST preserve every other key, value, and setting in that file exactly as it was, byte-for-byte.
- **FR-039**: System MUST never write a real secret/credential value into any shared, non-restricted tracking file; only a masked placeholder indicating "a value is set" may appear there.
- **FR-040**: System MUST NOT perform any self-update of the tool itself; the only permitted response to detecting a newer tool version is to notify the developer and name the exact external command they must run themselves to upgrade.
- **FR-041**: System MUST record, for every installed component, at minimum: where it came from (installed by claude-kit vs. pre-existing/manual), a way to detect whether its installed content has drifted from what was installed, and when it was installed or last touched.

### Resolution of Open Behaviors

- **FR-042**: When a script-style component's verification step fails after its server connection has already been registered in the developer's settings file, system MUST deregister that connection immediately, mark the component's status as failed (neither "done" nor silently absent), and report the failure clearly rather than leaving a registered-but-unverified connection in place.
- **FR-043**: When the developer tries to add or select a catalog component whose name matches an existing item that was not installed by claude-kit (i.e., placed there manually), system MUST refuse to overwrite it automatically and MUST clearly warn the developer of the naming collision, requiring an explicit, distinct confirmation before proceeding.
- **FR-044**: When `update` re-runs a verification step for an already-configured script-style component and that verification fails (e.g., a previously working credential is no longer valid), system MUST mark that component's configuration status as pending again and include it in the update's end-of-run summary, without pausing the update to collect a new value.

### TUI Presentation & Interaction (Phase 2 Refinement)

- **FR-045**: System MUST present the interactive configuration flow as a lightweight, inline experience within the developer's existing terminal scrollback — it MUST NOT take over the full terminal screen (no full-screen/alternate-screen app) and MUST NOT clear or hide the developer's existing scrollback buffer at any point during entry, use, or exit.
- **FR-046**: System MUST limit the interactive configuration flow's on-screen presentation to the picker list, current selections, and minimal status/help text; it MUST NOT display non-essential visual chrome such as decorative buttons, a theme-switcher, or other controls that do not directly support browsing, searching, selecting, or approving components.
- **FR-047**: System MUST render each item's selection state using a stable, always-visible marker distinguishing exactly three states: unselected (`[ ]`), selected (`[✓]`, rendered in a positive/affirming color such as green), and selected-for-removal (`[X]`, rendered in a warning color such as red) — and this marker MUST remain visible and unchanged in meaning as the highlighted row moves or focus shifts between the main list and search results.

### Key Entities

- **Component**: Anything a developer can add through claude-kit — a Skill, Agent, Plugin, Tool, or MCP Server. Each has a category, a description, a declared handler behavior (content copy, marketplace delegation, or scripted lifecycle), and, optionally, a list of inputs it requires from the developer.
- **Catalog**: The declarative, versioned source of truth for everything available to install — every component's metadata, file contents, required inputs, and compatibility requirements (including the minimum tool version needed to use it).
- **Installed Record**: The local, machine-readable ledger of what is actually installed on this developer's machine right now — per component, its origin (claude-kit vs. manually placed), whether its content matches what was last installed, its configuration status (complete or pending), and whether it is currently active.
- **Notification Snapshot**: The small, locally cached result of the most recent background check — a single ready-to-display message plus the underlying comparison details it was built from, and a record of which findings have already been shown to the developer.
- **Credential**: A sensitive input value (such as an API key) supplied by the developer for a specific component. Stored only in a restricted, developer-local location; never present in cleartext in any shared record.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer with no prior claude-kit state can go from first run to having at least one fully configured, active component, using only the interactive flow, in under 5 minutes.
- **SC-002**: Running any claude-kit action twice in a row with no other changes in between produces byte-identical local tracking state after the second run compared to after the first (zero duplicate entries observed across 100% of repeated-run tests).
- **SC-003**: Zero real credential values are ever found in the shared, non-restricted tracking file across all tested installs — 100% of recorded credential fields contain only the masked placeholder.
- **SC-004**: Starting a new session never takes perceptibly longer because of claude-kit's notification feature, regardless of whether a background check is in progress at that moment.
- **SC-005**: A developer can determine the freshness, configuration, and active status of any installed component in under 10 seconds using the discovery view, without opening any file directly, and without that view being cluttered by components they have never installed.
- **SC-006**: The update action never pauses for developer input in 100% of test runs, including runs where new configuration becomes required as a result of the update.
- **SC-007**: After any sequence of install, update, or remove actions, every setting and value in the developer's shared settings file that claude-kit does not own remains exactly as it was beforehand, verified byte-for-byte, in 100% of tested scenarios.
- **SC-008**: A developer's personal project guidance file retains 100% of its original content (aside from at most one added reference line) after any number of claude-kit runs.
- **SC-009**: A developer is never shown the same background-check finding more than once after having already seen it, across consecutive sessions with no new findings.
- **SC-010**: A developer's terminal scrollback content from before launching the interactive configuration flow is fully intact and scrollable-to immediately after the flow exits, in 100% of tested runs, and the flow never occupies the full terminal screen.

## Assumptions

- claude-kit operates on a single developer's local machine at a time; multi-user or shared-team catalog governance is out of scope for this specification.
- A working Claude Code installation and a reachable catalog source are prerequisites; claude-kit's own initialization only verifies their presence/reachability rather than installing them.
- The interactive configuration flow (picker and configuration prompts) requires a terminal capable of interactive rendering; the scripted add/remove and update/list/check actions are the supported path for non-interactive environments such as CI.
- "External skill sources" referenced during search mode are optional, developer-configured sources merged into search results; how any particular external source is configured is out of scope for this specification.
- The developer's shared settings file and personal project guidance file already exist in a recognizable, editable form prior to claude-kit's first run, or are created fresh by initialization if entirely absent.
- Upgrading the tool itself is always a manual, developer-initiated action performed through the developer's package manager; no in-app upgrade path is provided.
- Version and freshness comparisons (installed vs. catalog, local tool version vs. latest available) are based on explicit version/hash identifiers already present in the catalog and local tracking data, not on inferred or fuzzy comparisons.
