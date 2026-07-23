---
feature_id: DW-FUT-103
title: Evaluation datasets and outcome learning
release: v1.x
status: proposed-brief
decision_status: discovery-gated
owners: [quality, agent, api]
surfaces: [task-detail, activity, agent-detail]
runtime_scopes: [classic, mda, fleet]
source_refs: [SRC-DW, SRC-LC]
dependencies: [DW-HITL-002, DW-OPS-002]
last_reviewed: 2026-07-23
---

# Evaluation datasets and outcome learning

> This v1.x brief is discovery-gated. It proposes a governed staging and export experience; it does not assert current LangSmith dataset, example, experiment, Fleet, permission, or trace-linking contracts. Any live integration requires a pinned-package/live-contract spike.

## User outcome

Teams can turn explicit decisions and verified outcomes into reviewed evaluation examples, measure behavior across agent revisions, and correct or exclude records without treating every click, merge, or model verdict as ground truth.

## Evidence and confidence

- `SRC-DW` supports rubrics, decisions, agent revisions, and organizational learning as product direction. Confidence: medium for the workflow.
- `SRC-LC` describes evaluation and observability concepts, but exact APIs, permissions, and linking behavior are external and version-sensitive. Confidence: unknown until verified.
- HITL edits/rejections, confirmed rubric verdicts, corrected artifacts, and reviewed delivery outcomes are higher-quality signals than implicit engagement. Confidence: medium as a quality hypothesis requiring dataset study.

## Scope, ownership, and non-goals

The quality owner defines eligibility, labels, sampling, evaluation design, and quality thresholds. The agent owner defines revision/evaluator context. The API owner owns consent, redaction, immutable staging snapshots, provenance, correction, exclusion, export, and audit.

In scope:

- Eligibility review for explicit HITL feedback, confirmed rubric outcomes, corrected artifacts, reviewed PR outcomes, and explicit ratings.
- Preview of content, metadata, label, provenance, retention, and destination before staging/export.
- Reviewed staging, label correction, project/source exclusions, application-owned deletion, JSONL export, and optional verified LangSmith adapter.
- Agent-detail links to external experiment analysis rather than rebuilding an experiment platform.

Non-goals:

- Automatic training, reinforcement, fine-tuning, or autonomous production promotion.
- Using raw clicks, completion, merge, or model self-score as truth without policy and review.
- Reimplementing LangSmith experiment analysis, asserting public Fleet CRUD, or copying unrestricted traces into application storage.

## Primary journeys

1. **Nominate an example:** an authorized user selects an eligible task outcome and previews input, output/action, correction, label, source revisions, and redactions.
2. **Review a batch:** a quality reviewer accepts, edits, rejects, excludes, or defers records and sees sampling/label guidance.
3. **Export:** approved records form an immutable versioned package; a verified adapter may publish it or the user downloads reviewed JSONL.
4. **Evaluate revisions:** agent detail links a reviewed dataset/version and agent revisions to an external experiment, then ingests only a minimal result reference if verified.
5. **Correct or delete:** a reviewer corrects a label while preserving lineage, or an authorized administrator removes application-owned staged content under policy.

## Complete state matrix

| State/condition | Expected experience |
| --- | --- |
| Loading | Skeleton record content, policy, and provenance separately; export remains disabled. |
| Empty | Explain eligible signals and current exclusions; never imply that no feedback exists when the query is incomplete. |
| Candidate | Show why it is eligible, explicit versus inferred fields, redaction preview, label confidence, and destination. |
| Needs review | Permit accept/edit/reject/defer/exclude with reason; no export before required review. |
| Approved/staged | Freeze an immutable snapshot and version; later edits create a new revision. |
| Exporting | Show destination, version, record count, retry-safe operation ID, and cancellation behavior if supported. |
| Exported | Show receipt or artifact hash, time, actor, destination, and trace/experiment link only when confirmed. |
| Rejected/excluded/deleted | Preserve non-content audit as policy allows; excluded content never enters export, and deletion status is destination-specific and honest. |
| Error | Distinguish policy, redaction, staging, export, and result-link errors; retain approved local state and offer idempotent retry. |
| Offline | Allow read-only cached queue metadata; nomination, label decisions, and export require connectivity in the initial brief. |
| Permission denied | Hide restricted content and destination details; explain the required application role without leaking dataset existence. |
| Reconnecting | Revalidate task revision, policy, consent, and record version before enabling decisions. |
| Stale | If task content, label guidance, policy, or destination changes, require regeneration/re-review and preserve the superseded revision. |
| Mobile | Support nomination and single-record review; complex batch comparison/export configuration moves to an accessible desktop link, not a broken compressed table. |

## Proposed interfaces (non-binding)

