---
feature_id: DW-FUT-207
title: Organizational knowledge base and structured data plane
release: v2
status: proposed-brief
decision_status: discovery-gated
owners: [knowledge, data, security]
surfaces: [knowledge-review, task-composer, agent-detail]
runtime_scopes: [classic, mda]
source_refs: [SRC-DW]
dependencies: [DW-OPS-003, DW-FUT-102]
last_reviewed: 2026-07-23
---

# Organizational knowledge base and structured data plane

> This v2 brief is discovery-gated and contains two independently releasable tracks: reviewed source-backed knowledge and governed structured-data access. OKF/openwiki-style generation, dbt Semantic Layer, connectors, databases, and MCP are hypotheses—not selected vendors or verified contracts.

## User outcome

Authorized users and agents can answer organization-specific knowledge and metric questions with source/revision/query provenance, understand conflicts and staleness, and require review before consequential ingestion or data execution.

## Evidence and confidence

- `SRC-DW` defines organizational-intelligence progression from reviewed memory toward knowledge and structured data. Confidence: medium for direction, low for specific technologies.
- `DW-OPS-003` and `DW-FUT-102` establish provenance/review boundaries rather than automatic truth. Confidence: medium, pending their delivery/discovery.
- Connector permission inheritance, retrieval quality, semantic-layer contracts, database policies, and secure execution are unverified. Confidence: unknown provider by provider.

## Scope, ownership, and non-goals

Knowledge owns source ingestion policy, generated page/search/review experience, provenance, staleness, and retrieval evaluation. Data owns semantic/query models, checking, bounded execution, result provenance, and cost controls. Security owns connector/database threat models, authorization propagation, credentials, egress, redaction, retention, and deletion.

Knowledge track scope:

- Approved source connections, incremental source revision ingestion, candidate page/index generation, review, browse/search, citation, conflict, staleness, revocation, and deletion.

Structured-data track scope:

- Governed semantic metrics where available; read-only schema discovery, query proposal/check/approval, bounded execution, interpretation, and export with provenance.

Non-goals:

- Replacing source documents/warehouses, indexing every organizational system by default, unrestricted SQL, raw write/admin credentials, automatic claim publication, or claiming permission inheritance without verification.
- Temporal relationship graph behavior, owned by `DW-FUT-301`.

## Primary journeys

1. **Connect and scope knowledge source:** admin reviews provider permissions, locations, classifications, retention, and deletion; test access proves identity propagation before ingestion.
2. **Generate and review:** incremental job proposes pages/chunks/claims with source revision/citations; reviewer accepts, edits, rejects, or flags conflict.
3. **Ask knowledge question:** authorized user sees answer with citations, coverage, staleness/conflict, and source access checks at retrieval/render.
4. **Ask metric question:** agent resolves an approved semantic definition or proposes bounded read-only query, displays target/source/cost/risk, obtains approval if required, executes, and cites result/query revision.
5. **Revoke/correct:** source permission/revision/deletion or metric-definition change marks derived content stale and propagates access/removal under policy.

## Complete state matrix

| State/condition | Expected experience |
| --- | --- |
| Loading | Load source access, index/review, answer, and query execution states separately; never show uncited answer while provenance is pending. |
| Empty | Explain no approved sources/pages/metrics and route authorized users to scoped connection; do not synthesize an answer from absence. |
| Ingesting/indexing | Show source/revision scope, counts, cancellation, errors, and pending review; content is not agent-readable before policy allows. |
| Proposed/review | Show source/current/proposed comparison, citations, classification, conflicts, and granular decision. |
| Approved/current | Display approved version, source coverage, last checked time, access scope, and citations. |
| Conflicted/stale | Label answer/page/result, identify changed/revoked support, avoid definitive current claim, and route to review/requery. |
| Query proposed | Show semantic metric or SQL, parameters, data source, expected scan/cost/limits, policy, and approval requirement. |
| Query running | Show bounded execution, timeout/cancel status, and no partial interpretation as final. |
| Error | Distinguish connector/auth, ingestion, retrieval, citation, policy, query-check, execution, and export errors; preserve last approved state. |
| Offline | Allow authorized cached approved pages/results with clear timestamp/policy; no ingestion, source mutation, query approval, or execution. |
| Permission denied | Return no source/page/table/row/result existence signal outside authorization; clear revoked cache. |
| Reconnecting | Refresh source permission/revision, knowledge version, metric definition, query policy, and result access before action. |
| Mobile | Support cited answer, page review, and query approval summary; dense SQL/result exploration provides accessible desktop handoff/export. |

## Proposed interfaces (non-binding)

Illustrative knowledge concepts are `KnowledgeSource`, `SourceRevision`, `IngestionRun`, `KnowledgeCandidate`, `KnowledgeRevision`, `Citation`, and `RetrievalResult`. Structured concepts are `DataSource`, `SemanticDefinitionRef`, `QueryProposal`, `QueryPolicyDecision`, `ExecutionReceipt`, and `ResultArtifact`.

Provider connectors, OKF/openwiki representation, dbt APIs, database drivers, and MCP surfaces are not specified. All adapters declare verified capabilities such as permission sync, incremental revision, delete signal, semantic resolve, query check, cancellation, and result expiry. Query execution uses typed policy and immutable approved query hash; interpretation cannot mutate it.

