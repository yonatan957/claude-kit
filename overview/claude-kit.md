# Base-Kit — Project Summary

## The purpose

Base-Kit is an internal, opt-in package manager that keeps every developer's **Claude Code setup** aligned with an organizational standard — inside a restricted/air-gapped network. It solves three problems your team has today: configs spread by copy-paste with no source of truth, no way to push an update to people who already copied something, and every machine drifting so onboarding and support become guesswork. The goal in one line: *one command keeps every machine current — opt-in, auditable, air-gap friendly.*

## What it manages

Four kinds of things, each handled the way it's naturally suited to:

- **Skills / agents** — delegated entirely to **ClawHub** (a comfortable CLI with vector search over a large skill library). The catalog stores **no skill content and has no skills folder**. A blessed skill is a *link*: `source` + `source_id` pointing at ClawHub, plus our category and a `note` explaining why we bless it. Install, uninstall and update all run through the `skill_sources` commands declared in the registry — so ClawHub owns `~/.claude/skills/` and Base-Kit never writes there. You're the source of truth for *the best*; ClawHub is the source of *all*, and the mechanism is pluggable if ClawHub is ever replaced.
- **Tools** (binaries like glab, graphify) — installed via scripts, version-tracked.
- **MCP servers** — pre-installed from your Artifactory (never `npx`-download-at-launch), plus a launch recipe injected into Claude Code's settings.
- **The org baseline** — a standard written to its **own file**, `~/.claude/genie-claude.md`. The user's `CLAUDE.md` gains exactly one `@genie-claude.md` reference line and is otherwise never read, rewritten, or reordered. Updating the baseline means replacing one file we own.

## The architecture

**Two repos + two distribution channels:**
- `claude-kit-cli` (Python: typer, rich, prompt_toolkit) — the engine. Written in Python, **frozen to a standalone binary** and published as an **npm** package to internal Artifactory, so the machine needs no Python at all. npm is already required for Claude Code and ClawHub, so this adds no new tooling. The binary is embedded in the tarball — never fetched by a postinstall script, which would break air-gapped.
- `base-kit-catalog` (Git) — the content/curation source of truth: `registry.json` + per-component scripts, guarded by a **CI validation gate** so broken content can't reach anyone.

**The component model** — the elegant core of the design. Every component can optionally declare four scripts — **install.sh / config.sh / verify.sh / uninstall.sh** — plus an **inputs** form (what to ask the user). MCPs additionally carry **mcp_config** (the launch recipe). The CLI's loop is identical for all of them:

- *installing:* install → collect inputs → config (inputs passed as env vars) → inject mcp_config → verify
- *removing:* strip mcp_config → uninstall → delete the secret file → drop from state

`uninstall.sh` exists because the config picker treats unchecking an installed item as a removal, so every type needs a defined way back out — otherwise "remove" would only mean "forget", leaving the binary on PATH and the machine drifting from `installed.json`, which is the exact drift this tool exists to prevent. It stays optional: with no script, Base-Kit removes what it owns and reports honestly that system-level artifacts were left alone. All the per-program weirdness lives in reviewable bash in the catalog, keeping the CLI generic.

**Two state files, and the whole system is the diff between them:**
- `registry.json` — what exists (one per org, in Git): `skill_sources`, curated skills, tools, mcps, `min_cli_version`.
- `installed.json` — what this user chose (one per machine); config state nests under each component, and secrets are stored only as `"<set>"` markers, never values.

## How a user experiences it

- `npm install -g claude-kit` → `claude-kit init` bootstraps everything (Claude Code check, catalog clone, baseline file + reference line), then drops into config.
- `claude-kit config` — the heart of it: **picker → configure**.
  - **One keybinding scheme everywhere:** arrows move, `enter` selects or unselects the highlighted row, `tab` toggles between the main screen and search mode, `ctrl-c` quits. One verb per key — `enter` always acts on the row you're standing on.
  - **The picker** is one list of everything with current state pre-checked, live selection counters per section, and search results pinned to the top. Selecting installs, unselecting removes — pending removals are flagged in red on their own rows.
  - **Approve & install** is the last row of the list. Reaching it means scrolling past everything you changed; `enter` there runs immediately. Nothing acts until that row.
  - **Configure** opens automatically for anything needing input; pending items are preselected, and you re-select a done item to reconfigure it (e.g. a rotated token).
  - **Recommended vs Custom** is offered based on *state, not history* — it appears only when no managed components are installed. Afterwards, `--recommended` re-aligns with the blessed set on demand.
  - **Scoped:** `claude-kit config skills` (or `agents`, `plugins`, `tools`, `mcps`) is the same picker filtered to one type — so add/remove for every type comes for free rather than being built per-type.
