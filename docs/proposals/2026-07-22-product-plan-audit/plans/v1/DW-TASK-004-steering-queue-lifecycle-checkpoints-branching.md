---
feature_id: DW-TASK-004
title: Steering, queue, lifecycle actions, checkpoints, and branching
release: v1
status: proposed
decision_status: blocked-on-spikes
owners: [task-experience, api, sdk, agent-runtime]
surfaces: [web, pwa, desktop, api]
runtime_scopes: [classic, mda, fleet, local]
source_refs: [SRC-FE, SRC-LC, SRC-DW, SRC-DP]
dependencies: [DW-TASK-003, DW-FND-003, DW-FND-004, DW-FND-005]
contract_gates: [SPIKE-STREAM-002, SPIKE-CANCEL-001, SPIKE-CHECKPOINT-001]
last_reviewed: 2026-07-22
---

# Steering, queue, lifecycle actions, checkpoints, and branching

## User outcome

A user can add direction while work is active, see and remove queued follow-ups, cancel safely, retry a failed attempt, rename or archive a task, and fork from a valid checkpoint without accidentally creating duplicate runs or rewriting history. Each action accurately reflects the active source's capabilities.

## Evidence and confidence

| Evidence | Classification | Planning consequence |
|---|---|---|
| The prototype keeps a composer visible during a fixture run, but it does not implement provider queue, interrupt, cancel, retry, archive, or checkpoint behavior. | Prototype evidence at `8866d39`; simulated | Retain the always-available steering concept, not the implied action semantics. |
| Pinned frontend documentation describes `submit` and an `enqueue` multitask strategy; other existing plans mention queue and interrupt modes. | Documented in part at `7b9215d`; package/server parity unknown | Pin exact submit options in `SPIKE-STREAM-002`; expose only conformance-tested modes. |
| Checkpoints and fork-from-checkpoint are supported in parts of LangGraph/Agent Server, but the exact current client surface and cross-run behavior are not established for every source. | Documented in parts; unknown per adapter | Gate edit-and-fork and branch switcher on `SPIKE-CHECKPOINT-001`. |
| Rename and archive are product presentation state; provider delete semantics are risky and inconsistent. | Product decision | Store rename/archive in Postgres. Task deletion is not a v1 lifecycle action. |

## Scope and ownership

### In scope

- Follow-up submission when idle.
- Active-run steering through a verified `enqueue` or interrupt-style strategy.
- A visible ordered queue with cancel-entry and clear-queue only where conformance-tested.
- Cancel active run with pending, confirmed, rejected, timeout, and race states.
- Retry failed/cancelled attempts with explicit input provenance and idempotency.
- Rename and archive/unarchive as application-owned metadata.
- View checkpoints, edit-and-fork from an eligible checkpoint, name a branch, and switch among task branches.
- Attempt/run history with trace links and clear parent relationships.

### Out of scope

- Deleting provider threads, runs, sandboxes, branches, or artifacts.
- Reordering an upstream queue unless the verified runtime supports it.
- Rewinding or mutating a completed run in place.
- Merging conversational checkpoint branches.
- Async workstream orchestration; that is a later-release capability.

### Ownership

- FastAPI owns authorization, idempotency, command reconciliation, local queue fallback, task metadata, archive state, and audit events.
- FastAPI maps verified source capabilities and provider command results into the application contract; `packages/sdk` exposes those browser-safe results separately from React stream rendering.
- Postgres owns task title, archive state, action requests, idempotency records, attempt lineage, and branch labels. The runtime owns runs and checkpoints.
- The Python starter agent owns any queue-aware middleware required beyond provider-native submit behavior, but only after the spike selects a documented mechanism.
- Next.js/Tauri own action affordances, confirmation, optimistic-pending presentation, and race recovery.

## Primary journeys

### Steer or queue

1. The composer labels the next action from current truth: **Send follow-up**, **Add to queue**, or **Interrupt with direction**.
2. The user sees a short explanation of the chosen strategy and can change it only among supported options.
3. FastAPI accepts an idempotent command, records it as pending, and invokes the source adapter.
4. The queue appears in provider order. Entries show safe preview, author, created time, strategy, and Cancel if supported.
5. Provider/live events reconcile pending entries; a timed-out response is queried before any retry.

### Cancel and retry

