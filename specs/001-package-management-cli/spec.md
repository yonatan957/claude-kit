# Feature Specification: Claude Kit Package Management CLI

**Feature Branch**: `001-package-management-cli`

**Created**: 2026-08-10

**Status**: Draft

**Input**: User description: "reade the README.md and specify"

## Overview

Claude Kit (`ck`) is a command-line tool that gives a single, uniform way to discover, install, inspect, and remove the add-ons that extend Claude Code — skills, agents, MCP servers, tools, and plugins — regardless of which source they come from. Today a person who wants to extend Claude Code must know where each add-on lives, follow a different procedure for each one, and track by hand what they installed and whether it is current. Claude Kit removes that per-source knowledge: one search finds packages everywhere, one install command brings any of them in, and one status check tells the person what is out of date.

## Clarifications

### Session 2026-08-10

- Q: Which kinds of add-on count as a package? → A: Five kinds — skill, agent, MCP server, tool, and plugin — all treated identically by every command.
- Q: Does installation target the user-level `.claude` directory, a project-local one, or both? → A: User-level only; project-local installation is out of scope for this project.
- Q: When a package name exists in more than one source and no source is named, how is it resolved? → A: First source in the precedence order wins, silently, with `genie` first.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find and install a package by describing it (Priority: P1)

A person wants a capability for Claude Code but does not know whether it exists, what it is called, or where it is published. They search in plain words, read the results with enough context to choose (name, description, source, popularity), and install the one they picked with a single command. If the package needs configuration values, Claude Kit asks for them one at a time before installing, and states what each value will be used for.

**Why this priority**: This is the product's reason to exist. A person who can only search and install already gets the whole value proposition — everything else in this feature makes that loop safer and more repeatable.

**Independent Test**: With at least one registered source containing packages, run a search for a term, confirm relevant packages are listed with their source, then install one and confirm Claude Code can use it. No other command is needed.

**Acceptance Scenarios**:

1. **Given** at least one registered source, **When** the person searches for a term that matches packages, **Then** matching packages are listed with name, description, source, and popularity where the source provides it.
2. **Given** a search result the person wants, **When** they install it by name, **Then** the package is installed and reported as ready to use.
3. **Given** a package that requires configuration values, **When** the person installs it, **Then** they are prompted for each value one at a time, told what it will be used for and where it will be stored, and installation completes only after all values are supplied.
4. **Given** a package that is already installed, **When** the person installs it again without asking for an upgrade, **Then** they are told it is already installed and nothing on disk changes.
5. **Given** a package that is already installed, **When** the person installs it with the upgrade option, **Then** it is replaced with the newer version and the prior version can be restored.
6. **Given** more than one source, **When** the person installs a package without naming a source, **Then** Claude Kit uses the source precedence order and reports which source the package came from.
7. **Given** a named source, **When** the person installs with that source specified, **Then** only that source is consulted and the command fails with a clear message if the package is not there.
8. **Given** no source is reachable, **When** the person searches or installs, **Then** they are told which sources could not be reached and no partial installation is left behind.

---

### User Story 2 - Get a working environment from nothing (Priority: P2)

Someone on a new machine, with no Claude Code present, runs a single initialization command. Claude Kit installs Claude Code, then applies a recommended configuration it retrieves from the network — including the catalog of recommended packages that later searches and recommendations draw on. Anything that reaches outside Claude Kit's own files — running an installer, fetching over the network — is described to the person before it runs, and declining one of those steps leaves the rest of the setup valid rather than aborting everything.

**Why this priority**: It removes the largest single barrier to a first successful install, but a person who already has Claude Code can get full value from User Story 1 without it.

**Independent Test**: On a machine with no Claude Code and no Claude Kit configuration, run initialization and confirm that Claude Code is present, configuration is applied, and the recommended-package catalog is available locally.

**Acceptance Scenarios**:

1. **Given** a machine with no Claude Code installed, **When** the person initializes, **Then** Claude Code is installed and configuration retrieved over the network is applied.
2. **Given** Claude Code is already installed, **When** the person initializes, **Then** the existing installation is left intact and only missing configuration is added.
3. **Given** initialization has already been run once, **When** it is run again, **Then** the resulting state is identical to after the first run and nothing the person changed by hand is silently overwritten.
4. **Given** a step that runs an external installer or reaches the network, **When** initialization reaches it, **Then** the person is told what will run and what it will access before it executes.
5. **Given** the person declines such a step, **When** initialization continues, **Then** the remaining steps still complete and the environment is left in a usable state with the skipped step reported.

