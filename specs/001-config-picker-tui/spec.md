# Feature Specification: Config Picker & Configure Flow

**Feature Branch**: `001-config-picker-tui`

**Created**: 2026-07-30

**Status**: Draft

**Input**: User description: "claude-kit config picker/TUI — the core end-to-end flow: picker → select → configure → approve & install, per overview/claude-kit-ux-walkthrough-v2.html."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - First-time setup lands a working baseline (Priority: P1)

A developer who just installed claude-kit on a fresh machine runs the config command for the
first time. Because nothing is installed yet, they're offered a choice between the org's
recommended set and a fully custom one. Either way, they land in one scrollable list covering
every component type, move through it, adjust anything they want, and reach a single approval
action at the end. Approving installs everything selected in one pass; anything that still needs
input (like a token) is then requested automatically, one item at a time, until nothing is left
pending.

**Why this priority**: This is the very first experience of the product for every new user. If it
doesn't work smoothly and inspire trust, there's no second chance at adoption — this is the
whole point of the tool.

**Independent Test**: Can be fully tested by running the config flow on a machine with no
managed components installed, choosing the recommended set, approving, and confirming that every
selected component ends up installed and — where it requires input — configured and verified,
with no manual follow-up command required.

**Acceptance Scenarios**:

1. **Given** no claude-kit-managed components are installed on this machine, **When** the config
   command is run, **Then** the user is asked to choose between a recommended pre-selected set
   and a fully custom one before anything else is shown.
2. **Given** the user chose the recommended set, **When** the picker opens, **Then** every
   recommended component across every declared type is already selected, and the user can still
   change any selection before approving.
3. **Given** the user is scrolling through the picker, **When** they reach the last row, **Then**
   it is a single "Approve & install" action, and nothing has been installed or removed up to
   that point.
4. **Given** the user approves the plan, **When** installation runs, **Then** every selected
   component is installed with no further input required from the user for components that need
   none.
5. **Given** a just-installed component requires configuration (e.g., an API token), **When**
   installation finishes, **Then** the user is automatically prompted for that component's inputs,
   with sensitive values masked as they're typed, and told when the component is verified working.
6. **Given** a component's configuration step fails (e.g., an invalid token), **When** the failure
   occurs, **Then** the already-completed install is not undone, and the component is reported as
   still pending so the user can retry later.

---

### User Story 2 - Returning user adjusts what's installed (Priority: P2)

Weeks later, the same developer runs the config command again. This time nothing is asked up
front — the picker opens straight away, pre-checked with exactly what's currently installed.
The developer adds one new item and unchecks one they no longer want. Unchecking an installed
item is clearly marked as a removal, not just a deselection, and stays visible as they keep
scrolling. Approving applies both the addition and the removal together.

**Why this priority**: This is the command developers will run repeatedly over the life of the
tool. Getting "what will change" to be obvious before anything happens is what keeps the tool
trustworthy over time, second only to the first-run experience.

**Independent Test**: Can be fully tested by opening the config command on a machine with an
existing set of installed components, selecting one new item, deselecting one installed item,
and confirming the approval screen and the resulting state both reflect exactly one install and
one removal — nothing else changes.

**Acceptance Scenarios**:

1. **Given** at least one claude-kit-managed component is already installed, **When** the config
   command is run, **Then** the picker opens directly with current installations pre-checked and
   no recommended/custom choice is shown.
2. **Given** the user unchecks a currently-installed component, **When** they continue scrolling,
   **Then** that row is visually flagged as a pending removal, distinct from rows that are
   unchanged or newly selected.
3. **Given** the user has both a new selection and a removal pending, **When** they reach the
   approval row, **Then** the count of pending removals is visible at the approval action itself,
   not only on the individual rows.
4. **Given** the user approves a plan containing a removal, **When** the run completes, **Then**
   the removed component no longer appears as installed in any later listing of state.
5. **Given** the user re-selects an already-installed, already-configured component without
   changing anything else, **When** they approve, **Then** the system treats it as a request to
   reconfigure that component rather than a no-op.
6. **Given** the user's selections after opening the picker match the current installed state
   exactly (no installs or removals pending), **When** they approve, **Then** the system skips
   straight to prompting for configuration of any components still pending from before, without
   presenting an "installing" step for zero changes.

---

### User Story 3 - Narrowing to a single component type (Priority: P3)

A developer only cares about, say, the org's blessed plugins today. Instead of scrolling past
skills, agents, tools, and MCP servers, they can invoke the same flow scoped to just one
component type declared by the catalog, and get the identical picker, approval, and configure
experience filtered to that type alone.

**Why this priority**: A convenience layer over Stories 1 and 2 — valuable for reducing friction
on focused tasks, but the tool is fully usable without it since the unscoped flow already covers
every type.

**Independent Test**: Can be fully tested by invoking the flow scoped to one declared component
type and confirming only that type's items appear, with selection, approval, and configuration
behaving identically to the unscoped flow.

**Acceptance Scenarios**:

1. **Given** the catalog declares a set of component types, **When** the user scopes the flow to
   one type, **Then** only components of that type are listed, using the same controls and the
   same single approval action.
2. **Given** a new component type is added to the catalog, **When** the user next scopes the flow
   to that new type by name, **Then** it works without requiring any change to the tool itself.
