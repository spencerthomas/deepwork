---
feature_id: DW-AGENT-004
title: Models, profiles, runtime, and advanced settings
release: v1
status: proposed
decision_status: blocked-on-spikes
owners: [agent, web, api]
surfaces: [agent-detail, environment-detail]
runtime_scopes: [classic, mda]
source_refs: [SRC-FE, SRC-DW, SRC-LC]
dependencies: [DW-AGENT-003, DW-CODE-001]
contract_gates: [SPIKE-CONFIG-001]
last_reviewed: 2026-07-23
---

# Models, profiles, runtime, and advanced settings

## User outcome

An agent author sees only settings that have a clear owner and enforceable contract. They can change supported portable configuration in a versioned draft, understand whether a value is application-, project-, environment-, or runtime-owned, and know exactly when it will affect a deployed agent. Prototype-only switches never masquerade as functioning controls.

## Evidence and confidence

| Claim | Evidence | Classification | Planning consequence |
|---|---|---|---|
| The prototype exposes 22 settings sections with mostly local simulated state. | `SRC-FE`, findings `FE-C01`–`FE-C22` | Direct interaction/code evidence | Every section needs an explicit disposition before migration. |
| Agent, environment, workspace, and deployment settings are currently mixed. | `SRC-FE` and `SRC-DW` | Confirmed product/IA conflict | Split ownership and move controls to the object they affect. |
| Deep Agents projects can carry model and middleware configuration. | `SRC-LC` | Documented in principle; exact portable fields vary by package/runtime | Only fields verified by the pinned Python package/project schema are editable. |
| MDA backend, checkpointer, store, profile, interpreter, and protocol controls are public mutable contracts. | Prototype/internal assumptions | Unknown, gated, or contradicted | Treat runtime facts as read-only and defer unsupported editors. |

The settings schema, provider parameter matrix, and runtime ownership probes remain outputs of `SPIKE-CONFIG-001`. This proposed plan cannot be marked implementation-ready while any editable field lacks its accepted validator and round-trip fixture.

## Scope, ownership, and non-goals

The Python agent package owns portable configuration schemas and validators. The FastAPI/PostgreSQL application service owns drafts, workspace credential references, authorization, audit, and source capability facts. The TypeScript SDK exposes typed query/mutation boundaries to Next.js and Tauri. `DW-AGENT-003` owns Save/Validate/Deploy semantics; coding plans own environment and repository settings.

This plan owns model/provider controls, the ownership/disposition map for all prototype settings, advanced-field disclosure, runtime diagnostics, and the rules for rendering editable versus read-only versus deferred settings.

Non-goals are a generic JSON/YAML editor with arbitrary execution, runtime backend selection, transport tuning as a user preference, private MDA management routes, profile/interpreter claims without a stable contract, ACP/A2A configuration in v1, secret entry into project files, and duplicate global/agent/environment screens for the same value.

## Canonical disposition of all 22 prototype sections

| ID | Prototype section | Canonical owner | v1 disposition and owning plan |
|---|---|---|---|
| `FE-C01` | Models | Agent draft | Live for verified provider/model identifier and supported safe parameters; advanced routing is capability-gated here. |
| `FE-C02` | Configuration | Field-dependent | Remove generic section; fold normalized fields into agent Configuration or Environment. No “Open config” fiction. |
| `FE-C03` | Profiles | Agent project | Later/v1.x unless a pinned package contract proves reusable profile semantics; read-only manifest facts may appear. |
| `FE-C04` | Goals & rubrics | Agent defaults and task verification | Feature-flagged v1 only where verified middleware supports defaults through `DW-HITL-002`; full lifecycle is `DW-FUT-101`. |
| `FE-C05` | Sandboxes | Project/environment | Live through `DW-CODE-001`; reflect source/thread ownership rather than prototype task/worktree equivalence. |
| `FE-C06` | Interpreters | Project/environment | Later/capability-gated until a public stable runtime contract and isolation policy are accepted. |
| `FE-C07` | Backends | Source/runtime diagnostics | Remove from normal editing; show read-only store/checkpointer/backend facts when verified. |
| `FE-C08` | Tools | Agent draft | Live through `DW-AGENT-005` with source schema fidelity. |
| `FE-C09` | Permissions | Agent draft/HITL | Live only where policy compiles to an enforceable verified runtime contract through `DW-AGENT-005`. |
| `FE-C10` | Multimodality | Agent/source capability | Feature-flagged v1 display and configuration only for verified modes; no generic toggle. |
| `FE-C11` | Memory | Agent/user/org scopes | v1 policy and reviewed read view through `DW-AGENT-005`/`DW-OPS-003`; publication requires review. |
| `FE-C12` | Subagents | Agent draft | v1 only where graph/runtime capability and limits are verified through `DW-AGENT-005`. |
| `FE-C13` | Streaming | Source diagnostics | Fold into read-only diagnostics; protocol choice/tuning stays inside the adapter. |
| `FE-C14` | Hooks | Project/environment | Later/v1.x after an execution, signing, and security model; audited built-ins need no generic editor. |
| `FE-C15` | Environments | Project/environment | Live through `DW-CODE-001` with versioned, secret-safe persistence. |
| `FE-C16` | Worktrees | Project/environment | Later/v1.x; multi-repo/worktree lifecycle is `DW-FUT-205`. |
| `FE-C17` | Git | Project/environment | v1 repository and branch policy through `DW-CODE-002`; no duplicate agent field. |
| `FE-C18` | Connectors | Workspace account plus agent binding | v1 through `DW-AGENT-005`; official project/SDK paths only. |
| `FE-C19` | Plugins | Workspace catalog plus project manifest | Later/v1.x; no opaque install/build control in v1. |
| `FE-C20` | Skills | Versioned agent project/source | v1 read and versioned edit where supported through `DW-AGENT-005`. |
| `FE-C21` | Protocols | Source integration architecture | Remove top-level section; MCP belongs under connectors, ACP/A2A actions are deferred. |
| `FE-C22` | Deployment | Deployment operation/source | Live classic status and actions through `DW-AGENT-003`; MDA remains beta, detected, and CLI-first. |

