# Contract: `core/` ↔ frontend interface

This is the interface Constitution Principle II (Core Has No Voice) requires: `core/` exposes
only input→object functions, never prints/prompts/exits, and every frontend — `ui/tui.py` today,
a future `web/` — MUST drive the entire config-picker feature through exactly these four calls.
Shapes referenced below (`Component`, `SelectionPlan`, `ConfigStep`, `ApplyResult`,
`VerifyResult`) are defined in `data-model.md`.

## `core.plan(state, registry, selections) -> SelectionPlan`

**Purpose**: Pure diff of the user's in-progress selections against installed state. Drives the
picker's live section counters and pending-removal flags (FR-002, FR-004). Called on every
selection toggle — MUST have no side effects.

- **Input**: `state` (current `installed.json` contents), `registry` (current catalog contents),
  `selections` (the set of component keys currently checked in the UI, across all types)
- **Output**: `SelectionPlan` — see data-model.md. `is_noop=true` when `selections` matches
  `state` exactly, which the frontend uses to implement FR-011 (skip install step, go straight to
  configure).
- **Never**: prints, prompts, raises for "no changes" (that's a valid, common result).

## `core.apply(plan: SelectionPlan, registry: dict, ctx: ApplyContext) -> list[ApplyResult]`

**Purpose**: What the single "Approve & install" action calls (FR-005). Performs installs then
removals as transactions (snapshot → apply → health-check → commit/revert per Constitution
Principle I) via `src/core/transaction.py`.

- **Input**: the `SelectionPlan` produced by the most recent `core.plan` call; `registry` (to look
  up each component's install mechanism — scripts, marketplace commands, file lists); `ctx` (an
  `ApplyContext` bundling `installed_path`/`installed` plus pluggable `install_component` /
  `remove_component` callables — the default implementations run the registry-declared
  `install.sh`/`uninstall.sh`). *Refinement made during implementation*: the original draft of
  this contract took only `plan`, but the install/removal mechanism cannot act without registry
  and state access, so both were added — `core/` is still pure with respect to I/O it doesn't
  declare (no printing/prompting), it just needs these inputs to do its one stated job.
- **Output**: one `ApplyResult` per component acted on, in the fixed dependency order (tools →
  plugins → the rest, per the UX walkthrough) — never partial silence; every attempted component
  gets a result, `ok: false` included. A component with no declared `uninstall.sh` still gets
  `ok: true` with a `detail` explaining what was left in place (edge case).
- **Never**: prompts for input (components needing input become pending, surfaced separately by
  `core.pending` — they are not requested mid-`apply`).

## `ApplyContext`

Bundles what `core.apply` needs beyond the plan: `installed_path: Path`, `installed: dict` (the
in-memory `installed.json` contents it mutates and persists), and the two pluggable action
callables above. This is the seam frontends/tests use to inject fakes without touching the
filesystem or a real catalog.

## `core.pending(state, registry) -> list[ConfigStep]`

**Purpose**: What components need configuration right now, and what to ask for each (FR-010).
Called immediately after `apply`, and also stands alone so `config` can jump straight to
configuration when `core.plan` returned `is_noop=true` (FR-011).

- **Input**: `state`, `registry`
- **Output**: ordered list of `ConfigStep`, each carrying its `inputs` (with `sensitive` flags the
  frontend MUST use to mask input) and a `reason` (FR-015: `newly_installed` vs.
  `user_requested_reconfigure` render identically)
- **Never**: prints, prompts — the frontend collects `answers` and passes them to `submit`.

## `core.submit(step: ConfigStep, answers: dict, ctx: SubmitContext) -> VerifyResult`

**Purpose**: Runs the component's `config.sh` with `answers` as env vars, then its `verify.sh`,
and returns the outcome (FR-014). One call per component in the configure wizard.

- **Input**: the `ConfigStep` being completed, `answers` keyed by each `ConfigurationInput.name`,
  and `ctx` (a `SubmitContext` bundling `installed_path`/`installed`/`registry` plus pluggable
  `run_config`/`run_verify` callables) — added for the same reason as `ApplyContext` above.
- **Output**: `VerifyResult` — on failure (either `config.sh` or `verify.sh`), the component's
  install is untouched and it remains `PENDING_CONFIGURATION` for the next `core.pending` call
  (FR-014); the frontend reports the failure and lets the user retry without restarting the whole
  flow.
- **Never**: prompts for retry, prints progress — the frontend renders `VerifyResult` and decides
  what to show next (e.g., re-invoking the configure step for that same component).

## `core.configure.request_reconfigure(state, type_name, name)`

**Purpose**: What the frontend calls when a user re-selects an already-`CONFIGURED` component
(FR-015). Flips that component's `config.status` back to `"pending"` while preserving
`verified_at`, so the next `core.pending` call reports it with `reason:
user_requested_reconfigure` instead of `newly_installed` — both render identically in the wizard.

## What is explicitly out of contract here

- Catalog sync/version comparison (`update`'s concern) — this feature only reads whatever
  `registry`/`state` it's handed.
- The exact snapshot/rollback mechanics inside `core.apply` — governed by Constitution Principle I
  as a cross-cutting guarantee, not owned by this feature.
- Search against optional external `skill_sources` — resolved in research.md §3; it MAY live in
  `core/` or a thin adapter, but its result shape is `list[Component]` with `origin` set, so it
  composes with the same rendering the picker already uses.
