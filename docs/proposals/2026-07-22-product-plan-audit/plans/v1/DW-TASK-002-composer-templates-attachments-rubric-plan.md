---
feature_id: DW-TASK-002
title: Task composer, templates, attachments, rubric, and plan approval
release: v1
status: proposed
decision_status: blocked-on-spikes
owners: [task-experience, agent-runtime, source-platform, web, security]
surfaces: [web, pwa, desktop, api, agent]
runtime_scopes: [classic, mda, fleet, local, fixture]
source_refs: [SRC-FE, SRC-LC, SRC-DW, SRC-DP]
evidence_pins:
  frontend: 8866d39
  langchain_docs: 7b9215d
  canonical_plan: 06f0515
dependencies: [DW-ONB-002, DW-TASK-001, DW-FND-003, DW-FND-004, DW-FND-005]
contract_gates:
  - SPIKE-COMPOSE-001
  - SPIKE-ATTACH-001
  - SPIKE-PLAN-001
last_reviewed: 2026-07-22
---

# Task composer, templates, attachments, rubric, and plan approval

## User outcome

A user can describe work, deliberately choose the agent source and task type, attach supported context, set completion criteria, require a plan review where the runtime can enforce it, and dispatch exactly one task with a clear summary of what will run and where.

## Evidence and confidence

| Evidence | Classification | Planning consequence |
|---|---|---|
| The prototype new-task route presents a polished but fixture-backed composer. | Prototype evidence at `8866d39`; simulated | Preserve the low-friction composition flow but add real validation, upload, capability, and idempotency states. |
| Canonical plans call for coding, research, and writing templates, attachments, rubric input, environment/repository choices, and plan approval. | Internal intent at `06f0515` | Model these as explicit task inputs and source capabilities, not visual toggles. |
| Deep Agents exposes filesystem, sandbox, HITL, rubric, and multimodal building blocks, but exact deployed input/state schemas are agent-defined. | Documented building blocks at `7b9215d`; integration shape unknown | The versioned Python agent package owns a Deep Work task-input schema; external agents receive only fields their manifest declares. |
| Attachment upload and plan-interrupt behavior differ by source/runtime. | Unknown | Named spikes must establish contracts; unsupported controls are disabled with deterministic alternatives. |

## Scope and ownership

### In scope

- Prompt with autosaved local/application draft and explicit dispatch.
- Source, assistant, task kind, template, repository, branch/base, and environment selection when supported.
- Versioned research, writing, coding, and blank templates.
- Supported text, image, PDF, and code attachments with size/type/count policy.
- Completion rubric entry, default rubric preview, and explicit user edits.
- **Require plan approval** only for sources that declare and pass the plan-approval conformance test.
- Preflight summary, validation, idempotent submission, and safe failure recovery.

### Out of scope

- Arbitrary unscanned binary execution, folders, or unlimited uploads.
- Implicitly turning every prompt into a coding sandbox task.
- Pretending an ordinary user message provides an enforceable plan gate.
- Native voice capture; browser-provided dictation may remain a progressive enhancement.
- Template/configuration authoring; this plan consumes versioned templates.

### Ownership

- Next.js owns the responsive form, client-side safe draft, file-picker affordances, accessible validation, and preflight review.
- FastAPI owns authorization, server draft, upload coordination, validation, idempotency, task/thread/run creation, and dispatch orchestration.
- Postgres owns draft metadata, task input, attachment references, template version, idempotency key, and dispatch audit state.
- The Python Deep Agents package owns the canonical `DeepWorkTaskInput` and template defaults used by the starter agent.
- Target runtimes own thread/run state and accepted attachment/filesystem semantics.

## Primary journey

1. The user opens **New task** from any surface. The default source is selected only if healthy and authorized.
2. Selecting a source loads its current capability manifest; controls that cannot work are hidden or disabled with a reason.
3. Selecting research, writing, or coding applies a visible template version and safe defaults without overwriting user edits.
4. The user writes the request, adds attachments, and optionally edits completion criteria.
5. Coding tasks require repository, base branch, and environment readiness. Research/writing do not require a sandbox unless the template explicitly does.
6. If plan approval is requested, the composer verifies `planApproval: true`; otherwise it offers dispatch without the gate or a compatible source.
7. Preflight summarizes source, agent, permissions, environment, repository, attachment handling, rubric, plan gate, and likely side-effect boundaries.
8. Dispatch uses an idempotency key. Success returns one task ID and routes to detail; uncertain network outcomes are reconciled before retrying.

