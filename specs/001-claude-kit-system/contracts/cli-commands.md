# Contract: CLI Command Surface

This is the externally observable contract for every claude-kit command: invocation shape, side effects, output expectations, and exit codes. Any implementation change that alters one of these must be treated as a breaking contract change.

## `claude-kit init`

- **Args**: none
- **Preconditions**: none
- **Behavior**: Verify a valid Claude Code environment exists → create local directories/baseline files (idempotent) → deploy `genie-claude.md` → append the `@genie-claude.md` reference line to `CLAUDE.md` only if absent → launch the interactive configuration flow (`config` Step 1).
- **Exit codes**: `0` success (including "already initialized, nothing to do"); non-zero if no valid Claude Code environment is found, with a clear message and no directories/files created.

## `claude-kit config [type]`

- **Args**: optional `type` (one of the declared categories) to pre-filter Step 1's list.
- **Behavior**: Step 1 (picker) → on approval, apply all adds/removes in one pass → Step 2 (sequential configure prompts) for any newly selected component with declared `inputs[]`.
- **Interactivity**: requires a TTY; MUST refuse with a clear error (not a hang or a crash) if run without one.
- **Presentation** (FR-045/FR-046): renders **inline** in the terminal's normal buffer. MUST NOT enter the alternate screen buffer, MUST NOT clear the screen or scrollback, and MUST leave its final frame in scrollback on exit. On-screen chrome is limited to the per-category counts line, the bounded list viewport, and a one-line key hint.
- **Key bindings** (FR-007/FR-009/FR-012) — this set is exhaustive; no other key may be bound:

  | Key | Behavior |
  |---|---|
  | `↑` / `↓` | Move the highlight within the visible rows (clamped, no wraparound) |
  | `Enter` | On an entry row: toggle its selection. On the trailing **"Approve & Install"** row: commit the plan and exit |
  | `Tab` | Toggle search mode on/off — the only way in and the only way out |
  | printable / `Backspace` | In search mode only: edit the query |
  | `Esc` | In search mode: return to browsing. In browse mode: cancel with zero changes |
  | `Ctrl-C` | Cancel with zero changes |

  Explicitly forbidden: any single-letter approval shortcut (the legacy `a`), `Space` as a selection toggle, and any separate "exit search" row, button, or control.
- **Selection markers** (FR-047): `[ ]` unselected, `[✓]` selected (green), `[X]` pending removal (red). A row's marker depends only on its selection state, never on whether it is highlighted, and MUST remain visible across focus/mode transitions.
- **Exit codes**: `0` on completion (including a clean cancel with zero changes applied); non-zero if any part of the approved install/remove plan fails to apply.

## `claude-kit update`

- **Args**: none
- **Behavior**: sync catalog → check `min_cli_version` (halt with non-zero exit and no other changes if violated) → re-run install/config/verify for every currently-installed component to sync content while reusing existing credentials → print an end-of-run summary listing anything now `"pending"`.
- **Interactivity**: MUST NOT read from stdin or block on any prompt under any circumstance.
- **Exit codes**: `0` on completion, even if some components ended up `"pending"` or `"failed"` (those are reported in the summary, not exit-code failures); non-zero only for the `min_cli_version` gate or a hard sync failure (e.g., catalog completely unreachable and no prior local cache exists).

## `claude-kit add <type> <name>`

- **Args**: `type` (required, must match a declared category), `name` (required, must exist in the synced catalog for that type).
- **Behavior**: install the named component via its declared handler → if it declares `inputs[]`, immediately run Step 2 configure prompts for it (interactive).
- **Exit codes**: `0` on success; non-zero on unknown type/name, handler failure, or (if configure prompts run) a failed verification step — with a clear message in every non-zero case.

## `claude-kit remove <type> <name>`

- **Args**: `type`, `name` — must currently be installed.
- **Behavior**: run the type's removal lifecycle (see `script-lifecycle.md` for script-handler components).
- **Exit codes**: `0` on success (including "not installed, nothing to do" — idempotent no-op); non-zero on handler failure.

## `claude-kit list`

- **Args**: none
- **Behavior** (FR-026, revised): read-only; renders **only the components recorded in `installed.json`** — never catalog components that are not installed. Columns: category, name, version, up-to-date/outdated/unknown, configuration status (done/pending/failed/n/a), active/inactive. Pending configuration MUST be visually distinct from done (FR-027).
- **Orphaned entries**: a component present in `installed.json` but absent from the current catalog MUST still be listed, with freshness reported as `unknown` rather than being hidden.
- **Empty state**: with zero installed components, prints a single explanatory line naming `claude-kit config` as the way to add some, and exits `0`.
- **Exit codes**: `0` always, unless the local catalog cache is entirely missing/corrupt (non-zero, with instructions to run `update`) — the cache is required because freshness cannot be computed without it.

## `claude-kit check`

- **Args**: none (invoked by the session-start hook as a detached child process; also runnable manually)
- **Behavior**: silent — no stdout/stderr output intended for a human in the common case; compares local vs. remote catalog commit, local vs. latest CLI version, and counts `"pending"` configurations; writes one pre-rendered `message` plus `findings` to `state.json`; exits.
- **Exit codes**: `0` on successful check (regardless of whether anything new was found); non-zero only if `state.json` could not be written.

## Cross-command guarantees

- Every command above is safe to run twice in a row with no intervening state change and MUST produce identical resulting state on disk after the second run (Principle IV).
- No command other than `init` (first run only) and `config`/`add` (only when collecting declared `inputs[]`) may read from stdin.
- `claude-kit update` and `claude-kit check` MUST NOT read from stdin under any circumstance, even if run in a TTY.
