---
feature_id: DW-FUT-301
title: Opt-in temporal organizational graph
release: v3
status: proposed-brief
decision_status: discovery-gated
owners: [knowledge, data, security]
surfaces: [knowledge, agent-tools, administration]
runtime_scopes: [classic, mda, oss]
source_refs: [SRC-DW]
dependencies: [DW-FUT-102, DW-FUT-207]
last_reviewed: 2026-07-23
---

# Opt-in temporal organizational graph

> This v3 brief is discovery-gated research, not an implementation plan. Graphiti compatibility, ontology, graph database, extraction model, tenancy, temporal semantics, query interface, deployment, and deletion behavior are all unselected until the gates below close.

## User outcome

Organizations with a demonstrated need for historical relationship reasoning can opt into a user-owned graph, inspect every relationship and its supporting source/version, compare what was believed over time, and correct, supersede, retract, export, or delete it without replacing source documents, governed metrics, or reviewed memory.

## Evidence and confidence

- `SRC-DW` identifies a temporal organizational graph as a v3 possibility after reviewed memory and structured knowledge. Confidence: low-to-medium for product value and low for technical shape.
- `DW-FUT-102` and `DW-FUT-207` provide prerequisite reviewed claims, source permission, provenance, conflict, and deletion concepts. Confidence: dependent on their discovery and release evidence.
- Graphiti-compatible tooling may offer temporal graph patterns, but maturity, licensing, correctness, tenant isolation, and deletion are unverified. Confidence: unknown; no compatibility assertion is made.
- Temporal relationship inference is unusually sensitive and can amplify incorrect or private associations. Confidence: high that explicit opt-in, review, access, and evaluation are required.

## Scope, ownership, and non-goals

Knowledge owns ontology governance, candidate extraction/review, fact status, provenance, and user correction. Data owns temporal representation, query semantics, indexing, consistency, backup/export/deletion, and evaluation tooling. Security owns source-permission propagation, sensitive categories, inference controls, tenant isolation, threat model, and privacy review.

In scope for a first research profile:

- A deliberately small ontology hypothesis: Person, Team, Project, System, Decision, Policy, and Source.
- Proposed nodes/edges with valid-time, transaction-time, source provenance, confidence classification, access policy, reviewer status, and revision lineage.
- Review before publication; current/historical inspection; conflict, correction, supersession, retraction, expiry, source revocation, export, and complete tenant-store deletion.
- A constrained, read-only agent/query tool over authorized accepted graph facts if later verified.

Non-goals:

- Replacing canonical sources, reviewed knowledge, metrics, identity directory, authorization service, project tracker, or general-purpose data warehouse.
- Inferring sensitive relationships by default, scoring people, hidden employee monitoring, autonomous organizational decisions, or presenting confidence as truth.
- Universal ontology, unrestricted natural-language graph query, graph writes by runtime agents, or public Graphiti/MCP claims before conformance.

## Primary journeys

1. **Opt in and scope:** an authorized organization admin reviews purpose, source classes, sensitive categories, ontology, retention, user rights, deployment ownership, and irreversible risks before enabling a sandboxed pilot.
2. **Propose and review:** approved source revisions generate candidate nodes/edges; reviewer compares source excerpts, interval, confidence, access, and conflict, then accepts, edits, rejects, or defers.
3. **Inspect history:** user opens a fact, sees every support/revision/reviewer, compares valid-time versus recorded-time, and asks current or as-of questions with explicit time basis.
4. **Correct/retract:** authorized reviewer supersedes an incorrect relationship or retracts it; historical audit remains while current query behavior changes.
5. **Revoke/export/delete:** a source or subject request triggers dependency analysis and removal/re-evaluation; organization can export a documented portable representation and completely delete its owned graph store.

## Complete state matrix

