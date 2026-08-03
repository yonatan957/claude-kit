# Phase 0 Research: claude-kit System

All items below were open technical decisions in the Technical Context, not spec-level ambiguities (the spec has zero `[NEEDS CLARIFICATION]` markers). Each is resolved with a decision, rationale, and alternatives considered.

## 1. TUI framework for the two-step picker/configure flow

> **Superseded 2026-08-03 by the Phase 2 refinement — see §1a below.** The original decision (Textual) is retained here for the record because it explains why the first implementation looked the way it did.

- **Original decision**: Textual.
- **Original rationale**: The picker (Step 1) needs a scrollable list with per-item toggle state, live per-category counters, a dedicated search-mode overlay with pinned results, and red "pending removal" highlighting — all of which map directly onto Textual's compositable widget model (`ListView`/`OptionList`, reactive attributes for live counters, CSS-like styling for state highlighting) and its built-in `Pilot` test harness makes the acceptance scenarios in the spec scriptable as automated tests. Textual also renders consistently across macOS/Linux/Windows terminals, which matters since claude-kit is cross-platform.
- **Alternatives considered at the time**: `prompt_toolkit` — lighter weight and sufficient for simple sequential prompts (Step 2), but building a multi-panel list-with-counters-and-search-mode UI on it means hand-rolling most of what Textual provides out of the box.

## 1a. TUI framework, revisited (Phase 2 — FR-045/FR-046/FR-009)

- **Decision**: `prompt_toolkit` ≥3.0, replacing Textual entirely. Textual is removed from the dependency list.
- **Rationale**: Two of the Phase 2 requirements are not satisfiable within Textual's model, and a third is merely awkward:
  1. **`Tab` cannot be a pure search toggle in Textual (FR-009).** Textual reserves `Tab`/`Shift-Tab` for focus traversal across focusable widgets. The existing implementation had to live with this — `tests/integration/test_story1_picker.py:66` presses `tab` explicitly *to move focus off the search input*, and the shipped binding for search was `/` with `escape` to leave, precisely the "explicit exit" affordance FR-009 now forbids. In `prompt_toolkit`, `Tab` carries no built-in meaning; a `KeyBindings` handler owns it outright.
  2. **Inline, scrollback-preserving rendering (FR-045).** `prompt_toolkit`'s `Application(full_screen=False)` renders below the prompt in the normal buffer and leaves its output in scrollback on exit — the default mode it was designed for. Textual added an `inline=True` option in v0.55, so this alone would not force a switch, but inline is a secondary mode there rather than the primary design center, and it still carries the full widget/CSS/compositor stack for a UI that is now deliberately one list.
  3. **Constitution Principle VI (90-line files).** A Textual app concentrates behavior in `App` subclasses with class-level `CSS` and `BINDINGS`, which resists being cut into ≤90-line units. `prompt_toolkit` separates naturally along the exact seams the constitution wants: a key-binding registry, a formatted-text renderer, a style dict, and a plain state object — with the state machine having no framework imports at all.
- **What this costs**: the `Pilot` test harness is lost. Replaced by (a) direct unit tests against the framework-free `PickerState`, which is strictly better coverage of the interaction rules, and (b) `prompt_toolkit`'s `create_pipe_input()` / `DummyOutput()` for end-to-end key tests. Net test surface is comparable; the state-machine half becomes faster and terminal-independent.
- **Alternatives considered**: **Textual in `inline=True` mode** — rejected on FR-009 (the `Tab` reservation is the blocker, not the rendering mode) and Principle VI. **A hand-rolled ANSI/`curses` renderer** — rejected: `curses` is not available on Windows in the stdlib, and hand-rolling key decoding across terminals re-implements the one thing `prompt_toolkit` is most reliable at. **Keeping Textual for Step 2's prompts only** — rejected: `prompt_toolkit.shortcuts.prompt(is_password=True)` covers masked sequential input in a few lines, and keeping two TUI frameworks in a frozen binary for one input box is not worth the bundle size or the split test harness.

## 1b. Line-count measurement for Constitution Principle VI

> **Superseded 2026-08-03 by §1d, after measuring it against the codebase.** The original decision is kept here because the reversal is the useful part of the record.

- **Original decision**: count **total physical lines per file** (blanks, comments, and docstrings all included); enforce with a contract test over `src/**/*.py`.
- **Original rationale**: The constitution says "90 lines of code" without defining it, and the two readings differ materially — 11 files violate on total lines, 7 on non-blank/non-comment lines. Total physical lines is the strictest reading, requires no AST parsing, cannot be gamed by reformatting, and matches how a reviewer eyeballs a file's length.

