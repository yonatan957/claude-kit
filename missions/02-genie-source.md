# Mission 2 — The genie source

**Status:** `review` — built, slimmed after the first review, waiting on you.

**Goal:** a second source, `genie`, first in precedence, that installs and removes two
kinds SkillHub cannot serve:

- **`mcp`**: MCP servers, registered with Claude Code through `claude mcp add-json` /
  `claude mcp remove`, never by editing `~/.claude.json`.
- **`tool`**: anything that needs an installer, installed and removed only by scripts the
  manifest names.

One entry can be both: a script installs the binary, then genie registers it as an MCP.

**Also in this mission:** `sources/available.py` is renamed to `sources/index.py`.

**The rule the code follows:** the manifest is written by our own team and is trusted — it
already runs scripts on every machine. The code does not defend against a hostile or sloppy
manifest; anything wrong with it fails loudly with one clear `SourceError`.

---

## How it works

**`ck init` downloads; everything else is local.** `ck init` is the only command that
touches the network for genie. It copies the manifest and every script it names into
`CLAUDE_KIT_HOME/genie/`, and every other command reads that copy. Refreshing genie means
running `ck init` again.

```
ck init
  1. GENIE_MANIFEST_URL unset             -> "genie: not configured", nothing else
  2. fetch the manifest (urlopen, TIMEOUT) and parse it with the normal parser
                                             not JSON -> "<url> did not return JSON --
                                             is the GitLab project public?"
  3. fetch every install/uninstall script, for every platform, at
     urljoin(manifest_url, script_path)
  4. write it all into a temp dir next to CLAUDE_KIT_HOME/genie/
  5. only when everything succeeded       -> swap the temp dir in for genie/
     any failure                          -> the old copy stays untouched
  6. print one line: "genie: N entries from <url>", or
     "genie: unreachable -- <reason>, keeping the copy from <date>" / "... no local copy"
     (<date> is the mtime of genie/manifest.json; for a connection error, <reason> is
     the reason only, not Python's raw "<urlopen error ...>")
     A genie failure is a warning: init still succeeds.
```

```
CLAUDE_KIT_HOME/genie/
  manifest.json      the manifest as downloaded
  scripts/...        every script, at the same relative path as in the manifest
```

```
ck install mcp gitlab
  1. genie loads CLAUDE_KIT_HOME/genie/manifest.json (once per process, only when first
     asked for mcp or tool). No local copy -> genie offers nothing and says once:
     "genie: no local manifest -- run `ck init`"
  2. no entry called gitlab of kind mcp?  -> return []  (falls through to skillhub)
  3. the entry has an mcp block           -> claude mcp get gitlab
                                             already there -> Conflict (exit 6), unless force
                                             claude missing -> SourceUnreachable (exit 4)
  4. the entry declares inputs            -> ask the user, interactively
  5. fill {PLACEHOLDERS} in the mcp block -> unknown one -> SourceError
  6. the entry has an install script      -> run it, inputs passed as env vars
  7. the entry has an mcp block           -> claude mcp add-json <name> <json> --scope user
  8. return the component                 -> install_service records it in installed.db
  9. the input values are dropped         -> nothing is stored by the kit
```

Steps 3–5 happen before any script runs, so a conflict, a missing `claude`, a missing input
or a bad placeholder never leaves a half-installed tool.

Uninstall runs the other way: `claude mcp remove` first, then the uninstall script, so
Claude Code is never left pointing at a binary that is gone.

### Decisions

| Question | Decision |
|---|---|
| Where the manifest comes from | `GENIE_MANIFEST_URL` (env), else `DEFAULT_GENIE_MANIFEST_URL` in `consts.py` — today `""` with a TODO for our GitLab raw URL. `https://` only, or `http://` on `localhost`/`127.0.0.1` for local testing; any other scheme is a `SourceError`. |
| When it is downloaded | Only by `ck init`, together with every script. Refresh = run `ck init` again. |
| Where the copy lives | `CLAUDE_KIT_HOME/genie/`: `manifest.json`, and the scripts at their manifest paths. Scripts resolve relative to that folder. |
| Network at runtime | None. `search`, `install` and `uninstall` read only the local copy. |
| TLS and proxies | The system proxy env vars and the OS cert store, through `urllib`'s defaults. No TLS options of our own. |
| Where MCPs are written | Only through `claude mcp`. Always `--scope user`. |
| Where input values are stored | Nowhere. Asked on every install. |
| How values reach the script | As environment variables of the script's process only. `os.environ` is not touched. |
| Who registers the MCP for a tool+mcp entry | genie, not the script. Scripts install binaries and know nothing about Claude. |
| Manifest format | JSON. No new dependency. |
| Network or I/O at import time | None. `GenieSource()` is built when `sources/index.py` is imported, so the manifest loads lazily. |
| Not in the manifest, or no local copy | `[]`, never an error, so the request falls through to the next source. |
| A bad manifest entry | The whole manifest fails with one `SourceError` naming the entry. Nothing is skipped quietly. |
| A failed step after the script ran | Raised as is. No best-effort rollback: scripts are idempotent, so running the install again fixes a half-done one. Real rollback is mission 9. |