## State matrix

| State | Required behavior | Recovery / transition |
|---|---|---|
| Blank draft | Show task-kind guidance and no premature errors. | Enter prompt or choose template. |
| Draft restoring | Show non-blocking restore state and origin timestamp. | Restore, discard, or merge if newer server draft exists. |
| Source loading | Disable dispatch and source-dependent controls. | Load manifest or choose another source. |
| Source unavailable/stale | Preserve draft; explain inability to validate. | Reprobe, reconnect, or switch source. |
| Template selected | Show which fields/defaults changed and template version. | Customize or reset to template defaults. |
| Attachment selecting | Enforce accept policy before upload where possible. | Add, cancel, or see validation error. |
| Attachment scanning/uploading | Show per-file progress and permit removing pending files. | Complete, retry failed file, or dispatch without it after explicit removal. |
| Attachment rejected | Name type/size/security reason without echoing unsafe content. | Remove or replace. |
| Attachment unavailable to source | Explain source limitation before dispatch. | Switch source or remove attachment. |
| Coding prerequisites incomplete | Identify missing GitHub, repository, branch, or environment. | Complete prerequisite or change task kind. |
| Rubric default | Display criteria and provenance from template. | Edit, reset, or intentionally disable if policy allows. |
| Rubric invalid | Point to empty/overlong/unsupported criteria. | Correct before dispatch. |
| Plan approval supported | Explain that execution will pause after proposing a plan. | Keep enabled or disable. |
| Plan approval unsupported | Disable toggle; never silently downgrade. | Choose compatible source or proceed without it explicitly. |
| Preflight ready | Present complete execution summary and side-effect posture. | Dispatch or return to edit. |
| Dispatching | Lock mutation fields, allow safe cancel before provider acceptance, and show one operation. | Success, known failure, or reconciliation. |
| Dispatch uncertain | Do not create another run automatically. | Query idempotency/task state, then resume or retry safely. |
| Dispatch failed before acceptance | Preserve draft and uploads where safe. | Retry with same idempotency key or edit. |
| Offline | Keep local draft and attachment metadata; do not imply uploads completed. | Resume when online. |
| Mobile | Use staged sections and a sticky summary/dispatch action that does not cover fields. | Review and dispatch. |

## Proposed interfaces and runtime fallback

```ts
interface DeepWorkTaskDraft {
  draftId: string;
  sourceId?: string;
  assistantId?: string;
  kind: "research" | "writing" | "coding" | "blank";
  template: { id: string; version: string };
  prompt: string;
  repository?: { installationId: string; owner: string; name: string; baseBranch: string };
  environmentId?: string;
  attachmentIds: string[];
  rubric?: { criteria: Array<{ id: string; text: string; required: boolean }>; maxIterations?: number };
  requirePlanApproval: boolean;
}

interface CreateTaskResult {
  taskId: string;
  sourceId: string;
  threadId: string;
  runId?: string;
  dispatchState: "accepted" | "queued" | "awaiting_plan";
}
```

Proposed application operations:

- `POST /api/v1/task-drafts`, `PATCH /api/v1/task-drafts/{id}`, and `DELETE /api/v1/task-drafts/{id}` manage recoverable drafts.
- `POST /api/v1/attachments` creates an upload/transfer intent after policy validation.
- `POST /api/v1/tasks` validates the manifest and dispatches using an `Idempotency-Key`.
- Query and mutation services remain separate from the React streaming hook; the composer never reaches into stream internals to create a task.

`SPIKE-COMPOSE-001` pins thread/run creation and input schema behavior for the starter Python agent and each supported external-source class. Unknown fields are never sent opportunistically.

