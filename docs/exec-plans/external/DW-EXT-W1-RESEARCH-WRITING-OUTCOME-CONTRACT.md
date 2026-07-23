---
packet_id: DW-EXT-W1-RESEARCH-WRITING-OUTCOME-CONTRACT
title: External dispatch - finish research and writing with verifiable results
status: ready-for-external-dispatch
base_commit: fff1bfd278d550d01de6e8d74f553f45c4003a8c
branch: external/research/research-writing-outcome-contract
owner: external-research-writing-outcome-researcher
reviewers: [runtime-contracts, security, product]
risk: high
acceptance_ids: [SPIKE-ARTIFACT-001, SPIKE-SUBAGENT-001, SPIKE-RUBRIC-001, SPIKE-VERIFICATION-001, AC-DW-TASK-005-01, AC-DW-TASK-005-02, AC-DW-TASK-005-03, AC-DW-HITL-002-01, AC-DW-HITL-002-02, AC-DW-HITL-002-03, AC-DW-HITL-002-04]
allowed_paths: [tools/contract-spikes/research-writing-outcomes/**, docs/references/research/research-writing-outcomes/**, docs/exec-plans/external/DW-EXT-W1-RESEARCH-WRITING-OUTCOME-CONTRACT.md]
dependencies: [SPIKE-COMPOSE-001, SPIKE-CONFIG-001, SPIKE-STREAM-003, SPIKE-HITL-001, SRC-LC@7b9215d708e0b57e6fbae7b5d0762c4118b8e309, SRC-DA@7794b61a6e76230e8c7a49bdce808b3728305914, SRC-LCPY@592055e15e138f5369dce95dd049ce22430996e2, SRC-LG@31f90df3e6b0268fa77fd2d118a917d420b84a68, public-package-index-access, official-documentation-access, optional:non-production-classic-sandbox]
blockers: [accepted-SPIKE-COMPOSE-001, accepted-SPIKE-CONFIG-001, accepted-SPIKE-STREAM-003, accepted-SPIKE-HITL-001, approved-public-package-index-access, sanctioned-non-production-classic-sandbox]
created: 2026-07-23
reviewed_at: 2026-07-23
review_result: accepted
---

# External dispatch - finish research and writing with verifiable results

## Dispatch identity

- Exact base SHA:
  `fff1bfd278d550d01de6e8d74f553f45c4003a8c`.
- Branch to create:
  `external/research/research-writing-outcome-contract`.
- ExecPlan: this file.
- This is one coherent contract-research packet with artifact, subagent,
  rubric, and verifier internal streams. It does not authorize product UI/API
  implementation, provider adapters, artifact hosting, async workstreams, model
  procurement, capability enablement, or any end-to-end claim.
- This packet is for an external worker. The program coordinator has not assigned
  its implementation scope to an internal agent.

## Purpose and observable result

Answer `SPIKE-ARTIFACT-001`, `SPIKE-SUBAGENT-001`, `SPIKE-RUBRIC-001`, and
`SPIKE-VERIFICATION-001` with one version-pinned contract corpus proving how a
research or writing task can finish with reviewable outputs, provenance, bounded
subagent facts, ordered criteria, append-only repair history, and a verdict that
cannot be substituted by a generic model summary.

The result must keep four internal streams correlated by stable tenant/workspace/
source/actor/task/run/attempt/artifact/subagent/criterion/evidence identities:

1. artifact metadata/content/access/retention;
2. synchronous subagent lifecycle and parent attribution;
3. rubric initialization, ordered evaluation, repair, and caps; and
4. template-specific evidence binding and verdict normalization.

Deterministic fake-model research/writing fixtures may complete Deep Work
normalization without a hosted sandbox. They do not prove an installed Deep
Agents API. Separate installed-public conformance cells and real classic
file/state/sandbox or subagent rows remain blocked until their exact dependencies
are available.

## Allowed paths

The worker may change only:

```text
tools/contract-spikes/research-writing-outcomes/**
docs/references/research/research-writing-outcomes/**
docs/exec-plans/external/DW-EXT-W1-RESEARCH-WRITING-OUTCOME-CONTRACT.md
```

The probe is one coherent packet with two isolated uv projects:

```text
tools/contract-spikes/research-writing-outcomes/offline/
tools/contract-spikes/research-writing-outcomes/installed-public/
```

`offline/` has a dependency-free lock, validators, scrubber, deterministic fake
model/runtime, and global network-denial tests. `installed-public/` has a separate
lock and runs only after approved public-package-index access pins the public
distributions. Neither project imports another repository project or writes a
root/shared lock. Both feed one cross-stream identity/schema matrix without
turning fake normalization into package or hosted-runtime evidence.

Application/package source, agent templates, shared fixtures, root manifests/
locks, product specs, decisions, source ledger, generated docs, program/index
records, CI, and `docs/plans/**` are read-only.

## Scope and explicit exclusions

In scope:

- research report/provenance/unresolved-claim outcomes;
- writing working-file versus promoted final-artifact outcomes;
- synchronous/namespaced subagent facts where the source supplies them;
- manual-checklist fallback when automatic verification is unsupported;
- rubric/verifier failure, repair, cap, cancellation, and recovery; and
- a minimal coding evidence-binding negative fixture only where required to answer
  `SPIKE-VERIFICATION-001` across all named template families.

Out of scope:

- the coding journey, PR/CI/merge state, or `AC-DW-TASK-005-04`;
- async/background subagents or multi-day workstreams;
- general-purpose artifact storage/application downloads;
- factual-truth claims based only on citations;
- hidden chain-of-thought collection or persistence;
- product/application/browser/accessibility/performance implementation; and
- every `E2E-*` scenario.

The minimal coding verifier row does not contribute to a coding product scenario;
it proves only that failed/missing test evidence cannot be hidden by a generic pass.

## Dependencies and evidence precedence

Consume, do not duplicate, these separately owned gates:

- `SPIKE-COMPOSE-001` for task/run input and normalized creation;
- `SPIKE-CONFIG-001` for pinned starter templates/config;
- `SPIKE-STREAM-003` for projected event namespaces/content; and
- `SPIKE-HITL-001` for any ordered interrupt/decision interaction.

Record exact accepted artifact commits and fixture hashes. A dependent row inherits
`blocked-live-evidence` or rejection from an unresolved upstream gate. The
deterministic fake harness can prove local cross-stream behavior but cannot accept
an upstream or hosted provider contract.

This dispatch base does not contain upstream artifacts. The independently reviewed
LangChain research head
`758c1d4a2230b7c4261fcfbd0f3008634509e096` is cited only as blocked evidence:
its `SPIKE-COMPOSE-001`, `SPIKE-CONFIG-001`, `SPIKE-STREAM-003`, and
`SPIKE-HITL-001` rows are all `blocked-live-evidence`. They are not accepted
capability inputs, and this worker must neither copy/reclassify them nor accept a
dependent hosted row. A later coordinator rebase/integration may update their
provenance without silently changing their state.

Pinned inputs are `SRC-LC` at
`7b9215d708e0b57e6fbae7b5d0762c4118b8e309`, `SRC-DA` at
`7794b61a6e76230e8c7a49bdce808b3728305914`, `SRC-LCPY` at
`592055e15e138f5369dce95dd049ce22430996e2`, and `SRC-LG` at
`31f90df3e6b0268fa77fd2d118a917d420b84a68`, plus reviewed official
documentation, installed public/generated packages, and, only for live
acceptance, an explicitly supplied non-production classic sandbox with account
tier, region, server/package versions, auth context, and synthetic task data.

Evidence precedence is accepted live fixture, installed public/generated
contract, official documentation, pinned reference, deterministic fake, then
unknown. A model-generated citation, filename, completion message, score, or
subagent narrative is untrusted until bound to validated source-owned evidence.

Pinned example evidence is reference-only:

- `SRC-DA@7794b61...:examples/deep_research`, Git tree
  `221c48af3799b2f1ddf30da38c123782fe43d08d`; and
- `SRC-DA@7794b61...:examples/deploy-content-writer`, Git tree
  `1092e58bced52dc204184273f30f8a7244874158`.

These are examples, not Deep Work starter-template contracts. The report records
their exact paths/tree hashes and may use them only to formulate questions. It
must not claim their prompts, tools, state, deployment, memory, or subagent shape
as a supported starter contract.

## Installed-public conformance cells

After package-index preflight succeeds, pin the exact public distribution versions
and lock/file hashes before observing behavior. Using a deterministic fake chat
model and no provider network, the installed-public project must separately
conformance-test only public imports/constructors for:

- `deepagents.create_deep_agent`;
- `deepagents.RubricMiddleware`; and
- synchronous `deepagents.SubAgent` / `deepagents.SubAgentMiddleware`.

The pinned `SRC-DA` public-export anchors are
`libs/deepagents/deepagents/__init__.py` blob
`e4f49a7bfb606bd208212f5c28a9f41d9e87ee33`,
`middleware/rubric.py` blob
`44ca2fc1a0cdcf72b53eb20b5529f21cfcacc21d`, and
`middleware/subagents.py` blob
`0ba32e11490f24f13b3c11c08235499522c88f06`. Those source blobs guide review;
only the installed public distributions establish the conformance result.

Without approved package-index access, `installed-public/` is not locked or run.
Every public-API cell and dependent spike disposition is
`blocked-package-index-evidence`; the worker completes only the dependency-free
offline normalization corpus and must not improvise a source checkout install,
path dependency, editable install, wheel copied from another worktree, or network
fallback.

## Required four-stream matrix

### Artifact stream

Cover list/metadata, working-file versus explicitly promoted artifact, stable
version/content hash, source/state/file/sandbox ownership, safe media metadata,
authorized open/download, range and size limits, expiry, revocation, retention,
deletion, unavailable content, stale link, and cross-artifact substitution.
Negative rows substitute every tenant/workspace/source/actor/task/run/attempt
identity and evidence reference independently. Without live content access proof,
retain metadata and a source-native link only.

### Subagent stream

Cover spawn/discover, stable namespace/ID, parent tenant/workspace/source/actor/
task/run/attempt linkage,
input-summary bounds, progress as source-supplied facts, complete, fail, cancel,
reconnect, compacted history, duplicate/out-of-order events, unknown/malformed
content, wrong identity at every level, cross-workspace replay, and evidence
substitution. Do not infer progress, expose hidden prompts/reasoning, or call an
async supervisor.

### Rubric stream

Cover immutable rubric/version, ordered criteria, required/advisory semantics,
evidence references, initialization, pass/fail/uncertain/not-evaluated, repair
candidate/iteration linkage, interrupt interaction, cap, cancellation, verifier
error, reconnect/restart, cost/time ceilings, and append-only supersession.
Required fail/uncertain/not-evaluated can never normalize to automatic pass.
Negative rows bind and then substitute tenant/workspace/source/actor/task/run/
attempt/criterion/evidence identities.

### Verification stream

Use deterministic fake-model outputs for:

- research: cited report with provenance and unresolved claims; missing,
  unreachable, mismatched, or fabricated citation; generic pass despite a missing
  required evidence record;
- writing: working files versus promoted final deliverable; missing/empty/stale
  deliverable; source attribution; generic pass despite no final artifact;
- minimal coding gate row: failing or missing test evidence despite a generic pass,
  without implementing or claiming the coding journey; and
- repair iteration history, evidence changed between attempts, cap, cancel,
  verifier/model error, resume, and manual-checklist fallback.

Verdicts bind to exact tenant/workspace/source/actor/task/run/attempt/template/
rubric/candidate/evidence versions. Negative rows substitute each identity and
cross-stream evidence owner. Store only bounded user-displayable rationale
summaries, never hidden reasoning.

## Required retained outputs

Under `docs/references/research/research-writing-outcomes/`, retain:

- `matrix.json`: complete rows for all four streams with exact versions, upstream
  pins, identity tuple, evidence tier, request/output schemas, state transitions,
  result, blocker, and fallback;
- `report.md`: coherent cross-stream contract, contradictions, accepted/blocked/
  rejected rows, manual fallbacks, and explicit downstream contribution limits;
- `fixtures/`: deterministic research/writing/coding-negative transcripts,
  artifact/evidence manifests, subagent events, rubric/verdict histories, hashes,
  and expected outcomes;
- `schemas/`: machine-readable versioned artifact, subagent, rubric, verdict, and
  cross-reference schemas produced for the probe only;
- `versions.json`: Python, dependencies, reference-example paths/tree hashes,
  explicitly blocked starter-template contract state, public/generated contracts,
  runtime/server/account/region/date, and upstream artifacts;
- `commands.txt`: exact commands and exit statuses without environment dumps;
- `scrub-report.json`: zero secrets, credentials, customer/tenant data, reusable
  endpoints, raw headers/cookies, hidden reasoning, unsafe HTML/URLs, or
  unsanitized absolute paths; and
- `index-status.json`: fail-closed public-package-index preflight result and the
  exact permitted validation path;
- `review.json`: immutable final runtime-contract, security, and product verdicts,
  finding resolutions, candidate commit/tree hashes, attestation commit, reviewer
  identities/roles, reviewed commands, and per-row/per-spike state; and
- `hashes.json`: closure over every retained fixture/schema/report/matrix/version/
  command/scrub artifact except the self-referential hash manifest itself.

The matrix validator rejects missing cross-stream references, duplicate identity,
orphaned evidence, artifact/working-file confusion, inferred subagent facts,
mutable/superseded history, automatic pass with failed required evidence,
accepted-live rows without live metadata, fake evidence promoted to provider
proof, cross-tenant/workspace/source/actor/task/run/attempt/evidence substitution,
inherited blocked dependencies promoted to accepted, missing fallbacks, and
unresolved source-precedence conflicts. Separate validators also reject invalid
`versions.json`, missing/nonzero command exit records, incomplete fixture/hash
closure, a scrub report older than any covered evidence file, absent/stale
package-index status, or an incomplete/drifted review attestation.

## Acceptance IDs and downstream contribution

Every `AC-*` row is supporting contract evidence only. This packet credits zero
`E2E-*` IDs and does not
satisfy application, UI, persistence, authorization, browser, accessibility,
performance, release, or end-to-end acceptance by itself.

| ID | Required evidence and limit |
|---|---|
| `SPIKE-ARTIFACT-001` | File/state/sandbox metadata and content/access/expiry/retention/range/size/deletion rows are decided per source. Live-required content rows stay blocked without sanctioned sandbox proof. |
| `SPIKE-SUBAGENT-001` | Synchronous namespace/lifecycle/parent/compaction rows are decided per source. Unsupported or live-unproved sources retain the generic-parent-timeline fallback. |
| `SPIKE-RUBRIC-001` | Pinned middleware schema and initialization/order/evidence/repair/interrupt/cap/cancel/failure/resume rows are complete at their truthful evidence tier. |
| `SPIKE-VERIFICATION-001` | Research, writing, and minimal coding-negative fixtures prove missing citations, deliverables, or tests cannot be replaced by a generic pass. |
| `AC-DW-TASK-005-01` | Supports research provenance, unresolved-claim, and no-truth-overclaim contract slices. Full task/application rendering remains downstream. |
| `AC-DW-TASK-005-02` | Supports working-file versus explicitly promoted artifact semantics. Full artifact catalog/access UI remains downstream. |
| `AC-DW-TASK-005-03` | Supports truthful absence/generic events when subagents are unsupported. Full source manifest/task-detail behavior remains downstream. |
| `AC-DW-HITL-002-01` | Supports required-failure normalization only; application/task status and UI remain downstream. |
| `AC-DW-HITL-002-02` | Supports append-only repair/verdict history only; application persistence and review UI remain downstream. |
| `AC-DW-HITL-002-03` | Supports the manual-checklist fallback and no automatic score only; product UI remains downstream. |
| `AC-DW-HITL-002-04` | Supports bounded iteration/cap behavior only; runtime orchestration and UI remain downstream. |

This packet explicitly excludes `AC-DW-TASK-005-04` and every `E2E-*` scenario.
Full `AC-DW-TASK-005-*` qualification remains owned by `DW-TASK-005`
(`product`, `task-experience`, `agent-runtime`, `sdk`). Full
`AC-DW-HITL-002-*` qualification remains owned by `DW-HITL-002`
(`verification`, `agent-runtime`, `task-experience`, `api`). Release/E2E
qualification remains with `DW-QUAL-001` and the program coordinator. Persistence,
authorization, audit, and recovery proof remains with `DW-FND-003` and
`DW-FND-005`; normalized client contracts and fixture equivalence remain with
`DW-FND-004`; web/demo projection remains with `DW-FND-002`; responsive,
accessible surface qualification remains with `DW-SURF-001` and `DW-QUAL-001`.
The excluded `AC-DW-TASK-005-04` remains with later `DW-CODE-001`,
`DW-CODE-002`, `DW-CODE-003`, and their coding-journey implementation packet.

## Exact validation commands

First run the fail-closed no-index path. It performs no package-index request and
must be the default:

```bash
python3 tools/contract-spikes/research-writing-outcomes/index_preflight.py --mode no-index --output docs/references/research/research-writing-outcomes/index-status.json
uv lock --project tools/contract-spikes/research-writing-outcomes/offline --offline
uv sync --project tools/contract-spikes/research-writing-outcomes/offline --frozen --offline
UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m unittest discover -s tools/contract-spikes/research-writing-outcomes/offline/tests -p 'test_*.py'
UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.inventory --output docs/references/research/research-writing-outcomes/versions.json
UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.validate_matrix docs/references/research/research-writing-outcomes/matrix.json --require-all-streams --require-complete-cross-product --require-installed-public-blocked --reject-orphaned-evidence --reject-blocked-dependency-promotion --reject-unresolved-precedence-conflicts
UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.scrub docs/references/research/research-writing-outcomes
UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.hash_evidence docs/references/research/research-writing-outcomes --output docs/references/research/research-writing-outcomes/hashes.json
UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.validate_evidence docs/references/research/research-writing-outcomes --require-command-statuses --require-fixture-hash-closure --require-fresh-scrub
UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.validate_scope --base fff1bfd278d550d01de6e8d74f553f45c4003a8c --include-untracked
uv lock --project tools/contract-spikes/research-writing-outcomes/offline --check --offline
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
git diff --check fff1bfd278d550d01de6e8d74f553f45c4003a8c...HEAD
git diff --name-only fff1bfd278d550d01de6e8d74f553f45c4003a8c
git status --short
```

Only after a reviewer-approved package-index preflight succeeds, run the separate
installed-public conformance path:

```bash
python3 tools/contract-spikes/research-writing-outcomes/index_preflight.py --mode approved-public-index --output docs/references/research/research-writing-outcomes/index-status.json
uv lock --project tools/contract-spikes/research-writing-outcomes/installed-public
uv sync --project tools/contract-spikes/research-writing-outcomes/installed-public --frozen
uv run --project tools/contract-spikes/research-writing-outcomes/installed-public --frozen pytest -m installed_public
UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/installed-public --frozen pytest -m installed_public
uv lock --project tools/contract-spikes/research-writing-outcomes/installed-public --check --offline
UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.inventory --output docs/references/research/research-writing-outcomes/versions.json
UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.validate_matrix docs/references/research/research-writing-outcomes/matrix.json --require-all-streams --require-complete-cross-product --require-installed-public-conformance --reject-orphaned-evidence --reject-blocked-dependency-promotion --reject-unresolved-precedence-conflicts
UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.scrub docs/references/research/research-writing-outcomes
UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.hash_evidence docs/references/research/research-writing-outcomes --output docs/references/research/research-writing-outcomes/hashes.json
UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.validate_evidence docs/references/research/research-writing-outcomes --require-command-statuses --require-fixture-hash-closure --require-fresh-scrub
```

If the approved index preflight cannot succeed, none of these installed-public
commands may run; the no-index result and blockers are the final truthful outcome.

Only with accepted upstream artifacts and explicitly supplied non-production
classic-sandbox access, run:

```bash
uv run --project tools/contract-spikes/research-writing-outcomes/installed-public --frozen pytest -m live_contract --live-profile non-production-classic-outcomes --evidence-dir docs/references/research/research-writing-outcomes/live
UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.scrub docs/references/research/research-writing-outcomes/live
```

The live command fails closed if the sandbox/profile or any accepted dependency is
absent. It uses synthetic bounded tasks, cleans up where the accepted public
contract permits, and never prints or persists secrets, raw headers/cookies,
reusable endpoints, customer content, hidden reasoning, or environment dumps.

## Deterministic fallback

Until each row is independently accepted for a source:

- show artifact metadata and an authorized source-native link only; no application
  content download or preview claim;
- fold source-supplied subagent facts into safe generic parent-timeline events and
  show no Subagents panel;
- retain the immutable rubric as task context and offer the same criteria as a
  manual checklist;
- label verification `unsupported` or `manually_reviewed`, never automatic pass or
  a numeric score; and
- keep research/writing tasks usable without the unproved projections.

## Idempotence, rollback, and handoff

Offline runs are deterministic, network-denied, and write only bounded evidence
and temporary state. Replaying an event/verdict cannot duplicate an artifact,
subagent, iteration, or terminal transition. Restart fixtures restore
append-only state and exact evidence bindings. Live synthetic records use unique
identities, bounded operations, and explicit cleanup evidence.

The author commits a clean candidate and records its commit/tree hash. After every
finding is fixed, three distinct reviewers independently cover runtime contracts,
security, and product. A reviewer then creates one review-only attestation commit
whose parent is exactly the candidate and whose diff changes only
`docs/references/research/research-writing-outcomes/review.json`.
`validate_review` must reject missing/non-final verdicts, repeated reviewer
identity, author self-review, parent/candidate mismatch, non-review path changes,
candidate-tree drift, missing reviewed commands, or an attestation created before
the final fixes:

```bash
UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.validate_review docs/references/research/research-writing-outcomes/review.json --attestation-commit HEAD --require-review-only-parent --require-roles runtime-contracts security product
```

Commit only allowed paths on the named branch. Keep this packet current with
progress, discoveries, decisions, commands, dependency states, evidence, and
blockers. The author cannot accept their own work or modify the review-only
attestation commit. Reviewers decide each matrix row and all four spike
dispositions.

The coordinator alone updates source ledgers, upstream spike state, product/
program/index records, starter agents, application adapters, normalized
contracts, capability flags, or release scope. No worktree creation, push, merge,
deployment, publication, production mutation, credential collection, or
destructive cleanup is authorized by this packet.

## Progress

- [x] Confirmed the delegated worktree, branch, seed, exact base, governed paths,
  and repository/documentation instructions.
- [x] Implemented the dependency-free offline project with a local PEP 517
  backend, frozen lock, stdlib `unittest` suite, deterministic fake normalizer,
  and global socket/DNS denial.
- [x] Implemented fail-closed package-index preflight and the separate,
  deliberately unlocked and unexecuted installed-public conformance cell.
- [x] Generated the correlated artifact/subagent/rubric/verifier matrix, closed
  schemas, deterministic transcripts/manifests/histories, report, versions,
  commands, scrub status, and evidence hash closure.
- [x] Kept COMPOSE-001, CONFIG-001, STREAM-003, and HITL-001 blocked at reviewed
  head `758c1d4a2230b7c4261fcfbd0f3008634509e096`; no upstream row was copied,
  accepted, or reclassified.
- [x] Completed all exact no-index validations after final corpus fixes: 15
  stdlib tests, 78 matrix rows, 12 evidence records, 19-file retained hash
  closure, zero scrub findings, fresh evidence, governed scope, offline lock,
  documentation generation/check, and diff checks.
- [ ] Commit a clean candidate, obtain distinct runtime-contract/security/product
  final reviews, resolve findings, and create the review-only attestation commit.
- [ ] Validate the attestation, send the coordinator the reviewed SHA and exact
  evidence, then stop.

## Surprises and discoveries

- The sandboxed first `uv` invocation could not access the existing user cache.
  The required no-index commands therefore run with explicit sandbox escalation;
  `UV_OFFLINE=true`, `--offline`, and the test-level network denial remain active.
- The first offline sync exposed that uv requested the PEP 660 editable hooks.
  The dependency-free local backend now supplies those hooks by emitting the same
  deterministic wheel, without a build dependency.
- The first scrub correctly rejected a prose occurrence matching its private
  reasoning detector. The detector is now scoped to persisted reasoning fields
  and chain-of-thought markers, so the report can state the prohibition without
  becoming a false positive.

## Decision log

- Decision: finish the no-index path and mark installed-public and live cells
  blocked.
  Rationale: no reviewer-approved package-index access, accepted upstream
  artifact, or sanctioned non-production classic sandbox was supplied.
- Decision: retain an installed-public fail-closed test template but no
  `uv.lock`, distribution pins, or observed constructor result.
  Rationale: the packet requires a separate project while prohibiting improvised
  source/editable/copied-wheel evidence before approved public index access.
- Decision: use one synthetic identity tuple across the positive corpus and
  independently substitute every tenant/workspace/source/actor/task/run/attempt
  and stream-specific identity in negative rows.
  Rationale: this makes cross-stream ownership explicit and lets the validator
  reject both orphaned evidence and replay/substitution.

## Outcomes and retrospective

Pending final validation and independent review. The intended truthful outcome is
accepted deterministic Deep Work normalization for bounded offline cells, with
public Deep Agents conformance and classic-sandbox behavior left blocked at their
named evidence gates. This packet will credit only AC-DW-TASK-005-01/-02/-03 and
AC-DW-HITL-002-01..04, zero `E2E-*` IDs, and no AC-DW-TASK-005-04.