| State/condition | Expected experience |
| --- | --- |
| Loading | Load graph query, fact detail, provenance, permission, and temporal basis separately; no relationship renders before authorization/provenance resolve. |
| Empty | Explain no accepted graph facts/source coverage and current opt-in scope; do not infer relationships from absence. |
| Proposed | Show node/edge type, endpoints, interval, source revision/excerpt, extraction rationale, confidence classification, access, and review actions. |
| Accepted/current | Show reviewed status, reviewer, valid/transaction time, supporting sources, last re-evaluated time, and authorized queries using it. |
| Disputed | Preserve competing facts and review history; do not select a “current truth” without accepted resolution policy. |
| Superseded/retracted/expired | Exclude from default current answers, retain authorized historical lineage, and explain why/when status changed. |
| Conflicting intervals | Flag overlap/gap and require review; temporal reducer must not silently coerce it. |
| Source revoked/stale | Remove inaccessible support from results immediately, mark dependent facts unsupported/pending re-evaluation, and apply deletion policy. |
| Querying | Display requested time basis, scope, filters, authorization, and progress; results remain provisional until provenance completes. |
| Error | Distinguish source, extraction, graph write/read, temporal, permission, query, export, and deletion failure; fail closed and preserve last accepted state. |
| Offline | Allow only policy-approved cached fact detail with timestamp and source-access caveat; no review, query execution, export, or graph mutation. |
| Permission denied | Return no node/edge/source/subject existence signal; redact connected facts that could reveal a restricted endpoint. |
| Reconnecting | Revalidate identity, policy, source access, fact version, and time basis before enabling action or rendering cached relationships. |
| Mobile | Provide fact/provenance/history cards and focused review; dense graph visualization is optional and must have an accessible list/timeline equivalent. |
| Exporting/deleting | Show exact tenant/scope, progress, receipts, failure/retry, residual/backup policy, and independent verification; block new writes during final deletion as designed. |

## Proposed interfaces (non-binding)

Illustrative domain concepts are `GraphTenant`, `OntologyVersion`, `EntityRef`, `TemporalFact`, `FactSupport`, `FactRevision`, `FactReview`, `GraphQuery`, `GraphResult`, `SourceRevocationJob`, and `GraphExport`. A temporal fact carries application ID, typed endpoints, predicate, valid interval, transaction interval/history, support set, confidence classification, access policy reference, status, reviewer lineage, and tenant.

The query hypothesis requires explicit `asOfValidTime` and/or `asKnownAtTime`, bounded types/depth/results, and complete provenance in every result. This is not a chosen API, Graphiti schema, graph database model, or MCP contract. Writes occur only through the reviewed application pipeline; runtime agents receive a constrained read tool if verified.

## Runtime capability and fallback

- The graph is application/organization-owned and source-neutral; classic/MDA/OSS labels do not imply graph support or routes.
- An agent tool advertises graph query only when tenant, source permission, temporal query, provenance, and revocation conformance pass.
- Unsupported temporal queries fall back to reviewed knowledge/source search and explain the limitation; never answer from an approximate graph silently.
- If value, privacy, correctness, operations, export, or deletion gates fail, retain reviewed markdown/OKF-style knowledge and governed metrics with no graph.

## Persistence and security

Persist accepted graph facts and necessary proposals/support under tenant-specific policy, with ontology/reviewer/version/audit and source references. Minimize copied source excerpts and sensitive person data. Encrypt stores/backups/exports, isolate keys/tenants, and define backup expiry plus deletion verification. Never store provider credentials, hidden reasoning, or unauthorized source content in graph properties/logs.

Authorize at source, subject, node, edge, path traversal, query, aggregate, result, export, and agent-tool layers. Prevent inference through counts, timing, neighborhood shape, error differences, embeddings, caches, and historical snapshots. Sensitive relationship types are disabled by default and may remain prohibited. Threat model includes poisoned extraction, ontology abuse, linkage/re-identification, cross-source permission conflict, recursive query cost, prompt injection, and cross-tenant leakage.

## Responsive and accessible behavior

The canonical experience is an accessible fact list, provenance detail, and timeline—not a visual graph alone. Any graph visualization has keyboard navigation, focus/selection equivalence, zoom-independent text alternative, non-color encoding, screen-reader summary, and reduced-motion mode. Mobile prioritizes current/historical fact cards, conflicts, and review actions; desktop can add comparative timeline/graph views.

## Metrics and guardrails

