<!--
Sync Impact Report
==================
Version change: [TEMPLATE] → 1.0.0 (initial ratification)
Modified principles: n/a (first fill of template placeholders)
Added sections:
  - Core Principles: I. Test-Before-Mutation, II. Core Has No Voice,
    III. Types Are Data Not Code, IV. Delegate Don't Rebuild, V. Sacred User Files
  - Catalog Integrity (Section 2)
  - Two-Repo Development Workflow (Section 3)
  - Governance
Removed sections: none
Templates requiring updates:
  - .specify/templates/plan-template.md — ✅ no changes needed (Constitution Check
    section already loads gates generically from this file)
  - .specify/templates/spec-template.md — ✅ no changes needed (no principle-specific
    references)
  - .specify/templates/tasks-template.md — ✅ updated: "Tests" note now carries the
    Test-Before-Mutation exception for file-mutating tasks
  - .claude/skills/speckit-*/SKILL.md — ✅ no changes needed (all load
    .specify/memory/constitution.md dynamically, no hardcoded principle names)
Follow-up TODOs: none
-->

# claude-kit Constitution
<!-- Product name "Base-Kit"; CLI binary and repo are both "claude-kit". -->

## Core Principles

### I. Test-Before-Mutation (NON-NEGOTIABLE)
Every operation that writes to a file the user owns — Claude Code settings, `installed.json`,
`CLAUDE.md`, or `env.d/` secrets — MUST be validated before it is applied and MUST run as a
transaction: snapshot current state → apply the change → health-check what changed → commit or
revert. Settings writes MUST go through a temp-file-then-atomic-swap so Claude Code is never left
with a broken config mid-write. A failed *config* step (e.g., a bad token) MUST NOT roll back a
completed *install*; the component stays pending so the user can retry.
Rationale: this tool is trusted with a live, org-wide Claude Code setup; a single bad write that
corrupts settings or leaves state inconsistent breaks trust in the whole rollout, and adoption
does not get a second chance.

### II. Core Has No Voice
`core/` MUST NOT print, prompt, or exit. Core functions take inputs and return objects only; all
rendering and user interaction lives in frontends (`commands/`, `ui/tui.py`, and any future
`web/`). One documented exception: a component's `config.sh` MAY inherit terminal stdio when the
underlying tool runs its own interactive login (e.g., `glab`) — even then, the installer itself
still never prints on its own behalf.
Rationale: this separation turns a future non-programmer GUI into a rendering exercise instead of
a rewrite — a web wizard would call the exact same core functions the TUI does.

### III. Types Are Data, Not Code
The list of manageable component types (skills, agents, plugins, tools, MCP servers, and any
future type) MUST be sourced from the registry's `types[]` array, never hardcoded into CLI logic.
Adding or changing a type MUST be achievable as a catalog edit alone, without a CLI release.
Rationale: keeps every component kind handled generically by one install → config → verify →
uninstall loop, instead of per-type special-casing that would force a binary release for every
catalog change.

### IV. Delegate, Don't Rebuild
When a dedicated tool already solves part of the problem, claude-kit MUST wrap or call it rather
than reimplement its function: skill/agent search and install delegate to ClawHub, binaries are
pre-installed from Artifactory rather than fetched at runtime, catalog curation and review live in
Git, and each managed tool keeps its own secrets in its own config.
Rationale: this is the recurring design instinct that keeps claude-kit small — and small is what
keeps it adoptable and supportable inside a restricted network.

### V. Sacred User Files
claude-kit MUST touch only the exact scope it owns and nothing more: the `mcpServers` block within
Claude Code settings, and exactly one `@genie-claude.md` reference line appended to the user's
`CLAUDE.md`. Everything else in those files MUST NOT be read, rewritten, or reordered. Secrets
MUST NOT be stored by claude-kit; `installed.json` records only a `"<set>"` marker, never a value.
Rationale: adoption is opt-in and trust-dependent — a tool that silently touches more than its
declared footprint teaches users to distrust it.

## Catalog Integrity

`registry.json` and every per-component script MUST pass a CI validation gate in the catalog repo
before merge: schema validation, hash recomputation for every entry in a component's `files` map,
and script lint/syntax checks. File hashes MUST be computed by CI, never written by hand, so
`installed_hash` comparisons reliably distinguish "outdated" from "locally modified." The CLI MUST
refuse to install a component whose `min_cli_version` exceeds the running CLI version, and MUST
instead direct the user to update the CLI first.

## Two-Repo Development Workflow

The system MUST remain split across two repositories with distinct responsibilities: the CLI
engine (Python, frozen to a standalone binary, published as an npm package to internal Artifactory
— never fetched by a postinstall script) and the catalog (Git, the content/curation source of
truth: `registry.json` plus per-component scripts). The whole system's install state MUST be
expressible as the diff between `registry.json` (what exists, one per org) and `installed.json`
(what this machine chose, one per machine) — no other source of truth is permitted for install
state.

## Governance

This constitution supersedes ad-hoc practice in both repositories. Amendments require a documented
rationale, an updated Sync Impact Report, and a version bump under semantic versioning: MAJOR for
backward-incompatible principle removal or redefinition, MINOR for a new principle or materially
expanded guidance, PATCH for clarification or wording. Every PR to either repository MUST verify
compliance with the principles above before merge; a deviation (e.g., a component type that cannot
be expressed as registry data) MUST be justified in the PR description or the PR MUST be rejected.

**Version**: 1.0.0 | **Ratified**: 2026-07-30 | **Last Amended**: 2026-07-30
