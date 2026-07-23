---
feature_id: DW-HITL-002
title: Rubrics, goals, and verification history
release: v1
status: canonical-spec
decision_status: blocked-on-spikes
owners: [verification, agent-runtime, task-experience, api]
surfaces: [web, pwa, desktop, api, agent]
runtime_scopes: [classic, mda, fleet, local]
source_refs: [SRC-FE, SRC-LC, SRC-DW, SRC-DP]
dependencies: [DW-TASK-002, DW-TASK-003, DW-FND-003, DW-FND-005]
contract_gates: [SPIKE-RUBRIC-001, SPIKE-VERIFICATION-001]
last_reviewed: 2026-07-22
---

# Rubrics, goals, and verification history

## User outcome

A user can state what success means before work starts, see which criteria the agent or verifier evaluated, distinguish execution completion from verification, and inspect every verdict and retry without a failed criterion being hidden by a final fluent answer. Sources that cannot run automatic verification still preserve a useful manual checklist and never claim a pass.

## Evidence and confidence

| Evidence | Classification | Planning consequence |
|---|---|---|
| Prototype settings include goals/rubrics and fixture subagents reference a critic, but no runtime evaluation is wired. | Prototype evidence at `26c698b`; simulated | Keep task-scoped goal/rubric concepts; replace mock scores with attributable verdict records. |
| Canonical planning proposes `RubricMiddleware`, verdict iterations, default task-template rubrics, and configurable caps. | Internal intent at `06f0515` | The Python starter agent owns the automatic loop and its state schema. |
| Rubric middleware is a beta/version-sensitive Deep Agents capability. | Documented/gated at `7b9215d` | `SPIKE-RUBRIC-001` pins package behavior; external sources must declare conformance. |
| A goal lifecycle beyond one task is explicitly later-scope. | Internal cut line | v1 `goal` means the task's user outcome, constraints, and completion criteria, not an autonomous long-lived goal object. |

## Scope and ownership

### In scope

- Task goal: concise outcome, constraints, required deliverables, and task-scoped rubric.
- Versioned rubric criteria from a template or user edits before dispatch.
- Required versus advisory criteria and optional evidence expectations.
- Automatic verification on the starter Python agent when the pinned middleware passes conformance.
- Bounded repair/retry iterations, cost/time caps, explicit terminal reason, and cancellation.
- Verdict history with criterion results, safe rationale summary, evidence references, verifier identity/config reference, timestamps, and attempt/run lineage.
- Manual review checklist when automatic verification is unsupported or intentionally disabled.
- Separate execution and verification statuses in inbox/detail/artifact views.

### Out of scope

- Multi-task strategic goal lifecycle, goals that schedule their own work, or goal amendment workflows.
- Claiming LLM-as-judge is ground truth.
- LangSmith dataset/evaluation product replacement.
- Silent rubric mutation after dispatch.
- Unbounded self-repair or a default that spends until every subjective criterion passes.

### Ownership

- The Python Deep Agents package owns task-state integration, verifier invocation, bounded repair policy, and emitted verification records.
- FastAPI owns rubric/version persistence, capability validation, normalized verdict catalog, cost/iteration guardrails, and user review actions.
- Postgres owns task goal, immutable dispatched rubric version, normalized verdict metadata/history, and manual-review records.
- FastAPI normalizes verification facts, `packages/sdk` maps the application contract, and `packages/domain` owns client-safe status/verdict types; Next.js/Tauri own authoring, progress, evidence links, and accessible history.
- LangSmith owns underlying run/trace data; provider models generate fallible verdicts.

## Product semantics

- `executionStatus` answers whether the agent run is queued, active, interrupted, failed, cancelled, or completed.
- `verificationStatus` answers whether the rubric is not requested, pending, running, passed, failed, capped, errored, manually reviewed, or unsupported.
- A completed run with failed verification is **Completed - verification failed**, not simply Done.
- A user may accept the output despite failed/unsupported verification, but that records **accepted with exception** and never rewrites failed criteria to passed.
- Template rubrics are defaults. The dispatched task stores the exact immutable version the user reviewed.

## Primary journey

