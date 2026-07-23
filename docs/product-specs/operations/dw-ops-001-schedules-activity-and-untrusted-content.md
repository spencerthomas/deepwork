---
feature_id: DW-OPS-001
title: Schedules, activity, and untrusted content
release: v1
status: canonical-spec
decision_status: blocked-on-spikes
owners: [api, web, agent]
surfaces: [web, pwa, desktop]
runtime_scopes: [classic, mda, fleet]
source_refs: [SRC-LC, SRC-DW, SRC-FE]
dependencies: [DW-AGENT-001, DW-FND-003]
contract_gates: [SPIKE-SCHEDULE-001, SPIKE-MDA-001, SPIKE-FLEET-001]
last_reviewed: 2026-07-23
---

# Schedules, activity, and untrusted content

## User outcome

A user can understand when recurring work will run, which system owns it, what will happen on overlap or failure, and where each firing produced a task. They can review a trustworthy chronological activity record across sources without Deep Work silently treating external content as instructions or claiming a universal schedule API.

## Evidence and confidence

| Claim | Evidence | Classification | Planning consequence |
|---|---|---|---|
| The prototype has primary Schedules and Activity destinations with simulated rows and controls. | `SRC-FE`, `FE-O01`–`FE-O03` | Direct interaction/code evidence, not runtime proof | Preserve the experiences, replace fixtures with ownership-aware application records. |
| The product vision includes recurring work, activity, and slim observability. | `SRC-DW` | Product intent | Schedules and Activity remain v1 primary destinations; charts fold into Activity. |
| Classic Agent Server/Deployment documentation describes scheduling capabilities. | `SRC-LC` | Documented at feature level; exact CRUD, payload, auth, and state semantics need pinned contract fixtures | Classic mutations stay behind verified capability checks. |
| MDA schedules can be managed by Deep Work through public deployment APIs. | Prior internal assumption | Contradicted/gated | Preserve a verified project declaration and hand off deployment to official `mda` CLI. |
| Fleet has public schedule CRUD and all sources support one global activity query. | Prior internal assumption | Unknown/unsupported | Fleet schedule management is absent; Activity aggregates per source and application events. |

The classic scheduling contract, MDA project representation, trigger/delivery model, and overlap semantics require the accepted live fixtures in `SPIKE-SCHEDULE-001`, plus the separate MDA/Fleet gates. This proposed plan is not implementation-ready until those contracts and failure reducers are approved.

## Scope, ownership, and non-goals

The FastAPI/PostgreSQL application service owns normalized schedule registrations, source ownership, application-triggered schedules if approved, idempotent firing/task linkage, activity projection, audit events, and safe content envelopes. The Python agent package validates portable MDA/classic project schedule declarations where verified. The TypeScript SDK supplies query/mutation clients to Next.js/PWA and Tauri. Runtime adapters own source-native operations.

In scope:

- Schedules index/detail with source, agent, ownership, timezone, human-readable cadence, next-run preview, enabled state, overlap policy, input mode, destination, last result, and run history;
- classic create/update/pause/resume/delete only when the pinned adapter proves each operation;
- MDA project declaration editing only where the beta project schema proves it, followed by export/official CLI handoff rather than in-app deployment;
- Fleet read-only evidence only after `SPIKE-FLEET-001` proves it, with no schedule mutation;
- application audit/activity events and normalized per-source task/run/schedule events with explicit freshness/provenance;
- safe handling and display of schedule, webhook, connector, source, and runtime content as untrusted data.

Non-goals are an invented global schedule service across runtimes, public Fleet CRUD, private `/v1/deepagents/*`, arbitrary MDA connector or deploy calls, a replacement for LangSmith trace analytics, raw log search, implicit agent invocation from unverified webhook content, or background work without an application idempotency/audit record.

## Schedule ownership model

Every schedule identifies one `ownershipMode`:

- `classic_source`: source runtime is authoritative; Deep Work mutates only through verified classic operations and stores normalized evidence;
- `mda_project`: portable project declaration is authoritative; Deep Work may edit/validate/export, while official CLI deployment activates changes;
- `external_read_only`: Fleet or another verified source exposes evidence only; source-native tool owns changes;
- `application`: the application service owns timing and dispatch only if an explicit v1 architecture decision approves this mode and all durability/security acceptance scenarios pass.

Every normalized record includes timezone ID, local cadence and canonical expression, next-run calculations with tzdata version, prompt XOR typed structured input, immutable agent source/assistant binding, thread mode, destination capability/reference, overlap policy (`skip` or `queue` only when enforceable), enabled state, source-native ID, version/freshness, and provenance. “Replace” or concurrent strategies are never offered without a verified contract.

## Primary journeys

### Create and operate a classic schedule

