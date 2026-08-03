# Development Guide

How to set up, test, try out interactively, build a binary from, and package
this repo for npm. See [`README.md`](README.md) for what claude-kit *is*;
this file is about building and shipping it.

Commands below are for **Git Bash** (or any POSIX-style shell). Paths under
`.venv/Scripts/` are correct for a Windows venv even when invoked from bash.

## Prerequisites

- Python 3.11+
- `git` on PATH
- `bash` on PATH (Git Bash on Windows) — the script-handler install/remove
  lifecycle (tools/MCP servers) shells out to it
- Node.js 16+ — only needed for the npm packaging steps (§5)

## 1. Set up

```bash
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"
```

## 2. Run the test suite

```bash
.venv/Scripts/python -m pytest
```

95 tests: unit, contract (JSON schema validation), and integration tests —
including one (`tests/integration/test_full_idempotency.py`) that drives
every command through a full add → update → list → check cycle twice and
diffs the result.

## 3. Try it yourself, interactively

The picker and configure screens need a real interactive terminal — they
can't be driven through automation, so this part only works if you run it
in your own terminal window.

claude-kit writes to `~/.claude`, `~/.claude-kit`, etc., and the only
"catalog" that exists so far is a fixture one used for tests
(`tests/fixtures/registry_repo/`) — not real content. So set up an isolated
fake home first rather than pointing it at your real Claude Code setup.

This sandbox lives under `.demo/` in the project root (gitignored) rather
than the system temp dir, so it's easy to find and inspect between runs —
**double-check `echo "$DEMO"` below actually points inside this repo before
running `init`**, since `init` really does write to whatever `$HOME`/
`$USERPROFILE` resolve to at that moment:

```bash
# Isolated fake home, inside this project (nothing touches your real ~/.claude)
DEMO="$(pwd)/.demo"
mkdir -p "$DEMO/home/.claude"
echo "$DEMO"   # sanity-check this before continuing

# Turn the fixture catalog into a real local git repo (claude-kit syncs via git clone/pull)
rm -rf "$DEMO/catalog_repo"
cp -r tests/fixtures/registry_repo "$DEMO/catalog_repo"
git -C "$DEMO/catalog_repo" init -q
git -C "$DEMO/catalog_repo" add -A
git -C "$DEMO/catalog_repo" -c user.email=demo@demo.com -c user.name=demo commit -q -m "fixture catalog"

# Point claude-kit at the demo home + demo catalog (this shell session only)
export HOME="$DEMO/home"
export USERPROFILE="$DEMO/home"
export CLAUDE_KIT_CATALOG_URL="$DEMO/catalog_repo"
```

Then:

```bash
.venv/Scripts/python -m src.cli init
```

This creates the demo dirs, deploys `genie-claude.md`, appends the reference
line to a fake `CLAUDE.md`, and drops you into the picker.

**Picker controls**: `↑`/`↓` navigate, `space` toggle select, `/` enter
search mode → type → `Tab` jumps into the filtered results → `space` to
select → `Esc` back to browsing, `a` = Approve & install, `q` = cancel.

The fixture catalog has 4 fake components. Select `fixture-skill`,
`fixture-tool`, and `fixture-mcp`, then `a` — it copies the fake skill file
and walks you through Step 2 prompts (the tool's plain input, then the MCP's
secret input, masked on screen). Skip `fixture-plugin` unless you want to
see it fail — it shells out to a literal `claude plugin marketplace add ...`
command that doesn't correspond to anything real.

Afterwards:

```bash
.venv/Scripts/python -m src.cli list
.venv/Scripts/python -m src.cli update
.venv/Scripts/python -m src.cli config      # re-open the picker
cat "$DEMO/home/.claude-kit/installed.json"
cat "$DEMO/home/.claude/settings.json"
```

To try the built binary (§4) instead of running from source, use the same
env vars and just run `dist/claude-kit/claude-kit.exe init` etc.

When done: close the shell (the env vars above are session-local) and
`rm -rf .demo` to clean up. Run `unset HOME USERPROFILE CLAUDE_KIT_CATALOG_URL`
if you're continuing to work in the same shell afterward, so nothing later
in that session accidentally targets the demo (or, having unset `HOME`,
your real one).

