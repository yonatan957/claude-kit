# Mission 2 — The genie source

**Status:** `todo` — plan written, waiting on approval.

**Goal:** a second source, `genie`, first in precedence, that installs and removes two
kinds SkillHub cannot serve:

- **`mcp`**: MCP servers, registered with Claude Code through `claude mcp add-json` /
  `claude mcp remove`, never by editing `~/.claude.json`.
- **`tool`**: anything that needs an installer, installed and removed only by scripts the
  manifest names.

One entry can be both: a script installs the binary, then genie registers it as an MCP.

**Also in this mission:** `sources/available.py` is renamed to `sources/index.py`.

---

## How it works

```
ck install mcp gitlab
  1. genie loads the manifest (once per process, only when first asked)
  2. no entry called gitlab of kind mcp?  -> return []  (falls through to skillhub)
  3. the entry declares inputs            -> ask the user, interactively
  4. the entry has an install script      -> run it, inputs passed as env vars
  5. the entry has an mcp block           -> fill {PLACEHOLDERS} from the inputs,
                                             claude mcp add-json <name> <json> --scope user
                                             claude mcp get <name>   (verify)
  6. return the component                 -> install_service records it in installed.db
  7. the input values are dropped         -> nothing is stored by the kit
```

Uninstall runs the other way: `claude mcp remove` first, then the uninstall script, so
Claude Code is never left pointing at a binary that is gone.

### Decisions this plan takes

| Question | Decision |
|---|---|
| Where MCPs are written | Only through `claude mcp`. Always `--scope user`. |
| Where input values are stored | Nowhere. Asked on every install; `--force` reinstalls to change one. |
| How values reach the script | As environment variables of the script's process only. `os.environ` is not touched. |
| Who registers the MCP for a tool+mcp entry | genie, not the script. Scripts install binaries and know nothing about Claude. |
| Manifest format | JSON. No new dependency. |
| Network at import time | None. `GenieSource()` is built when `sources/index.py` is imported, so the manifest loads lazily. |
| Not in the manifest | `[]`, never an error, so the request falls through to the next source. |

---

## The manifest

Location comes from `GENIE_MANIFEST_URL`: an `https://` URL or a local path. Script paths
in the manifest are relative to the manifest's own location.

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

### Validation rules (`manifest.py`)

- `kind` is `mcp` or `tool`. Other kinds are skipped for now.
- `name` and `version` are required. `(kind, name)` is unique in the manifest.
- A `tool` entry needs `install` **and** `uninstall`.
- An `mcp` entry needs an `mcp` block. `install` is optional, but if it is there,
  `uninstall` has to be there too.
- Every `{PLACEHOLDER}` in `mcp` is either a declared input key or a built-in
  (`KIT_HOME`). An unknown placeholder makes the entry invalid.
- A malformed **entry** is skipped and reported as a warning. A malformed **file** (not
  JSON, wrong `manifest_version`) is a `SourceError`.
- An entry with no script for the current platform cannot be installed here:
  `SourceError("k8s has no installer for windows")`.

### Rules for scripts (documented for whoever writes them)

- Exit 0 means success. Anything else is a failure, and its stderr is shown to the user.
- Not interactive: stdin is closed. Every value comes in as an env var.
- Idempotent: running it a second time does not break anything.
- Environment it gets: the inputs, plus `CLAUDE_KIT_HOME`, `GENIE_NAME` and
  `GENIE_VERSION`.
- `.ps1` runs with `powershell -NoProfile -ExecutionPolicy Bypass -File`, `.sh` with `bash`.

---

## Files

### Renamed

**`src/claude_kit/sources/available.py` → `src/claude_kit/sources/index.py`**
- Content is unchanged except for one line:
  `AVAILABLE_SOURCES: list[Source] = [GenieSource(), SkillHubSource()]`
- The constant names (`AVAILABLE_SOURCES`, `get_source`, ...) stay, so no caller has to
  change.

**`src/claude_kit/sources/__init__.py`**
- `from claude_kit.sources.index import ...` instead of `.available`.
- Exports `GenieSource`.

### New: `src/claude_kit/sources/genie/`

One source, split only so no file grows too large. Nothing outside this folder imports
anything from inside it except `GenieSource`.

