# Phase 0 Research: Config Picker & Configure Flow

## 1. Picker rendering: `prompt_toolkit` direct vs. `Textual`

**Decision**: Build the picker, search overlay, and configure wizard directly on `prompt_toolkit`
(`Application`, `Layout`, `HSplit`/`VSplit`, `KeyBindings`), not `questionary` and not `Textual`.

**Rationale**: The UX walkthrough (`overview/claude-kit-ux-walkthrough-v2.html`, §2 build note)
explicitly flags this as an open decision that must be made before implementation, since it's "the
difference between a day and a week" and only affects `ui/tui.py` — `core/` is unaffected either
way, so the choice is low-risk to the rest of the design. `claude-kit.md` already commits the
project's dependency stack to `typer`, `rich`, and `prompt_toolkit`; choosing `prompt_toolkit`
direct keeps the implementation inside the already-declared stack (Constitution IV — Delegate,
Don't Rebuild: use the dedicated tool already chosen rather than introduce a second, competing UI
framework) and gives full control over the exact layout primitives the picker needs — section
headers with live counters, a sticky one-line footer, and a toggleable search overlay — all of
which are directly expressible as `prompt_toolkit` `Window`/`FormattedTextControl` panes without
fighting a higher-level widget framework's own list/table components.

**Alternatives considered**:
- **`questionary`** (rejected) — it's the friendlier layer already used elsewhere in the org
  tooling, but it wraps `prompt_toolkit` precisely to simplify single-purpose prompts; it has no
  built-in support for grouped sections with independent live counters, a persistent footer, or an
  in-place search-mode toggle, so building this picker on top of it would mean fighting or
  monkey-patching its abstractions rather than using them.
- **`Textual`** (rejected, not disqualified) — a capable, modern TUI framework that could build
  this screen faster in isolation (built-in widgets for lists, live-updating labels, and overlays).
  It was set aside because it is not part of the stack already declared for this project, adding
  it means a second interactive-UI dependency alongside `prompt_toolkit` (which other parts of the
  CLI, e.g. `config.sh` terminal handoff, already assume is present), and `prompt_toolkit`'s lower-
  level primitives are sufficient for the exact set of behaviors this screen needs. If a future
  feature needs substantially richer TUI capability, revisit this decision then rather than
  carrying two TUI frameworks for one screen's sake now.

## 2. Transaction mechanics for approval (install/removal safety)

**Decision**: This feature calls into a transaction primitive (snapshot → apply → health-check →
commit-or-revert) rather than defining one. The primitive itself — how a snapshot is taken, how a
settings temp-file swap is made atomic, how a partial failure is rolled back — belongs to a
separate, lower-level feature (the install/removal transaction engine) that this flow depends on
via `core.apply(plan) -> list[ApplyResult]`.

**Rationale**: Keeping this boundary explicit matches the spec's own scoping (see spec.md
Assumptions) and avoids this feature's plan re-deriving mutation-safety mechanics that Constitution
Principle I already governs independently. `core.apply` is treated here as a dependency with a
known contract (see `contracts/core-interface.md`), not as something this plan designs from
scratch.

**Alternatives considered**: Designing the transaction mechanics inline as part of this feature
was considered and rejected — it would duplicate work that belongs to (and should be tested
independently from) the transaction-engine feature, and would make this plan responsible for a
constitutional guarantee (Test-Before-Mutation) that applies to every mutating feature, not just
this one.

## 3. Search across optional external sources

**Decision**: Search queries the local catalog directly (in-process, reading the already-loaded
registry) and, only if a `skill_sources` entry is both declared and `enabled` in the registry,
additionally shells out to that source's declared `search` command and merges results, tagged by
origin.

**Rationale**: This mirrors the registry-driven design already established for `skill_sources` in
`registry.json` (each source declares its own `search`/`install`/`uninstall`/`update` commands) —
the picker's search overlay does not need to know anything about a specific external tool (e.g.
ClawHub); it only needs to know how to invoke whatever `enabled` sources the registry lists and
render their results with an origin tag. This is consistent with Constitution IV (Delegate, Don't
Rebuild).

**Alternatives considered**: Hardcoding a ClawHub integration was rejected — the registry already
models external sources as pluggable, and the current registry example ships `clawhub` with
`enabled: false`, confirming this must degrade gracefully to catalog-only search with zero special
casing.

## Outstanding NEEDS CLARIFICATION markers

None. All unknowns identified in the Technical Context have a resolved decision above.
