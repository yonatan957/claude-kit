# claude-kit

One uniform way to discover, install, inspect and remove the add-ons that extend Claude
Code — **skills, agents, MCP servers, tools (tools are general system that help claude code - installed usually with installation script) and plugins** — regardless of which source they
come from.

Without it, you have to know where each add-on lives, follow a different procedure for
each, and track by hand what you installed and whether it is current. `ck` removes that:
one search finds packages everywhere, one install command brings any of them in, and one
status check tells you what is out of date.

```console
$ ck search skill "code review"
┌───────────────┬────────────────────────┬────────┬─────────┬────────────┐
│ name          │ description            │ source │ version │ popularity │
├───────────────┼────────────────────────┼────────┼─────────┼────────────┤
│ code-reviewer │ Reviews code carefully │ genie  │ 1.2.0   │ 128        │
└───────────────┴────────────────────────┴────────┴─────────┴────────────┘

$ ck install skill code-reviewer
installed code-reviewer (skill) 1.2.0 [a0f9] from genie
```

## Install

```console
npm install -g claude-kit
```

No Python is required: the npm package ships a standalone binary for your platform.

## Commands

`<kind>` is always one of `skill` · `agent` · `mcp` · `tool` · `plugin`. Every command
accepts all five with the same shape.

### `ck init`

Installs Claude Code if it is absent, then retrieves the recommended-package catalog.

Every step that runs an external program or reaches the network says what it will run and
what it will access **before** it runs. Declining a step skips it and continues — the rest
of the setup still completes, and re-running finishes what you skipped. Running it twice
leaves exactly the same state as running it once.

### `ck search <kind> [--recommend] "<query>"`

Searches every registered source in parallel and shows name, description, source, version
and popularity where the source publishes it.

- `--recommend` — only packages the main registry recommends.

An unreachable source is named, and the sources that did answer still return their results.

### `ck install <kind> <name> [--source <source>] [--upgrade]`

- `--source` — install only from that source.
- `--upgrade` — replace it if already installed.

Without `--source`, sources are consulted in precedence order (`genie` first) and the
source actually used is reported. If the package needs configuration, you are asked for
each value one at a time, and told what it is for and where it will be stored. Credentials
are never written to the manifest, logs, or a command line.

If anything fails partway, everything is rolled back — the tree is byte-identical to before
you started.

### `ck list <kind>`

Shows what is installed: name, description, version, and a four-character **tag**.

The tag is what tells two same-named packages apart. A plugin is one opaque package: the
skills and agents bundled inside it are not listed separately and cannot be removed on
their own.

### `ck uninstall <kind> <name>[:<tag>]`

Reverses everything the install added, leaving no empty directories behind.

If a name matches more than one installed package, **nothing** is removed — you get the
candidates and their tags, and choose with `name:tag`.

### `ck status`

Reports installed versus latest for claude-kit, Claude Code and the catalog, plus any
installed packages behind their source. Anything that cannot be determined reads `unknown`
rather than failing the command. The result is written to disk and survives a restart.

### `ck upgrade [--no-ck] [--no-cc] [--no-catalog]`

Upgrades only the three core components, and only those behind.

Installed packages are **never** upgraded here — `ck status` lists the ones that are
behind, and each is upgraded with `ck install <kind> <name> --upgrade`.

> `--no-cc` guarantees that *claude-kit* will not touch Claude Code. It cannot freeze
> Claude Code's version: a native Claude Code installation updates itself in the
> background.

## Exit codes

Failures are distinguishable without parsing messages.

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Unexpected failure |
| 2 | Usage error |
| 3 | Not found |
| 4 | Unreachable |
| 5 | Refused / declined |
| 6 | Conflict — ambiguous, already installed, or a file you edited |
| 7 | Rolled back — nothing changed |

Code 7 is deliberately distinct from 1: "it failed and I undid everything" is different
news from "it failed".

## Where things go

Everything lives under your Claude configuration directory (`CLAUDE_CONFIG_DIR`, or
`~/.claude`):

```text
skills/ agents/ mcp/ tools/ plugins/   installed packages
.claude-kit
├── installed.db        knowledge about which compoents are instaled
├── state.json        
├── registry/        the local copy of the main registry
└── journal/         in-flight transaction; empty in steady state
```


## Configuration

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CONFIG_DIR` | Where Claude Code's configuration lives. Defaults to `~/.claude`. |
| `CLAUDE_KIT_CATALOG_URL` | HTTPS base URL for the recommended-package catalog. |
| `CLAUDE_KIT_CATALOG_REPOSITORY` | Git URL for the main registry, used when `git` is on PATH. |

No catalog is published yet, so `ck status` reports the catalog as `unknown` until one of
those is set. That is the honest answer, not a failure.