`SPIKE-ATTACH-001` establishes where bytes live, how the selected runtime receives them, supported media representation, limits, malware scanning, deletion, and failure semantics. Preferred v1 behavior is direct transfer to an authorized provider/sandbox or a bounded application upload service with Postgres metadata. If no safe transfer exists, attachments are disabled for that source; pasted text with explicit size limits is the fallback.

`SPIKE-PLAN-001` establishes a versioned plan proposal and approval signal implemented by the starter agent using the normalized HITL batch contract. If a source does not pass it, **Require plan approval** is unavailable; Deep Work does not approximate the gate with prompt wording.

## Persistence and security

- Persist prompt/task input only for the chosen tenant and according to retention settings; drafts have an expiry and explicit delete action.
- Store attachment metadata and integrity hash in Postgres. Store bytes only in an approved encrypted object/provider store, never a normal database column or analytics event.
- Strip path traversal, executable metadata, active HTML, macros where policy requires, and unsafe filenames. Scan uploads before making them visible to an agent.
- Treat attachment contents and template text as untrusted model input. Boundary markers and agent instructions never imply that content is trusted policy.
- Repository and environment choices are authorized again on dispatch. A stale UI choice cannot grant access.
- Idempotency records bind actor, tenant, normalized request hash, and outcome; a reused key with different input is rejected.
- Template and rubric versions are immutable on an existing task so later edits do not rewrite execution history.

## Responsive and accessible behavior

- Every field has a persistent label, description, and programmatic error association.
- File upload works through keyboard-accessible picker and optional drag/drop; drag/drop is never the only path.
- Progress exposes filename, safe status, bytes/percentage where known, cancel, and retry. Status is not color-only.
- Mobile presents Prompt, Context, Completion criteria, and Review as logical steps while preserving one form and draft.
- Preflight is a semantic summary with Edit links that return focus to the relevant field.
- Plan-approval and permission explanations are readable at 200% zoom. Reduced motion removes progress animations.

## Metrics and guardrails

- Composer start-to-dispatch conversion and median composition time by task kind.
- Validation failure rate by category and prerequisite abandonment rate.
- Attachment upload success, scan rejection, retry, and orphan-cleanup rate.
- Plan-approval opt-in rate among capable sources and explicit unsupported-source encounters.
- Duplicate-dispatch prevention/reconciliation count.
- Guardrails: zero execution with failed attachment scan; zero silent downgrade of requested plan approval; zero duplicate task for one idempotency fixture.

## Dependencies and rollout

- Depends on source manifests, authentication, task identities, persistence, and SDK contracts. HITL, verification, and coding plans consume the composer's versioned draft and preflight contract; their fields stay capability-gated until those owning plans pass.
- Phase 0: accept compose, attachment, and plan conformance fixtures.
- Phase 1: text-only research/writing/blank tasks on the starter classic source.
- Phase 2: rubric and enforceable plan approval on the starter agent.
- Phase 3: attachments by validated media/source class.
- Phase 4: coding preflight after environment and GitHub plans are green.
- Roll back an input capability by disabling it in the source manifest; existing tasks retain immutable input history.

## Executable acceptance scenarios

```gherkin
Scenario: Dispatch creates exactly one task after a timeout
  Given a valid research draft and an idempotency key
  And the provider accepts the run but the client response times out
  When the client reconciles and retries with the same key
  Then FastAPI returns the original task, thread, and run identifiers
  And no second provider run is created

Scenario: Requested plan approval never downgrades silently
  Given a source whose manifest has planApproval false
  When the user opens the composer
  Then Require plan approval is disabled with an explanation
  And no prompt-only approximation is offered as equivalent

Scenario: Unsafe attachment is blocked before agent visibility
  Given the malware fixture marks an uploaded file unsafe
  When upload processing completes
  Then the attachment state is rejected
  And the file is not transferred to the source or sandbox
  And dispatch remains blocked until it is removed

Scenario: Coding task preflight shows all execution boundaries
  Given a healthy source, GitHub installation, repository, base branch, and environment
  When the user opens preflight
  Then it names the source, assistant, repository, branch, environment, rubric, plan gate, and attachments
  And dispatch uses those immutable reviewed values
```