---

## The manifest

```json
{
  "manifest_version": 1,
  "entries": [
    {
      "kind": "mcp",
      "name": "gitlab",
      "version": "1.2.0",
      "description": "Internal GitLab MCP",
      "inputs": [
        { "key": "GITLAB_TOKEN", "description": "Personal access token",
          "help": "GitLab -> Preferences -> Access Tokens, scope: api",
          "secret": true, "required": true },
        { "key": "GITLAB_URL", "description": "GitLab base URL",
          "default": "https://gitlab.internal" }
      ],
      "mcp": {
        "type": "http",
        "url": "{GITLAB_URL}/mcp",
        "headers": { "Authorization": "Bearer {GITLAB_TOKEN}" }
      }
    },
    {
      "kind": "mcp",
      "name": "k8s",
      "version": "2.0.1",
      "description": "Kubernetes MCP (local binary)",
      "inputs": [ { "key": "KUBECONFIG", "description": "Path to kubeconfig", "required": true } ],
      "install":   { "windows": "scripts/k8s/install.ps1",   "linux": "scripts/k8s/install.sh" },
      "uninstall": { "windows": "scripts/k8s/uninstall.ps1", "linux": "scripts/k8s/uninstall.sh" },
      "mcp": {
        "type": "stdio",
        "command": "{KIT_HOME}/tools/k8s-mcp/k8s-mcp",
        "env": { "KUBECONFIG": "{KUBECONFIG}" }
      }
    },
    {
      "kind": "tool",
      "name": "kubectl",
      "version": "1.31.2",
      "description": "Kubernetes CLI",
      "install":   { "windows": "scripts/kubectl/install.ps1",   "linux": "scripts/kubectl/install.sh" },
      "uninstall": { "windows": "scripts/kubectl/uninstall.ps1", "linux": "scripts/kubectl/uninstall.sh" }
    }
  ]
}
```

### What is checked (`manifest.py`)

- `manifest_version` is `1`, and the file is JSON.
- `kind` is `mcp` or `tool`; `name` and `version` are there; every input has only the fields
  `GenieInput` knows (`key`, `description`, `help`, `secret`, `required`, `default`).
- A `tool` entry needs `install` and `uninstall`.
- `install` and `uninstall` come together.
- An `mcp` entry needs an `mcp` block.

Placeholders are checked when they are filled, at install time: a `{NAME}` that is neither
an input key nor `KIT_HOME` is `SourceError("<name>: unknown placeholder NAME")`, raised
before any script runs. An entry with no script for the current platform is
`SourceError("<name> has no script for windows")`.

### Rules for scripts (documented for whoever writes them)

- Exit 0 means success. Anything else is a failure, and its stderr is shown to the user
  (with secret values replaced by `***`).
- Not interactive: stdin is closed. Every value comes in as an env var.
- Idempotent: running it a second time does not break anything. This is what makes
  "install again" the recovery from a half-done install.
- Environment it gets: the inputs (install only — inputs are never stored, so the uninstall
  script does not get them), plus `CLAUDE_KIT_HOME`, `GENIE_NAME` and `GENIE_VERSION`.
- `.ps1` runs with `powershell -NoProfile -ExecutionPolicy Bypass -File`, anything else
  with `bash`.

---

## Files

### Renamed

**`src/claude_kit/sources/available.py` → `src/claude_kit/sources/index.py`**
- `AVAILABLE_SOURCES: list[Source] = [GenieSource(), SkillHubSource()]`. Nothing else
  changed, so no caller had to.

**`src/claude_kit/sources/__init__.py`**: imports from `.index`, exports `GenieSource`.

### New: `src/claude_kit/sources/genie/`

**`genie/__init__.py`**: exports `GenieSource`, plus `download_manifest` for `ck init`.

**`genie/download.py`** (76 lines): the only genie code that touches the network, called
only from `services/init_service.py`.
- `download_manifest(manifest_url, genie_dir) -> Manifest`: fetch, parse with
  `parse_manifest`, fetch every script, write into a temp dir next to `genie_dir`, swap it
  in only when all of that worked: the old folder is moved aside, the new one renamed in,
  the old one deleted. Network and HTTP errors → `SourceUnreachable` naming the URL.

