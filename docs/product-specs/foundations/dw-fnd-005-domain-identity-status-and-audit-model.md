---
feature_id: DW-FND-005
title: Domain identity, status, and audit model
release: v1
status: canonical-spec
decision_status: blocked-on-spikes
implementation_readiness: not-ready
owners: [api, domain, product]
surfaces: [api, web, pwa, desktop]
runtime_scopes: [any]
source_refs: [SRC-LC, SRC-DW, SRC-LCJS]
evidence_pins:
  langchain_docs: 7b9215d
  canonical_plan: 06f0515
  langchainjs: ee76ea0
dependencies: [DW-FND-003]
contract_gates: [SPIKE-STREAM-001, SPIKE-MDA-001, SPIKE-FLEET-001]
last_reviewed: 2026-07-23
---

# Domain identity, status, and audit model

## User outcome

A user sees one stable task identity and trustworthy status across inbox, detail, approval, notification, phone, tray, and activity views. Retrying, cancelling, renaming, archiving, branching, approving, and reconnecting never conflate sources or erase history; every security- or outcome-relevant action remains attributable without storing secrets or raw untrusted content.

This plan is proposed and blocked on external contract verification. It cannot become implementation-ready until `SPIKE-STREAM-001` proves the source events and commands used by the reducer, especially run terminal states, cancellation confirmation, queues, interrupts, checkpoints, and reconnect reconciliation for each enabled adapter.

## Evidence and confidence

| Evidence | Classification | Confidence | Planning consequence |
|---|---|---:|---|
| LangSmith distinguishes assistants/agents, deployments, threads, runs, checkpoints/state, interrupts, and traces. | Documented at `7b9215d` | High for classic deployment | Preserve upstream identities and lifecycle boundaries rather than collapsing them into “task.” |
| Deep Work needs application-owned rename, archive, unread, notification, source, and display metadata. | Product requirement | High | Create application identities that reference, but do not replace, authoritative source identities. |
| No public global thread-search contract exists across sources. | Audit finding | High | Every external identity includes `sourceId`; aggregation remains per source. |
| HITL is an ordered batch and pending interrupt can coexist with active run metadata. | Documented | High | `needs-review` wins the presentation reducer while underlying run/interrupt state remains visible. |
| Cancel, retry, queue, reconnect, checkpoint, and terminal event shapes differ by source/transport. | Documented in parts; live package behavior unverified | Medium | Gate transition evidence on `SPIKE-STREAM-001`; unknown state remains unknown. |
| MDA/Fleet support and identity relationships are not stable public CRUD contracts. | Gated/unknown | High | Do not infer agent/deployment/source ownership; use capability evidence and source-qualified bindings. |

## Scope, ownership, and non-goals

### In scope

- Stable application IDs and immutable source-qualified external keys for actor, workspace, source, agent binding, task/thread, run, checkpoint/branch, interrupt batch, artifact, attachment, notification, and audit event.
- A normalized task status reducer plus orthogonal substates for cancelling, reconnecting, stale, source health, unread, archived, and queued count.
- Explicit allowed transitions and race resolution for dispatch, queue, steer, cancel, retry, interrupt/decision, reconnect, failure, completion, rename, and archive.
- Version/etag and idempotency semantics for application-owned mutations and externally effective actions.
- Append-only, redacted audit events with actor, tenant/workspace, target, correlation, source outcome, and safe change summary.
- Consistent status labels, iconography inputs, notification/tray badge semantics, and historical run/verdict linkage.
- Provenance records for artifacts/files and parent/child relationships for checkpoints, task branches, subagents, and retries.

### Ownership