**`genie/__init__.py`**
- `from claude_kit.sources.genie.genie_source import GenieSource`

**`genie/manifest.py`**: what the manifest says. No I/O.
- `GenieInput(key, description, help="", secret=False, required=False, default="")`
- `GenieEntry(kind, name, version, description, inputs, install, uninstall, mcp)`, where
  `install`/`uninstall` are `Mapping[platform, relative_path]` and `mcp` is a dict or None.
- `Manifest(entries, warnings, base)` with `find(kind, name)` and `search(kind, query)`.
- `parse_manifest(payload: dict, base: str) -> Manifest`: applies the validation rules
  above.
- `current_platform() -> "windows" | "linux" | "macos"`

**`genie/loader.py`**: getting the manifest and its scripts onto this machine.
- `load_manifest(location: str) -> Manifest`: a local path is read from disk; `https://`
  is fetched with `urllib.request` and `TIMEOUT`. A network or read failure is
  `SourceUnreachable`.
- `fetch_script(manifest, relative_path) -> Path`: a local manifest resolves the path next
  to it; a remote one downloads into a temp dir that is removed after the run.

**`genie/inputs.py`**: asking for values and filling them in.
- `Prompter = Callable[[GenieInput, str | None], str]`. The second argument is the value
  already in the environment, if there is one, offered as the default.
- `collect_inputs(entry, prompter, environ) -> dict[str, str]`
  - The value already in `environ` is offered as `[already set, Enter to keep]`.
  - Required and empty after the prompt: `UsageError("GITLAB_TOKEN is required")`.
- `fill_placeholders(mcp: dict, values: dict) -> dict`: recursive over strings in
  dicts and lists.

**`genie/commands.py`**: everything genie runs, through `helpers.system.run`.
- `run_script(path, env) -> CommandResult`: chooses powershell or bash by extension.
- `mcp_add(name, config) -> CommandResult`:
  `claude mcp add-json <name> <json> --scope user`, run with `label=f"claude mcp add-json {name}"`
  so the JSON (which holds the token) never appears in a message.
- `mcp_remove(name) -> CommandResult`
- `mcp_exists(name) -> bool`: `claude mcp get <name>` exits 0.

**`genie/genie_source.py`**: `GenieSource(Source)`
- `kinds = frozenset({ComponentKind.MCP, ComponentKind.TOOL})`, `name = "genie"`
- `__init__(location=GENIE_MANIFEST_URL, prompter=None, runner=None, environ=None)`:
  everything injectable, so the tests never touch the network, a process or a terminal.
- `_manifest()`: loaded on first use and kept for the rest of the process.
- `search(kind, query)`: `manifest.search` mapped to `ClaudeComponent`.
- `install(kind, name, force)`:
  1. `entry = manifest.find(kind, name)`; `None` → `[]`
  2. `values = collect_inputs(...)`
  3. If `entry.install`: `run_script`. Failure → `SourceError` with the script's stderr.
  4. If `entry.mcp`:
     - `force` → `mcp_remove` first; "not found" is fine.
     - `mcp_add`; "already exists" → `Conflict`.
     - `mcp_exists`, or else `SourceError("gitlab was added but claude mcp get cannot see it")`.
     - If this step fails after a script ran, run the uninstall script (best effort),
       then raise. Full rollback is mission 9.
  5. Return `[ClaudeComponent(kind, name, "genie", description, version)]`.
- `uninstall(kind, name)`:
  1. Not in the manifest → `[]`
  2. If `entry.mcp`: `mcp_remove`; "not found" counts as already gone.
  3. If `entry.uninstall`: `run_script`. Failure → `SourceError`.
  4. Return the component.
- Error mapping, the same as skillhub: exit 127 (`claude` not on PATH) → `SourceUnreachable`.

### Changed

**`src/claude_kit/helpers/system.py`**: `run()` gains two keyword arguments:
- `env: Mapping[str, str] | None = None`: passed to `subprocess.run` as
  `{**os.environ, **env}`.
- `label: str | None = None`: replaces `" ".join(command)` in `CommandResult.command`, so
  a caller can keep secrets out of it.