**`genie/manifest.py`** (124 lines): what the manifest says. Local files only.
- `GenieInput`, `GenieEntry`, `Manifest(entries, manifest_dir)` with `find_entry_by_name` and
  `search`.
- `load_manifest(manifest_path)`: reads the local file. Cannot be read → `SourceUnreachable`;
  not JSON → `SourceError`. Then `parse_manifest(manifest_json, origin, manifest_dir)`,
  which `download.py` also uses: wrong version or a bad entry → `SourceError`. Inputs are built with
  `GenieInput(**input_json)`, so an unknown field is a `TypeError` turned into a
  `SourceError`; an entry that is not a JSON object is one too. In code the JSON keys
  `install`, `uninstall` and `mcp` become `install_scripts`, `uninstall_scripts` and
  `mcp_config`.

**`genie/genie_source.py`** (269 lines): `GenieSource(Source)` and the input helpers.
- `GenieSource(genie_dir=CLAUDE_KIT_HOME / "genie", prompter=ask, runner=run)`; it reads
  `genie_dir/manifest.json` and nothing else. The runner is a plain
  `Callable[..., CommandResult]`.
- `_claude_mcp(*args, label=None)`: every `claude mcp` call. `NOT_FOUND_CODE` / `TIMED_OUT_CODE`
  (127/124, from `helpers/system.py`) → `SourceUnreachable`. `add-json` runs with `label="claude mcp add-json <name>"`, so the
  JSON (which holds the token) never appears in a message.
- `_remove_mcp(name)`: `claude mcp remove`; Claude's `No MCP server named` counts as
  already gone. Used by uninstall and by a forced install.
- `_run_script(entry, script, input_values=<empty>, secret_values=())`: powershell or bash
  by suffix; uninstall passes neither, since inputs are never stored.
- `ask(spec, value_from_env)`: prints description and help, `getpass` for secrets, `input`
  otherwise; with no terminal it answers `""` at once.
- `collect_inputs(entry, prompter)`: the answer, else the value already in `os.environ`,
  else the default. Required and still empty → `UsageError` naming every missing key.
- Uninstalling an MCP-only entry that is not registered answers `[]`, so `ck uninstall`
  says "not installed".

### Changed

- **`helpers/system.py`**: `run()` gains `env` (merged over `os.environ` for that process
  only) and `label` (shown instead of the command line). `NOT_FOUND_CODE` and
  `TIMED_OUT_CODE` are exported.
- **`helpers/consts.py`**: `DEFAULT_GENIE_MANIFEST_URL` (`""`, TODO: our GitLab raw URL),
  `GENIE_MANIFEST_URL` (the env var, else the default), `GENIE_DIR_NAME`,
  `GENIE_MANIFEST_FILE_NAME`, `GENIE_LABEL = "genie"`,
  `MCP_SCOPE = "user"`. `GENIE_MANIFEST_PATH` is gone.
- **`sources/source.py`**: `Source.init(home, install_missing) -> InitReport(ok, message) | None`.
  `GenieSource.init` downloads into `home/genie/`, always `ok=True` (a warning on failure);
  `SkillHubSource.init` ensures the SkillHub CLI. `init_service` checks Claude Code, then
  every source; one that raises is reported and the rest still run. `ck init` prints each.
- **`claude_kit/__init__.py`**: exports `GenieSource`.
- `components/`, `storage/`: no change.

### Tests

- **`tests/data/genie/manifest.json`**: the three example entries. No scripts — the fake
  runner never executes them and nothing checks they exist on disk.
- **`tests/fakes.py`**: `FakeRunner` answers `claude mcp` from a set of registered names
  and lets scripts succeed unless `failing` names them; `FakePrompter` answers from a dict
  and records what it was asked.
- **`tests/test_genie_download.py`** (8, `urlopen` monkeypatched): manifest and every
  script land in `genie/` (over https and over http on 127.0.0.1); a page that is not
  JSON is rejected and nothing is written; an unreachable URL is named; three refused
  schemes; a failed script download leaves the previous copy intact.
- **`tests/test_services.py`** (+3): init configured / not configured / unreachable, with
  `init.ok` true every time and the old copy's date reported.
- **`tests/test_genie_manifest.py`** (2): the example parses; every bad manifest is one
  `SourceError`.
- **`tests/test_genie_source.py`** (16): the behaviour list — lazy loading, empty answers,
  search, mcp-only, tool-only, tool+mcp in both directions, unregistered uninstall, failed
  script, force, conflict before asking, missing `claude`, token never in a label or
  error, environment value offered, required input missing, unknown placeholder.