- FastAPI owns UUIDv7 application IDs, source binding validation, optimistic versions, audit persistence, task metadata, and mutation transition checks.
- Postgres owns application records, durable application statuses/substates, idempotency, source references, and redacted audit events.
- LangSmith/Agent Server remains authoritative for thread, run, checkpoint, interrupt, trace, sandbox, and deployment records.
- `packages/domain` owns client-safe normalized key/status/capability/error/event types and a pure deterministic reducer shared by SDK, UI, web/PWA, Tauri, fixtures, and future native clients.
- `packages/sdk` maps reviewed wire DTOs/events into `packages/domain`; it does not own or duplicate the reducer vocabulary.
- Product owns user-facing status vocabulary and which state has attention priority.
- Each feature plan owns its mutations; this plan defines the shared identity/transition contract, not their upstream calls.

### Non-goals

- Replacing upstream IDs, assigning one global thread ID without a source, or treating an assistant ID as an agent/deployment/source identity.
- Inferring a terminal result from connection loss, source outage, missing event, or elapsed time.
- Deleting tasks in v1, flattening retry history, rewriting audit history, or storing raw credentials/tool output in audit events.
- A generic event-sourcing platform or unbounded replication of upstream runtime records.
- Claiming MDA/Fleet identity/CRUD semantics before their named spikes.

## Canonical identity and status model

### Stable identities

- All Deep Work application IDs are UUIDv7 and never reuse an upstream/provider ID as the primary key.
- `SourceThreadKey = { sourceId, threadId }` is the unique thread reference.
- `SourceRunKey = { sourceId, threadId, runId }` is the unique run reference.
- `SourceCheckpointKey = { sourceId, threadId, checkpointId }` and `InterruptKey = { sourceId, threadId, runId, interruptId, version }` prevent stale cross-run decisions.
- One task references one primary source/thread. A checkpoint branch remains related to that task unless the source creates a new thread, in which case Deep Work records a new application task plus explicit parent relationship.
- One application agent may have multiple versioned runtime bindings, each with source, assistant/deployment identity, capability snapshot, and validity interval.
- Artifact identity records source, task, producing run/subagent, content type, size, checksum when available, provenance, access method, and authorization scope.
- Attachments are user inputs; artifacts are outputs. A file may have both lifecycle records only through an explicit provenance relationship.

### Presentation status

Highest-attention precedence is:

1. `cancelled` when authoritative cancellation is confirmed;
2. `needs-review` when a current pending interrupt requires the actor;
3. `running` when an active run exists;
4. `queued` when a verified queued submission exists without an active run;
5. `failed` for authoritative terminal failure;
6. `done` for authoritative terminal success;
7. `status-unavailable` when no supported evidence can determine the state.

`cancelling`, `reconnecting`, `stale`, `source-unavailable`, `archived`, `unread`, and queue count are orthogonal substates, not replacements for the last durable outcome. A historical completed task does not become failed when its source is offline.

### Mutation semantics

- Rename changes application display metadata and increments its version; it does not rename the upstream thread unless a separate verified contract is later approved.
- Archive hides from the default inbox but preserves task/run/audit history and can be reversed.
- Retry creates a new run attempt linked to the failed/cancelled attempt on the same thread only when the source contract allows it. It never overwrites the old run.
- Cancel sends a verified source command, enters `cancelling`, and becomes `cancelled` only after authoritative confirmation. Disconnect/unsubscribe is not cancellation.
- Branch records checkpoint parent and resulting thread/checkpoint identity; it never mutates the parent history.
- Delete and duplicate are deferred; no unlabeled “Mark resolved” action substitutes for an upstream transition.

## Primary journeys

### Dispatch through terminal outcome

1. FastAPI creates an application task ID and binds it to one authorized source/thread identity idempotently.
2. A verified run-start response creates a run-attempt record and the reducer enters queued or running according to authoritative evidence.
3. Stream/query events update underlying facts; pure reduction derives the same status on every client.
4. An interrupt creates a versioned batch and moves attention to needs-review without erasing active-run facts.
5. Accepted decisions are linked to actor, batch, ordered decision digest, and provider outcome.
6. Terminal source state produces done, failed, or cancelled and keeps all attempts/trace links.

### Retry and cancellation race