1. Cancel requires confirmation describing what stops and what remains: task history, files, branch, artifacts, and sandbox policy.
2. Status becomes **Cancelling** without claiming cancellation is complete.
3. The runtime's terminal state confirms Cancelled, or Deep Work reports that the run already finished/failed.
4. Retry creates a new attempt linked to the prior run and reuses the same thread only when the accepted adapter contract says that is correct.
5. The retry review names carried-forward prompt/context and any changed environment, branch, or attachments.

### Rename, archive, and branch

1. Rename updates the local task title without mutating historical user/agent messages.
2. Archive removes the task from default inbox views and leaves direct access, audit, and runtime data intact.
3. For an eligible message/checkpoint, **Edit and fork** opens the original user input, shows the checkpoint boundary, and creates a new provider branch/run through the verified API.
4. Branch switcher shows parent, creation point, latest status, and distinct trace/run history.

## State matrix

| State | Required behavior | Recovery / transition |
|---|---|---|
| Idle follow-up | Send creates a new run/attempt through verified source behavior. | Stream new attempt or show failure. |
| Active, enqueue supported | Composer labels Add to queue and shows existing count. | Accept, cancel entry, or clear. |
| Active, interrupt supported | Warn that current work may be interrupted/superseded. | Confirm and submit once. |
| Active, no multitask capability | Keep draft but disable submit until terminal. | Wait or cancel active run. |
| Queue submitting | Show optimistic pending entry distinct from provider-accepted entry. | Reconcile, fail, or remove. |
| Queue accepted | Show stable provider/local ID and position if known. | Start, cancel, or clear. |
| Queue entry cancel pending | Disable repeat cancel; preserve preview. | Confirm removed, already started, or failed. |
| Local queue fallback | Label queue as Deep Work-managed and serialize dispatch after terminal state. | Cancel locally before dispatch. |
| Cancel available | Explain scope and retain artifacts/history. | Confirm or dismiss. |
| Cancelling | Keep prior status plus cancelling substate; block duplicate cancel/retry. | Confirm terminal or reconcile race. |
| Cancel confirmed | Canonical status cancelled; live stream closed after durable reconciliation. | Retry, archive, or inspect. |
| Cancel loses race to completion | Show completed outcome and audit the rejected/no-op cancel. | Review or retry only if allowed. |
| Retry eligible | Review original attempt and mutable inputs. | Dispatch one linked attempt. |
| Retry ineligible | Explain active run, unresolved interrupt, permission, or source limitation. | Resolve blocker. |
| Rename saving | Optimistically show draft with saving label; retain prior server value. | Confirm or restore on failure. |
| Duplicate title | Allowed; identity is not title-based. | None. |
| Archived | Hidden from default views, direct route retained, mutations governed normally. | Unarchive. |
| Checkpoints loading | Keep message history visible; show bounded skeleton in branch controls. | Populate or show unsupported/error. |
| No eligible checkpoint | Hide edit-and-fork and explain source capability in help. | None. |
| Fork creating | Lock the selected checkpoint/input; show parent link. | Open new branch or typed failure. |
| Checkpoint stale/deleted | Do not fall back to latest silently. | Refresh checkpoint list and ask user to choose. |
| Branch active elsewhere | Branch switch does not cancel its run. | Join selected branch; show status. |
| Offline | Rename draft can remain local; runtime actions and archive sync are disabled/pending explicitly. | Reconcile online. |
| Permission lost | Remove active mutation controls and retain only authorized safe history. | Reauthenticate/switch. |

## Proposed interfaces and runtime fallback

```ts
type SteeringStrategy = "enqueue" | "interrupt" | "after_current";

interface TaskCommand {
  commandId: string;
  taskId: string;
  expectedRunId?: string;
  kind: "follow_up" | "cancel_run" | "retry_run" | "cancel_queue_entry" | "fork_checkpoint";
  idempotencyKey: string;
  payload: unknown;
}

interface TaskAttempt {
  attemptId: string;
  taskId: string;
  sourceId: string;
  threadId: string;
  runId?: string;
  parentAttemptId?: string;
  forkedFromCheckpointId?: string;
  status: string;
}
```

Proposed application operations are `POST /api/v1/tasks/{id}/commands`, `GET /api/v1/tasks/{id}/queue`, `PATCH /api/v1/tasks/{id}` for rename/archive, and `GET /api/v1/tasks/{id}/checkpoints`. Each mutation accepts an idempotency key and an expected current run/version to make races explicit.

