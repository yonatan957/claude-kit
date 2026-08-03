# Quickstart: Validating the claude-kit System End-to-End

This guide proves the feature works by walking through every user story in [spec.md](./spec.md) against a real (or fixture) Catalog Repo. It intentionally does not include implementation code — see [contracts/](./contracts/) for the exact interfaces being exercised and [data-model.md](./data-model.md) for the state each step should produce.

## Prerequisites

- A claude-kit build (or `python -m src.cli` during development) on `PATH`.
- An isolated `$HOME` (or `%USERPROFILE%`) for the test run, so `~/.claude/`, `~/.claude-kit/`, and `~/.claude-kit-repo/` don't touch a real developer setup.
- A reachable (or local fixture) Catalog Repo containing at least: one `content`-handler skill, one `script`-handler tool with a non-secret input, one `script`-handler MCP server with a secret input, and one `marketplace`-handler plugin.
- Claude Code itself installed and recognizable in the isolated environment (per FR-001).

## Story 1 — First-Time Setup and Interactive Configuration (P1)

1. Run `claude-kit init`.
   - **Expect**: exit code `0`; `~/.claude-kit/` and `~/.claude-kit-repo/` created; `CLAUDE.md` gains exactly one new line referencing `genie-claude.md`; the picker (Step 1) launches automatically.
2. **Before touching anything**, confirm the inline presentation (FR-045/FR-046): the picker rendered *below* your shell prompt, your previous terminal output is still visible above it, and scrolling up reaches your pre-existing scrollback. The screen was not cleared and no full-screen frame was drawn. On screen there is only the counts line, the list, and a one-line key hint — no header bar, no footer widget, no theme control, no buttons.
3. In the picker: navigate with arrow keys, press `Enter` on the fixture skill and the fixture MCP server to select them, confirm their category counters increment and each row's marker changes from `[ ]` to a green `[✓]`. Move the highlight up and down across those rows and confirm the markers stay visible and unchanged (FR-047).
4. Press `Tab` to enter search mode, type part of the fixture tool's name, press `Enter` on the match to select it, then press `Tab` again to return to browsing — confirm it is now pinned near the top. Verify there is no "exit search" row or button anywhere: `Tab` is the only way in and out (FR-009).
5. Confirm the legacy shortcuts are gone: pressing `a` in browse mode does nothing (it must not approve), and `Space` does not toggle selection (FR-007/FR-012).
6. Navigate to the **"Approve & Install"** row at the bottom of the list and press `Enter`.
   - **Expect**: skill files appear under `~/.claude/skills/`; the tool and MCP server are installed; Step 2 launches automatically for the tool and MCP server (they declared `inputs[]`).
7. In Step 2, enter the tool's plain input, then the MCP server's secret input (confirm it is masked on screen).
   - **Expect**: `~/.claude-kit/installed.json` shows both components with `config.status = "done"`; `~/.claude-kit/env.d/<mcp-name>.env` exists with the real secret; `installed.json`'s `answers` field for that input is the literal string `"<set>"`, never the real value (validates FR-016/FR-039/SC-003); `claude_settings.json`'s `mcpServers` key contains the new entry while every pre-existing key in that file is byte-identical to before (validates FR-038/SC-007 — diff the file before/after).
8. After the flow exits, confirm the picker's final frame is still present in scrollback like ordinary command output, and that everything printed before `claude-kit init` is still reachable by scrolling up (validates SC-010).
9. Re-open the picker, press `Enter` on the fixture skill to deselect it, and confirm its marker becomes a red `[X]` flagging it as a pending removal before approving.

## Story 2 — Scripted Add and Remove (P2)

1. Run `claude-kit add tools <fixture-tool-name>` against a clean install.
   - **Expect**: no interactive picker appears; the command drives Step 2 configure prompts directly if inputs are required; exit `0`.
2. Run `claude-kit remove tools <fixture-tool-name>`.
   - **Expect**: exit `0`; entry gone from `installed.json`.
3. Run `claude-kit add tools not-a-real-component`.
   - **Expect**: non-zero exit, clear error message, no entry written to `installed.json`.

## Story 3 — Keeping Installed Components in Sync (P3)

1. With the fixture MCP server installed and `"done"`, advance the fixture catalog's `version` for that component (simulating upstream content changing).
2. Run `claude-kit update`.
   - **Expect**: process never pauses for input; exit `0`; the component's content is refreshed; its stored secret is still present in `env.d/` and was not re-prompted; the run's printed summary lists any component now `"pending"`.
3. Run `claude-kit update` again immediately with no further catalog changes.
   - **Expect**: resulting `installed.json` is identical to after the first run (diff both — validates FR-025/SC-002).
4. Set the fixture catalog's `min_cli_version` above the test build's own version, run `update` again.
   - **Expect**: non-zero exit, clear message instructing an upgrade, zero changes applied.

## Story 4 — Discovering Current State (P4)

1. With a mix of installed/not-installed/pending components from the steps above, run `claude-kit list`.
   - **Expect**: **only the installed components appear** — every fixture catalog component that was never installed is absent from the output entirely (validates FR-026). Each listed component is correctly labeled current/outdated, done/pending, active/inactive; the pending one is visually distinguishable from the done ones. There is no `INSTALLED` column.
2. Remove a component from the fixture catalog while leaving it installed locally, then run `claude-kit list` again.
   - **Expect**: the orphaned component still appears, with its freshness column reading `unknown` rather than being hidden.
3. Against a fresh `$HOME` with a synced catalog but nothing installed, run `claude-kit list`.
   - **Expect**: exit `0` and a single empty-state line naming `claude-kit config` — not a bare header with no rows.

## Story 5 — Passive Awareness at Session Start (P5)

1. Run `claude-kit check` manually (simulating the detached child the startup hook would spawn) against a fixture with a newer CLI version and at least one pending component.
   - **Expect**: `~/.claude-kit/state.json` is written with a non-null `message` and matching `findings`; command exits `0` with no interactive output.
2. Invoke the startup hook's read path (`notify/hook.py` equivalent) directly.
   - **Expect**: the exact `message` string from `state.json` is printed verbatim, with no measurable delay (no network/git/subprocess calls on this path — validates Principle V/SC-004).
3. Re-run the hook path a second time with no new `check` run in between.
   - **Expect**: same message printed again only if it hasn't been recorded in `announced` yet; run `check` once more with identical findings, then re-run the hook — the message must not repeat (validates FR-032/SC-009).

## Full-system idempotency pass (Principle IV)

Run the entire sequence above a second time end-to-end from the same populated state (skip `init`). Diff `installed.json`, `state.json`, and `claude_settings.json` before and after. Nothing should differ except timestamps (`last_updated`, `checked_at`, `verified_at`) — no duplicate entries, no duplicate `mcpServers` registrations, no duplicate `CLAUDE.md` reference lines.