## 4. Build a frozen binary

```bash
.venv/Scripts/pip install -e ".[build]"
.venv/Scripts/pyinstaller claude-kit.spec
```

Output: `dist/claude-kit/` — a folder containing `claude-kit.exe` (Windows)
or `claude-kit` (macOS/Linux) plus its runtime dependencies. Run it directly
to sanity-check: `dist/claude-kit/claude-kit.exe --help`.

PyInstaller does not cross-compile — building the Windows binary requires
running this step on Windows, macOS on macOS, Linux on Linux. To support all
three platforms you need to run this step on (or in CI on) each one.

## 5. Package it for npm

The npm package (`npm/`) doesn't bundle the binary itself — `npm install`
downloads the right platform build via `npm/postinstall.js`, and
`npm/bin/claude-kit.js` execs whatever landed in `npm/dist/`. So shipping it
means: build the binary per platform (§4), publish each as a downloadable
archive, then publish the npm package pointing at them.

### A. Build the release archive per platform

`npm/postinstall.js` expects archives named `claude-kit-<platform>-<arch>.<ext>`,
where `<platform>` is `macos`/`linux`/`windows`, `<arch>` is `x64`/`arm64`,
and `<ext>` is `zip` on Windows or `tar.gz` elsewhere. The archive's contents
must be the *contents* of `dist/claude-kit/` (not the folder itself) —
`claude-kit.exe` needs to end up at the archive's top level.

Git Bash's `tar` works fine for `.tar.gz`, but its `tar` build does **not**
produce a real `.zip` despite accepting the extension — use Python's
`zipfile` (already a project dependency) for the Windows archive instead:

```bash
# macOS / Linux
tar -czf claude-kit-macos-x64.tar.gz -C dist/claude-kit .
```

```bash
# Windows (run on/for the Windows build)
.venv/Scripts/python -c "
import zipfile, pathlib
src = pathlib.Path('dist/claude-kit')
with zipfile.ZipFile('claude-kit-windows-x64.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    for f in src.rglob('*'):
        if f.is_file():
            zf.write(f, f.relative_to(src))
"
```

### B. Host the archives somewhere reachable

The easiest option is GitHub Releases:

```bash
git tag v0.1.0
git push --tags
```

Create a GitHub Release for that tag and upload each platform's archive as a
release asset. `postinstall.js` then downloads from:

```text
$CLAUDE_KIT_RELEASES_BASE_URL/v<version>/claude-kit-<platform>-<arch>.<ext>
```

so set `CLAUDE_KIT_RELEASES_BASE_URL=https://github.com/<org>/<repo>/releases/download`
wherever `npm install` will run (or bake it into `npm/postinstall.js` as a
default once you have a real host).

### C. Test the npm package locally (no real release host needed)

Skip the download — copy the binary you built straight into `npm/dist/`:

```bash
mkdir -p npm/dist
cp -r dist/claude-kit/. npm/dist/
```

Then:

```bash
cd npm
npm link
claude-kit --help    # now runs from anywhere, using the dist/ you just placed
```

Or produce an installable tarball without publishing: `npm pack`, then
`npm install -g ./claude-kit-0.1.0.tgz` in another shell/machine to test a
real install.

### D. Publish for real

```bash
cd npm
npm version <new-version>   # keep in sync with pyproject.toml's version
npm login                   # once, if not already
npm publish
```

This only works once the matching version's platform archives already exist
at `CLAUDE_KIT_RELEASES_BASE_URL` (step B) — `npm install -g claude-kit`
elsewhere will run `postinstall.js`, which needs that URL reachable.

## Current gaps

- No CI pipeline builds the platform binaries automatically — for now,
  building and uploading each platform's archive (§5A/B) is a manual step,
  or one you'd wire up as a GitHub Actions release workflow.
- `npm/postinstall.js`'s download path hasn't been exercised against a real
  release host — only its "skip gracefully with a warning when
  `CLAUDE_KIT_RELEASES_BASE_URL` is unset" path is covered.
- The Catalog Repo itself (real skills/agents/tools/MCP servers, not the
  test fixture) doesn't exist yet — that's separate content work from the
  CLI/TUI tool itself.