1. The user opens Schedules and filters to an authorized classic agent.
2. Deep Work checks the current capability/permission and presents only verified fields.
3. The user supplies cadence, IANA timezone, input, thread mode, overlap policy, and optional supported delivery destination.
4. A preview shows upcoming wall-clock and UTC runs, including DST transitions and unavailable/duplicate local times.
5. Save creates one idempotent source operation and an application registration; it never falls back to another ownership mode silently.
6. The user pauses/resumes/deletes only when the adapter supports that action, with source confirmation and audit.

### Edit an MDA schedule declaration

1. The user edits a verified schedule block in the versioned agent project.
2. The Python validator checks schema/capability and the semantic diff shows timing/input changes.
3. Deep Work saves and validates the draft, then offers artifact export and official CLI guidance.
4. The schedule remains unchanged in the runtime until source evidence later confirms an external CLI deployment.

### Review activity and recover a failed firing

1. Activity loads cached application audit events and refreshes each source independently.
2. The user filters by time, actor, source, agent, type, and outcome, then opens the linked application task and authorized source trace.
3. A failed or duplicate firing shows ownership, idempotency key, input provenance, and safe retry options only when policy allows.
4. Retry creates a new attributable operation linked to the original; it never rewrites history.

## Complete state matrix

| State | Schedules behavior | Activity behavior |
|---|---|---|
| Initial loading | Stable row/card skeleton and filter controls. | Render cached events if present and source-group refresh state. |
| Empty, no supported agents | Explain source/agent prerequisites and demo entry. | Explain which actions will appear and preserve filters. |
| Empty after filters | Show active filters and reset; do not imply no schedules exist. | Same, with date-range context. |
| Supported editable schedule | Show authority, version, next runs, and only verified mutations. | Link source operations and generated tasks. |
| Read-only external schedule | Show source owner and allowlisted management fallback. | Keep events browseable; no local mutation. |
| MDA draft differs from source | Label draft versus last observed deployed declaration; CLI handoff only. | Show draft/deploy evidence as separate events. |
| Loading/saving mutation | Lock duplicate action, show idempotent progress, and retain prior source truth. | Add pending application event only if clearly labelled. |
| Invalid cron/timezone/input | Field and summary errors; Save/Deploy disabled. | Not applicable. |
| DST gap/duplicate time | Preview exact policy and next UTC instants; require acknowledgement when ambiguous. | Record actual source instant and displayed timezone. |
| Overlap skipped/queued | Show enforceable policy and source result; no inferred completion. | Record firing, overlap decision, and linked task if one exists. |
| Source permission denied | Preserve readable record when allowed and explain required role/scope. | Omit protected content, not the entire healthy-source feed. |
| Authentication expired | Mark affected schedules degraded and disable mutations. | Show prior events as stale; provide administrator recovery. |
| Source timeout/partial failure | Keep cached rows and other sources live with a scoped warning. | Merge successful source/application pages and one source error. |
| Offline | Show cached schedules, next-run calculation marked local/stale, and no mutations. | Show cached events with snapshot time; external links requiring auth disabled. |
| Reconnecting | Reconcile the same pending operation; never duplicate save/fire. | Resume each source cursor independently and deduplicate event IDs. |
| Stale schedule version | Re-fetch, compare, and require review before mutation. | Preserve both observation events and provenance. |
| Agent/source removed | Disable future application-owned firing or mark external orphan; preserve history. | Retain tombstone identity and linked tasks/audit. |
| Fired payload malicious/untrusted | Store bounded typed envelope and render inert quoted data. | Escape content, block raw HTML/active URLs, and show provenance. |
| Duplicate/replayed firing | Return the existing application result for the idempotency key. | One canonical firing plus replay/audit evidence, not a second task. |
| Mobile | Cards retain timezone, ownership, next run, status, and primary safe action. | Chronological list retains actor/source/outcome; filters move to an accessible sheet. |

## Interfaces and state ownership

The proposed internal `/api/v1` contract includes schedule queries by application ID/source, validated preview, source-capability-specific mutation commands, firing/run linkage, and activity queries. Exact paths remain API-review outputs. Mutations carry expected normalized/source version and idempotency key. Activity pagination uses an application cursor over persisted events plus per-source cursors; it never assumes a global upstream search or cursor.

Normalized `ScheduleRecord` includes owner mode, source/assistant identity, source-native ID/version, schedule expression/timezone/tzdata version, typed input reference, thread/overlap/delivery policy, capability decision, next-run evidence, lifecycle state, and freshness. `ActivityEvent` includes application event ID, event type/version, actor/system identity, tenant/source/agent/task/run/schedule references, timestamp, outcome, provenance, safe summary, sensitivity classification, and optional allowlisted trace link.

PostgreSQL owns application registrations, idempotency, application-owned trigger state if approved, activity/audit projection, source cursors, and task links. Source runtimes own source-native schedule truth and runs. The agent project owns MDA declarations until official CLI deployment. Raw payload bodies use bounded encrypted storage only where retention requires it; Activity uses redacted summaries.

## Runtime capability and fallback rules