1. A user cancels an active run with task version and idempotency key.
2. The application records cancelling and sends one verified source command.
3. A reconnect/full hydration reconciles late terminal events and cancel outcome according to authoritative source order/evidence.
4. Retry remains unavailable until the current run reaches an eligible terminal state.
5. Retrying creates a new attempt and preserves the cancelled/failed attempt.

### Cross-source aggregation and notification

1. Two sources return identical thread/run strings.
2. Source-qualified keys produce distinct tasks, links, status, notification, and audit targets.
3. A needs-review transition creates at most one actor notification for the interrupt version.
4. Resolving it on web causes PWA/Tauri/tray to converge by application task/interrupt identity.

## Complete state matrix

| Evidence situation | Derived state and substate | Required transition/recovery |
|---|---|---|
| Projection loading or reconciling | Last authorized projection plus `loading` or `reconnecting`; no guessed terminal state | Resolve normalized facts, time out safely, or expose source-scoped error. |
| Task identity being created | `creating`; no terminal claim | Idempotently bind source/thread or fail without orphan display task. |
| No task exists / empty inbox | No fabricated task status | Render owning empty state. |
| Verified queued submission, no active run | `queued`, queue position/count only if supported | Start when source confirms; unknown position remains hidden. |
| Active run | `running` | Continue stream/query reconciliation. |
| Active run plus queued submissions | `running` + verified queue count | Preserve each queued submission identity. |
| Pending current interrupt plus active run metadata | `needs-review` + underlying run fact | Submit ordered decision or await another actor; no “resolved” shortcut. |
| Interrupt submission in flight | `needs-review` + `decision-submitting` | Idempotent accept, stale, or failure result. |
| Stale interrupt | Last durable task state + stale approval record | Refetch current interrupt; apply no stale decision. |
| Cancel requested, not confirmed | Prior task status + `cancelling` | Await/reconcile source; prevent duplicate cancel side effect. |
| Cancellation confirmed | `cancelled` | Offer eligible retry/history; do not infer success. |
| Cancel races with success | Use authoritative source outcome and event/version evidence from accepted adapter | Record both request and outcome in audit; never pick by client arrival alone. |
| Terminal success | `done` | Preserve trace, artifacts, verification, attempts. |
| Terminal failure | `failed` with safe reason category | Retry if source supports; retain failed attempt. |
| Failed attempt followed by successful retry | Task `done`; attempt history failed then succeeded | UI exposes both and links new attempt to prior. |
| Source unavailable after durable completion | `done` + `source-unavailable` | Retry source health; do not change outcome. |
| Source unavailable during active work | Last durable status + `source-unavailable`/`reconnecting` | Reauthorize and hydrate; do not infer failure/cancel. |
| Permission revoked | Last safe status + `permission-denied` | Hide protected content, preserve safe metadata, change source/access. |
| Offline client | Last safe status + `offline` and timestamp | Read-only; reconnect before mutation. |
| Reconnected with cursor gap | `reconnecting` then authoritative reduction after full hydration | Dedupe and converge through `DW-FND-004`. |
| Unknown upstream state | `status-unavailable` | Show source diagnostics; never coerce to failed/done. |
| Rename version conflict | Existing name and `stale-version` error | Refetch/review; no silent overwrite. |
| Archived | Durable task status + `archived` | Exclude from default inbox; restore without runtime mutation. |
| Duplicate event/notification | Existing state unchanged | Dedupe by source-qualified durable identity/idempotency. |
| Mobile/background notification stale | Do not trust payload status | Open app, authorize, and load current durable state. |

## Proposed interfaces

