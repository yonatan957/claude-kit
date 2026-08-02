<!--
Sync Impact Report
Version change: [TEMPLATE] → 1.0.0 (initial ratification)
Modified principles: n/a (first concrete adoption; all placeholders replaced)
Added sections:
  - Core Principles I–V (Strict Architectural Separation; Non-Interactive and
    Uninterrupted Updates; User-Controlled Upgrades; Strict Idempotency;
    Fast-Path Session Startup Hook)
  - Additional Constraints (artifact/naming conventions)
  - Development Workflow (compliance review gates)
  - Governance (amendment procedure, versioning policy, compliance review)
Removed sections: none (template placeholders only)
Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ no change needed — its
    "Constitution Check" section already defers dynamically to this file
  - .specify/templates/spec-template.md: ✅ no change needed — no
    principle-specific structural requirements introduced
  - .specify/templates/tasks-template.md: ✅ no change needed — task
    categories (Setup/Foundational/User Story/Polish) remain compatible;
    idempotency/separation/no-self-upgrade concerns are enforced at review
    time per the Development Workflow section below, not via new task types
  - .claude/skills/speckit-*/SKILL.md: ✅ reviewed, no outdated
    agent-specific or CLAUDE-only references found requiring generic-ization
  - README.md / docs/quickstart.md: ⚠ pending — neither file exists yet in
    this greenfield repository; create them to reference these principles
    when the corresponding code (core/, installers/, commands/,
    claude-kit-notify) is first scaffolded
Follow-up TODOs: none blocking; see ⚠ item above for future documentation work
-->

# claude-kit Constitution

## Core Principles

### I. Strict Architectural Separation (Core vs. Frontend)

The core engine (`core/`) and installation routines (`installers/`) MUST remain
pure and free of any direct human I/O. Core and installer modules MUST NOT
write directly to stdout/stderr, prompt the user for input, or call system
exits (`exit`). All user interaction — console printing, CLI prompts, menu
rendering — MUST live exclusively in the frontend/command layer (`commands/`,
`ui/tui.py`, or future UI wrappers). Core functions MUST communicate only by
returning clean data structures or raising typed exceptions.

**Rationale**: Keeping I/O out of the core guarantees the engine is testable
in isolation, reusable across multiple frontends (CLI, TUI, future UIs), and
never silently terminates a host process it doesn't own.

### II. Non-Interactive and Uninterrupted Updates

The update command (`claude-kit update`) MUST never block, prompt, or require
real-time interactive input. If an update introduces a component that needs
user configuration, that component's status MUST be flagged as `"pending"` in
the local state lockfile (`installed.json`), allowing the update to complete
and report pending tasks in the terminal output summary at the end of the run.

**Rationale**: Updates frequently run unattended (CI, scripts, automation);
an update that can hang on a prompt is an update that can silently break a
pipeline.

### III. User-Controlled Upgrades (No Self-Upgrades)

The CLI MUST NOT upgrade itself automatically. It MUST only perform light
version checks and notify the user when a newer CLI version exists on the
registry. Upgrading the CLI itself MUST always remain an explicit,
user-initiated action performed externally via npm (e.g.,
`npm install -g claude-kit@latest`).

**Rationale**: Self-upgrading CLIs can silently change behavior underneath a
running environment or CI pipeline; the user must retain full control over
when and how the tool itself changes.

### IV. Strict Idempotency

All CLI commands and installation/configuration operations MUST be completely
idempotent. Running any command or script multiple times consecutively MUST
be safe and MUST NOT produce duplicate entries, redundant configuration, or
unstable system states.

**Rationale**: Installers and config operations are re-run often (retries,
re-provisioning, CI re-runs); non-idempotent behavior compounds into corrupt
local state that is hard to diagnose.

### V. Fast-Path Session Startup Hook (Instant Boot)

The startup hook (`claude-kit-notify` plugin) executed on Claude Code session
start MUST be instantaneous, so it introduces no delay into the developer's
shell environment. The hook MUST NOT initiate synchronous network checks,
git operations, or wait on slow subprocesses. On session start, the hook MUST
only perform a fast local read of a cached notice file (`state.json`) and
print its contents verbatim. Any active network checking or catalog fetching
MUST be executed asynchronously in a fully detached, background subprocess
(`claude-kit check`), which refreshes `state.json` for the next session.

**Rationale**: A startup hook sits on the critical path of every session
launch; any synchronous slow call there is felt by every developer, every
time, regardless of whether they need fresh data that instant.

## Additional Constraints

The following artifact and naming conventions are established by the
principles above and MUST be followed consistently:

- `core/` and `installers/` — I/O-free engine and installation logic (Principle I).
- `commands/`, `ui/tui.py` — the only locations permitted to perform console
  I/O, prompts, or menu rendering (Principle I).
- `installed.json` — local state lockfile recording installed component
  status, including `"pending"` flags for components awaiting user
  configuration (Principle II).
- `state.json` — locally cached notice file read verbatim by the startup
  hook; refreshed only by the detached background process (Principle V).
- `claude-kit check` — the detached, asynchronous background subprocess
  responsible for network/catalog checks and refreshing `state.json`
  (Principle V).
- `claude-kit-notify` — the session-start plugin bound by the instant-boot
  constraint (Principle V).

## Development Workflow

Every pull request and code review MUST verify compliance with the Core
Principles before merge:

- Changes to `core/` or `installers/` MUST be checked for any added
  stdout/stderr writes, input prompts, or `exit` calls; such changes MUST be
  rejected or moved into the frontend/command layer.
- Changes to `claude-kit update` MUST be checked for any new blocking or
  interactive behavior; components needing configuration MUST be wired to
  the `"pending"` flag in `installed.json` instead.
- Any code that triggers a CLI self-upgrade MUST be rejected; version checks
  MUST remain notify-only.
- New or modified install/config operations MUST be exercised by running the
  same command/script consecutively (at minimum twice) to confirm idempotent
  behavior before merge.
- Changes to the `claude-kit-notify` startup hook MUST be checked for any new
  synchronous network, git, or subprocess-blocking call; such work MUST be
  moved into the detached `claude-kit check` subprocess.

Complexity or deviation from these gates MUST be explicitly justified in the
pull request description; unjustified deviations MUST block merge.

## Governance

This constitution supersedes all other project practices, conventions, and
prior informal agreements. Amendments are made by editing this file via the
`/speckit-constitution` workflow, which MUST regenerate the Sync Impact
Report and check dependent templates (plan, spec, tasks) and command/skill
files for required updates as part of the same change.

Versioning follows semantic versioning:

- **MAJOR** — backward-incompatible governance changes, or removal/redefinition
  of an existing principle.
- **MINOR** — a new principle or materially expanded guidance is added.
- **PATCH** — clarifications, wording, or non-semantic refinements.

All pull requests and code reviews MUST verify compliance with the Core
Principles and the Development Workflow gates above. Any complexity that
appears to conflict with a principle MUST be justified in writing in the PR
description or rejected.

**Version**: 1.0.0 | **Ratified**: 2026-08-02 | **Last Amended**: 2026-08-02
