---
feature_id: DW-FUT-102
title: Memory synthesis and review loop
release: v1.x
status: proposed-brief
decision_status: discovery-gated
owners: [agent, api, knowledge]
surfaces: [activity, memory-review, agent-detail]
runtime_scopes: [classic, mda]
source_refs: [SRC-DW, SRC-LC]
dependencies: [DW-OPS-003, DW-AGENT-005]
last_reviewed: 2026-07-23
---

# Memory synthesis and review loop

> This v1.x brief is discovery-gated. It does not assert that Context Hub exposes a public mutation, webhook, conflict, or version API. Approved memory remains the only agent-readable organizational memory until every external and governance gate is verified.

## User outcome

Teams can turn recurring task evidence into proposed organizational memory, review each claim with provenance, and safely accept, correct, reject, defer, or roll back it without allowing generated text to become truth automatically.

## Evidence and confidence

- `SRC-DW` establishes organizational intelligence Layers 0–1 and a human-reviewed memory direction. Confidence: medium for the review workflow, low for any later external knowledge-system integration.
- `SRC-LC` provides runtime/context concepts, but ownership and public write semantics for Context Hub are unverified in this package. Confidence: unknown until a pinned-package/live-contract spike.
- Existing task, trace, approval, artifact, and audit identities can support application-owned candidate provenance. Confidence: medium, dependent on v1 persistence and retention decisions.

## Scope, ownership, and non-goals

The agent owner owns bounded extraction and candidate rationale. The API owner owns eligibility policy, immutable provenance, concurrency, merge/rollback workflow, and redaction. The knowledge owner owns information architecture, reviewer policy, quality evaluation, and source lifecycle.

In scope:

- Policy-bounded consolidation from eligible completed work.
- Candidate facts, decisions, preferences, contradictions, and staleness notices.
- Source links, confidence rationale, proposed target/diff, reviewer actions, conflict rebase, atomic publication, and rollback.
- Rejection/edit feedback as governed synthesis guidance, not automatic training data.

Non-goals:

- Autonomous memory writes, bulk acceptance without review, personal surveillance, hidden inference profiles, or replacing source systems.
- A claim that Context Hub is application-owned or supports a specific public write route.
- Broad knowledge ingestion, semantic search, or temporal graph behavior owned by `DW-FUT-207` and `DW-FUT-301`.

## Primary journeys

1. **Run synthesis:** an authorized reviewer selects an eligible scope and policy; a bounded job extracts candidates with source evidence and redaction preview.
2. **Review candidate:** the reviewer compares proposed text/diff with current approved memory and source excerpts, then accepts, edits, rejects, or defers individually.
3. **Resolve conflict:** if approved memory changes, the candidate becomes conflicted; the system rebases the proposal and requires fresh review.
4. **Publish and consume:** accepted candidates merge atomically into a version; runtime agents see the new memory only after publication succeeds.
5. **Correct or revoke:** an administrator rolls back a revision or revokes a source; downstream candidates and approved claims are re-evaluated under the retention policy.

## Complete state matrix

| State/condition | Expected experience |
| --- | --- |
| Loading | Show separate skeletons for candidate queue, approved version, and evidence; do not display an empty queue prematurely. |
| Empty | Explain eligibility and review policy, show the last completed synthesis run, and offer a scoped run only to authorized users. |
| Extracting | Show bounded scope, elapsed status, cancellation availability, and counts without exposing candidate content to unauthorized actors. |
| Proposed | Display source links, rationale, confidence classification, target, proposed diff, and accept/edit/reject/defer actions. |
| Conflicted | Disable acceptance, show current-versus-base change, and require rebase plus new review. |
| Accepted | Record the decision but distinguish “accepted for publication” from “merged.” |
| Rejected/deferred/expired | Preserve rationale and provenance; rejected content is never runtime-visible, deferred content remains reviewable, expired content requires regeneration. |
| Merged | Show approved version, reviewer, source set, merge timestamp, prior version, and rollback action where authorized. |
| Error | Keep last approved memory unchanged, identify extraction versus publication failure, and offer idempotent retry. |
| Offline | Allow read-only cached approved memory and queue metadata with timestamp; no candidate decision or merge is queued offline. |
| Permission denied | Reveal neither restricted source excerpts nor candidate existence; explain the required role generically. |
| Reconnecting | Re-fetch candidate and approved-memory versions before enabling review actions. |
| Stale/source revoked | Mark dependent candidate or approved claim, block publication, and initiate policy-defined re-evaluation; never silently retain “current” status. |
| Mobile | Use a one-candidate review flow with source/diff tabs, sticky decision controls, and explicit warning before accepting edited content. |

## Proposed interfaces (non-binding)