- **`tests/test_helpers.py`** (4): `run`'s `env` and `label`.
- **`tests/test_sources.py`**: precedence is `["genie", "skillhub"]`.
- **`tests/test_cli.py`**: install → list → uninstall of a genie MCP end to end, a skill
  still reaching skillhub with genie first, search listing genie MCPs, and no token in the
  kit home.

---

## Cut in review, and why

The first version was ~670 lines over six files. All of this went, and none of it was
behaviour that had been verified against the real `claude` CLI:

| Cut | Why |
|---|---|
| https at runtime, the `fetch_script` temp dirs, `loader.py` | Runtime stays local. Downloading came back afterwards, but only in `ck init` (`download.py`), which copies everything once. |
| Skip-and-warn validation: the warnings tuple, the duplicate check, the type helpers | A trusted manifest with a mistake should fail loudly, not half-load. |
| Script path checks (absolute, `..`, `:`, platform names) | They defended against a hostile manifest, and ours already runs scripts. |
| `get_placeholders` and placeholder validation at parse time | Filling already finds an unknown placeholder; it is reported then, before any script runs. |
| `commands.py` and the `Runner` protocol | One private `_claude_mcp` helper does the same. |
| `helpers/prompt.py` and the `Question` protocol | `ask` only ever asks for a `GenieInput`; it lives next to `collect_inputs`. |
| `claude mcp get` after `add-json` | `add-json` exiting 0 is enough. |
| Best-effort rollback (`_undo_install`) | Rollback is mission 9; scripts are idempotent. |
| The `environ` parameter | Tests use `monkeypatch.setenv`. |

Kept on purpose: `env`/`label` on `run`, lazy loading, the `claude mcp get` check before
prompting, matching only Claude's exact "No MCP server named" wording, `***` for secrets in
messages, and `[]` for uninstalling an MCP that is not registered.

---

## Verified against the real `claude` CLI

Run on Windows with a throwaway `ck-genie-smoke` entry in a scratch kit home, before and
after the slimming — the results were the same. After the init download was added, the
same entries were served from `http.server` on 127.0.0.1: `ck init` copied the manifest,
and the scripts into `home/genie/`; install and uninstall then ran from that
copy with no URL set; with the server stopped, init warned "unreachable ... keeping the
copy from <date>" and still exited 0. The checks:

- `ck install mcp` registers it in user scope; characters like `& | < > " % ^` in the JSON
  arrive intact.
- `ck list` shows it from `genie`; a second install exits 6.
- `ck uninstall` removes it from Claude Code and from `ck list`.
- A PowerShell script gets the inputs as env vars; a failing one shows its stderr, exits 1.
- A missing required input exits 2.
- The token is nowhere in the kit home.

## Done when

- `ck search mcp ""` lists the manifest's MCPs from source `genie`.
- `ck install mcp gitlab` asks for the token (hidden), and afterwards `claude mcp get gitlab`
  shows it in user scope. `ck list` shows it.
- `ck uninstall mcp gitlab` removes it from Claude Code and from `ck list`.
- `ck install tool kubectl` runs the script for this platform with the inputs as env vars.
- `ck install skill x` still reaches skillhub.
- The token appears nowhere in `~/.claude-kit/`, in the output or in an error message.
- All tests are green, and `lint-imports` passes with no new contract exceptions.

## Out of scope

- `agent` and `plugin` kinds.
- `--upgrade` and version comparison: missions 4 and 7.
- The recommended-package catalog: mission 6. That is a different file from this manifest.
- Rollback: mission 9.
- Writing `.mcp.json` or `managed-mcp.json`.

## Still open

1. **Windows `NUL` stdin:** Python reports stdin redirected from `NUL` (`< /dev/null`) as a
   terminal, so `ask` prompts instead of falling back to the environment, and `getpass`
   reads the console anyway and waits. `ck init`'s confirm has the same bug. Piped stdin
   works. Fix: a Windows console check where `ask` tests for a terminal.
2. **Script checksums:** a `sha256` per script — less pressing now that the manifest is
   always a local, team-owned file.
3. **Windows scripts:** PowerShell only, or also `.sh` through Git Bash for teams in MINGW?
   Today a non-`.ps1` script runs with `bash`, so `.sh` on Windows works only if `bash` is
   on PATH.
4. **`KIT_HOME` and `--home`:** `KIT_HOME`, the scripts' `CLAUDE_KIT_HOME` and the genie
   folder `GenieSource` reads all follow the `CLAUDE_KIT_HOME` variable, not `ck --home`.
   (`ck init --home X` downloads into `X/genie/`, which genie only reads when `X` is also
   `CLAUDE_KIT_HOME`.)
5. **The real URL:** `DEFAULT_GENIE_MANIFEST_URL` is `""` until we fill in the GitLab raw
   URL.