- Classic mutations ship action by action only after exact pinned route/auth/payload/version/error/idempotency fixtures pass.
- MDA is beta, detected, and CLI-first. Deep Work edits only a verified declaration and never activates it through inferred APIs or recreates `mda deploy`.
- Fleet has no mutation; even read-only records require the accepted read/invoke spike and explicit schedule evidence.
- Unsupported delivery, overlap, thread, or payload modes are removed from the form rather than approximated.
- A source that cannot enumerate schedules may still show application registrations and source-native deep links without claiming completeness.
- Source failures are independent; Activity retains application audit evidence and qualified coverage.

## Persistence, security, and untrusted-content boundary

All schedule and activity access is tenant/actor authorized. Mutations are idempotent, version-checked, CSRF-protected as applicable, reauthenticated for destructive production changes, and audited. Schedule inputs reference authorized credentials/artifacts rather than embedding secrets. Deleted schedules retain minimal tombstone/provenance according to audit policy.

Webhook and external trigger endpoints exist only for approved integrations. They require verified authentication/signature or broker identity, replay windows, bounded bodies, content-type/schema checks, rate limits, tenant binding, and idempotency before task creation. Payload text, HTML, Markdown, links, headers, tool output, logs, and source metadata are untrusted. They are never evaluated as UI instructions, interpolated into trusted templates without explicit delimiting, or rendered as raw HTML. External links are normalized, allowlisted where necessary, and labelled.

## Responsive and accessible behavior

Cron/cadence inputs have plain-language previews, keyboard-operable controls, error summaries, and explicit timezone/DST descriptions. Status and ownership never rely on color. Tables become labelled cards on narrow screens without hiding next run or authority. Activity filters are reachable without horizontal overflow and announce result count changes. Infinite scroll is not the only navigation mechanism; pagination/load-more has an accessible button. Reduced motion applies to live-event insertion.

## Metrics and guardrails

- Zero duplicate task is created for one normalized schedule firing/idempotency key.
- 100% of application-observed firings link source, schedule, task, run, and trace when each exists; absent links are explicitly classified.
- Next-run preview matches accepted tzdata/DST fixtures and observed classic execution within the agreed tolerance.
- Zero untrusted payload fixture executes script, becomes trusted markup, or triggers an unapproved network request.
- Healthy source schedules/activity remain usable when another source fails.
- Guardrail: no schedule mutation is enabled without an accepted operation-specific source contract.

## Dependencies and readiness gates

Depends on `DW-AGENT-001`, `DW-FND-003`, task identity/status/idempotency, source adapter fixtures, `DW-AGENT-003` for MDA draft/export, and safe trace-link policy. Readiness requires an ownership decision for application schedules, accepted classic schedule live fixtures, MDA declaration fixture, timezone/DST/overlap specification, event taxonomy, activity cursor design, and untrusted-content threat tests.

## Rollout and rollback

1. Launch Activity with application audit events and fixture schedules; no source mutations.
2. Add classic read/preview against pinned non-production fixtures.
3. Enable classic create and each lifecycle mutation independently behind flags.
4. Add MDA draft/export presentation after schema proof and Fleet read-only evidence only after its spike.
5. Consider application-owned scheduling only through a separate architecture/security review.

Rollback disables the affected source mutation or trigger, preserves registrations/history, reconciles in-flight operations to a durable state, and presents source-native management links. Disabling Activity source refresh retains application audit events and clearly qualifies coverage.

## Executable acceptance scenarios

1. **Classic lifecycle:** Given a pinned classic schedule fixture that proves create/pause/resume/delete, when an authorized user performs each action, then one versioned source operation occurs and Activity records its confirmed result.
2. **MDA boundary:** Given a verified MDA project schedule declaration, when edited and approved, then Deep Work saves/exports it and offers official CLI guidance without calling MDA deployment or arbitrary schedule routes.
3. **Fleet boundary:** Given `SPIKE-FLEET-001` is unaccepted, when Schedules loads, then no Fleet CRUD control or request exists.
4. **DST correctness:** Given spring-forward and fall-back fixtures in two IANA zones, when previewed, then wall-clock ambiguity/gaps and exact UTC instants match the accepted policy and runtime evidence.
5. **Replay protection:** Given the same authenticated firing arrives twice inside the replay window, when processed, then one task exists, the second response resolves to it, and replay evidence is audited.
6. **Malicious content:** Given HTML, scripts, prompt injection, unsafe URLs, and oversized fields in a trigger/source event, when stored and rendered, then content is inert, bounded, redacted, and no unapproved execution/request occurs.
7. **Partial source failure:** Given two sources and one timeout during pagination, when Activity refreshes, then successful events remain ordered/usable, the failed source is named, and its cursor can retry independently.
8. **Offline/reconnect:** Given a schedule mutation response is lost, when the client reconnects with the same idempotency key, then it reconciles one operation and never creates a second schedule.
9. **Responsive accessibility:** Given keyboard-only use at 320 px and 200% zoom, when a user previews DST, corrects an error, and filters Activity, then all ownership, time, outcome, and actions remain perceivable and operable.