1. The composer presents the selected template's goal and rubric with provenance, required criteria, and verification availability for the chosen source.
2. The user edits criteria before dispatch. Preflight stores an immutable rubric version with the task input.
3. The agent executes and produces candidate output/evidence.
4. If automatic verification is supported, the verifier evaluates each criterion and emits a verdict record linked to the candidate attempt.
5. On failure, the bounded policy either asks the agent to repair and records another iteration, or stops because of iteration, cost, time, user, or non-retryable limits.
6. Task detail shows the latest result and complete ordered history. Evidence links open the exact artifact/file/test/trace reference used where available.
7. The user can request a normal follow-up/retry, mark the checklist manually reviewed, or accept with exception. History remains immutable.

## State matrix

| State | Required behavior | Recovery / transition |
|---|---|---|
| No rubric requested | Verification status not_requested; no score placeholder. | Add only before dispatch or create follow-up task version. |
| Template rubric loaded | Show criterion source/version and required/advisory labels. | Edit/reset before dispatch. |
| Rubric invalid | Identify empty, duplicate, contradictory, overlong, or unsupported rules. | Correct before dispatch. |
| Source unsupported | Show manual checklist and Automatic verification unavailable. | Switch source or proceed manually. |
| Execution active | Verification pending; do not show a provisional pass. | Await candidate output. |
| Verification queued | Show candidate attempt and queue reason if known. | Start, cancel, or timeout. |
| Verification running | Show current iteration and cap, not fabricated percentage. | Verdict, error, or cancel. |
| Criterion passed | Show pass, evidence refs, verifier/config reference, and time. | Remains immutable in that verdict. |
| Criterion failed | Show fail/uncertain result and safe rationale/evidence gap. | Repair iteration or stop. |
| Mixed verdict | Overall fail if any required criterion fails; advisory failures remain visible. | Repair or accept with exception. |
| Repair running | Link new candidate attempt to prior failed verdict. | Reverify or fail execution. |
| Passed after repair | Keep all earlier failed verdicts; latest overall status passed. | Review output/history. |
| Iteration cap reached | Overall capped/failed; explain cap and remaining criteria. | User follow-up, change rubric in new attempt, or accept exception. |
| Cost/time cap reached | Stop safely and show budget reason. | Increase policy in a new attempt if authorized. |
| Verifier error | Distinguish tool/model outage from rubric failure. | Retry verifier within cap or manual review. |
| Evidence unavailable/stale | Do not pass an evidence-required criterion solely on narrative. | Restore evidence or mark unverifiable. |
| Rubric changed after task | Historical task retains original version; new version affects new tasks/attempts only. | Compare versions. |
| Manual review incomplete | Ordered checklist with reviewer identity and no automatic score. | Complete or leave pending. |
| Manual review complete | Record checked criteria and exceptions; label human-reviewed. | Remains separate from automatic pass. |
| Accepted with exception | Record actor, failed/unsupported criteria, and reason. | Does not mutate verdict. |
| Offline | Cached history read-only and visibly stale. | Re-fetch before review mutation. |
| Permission revoked | Hide restricted evidence and disable review mutations. | Reauthenticate/switch. |

## Proposed interfaces and runtime fallback

```ts
interface TaskGoal {
  outcome: string;
  constraints: string[];
  deliverables: string[];
}

interface RubricVersion {
  rubricId: string;
  version: number;
  source: "template" | "user";
  criteria: Array<{
    criterionId: string;
    text: string;
    required: boolean;
    evidenceRequired?: boolean;
  }>;
  policy: { maxIterations: number; maxVerifierCost?: number; maxWallSeconds?: number };
}

interface VerificationVerdict {
  verdictId: string;
  taskId: string;
  attemptId: string;
  rubricId: string;
  rubricVersion: number;
  iteration: number;
  verifierRef: string;
  results: Array<{
    criterionId: string;
    outcome: "pass" | "fail" | "uncertain" | "not_evaluated";
    rationaleSummary?: string;
    evidenceRefs: string[];
  }>;
  overall: "pass" | "fail" | "capped" | "error";
  createdAt: string;
}
```

Proposed operations are `GET /api/v1/tasks/{id}/rubric`, `GET /api/v1/tasks/{id}/verdicts`, and audited manual-review/accept-exception mutations. Automatic verifier state arrives through the starter agent's versioned runtime state and is normalized by the application service.

