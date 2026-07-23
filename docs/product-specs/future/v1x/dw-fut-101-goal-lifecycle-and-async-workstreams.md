---
feature_id: DW-FUT-101
title: Goal lifecycle and asynchronous workstreams
release: v1.x
status: canonical-deferred-brief
decision_status: discovery-gated
owners: [agent, api, web]
surfaces: [task-composer, task-detail, inbox]
runtime_scopes: [classic, mda]
source_refs: [SRC-DW, SRC-LC]
dependencies: [DW-TASK-004, DW-TASK-005, DW-HITL-002]
last_reviewed: 2026-07-23
---

# Goal lifecycle and asynchronous workstreams

> This is a discovery-gated v1.x product brief. It defines the intended experience, not a verified runtime design. No child-run, goal-middleware, or cancellation contract is ready for implementation until the gates below are closed against pinned packages and live contracts.

## User outcome

Users can agree on measurable success before expensive work begins, supervise several durable workstreams as one goal, and understand what completed, failed, paused, or still needs review without reconstructing state from chat history.

## Evidence and confidence

- `SRC-DW` supports goal-oriented work, rubric-based verification, supervisors, and async subagents as product direction. Confidence: medium for the outcome, low for the exact runtime representation.
- `SRC-LC` supports durable threads, runs, interrupts, and subagent patterns, but this brief does not treat an unverified async-task, compaction, or cancellation shape as public contract. Confidence: medium, gated by package/live-contract spikes.
- Linked-task fallback uses application-owned identities already proposed in `DW-FND-005`. Confidence: high as a product fallback; implementation readiness remains dependent on the v1 foundations.

## Scope, ownership, and non-goals

The agent owner defines the goal/rubric representation and evidence protocol. The API owner owns durable parent-child relationships, authorization, idempotent mutations, and the aggregate reducer. The web owner owns drafting, review, workstream navigation, and compact/mobile supervision.

In scope:

- Draft, clarify, review, activate, amend, pause, resume, cancel, verify, and complete a goal.
- Versioned objective, constraints, acceptance criteria, required evidence, and reviewer decisions.
- Required and optional child workstreams with independent lifecycle, approvals, traces, artifacts, and cancellation.
- Parent progress derived from durable child/evidence state, never model confidence alone.

Non-goals:

- A general project-management system, arbitrary dependency graphs, resource allocation, billing, or calendar planning.
- Silent goal mutation by an agent, implicit acceptance from inactivity, or automatic completion without criterion evidence.
- Assuming child workstreams are a particular LangGraph/Agent Server primitive before verification.

## Primary journeys

1. **Draft and activate:** a user describes an outcome; the agent proposes objective, constraints, criteria, evidence, and workstreams; the user edits and approves revision 1 before execution.
2. **Supervise parallel work:** the parent view shows each required/optional stream, active approval, evidence produced, and impact on overall progress; the user can enter any child without losing parent context.
3. **Amend safely:** a material scope change creates revision 2, pauses affected work, identifies invalidated evidence, and requires explicit review before new-scope work proceeds.
4. **Recover:** after backgrounding, network loss, compaction, or runtime restart, the app reconciles parent and child state without duplicate streams or approvals.
5. **Conclude:** the reducer evaluates each criterion, presents missing or conflicting evidence, and allows complete, partial-complete, failed, or cancelled closure with a durable summary.

## Complete state matrix

| State/condition | Expected experience |
| --- | --- |
| Loading | Show goal metadata and workstream skeletons separately; never imply zero workstreams while either query is pending. |
| Empty | A new draft explains criteria and workstreams and offers a bounded “propose goal” action; an active goal with no workstreams is explicitly valid only when the plan requires none. |
| Draft | Objective and criteria are editable; no execution occurs. |
| Awaiting review | Display immutable revision diff and approve/edit/reject/request-clarification actions. |
| Active | Show evidence-linked progress and independent child states: queued, running, needs-review, paused, done, failed, or cancelled. |
| Amendment pending | Keep the last approved revision visible, identify affected streams, and block only work that depends on unapproved scope. |
| Paused | Preserve streams and evidence; show who paused the goal, why, and what resume will do. |
| Partially complete | Identify satisfied, waived, and unresolved criteria; require an explicit authorized closure decision. |
| Complete/failed/cancelled | Render a terminal summary, criterion verdicts, child disposition, provenance, and allowed retry/branch actions without changing history. |
| Error | Preserve last confirmed state, label the failed operation, and offer idempotent retry; never optimistically claim activation, cancellation, or completion. |
| Offline | Permit local reading of a clearly timestamped cache; queue no goal-scope, approval, or cancellation mutation unless an offline mutation policy is later approved. |
| Permission denied | Explain the denied action without exposing hidden children, actors, or evidence; retain authorized read-only context where allowed. |
| Reconnecting | Freeze destructive controls, show last confirmed cursor/time, and reconcile before accepting more commands. |
| Stale/conflicted | Mark the displayed revision stale, fetch the latest version, and require rebase/re-review instead of last-write-wins. |
| Mobile | Merge goal summary, active approval, and next required action into a compact landing view; place the full workstream tree in an accessible drill-down. |

