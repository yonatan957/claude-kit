# Shipping `ck` as a binary and an npm package

Two layers, in this order:

1. **PyInstaller** turns the Python package into a self-contained `ck` bundle. No Python on the user's machine.
2. **npm** carries those bundles. `npm install -g claude-kit` puts `ck` on the PATH of people who have never installed Python.

The npm layer is only a delivery mechanism — it contains no logic beyond picking the right binary.

---

## Step 1 — Build the binary

PyInstaller reads an entry script and follows every import. Ours is already there: `src/claude_kit/__main__.py`.

```powershell
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --onedir --name ck `
    --distpath dist/win32-x64 `
    --copy-metadata claude-kit `
    src/claude_kit/__main__.py
```

Output: `dist/win32-x64/ck/ck.exe` plus its libraries.

### `--onedir`, not `--onefile`

`--onefile` produces one tidy `.exe`, but it unpacks itself into a temp directory **on every run** — 100–300 ms added to a command people type dozens of times a day. npm ships a directory regardless, so `--onedir` costs nothing in distribution and keeps startup instant.

### `--copy-metadata claude-kit` is not optional

`ck --version` calls `importlib.metadata.version("claude-kit")`. PyInstaller does not bundle `dist-info` metadata unless told to, so **without this flag the binary prints `claude-kit not installed`** — the fallback branch in `_print_version`, firing in a shipped build. Check it explicitly in the smoke test below.

The flag also requires the distribution to be installed in the environment you build from, or PyInstaller fails with "Unable to find package". Run `pip install -e .` first — the build machine needs it anyway to resolve `typer`.

### Keep the bundle small

PyInstaller follows optional imports inside your dependencies, and on a dev machine picks up whatever else is in `site-packages`. Left alone, this kind of build lands at 100 MB+, nearly all of it things claude-kit never touches. Exclude them:

```
--exclude-module numpy --exclude-module scipy --exclude-module pandas
--exclude-module matplotlib --exclude-module PIL --exclude-module tkinter
--exclude-module IPython --exclude-module jedi --exclude-module pytest
--exclude-module setuptools
```

Set a ceiling — around 40 MB — and fail the build above it. A bundle far over budget has picked up something it doesn't use, and nobody notices a slow download during review.

---

## Step 2 — Verify before shipping

A binary that can't report its own version isn't worth publishing:

```powershell
.\dist\win32-x64\ck\ck.exe --version   # must print "claude-kit 0.1.0", not "not installed"
.\dist\win32-x64\ck\ck.exe --help
$env:CLAUDE_KIT_HOME = "$env:TEMP\ck-smoke"
.\dist\win32-x64\ck\ck.exe init
```

Two runtime dependencies survive bundling and must exist on the user's machine — PyInstaller cannot package them:

- **`npm`**, used by `ck init` to install Claude Code.
- **`skillhub`**, which `skillhub_library` shells out to.

Both are located with `shutil.which` at runtime and report a clean error when absent, so this degrades rather than crashes.

---

## Step 3 — You cannot cross-compile

This is the constraint that shapes everything else. **PyInstaller produces a binary only for the OS and architecture it runs on.** There is no `--target`. Five platforms means five machines:

| target | built on |
|---|---|
| `win32-x64` | Windows runner |
| `darwin-arm64` | macOS 14 (Apple silicon) |
| `darwin-x64` | macOS 13 (Intel) |
| `linux-x64` | Ubuntu |
| `linux-arm64` | Ubuntu ARM runner, or QEMU |

In practice this means a GitHub Actions matrix that builds on each runner, uploads the bundles as artifacts, and a final job that assembles and publishes. Locally you can only ever produce your own platform's build — which is fine for testing, and not enough to publish.

Build Linux binaries on the **oldest** distro you support: glibc is backward compatible, not forward, so a binary built on Ubuntu 24.04 will not run on 22.04.

---

## Step 4 — One npm package per platform

Don't ship five binaries to everyone. The pattern esbuild and turbo use: a **wrapper** package that depends on five **platform** packages as `optionalDependencies`, each tagged with `os` and `cpu`. npm evaluates those fields and installs exactly the one that matches.

Each platform package is trivial — a manifest and the bundle:

```json
{
  "name": "@claude-kit/cli-win32-x64",
  "version": "0.1.0",
  "os": ["win32"],
  "cpu": ["x64"],
  "files": ["bin"],
  "license": "Apache-2.0"
}
```

with the PyInstaller output copied to `bin/`. Generate these with a script rather than by hand — five manifests kept in sync manually is five chances to publish a version mismatch.

---

## Step 5 — The wrapper package

```json
{
  "name": "claude-kit",
  "version": "0.1.0",
  "bin": { "ck": "bin/ck.js" },
  "files": ["bin/ck.js"],
  "engines": { "node": ">=18" },
  "optionalDependencies": {
    "@claude-kit/cli-darwin-arm64": "0.1.0",
    "@claude-kit/cli-darwin-x64": "0.1.0",
    "@claude-kit/cli-linux-x64": "0.1.0",
    "@claude-kit/cli-linux-arm64": "0.1.0",
    "@claude-kit/cli-win32-x64": "0.1.0"
  }
}
```

`bin/ck.js` is a shim that resolves the installed platform package and hands over control:

```js
#!/usr/bin/env node
const { spawnSync } = require("node:child_process");

const TARGETS = {
  "darwin arm64": "darwin-arm64",
  "darwin x64": "darwin-x64",
  "linux x64": "linux-x64",
  "linux arm64": "linux-arm64",
  "win32 x64": "win32-x64",
};

const target = TARGETS[`${process.platform} ${process.arch}`];
if (!target) {
  console.error(`claude-kit has no build for ${process.platform}/${process.arch}`);
  process.exit(1);
}

const executable = process.platform === "win32" ? "ck.exe" : "ck";
const binary = require.resolve(`@claude-kit/cli-${target}/bin/${executable}`);
const result = spawnSync(binary, process.argv.slice(2), { stdio: "inherit" });
process.exit(result.status === null ? 1 : result.status);
```

**`stdio: "inherit"` matters.** Without it the child's output is captured instead of streamed, and typer's colors, progress and prompts break.

**Do not add a `postinstall` that downloads the binary.** It fails offline, fails behind corporate proxies, fails in air-gapped CI, and runs network I/O at install time. `optionalDependencies` needs none of that.

---

## Step 6 — Publish, in this order

```bash
# 1. platform packages FIRST
cd packaging/npm/platforms/cli-win32-x64 && npm publish --access public
# ... repeat for the other four

# 2. the wrapper LAST
cd packaging/npm && npm publish --access public
```

Reversed, the wrapper publishes with dependencies that don't exist yet and every install in that window fails.

Scoped packages (`@claude-kit/...`) are private by default — `--access public` is required on the first publish of each, and the `claude-kit` org must exist on npm.

### Version numbers must agree

`pyproject.toml`, the wrapper `package.json`, all five platform `package.json` files, and the `optionalDependencies` pins move together. Pin them exactly (`"0.1.0"`, not `"^0.1.0"`) — a wrapper that floats onto a platform package built from different source is a debugging afternoon you don't want.

---

## Checklist

- [ ] `--copy-metadata claude-kit`, or `--version` reports "not installed"
- [ ] `--onedir`, not `--onefile`
- [ ] Excluded modules; bundle under the size ceiling
- [ ] Smoke test runs `--version` and `init` on the real binary
- [ ] Linux built on the oldest supported glibc
- [ ] `stdio: "inherit"` in the shim
- [ ] No `postinstall` download step
- [ ] Every version string identical
- [ ] Platform packages published before the wrapper
