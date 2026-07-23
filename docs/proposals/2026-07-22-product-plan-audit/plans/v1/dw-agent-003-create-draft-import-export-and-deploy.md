---
feature_id: DW-AGENT-003
title: Agent creation, versioned configuration, import/export, and deployment
release: v1
status: proposed
decision_status: blocked-on-spikes
owners: [api, agent, web]
surfaces: [web, api]
runtime_scopes: [classic, mda, fleet]
source_refs: [SRC-LC, SRC-DW, SRC-FE]
dependencies: [DW-AGENT-001, DW-FND-003]
contract_gates: [SPIKE-CONFIG-001, SPIKE-DEPLOY-001, SPIKE-MDA-001, SPIKE-FLEET-001]
last_reviewed: 2026-07-23
---

# Agent creation, versioned configuration, import/export, and deployment

## User outcome

An authorized user can start from a trusted template or portable project, make changes in a durable draft, understand validation and semantic differences, and explicitly deploy or roll back a classic deployment without accidental live mutation. For MDA, Deep Work prepares a reviewed artifact and official CLI handoff rather than pretending to own deployment.

## Evidence and confidence

| Claim | Evidence | Classification | Planning consequence |
|---|---|---|---|
| The prototype presents create, configure, ZIP import/export, deploy, and rollback-like controls. | `SRC-FE` | Interaction evidence; many controls are simulated | Every control receives a disposition and inert behavior is removed. |
| Deep Work plans call for portable Deep Agents projects and versioned configuration. | `SRC-DW` | Product intent | Draft/save/deploy are separate application states. |
| Classic LangSmith Deployment is the supported public lifecycle baseline. | `SRC-LC` | Documented; exact control-plane operations require pinned live fixtures | Build a classic adapter only from verified routes, headers, states, and idempotency behavior. |
| MDA deployment can be reproduced safely inside Deep Work. | Prior internal assumption | Contradicted/gated | Export and hand off to the official `mda` CLI; never recreate `mda deploy`. |
| Fleet offers public project CRUD or portable ZIP parity. | Prior internal assumption | Unknown | Fleet stays read/invoke-only after its spike; no v1 create/deploy path. |

The project manifest, versioning policy, deployment state reducer, and exact classic lifecycle fixtures from `SPIKE-CONFIG-001` and `SPIKE-DEPLOY-001` must be approved before this plan can be implementation-ready. MDA and Fleet remain separately gated.

## Scope, ownership, and non-goals

The Python agent package owns the portable agent-project schema, templates, validators, migrations, and deterministic semantic representation. The FastAPI/PostgreSQL application service owns draft records, version conflicts, file quarantine, actor authorization, deployment operations, audit events, and credential references. Next.js/Tauri owns forms, file selection, diff/review, validation navigation, and progress. The TypeScript SDK exposes separate draft/deploy mutations and never embeds deployment logic in React hooks.

In scope:

- reviewed SWE, Research, Writing, and Blank templates with explicit schema/package compatibility;
- a canonical project archive containing only approved agent entry, instructions, configuration, tool and middleware declarations, connector references, schedules, skills, sandbox policy, and identity metadata;
- server-side archive validation, safe inspection, version migration preview, import, and deterministic export;
- durable versioned drafts with explicit Save, Validate, Discard, Deploy, and Roll back actions;
- semantic and file diff, validation results, revision/deployment history, build status, safe log excerpts, and source deep links;
- classic deployment through accepted public control-plane contract fixtures;
- MDA artifact export plus generated official CLI instructions that users run outside Deep Work.

Non-goals are live mutation on field change, embedded secrets, arbitrary executable bundles, dependency installation during archive inspection, Fleet CRUD/import parity, `/v1/deepagents/*`, arbitrary MDA routes, hidden deployment behind Save, or a replacement for source-native build/tracing consoles.

## Primary journeys

### Create and deploy classic

1. The user chooses a reviewed template and target classic source.
2. The service creates an application draft pinned to a base schema/template and, where applicable, an active source revision.
3. Edits save explicitly or through clearly labelled draft autosave policy; no save mutates the runtime.
4. Validate checks schema, supported capabilities, credential references, dependency policy, permissions, and target compatibility.
5. Review shows semantic changes and file-level detail, including migration normalization.
6. FastAPI performs a final authorization/freshness check, selects the verified
   classic adapter, creates one idempotent operation, and tracks source-native
   states; the client sends only the normalized Deep Work command.
7. On activation, the active revision and audit event update; a smoke invocation must pass before broad rollout criteria are satisfied.

### Import and export

