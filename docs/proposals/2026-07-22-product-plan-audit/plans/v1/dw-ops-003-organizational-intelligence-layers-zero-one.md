---
feature_id: DW-OPS-003
title: Organizational intelligence layers 0 and 1
release: v1
status: proposed
decision_status: blocked-on-spikes
owners: [agent, api, product]
surfaces: [onboarding, agent-detail, activity]
runtime_scopes: [classic, mda]
source_refs: [SRC-DW, SRC-LC]
dependencies: [DW-AGENT-005, DW-OPS-001, DW-OPS-002]
contract_gates: [SPIKE-CONTEXT-001, SPIKE-TRACE-001]
last_reviewed: 2026-07-23
---

# Organizational intelligence layers 0 and 1

## User outcome

A workspace can establish a reviewed source of operating context and receive periodic, coverage-qualified summaries of agent activity. Agents can read only the approved context they are authorized to use and may submit proposals, but they can never silently rewrite authoritative organization memory.

## Evidence and confidence

| Claim | Evidence | Classification | Planning consequence |
|---|---|---|---|
| The vision proposes organizational intelligence layers, reviewed memory, analyst digests, and later structured/temporal knowledge. | `SRC-DW` | Product intent | v1 is limited to Layers 0–1; structured knowledge and graph inference remain future plans. |
| The prototype exposes a Memory section and simulated organizational context. | `SRC-FE`, `FE-C11` | Interaction evidence only | Replace direct-looking edits with scoped read/proposal/review states. |
| Deep Agents/Context Hub and runtime memory have stable uniform ownership and write semantics. | `SRC-LC` | Gated, runtime-specific, or unknown | Preserve source ownership, capability-detect reads, and do not assume application writes. |
| Weekly analysis can query all global threads/traces across sources. | Prior internal assumption | Unsupported | Build from authorized application operational events and explicitly verified per-source evidence only. |
| Insights is available to every workspace. | Prior internal assumption | Gated/unknown | Use it only after capability proof; otherwise publish a qualified application-event digest. |

The memory storage format, Context Hub ownership, evidence-retention policy, analyst input contract, and review workflow need accepted evidence from `SPIKE-CONTEXT-001`, `SPIKE-TRACE-001`, and the named security decisions. This plan remains proposed and cannot be implementation-ready while those contracts are unverified.

## Scope, ownership, and non-goals

The FastAPI/PostgreSQL application service owns approved organization-memory versions, proposals, reviews, evidence references, authorization, merge concurrency, digest records, and audit. The separate Python agent package owns a constrained analyst workflow and portable read/proposal interfaces, not the write authority. The TypeScript SDK and Next.js/Tauri provide onboarding, reading, diff/review, and digest experiences. Source runtimes/Context Hub retain any source-native memory according to verified ownership.

Layer 0 scope:

- starter structure for company, teams, systems, glossary, policies, decisions, and source references;
- an onboarding interview that creates a proposed initial version, never immediate authoritative memory;
- immutable approved versions and explicit provenance, reviewer, effective date, sensitivity, and source links per entry;
- user memory separated by actor scope; organization memory mounted read-only to runtime agents;
- instructions/skills remain deployment-owned and are not silently merged with runtime or organization memory.

Layer 1 scope:

- scheduled or manually initiated analyst runs over authorized application operational events and only verified source evidence;
- a digest artifact with coverage window, included/excluded sources, confidence, evidence links, and redactions;
- optional memory changes staged as discrete proposals with semantic diffs;
- human accept/reject/edit per item, conflict rebase, merge to a new approved version, feedback, and audit.

Non-goals are direct agent writes, autonomous publication, global thread/trace search, copying full trace bodies, universal Context Hub mutation, secrets/raw prompts in digests, RBAC administration, eval/dataset learning loops (`DW-FUT-103`), full memory synthesis (`DW-FUT-102`), structured organizational knowledge (`DW-FUT-207`), or temporal graph inference (`DW-FUT-301`).

## Canonical concepts and ownership

- **Approved memory version:** immutable organization context that passed review and is the only organization version runtime agents may read.
- **Proposal:** a draft set of additions, edits, or removals against one base version; never visible as approved memory.
- **Evidence reference:** tenant-scoped pointer and safe excerpt metadata, authorized again at read time; it is not a copied unrestricted trace.
- **Digest:** immutable analysis artifact with a coverage statement and optional proposal links; it may exist without changing memory.
- **Review decision:** actor-attributed accept, reject, or edited-accept outcome on a proposal item.
- **Merge:** application-service-only operation producing a new immutable approved version after current-base and authorization checks.

Context Hub, project instructions/skills, runtime/checkpointer memory, user memory, and organization memory are separate stores/owners even if a source UI groups them. The state/credential matrix must prohibit automatic copying among them.

## Primary journeys

### Seed Layer 0

1. During or after onboarding, an authorized user starts the organization-context interview.
2. Deep Work explains purpose, viewers, agent read scope, provenance, retention, and that answers form a proposal.
3. The user supplies or skips each section and attaches authorized source references.
4. The service generates a proposed initial version with a semantic diff from empty.
5. A reviewer accepts, edits, or rejects items; merge creates version 1 and an audit event.
6. Agents receive read-only access only after their binding is authorized and validated.

