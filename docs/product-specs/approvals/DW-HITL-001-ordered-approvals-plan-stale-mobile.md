---
feature_id: DW-HITL-001
title: Ordered approvals, plan review, stale-race handling, and mobile action
release: v1
status: canonical-spec
decision_status: blocked-on-spikes
owners: [task-experience, approvals, sdk, agent-runtime, security]
surfaces: [web, pwa, desktop, api, agent]
runtime_scopes: [classic, mda, fleet, local]
source_refs: [SRC-FE, SRC-LC, SRC-DW, SRC-DP]
dependencies: [DW-FND-003, DW-FND-004, DW-FND-005, DW-TASK-003]
contract_gates: [SPIKE-HITL-001, SPIKE-HITL-002]
last_reviewed: 2026-07-22
---

# Ordered approvals, plan review, stale-race handling, and mobile action

## User outcome

A user can review every pending human decision across connected sources, understand the exact proposed actions and allowed responses, decide a complete aligned batch in order, and safely resume the right interrupt once. Plan review uses the same enforceable mechanism. Mobile provides a fast review path without reducing authorization or bypassing required context.

## Evidence and confidence

| Evidence | Classification | Planning consequence |
|---|---|---|
| The prototype approvals page filters fixture shell/write/commit approvals and its action component only changes local state. | Prototype evidence at `26c698b`; simulated | Preserve inbox/card cues but replace the local verbs with the exact HITL contract and real race states. |
| Pinned LangChain HITL docs define a request containing aligned `action_requests[]` and `review_configs[]`, and responses containing one ordered `decisions[]` entry per action. | Documented at `7b9215d` | Normalization must preserve array order and one-to-one alignment; never flatten by tool name. |
| The documented decisions are approve, edit, reject, and respond; respond is specifically a successful human answer for ask-user tools. | Documented | Render only allowed decisions. Never use respond as a soft rejection. |
| Exact frontend resume surface and casing can differ by package/server version. | Documented in multiple layers; live mismatch risk | `SPIKE-HITL-001` pins transport and normalized fixtures. |
| Existing UI intent includes "Mark resolved," but force-ending/updating state is not the same as a HITL decision. | Unsupported/unsafe | Remove from v1 approval cards unless a separately reviewed administrative termination contract is added. |

## Scope and ownership

### In scope

- Cross-source approvals inbox assembled by per-source reads/known pending interrupts.
- Exact ordered batch rendering for `actionRequests[]` aligned with `reviewConfigs[]`.
- Approve, edit, reject with optional feedback, and respond for ask-user requests, only when allowed.
- Schema-driven editable arguments with a safe JSON fallback.
- Plan proposal as a versioned, starter-agent HITL action/review pair.
- Optimistic locking, stale interrupt detection, duplicate-submit prevention, and post-decision durable reconciliation.
- Mobile push/deep-link landing to an authenticated, full-context approval screen and one-tap approve only when policy allows.
- Audit record for every attempted and accepted decision.

### Out of scope

- Global provider approval APIs assumed to span all sources.
- Force-ending a task under the label **Mark resolved**.
- Partial batch submission unless the verified HITL contract explicitly supports it; v1 assumes a complete ordered vector.
- Approval delegation, team quorum, scheduled auto-approval, or RBAC management.
- Auto-approving from a push notification action without opening an authenticated review surface.

### Ownership

- The Python starter agent configures `interrupt_on`, plan-review actions, allowed decisions, and permission rules.
- FastAPI owns approval aggregation, authorization, idempotency, optimistic version checks, decision submission, audit, and push deep-link issuance.
- Postgres owns normalized pending-approval projections, notification deduplication, last-seen state, and decision audit; runtime durable interrupt state is authoritative.
- FastAPI preserves and normalizes the exact ordered provider batch; `packages/sdk` maps its wire casing and `packages/domain` owns client-safe ordered request/decision types and reducer transitions.
- Next.js/PWA/Tauri own accessible batch forms, context presentation, stale recovery, and mobile landing.

## Normalized contract

```ts
type DecisionType = "approve" | "edit" | "reject" | "respond";

interface NormalizedActionRequest {
  name: string;
  args: Record<string, unknown>;
  description?: string;
}

interface NormalizedReviewConfig {
  actionName: string;
  allowedDecisions: DecisionType[];
  argsSchema?: Record<string, unknown>;
}

interface NormalizedHITLRequest {
  interruptId: string;
  sourceId: string;
  threadId: string;
  runId?: string;
  version: string;
  actionRequests: NormalizedActionRequest[];
  reviewConfigs: NormalizedReviewConfig[];
}

type OrderedDecision =
  | { type: "approve" }
  | { type: "edit"; editedAction: { name: string; args: Record<string, unknown> } }
  | { type: "reject"; message?: string }
  | { type: "respond"; message: string };
```