- Extraction precision, reviewer accept/edit/reject, contradiction detection, interval correction, and inter-reviewer agreement by relation type.
- Unsupported-current-fact rate, source/citation completeness, stale/revocation/deletion propagation, and temporal-query correctness.
- Reviewer burden and validated unique value over ordinary reviewed search/knowledge.
- Sensitive relationship, unauthorized path/result, cross-tenant existence, deletion residual, and source-revocation leak; targets zero.
- Guardrails: no automatic publication, no people scoring, no sensitive inference by default, no unsupported current fact, no result without authorized provenance.

## Dependencies

- `DW-FUT-102` must establish reviewed memory synthesis, candidate/conflict/version/rollback, and source eligibility.
- `DW-FUT-207` must establish approved knowledge/structured sources, permission propagation, citations, staleness, revocation, and deletion.
- `DW-FND-003` and `DW-FND-005` transitively supply tenant/actor, durable audit, credentials, security, and deletion foundations.
- v3 research cannot weaken or bypass the authority of source documents and governed metrics.

## Rollout and rollback

1. Problem/value study comparing temporal graph tasks with reviewed search/knowledge; no implementation commitment.
2. Synthetic ontology/temporal correctness harness and red-team privacy evaluation.
3. Offline extraction against a consented, non-sensitive corpus with human review; no agent query.
4. Isolated single-tenant sandbox with export/delete drills and read-only administrator queries.
5. Narrow opt-in pilot for approved relation types/sources after legal/security review; agent tool remains separately flagged.
6. Expand ontology/source/query only through independent gates and measured value.

Rollback disables extraction, publication, user query, and agent tool independently; returns users to reviewed knowledge/search; preserves authorized audit/export during a defined wind-down; and supports complete tenant-store deletion. Retracting a feature never silently leaves an operational shadow graph.

## Executable acceptance scenarios

1. Given a decision owner changes from person A to B, when querying current, valid-as-of, and known-as-of times, then each answer is temporally correct and cites the accepted source revisions.
2. Given two conflicting sources with overlapping intervals, when candidates are generated, then both remain disputed until review and neither is silently selected as current.
3. Given a user lacks access to one endpoint/source, when querying direct, aggregate, or neighboring relationships, then no fact or existence signal reveals it.
4. Given a source is revoked, when current/historical queries and caches run, then inaccessible support disappears and dependent facts are reclassified within the accepted target.
5. Given a reviewer retracts a false fact, when a runtime agent queries current state, then it is absent; authorized audit still shows why and when it changed.
6. Given an organization exports then requests deletion, when the deletion process completes, then active store, indexes, caches, queued jobs, and policy-defined backups are verified and a receipt identifies any legally retained audit without content.
7. Given a malicious recursive/path query, when submitted, then authorization and cost/depth/result bounds reject it before resource exhaustion or leakage.
8. Given graph visualization is unavailable or inaccessible, when a mobile screen-reader user asks a historical question, then the list/timeline experience supplies equivalent facts, time basis, conflicts, and provenance.

## Explicit discovery gates

- **Value and ethics:** prove temporal relationship questions materially outperform reviewed knowledge; approve prohibited/allowed uses, subject rights, consent, and people-data policy.
- **Technology:** evaluate current Graphiti and alternatives for maturity, license, maintenance, temporal semantics, tenant isolation, authorization hooks, export, backup, and deletion without assuming compatibility.
- **Ontology:** define governance, stable identifiers, merge/split, relation types, interval semantics, confidence/review, evolution/migration, and sensitive-category defaults.
- **Correctness:** build temporal/property-based tests and representative extraction/query benchmarks with accepted thresholds by relation type.
- **Permission/deletion:** prove source-to-node/edge/path policy propagation, revocation, subject deletion, derived inference cleanup, caches/indexes/backups, and independent verification.
- **Security/privacy:** complete linkage/inference, poisoning, prompt injection, graph traversal, enumeration, cross-tenant, cost-exhaustion, export, and agent-tool threat model.
- **Operations/ownership:** prove user-owned deployment, capacity, backup/restore, migration, observability, incident response, export portability, and sunset/deletion.
- **UX/accessibility:** validate provenance, temporal-basis comprehension, conflict review, correction, and equivalent non-visual/mobile experience.

The graph remains a v3 research option until all gates close. A successful prototype, extraction demo, or Graphiti integration alone cannot make it implementation-ready.