```ts
interface SourceThreadKey { sourceId: string; threadId: string }
interface SourceRunKey extends SourceThreadKey { runId: string }
interface InterruptKey extends SourceRunKey { interruptId: string; version: string }

type TaskStatus =
  | "queued"
  | "running"
  | "needs-review"
  | "done"
  | "failed"
  | "cancelled"
  | "status-unavailable";

interface TaskProjection {
  taskId: string;
  sourceThread: SourceThreadKey;
  status: TaskStatus;
  cancelling: boolean;
  reconnecting: boolean;
  stale: boolean;
  sourceHealth: "healthy" | "degraded" | "unavailable" | "permission-denied";
  queuedCount?: number;
  archived: boolean;
  unread: boolean;
  version: number;
  observedAt: string;
}

interface AuditEvent {
  id: string;
  occurredAt: string;
  actorId: string;
  tenantId: string;
  workspaceId?: string;
  action: string;
  target: { type: string; applicationId: string; sourceId?: string };
  correlationId: string;
  sourceOutcome?: "accepted" | "rejected" | "failed" | "unknown";
  redactedSummary: Record<string, string | number | boolean | null>;
}
```

Proposed FastAPI `/api/v1` behavior:

- Every resource response carries application ID, source-qualified references where applicable, observed time, and optimistic version.
- Mutations that can duplicate external effects require `Idempotency-Key`; application metadata updates also require expected version.
- Status endpoints return underlying normalized facts and derived projection version so clients can test deterministic parity.
- Audit query is actor/resource-authorized and cursor-paginated; it never exposes raw provider request/response bodies.
- The pure `packages/domain` reducer consumes normalized facts supplied through `DW-FND-004`; React components cannot set terminal status directly.

## Runtime capability and fallback

- Classic LangSmith Deployment is the baseline only for transition facts proven through `SPIKE-STREAM-001` and captured query/stream contracts.
- Protocol-v2, legacy, and run-join event identities remain adapter-specific before normalization; the model preserves enough source evidence to reconcile rather than assuming one global sequence.
- MDA/Fleet bindings remain gated by `SPIKE-MDA-001`/`SPIKE-FLEET-001`. Unknown agent/deployment identity relationships are represented as unknown, not synthesized.
- If a runtime does not expose queue position, retry, cancellation confirmation, checkpoint branching, or trace link, the corresponding capability is unavailable and the task retains only supported states/actions.
- If streaming is unavailable but authoritative query is verified, status can refresh by bounded polling with visible freshness. If neither is verified, use `status-unavailable`.
- Fixture mode produces deterministic source-qualified identities and every reducer combination, but cannot cause its runtime label to advertise a live capability.

## Persistence and security

- Postgres stores application IDs, source-qualified references, bounded normalized facts/projections, optimistic versions, idempotency records, metadata, and audit events.
- Upstream runtime records remain authoritative and are refreshed before destructive/approval mutations; local projections include source observation time and adapter contract version.
- Audit payloads exclude credentials, OAuth codes, raw prompts, raw tool arguments/results, repository contents, artifact bodies, untrusted markdown, and provider error bodies.
- Sensitive changes record safe before/after digests or field names, not secret values.
- Tenant/workspace/source authorization is checked both when an audit event is written and when it is read. Notification/deep-link identity is opaque and reauthorized on open.
- Audit events are append-only to application roles; corrections create linked events. Retention, export, deletion exception, and legal requirements need explicit policy review.
- UUIDv7 generation, unique source keys, foreign keys, version constraints, and idempotency uniqueness are database-enforced where possible.

## Responsive and accessible behavior

- Every status uses a consistent text label, icon, and optional color; color never carries outcome alone.
- Status changes that require action—needs-review, cancellation confirmed, failed—receive concise announcements. Streaming/running updates are throttled to avoid screen-reader churn.
- Inbox row, task detail, approval page, push notification destination, and Tauri tray expose the same canonical label and task identity.
- On phone, attention state and primary safe action appear before secondary metadata; attempt/audit history remains reachable without a wide table.
- Long histories virtualize without losing chronological reading order, headings, focus, or access to earlier attempts.
- Offline/stale/source-unavailable substate always includes timestamp and recovery text; it does not visually overwrite durable status.

## Metrics and guardrails