`SPIKE-RUBRIC-001` must pin Python/deepagents/LangChain versions and prove middleware initialization, state/output schema, criterion ordering, repair loop, interrupt interaction, caps, cancellation, failure, and resume after reconnect/redeploy. It must record whether verifier/model configuration can be referenced without exposing secrets.

`SPIKE-VERIFICATION-001` must establish the starter templates' default rubrics and evidence bindings for research, writing, and coding. A contract fixture must prove that test/CI failure, missing citations, or missing deliverables cannot be hidden by a generic pass summary.

Deterministic fallback is an application-owned manual checklist using the same immutable criteria. Its state is `unsupported` or `manually_reviewed`, never an automatic score. External sources may supply verdicts only after their schema and provenance pass conformance; arbitrary model messages are not parsed as verdicts.

## Persistence and security

- Store goal, rubric versions, verdict metadata, safe rationale summaries, evidence references, and review audit in tenant-scoped Postgres.
- Do not store hidden model reasoning as rationale. Persist only a user-displayable summary emitted for that purpose.
- Treat verifier output and evidence labels as untrusted. Validate identifiers, lengths, media types, and artifact/task ownership.
- Never send secrets, unrelated memory, hidden credentials, or cross-tenant artifacts to a verifier. The agent package builds a least-necessary evaluation context.
- Cost/iteration/time limits are server-enforced; agent/model output cannot raise them.
- Manual and exception actions require current authorization, CSRF protection, idempotency, and an actor-scoped audit event.
- Historical verdicts are append-only. Corrections create a superseding record with reason rather than editing history.

## Responsive and accessible behavior

- Criteria are an ordered semantic list with textual result, required/advisory label, iteration, and evidence links.
- Pass/fail/uncertain use text and icon in addition to color. Score alone is never the accessible name.
- Mobile starts with overall execution and verification summaries, then expandable criteria/history.
- Evidence links identify artifact/file/test/trace target and unavailable state.
- Verification live updates are announced at iteration/verdict boundaries, not token-by-token.
- Charts are not required for v1; history is usable as text/table at 200% zoom and by keyboard.
- Reduced motion removes verification pulses.

## Metrics and guardrails

- Verification requested/supported/run rates by task kind and source.
- Pass-first-time, pass-after-repair, failed, capped, verifier-error, manual-review, and accepted-exception rates.
- Iterations, wall time, and cost per verified task with tenant-safe aggregation.
- Criterion evidence-coverage rate and stale/missing evidence rate.
- Guardrails: zero automatic pass when required criterion is fail/uncertain/not evaluated; zero history mutation; 100% loops stop at configured cap.

## Dependencies and rollout

- Depends on composer/task detail, artifact provenance, task identity/audit, and the Python agent package.
- Phase 0: accept middleware and journey-specific verification fixtures.
- Phase 1: manual checklist for all sources and automatic coding-test rubric on internal classic source.
- Phase 2: research/writing automatic verification after evidence bindings pass review.
- Phase 3: enable conformance-tested external sources individually.
- On middleware drift, set automatic verification unavailable, stop new loops, preserve verdict history, and use manual review.

## Executable acceptance scenarios

```gherkin
Scenario: Required failed criterion prevents automatic pass
  Given a rubric has two required criteria
  And the verifier marks one pass and one fail
  When the verdict is normalized
  Then overall is fail
  And task execution may be completed while verification is failed
  And the UI does not show a generic Done state

Scenario: Repair history remains visible
  Given iteration 1 failed and iteration 2 passed after a repair
  When the user opens verification history
  Then both verdicts appear in order with their candidate attempt links
  And iteration 1 has not been overwritten

Scenario: Unsupported runtime uses manual checklist honestly
  Given a source has automaticVerification false
  When a task with a rubric completes
  Then verification status is unsupported
  And the same criteria are available for manual review
  And no numeric or automatic pass score is shown

Scenario: Iteration cap stops the loop
  Given maxIterations is 2 and both verifier attempts fail
  When the second verdict is recorded
  Then no third repair run is started
  And verification status is capped
  And the remaining failed criteria are visible
```