Illustrative entities are `EvaluationCandidate`, `ExampleRevision`, `DatasetDraft`, `DatasetVersion`, `ExportDestination`, `ExportReceipt`, and `EvaluationReference`. Proposed service operations cover nominate, preview redaction, decide, revise label, build version, export, reconcile receipt, and delete application-owned staging.

No endpoint path or LangSmith payload is specified. The application adapter must translate only after current contracts are verified. Snapshots should identify source task/run/trace by authorized reference, agent revision, policy version, label author, and content hash. Mutations require idempotency and expected-version checks.

## Runtime capability and fallback

- Capability detection distinguishes trace-reference access, dataset write, example update/delete, experiment creation/read, and agent revision identity.
- Classic, MDA, and Fleet-related sources may expose different verified capabilities; source labels do not imply support.
- If live dataset write is absent or uncertain, produce a reviewed, schema-versioned JSONL package plus provenance manifest.
- If result linking is unavailable, allow a user-entered external result URL with validation and mark it as user-supplied.

## Persistence and security

Persist policy/consent version, redacted immutable snapshot, source references, label/review lineage, export manifest, artifact hash, receipts, and non-sensitive audit. Avoid copying full traces; retain only the approved evaluation slice. Encrypt staged content, isolate by tenant/workspace/project, and keep credentials in the credential service.

Redaction is fail-closed. Hidden reasoning, secrets, tokens, unrelated attachments, and excluded project content cannot enter a record. Deletion clearly distinguishes local staging deletion from verified downstream deletion; the UI never promises deletion it cannot prove.

## Responsive and accessible behavior

Desktop may compare original/corrected content and revisions side by side; mobile uses ordered panels with a persistent record identity. Accessibility requirements include text equivalents for labels/diffs/validation/confidence, keyboard-navigable queues and tables, announced selection counts, long content that never traps focus, and reduced motion.

## Metrics and guardrails

- Candidate-to-approved rate, edit/reject/exclusion rate, inter-reviewer agreement, and label correction rate.
- Provenance completeness and redaction pass rate; both target 100% before export.
- Export success/duplicate/partial-failure rate and destination reconciliation latency.
- Coverage by journey and agent revision without incentivizing indiscriminate data capture.
- Guardrails: zero unconsented records, zero excluded-content exports, no auto-training/promotion, and no result claim without linked evidence.

## Dependencies

- `DW-HITL-002` supplies reviewed rubrics, verdicts, goals, and decision provenance.
- `DW-OPS-002` supplies trace links and observability boundaries.
- `DW-AGENT-003` transitively supplies versioned agent draft/deploy identity needed for comparisons.
- `DW-FND-003` supplies retention, authorization, secure persistence, and idempotency.

## Rollout and rollback

1. Offline feasibility study using synthetic and consented redacted examples.
2. Internal candidate nomination with no external export.
3. Feature-flagged review queue and JSONL-only export for a quality cohort.
4. Validate label quality and reviewer agreement against an approved threshold.
5. Enable a verified external adapter destination by destination, read-only result linking first.

Rollback disables nomination/export adapters, preserves authorized dataset versions and manifests, and allows download/deletion of application-owned staging. It never deletes an external dataset without a separate verified, authorized operation.

## Executable acceptance scenarios

1. Given a rejected tool action and authorized corrected action, when nominated, then the preview shows exact provenance, redactions, label author, and destination before review.
2. Given a sensitive task is excluded, when candidate generation and export run, then no content, identifier, or attachment from it appears in staging, artifacts, or logs.
3. Given an approved record needs a label correction, when edited, then a new revision is created and the prior label/audit remain inspectable.
4. Given no verified dataset-write capability, when a batch is approved, then a schema-versioned JSONL and provenance manifest are produced with no network mutation.
5. Given an export retries after timeout, when the destination reconciles, then at most one logical dataset version/record set is represented.
6. Given an unauthorized viewer opens an agent’s evaluation area, then restricted dataset names, counts, content, and result existence are not disclosed.
7. Given a mobile reviewer loses connectivity, when they reconnect, then stale records refresh before their decision controls re-enable.

## Explicit discovery gates

- **External contract:** verify current LangSmith dataset/example, permission, rate-limit, trace-link, experiment, update, and delete behavior against pinned packages/live contracts.
- **Signal policy:** approve eligible signals, consent, redaction, retention, deletion, project exclusion, and destination ownership.
- **Label quality:** define taxonomy, reviewer guidance, disagreement resolution, quality threshold, and representative sampling audit.
- **Snapshot schema:** prove immutable, replayable, minimally sufficient examples across coding, research, and writing journeys.
- **Integration safety:** validate idempotency, partial export, reconciliation, and downstream deletion truthfulness.
- **Product research:** confirm users understand what becomes evaluation data and can preview/correct it on supported surfaces.

This brief remains discovery-gated until the external adapter conformance and governance/label-quality decisions are accepted; JSONL fallback does not make the live integration implementation-ready.