**`src/claude_kit/helpers/prompt.py`** (new, in `helpers` because it is plain terminal I/O)
- `ask(item: GenieInput-like, current: str | None) -> str`: prints description and help,
  uses `getpass.getpass` for secrets and `input` otherwise.
- With no terminal (`not sys.stdin.isatty()`) it does not wait: a required value that is
  not already in the environment raises `UsageError` that names every missing key.
- So that `helpers` does not import from `sources`, it takes a small `Protocol`
  (`key`, `description`, `help`, `secret`, `default`) rather than `GenieInput` itself.

**`src/claude_kit/helpers/consts.py`**
- `GENIE_MANIFEST_URL = os.environ.get("GENIE_MANIFEST_URL") or ""`. Empty means genie
  answers `[]` to everything and says so once, so the kit still works without it.
- `GENIE_LABEL = "genie"`, `MCP_SCOPE = "user"`

**`src/claude_kit/__init__.py`**: export `GenieSource` beside `SkillHubSource`.

**`src/claude_kit/components/component.py`**, **`storage/*`**, **`services/*`**: no change.
genie answers in the same `ClaudeComponent` shape, and the services already record and
remove it.

**`MISSIONS.md`**: section 2 points here.

### Tests

**`tests/data/genie/manifest.json`**: the three example entries above, plus scripts that
only `echo` and `exit 0`/`exit 1`.

**`tests/fakes.py`**
- `FakeRunner`: records every command and env, and answers from a table
  (`("mcp", "add-json")` → 0, and so on).
- `FakePrompter`: answers from a dict and records what it was asked.

**`tests/test_genie_manifest.py`**
- A valid manifest parses into three entries.
- Each validation rule: missing uninstall, unknown placeholder, duplicate name, unknown
  kind. Each one skips the entry and adds one warning.
- A file that is not JSON is a `SourceError`.

**`tests/test_genie_source.py`**
- A name not in the manifest: `install`, `uninstall` and `search` answer `[]`, and the
  runner is never called.
- `mcp` only: `add-json` is called with filled placeholders and `--scope user`, and no
  script runs.
- tool only: the script runs with the inputs in its env, and `claude` is never called.
- tool + mcp: the script runs first, then `add-json`. On uninstall the order is reversed.
- `add-json` fails after the script ran: the uninstall script runs, and a `SourceError`
  is raised.
- `--force` removes first, then adds.
- "already exists" without force is a `Conflict`.
- The token never appears in `CommandResult.command` or in any error message.
- `claude` not found is `SourceUnreachable`.
- An input already in the environment is offered and used. A required one that is left
  empty is a `UsageError`.
- `GenieSource()` makes no call at construction time.

**`tests/test_sources.py`**: imports from `claude_kit.sources.index`. Precedence is
`["genie", "skillhub"]`.

**`tests/test_cli.py`**: one end-to-end with a fake genie: `ck install mcp gitlab`, then
`ck list` shows it with source `genie`, then `ck uninstall` removes it.

---

## Order of work

1. Rename `available.py` → `index.py`. Run the tests: green, nothing else changed.
2. `helpers/system.run`: `env` and `label`, plus tests.
3. `genie/manifest.py` and its tests. No I/O yet.
4. `genie/inputs.py` and `helpers/prompt.py`.
5. `genie/commands.py` and `genie/genie_source.py`, MCP-only path first.
6. Script path (tool and tool+mcp).
7. `genie/loader.py`: local path first, then `https://`.
8. Register in `index.py`, then the CLI end-to-end test.
9. `pytest`, `lint-imports`, `ruff`, `mypy`.

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

- `agent` and `plugin` kinds (`claude plugin ...` comes later, through the same kind of
  command).
- `--upgrade` and version comparison: missions 4 and 7.
- The recommended-package catalog: mission 6. That is a different file from this
  manifest.
- Full rollback: mission 9. Here it is only best effort, the uninstall script after a
  failed registration.
- Writing `.mcp.json` or `managed-mcp.json`.

## Open questions

1. **Default for `GENIE_MANIFEST_URL`:** a GitLab raw URL, an internal static server, or
   empty until set?
2. **Script checksums:** require a `sha256` per script in the manifest now, or once the
   manifest is remote?
3. **Windows scripts:** PowerShell only, or also `.sh` through Git Bash for teams that
   live in MINGW?