- Cross-source identity collisions: zero in generated and live contract suites.
- Sensitive actions with actor, target, correlation ID, and audit outcome: 100%.
- Reducer contract coverage: every allowed underlying-state combination, transition, race, and adapter fallback.
- Duplicate run, decision, notification, or audit effect from retries: zero.
- Status disagreement among inbox/detail/PWA/Tauri/tray for the same projection version: zero.
- Unknown/unverified upstream state coerced to done, failed, or cancelled: zero.
- Time from current interrupt to needs-review projection/notification and time from resolution to badge convergence are measured by source, excluding private content.
- Guardrails: no external identity without source, no terminal state from transport loss, no retry overwriting history, no client-only cancellation confirmation, and no delete in v1.

## Dependencies, external contract gates, rollout, and rollback

### Dependencies and gates

- `DW-FND-003` for state ownership, FastAPI `/api/v1`, Postgres, authorization, and audit persistence.
- `DW-FND-004` consumes this vocabulary and must prove that source events, capability evidence, resume, idempotency, and fixture/live conformance map into these accepted facts without redefining them.
- `SPIKE-STREAM-001` must prove start/queue/interrupt/cancel/retry/terminal/checkpoint identities and reconciliation per enabled classic transport.
- `SPIKE-MDA-001` and `SPIKE-FLEET-001` must establish any runtime-specific agent/source/deployment identity relation before bindings are enabled.
- Product review must accept vocabulary, precedence, retry/cancel/archive semantics, delete deferral, and removal of ambiguous “Mark resolved.”
- Security/privacy review must accept audit schema, retention, redaction, access, export, and deletion rules.

### Proposed rollout

1. Freeze glossary, identity keys, status facts, precedence, transition table, mutation versions, and audit schema in fixtures.
2. Build pure reducer/property tests and FastAPI/Postgres uniqueness/idempotency tests.
3. Run classic deployment spike and map only verified events/queries to facts.
4. Integrate task inbox/detail, then approvals, notifications, PWA, and Tauri against the same projection.
5. Inject cancel/retry/reconnect/permission/stale races and prove convergence.
6. Enable MDA/Fleet bindings only after accepted identity contracts.

### Rollback

- Version normalized facts/projections and retain a migration adapter during rollout. Recompute derived status from durable facts when reducer logic rolls back.
- Do not delete upstream resources or append-only audit history during application rollback.
- If a transition mapping is unsafe, disable the affected mutation/capability and show `status-unavailable` while retaining last durable evidence.

## Executable acceptance scenarios

```gherkin
Scenario: Identical provider IDs remain separate across sources
  Given source A and source B both return thread id thread-1 and run id run-1
  When Deep Work creates task projections
  Then each task has a distinct application task id
  And its SourceThreadKey and SourceRunKey include the correct source id
  And notifications, audit events, and deep links cannot cross the sources

Scenario: Pending interrupt owns attention without erasing run state
  Given a source reports an active run and a current pending interrupt batch
  When the reducer processes normalized facts
  Then the task status is needs-review
  And underlying run-active evidence remains available
  And inbox, detail, approval, push destination, and tray use the same projection version

Scenario: Cancel and reconnect converge on authoritative state
  Given a user sends an idempotent cancel and the client disconnects while it is cancelling
  When the client reconnects and hydrates the source-confirmed outcome
  Then the reducer reaches cancelled only if cancellation is authoritative
  And transport disconnect alone never produces cancelled or failed
  And the cancel request and source outcome are both audited

Scenario: Retry preserves every attempt
  Given attempt 1 ends in authoritative failure
  When the user retries through a supported source adapter
  Then a new run attempt links to attempt 1
  And attempt 1 remains failed in history
  And successful attempt 2 makes the task done without rewriting attempt 1

Scenario: Source outage preserves a historical outcome
  Given a task is authoritatively done
  When its source becomes unreachable
  Then the task remains done with source-unavailable and an observed timestamp
  And no failed status or duplicate notification is created

Scenario: A stale approval is never recorded as accepted
  Given an interrupt batch has advanced from version 3 to version 4
  When a client submits ordered decisions for expected version 3
  Then the mutation returns a stale conflict
  And no decision effect is sent or duplicated
  And the client refetches version 4
```