## Runtime capability and fallback

- Knowledge/source and data capabilities are detected independently; runtime tier labels do not imply connector routes.
- If permission inheritance or revocation cannot be proven, that source is not persistently indexed.
- If semantic layer is unavailable, a reviewed read-only query path may be considered only after database gates; otherwise no structured execution.
- Default fallback is per-task remote read-only connector/MCP with no persistent index, plus manual source artifacts and explicit provenance.

## Persistence and security

Persist minimum authorized source metadata, revisions/hashes, reviewed derived content, citations, policy decisions, access lineage, query proposals/approvals, bounded results, deletion receipts, and audit. Credentials remain referenced in the broker. Separate raw source cache, approved knowledge, query result, and audit retention.

Enforce source permission at ingest, retrieval, answer, review, export, and agent-tool time. Defend against prompt injection in source content, poisoned documents, malicious schemas, SQL injection, policy bypass, row/column leakage, timing/existence inference, cost abuse, SSRF/egress, result exfiltration, and cross-tenant caches. Queries are read-only, allowlisted/bounded, timed, row/byte limited, and never receive write/admin credentials.

## Responsive and accessible behavior

Citation order and source status are semantic and keyboard accessible. Desktop can compare source/current/proposed and inspect query/results; narrow screens serialize panels with persistent source/query identity. Tables reflow or provide accessible summaries/downloads, code is labelled/wrapped/scrollable, conflicts and policy are not color-only, and charts have tabular/text alternatives.

## Metrics and guardrails

- Citation precision/recall/completeness, answer support, reviewer edit/reject, conflict/stale detection, and permission/deletion propagation.
- Semantic resolution accuracy, query approval/rewrite/reject, execution success/timeout/cost, result reproducibility, and user correction.
- Unauthorized retrieval/row, unsupported citation, unsafe query execution, source-revocation leak, and credential exposure; targets zero.
- Reviewer burden, freshness SLA by source class, and value by validated user journey.
- Guardrails: no answer presented as grounded without accessible support; no query executes outside approved policy/hash.

## Dependencies

- `DW-OPS-003` provides Layers 0–1 boundaries, source evidence, and organizational-intelligence ownership.
- `DW-FUT-102` provides reviewed synthesis, conflict, version, and rollback concepts.
- `DW-FND-003`, `DW-FND-005`, and `DW-AGENT-005` transitively supply tenant/actor, credentials, audit, and runtime tool/memory boundaries.
- `DW-FUT-301` consumes only approved outputs later and cannot weaken this plan’s source authority.

## Rollout and rollback

Run knowledge and structured-data tracks independently:

1. Synthetic/consented corpus and warehouse evaluation with no production connectors.
2. One read-only source or semantic catalog in internal review-only mode.
3. Feature-flagged approved knowledge retrieval or query proposal with no execution.
4. Limited retrieval and separately limited read-only execution after security/quality thresholds.
5. Add providers/datasets one at a time after their own conformance and permission-deletion tests.

Rollback disables ingestion/retrieval/query execution independently, marks derived content unavailable/stale, preserves authorized audit/exports, and revokes credentials. Deletion/revocation cleanup continues even while features are disabled.

## Executable acceptance scenarios

1. Given an approved document source, when a page is generated/reviewed, then every material claim links to authorized source revision and no rejected claim is agent-readable.
2. Given source permission is revoked, when retrieval/cache/export are attempted, then content and existence signals disappear within the accepted propagation target and audit records the cleanup.
3. Given conflicting sources, when asked a question, then the system presents conflict/provenance rather than choosing an unsupported current fact.
4. Given a governed metric question, when resolved, then definition/version/parameters/result time are shown and the answer is reproducible under retention.
5. Given unsafe or unbounded SQL, when proposed, then checking/policy blocks execution before database access and explains a safe correction.
6. Given a query is changed after approval, when execution is requested, then the approved hash mismatch requires fresh review.
7. Given an unverified connector permission model, when persistent indexing is requested, then it is refused and per-task/manual fallback is offered.
8. Given mobile screen-reader use, when reviewing an answer/query, then citations, staleness, policy, and next action are operable and understandable.

## Explicit discovery gates

- **Provider contract per source:** verify auth, scopes, permission inheritance, revisions/webhooks, rate limits, content types, deletion, retention, and enterprise constraints.
- **Knowledge quality:** establish representative corpus and thresholds for extraction, retrieval, citation, conflict, freshness, and reviewer burden.
- **Structured contract:** evaluate current semantic-layer options and read-only database adapters without locking dbt or MCP prematurely.
- **Query safety:** approve parse/check/policy, read-only enforcement, row/column security, limits/cost, cancellation, results, export, and exfiltration controls.
- **Data governance:** approve classification, residency, retention, legal hold, source revocation, derived-content deletion, and user correction.
- **Product/accessibility:** validate separate knowledge and metric journeys, review burden, citation comprehension, and mobile handoffs.

Neither track becomes implementation-ready because the other passes. Each provider and data source remains disabled until its own gates close.
