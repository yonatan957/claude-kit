# Phase 0 Research: claude-kit System

All items below were open technical decisions in the Technical Context, not spec-level ambiguities (the spec has zero `[NEEDS CLARIFICATION]` markers). Each is resolved with a decision, rationale, and alternatives considered.

## 1. TUI framework for the two-step picker/configure flow

- **Decision**: Textual.
- **Rationale**: The picker (Step 1) needs a scrollable list with per-item toggle state, live per-category counters, a dedicated search-mode overlay with pinned results, and red "pending removal" highlighting — all of which map directly onto Textual's compositable widget model (`ListView`/`OptionList`, reactive attributes for live counters, CSS-like styling for state highlighting) and its built-in `Pilot` test harness makes the acceptance scenarios in the spec scriptable as automated tests. Textual also renders consistently across macOS/Linux/Windows terminals, which matters since claude-kit is cross-platform.
- **Alternatives considered**: `prompt_toolkit` — lighter weight and sufficient for simple sequential prompts (Step 2), but building a multi-panel list-with-counters-and-search-mode UI on it means hand-rolling most of what Textual provides out of the box. **Decision**: use Textual for the picker (Step 1) and reuse Textual's simple `Input` widget (masked mode) for the sequential Step 2 configure prompts too, so the whole two-step flow shares one framework and one test harness instead of splitting across two TUI libraries.

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
