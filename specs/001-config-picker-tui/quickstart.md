# Quickstart: Validating the Config Picker & Configure Flow

Manual/scripted scenarios that prove this feature works end-to-end, one per user story in
spec.md. Run these against a local, disposable `installed.json` and a small fixture registry —
never against a real machine's state.

## Prerequisites

- A fixture `registry.json` with at least two components per type, one marked `recommended`, and
  one MCP/tool with `inputs` declared (so a configure step is exercised) — the example in
  `overview/registry.json` is sufficient as-is.
- A fixture `installed.json` you control, so each scenario below starts from a known state.
- The `config` command runnable against these fixtures (via whatever test/dev entrypoint the
  implementation phase wires up — see `tasks.md` for the actual command).

## Scenario 1 — First-time setup (User Story 1, P1)

1. Start with an empty `installed.json` (no claude-kit-managed components).
2. Run the config command.
3. **Expect**: Recommended/Custom choice appears; choosing Recommended pre-checks every
   `recommended: true` component across all sections.
4. Scroll to the bottom without changing anything; select "Approve & install".
5. **Expect**: every recommended component reports `installed`; any with declared `inputs`
   (e.g. `jira-internal`) is then prompted for automatically, with sensitive fields masked.
6. **Expect**: final summary distinguishes installed vs. configured vs. pending (FR-013); zero
   pending remain if all configure steps succeeded.

**Pass condition**: resulting `installed.json` contains exactly the recommended set, each
configured entry reflecting `"<set>"` markers only (Constitution V) — never raw secret values.

## Scenario 2 — Returning user adds and removes (User Story 2, P2)

1. Start with `installed.json` containing 2+ components across different types.
2. Run the config command.
3. **Expect**: no Recommended/Custom prompt; picker opens pre-checked with current state.
4. Select one new, not-yet-installed component; deselect one currently-installed component.
5. **Expect**: the deselected row is visually flagged as a pending removal while scrolling; the
   approve row shows a removal count.
6. Approve.
7. **Expect**: resulting state has the new component installed and the deselected one absent —
   every other previously-installed component untouched (SC-003).

**Pass condition**: diffing `installed.json` before/after shows exactly one addition and one
removal.

## Scenario 3 — No-op selection routes straight to configure (User Story 2 edge case, FR-011)

1. Start with `installed.json` containing one component with a `pending` configuration.
2. Run the config command and approve without changing any selection.
3. **Expect**: no "installing" step is shown (nothing to install/remove); the flow proceeds
   directly to the configure wizard for the pending component.

## Scenario 4 — Reconfigure an already-configured component (FR-015)

1. Start with `installed.json` containing one fully `configured` MCP/tool.
2. Run the config command, re-select that already-checked component in the picker (toggle off
   then on, or use the Configure screen's own re-select per the UX walkthrough), leave everything
   else untouched, approve.
3. **Expect**: the configure wizard opens for that component again (`reason:
   user_requested_reconfigure`), prompting for its inputs anew.

## Scenario 5 — Scoped to one type (User Story 3, P3)

1. Run the config command scoped to a single declared type (e.g. `plugins`).
2. **Expect**: only that type's section appears; same keys, same single approve row.
3. Approve with no changes selected.
4. **Expect**: no component of any other type is affected.

**Pass condition**: components of other types are byte-identical in `installed.json` before and
after.

## Scenario 6 — Configuration failure doesn't undo install (FR-014)

1. Start from a state where a component is freshly installed and pending configuration.
2. Run the configure step and supply an input that causes `verify.sh` to fail (e.g. an invalid
   token in the fixture's `verify.sh`).
3. **Expect**: the component remains recorded as installed; its configuration status remains
   `pending`; the user is told what failed and can retry without re-running the whole install.

## Out of scope for this quickstart

- Catalog sync (`update`) — assumed already up to date for all scenarios above.
- The internals of the install/removal transaction engine (snapshot/rollback) — exercised here
  only through its public `core.apply` contract (see `contracts/core-interface.md`), not verified
  at the mechanism level.