3. **Given** the user completes a scoped run, **When** they check overall state afterward, **Then**
   components of other types are unaffected.

---

### Edge Cases

- What happens when a user searches for a component and one or more matches also exist in an
  optional external source? Results from the org's own catalog and from the external source MUST
  both be selectable the same way, but visually distinguished by where each one comes from.
- What happens when a user selects a search result and then returns to the main list? The
  selection MUST already be reflected in the main list without the user having to find and
  re-select it there.
- What happens when the user quits (without approving) partway through the picker or the
  configure step? No installs, removals, or configuration changes MUST be applied, and anything
  already pending from before MUST remain exactly as it was.
- What happens when a component the user wants to remove has no defined way to fully uninstall
  itself? The user MUST still be able to mark it for removal, and MUST be told plainly, after the
  run, which parts were cleaned up and which were left in place.
- What happens when the same component type is requested for scoping but doesn't exist in the
  catalog? The user MUST get a clear error rather than an empty or broken screen.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST present every component type declared by the catalog as its own section
  within a single, unified selection list.
- **FR-002**: Each section MUST display a live count of how many of its items are currently
  selected.
- **FR-003**: System MUST pre-check every component already installed on the machine when the
  selection list opens.
- **FR-004**: Selecting a not-yet-installed component MUST mark it pending installation;
  unselecting an installed component MUST mark it pending removal. Both states MUST be visually
  distinguishable from unchanged rows before approval.
- **FR-005**: System MUST offer exactly one action that applies any change — presented as the
  final row of the selection list — and MUST NOT install or remove anything before that action is
  taken.
- **FR-006**: System MUST use one identical set of controls (move, select/toggle, enter search,
  quit) across the entire flow, with the same meaning on every screen.
- **FR-007**: System MUST provide a search mode reachable from, and returnable to, the main
  selection list, which queries the org catalog and, when configured, any optional external
  source — labeling results by their origin.
- **FR-008**: Any selection made while in search mode MUST be reflected in the main list when the
  user returns to it.
- **FR-009**: On first use — defined as no claude-kit-managed component being currently installed
  — system MUST offer a choice between a recommended pre-selected set and a fully custom
  selection before the selection list is shown. On every subsequent use, system MUST skip this
  choice and open the selection list directly.
- **FR-010**: After the approval action installs or removes components, system MUST automatically
  prompt, one at a time, for configuration inputs of every component that requires them, masking
  any input marked sensitive.
- **FR-011**: If the user's selections at approval time match the current installed state exactly
  (no pending installs or removals), system MUST skip the install/removal step and proceed
  directly to configuring any components still pending from a previous run.
- **FR-012**: System MUST support restricting the entire flow — selection, approval, and
  configuration — to a single catalog-declared component type, using identical behavior to the
  unscoped flow.
- **FR-013**: System MUST report, at the end of a run, a summary distinguishing what was
  installed, what was removed, what was configured, and what remains pending.
- **FR-014**: A configuration failure for one component MUST NOT undo that component's completed
  installation; the component MUST instead be left in a pending-configuration state.
- **FR-015**: System MUST let the user re-select an already-configured, already-installed
  component to redo its configuration, distinct from leaving it untouched.

### Key Entities

- **Component**: A single installable item (a skill, agent, plugin, tool, or MCP server). Carries
  a name, description, category, whether it's recommended, and its current state on this machine
  (not installed / installed / pending install / pending removal / pending configuration).
- **Component Type**: A category of component declared by the catalog (e.g., skills, agents,
  plugins, tools, MCP servers). The set of types is not fixed — it is whatever the catalog
  currently declares.
- **Selection Plan**: The difference between what the user has selected in the list and what is
  currently installed — the set of pending installs and pending removals that the approval action
  will act on.
- **Configuration Input**: A single piece of information a component needs from the user (e.g., a
  token), with a prompt to show and a flag for whether it should be masked.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time user goes from an empty setup to every recommended component fully
  installed and configured using a single approval action per run, with zero separate commands
  needed to finish configuration.
- **SC-002**: In 100% of runs, a user can see every pending install and pending removal before
  approving, with no change applied earlier in the flow.
- **SC-003**: A returning user changing their setup (adding and/or removing components) sees the
  result of exactly the changes they made — nothing they left untouched is altered.
- **SC-004**: Every component that requires configuration is presented to the user for that input
  automatically after install, with no additional command required to discover it needs input.
- **SC-005**: A user can narrow their view to a single component type and see only that type's
  items, with no items of other types appearing.
- **SC-006**: A user learns and uses the entire flow — selecting, searching, approving, and
  configuring — using one small set of controls that behave identically on every screen, without
  needing to consult documentation mid-flow.

## Assumptions

- Users are developers already comfortable with keyboard-driven terminal navigation (arrow keys,
  enter, standard toggles).
- The catalog (what components exist) is already available locally by the time this flow runs —
  fetching/updating the catalog itself is a separate concern from this feature.
- The safety mechanics of applying an install or removal (snapshotting, verifying, rolling back on
  failure) are governed elsewhere as a foundational guarantee this flow relies on, not something
  this flow itself needs to define.
- An optional external search source may or may not be configured; when absent, search covers only
  the org's own catalog.
- "Recommended" is decided by the current installed state, not by whether the user has ever run
  the tool before.