---

### User Story 3 - See what is installed and remove what is not needed (Priority: P3)

A person lists everything Claude Kit has installed locally, of a given kind, and sees for each one its name, description, and a short identifying tag. When two installed packages share a name, the tag is what tells them apart, and the person can uninstall a specific one by naming its tag.

**Why this priority**: Needed for confidence and cleanup over time, but a first-time user gets value before ever needing it.

**Independent Test**: Install two packages, list them, confirm each shows name, description, and tag, then uninstall one by name and confirm the other survives.

**Acceptance Scenarios**:

1. **Given** packages installed of a given kind, **When** the person lists that kind, **Then** each installed package is shown with name, description, and identifying tag.
2. **Given** no packages of a kind are installed, **When** the person lists that kind, **Then** an empty result is reported clearly rather than as an error.
3. **Given** exactly one installed package with a given name, **When** the person uninstalls by that name, **Then** it is removed and everything it added is reverted.
4. **Given** two installed packages sharing a name, **When** the person uninstalls by name alone, **Then** the command does not remove anything and asks them to disambiguate, listing the candidates and their tags.
5. **Given** two installed packages sharing a name, **When** the person uninstalls naming a specific tag, **Then** only that package is removed and the other is untouched.
6. **Given** a name that is not installed, **When** the person uninstalls it, **Then** they are told it is not installed and nothing changes.

---

### User Story 4 - Know what is out of date, and update deliberately (Priority: P4)

A person checks the versions of everything Claude Kit is responsible for — Claude Kit itself, Claude Code, and the catalog of recommended packages — and sees current versus latest available, recorded to a file that survives between runs. When they decide to act, a separate command performs the upgrades, and they can exclude any of the three parts from that upgrade.

**Why this priority**: Maintenance value that accrues after the tool is in use. Nothing in the first three stories depends on it.

**Independent Test**: With at least one component behind the latest available version, run the status check, confirm current and latest are both reported and recorded, then upgrade and confirm the recorded versions converge.

**Acceptance Scenarios**:

1. **Given** Claude Kit, Claude Code, and the catalog are installed, **When** the person checks status, **Then** current and latest-available versions are reported for each and written to a file that persists across runs.
2. **Given** a previous status check has been recorded, **When** the person checks status again, **Then** the recorded file reflects the newer result rather than accumulating duplicates.
3. **Given** version information cannot be retrieved for a component, **When** the person checks status, **Then** the reachable components are still reported and the unreachable one is marked unknown rather than failing the command.
4. **Given** components are behind, **When** the person upgrades, **Then** only components identified as behind are upgraded and each outcome is reported.
5. **Given** the person excludes a component from the upgrade, **When** the upgrade runs, **Then** that component is left at its current version and the others are still upgraded.
6. **Given** any other command is run, **When** it completes, **Then** Claude Kit has not upgraded or replaced itself as a side effect of that command.
7. **Given** an upgrade fails partway, **When** the person inspects the result, **Then** the affected component is either fully upgraded or fully at its prior version, never in between.

---

### Edge Cases

- The same package name exists in more than one source: sources are consulted in a fixed precedence order with the main registry first, so a bare install resolves deterministically and reports which source won. Naming a source overrides the order.
- A package is installed from one source and the same name later appears in another: the installed copy is identified by its tag, so both can coexist locally and be told apart in listings and uninstalls.
- Two locally installed packages produce the same identifying tag: the person is asked to disambiguate rather than Claude Kit guessing.
- The network is unavailable during search, install, status, or upgrade: the person is told which sources or version checks were unreachable, and no command leaves a half-applied change.
- The main registry has not been fetched yet when a recommendation search is run: the person is told the catalog is missing and how to obtain it.
- A person has hand-edited a file that a package also owns: the file is not silently overwritten; the person is told what would be lost and must confirm.
- An uninstall is run for a package whose files were removed by hand: the remaining record is cleared and the discrepancy is reported.
- A search returns no matches, or a very large number: an empty result is stated plainly, and large results are bounded so the output stays readable.
- Initialization is interrupted midway: re-running it completes the setup rather than producing a mixture of the two attempts.