### Produce a Layer 1 digest

1. A schedule or authorized user starts an analyst run with a fixed coverage window and source set.
2. The service assembles application events and available verified source summaries, recording every exclusion, error, and rate limit.
3. The constrained analyst produces a digest and optional itemized proposals with evidence references and confidence.
4. The digest publishes to the workspace review area; no memory changes occur.
5. Reviewers inspect evidence/diffs and merge selected items through the application service.

### Resolve a concurrent review

1. Two reviewers open proposals against the same approved base.
2. The first merge creates a new version.
3. The second attempt detects a stale base and shows conflicting/non-conflicting items.
4. Any rebase creates a new reviewable proposal version; prior approval is not silently carried across changed text.

## Complete state matrix

| State | Required behavior |
|---|---|
| Loading memory/digest | Preserve workspace/version identity and show section skeletons. |
| No approved memory | Offer guided seed proposal and explain that agents currently receive none. |
| Empty optional section | Show intentionally empty with add-to-proposal action for authorized actors. |
| Proposal drafting | Save durable draft/version; approved memory remains unchanged. |
| Proposal validation error | Preserve items, link field/evidence errors, and block review submission. |
| Proposal pending review | Agents read last approved version; show reviewers and base version. |
| Partially accepted | Create a merge set containing accepted/edited items only; rejected items retain feedback. |
| Proposal rejected | Preserve review feedback and provenance; no approved-memory change. |
| Stale/conflicting proposal | Compare base/current/proposal, require rebase and full re-review of changed items. |
| Merge running | One idempotent version operation; no partial approved version is visible. |
| Merge failed | Last approved version remains authoritative; proposal/review state remains retryable. |
| Approved/current | Show effective version/date, provenance, reviewer, and read audience. |
| Source evidence inaccessible | Withhold excerpt, retain safe provenance, and state access changed. |
| Partial source coverage | Digest lists included/excluded sources/time and avoids global conclusions. |
| Insights unavailable | Use application events plus verified source evidence; label the narrower coverage. |
| Rate limited/source timeout | Back off/checkpoint where safe, mark incomplete, and publish only with explicit qualification. |
| No evidence in window | Produce an empty/insufficient-evidence result, not invented insights. |
| Analyst run failed | Keep prior digests and approved memory; show safe retry and correlation ID. |
| Analyst output unsafe/sensitive | Quarantine/redact, prevent publication/proposal, and route to authorized review. |
| Context Hub ownership unknown | Do not sync/write; show application approved memory and discovery gate. |
| Permission denied | Show only entries/digests allowed by sensitivity; remove review/merge actions. |
| Offline | Show cached approved version/digests with snapshot time; drafting/review/merge disabled unless an explicit conflict-safe draft policy applies. |
| Reconnecting | Revalidate session, base version, evidence access, and proposal version before mutations. |
| Memory deleted/retention expired | Remove content as policy requires while retaining minimal non-sensitive audit tombstone where lawful. |
| Mobile | Reading and one-item accept/reject remain operable; complex diff/evidence review can hand off via durable link, never collapse to one unsafe “Approve all.” |

## Interfaces and state ownership

The proposed `/api/v1` application contract covers approved-memory/version queries, proposal draft/submit, item review, rebase, idempotent merge, digest run/query/publication, and evidence resolution. Exact paths remain API review outputs. Runtime agents receive a least-privilege read projection and a separate proposal-submission capability; neither grants merge.

Required entities include `OrgMemoryVersion`, `MemoryEntry` with sensitivity/provenance/effective dates, `MemoryProposal` and immutable proposal versions, `ProposalItem`, `ReviewDecision`, `EvidenceReference`, `AnalystRun`, `CoverageManifest`, and `DigestArtifact`. Every mutation carries tenant, actor, expected version, and idempotency metadata.

PostgreSQL owns version/proposal/review/digest metadata, normalized content where approved, evidence references, authorization, and audit. Large immutable digest artifacts may use an approved object store after a retention/security decision; no vendor is assumed here. The source runtime owns traces/source-native memory. Context Hub remains a separate owner until its accepted contract explicitly permits a safe integration.

## Runtime capability and fallback rules

- Classic agents may receive the approved read projection and submit proposals only through application-owned authorized interfaces designed for that purpose; no runtime tool gets merge authority.
- MDA access remains beta/capability-detected. Context Hub sync/read/write behavior is absent until exact ownership, persistence across deployment, auth, and conflict semantics are proven.
- Fleet is not an organization-memory configuration surface; read/invoke integration after its spike grants no memory mutation.
- Analyst evidence comes from `DW-OPS-002` application events and verified per-source links/summaries, never a nonexistent global thread search.
- Without Insights or complete trace access, the digest narrows claims and displays coverage; it does not fill gaps with inference.
- If the analyst runtime is unavailable, approved memory and previous digests remain accessible and review-safe.