Normalization accepts only the documented casing variants at the adapter boundary. It rejects a batch when lengths differ, an action cannot be aligned by index/name rules established by the fixture, or an allowed decision is unknown. Components never pair requests by grouping identical tool names.

## Primary journeys

### Approval inbox and batch

1. The inbox queries each source independently and shows partial-source diagnostics.
2. A row identifies task, agent/source, requested actions, age, and risk/permission context without dumping sensitive arguments.
3. Opening the row re-fetches durable interrupt state and records its version.
4. Each action is rendered in array order with its corresponding review config. The user chooses one allowed decision for every action.
5. Editing begins with original arguments and validates against the supplied/known schema. A dirty approved action becomes an explicit edit decision.
6. Preflight summarizes the complete ordered vector and side effects.
7. FastAPI submits once with interrupt/version/idempotency. Success is not shown until durable state no longer contains that pending interrupt or the verified response proves acceptance.

### Plan approval

1. The starter agent emits a plan action containing stable step IDs, text, and version, with allowed approve/edit/reject according to template policy.
2. The inline task card and approvals inbox point to the same interrupt identity.
3. Edit returns a complete versioned plan payload, not an unrelated steering message.
4. Approval resumes execution; rejection feedback tells the agent to revise/stop according to template policy.

### Mobile action

1. Push contains only opaque approval/task identifiers and generic safe copy.
2. Deep link opens the authenticated PWA, refreshes the interrupt, and displays action summary plus risk/context.
3. One-tap approve is offered only for a single current action where approve is allowed, no edit is required, and local policy does not demand expanded review.
4. Any stale, batch, high-risk, or schema-rich request opens the full form.

## State matrix

| State | Required behavior | Recovery / transition |
|---|---|---|
| Inbox loading | Skeleton rows and per-source progress. | Results, empty, partial, or error. |
| No pending approvals | Explain how approval policies create interrupts. | Open tasks/agent config. |
| Partial source failure | Show healthy approvals and failed-source diagnostics. | Retry source. |
| Batch valid | Render all action/config pairs in exact order. | Decide each and review. |
| Batch length mismatch | Block decisions; show schema-error card and support ID. | Refresh/source fix; raw safe copy optional. |
| Unknown decision type | Do not render as approve; block affected batch. | Adapter update/source fix. |
| Approve allowed | Present unedited args and risk context. | Select approve. |
| Edit allowed | Use schema form or safe JSON editor; show changed fields. | Validate and select edit. |
| Reject allowed | Explain tool will not run and feedback guides agent. | Submit optional message. |
| Respond allowed | Label as answering the agent; require message. | Submit successful tool response. |
| Decision not allowed | Control absent, not merely disabled without reason. | Choose allowed decision. |
| Incomplete batch | Submit disabled; identify missing decisions. | Complete vector. |
| Submitting | Disable duplicate action; retain review summary. | Accepted, stale, denied, or retryable failure. |
| Already decided elsewhere | Mark stale with actor/time if authorized; do not resubmit. | Refresh task. |
| Interrupt changed | Diff old/new action summary; discard unsubmitted vector only after warning. | Re-review current version. |
| Run cancelled/completed | Close approval as stale/superseded, not approved. | Open task outcome. |
| Accepted, resume connecting | Show decision accepted separately from agent resumed. | Reconnect/poll task. |
| Resume failed after acceptance | Reconcile durable interrupt before retrying. | Show current state; never duplicate blindly. |
| Plan awaiting review | Render ordered steps, version, edit/reject semantics. | Submit current plan decision. |
| Push opened signed out | Preserve opaque return target; reveal no details. | Authenticate then re-fetch. |
| Mobile one-tap eligible | Require deliberate button press on refreshed state. | Accept once. |
| Offline | Show cached summary as stale; decision controls disabled. | Re-fetch online. |
| Permission revoked | Remove sensitive arguments and controls immediately. | Reauthenticate/switch. |

## Interfaces and runtime fallback

Proposed application operations:

- `GET /api/v1/approvals` aggregates normalized pending records per source.
- `GET /api/v1/approvals/{id}` rehydrates current runtime truth.
- `POST /api/v1/approvals/{id}/decision` accepts `{version, decisions, idempotencyKey}`.
- `GET /api/v1/tasks/{id}/current-interrupt` lets task detail share the same projection.

`SPIKE-HITL-001` must capture a pinned classic deployment transcript for single and repeated-name batched actions, all four decision types, snake/camel input, resume transport, post-resume state, invalid lengths, and duplicate/stale responses. The application uses the exact accepted resume operation, not a legacy `submit(null, {command:{resume}})` assumption.

`SPIKE-HITL-002` must prove the starter agent's plan-review payload, edit semantics, and restart/reconnect behavior. If plan review fails conformance, the composer capability is false and execution cannot advertise an enforceable plan gate.

For a source without list/search support, approvals are discovered from known task projections and direct current-interrupt reads. Results are marked non-exhaustive. For a source without verified HITL resume, cards are read-only with **Open at source**; Deep Work never invents a mutation endpoint. MDA remains gated and Fleet behavior is enabled only by conformance.

## Persistence and security

- Persist only normalized safe summaries plus encrypted/authorized references where necessary; always re-fetch full action arguments before decision.
- Bind decision authorization to actor, tenant, source, thread, interrupt ID, version, and current workspace membership.
- Apply CSRF, idempotency, replay prevention, rate limits, and expected-version checks to every decision.
- Redact secrets, tokens, environment values, and sensitive tool args in notifications, analytics, logs, and audit summaries.
- Treat action descriptions, schemas, arguments, and tool names as untrusted content. Do not execute embedded links/scripts.
- Edit validation cannot make an unallowed tool allowed. If tool name changes are permitted by middleware, the edited name still passes server policy; otherwise it must equal the original.
- High-risk permission policy may require expanded review even when the runtime technically allows approve.

## Responsive and accessible behavior

- Each batch is a semantic ordered list. Every decision field is labelled with action position, name, and allowed choices.
- Keyboard flow moves through actions in order; a review summary links back to invalid/incomplete entries.
- Argument diffs use text additions/removals and do not rely on red/green alone.
- Mobile cards prioritize requested effect, target, risk, and decision; long JSON opens a full-screen accessible editor.
- Push deep links land on a heading describing the current task/action after authentication.
- Status changes are announced once; focus returns to the inbox or task after accepted decision. Reduced motion removes pending pulses.

## Metrics and guardrails

- Approval arrival-to-open and arrival-to-decision time.
- Decision distribution by allowed type and source, without sensitive argument content.
- Batch validation mismatch, stale-decision, duplicate suppression, and post-accept resume failure rates.
- Mobile notification-to-authenticated-review conversion and one-tap eligibility/use.
- Plan approve/edit/reject and revision-loop rates.
- Guardrails: 100% accepted batches have exactly one decision per action in order; zero respond decisions used as rejection; zero approval from stale push payload without re-fetch.

## Dependencies and rollout

- Depends on auth/security, normalized SDK, identity/status, task detail, notifications/PWA, and starter-agent HITL policy.
- Phase 0: accept all HITL and plan golden transcripts.
- Phase 1: inline single and batch approvals on classic starter agent.
- Phase 2: cross-source inbox and partial-source behavior.
- Phase 3: mobile deep links/push and narrowly eligible one-tap approve.
- Enable adapters independently. On contract drift, switch affected approvals to read-only/Open at source while preserving task state.

## Executable acceptance scenarios

```gherkin
Scenario: Repeated tool names remain aligned by array order
  Given an interrupt has two actionRequests named write_file with different args
  And two aligned reviewConfigs
  When the user approves the first and edits the second
  Then the submitted decisions vector has two entries in the original order
  And the editedAction applies only to the second request

Scenario: Respond cannot be used to reject a side effect
  Given a delete tool allows approve and reject but not respond
  When the approval form renders
  Then no Respond control is present
  And rejection produces a reject decision with optional feedback

Scenario: Stale mobile approval is never submitted
  Given a push refers to interrupt version 1
  And another device resolves it before the PWA opens
  When the user follows the push
  Then the PWA re-fetches current state
  And shows Already resolved
  And sends no decision for version 1

Scenario: Malformed batch fails safely
  Given a fixture has two actionRequests and one reviewConfig
  When the adapter normalizes it
  Then decision controls are blocked
  And the rest of the approvals inbox continues rendering
  And no guessed alignment is submitted
```