## Requirements *(mandatory)*

### Functional Requirements

**Package discovery**

- **FR-001**: System MUST let a person search for packages of a chosen kind — skill, agent, MCP server, tool, or plugin — across all registered sources using free-text terms.
- **FR-002**: System MUST show, for each search result, its name, description, and originating source, plus a popularity indicator when the source supplies one.
- **FR-003**: System MUST support restricting a search to recommended packages only, drawn from the main registry's catalog.
- **FR-004**: System MUST report which sources were unreachable during a search while still returning results from the sources that responded.

**Installation**

- **FR-005**: Users MUST be able to install a package of a chosen kind by name.
- **FR-006**: System MUST let a person restrict an installation to a single named source, and MUST fail with a clear message if the package is not available there.
- **FR-007**: System MUST resolve a source-less installation using a fixed source precedence order, with the main registry first, and MUST report which source the package was taken from.
- **FR-008**: System MUST prompt for any configuration values a package requires, one value at a time, before performing the installation.
- **FR-009**: System MUST state, for each prompted value, what it will be used for and where it will be stored, and MUST NOT record credentials in logs or in any file that reports state.
- **FR-010**: System MUST support installing over an already-installed package on explicit request, and MUST otherwise leave an already-installed package untouched and say so.
- **FR-011**: System MUST leave no partially installed package behind when an installation fails or is interrupted.
- **FR-012**: System MUST NOT overwrite a file the person created or modified without telling them what would be lost and obtaining confirmation.
- **FR-013**: System MUST produce the same resulting state whether an install is run once or repeated.

**Inspection**

- **FR-014**: Users MUST be able to list all locally installed packages of a chosen kind.
- **FR-015**: System MUST show, for each installed package, its name, description, and a short identifying tag derived from the package's own content.
- **FR-016**: System MUST distinguish packages it installed from files the person owns.

**Removal**

- **FR-017**: Users MUST be able to uninstall a locally installed package by name.
- **FR-018**: System MUST accept an identifying tag alongside the name to select among same-named installed packages.
- **FR-019**: System MUST refuse to remove anything, and MUST list the candidates with their tags, when a name alone matches more than one installed package.
- **FR-020**: System MUST revert everything an installation added, so that uninstalling a just-installed package returns the environment to its prior state.

**Initialization**

- **FR-021**: System MUST install Claude Code during initialization when it is not already present, and MUST leave an existing installation intact when it is.
- **FR-022**: System MUST apply configuration retrieved over the network during initialization, including the catalog of recommended packages.
- **FR-023**: System MUST describe any step that runs an external program or reaches the network before that step executes, stating what will run and what it will access.
- **FR-024**: System MUST continue with the remaining initialization steps when the person declines such a step, and MUST report which steps were skipped.
- **FR-025**: System MUST produce the same resulting state whether initialization is run once or repeated.

**Status and upgrade**

- **FR-026**: System MUST report the installed and latest-available versions of Claude Kit, Claude Code, and the recommended-package catalog.
- **FR-027**: System MUST write the result of a status check to a file that persists between runs, replacing the previous result rather than appending to it.
- **FR-028**: System MUST mark a component's latest-available version as unknown, rather than failing, when that information cannot be retrieved.
- **FR-029**: System MUST upgrade only the components a status check identifies as behind, and MUST report the outcome for each.
- **FR-030**: Users MUST be able to exclude Claude Kit, Claude Code, or the catalog individually from an upgrade.
- **FR-031**: System MUST NOT upgrade or replace itself except as the direct result of the person invoking the upgrade command in that moment.
- **FR-032**: System MUST NOT let a version check block, delay past a bounded wait, or cause the failure of any command the person actually asked for.
- **FR-033**: System MUST leave each component either fully upgraded or fully at its prior version when an upgrade fails partway.

**Cross-cutting**

- **FR-034**: System MUST behave identically on Windows, macOS, and Linux, including how it locates and writes files.
- **FR-035**: System MUST report failures in terms of what the person can do next, and MUST distinguish "not found", "unreachable", and "refused" from one another.

