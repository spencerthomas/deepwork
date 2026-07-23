---
packet_id: DW-EXT-W1-RESEARCH-WRITING-OUTCOME-CONTRACT
title: External dispatch - finish research and writing with verifiable results
status: prepared-for-independent-review
base_commit: fff1bfd278d550d01de6e8d74f553f45c4003a8c
branch: external/research/research-writing-outcome-contract
owner: external-research-writing-outcome-researcher
reviewers: [runtime-contracts, security, product]
risk: high
acceptance_ids: [SPIKE-ARTIFACT-001, SPIKE-SUBAGENT-001, SPIKE-RUBRIC-001, SPIKE-VERIFICATION-001, AC-DW-TASK-005-01, AC-DW-TASK-005-02, AC-DW-TASK-005-03, AC-DW-HITL-002-01, AC-DW-HITL-002-02, AC-DW-HITL-002-03, AC-DW-HITL-002-04]
allowed_paths: [tools/contract-spikes/research-writing-outcomes/**, docs/references/research/research-writing-outcomes/**, docs/exec-plans/external/DW-EXT-W1-RESEARCH-WRITING-OUTCOME-CONTRACT.md]
dependencies: [SPIKE-COMPOSE-001, SPIKE-CONFIG-001, SPIKE-STREAM-003, SPIKE-HITL-001, SRC-LC@7b9215d708e0b57e6fbae7b5d0762c4118b8e309, SRC-DA@7794b61a6e76230e8c7a49bdce808b3728305914, SRC-LG@31f90df3e6b0268fa77fd2d118a917d420b84a68, public-package-index-access, official-documentation-access, optional:non-production-classic-sandbox]
created: 2026-07-23
reviewed_at: null
review_result: pending
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

The result must keep four internal streams correlated by stable
task/run/attempt/artifact/subagent/criterion/evidence identities:

1. artifact metadata/content/access/retention;
2. synchronous subagent lifecycle and parent attribution;
3. rubric initialization, ordered evaluation, repair, and caps; and
4. template-specific evidence binding and verdict normalization.

Deterministic fake-model research/writing fixtures may complete without a hosted
sandbox. Rows requiring real classic file/state/sandbox or subagent behavior
remain `blocked-live-evidence` until sanctioned non-production access exists.

## Allowed paths

The worker may change only:

```text
tools/contract-spikes/research-writing-outcomes/**
docs/references/research/research-writing-outcomes/**
docs/exec-plans/external/DW-EXT-W1-RESEARCH-WRITING-OUTCOME-CONTRACT.md
```

The probe is one isolated Python/uv project with its own `pyproject.toml`,
`uv.lock`, tests, validators, scrubber, deterministic fake model/runtime, and
no-network fixture runner. Internal modules may be separated by stream but must
share one cross-stream identity/schema validator. The project must not import
another repository project or write a root/shared lock.

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

Pinned inputs are `SRC-LC` at
`7b9215d708e0b57e6fbae7b5d0762c4118b8e309`, `SRC-DA` at
`7794b61a6e76230e8c7a49bdce808b3728305914`, and `SRC-LG` at
`31f90df3e6b0268fa77fd2d118a917d420b84a68`, plus reviewed official
documentation, installed public/generated packages, and, only for live
acceptance, an explicitly supplied non-production classic sandbox with account
tier, region, server/package versions, auth context, and synthetic task data.

Evidence precedence is accepted live fixture, installed public/generated
contract, official documentation, pinned reference, deterministic fake, then
unknown. A model-generated citation, filename, completion message, score, or
subagent narrative is untrusted until bound to validated source-owned evidence.

## Required four-stream matrix

### Artifact stream

Cover list/metadata, working-file versus explicitly promoted artifact, stable
version/content hash, source/state/file/sandbox ownership, safe media metadata,
authorized open/download, range and size limits, expiry, revocation, retention,
deletion, unavailable content, stale link, wrong actor/workspace/task, and
cross-artifact substitution. Without live content access proof, retain metadata
and a source-native link only.

### Subagent stream

Cover spawn/discover, stable namespace/ID, parent task/run/attempt linkage,
input-summary bounds, progress as source-supplied facts, complete, fail, cancel,
reconnect, compacted history, duplicate/out-of-order events, unknown/malformed
content, wrong parent, and cross-workspace replay. Do not infer progress, expose
hidden prompts/reasoning, or call an async supervisor.

### Rubric stream

Cover immutable rubric/version, ordered criteria, required/advisory semantics,
evidence references, initialization, pass/fail/uncertain/not-evaluated, repair
candidate/iteration linkage, interrupt interaction, cap, cancellation, verifier
error, reconnect/restart, cost/time ceilings, and append-only supersession.
Required fail/uncertain/not-evaluated can never normalize to automatic pass.

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

Verdicts bind to exact task/run/template/rubric/candidate/evidence versions. Store
only bounded user-displayable rationale summaries, never hidden reasoning.

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
- `versions.json`: Python, dependencies, starter templates, public/generated
  contracts, runtime/server/account/region/date, and upstream artifacts;
- `commands.txt`: exact commands and exit statuses without environment dumps;
- `scrub-report.json`: zero secrets, credentials, customer/tenant data, reusable
  endpoints, raw headers/cookies, hidden reasoning, unsafe HTML/URLs, or
  unsanitized absolute paths; and
- `review.json`: independent runtime-contract, security, and product verdicts,
  finding resolutions, reviewed commit, and per-row/per-spike state.

The matrix validator rejects missing cross-stream references, duplicate identity,
orphaned evidence, artifact/working-file confusion, inferred subagent facts,
mutable/superseded history, automatic pass with failed required evidence,
accepted-live rows without live metadata, fake evidence promoted to provider
proof, inherited blocked dependencies promoted to accepted, missing fallbacks, and
unresolved source-precedence conflicts.

## Acceptance IDs and downstream contribution

Every `AC-*` row is supporting contract evidence only. This packet does not
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

## Exact validation commands

The worker must implement and run:

```bash
uv lock --project tools/contract-spikes/research-writing-outcomes
uv sync --project tools/contract-spikes/research-writing-outcomes --frozen
uv run --project tools/contract-spikes/research-writing-outcomes --frozen pytest -m 'not live_contract'
uv run --project tools/contract-spikes/research-writing-outcomes --frozen python -m research_writing_outcome_spikes.inventory --output docs/references/research/research-writing-outcomes/versions.json
uv run --project tools/contract-spikes/research-writing-outcomes --frozen python -m research_writing_outcome_spikes.validate_matrix docs/references/research/research-writing-outcomes/matrix.json --require-all-streams --require-complete-cross-product --reject-orphaned-evidence --reject-blocked-dependency-promotion --reject-unresolved-precedence-conflicts
uv run --project tools/contract-spikes/research-writing-outcomes --frozen python -m research_writing_outcome_spikes.scrub docs/references/research/research-writing-outcomes
uv run --project tools/contract-spikes/research-writing-outcomes --frozen python -m research_writing_outcome_spikes.validate_scope --base fff1bfd278d550d01de6e8d74f553f45c4003a8c --include-untracked
uv lock --project tools/contract-spikes/research-writing-outcomes --check --offline
UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes --frozen pytest -m 'not live_contract'
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
git diff --check fff1bfd278d550d01de6e8d74f553f45c4003a8c...HEAD
git diff --name-only fff1bfd278d550d01de6e8d74f553f45c4003a8c
git status --short
```

Only with accepted upstream artifacts and explicitly supplied non-production
classic-sandbox access, run:

```bash
uv run --project tools/contract-spikes/research-writing-outcomes --frozen pytest -m live_contract --live-profile non-production-classic-outcomes --evidence-dir docs/references/research/research-writing-outcomes/live
uv run --project tools/contract-spikes/research-writing-outcomes --frozen python -m research_writing_outcome_spikes.scrub docs/references/research/research-writing-outcomes/live
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

Commit only allowed paths on the named branch. Keep this packet current with
progress, discoveries, decisions, commands, dependency states, evidence, and
blockers. The author cannot accept their own work. Runtime-contract, security, and
product reviewers independently decide each matrix row and all four spike
dispositions.

The coordinator alone updates source ledgers, upstream spike state, product/
program/index records, starter agents, application adapters, normalized
contracts, capability flags, or release scope. No worktree creation, push, merge,
deployment, publication, production mutation, credential collection, or
destructive cleanup is authorized by this packet.