## Proposed interfaces (non-binding)

Illustrative application-owned concepts are `Goal`, `GoalRevision`, `GoalCriterion`, `WorkstreamRef`, `CriterionEvidence`, and `GoalDecision`. Each carries application ID, source identity, actor/audit fields, version, and timestamps. A proposed service boundary would separate goal query/mutation operations from runtime orchestration and streaming.

Candidate operations include create draft, propose revision, review revision, pause/resume/cancel goal, create/cancel child, attach evidence, and reconcile aggregate state. Names, payloads, endpoint paths, and the mapping to runtime threads/runs are intentionally unspecified until discovery. Every mutation must accept an idempotency key and expected version.

## Runtime capability and fallback

- A source capability manifest must report whether durable child execution, per-child cancellation, resumable state, and stable parent-child metadata have been verified.
- Classic Deployment and capability-detected MDA adapters may map workstreams differently; UI semantics must remain source-neutral.
- If native async workstreams are unavailable or ambiguous, create ordinary linked Deep Work tasks and keep the goal reducer, review state, and relationship metadata in the application service.
- If durable cancellation is unavailable, expose “stop requested” until the source confirms a terminal state; never display cancelled on request alone.

## Persistence and security

Persist revisions, criterion decisions, child identities, evidence references, aggregate snapshots, idempotency records, and audit events in application storage. Runtime content remains referenced rather than copied unless the retention policy explicitly permits a snapshot. Encrypt sensitive evidence references and never persist provider credentials in goal records.

Authorization is checked independently for goal mutation, child access, approvals, evidence access, and cancellation. Parent summaries must not leak the existence or title of an unauthorized child. A revision records proposer, reviewer, decision, affected criteria, and rollback lineage.

## Responsive and accessible behavior

Desktop uses a goal summary with a navigable workstream/evidence region; narrow screens use progressive disclosure and a persistent “next action” summary. Accessibility requirements include non-color state, text progress equivalents, logical heading/list structure, keyboard-operable diffs, descriptive revision notifications, and reduced-motion progress transitions.

## Metrics and guardrails

- Time from draft to approved goal; clarification and amendment rates.
- Percentage of terminal goals with criterion-linked evidence; unsupported-completion rate must remain zero.
- Workstream recovery, duplicate-child, cancellation-confirmation, and stale-revision conflict rates.
- Reviewer burden and percentage of goals closed partial/failed after being shown as “on track.”
- Guardrails: no execution before approval where review is required; no unauthorized child metadata; no completion derived only from model assertion.

## Dependencies

- `DW-TASK-004` for lifecycle, queues, cancellation, reconnect, and branching semantics.
- `DW-TASK-005` for child-task journeys, artifacts, and subagent visibility.
- `DW-HITL-002` for criteria, rubrics, verdict evidence, and history.
- `DW-FND-003` and `DW-FND-005` transitively provide durable state, authorization, identities, and audit.

## Rollout and rollback

1. Internal fixture-mode usability study with linked ordinary tasks.
2. Read-only goal summary generated from manually linked tasks.
3. Feature-flagged drafting/review for one verified runtime tier; no automatic child launch.
4. Limited child orchestration after recovery and cancellation conformance passes.
5. Broaden by capability rather than source label.

Rollback disables goal creation/orchestration while preserving read-only revisions, links, evidence, and export. Active children remain ordinary tasks and are never deleted or silently cancelled by feature rollback.

## Executable acceptance scenarios

1. Given a draft with three criteria, when the user edits and approves revision 1, then execution starts once and every criterion retains its accepted wording.
2. Given an active goal, when an agent proposes a material amendment, then affected work pauses and revision 2 cannot execute before authorized review.
3. Given three required child streams, when one completes, one requests approval, and one is cancelled, then the parent reducer shows the exact criterion impact and does not claim completion.
4. Given a lost connection after child creation, when the client reconnects with the same idempotency key, then exactly one child exists and no event is duplicated.
5. Given a user without access to one child, when they view the parent, then no title, actor, artifact, or existence signal for that child is disclosed.
6. Given an unsupported async runtime, when the user activates a goal, then linked ordinary tasks provide the same review and aggregate semantics.
7. Given a stale goal revision on mobile, when the user tries to approve it, then the app blocks the decision, refreshes, and presents the new diff accessibly.

## Explicit discovery gates

- **Runtime contract:** pin packages and verify child execution, persistence, compaction, stream recovery, cancellation acknowledgement, and metadata limits in live conformance tests.
- **Representation decision:** choose linked threads/tasks versus a verified native async-task channel and record the capability mapping per source.
- **Reducer proof:** specify deterministic required/optional criterion and child-state reduction, including partial completion and late events.
- **Agent contract:** prove goal/rubric middleware emits stable machine-readable evidence without an unsupported upstream fork.
- **Product research:** validate that users understand goal revisions, stream hierarchy, and partial completion on desktop and mobile.
- **Operations:** establish stuck-child reconciliation, audit retention, and support procedures.

The brief cannot advance to implementation-ready until every gate has an owner, evidence artifact, and accepted decision; any unresolved external contract keeps the dependent capability disabled.
