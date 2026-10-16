# Missions

The order claude-kit gets built in, one mission at a time.

**The rule:** I do one mission, then stop. You read it and approve before the next one
starts. Nothing here happens in parallel.

`todo` not started · `doing` in progress · `review` written, waiting on you · `done` approved


| 1 | Record installs in the database | review |
| 2 | The genie source | todo |
| 3 | Search: parallel, tolerant, real columns | todo |
| 4 | `install --source` and `--upgrade` | todo |
| 5 | `CLAUDE_CONFIG_DIR` | todo |
| 6 | The catalog | todo |
| 7 | `ck status` that really checks, and `ck upgrade` | todo |
| 8 | Tags | todo |
| 9 | Rollback | todo |
| 10 | Make the README match | todo |
| 11 | Ship it: binary and npm | todo |

---

## 0 — The test suite · review

**Goal:** nothing below ships untested, so this comes first.

**What is there:** 83 tests. `tests/fakes.py` has a fake source and a fake SkillHub client,
so no test touches the network or spawns a process. `tests/conftest.py` has the fixtures.
Then one file per area: `test_storage.py` (18), `test_services.py` (19), `test_sources.py`
(14), `test_cli.py` (10), `test_state.py` (9). Plus `.importlinter`, which checks that
`cli → services → sources → storage → components → helpers` only ever points one way.

**Run it:** `pytest`, then `lint-imports`.

**Two things the tests found, both still open:**

- `popularity` is on `ClaudeComponent` but has no column in the database, so it is lost on
  save. Fine if popularity is only a search-time number — your call.
- `_is_missing` in `skillhub_source.py` matches `notFound` but not `NOT_FOUND`. If the
  registry ever uses the underscored spelling, "no such skill" turns into a hard error and
  stops the search falling through to the next source.

---

## 1 — Record installs in the database · review

**Goal:** `ck list` stops printing `nothing installed`.

`install` and `uninstall` never write to `installed.db` today. Everything in
`storage/writer.py` is already written and never called.

**Files:** `services/install_service.py`, `services/uninstall_service.py`, and
`storage/database.py` gains `open_kit_database(home)` — the `KitNotFound` guard that
`list_service` currently keeps to itself.

**Done when:** install a skill, `ck list` shows it, uninstall it, `ck list` is empty again.
Installing the same thing twice exits 6 instead of showing a traceback.

**Unblocks:** missions 4, 7 and 8 all need rows in the database to work on.

---

## 2 — The genie source

**Goal:** the main registry, first in precedence.

**Files:** new `sources/genie_source.py`, one line changed in `sources/available.py`.

This is the biggest single gap. Four separate things in the README depend on it:

- `agent`, `mcp`, `tool` and `plugin` have no provider at all until genie serves them.
  SkillHub serves skills only.
- Precedence and `--source` mean nothing with one source in the list.
- The catalog lives here.

**What I need from you:** I could not find genie anywhere — no API, no CLI name, no auth, no
JSON shapes. Tell me what it actually is and I target it directly. Otherwise I build the
source against a clearly marked stub, so precedence and the four kinds become real and
testable now, and the stub gets swapped for the real thing later.

**Done when:** `ck search agent ""` reaches genie, and `ck install skill x --source genie`
picks genie over skillhub.

---

## 3 — Search: parallel, tolerant, real columns

**Goal:** three README promises in one file.

- Ask every source at the same time instead of one after another.
- A source that cannot be reached gets named, and the sources that did answer still show
  their results. Today the first dead source kills the whole search.
- The output becomes a table: name, description, source, version, popularity.

**Files:** `services/search_service.py`, `cli.py`.

**Done when:** with one source unplugged, the search still prints the other's results, says
which one was unreachable, and exits 0. Exit 4 only when every source is down.

---

## 4 — `install --source` and `--upgrade`

**Goal:** the two flags the README documents.

`--source` only installs from that one source. `--upgrade` replaces what is already there.
Both are small: `get_source` and `add_component(replace=True)` already exist.

**Done when:** `--upgrade` leaves one row, not two, and without it a second install exits 6.

---

## 5 — `CLAUDE_CONFIG_DIR`

**Goal:** the kit knows where packages land.

The README documents this variable; the code has never heard of it. Today SkillHub decides
where files go and claude-kit takes its word for it.

**Files:** `helpers/consts.py`, plus the five per-kind directory names.

**Done when:** install verifies the files really are where Claude Code looks for them.

**Unblocks:** mission 9 cannot undo file changes it cannot find.

---

## 6 — The catalog

**Goal:** the recommended-package list the README promises.

`CLAUDE_KIT_CATALOG_URL` and `CLAUDE_KIT_CATALOG_REPOSITORY` get read, `~/.claude-kit/registry/`
gets created. A catalog that cannot be fetched leaves
status reading `unknown` rather than failing — the README already says so.

**Depends on:** mission 2.

---

## 7 — `ck status` that really checks, and `ck upgrade`

**Goal:** status stops being empty, and upgrade starts existing.

`status` only prints a cached file today, and nothing ever writes versions into it. Add the
check: claude-kit, Claude Code, the catalog, and every installed package against its source.
Anything it cannot work out reads `unknown`.

Then `ck upgrade` — the three core components only, only the ones behind. Installed packages
are never touched here; the README is explicit that those go through `ck install --upgrade`.

**Depends on:** missions 1 and 6.

---

## 8 — Tags

**Goal:** tell two same-named packages apart.

The tag in `ck list` output, and `name:tag` in `ck uninstall`. An ambiguous name removes
**nothing** and shows you the candidates.

Lower priority than everything above it, as you said.

**One decision:** the code puts SkillHub's namespace in `tag`; the README shows a 4-character
hex like `[a0f9]`. I would make the tag a short hash and keep the namespace in its own
column, but this is yours to pick.

---

## 9 — Rollback

**Goal:** a failed install leaves the tree exactly as it was. Exit code 7.

The biggest mission, and the one the README leans on hardest. A new `claude_kit/install/`
package: the file operations and their inverses, a write-ahead journal in
`~/.claude-kit/journal/`, and a transaction that stages, commits, or rolls back.

This is also where exit code 5 gets used: the steps in `init` you can decline, and the
config questions on `install` that keep credentials out of the manifest, the logs and the
command line.

**Depends on:** missions 1, 5 and a real test suite — this is the one that cannot be built
without tests that crash it at every step.

---

## 10 — Make the README match

**Goal:** the README says what the code does.

Some of this happens as each mission lands. What is left over:

- Document `ck init --no-install` — a good flag that is missing from the docs.
- Document `ck --version`, which works and is not mentioned.
- Add `CLAUDE_KIT_TIMEOUT`, `CLAUDE_KIT_CHECK_INTERVAL_HOURS`, `CLAUDE_BIN` and
  `SKILLHUB_BIN` to the configuration table. All four are read; none is listed.

---

## 11 — Ship it: binary and npm

**Goal:** `npm install -g claude-kit` actually works.

`docs/PACKAGING.md` is already a complete plan — PyInstaller `--onedir`, five platform
packages under `optionalDependencies`, the publish order, the traps. Nothing is built yet:
no `packaging/`, no spec file, no shim.

Needs a CI matrix, because PyInstaller cannot cross-compile. Last, because there is no point
shipping a binary of a half-built tool.