Illustrative application entities are `SynthesisRun`, `MemoryCandidate`, `EvidenceRef`, `MemoryRevision`, `ReviewDecision`, and `SourceEligibilityPolicy`. Candidate records include base revision, proposed patch, classification, provenance, redaction status, and version. Operations may include start/cancel synthesis, list/read candidates, decide candidate, rebase, publish accepted batch, and roll back revision.

These are application-domain proposals, not Context Hub API claims. Endpoint names, patch format, storage target, and publication adapter remain undecided. Mutations require authorization, expected version, idempotency key, and audit reason.

## Runtime capability and fallback

- A capability manifest must distinguish read context, publish reviewed memory, version conflict, source deletion, and webhook/reconciliation support.
- If a verified external memory target supports safe versioned mutation, an adapter may publish after application review.
- If any write or conflict contract is unverified, generate a reviewed digest/diff artifact for manual export and keep agents on the last approved memory.
- A synthesis failure never blocks task execution; it degrades to no new memory and a visible operational event.

## Persistence and security

Persist eligibility snapshots, candidate content where policy permits, evidence references, redaction decisions, reviewer actions, revision lineage, publication receipts, and rollback events. Store the minimum source excerpt needed for review; prefer references plus immutable hashes where durable retrieval is authorized. Apply project, actor, source classification, retention, legal hold, and deletion policies before extraction.

Runtime agents can read only published memory authorized for their source/workspace context. Secrets, raw credentials, hidden chain-of-thought, and excluded project content are never synthesis inputs. Logs use IDs and counts, not candidate content. Source revocation and tenant deletion have tested propagation paths.

## Responsive and accessible behavior

Desktop supports side-by-side source/current/proposed comparison; narrow screens serialize the same panels without hiding provenance. Accessibility requirements include semantic added/removed text, explicit labels and focus order, text-plus-icon status, complete keyboard review, reduced-motion queue transitions, and long-source expansion that never traps scroll.

## Metrics and guardrails

- Candidate precision from reviewer accept-without-edit, edit, reject, and contradiction rates.
- Median review time, candidates per review session, defer/expiry rate, and reviewer burden.
- Percentage of merged claims with accessible provenance and complete review audit; target 100%.
- Publication conflict, rollback, source-revocation propagation, and sensitive-content escape rates; escape target zero.
- Guardrails: no unreviewed runtime visibility, no auto-merge, no extraction from excluded scope, and no unsupported external mutation.

## Dependencies

- `DW-OPS-003` for organizational-intelligence Layers 0–1, evidence boundaries, and review ownership.
- `DW-AGENT-005` for approved-memory/runtime configuration boundaries.
- `DW-FND-003` and `DW-FND-005` transitively supply durable policy, tenant/actor identity, audit, and secure references.

## Rollout and rollback

1. Offline evaluation on a consented, redacted trace corpus with no product UI.
2. Internal read-only candidate digest; all publication remains manual.
3. Feature-flagged application review queue for one source class and reviewer cohort.
4. Manual export of approved revisions; measure quality and burden.
5. Enable a publication adapter only after its version/conflict/deletion conformance suite passes.

Rollback stops synthesis and publication, preserves authorized audit/revision history, returns agents to the last known approved memory version, and exports accepted-but-unpublished candidates. It never deletes the source task history or rewrites prior review decisions.

## Executable acceptance scenarios

1. Given an eligible completed task, when synthesis runs, then each candidate includes policy scope, source revision, rationale, redaction status, and proposed diff.
2. Given a hallucinated candidate, when a reviewer rejects it, then it never becomes runtime-visible and the rejection rationale remains auditable.
3. Given approved memory changed after candidate generation, when a reviewer opens the candidate, then acceptance is blocked until rebase and re-review.
4. Given a sensitive project exclusion, when synthesis runs and logs are inspected, then neither candidate, excerpt, identifier, nor log content reveals that project.
5. Given a merged revision, when an authorized user rolls it back, then agents receive the prior approved version and the complete lineage remains intact.
6. Given no verified publication capability, when candidates are accepted, then the app produces a reviewed export and performs no external write.
7. Given a source is revoked while offline, when the client reconnects, then affected content is marked stale before any review mutation is enabled.

## Explicit discovery gates

- **External contract:** verify current Context Hub ownership, authorization, read/write, version, webhook, conflict, and deletion behavior against pinned packages and live contracts; otherwise retain manual export.
- **Governance:** approve eligibility, classification, retention, legal hold, source revocation, reviewer role, and rollback policy.
- **Quality:** measure extraction precision, contradiction detection, citation completeness, and reviewer burden on a representative consented corpus.
- **Patch model:** choose and test a reversible, format-preserving diff/merge representation and concurrency strategy.
- **Runtime consumption:** prove agents receive only the authorized published revision and can be reverted deterministically.
- **Product research:** validate provenance comprehension and mobile diff review before enabling consequential decisions.

This brief remains non-ready until the external contract and governance gates are accepted and measured quality meets an explicitly approved threshold.