“Deferred” means the action is absent or appears as a non-interactive roadmap explanation only where context is useful. It never means an enabled-looking prototype control.

## Primary journeys

### Configure a supported model

1. The author opens an agent draft and sees active revision, draft state, setting scope, and target source.
2. The service returns a target-aware provider/model field schema from the pinned agent package and source manifest.
3. The author selects a verified provider/model, supported parameters, and optional ordered fallback only when the schema permits it.
4. Missing credential references or incompatible parameters appear before deployment.
5. The author saves and validates, reviews the semantic diff, and deploys explicitly through `DW-AGENT-003`.

### Inspect a runtime-owned fact

1. The user opens Diagnostics from an agent detail page.
2. Backend/checkpointer/store/stream facts show source, observation time, confidence, and owner.
3. No editor is rendered. If the source supports management elsewhere, an allowlisted official deep link or CLI explanation is provided.

### Encounter a deferred prototype setting

1. A migrated route or search result resolves the old section to its canonical owner.
2. If the feature is irrelevant or unsafe, the control is absent.
3. If users need the limitation to understand an imported project, a read-only field explains preservation, validation, and the later discovery gate.

## Model and advanced-setting contract

Each editable field has a stable field ID, canonical scope, portable schema path, value type, allowed values/constraints, source of truth, target capability predicate, credential requirements, default provenance, deploy effect, migration version, and redaction policy. Provider/model identifiers remain source-native strings validated against a pinned registry or configured allowlist; Deep Work does not promise a universal live model catalog.

Ordered fallbacks ship only when the Python package and target adapter prove their semantics. Temperature, reasoning effort, token limits, multimodal modes, and other provider-specific parameters are shown only when supported in the accepted matrix. Unknown fields imported from a future schema are preserved losslessly where safe, displayed read-only, and block deployment if the target cannot validate them.

## Complete state matrix

| State | Required behavior |
|---|---|
| Loading schema/values | Preserve section heading and draft identity; do not flash default values. |
| Empty optional group | Explain that no override is set and identify the inherited/default source. |
| Supported/editable | Show owner, validation, persistence target, dirty state, and deployment effect. |
| Supported/read-only for actor | Show value and required role; no enabled mutation affordance. |
| Runtime-owned | Show observation time/provenance and source-native fallback; no local save. |
| Unsupported by target | Hide irrelevant field or render a read-only incompatibility needed for import/review. |
| Unknown capability | Default to non-editable and require contract verification; never infer support. |
| Feature flag off | Remove the action and use stable deferred copy if context demands it. |
| Missing provider credential | Allow safe draft persistence, block target validation/deploy, and link to workspace connector setup. |
| Provider/model unavailable | Retain prior source-native identifier, mark invalid/stale, and require an explicit replacement. |
| Parameter conflict | Show field and summary errors; preserve values; Deploy remains disabled. |
| Schema/package mismatch | Offer a migration preview or compatible read-only view; never mutate automatically. |
| Unknown imported field | Preserve if safe, expose raw path/value read-only, and block unsupported target deploy. |
| Concurrent draft conflict | Use `DW-AGENT-003` version resolution; no last-write-wins. |
| Save error | Keep local values and error summary; active revision unchanged. |
| Offline | Permit clearly labelled non-secret draft buffering only; schema refresh, validation, and deploy disabled. |
| Reconnecting/stale schema | Re-fetch schema/capabilities, compare changes, and require revalidation before Deploy. |
| Permission revoked mid-edit | Preserve unsaved non-secret changes for export/copy; reject mutation and refresh authority. |
| Mobile | Group fields into short sections with persistent Save/Validate state; advanced matrices become labelled rows, not clipped tables. |

## Interfaces and state ownership