1. The user selects an archive; the client checks size only and uploads to quarantine.
2. The service inspects without executing, rejects unsafe structure, and returns a manifest, compatibility, normalizations, warnings, and errors.
3. The user confirms a new draft after reviewing the inspection report.
4. Export produces the approved manifest plus supported files and a checksum; secret references remain references.

### MDA handoff and rollback

1. For an eligible MDA-bound project, the user validates and exports the reviewed artifact.
2. Deep Work displays copyable official CLI guidance derived from accepted beta documentation, but does not execute or proxy the deploy command.
3. For classic rollback, an authorized user chooses a known-good revision, reviews impact, and initiates a new audited activation/redeployment according to the verified lifecycle rather than rewriting history.

## Complete state matrix

| State | Required behavior |
|---|---|
| Loading project/draft | Preserve identity and navigation; load sections independently. |
| No project | Offer trusted templates and import, with target availability explained. |
| Clean draft | Show active/base revision and no pending changes. |
| Dirty local edit | Persistent unsaved indicator and navigation protection; never imply server persistence. |
| Saved draft | Show draft version and save time; active runtime remains unchanged. |
| Validation running | Lock only conflicting mutations, allow navigation, and announce progress. |
| Validation warning | Permit review; deployment policy decides whether acknowledgement is required. |
| Validation error | Disable Deploy, summarize errors, and focus/link the owning field or file. |
| Missing credential/permission | Preserve draft; block validation/deploy as appropriate and link to authorized setup. |
| Stale base revision | Fetch current active revision and require rebase/review; never silently overwrite. |
| Concurrent draft conflict | Compare local/server/base and require explicit resolution with a new version. |
| Import inspecting | Show quarantine/inspection progress and allow safe cancel. |
| Import unsafe/incompatible | Delete quarantined payload per policy, return redacted reasons, and create no draft. |
| Import normalization required | Preview every changed path/field and require confirmation. |
| Deploy queued | Show idempotency-backed operation and target; active revision unchanged. |
| Building/deploying | Poll or consume only verified status events; state whether upstream cancellation exists. |
| Upstream reconnect | Resume status from the durable application operation; never submit a second deployment. |
| Build failed | Keep active revision, safe logs, unchanged draft, and retry-from-review action. |
| Activation/smoke failed | Mark degraded, preserve or restore known-good active revision per verified contract, and surface rollback. |
| Activated | Update active revision, provenance, and audit record only after source confirmation. |
| Rollback running/completed | Model as a new operation linked to both revisions; retain full history. |
| MDA target | Export/CLI handoff only; no in-app deploy progress fiction. |
| Fleet target | Read-only ownership and no create/import/deploy controls. |
| Offline editing | Allow explicitly scoped non-secret local draft buffer; Save/Validate/Deploy disabled. |
| Offline during deploy status | Show last durable state as stale and reconnect to the same operation. |
| Unauthorized | Preserve viewable history where allowed; remove mutation controls and explain required role. |
| Mobile | Support review and safe Save/Discard; large archive editing/deployment may hand off to desktop with a durable link, never an inert control. |

## Interfaces and state ownership

The proposed internal `/api/v1` contract covers templates, draft creation/query/save, archive inspection/import/export, validation, semantic diff, deployment intent/status, and rollback intent. Mutations carry an idempotency key and expected draft/base version. Exact paths and payload shapes remain API-review outputs.

Required application entities include `AgentProject`, immutable `ProjectRevision`, mutable `Draft` with optimistic version, `ValidationReport`, quarantined `ImportInspection`, and `DeploymentOperation` with source-native reference and normalized state. Deploy is a service command separate from draft persistence. The React client uses the TypeScript SDK; it does not call classic/MDA control planes or the Python agent package directly.

PostgreSQL owns metadata, versions, hashes, status transitions, actor intent, and audit events. An approved object store owns quarantined archives and immutable export/revision blobs. The source runtime owns active deployment state and build logs. Reconciliation never overwrites source truth; it records observation and mismatch.

## Runtime capability and fallback rules

- Classic deploy and rollback ship only after exact auth headers, lifecycle calls, status states, failure semantics, and idempotency are proven against a pinned package/live contract.
- MDA stays capability-detected, private-beta, and CLI-first. The application exports an artifact and guidance; it does not call private or inferred routes.
- Fleet remains read/invoke-only after `SPIKE-FLEET-001`; no archive import, create, update, deploy, or delete is presented.
- Unsupported project fields remain editable only if portable export can preserve them without falsely validating them for the target; otherwise they are read-only with migration guidance.
- If deployment capability regresses, users retain drafts and exports and receive a source-native fallback.

