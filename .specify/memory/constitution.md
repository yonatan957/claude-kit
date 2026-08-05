<!--
Sync Impact Report
==================
Version change: (unfilled template) → 1.0.0
Bump rationale: First concrete ratification. All placeholder tokens replaced with
binding governance; no prior version existed to be incompatible with.

Modified principles:
  - [PRINCIPLE_1_NAME] → I. Test-First (NON-NEGOTIABLE)
  - [PRINCIPLE_2_NAME] → II. Idempotent, Reversible Installation
  - [PRINCIPLE_3_NAME] → III. 100-Line File Ceiling
  - [PRINCIPLE_4_NAME] → IV. No Self-Update Without User Attention
  - [PRINCIPLE_5_NAME] → V. Consent-Gated Installation I/O

Added sections:
  - Distribution & Packaging Constraints (was [SECTION_2_NAME])
  - Development Workflow & Quality Gates (was [SECTION_3_NAME])

Removed sections: none

Templates requiring updates:
  ✅ .specify/templates/plan-template.md — Constitution Check gates filled in
  ✅ .specify/templates/tasks-template.md — tests promoted from OPTIONAL to REQUIRED
  ✅ .specify/templates/spec-template.md — reviewed, no constitution-driven change needed
  ✅ .claude/skills/speckit-tasks/SKILL.md — "Tests are OPTIONAL" line reconciled with Principle I
  ✅ README.md — reviewed, contains no principle references

Follow-up TODOs: none
-->

# claude-kit Constitution

claude-kit is a command-line tool that installs and updates Claude Code configuration —
Skills, Agents, Plugins, MCP servers, and guidance files — into a user's `~/.claude`
directory and into project-local `.claude` directories.

## Core Principles

### I. Test-First (NON-NEGOTIABLE)

TDD is mandatory. For every behavioral change the order is: write the test → observe it
fail for the right reason → write the minimum code that makes it pass → refactor.
Implementation code MUST NOT be committed ahead of a test that exercises it. A test that
has never been observed failing does not count as a test. Every command claude-kit exposes
MUST have at least one test that runs it end to end against a temporary HOME directory,
never against the developer's real `~/.claude`.

Rationale: this tool writes to directories users cannot easily reconstruct by hand. A
regression here silently corrupts a working environment, so the failing test is the only
acceptable proof that a fix addresses the reported defect.

### II. Idempotent, Reversible Installation

Every install, update, and uninstall operation MUST be safe to run any number of times:
running it twice produces the same filesystem state as running it once. Before overwriting
or deleting any file claude-kit did not create in this run, the tool MUST record enough
state to restore the prior content, and MUST expose a way to roll the operation back.
Files owned by claude-kit MUST be distinguishable from files owned by the user — by
manifest, by header, or by both — and user-owned files MUST NOT be silently clobbered.
Any operation that cannot be made reversible MUST refuse to run without an explicit
confirmation naming what will be lost.

Rationale: users invoke `claude-kit update` habitually and often unattended. Partial or
non-repeatable writes leave an environment that is neither the old one nor the new one.

### III. 100-Line File Ceiling

Every Python source file MUST contain at most 100 lines of code, counting only lines that
are neither blank nor comment-only. This is enforced by an automated check in CI; the check
is the authority, not a reviewer's judgment. A file approaching the ceiling MUST be split
along a real seam — a distinct responsibility — and MUST NOT be split by mechanically
moving lines into a helper module that has no independent meaning. Generated files and
vendored third-party code are exempt and MUST be listed explicitly in the check's
configuration.

Rationale: a hard ceiling forces decomposition to happen continuously rather than during a
large refactor, and keeps each unit small enough to hold in view while reading it.

### IV. No Self-Update Without User Attention

claude-kit MUST NOT modify, replace, or re-execute its own binary without a user action
taken in that moment. Background self-update, update-on-launch, and update-as-a-side-effect
of another command are all prohibited. The tool MAY check for a newer version and report
it; performing the upgrade requires an explicit, separate invocation. Version checks MUST
be skippable, MUST NOT block the requested command, and MUST NOT be the reason a command
fails.

Rationale: a tool that rewrites the user's environment must never also rewrite itself
unobserved, or the user loses the ability to say which version produced the state they are
looking at.

### V. Consent-Gated Installation I/O

Installation steps that reach outside claude-kit's own filesystem writes — running a
third-party installer, invoking a package manager, opening a network connection, or reading
or storing credentials, tokens, or API keys — MUST be isolated from the rest of the install
and MUST be presented to the user before they execute. The prompt MUST state what will run,
what it will access, and what will be stored where. Declining a gated step MUST leave the
remaining installation in a valid state; it MUST NOT abort the whole run. Credentials MUST
NOT be written to logs, telemetry, manifests, or state files, and MUST NOT be passed on a
command line where another process can read them.

Rationale: users are consenting to configuration management, not to arbitrary code
execution or credential handling. Bundling the two makes informed consent impossible.

## Distribution & Packaging Constraints

claude-kit is implemented in Python and distributed as a compiled standalone binary
published to npm. The following constraints are binding:

- Python is the only implementation language for the tool's logic. Shell and JavaScript are
  permitted only as thin wrappers at the packaging boundary.
- The published npm artifact MUST NOT require the end user to have a Python interpreter,
  a virtual environment, or `pip` available.
- Every published version MUST be reproducible from a tagged commit: the same tag builds a
  binary with the same behavior.
- Releases follow semantic versioning. A change that alters the on-disk layout claude-kit
  manages, or that breaks an existing installation's ability to be updated in place, is a
  MAJOR change and MUST ship with a documented migration path.
- The binary MUST run on Windows, macOS, and Linux. Path handling, shell invocation, and
  line endings MUST NOT assume a POSIX environment.

## Development Workflow & Quality Gates

- Feature work follows the Spec Kit flow: `/speckit-specify` → `/speckit-plan` →
  `/speckit-tasks` → `/speckit-implement`. Plans MUST pass the Constitution Check gate
  before research begins and again after design.
- CI MUST fail on any of: a failing test, a Python file exceeding the 100-line ceiling, a
  test suite that writes outside its temporary sandbox.
- Every pull request MUST state which principles its changes touch and how compliance was
  verified. "No principle applies" is an acceptable answer when true.
- Any deviation from a principle MUST be recorded in the plan's Complexity Tracking table
  with the simpler alternative that was rejected and why. An undocumented deviation is a
  defect regardless of whether the code works.

## Governance

This constitution supersedes all other development practices in this repository. Where a
README, template, skill file, or habit conflicts with it, this document wins and the
conflicting artifact MUST be corrected.

Amendments require: a written statement of the change and its rationale, a version bump
under the policy below, and propagation to every dependent artifact in the same change set
— at minimum `.specify/templates/plan-template.md`, `.specify/templates/spec-template.md`,
`.specify/templates/tasks-template.md`, and the installed `speckit-*` skill files.

Versioning policy for this document:

- MAJOR: a principle is removed or redefined in a way that invalidates existing compliance.
- MINOR: a principle or section is added, or existing guidance is materially expanded.
- PATCH: clarification, wording, or typo fixes that do not change what compliance means.

Compliance review: the Constitution Check gate in every plan is the routine enforcement
point. Principles I, II, and III are additionally machine-checked in CI. Principles IV and
V are reviewed by a human on every pull request that touches update logic, installer
invocation, or credential handling.

**Version**: 1.0.0 | **Ratified**: 2026-08-05 | **Last Amended**: 2026-08-05