- `claude-kit update` — the daily command. Pulls the catalog, syncs only what you opted into. **Never interactive, never upgrades itself** — it notifies you to `npm install -g claude-kit@latest` and reports pending items rather than prompting.
- `add` / `remove` / `list` / `--version` round it out — the scriptable path for when you already know the name.

## The guarantees that make it safe to adopt

Settings are sacred (only the `mcpServers` block is touched); your `CLAUDE.md` is never rewritten; one confirmation point before anything mutates; secrets never stored by Base-Kit; auth survives upgrades; opt-in only; idempotent; update never prompts.

## The load-bearing architecture rule

**core/ never talks to a human** — no print, no prompt, no exit. Core functions take inputs and return objects. All rendering and asking lives in the frontends (commands/, ui/tui.py, and a future web/). This one rule is what makes the eventual **non-programmer GUI** (a local Flask wizard on localhost) a rendering exercise instead of a rewrite — the wizard would call the exact same core functions the TUI does. The picker's counters and removal flags, for instance, are a straight render of `plan(state, registry, selections) -> ChangePlan`, which the web UI will render as a page instead of a list.

*(One documented exception: `config.sh` may inherit the terminal, because tools like `glab` run their own interactive login. Installers hand over stdio and take it back — they still never print on their own behalf.)*

## Where it stands, and the PM framing

The architecture is designed and presentation-ready — you have a Draw.io diagram, an HTML UX walkthrough (v2), example registry/installed JSONs, and a 13-slide deck (with two empty seed-plan slides for you to fill).

The design-review feedback reframed this as a **product-adoption problem**, not just an engineering one — because if people try it and don't like it, there's no second chance. That sorts the roadmap:

- **v1 (day-one trust + adoption feel):**
  - **Safety on mutation** — every change is a transaction: snapshot `installed.json` + settings, apply, health-check what changed, then commit or revert. Settings get a stronger treatment: write to a temp file, validate it, and swap it in atomically only if it's good — so there is never a moment where Claude Code has a broken config. A failed *config* (bad token) doesn't revert the install; it just stays pending so the user can retry.
  - `revert` for last-operation undo, error logging, recommended-first, a written usage philosophy.
- **v2 (retention & scale, defined by a pilot):** metrics→Grafana, `doctor` self-diagnosis (the same health checks run over everything instead of just the diff), update hooks, adopting manually-added skills.
- **Investigating:** script format, framework-agnosticism, prior art.
- **The plan:** ship the smallest tool people can't break and immediately understand, then run a small friendly pilot before scaling.

## Open decisions

- **The settings filename** — docs say `claude_settings.json`; Claude Code's actual user settings file should be confirmed before this reaches a deck, since the temp-file swap depends on it.
- **Path layout** — the catalog clones to `~/.claude-kit-repo/` while everything else lives in `~/.claude-kit/`. Nesting the clone would make the whole footprint one directory, which matters once snapshots join logs and `env.d/`.
- **`installed.json` gaps** — MCPs and skills record no version, so `update` can't detect per-component staleness the way it can for tools; and there's no `cli_version` recording which CLI last wrote the state.
- **Naming** — the product is "Base-Kit", the CLI is `claude-kit`, the repos are `claude-kit-cli` and `base-kit-catalog`. Worth settling on one name.

## The recurring design instinct

Every good decision in this project has been the same move: **delegate to the dedicated tool rather than rebuild it.** ClawHub for skills, Artifactory for the CLI, Git for content, each tool's own config for its secrets. That's what keeps Base-Kit small — and small is what keeps it adoptable and supportable.
