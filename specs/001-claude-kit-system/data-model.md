# Phase 1 Data Model: claude-kit System

Source entities are defined in [spec.md](./spec.md#key-entities). This document makes them concrete enough to implement against, mapped onto the three JSON engines. Field names below are the ones this plan commits to; they are internal to claude-kit and do not need to match any external system.

## Engine 1 — Catalog (`registry.json`, synced to `~/.claude-kit-repo/registry.json`)

Read-only from claude-kit's perspective; owned by the remote Catalog Repo.

| Field | Type | Notes |
|---|---|---|
| `schema_version` | string | Structural version of this file's own shape. A mismatch claude-kit doesn't understand is a hard error surfaced to the user, never silently ignored. |
| `version` | string | Content version of the catalog (bumped whenever any component entry changes). |
| `min_cli_version` | string | Gate for `update` (FR-022): if the running CLI version is older, `update` halts before making any change. |
| `types[]` | array of `{ name, handler }` | Declares each category (`skills`, `agents`, `plugins`, `tools`, `mcps`) and which handler (`content`, `script`, `marketplace`) installs/removes it. |
| `plugin_marketplace` | object | Exact shell command templates for add/install/update/remove of plugins, consumed only by `installers/marketplace.py`. |
| `skills`, `agents`, `plugins`, `tools`, `mcps` | map of name → **Component** | See Component below. |

### Component (an entry inside one of the five maps above)

| Field | Type | Notes |
|---|---|---|
| `description` | string | Shown in the picker and `list`. |
| `handler` | string | One of `content`, `script`, `marketplace`; must match the category's declared handler in `types[]` (validation rule: reject registry if mismatched). |
| `files[]` | array of `{ path, hash }` | Present for `content`-handler components; drives both install (copy) and drift detection (compare against `installed_hash`). |
| `inputs[]` | array of `{ name, label, secret: bool }` | Declares what Step 2 configuration must collect; `secret: true` triggers masked entry (FR-015) and restricted storage (FR-016). |
| `mcp_config` | object \| null | Present only for `mcps`; the exact block to merge into `claude_settings.json`'s `mcpServers[name]`. |
| `version` | string | Component-level content version, used for the "up to date vs. outdated" comparison surfaced by `list` (FR-026) — looked up *from* the catalog for each installed entry, since `list` now iterates `installed.json` rather than the catalog. |

**Validation rules**: every component's `handler` must be one of the three known handlers; every `content` component must declare at least one file; every `script`/`mcps` component's declared `inputs[]` names must be unique within that component (edge case from spec: two components may reuse an input name across *different* components — answers are still kept separate because they're stored per-component, per Installed Record below, never in a single flat namespace).

## Engine 2 — Installed Record (`installed.json`, at `~/.claude-kit/installed.json`)

The machine's ground truth. Owned exclusively by claude-kit; upserted by name (map, never a list) so re-running any install/removal is a pure overwrite — this is what makes FR-025/FR-037 (idempotency) structural rather than a behavior claude-kit has to remember to implement carefully.

| Field | Type | Notes |
|---|---|---|
| `state_version` | string | Structural version of this file's shape (claude-kit-owned migration key). |
| `last_updated` | ISO 8601 timestamp | Set on every successful `update`. |
| `catalog_commit` | string | The Catalog Repo commit hash last synced, feeding `check`'s drift comparison. |
| `registry_version` | string | Mirrors the synced `registry.json`'s `version`. |
| `cli_version` | string | Version of the claude-kit binary that last wrote this file. |
| `skills.<name>`, `agents.<name>` | object | `{ source: "claude-kit" \| "user", installed_hash, installed_at }` |
| `plugins.<name>` | object | `{ source, marketplace, version, enabled }` |
| `tools.<name>`, `mcps.<name>` | object | `{ source, version, installed_hash, config: { status: "pending" \| "done" \| "failed", verified_at, answers: { <input-name>: "<set>" } } }` |

**State transitions (script/mcp components' `config.status`)**:

```text
(not installed) → "pending"   [install.sh/config.sh ran, verify.sh not yet run or awaiting inputs]
"pending" → "done"            [verify.sh succeeds] (FR-035)
"done" → "pending"            [update introduces a new required input (FR-024), OR
                                a re-run verify.sh during update fails (FR-044)]
"pending"/"done" → "failed"   [verify.sh fails after mcp_config was already registered (FR-042);
                                the mcp_config registration is rolled back immediately in this case]
"failed" → "pending"          [developer re-runs add/config with corrected inputs]
(any) → (entry removed)       [remove completes: mcp_config stripped, uninstall.sh run, secrets deleted, entry deleted (FR-036)]
```

**Validation rules**: `source` is always exactly `"claude-kit"` or `"user"`; a `"user"`-sourced entry is created only by the naming-collision-acknowledgment path (FR-043) — never written implicitly; `answers` values are always the literal string `"<set>"`, never a real value (FR-039) — this is enforced at the boundary where `installers/script.py` hands data to `core/state_model.py` for persistence, not left to caller discipline.

## Engine 3 — Notification Snapshot (`state.json`, at `~/.claude-kit/state.json`)

Written only by `claude-kit check`; read only (never written) by the session-start hook.

| Field | Type | Notes |
|---|---|---|
| `notice_version` | string | Structural version of this file's shape. |
| `checked_at` | ISO 8601 timestamp | When the background check last ran; gates how often `check` re-runs its (relatively expensive) comparisons. |
| `check_interval_hours` | number | Minimum hours between full checks. |
| `message` | string | The single, fully pre-rendered string the startup hook prints verbatim (FR-030/FR-031) — never assembled at hook time. |
| `findings` | object | `{ local_commit, remote_commit, local_cli_version, latest_cli_version, pending_config_count }` — the raw data `message` was rendered from, kept for `list`/debugging, never re-parsed by the hook. |
| `announced` | array of strings | Identifiers (e.g., `"cli:2.4.0"`, `"catalog:9f1a3c"`) already shown to the developer, so the same finding is never shown twice (FR-032/SC-009). |

**Validation rule**: `message` is `null`/absent whenever `findings` indicates nothing new beyond what's already in `announced` — this is what lets the hook do a trivial "is there a message? print it" check with no comparison logic of its own (Principle V).

## Cross-cutting: Credential

Not a JSON-engine field itself — a **Credential** is a secret input value, keyed by `(component-name, input-name)`, persisted as one file per component under `~/.claude-kit/env.d/` (e.g., `env.d/<component-name>.env`), written once by the script handler's config step and never re-read by anything except that same component's own config/verify scripts. Its only representation inside any of the three JSON engines is the masked `"<set>"` placeholder in `installed.json`.

## Cross-cutting: Picker Interaction State (in-memory only)

Transient, never persisted — it exists only for the lifetime of one `claude-kit config` run, and is the model the inline TUI renders. Defined in `ui/state.py` with no `prompt_toolkit` imports, so it is unit-testable without a terminal.

**`PickerEntry`** (`ui/entry.py`) — one per catalog component in scope:

| Field | Type | Notes |
|---|---|---|
| `category`, `name`, `component` | — | Identity plus the catalog record being offered. |
| `currently_installed` | bool | Seeded from `installed.json` at launch; never mutated. |
| `selected` | bool | Seeded equal to `currently_installed`; toggled by `Enter`. |
| `pinned` | bool | Set when selected while in search mode; floats the entry to the top on return to browsing (FR-010). |
| `naming_collision` | bool | A manually-placed item shares this name (FR-043) — rendered as a warning prefix. |

**Derived selection state** (`SelectionState`, the only input to the checkbox glyph — FR-047):

| State | Condition | Glyph |
|---|---|---|
| `PENDING_REMOVAL` | `currently_installed and not selected` | `[X]` red |
| `SELECTED` | `selected` | `[✓]` green |
| `UNSELECTED` | otherwise | `[ ]` default |

**`PickerState`** — `entries: list[PickerEntry]`, `mode: BROWSE | SEARCH`, `query: str`, `cursor: int`. The visible row list is derived, never stored: in `BROWSE` it is pinned entries, then the rest, then a single sentinel **approve row**; in `SEARCH` it is entries matching `query`, with no approve row. `cursor` indexes that derived list and is clamped on every mode change or re-filter. `activate()` (bound to `Enter`) returns `TOGGLED` or `APPROVED` depending on whether the cursor rests on the sentinel row — the only path to approval (FR-012).

## Relationships

```text
Catalog.types[].handler  ──determines──▶  which installers/*.py module runs
Catalog.<category>.<name>  ──diffed against──▶  Installed Record.<category>.<name>  ──produces──▶  add/remove/update plan
Installed Record.<category>.<name>  ──iterated by──▶  list_cmd.build_rows()  ──enriched from──▶  Catalog.<category>.<name>  (absent ⇒ freshness "unknown")
Catalog + Installed Record  ──seed──▶  PickerState.entries  ──Enter/Tab──▶  desired selection  ──diffed──▶  add/remove plan
Installed Record.tools/mcps.<name>.config.answers  ──masks──▶  Credential file contents (env.d/<name>.env)
Notification Snapshot.findings  ──rendered into──▶  Notification Snapshot.message  ──printed verbatim by──▶  notify/hook.py
```
