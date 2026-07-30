# Phase 1 Data Model: Config Picker & Configure Flow

Entities below are the shapes `core/` produces and consumes. They are plain data (no behavior)
so any frontend — `ui/tui.py` today, a future `web/` — can render them without re-deriving state.

## ComponentType

A category declared by the catalog's `types[]` array (spec Key Entities: Component Type).

| Field | Type | Notes |
|---|---|---|
| `name` | string | e.g. `"skills"`, `"mcps"` — used as the section label and the `config <type>` filter argument |
| `handler` | string | `"content"` \| `"marketplace"` \| `"script"` — which install/remove mechanism this type uses (drives `core.apply`, not this feature's rendering logic) |

*Constitution III constraint*: this list is never hardcoded — `core/registry` (loaded via
`registry/catalog.py`) is the only source of the set of `ComponentType` values the picker will
ever render.

## Component

A single installable item (spec Key Entities: Component).

| Field | Type | Notes |
|---|---|---|
| `type` | ComponentType.name | which section it belongs to |
| `name` | string | catalog key, e.g. `dr-runbooks` |
| `description` | string | one-line summary shown in the list |
| `category` | string \| null | groups items within a section (e.g. "SRE / Operations") |
| `recommended` | bool | whether it's part of the org's blessed/recommended set |
| `version` | string \| null | present for tools/mcps/plugins; absent for skills/agents |
| `state` | ComponentState | see below |
| `origin` | `"catalog"` \| `<skill_source name>` | set only in search results, to label where a match came from |

### ComponentState (state machine)

```text
NOT_INSTALLED --(user selects)--> PENDING_INSTALL --(approve)--> INSTALLED
INSTALLED --(user deselects)--> PENDING_REMOVAL --(approve)--> NOT_INSTALLED
INSTALLED --(needs input, just installed)--> PENDING_CONFIGURATION --(submit ok)--> CONFIGURED
CONFIGURED --(user re-selects to redo)--> PENDING_CONFIGURATION --(submit ok)--> CONFIGURED
PENDING_CONFIGURATION --(submit fails)--> PENDING_CONFIGURATION   # stays pending, install not rolled back (FR-014)
```

Any selection change before approval is reversible by toggling again — no state left of
`PENDING_INSTALL`/`PENDING_REMOVAL` is written to `installed.json` until `core.apply` runs.

## SelectionPlan (a.k.a. `ChangePlan`)

The output of `core.plan(state, registry, selections)` (spec Key Entities: Selection Plan).

| Field | Type | Notes |
|---|---|---|
| `to_install` | list[Component] | currently `NOT_INSTALLED`, now selected |
| `to_remove` | list[Component] | currently `INSTALLED`, now deselected |
| `already_pending_configuration` | list[Component] | components needing config from a prior run, unaffected by this run's selections |
| `is_noop` | bool | true iff `to_install` and `to_remove` are both empty — drives FR-011 (skip straight to configure) |

## ConfigStep

One component's need for input (spec Key Entities: Configuration Input), produced by
`core.pending(state, registry)`.

| Field | Type | Notes |
|---|---|---|
| `component` | Component | which component this step configures |
| `inputs` | list[ConfigurationInput] | ordered form fields to collect |
| `reason` | `"newly_installed"` \| `"user_requested_reconfigure"` | why this step exists — both render identically per FR-015 |

### ConfigurationInput

| Field | Type | Notes |
|---|---|---|
| `name` | string | e.g. `JIRA_API_TOKEN` — passed to `config.sh` as an env var |
| `prompt` | string | text shown to the user |
| `help_url` | string \| null | shown alongside the prompt when present |
| `sensitive` | bool | when true, input MUST be masked as typed (FR-010) |

## ApplyResult / VerifyResult

Outputs of `core.apply` and `core.configure.submit`, consumed by the summary report (FR-013).

| Field (ApplyResult) | Type | Notes |
|---|---|---|
| `component` | Component | |
| `action` | `"installed"` \| `"removed"` | |
| `ok` | bool | |
| `detail` | string \| null | e.g. "no uninstall.sh — left on PATH" (edge case: no uninstall script) |

| Field (VerifyResult) | Type | Notes |
|---|---|---|
| `component` | Component | |
| `ok` | bool | |
| `verified` | bool | whether `verify.sh` ran and passed, distinct from `ok` (config could succeed but be unverifiable) |
| `detail` | string \| null | failure reason, surfaced to the user, component stays `PENDING_CONFIGURATION` (FR-014) |

## Validation rules (from Functional Requirements)

- A `SelectionPlan` MUST NOT be applied implicitly — only an explicit `core.apply(plan)` call,
  triggered by the approval action, MUST perform mutation (FR-005).
- `core.pending` MUST include a component whether it just installed (`newly_installed`) or was
  re-selected after being `CONFIGURED` (`user_requested_reconfigure`) — both surface identically
  to the configure wizard (FR-015).
- A `VerifyResult` with `ok: false` MUST NOT change an already-`INSTALLED` component's install
  state — only its configuration state moves back to `PENDING_CONFIGURATION` (FR-014).
- `ComponentType` values rendered by the picker MUST come from iterating the registry's declared
  types at call time, never a fixed list (Constitution III).