## Persistence, security, and privacy

Archive inspection rejects absolute paths, traversal, symlinks/hardlinks, device files, nested archive bombs, excessive compression, count/size/depth limits, unexpected executables, Unicode path collisions, and undeclared file types. Inspection never imports modules, installs dependencies, executes hooks, resolves remote includes, or renders raw HTML. Rejected objects are deleted according to quarantine policy.

Secrets are forbidden in project files and exports; scanners block likely credentials and direct users to server-side connector references. Mutations are tenant-scoped, actor-authorized, CSRF-protected as applicable, idempotent, audited, and reauthenticated for high-risk production deployment. Logs and diffs are untrusted, size-limited, redacted, and safely rendered. Retention distinguishes drafts, immutable revisions, quarantined uploads, deployment logs, and audit records.

## Responsive and accessible behavior

The editor has labelled scope and dirty-state indicators, an error summary, and deterministic focus movement to invalid fields. Semantic diffs use text markers in addition to color and support keyboard line/file navigation. Progress uses polite announcements; failure is asserted only once. At narrow widths the summary, validation, and action bar stack without obscuring Deploy consequences. Large file diffs offer an accessible file list and plain-text download. Reduced motion is respected.

## Metrics and guardrails

- 100% of production runtime changes require a valid saved draft, explicit Deploy intent, current authorization, and an audit event.
- Zero live mutations arise from blur/change events or draft Save.
- Failed build/deploy never silently replaces the last confirmed active revision.
- Supported archive round trips preserve bytes or enumerate every deterministic normalization.
- Zero extracted path escapes, executed import code, exported credential, or unredacted secret in logs across security fixtures.
- Guardrail: classic lifecycle capability remains off until its pinned contract suite passes; MDA in-app deployment count remains zero.

## Dependencies and readiness gates

Depends on `DW-AGENT-001`, `DW-FND-003`, workspace authorization, object storage/quarantine, credential references, configuration plans `DW-AGENT-004` and `DW-AGENT-005`, and release security testing. Readiness gates are the project schema/version policy, archive threat model, classic lifecycle live-contract fixture, deployment status reducer, rollback semantics, and approved template licenses/content.

## Rollout and rollback

1. Validate/export reviewed templates in fixture mode with no live deployment.
2. Enable drafts, conflict handling, and import quarantine for internal workspaces.
3. Enable classic deployment for a non-production pinned fixture, then selected sources after smoke/rollback evidence.
4. Add production classic rollout with per-source kill switch and operation monitoring.
5. Enable MDA export/CLI handoff only for detected beta workspaces; never couple it to classic availability.

Rollback disables new deploy mutations, lets in-flight operations reconcile to a durable terminal state, preserves drafts/revisions, and keeps export/source-deep-link fallbacks. Disabling import removes new upload capability and expires quarantined objects without deleting accepted revisions.

## Executable acceptance scenarios

1. **Template to classic:** Given each trusted template and a verified classic fixture, when an authorized user edits, saves, validates, reviews, and deploys, then one deployment operation reaches confirmed active state and a smoke task uses that revision.
2. **No implicit mutation:** Given an active revision, when a user changes and saves a draft, then the source active revision and runtime behavior remain unchanged until explicit Deploy.
3. **Concurrent conflict:** Given two sessions on one draft version, when both save, then one succeeds and the other receives a three-way conflict requiring explicit resolution.
4. **Unsafe archives:** Given traversal, symlink, nested bomb, Unicode-collision, secret-bearing, and executable fixture archives, when inspected, then each is rejected or quarantined per policy, nothing executes, and no project is created.
5. **Deterministic round trip:** Given a supported project, when exported, reimported, and exported again, then checksums match except for normalizations listed in both inspection reports.
6. **Failure isolation:** Given an upstream build failure, when status reaches failed, then the prior active revision remains confirmed, the draft remains available, and logs are redacted.
7. **Reconnect/idempotency:** Given connectivity loss after deploy submission, when the client reconnects and retries with the same key, then it resumes one durable operation and does not create a second deployment.
8. **MDA boundary:** Given an eligible MDA project, when Deploy is selected, then Deep Work offers reviewed export and official CLI guidance and makes no MDA deploy or inferred `/v1/deepagents/*` request.
9. **Fleet boundary:** Given a Fleet-bound agent, when Configuration opens, then creation/import/deployment controls are absent and no Fleet mutation request occurs.
10. **Responsive review:** Given keyboard-only use, 200% zoom, and a narrow viewport, when a user resolves validation errors and reviews a diff, then all changes and consequences are perceivable before any enabled deployment action.
