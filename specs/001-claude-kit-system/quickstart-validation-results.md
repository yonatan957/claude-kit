# Quickstart Validation Results (T064)

Ran quickstart.md's Story 1-5 sequence as **real subprocess invocations** of
`python -m src.cli <command>` (not in-process calls with monkeypatched
internals, unlike the automated test suite) against a real temporary `$HOME`
and a real local git Catalog Repo built from `tests/fixtures/registry_repo`.
This exercises the actual packaged-CLI entry point end-to-end, including
real `git clone`/`pull`, real subprocess lifecycle scripts, and real file I/O.

The interactive TUI portions of Story 1 (the picker, Step 2 configure) can't
be driven from a real terminal in this environment; those are covered
instead by the Textual `Pilot`-based automated tests (T017, T018).

## Results

| Story | Step | Result |
|---|---|---|
| 1 | `init` on a fresh `$HOME` with `.claude/` present | Creates `.claude-kit/`, `.claude-kit-repo/`, `env.d/`; deploys `genie-claude.md`; appends `@genie-claude.md` to `CLAUDE.md` exactly once. **Pass.** |
| 1 | `init`'s own exit code | `init` itself succeeds, but its process exit code is `1` because it unconditionally hands off to `config`, which correctly refuses (no TTY) rather than hanging. Noted as expected behavior for a real terminal user (who has a TTY), not a defect — see below. |
| 2 | `add skills fixture-skill` / `remove skills fixture-skill` | Installs/removes the skill file cleanly, exit `0` both times. **Pass.** |
| 2 | `add tools not-a-real-component` | Exits `1` with a clear "No component named…" message. **Pass.** |
| 2 | `add tools fixture-tool` (has a declared input) with no TTY | **Found a real bug**: hung indefinitely — the real Textual `ConfigureApp` launched against a non-interactive stdin instead of refusing. Fixed (`NoTTYError` in `config_cmd._collect_answers`, shared by `add`/`config`); re-verified: now exits `1` with a clear message instead of hanging. |
| 3 | `update` run twice consecutively | `installed.json` byte-identical aside from `installed_at`/`last_updated` timestamps. **Pass.** |
| 3 | `update` with `min_cli_version` bumped above the running build | Halts with exit `1`, clear message, `installed.json` completely unchanged (diffed byte-for-byte). **Pass.** |
| 4 | `list` | Shows every catalog component with correct installed/current/config/active columns. **Pass.** |
| 5 | `check` with nothing new | Writes `state.json` with `message: null`, exit `0`. **Pass.** |
| 5 | `check` after simulating a pending tool config | Writes a non-null message ("1 component(s) awaiting configuration"), `announced` includes `pending:1`. **Pass.** |
| 5 | hook read once, right after a `check` that found something new | Prints the message verbatim. **Pass.** |
| 5 | hook read twice **with no intervening `check` run** | Prints the same message both times — **not a bug**: `state.json`'s `message` field isn't cleared by reading it (data-model.md: the hook never writes state.json); dedup is achieved by the *next* `check` run re-evaluating `announced` and writing `message: null`. In real usage each hook invocation also launches a detached `check` (`hook.main()`), so by the *following* session's read, the message is already suppressed — exactly what T054's automated test verifies. |
| 5 | `launch_detached_check()` firing on every hook invocation | **Found a real gap**: it ignored `check_interval_hours` entirely, contradicting research.md #6 ("the hook can cheaply compare `checked_at` before deciding whether to even spawn the child"). Fixed: added `hook._should_launch_check()`, wired into `hook.main()`. |
| — | Non-blocking detached launch timing | `launch_detached_check()` returns in ~8ms regardless of the child's own (much slower) sync work. **Pass.** |
| — | PyInstaller `--onedir` build | `pyinstaller claude-kit.spec` produces a working `claude-kit.exe`/`claude-kit` that runs and shows the full command surface. **Pass.** |

## Bugs found and fixed during this pass

1. **`add` hung instead of failing cleanly** when a component needing input
   was added with no TTY available. Fixed in `config_cmd._collect_answers`
   (shared by `config` and `add`).
2. **The notify hook never rate-limited its detached `check` launch** against
   `check_interval_hours`. Fixed in `src/notify/hook.py`.

Both fixes are covered by new/updated automated tests and the full suite
(95 tests) passes after both fixes.

## Not exercised in this pass

- The interactive picker/Step 2 configure UI from a real terminal (requires
  a real TTY this environment doesn't have) — covered instead by Pilot-based
  tests.
- A real remote (non-local) git Catalog Repo over HTTPS/SSH — the sync
  mechanism (`git clone`/`pull`) is identical regardless of transport;
  `installers/catalog_sync.py`'s own tests exercise clone+pull against a
  local repo, which is what this pass also used.
- Real npm distribution (`npm install -g claude-kit`) — no release host
  exists yet; `npm/postinstall.js` is designed to skip gracefully (with a
  warning) rather than fail when its release-host env var isn't set.