## Persistence, security, privacy, and governance

Organization-memory reads and evidence are tenant-, workspace-, actor-, agent-, purpose-, and sensitivity-authorized. Runtime agents receive least-privilege read-only views. Proposal submission and merge use distinct credentials/roles; merge requires an authorized human session and may require step-up authentication. Every accepted text span has provenance and review identity.

Analyst inputs/outputs are untrusted and prompt-injection resistant by explicit delimiting, tool allowlists, bounded retrieval, evidence requirements, and no side-effect tools. Raw prompts, tool arguments, credentials, private trace content, and sensitive artifacts are excluded by default. Evidence links are resolved and authorized at view time. Exports and notifications follow sensitivity policy.

Approved versions are immutable; correction creates a new version. Retention/deletion policies separately address user memory, organization entries, proposals, reviews, evidence links, digests, and audit. Workspace deletion and actor erasure must not leave readable orphan content. Encryption and backup/restore cover PostgreSQL state; restoration preserves version lineage and tenant boundaries.

## Responsive and accessible behavior

Memory/digest sections use semantic headings, provenance lists, non-color confidence/coverage labels, and keyboard-operable evidence links. Semantic diffs mark add/change/remove in text and offer a plain-text representation. Review decisions have explicit consequences and focus recovery. On mobile, proposals are reviewed item by item with persistent progress and no default bulk approval. At 320 CSS px/200% zoom, evidence, coverage, base/current version, and decision controls remain perceivable. Reduced motion applies to merge/diff transitions.

## Metrics and guardrails

- 100% of approved organization-memory changes identify base/new version, provenance, human reviewer, review decision, and audit event.
- Zero runtime-agent or analyst direct writes to approved memory.
- 100% of digests publish a machine-readable and human-readable coverage manifest.
- Proposal acceptance, rejection, edit, later-correction, stale-conflict, and evidence-access failure rates are tracked.
- Zero workspace-wide claim is emitted when required source coverage is incomplete under the accepted rubric.
- Guardrail: digest publication and memory merge are separate commands and authorizations.

## Dependencies and readiness gates

Depends on `DW-AGENT-005`, `DW-OPS-001`, `DW-OPS-002`, onboarding workspace identity, schedules where the analyst is recurring, and the application authorization/audit foundation. Readiness requires the canonical memory ownership matrix, Context Hub contract spike, entry/evidence sensitivity taxonomy, analyst evidence/coverage rubric, review/merge concurrency specification, retention/deletion policy, and prompt-injection/security evaluation.

## Rollout and rollback

1. Launch Layer 0 manual seed proposals and human review with no runtime mount.
2. Enable read-only approved-memory projection for selected classic fixture agents.
3. Run Layer 1 analyst manually on application-owned fixture events; publish digests with no proposal generation.
4. Add optional proposals, then recurring schedule only after review quality/security gates.
5. Enable any Context Hub or MDA path independently after the ownership spike; never migrate authority implicitly.

Rollback disables analyst runs, proposal generation, runtime projection, or source integration independently. Approved versions and audit history remain readable to authorized users. Runtime projection rollback revokes future mounts without rewriting project instructions or source-native memory. A flawed digest can be withdrawn/tombstoned while its audit and downstream proposal links remain traceable.

## Executable acceptance scenarios

1. **Seed review:** Given no approved organization memory, when onboarding completes, then it creates a proposal; agents receive no organization context until an authorized reviewer merges accepted items into version 1.
2. **No direct writes:** Given an analyst/runtime credential, when it attempts an approved-memory merge endpoint, then authorization fails and the approved version remains unchanged while proposal submission remains available if allowed.
3. **Qualified digest:** Given two configured sources with one unavailable and no Insights entitlement, when the analyst runs, then the digest names the included/excluded source and time window and makes no whole-workspace claim.
4. **No evidence:** Given an empty authorized event window, when analysis runs, then it publishes an insufficient-evidence/empty result with no fabricated proposal.
5. **Selective review:** Given a proposal with three items, when a reviewer accepts one, edits/accepts one, and rejects one, then the new version contains exactly the two approved outcomes and retains rejection feedback outside approved memory.
6. **Concurrent reviewers:** Given two proposals/reviews against one base, when the first merges, then the second receives a stale-base conflict and changed items require re-review after rebase.
7. **Evidence revocation:** Given a digest evidence link the actor later loses access to, when reopened, then the excerpt is withheld, safe provenance remains, and no cached sensitive content leaks.
8. **Deployment isolation:** Given a new agent project revision is deployed, when reconciliation runs, then approved org memory, user memory, source-native runtime memory, and project instructions remain separate and none is overwritten.
9. **Context Hub gate:** Given ownership/write semantics are unverified, when an MDA agent opens Memory configuration, then no Context Hub write/sync request occurs and application memory is read-only/proposal-based.
10. **Mobile review:** Given a narrow viewport and keyboard/switch input, when a reviewer handles a multi-item proposal, then each diff/evidence/decision is accessible and no single accidental action approves the full set.