## 1d. Line-count measurement, corrected (constitution v1.2.0)

- **Decision**: count **lines of code** — physical lines that are neither blank nor comment-only. Docstrings count; blank lines and `#` comments do not.
- **What changed the decision**: implementing Phase 2 under the total-lines rule produced three concrete bad outcomes, none of which were predictable from the armchair:
  1. **It deleted documentation.** Docstrings were stripped from `src/ui/state.py` purely to fit, including the explanation of why the approve row is absent in search mode. A cap whose effect is *less* explanation is working against its own rationale.
  2. **It fought the formatter.** `commands/config_apply.py` was hand-squeezed to 88 lines; `black` reformatted its imports and pushed it back to 97. Hand-tuning line counts against an auto-formatter is a losing, pointless game.
  3. **It mismeasured four files.** `core/diffing.py` (99 total / 72 code), `commands/check_cmd.py` (96/75), `notify/hook.py` (95/75), and `commands/add_remove_cmd.py` (103/81) were flagged as violations purely for being well-commented. They are not complex files, and splitting them would have been busywork that made the codebase worse.
- **Rationale**: "Lines of code" is also what Principle VI said all along; the original decision was stricter than the text it was interpreting. Docstrings are counted because they genuinely occupy a reader's attention budget, which is what the cap is protecting; blank lines and comments are not, because penalising them discourages exactly the things that make a file readable.
- **Effect**: the deferred-violations list drops from 8 files to 4 (`installers/script.py` 169, `commands/update_cmd.py` 125, `installers/settings_patch.py` 121, `core/state_model.py` 114). Those four are genuinely oversized by any measure.
- **Alternatives considered**: raising the cap to ~120 total lines — would have relieved the pressure but kept the wrong incentive, since a file could still be forced to shed comments to fit; excluding docstrings entirely — rejected, since a 400-line docstring is a real readability problem and the cap should notice it.

## 1c. Scope of `claude-kit list` (FR-026)

- **Decision**: `list` projects `installed.json`, not the catalog. Installed components missing from the current catalog still appear, with freshness reported as `unknown`. Zero installed components yields an explicit empty-state line and exit code `0`. A missing/corrupt catalog cache remains a hard error (exit `1`).
- **Rationale**: Developer feedback was that a full-catalog dump made `list` useless as a "what do I have?" answer, which is the question Story 4 actually asks; catalog browsing is already the picker's job (and the picker searches it far better). Keeping orphaned-but-installed components visible matters because those are precisely the rows a developer needs to act on. The catalog cache stays a hard requirement because the `CURRENT` column cannot be computed without it, and degrading that silently would make the command's most useful column quietly meaningless.
- **Alternatives considered**: adding a `--all` flag to restore catalog-wide output — deferred, not rejected; no user has asked for it, and it can be added later without breaking the default. Degrading gracefully when the catalog cache is missing (render rows with `CURRENT: unknown` instead of erroring) — rejected for now to keep the existing contract and its test intact, though it is the natural follow-up if the hard error proves annoying in practice.

## 2. CLI argument-parsing framework

- **Decision**: Typer.
- **Rationale**: Built on Click, gives type-hint-driven subcommands (`init`, `config [type]`, `update`, `add <type> <name>`, `remove <type> <name>`, `list`, `check`) with minimal boilerplate, automatic `--help`, and straightforward non-zero exit code handling (`typer.Exit(code=1)`), which the spec requires for scripted add/remove (FR-020).
- **Alternatives considered**: raw `argparse` (more boilerplate, no automatic subcommand help); `click` directly (Typer is a thin, more ergonomic layer over the same engine — no real downside to preferring it).

## 3. Preserving `claude_settings.json` byte-for-byte outside `mcpServers`

- **Decision**: A surgical, text-level block editor rather than full parse-and-redump. The editor locates the `"mcpServers"` key's value span in the raw file text (using a JSON tokenizer to find exact start/end offsets, not a regex), replaces only that span with the newly serialized `mcpServers` object, and leaves every other byte of the file — including whitespace, key order, and formatting elsewhere — untouched.
- **Rationale**: FR-038 and SC-007 require byte-for-byte preservation of every key claude-kit doesn't own. A standard `json.load` → mutate → `json.dump` round-trip in Python does not preserve original formatting (key order can be stable with dict ordering, but whitespace/indentation style and trailing newline conventions are not guaranteed to match whatever wrote the file previously, e.g. Claude Code itself). A span-replacement approach makes the "everything else is untouched" guarantee structural rather than incidental, and is trivially unit-testable (round-trip a fixture file with an unrelated custom key and assert it is unchanged).
- **Alternatives considered**: Full parse/mutate/dump with `sort_keys=False` and matched indentation — rejected because it depends on guessing the exact serialization style used elsewhere and silently breaks if that style ever differs (extra keys with unusual formatting, comments if any tool adds them, etc.); a dedicated "preserve formatting" JSON library — none of the common ones are designed for arbitrary already-existing JSON files without adopting a special document object model throughout the codebase, which is unnecessary complexity for editing a single well-known key.

