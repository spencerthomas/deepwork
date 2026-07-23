# Independent review record

Review date: 2026-07-23

Reviewed commit: `73ecb1576f56f64ee07265dbabb936e155310834`

## Review roles and scope

The research author integrated the packet. Independent reviewers were assigned
three non-overlapping contract groups:

| Independent role | Scope | Gate verdict |
|---|---|---|
| Source/config/deploy contract reviewer | `SPIKE-SOURCE-001`, `SPIKE-CONFIG-001`, `SPIKE-DEPLOY-001` | Documentary and pinned package-source evidence only; generic settings and app-owned deploy claims rejected; live-dependent operations blocked |
| Compose/threads/HITL contract reviewer | `SPIKE-COMPOSE-001`, `SPIKE-THREADS-001`, `SPIKE-HITL-001` | Candidate request/response shapes retained with contradictions; ordered HITL and live mutation behavior blocked |
| Stream/lifecycle contract reviewer | `SPIKE-STREAM-001`, `SPIKE-STREAM-002`, `SPIKE-STREAM-003`, `SPIKE-CANCEL-001`, `SPIKE-CHECKPOINT-001` | Protocols kept separate; exact replay, queue, cancel, and checkpoint behavior blocked |

The compose/threads/HITL reviewer also performed an independent retained-artifact
audit after the first integrated draft. That audit was conditional rather than
an acceptance: it identified three actionable evidence-record defects. The
author corrected them before commit `73ecb1576f56f64ee07265dbabb936e155310834`
and reran the packet validation.

## Corrections resulting from independent review

1. **Evidence classification**
   - Removed `installed` response labels and unqualified installed package
     versions because public distributions were not installed.
   - Reclassified those shapes as pinned candidate package-source evidence.
   - Added matrix validation that rejects installed-contract claims while
     `installed_public_distributions` is empty.

2. **Ordered HITL fidelity**
   - Removed invented action IDs from `action_requests`, `review_configs`, and
     `decisions`.
   - Validated positional one-to-one alignment, exact snake_case key shapes,
     allowed decision types, repeated tool names, and decision-specific payloads.
   - Corrected the implementation citation to pinned `SRC-LCPY`; Deep Agents
     consumes this contract but does not own the cited implementation file.

3. **Protocol-v3 classification and fixture**
   - Replaced the stale protocol-v2 label with protocol v3 for
     `/threads/{thread_id}/stream/events`.
   - Kept protocol-v3 body cursor `since` and durable `event_id` deduplication
     separate from legacy `Last-Event-ID` joins.
   - Corrected the synthetic event envelope to retain `type`, `seq`, `method`,
     `params.namespace`, `params.timestamp`, `params.data`, and `event_id`.

4. **Assistant-search fixture**
   - Replaced an invalid `items` wrapper with the generated OpenAPI bare-array
     response.
   - Added an executable fixture-shape assertion and refreshed the fixture hash.

5. **Environment-bound runner qualification**
   - Removed the claim that the current probe lock is isolated/reproducible.
   - Recorded that the dependency-free probe delegates to the workspace's exact
     `pytest 9.0.2`.
   - Kept an isolated public-distribution/test-runner lock as an explicit blocker
     pending approved package-index access.

6. **Additional contract corrections**
   - Qualified UUID-formatted generated identifiers and required response fields
     in synthetic fixtures.
   - Distinguished missing-thread `if_not_exists` behavior from run mutation
     idempotency.
   - Recorded thread search as limit/offset pagination without a cursor or
     stable-snapshot promise.
   - Rejected the candidate Python `subagents` projection as distinct from
     `subgraphs` while the pinned implementation aliases them.

## Review verdict and authority boundary

The independent contract reviews support the packet as a bounded research
handoff after the listed corrections. Their unanimous gate verdict is that every
row remains `blocked-live-evidence`; no provider adapter or product capability is
accepted or enabled.

This review is not the formal runtime-contract, security, and product
adjudication named in the ExecPlan. Those reviewers must still independently
accept or reject each row after installed public-distribution and sanitized live
classic-sandbox evidence exists. The author has not self-accepted a row.