### Key Entities

- **Package**: An installable unit of one kind — skill, agent, MCP server, tool, or plugin. Every kind carries the same attributes and is handled identically by search, install, list, and uninstall: a name, description, kind, the source it came from, an identifying tag derived from its own content, and any configuration values it requires at install time.
- **Source**: A place packages come from. Has a name used to select it explicitly and a position in the precedence order used when no source is named.
- **Main registry ("genie")**: The first-precedence source, held locally as a copy of a repository maintained by the Claude Kit team. Supplies the catalog that recommendation searches draw on. Its contents are not installed merely by being present locally.
- **Recommended-package catalog**: The list of packages the main registry recommends, retrieved over the network, versioned independently of Claude Kit and Claude Code, and upgradeable on its own.
- **Installed package record**: The local record of what a given installation placed on disk, sufficient to list it, tell it apart from a same-named sibling, and fully reverse it.
- **Version status record**: The persisted result of the most recent status check — installed and latest-available versions for Claude Kit, Claude Code, and the catalog.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A person who has never used Claude Kit goes from a machine with no Claude Code to a first working package installed in under 10 minutes, without consulting documentation beyond the tool's own output.
- **SC-002**: A person who knows only what a capability does, not its name or where it is published, finds and installs it in a single search plus a single install command in at least 90% of attempts.
- **SC-003**: Installing, listing, or removing a package requires the same command shape regardless of which source it came from — the person never needs source-specific knowledge except to override precedence deliberately.
- **SC-004**: Uninstalling a package returns the environment to a state indistinguishable from before it was installed, in 100% of cases where the person has not hand-edited that package's files.
- **SC-005**: Running any command twice in succession leaves the environment in the same state as running it once, in 100% of cases.
- **SC-006**: No command reports success while having applied only part of its changes.
- **SC-007**: A person can determine which of Claude Kit, Claude Code, and the catalog are out of date in a single command, and their answer survives a restart.
- **SC-008**: Claude Kit never replaces its own version except during a run the person started for that purpose — verified across every other command.
- **SC-009**: A person is never surprised by an external program running or a credential being requested: every such step is announced before it happens, in 100% of cases.
- **SC-010**: A failed command tells the person which of "not found", "unreachable", or "refused" occurred, in 100% of failures.
- **SC-011**: Search results are returned quickly enough that the person does not perceive a wait when sources are reachable, and an unreachable source never extends the wait beyond a bounded timeout.
- **SC-012**: Every command behaves the same on Windows, macOS, and Linux, verified on all three.

## Assumptions

- **Package kinds are exactly five**: skill, agent, MCP server, tool, and plugin (clarified 2026-08-10). No kind is privileged — each is selectable wherever a kind is named, and each behaves the same under search, install, list, and uninstall.
- **Installation targets the person's user-level Claude Code configuration** (their home-directory `.claude`), not a project-local one (clarified 2026-08-10).
- **Only one source exists at launch** — the main registry, named `genie`. The commands are specified so that additional sources need no change to their shape, but no second source ships with this feature.
- **The main registry is held locally as a copy of a repository**, and its presence on disk does not mean its packages are installed.
- **The identifying tag is the first four characters of a hash of the installed package's own content**, as stated in the README. Collisions are handled by asking the person to disambiguate.
- **Popularity in search results is optional** and shown only for sources that publish it.
- **Search is text matching over package names and descriptions**; ranking quality beyond relevance ordering is not specified here.
- **Configuration values collected at install time may include credentials**, so the consent and non-logging requirements above apply to them.
- **Claude Code is installable non-interactively** on all three supported platforms, which initialization depends on.
- **Network access is available** for initialization, search, status, and upgrade; every command states clearly when it is not, and no command corrupts local state because of it.
- **Version identifiers for Claude Kit, Claude Code, and the catalog are independently comparable**, so each can be reported and upgraded on its own.

## Out of Scope

- Publishing, authoring, or submitting packages to any source.
- Any graphical or web interface; this feature is command-line only.
- Managing Claude Code settings unrelated to installed packages.
- Project-local (repository-scoped) installation targets.
- Additional registries beyond the main registry, and any source-registration workflow.
- Dependency resolution between packages, if packages ever declare dependencies on one another.