## 4. Appending to `CLAUDE.md` without rewriting it

- **Decision**: Open the file in text-append mode and write a single line only if a presence-check (plain substring search for the exact reference line) fails; never open the file in a truncating/rewriting mode.
- **Rationale**: FR-003/FR-004/SC-008 require zero risk of altering existing content, and append-only I/O makes that a property of the operation itself rather than something that must be verified after the fact.
- **Alternatives considered**: Read-modify-write with a templating library — rejected as unnecessary risk for a one-line, idempotent append.

## 5. Catalog sync mechanism

- **Decision**: Shell out to the system `git` binary (`subprocess.run(["git", "clone"/"pull", ...])`) to sync the Catalog Repo into `~/.claude-kit-repo`.
- **Rationale**: The spec's own data model describes the catalog as living "in the remote Catalog Repo, cloned locally" — this is a git-native distribution model (versioned, diffable, supports private repos via the developer's existing git credentials/SSH config with zero extra auth code in claude-kit). Shelling out to system git avoids bundling a heavy embedded git implementation and inherits the developer's existing git auth.
- **Alternatives considered**: An embedded pure-Python git library — adds a large dependency and its own auth/transport edge cases for no real benefit over the system binary; a plain HTTP/tarball fetch of `registry.json` — simpler, but loses the versioned/diffable nature implied by "Catalog Repo" and the `catalog_commit` field tracked in `installed.json`.

## 6. Detached background execution for `claude-kit check`

- **Decision**: Launch `claude-kit check` as a fully detached child process from the startup hook (`notify/hook.py`) using `subprocess.Popen` with platform-specific detachment: `start_new_session=True` on POSIX, `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS` on Windows — and immediately return control to the hook without waiting on it.
- **Rationale**: Principle V requires the startup hook to never wait on a subprocess. A detached, fire-and-forget child guarantees the hook's own exit is not gated on the child's lifetime, on every supported platform.
- **Alternatives considered**: A persistent background daemon/service — over-engineered for a periodic, short-lived check; an OS-level scheduled task (cron/Task Scheduler) — adds install-time system integration complexity that a simple fire-and-forget subprocess from the hook itself avoids, while still satisfying `check_interval_hours` gating (the hook can cheaply compare `checked_at` before deciding whether to even spawn the child).

## 7. Restricting secret file permissions cross-platform

- **Decision**: On POSIX (macOS/Linux), `chmod 600` each file under `~/.claude-kit/env.d/`. On Windows, apply an equivalent restrictive ACL (owner-only access) at file-creation time. Both paths are implemented behind one `installers/secrets.py` function so callers never branch on OS.
- **Rationale**: FR-016/FR-039 and Principle IV (secrets security) require secrets to be inaccessible to anyone but the current developer; POSIX permission bits and Windows ACLs are the respective platform-native mechanisms for that guarantee.
- **Alternatives considered**: OS-level credential stores (macOS Keychain, Windows Credential Manager) — more secure in principle, but each has a different API/UX and would need a per-platform integration for every secret write/read; deferred as a possible future enhancement, not required to satisfy the spec's stated guarantee (a restricted local file), and keeping to plain restricted files matches the spec's own description of `env.d/` files.

## 8. Packaging a Python frozen binary for npm distribution

- **Decision**: Build platform-specific PyInstaller `--onedir` outputs (macOS/Linux/Windows) as CI release artifacts, publish them alongside a thin npm package whose `bin` shim execs the correct platform binary for the current OS/arch (following the same pattern used by other npm-distributed native/frozen-binary CLIs), with a `postinstall` step that fetches or unpacks the matching platform artifact.
- **Rationale**: Satisfies "shipped as a frozen binary, distributed via npm" directly: npm remains the install/upgrade UX developers already use (`npm install -g claude-kit`, later `npm install -g claude-kit@latest` per Principle III), while the actual runtime is a self-contained Python build with no developer-side Python/dependency setup required.
- **Alternatives considered**: Publishing pure Python to PyPI instead — rejected because it's explicitly out of scope per the system's own stated distribution channel (npm) and would require developers to have a compatible Python environment, which a frozen binary avoids entirely.

**Output**: All open technical-context questions above are resolved; no `[NEEDS CLARIFICATION]` markers remain for Phase 1.