The Python agent package exports a versioned project/settings schema and deterministic validation result consumed by the FastAPI service. Proposed `/api/v1` queries return draft-scoped field definitions, resolved/inherited values, provenance, capability state, and validation. Draft mutations include expected version and change only application state; `DW-AGENT-003` owns deployment mutations. The TypeScript SDK generates types from the accepted application contract rather than duplicating provider logic.

PostgreSQL owns drafts, override values, version history, target bindings, validation reports, and audit events. The credential broker owns provider secrets. The project revision owns portable identifiers and references. The runtime owns effective backend/store/checkpointer and source-native deployment state. Browser storage may hold non-sensitive transient edits under explicit offline policy, never secrets or authoritative capability values.

## Runtime capability and fallback rules

- Classic configuration is editable only when the pinned Python project schema and classic target fixture validate the same representation.
- MDA shows detected read-only runtime facts and supports project artifact editing only where the accepted beta contract proves portability; deployment remains CLI-owned.
- Fleet has no configuration mutation in v1, even if the prototype displays a similar form.
- Profiles, interpreters, hooks, worktrees, ACP/A2A actions, arbitrary backend selection, and transport tuning remain off until their named later plan/spike is approved.
- A target that loses support leaves the draft exportable and the active revision untouched; Deep Work offers a supported classic target or source-native management fallback.

## Persistence, security, and privacy

Provider credentials are referenced by opaque server-side IDs and never included in project ZIPs, HTML, client caches, telemetry, or validation bodies. Imported provider/model strings and descriptions are untrusted and escaped. Schema/default changes are versioned and do not silently rewrite revisions. High-risk resets and provider changes require explicit confirmation and audit; deployment remains separately authorized.

Validation logs redact environment variables, credentials, file contents, and upstream error bodies. The service enforces tenant/agent/draft authorization on every field query and mutation. Retention preserves deployed revision provenance while allowing draft and transient offline data deletion.

## Responsive and accessible behavior

Every group has a semantic heading, concise scope explanation, labelled inputs, persistent help not dependent on hover, field-linked errors, and a page error summary. Inherited/read-only/unsupported states use text and icons, never color alone. Advanced disclosure is keyboard operable and preserves focus after validation. Mobile stacks fallback order and parameter groups with reorder buttons plus accessible announcements. The UI works at 320 CSS px, 200% zoom, high contrast, and reduced motion.

## Metrics and guardrails

- 100% of editable settings identify canonical owner, persistence target, validator, and deployment effect.
- Zero enabled control exists without an enforceable pinned schema and target capability.
- 100% of model/parameter incompatibilities in the accepted matrix fail before deployment.
- Zero provider secret appears in project exports, browser storage, logs, or analytics.
- Imported unknown fields are either safely preserved with a visible warning or explicitly rejected; never silently dropped.
- Guardrail: Save changes a draft only; active runtime mutation without explicit Deploy remains zero.

## Dependencies and readiness gates

Depends on `DW-AGENT-003`, `DW-CODE-001`, `DW-CODE-002`, `DW-HITL-002`, source capabilities, credential references, and the Python agent project schema. Readiness requires the full 22-section redirect/disposition map, field ownership matrix, provider-parameter fixture suite, unknown-field migration policy, and contract proof for every editable MDA/classic field.

## Rollout and rollback

1. Replace prototype settings routes with owner-aware read-only summaries and redirects.
2. Enable verified model/provider editing in fixture mode and classic non-production targets.
3. Add supported parameters and multimodal/profile gates individually from accepted fixtures.
4. Enable production draft editing only after export/import and deploy validation pass.

Rollback disables the affected field schema or mutation flag, preserves draft/revision values losslessly, and renders them read-only with export and source-native fallback. It does not coerce values to defaults or alter the active revision.

## Executable acceptance scenarios

1. **All-section disposition:** Given every `FE-C01`–`FE-C22` legacy settings route, when opened, then it resolves to the canonical owner, an explicit deferred explanation, or removal, and no inert enabled control remains.
2. **Supported model:** Given a verified classic target/provider fixture, when an author selects a model and supported parameters, saves, validates, and exports, then identifiers round-trip and the active revision remains unchanged before Deploy.
3. **Missing credential:** Given a provider without an authorized credential reference, when validation runs, then the draft remains saved, Deploy is blocked, and the accessible error links to workspace connector setup.
4. **Runtime-owned MDA:** Given an MDA-bound agent, when Backends or Streaming diagnostics open, then dated runtime facts are read-only and no inferred management route is called.
5. **Unknown imported field:** Given a safe future-schema field, when imported, then it is preserved and displayed read-only and cannot be deployed to an unverified target.
6. **Deferred controls:** Given interpreters, hooks, worktrees, plugins, or ACP/A2A actions with flags off, when the relevant page loads, then no actionable toggle is rendered.
7. **Offline conflict:** Given an offline buffered model edit and a newer server draft, when reconnecting, then the user receives an explicit conflict/revalidation flow rather than last-write-wins.
8. **Accessible mobile:** Given a 320 px viewport, keyboard/switch input, and 200% zoom, when the user reorders verified fallbacks and resolves validation errors, then order and errors are perceivable and operable.