`SPIKE-STREAM-002` must pin JS/Python packages and a classic server, then verify idle submit, active `enqueue`, any interrupt strategy, queue introspection, interrupt interaction, ordering, and error shapes. If native queue visibility is missing, FastAPI may provide a labelled `after_current` queue that dispatches only after durable terminal confirmation. It never calls that fallback provider-native.

`SPIKE-CANCEL-001` must establish run-cancel operation, terminal status, queue impact, interrupt impact, and already-terminal races. Until accepted, Stop is absent for that source rather than simulated.

`SPIKE-CHECKPOINT-001` must prove checkpoint listing, message/checkpoint mapping, fork input, new run/thread identity, and stale checkpoint errors. If absent, completed history remains view-only and retry starts from the current durable thread state or a new task as adapter policy specifies.

MDA and Fleet behavior is capability-detected. Classic Deployment is the baseline. No action uses undocumented Fleet/MDA routes.

## Persistence and security

- Persist command request, actor, expected version/run, sanitized payload summary, provider result, and correlation ID for audit and reconciliation.
- Do not persist queue message content beyond task-retention policy; client drafts remain encrypted/tenant-scoped where stored.
- All commands re-authorize task, source, workspace, and relevant GitHub/environment resources.
- Cancel and interrupt are protected against CSRF, replay, duplicate clicks, and stale expected-run IDs.
- Rename is length- and control-character-bounded; render as text only.
- Forked branches inherit no new permissions. Attachments, credentials, and environment access are revalidated at fork/retry time.
- Archive is reversible and does not delete external data. Future delete requires a separate retention and destructive-action plan.

## Responsive and accessible behavior

- Mobile uses one primary composer action plus a labelled strategy menu; dangerous Stop and Interrupt actions are not adjacent to routine Send without separation.
- Queue entries are an ordered semantic list with position and state announced in text.
- Confirmation dialogs name the task and active run outcome, trap focus correctly, and return focus to the invoker.
- Branch relationships are represented in text and headings, not only a graph. The switcher is fully keyboard operable.
- Live queue/cancel changes use throttled polite announcements; cancellation confirmation uses assertive announcement once.
- Reduced motion removes running/queue animations.

## Metrics and guardrails

- Steering acceptance, queue wait, queue cancellation, and strategy-specific failure rates.
- Cancel request-to-terminal latency and completion-race rate.
- Retry success and duplicate-attempt prevention rate.
- Rename/archive failure and reconciliation rate.
- Fork creation success, stale-checkpoint, and branch-switch rates.
- Guardrails: zero duplicate runs from one idempotency key; zero false Cancelled before provider confirmation; zero silent fork from a different checkpoint.

## Dependencies and rollout

- Depends on normalized source capabilities, status/identity model, stream reconciliation, and audit/security foundation.
- Phase 0: accept submit, cancel, and checkpoint conformance fixtures.
- Phase 1: idle follow-up, rename, archive, and retry on classic source.
- Phase 2: native enqueue where verified; labelled application queue elsewhere.
- Phase 3: cancel and checkpoint forks by adapter capability.
- Roll back an unstable strategy in the source manifest; preserve queued local drafts and prevent new commands until reconciled.

## Executable acceptance scenarios

```gherkin
Scenario: Timed-out enqueue does not submit twice
  Given an active run and a verified enqueue source
  And the provider accepts a queued message but the response times out
  When FastAPI reconciles the command and the client retries with the same idempotency key
  Then exactly one queued entry exists
  And the original command result is returned

Scenario: Cancel loses a race to successful completion
  Given an active run completes while a cancel request is in flight
  When the provider reports the run completed
  Then the task status is done, not cancelled
  And the cancel audit result is recorded as a no-op race

Scenario: Stale checkpoint never falls forward silently
  Given checkpoint C is selected for a fork and becomes unavailable
  When the fork command is processed
  Then it fails with checkpoint_stale
  And no run starts from the latest checkpoint

Scenario: Archive is local and reversible
  Given a completed task exists on a classic source
  When the user archives and then unarchives it
  Then only application metadata changes
  And no provider thread, run, artifact, or sandbox deletion is requested
```
