---
exec_plan_id: DW-EXEC-M1-FIXTURE-CONTRACT
title: Wave 1 deterministic product-demo fixture contract
status: draft
superseded_by: null
owner: fixture-contracts
reviewed_by: []
reviewed_at: null
primary_feature_id: DW-FND-004
supporting_feature_ids: [DW-FND-001, DW-FND-002, DW-FND-003, DW-FND-005]
issue: local:DW-M1-FIXTURE-CONTRACT
created: 2026-07-23
last_updated: 2026-07-23
base_commit: fff1bfd278d550d01de6e8d74f553f45c4003a8c
last_verified_commit: null
branch: codex/contracts/wave1-fixture-corpus
worktree: /Users/tomspencer/dev/deepwork/worktrees/w1-fixture-contract
risk: medium
governed_paths: [internal/fixtures/product-demo/**, docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md]
contract_gates: [SPIKE-STREAM-001, SPIKE-STREAM-002, SPIKE-STREAM-003, SPIKE-HITL-001, SPIKE-CANCEL-001, SPIKE-CHECKPOINT-001, SPIKE-SUBAGENT-001, SPIKE-ARTIFACT-001, SPIKE-MDA-001, SPIKE-FLEET-001, SPIKE-DIRECT-STREAM-001]
decision_gates: [DEC-021, DEC-022, DEC-023, DEC-033, DEC-034, DEC-035]
gate_review_status: unreviewed
gate_reviewed_by: []
gate_reviewed_at: null
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, docs/AGENTS.md, docs/PLANS.md, docs/SECURITY.md, docs/RELIABILITY.md, docs/design-docs/engineering/conventions.md, docs/design-docs/decisions/index.md, docs/product-specs/acceptance-scenarios.md, docs/product-specs/foundations/dw-fnd-001-repository-oss-and-delivery-foundation.md, docs/product-specs/foundations/dw-fnd-002-design-system-shell-and-demo-mode.md, docs/product-specs/foundations/dw-fnd-003-application-service-state-and-security.md, docs/product-specs/foundations/dw-fnd-004-sdk-stream-and-fixture-contracts.md, docs/product-specs/foundations/dw-fnd-005-domain-identity-status-and-audit-model.md, docs/product-specs/quality/dw-qual-001-accessibility-performance-security-testing-and-release.md, docs/exec-plans/active/DW-EXEC-M1-REPOSITORY-SCAFFOLD.md, docs/exec-plans/active/DW-EXEC-M1-TS-PACKAGES-SCAFFOLD.md, docs/exec-plans/completed/DW-EXEC-M1-API-SCAFFOLD.md, docs/exec-plans/completed/DW-EXEC-M1-AGENT-SCAFFOLD.md]
scenario_ids: [AC-DW-FND-004-04, AC-DW-FND-004-05, AC-DW-FND-004-06, AC-DW-FND-001-07, AC-DW-FND-002-06, AC-DW-FND-003-05, AC-DW-FND-005-01]
dispatch_kind: cell
dispatch_ready: false
agent_review_required: true
dependencies: [local:DW-M1-API-001, local:DW-M1-AGENT-001, local:DW-M1-TS-SCAFFOLD]
blockers: []
---

# Wave 1 deterministic product-demo fixture contract

## Purpose and observable result

Create a private, language-neutral, deterministic synthetic corpus and an
install-free validator under `internal/fixtures/product-demo/**`. A later API,
domain, SDK, web, or product-demo cell can consume the same reviewed cases for
source-qualified identities, capability honesty, ordered event semantics,
recovery, terminal state, malformed input, and partial failure without requiring
a provider credential or external network.

This cell is owned by `DW-FND-004`. It contributes the corpus-and-isolation slice
of `AC-DW-FND-004-05`; production reducer/API consumption remains downstream.
The partial-source, unknown-capability, gated-runtime, and source-collision cases
also provide bounded inputs for the other scenario IDs in front matter, but this
cell does not claim those complete application scenarios.

The deliverable is test data and its validator only. It is not an application
stream, source adapter, provider transcript, UI harness, full product demo, API
schema, TypeScript package, or live-contract result.

## Context and orientation

The exact reviewed base is
`fff1bfd278d550d01de6e8d74f553f45c4003a8c`, the branch is
`codex/contracts/wave1-fixture-corpus`, and the worktree is
`/Users/tomspencer/dev/deepwork/worktrees/w1-fixture-contract`.

At this base:

- `local:DW-M1-API-001` is terminal and independently accepted at
  `3fbdb01be06152cc39e50f6378dfb625daed8998`. It exposes only liveness and a
  fixture-only demo status; it has no normalized stream, source adapter,
  persistence, or generated client.
- `local:DW-M1-AGENT-001` is terminal and independently accepted at
  `e991700cb25e5be8020ace8d905c5ecbefa6600e`. It is an independently installable
  package boundary and supplies no production graph, provider event, or live
  fixture contract.
- `local:DW-M1-TS-SCAFFOLD` source is integrated through
  `03b019ab6a5d71e2911a6019013a089cca098101`, but its plan is active again after
  external review found correctness and proof gaps. Its current source-qualified
  identity and capability vocabulary is useful orientation, not a frozen
  executable dependency or authority for this corpus.
- `internal/fixtures/` contains only shared TypeScript configuration ancestors;
  `internal/fixtures/product-demo/` does not exist.
- The four external accelerator packets own only
  `tools/architecture/**`, `tools/worktree/**`,
  `internal/fixtures/{architecture,worktree}/**`,
  `tools/contract-spikes/{langchain,auth}/**`,
  `tools/docs/**`, `internal/fixtures/docs/**`, and their respective research and
  packet paths. This cell is disjoint from all of them.

`DW-FND-004` requires private language-neutral fixtures with deterministic clocks,
IDs, transcripts, capability manifests, and failure cases. `DEC-035` keeps Python
source-adapter conformance in `apps/api` and TypeScript DTO/reducer/client
conformance in `internal/adapter-tests`; both may later consume this corpus, but
neither consumer is implemented here.

## Scope

### In scope

- A versioned JSON corpus with deterministic clocks, source-qualified synthetic
  identities, fixture-owned case IDs, stable ordering, and explicit expected
  assertions.
- A normalized fixture envelope that identifies fixture schema version, evidence
  class, case category, logical clock, source/thread/run scope, ordered records,
  expected assertions, and provenance without becoming the production wire
  schema.
- Evidence-bearing capability manifests with the canonical states `available`,
  `unavailable`, `gated`, `permission-denied`, and `unknown`; fixture evidence may
  describe a simulated case but cannot promote a live runtime capability.
- Positive cases for start, content, tool lifecycle, ordered interrupt,
  checkpoint observation, reconnect, duplicate replay, completion, unknown event,
  malformed input classification, and partial-source failure.
- A source-collision case in which two synthetic sources deliberately reuse the
  same external thread and run strings while retaining distinct qualified keys.
- Intentional negative cases that prove stable validator rule codes for schema,
  ID, clock, ordering, capability, interrupt alignment, hash, scrub, network, and
  expectation failures.
- A standard-library-only read-only validator, deterministic corpus hashes, a
  scrub policy, and deterministic validation/no-external-network evidence.
- Corpus README, machine index, structural schema documents, scenario files,
  negative fixtures, hash manifest, and deterministic validation report wholly
  under `internal/fixtures/product-demo/**`.
- This living ExecPlan and no other documentation.

### Non-goals

- Implementing or changing `apps/api/**`, `packages/agent/**`,
  `packages/{domain,sdk,ui}/**`, `internal/adapter-tests/**`, `apps/web/**`,
  `apps/desktop/**`, root files, generated files, tools, or CI.
- Defining FastAPI/Pydantic production event models, OpenAPI, generated TypeScript,
  domain reducers, SDK transports, React hooks, routes, persistence, demo
  services, worker behavior, Postgres, object storage, or telemetry.
- Copying, modifying, or depending on the external LangChain research packet's
  fixtures. Those remain read-only evidence until independently accepted and
  deliberately mapped by a later adapter cell.
- Inventing provider paths, headers, cursors, status values, event discriminators,
  resume operations, HITL wire payloads, checkpoint/fork calls, or MDA/Fleet
  behavior.
- Claiming live parity, captured-contract parity, application integration,
  reconnect correctness, ordered decision submission, or complete acceptance of
  any scenario from corpus validation alone.
- Editing `docs/exec-plans/index.md`, the program/umbrella/other active plans,
  product specifications, `docs/plans/**`, `docs/proposals/**`,
  `docs/references/**`, external packets, or sibling repositories.

### Permissions and risk boundary

- Allowed paths are exactly `internal/fixtures/product-demo/**` and
  `docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md`.
- No dependency installation, package index access, provider/service access,
  credential, live account, production data, or external network is permitted.
- No destructive operation, migration, release, deployment, publication, push,
  merge, or automatic index/program update is permitted.
- The existing `docs/plans/**` bytes must remain unchanged.
- Risk is medium because the corpus is intended to become a cross-language
  conformance input. Fixture contracts can mislead downstream work if they
  accidentally encode an unverified provider or product wire.
- Required review is independent: SDK/domain contract, API contract, security,
  developer-experience, and product-fixture reviewers. The author cannot mark the
  plan reviewed, set `dispatch_ready: true`, accept gates, or approve its
  implementation.

## Authoritative sources and prerequisites

- Primary product owner:
  `docs/product-specs/foundations/dw-fnd-004-sdk-stream-and-fixture-contracts.md`.
- Supporting boundaries:
  `DW-FND-001` for private credential-free fixtures, `DW-FND-002` for honest demo
  presentation, `DW-FND-003` for service/credential authority, and `DW-FND-005`
  for source-qualified identity/status vocabulary.
- Architecture and safety: `ARCHITECTURE.md`, `docs/SECURITY.md`,
  `docs/RELIABILITY.md`, and
  `docs/design-docs/engineering/conventions.md`.
- Stable acceptance names:
  `docs/product-specs/acceptance-scenarios.md`.
- Terminal package prerequisites are the accepted API and agent cells listed in
  Context. They establish legal package boundaries only; this cell imports
  neither package.
- The active TypeScript source cell is a nonterminal source dependency. Corpus
  implementation may proceed only after independent reviewers confirm that its
  abstract vocabulary does not freeze the active TypeScript defects. Executable
  TS decoding/reduction remains blocked on fresh TS-source acceptance, lock
  integration, and executable verification.
- `docs/exec-plans/index.md` registration is coordinator-owned. The expected
  unindexed-plan diagnostic remains a known handoff gate, not permission for this
  cell to edit the index.

### Open runtime-gate ledger and deterministic fallback

- `SPIKE-STREAM-001` remains open. Reconnect/replay cases model only fixture-owned
  ordered inputs and expected dedupe/hydration assertions; they do not select
  protocol v2, `since`, `Last-Event-ID`, legacy join, or polling behavior.
- `SPIKE-STREAM-002` remains open. No submit or multitask strategy is advertised.
- `SPIKE-STREAM-003` remains open. Case categories are fixture semantics, not
  claims about exact upstream content/tool/checkpoint/interrupt event names.
- `SPIKE-HITL-001` remains open. The ordered-interrupt case preserves aligned
  arrays and repeated action names, but submission/resume stays unavailable.
- `SPIKE-CANCEL-001` remains open. Cancellation is absent or explicitly gated; no
  fixture simulates authoritative cancellation.
- `SPIKE-CHECKPOINT-001` remains open. A checkpoint may be observed as synthetic
  normalized data, while list/fork/stale behavior remains unavailable.
- `SPIKE-SUBAGENT-001` and `SPIKE-ARTIFACT-001` remain open. Specialized subagent
  and artifact capabilities are unavailable; generic unknown-content handling is
  the fallback.
- `SPIKE-MDA-001` and `SPIKE-FLEET-001` remain open. Their manifest entries are
  `gated` or `unknown`, never `available`.
- `SPIKE-DIRECT-STREAM-001` remains open. No browser-direct endpoint, credential,
  cursor, or CORS assumption appears.

## Interfaces and invariants

### Intended corpus layout

```text
internal/fixtures/product-demo/
  README.md
  corpus.json
  hashes.sha256
  validate.py
  schema/
    fixture-envelope.json
    capability-manifest.json
  manifests/
    fixture-source.json
    gated-runtimes.json
  cases/
    start.json
    content.json
    tool.json
    ordered-interrupt.json
    checkpoint.json
    reconnect.json
    replay.json
    completion.json
    unknown.json
    malformed.json
    partial-failure.json
    source-collision.json
  negative/
    matrix.json
    invalid-*.json
  evidence/
    validation-report.json
    no-external-network.json
```

The implementation may combine files only if review preserves one obvious
machine index, independent case identity, deterministic hashes, and the complete
positive/negative matrix. It must not add TypeScript, Python package metadata, a
lock, or a second project.

### Fixture envelope

Every positive case has:

- a format/version owned by the fixture corpus, not the public API;
- a stable `caseId` and semantic case category;
- `evidenceClass: "fixture"` and an unmistakable synthetic marker;
- an integer logical tick plus fixed RFC 3339 UTC timestamps derived from one
  documented epoch, never wall-clock reads;
- stable `fx_`-prefixed source, thread, run, event, interrupt, checkpoint, actor,
  tenant, and workspace values as applicable;
- ordered records with unique fixture record IDs and monotonic fixture sequence;
- an evidence-bearing capability snapshot;
- explicit expected ordered IDs, retained/ignored duplicates, terminal/freshness
  classification, safe error code, or partial-source result as applicable; and
- no endpoint, credential, `authRef`, provider cursor, real repository, customer
  content, plausible production identifier, or external URL.

`case category`, fixture sequence, and expected assertions are test-harness
concepts. A later Pydantic event authority may map them deliberately; no consumer
may serialize these files directly as `/api/v1` merely because the corpus exists.

### Required case semantics

- Start establishes one synthetic source/thread/run identity without implying a
  provider create call.
- Content proves stable chunk/order data without exposing private reasoning.
- Tool proves start/result correlation and bounded untrusted content.
- Ordered interrupt contains repeated action names, aligned request/config arrays,
  stable interrupt version, and no accepted decision or resume payload.
- Checkpoint preserves source/thread/checkpoint identity while fork remains gated.
- Reconnect preserves the last durable projection and a fixture recovery boundary;
  disconnect never means cancel or fail.
- Replay deliberately repeats durable event IDs and states the expected
  de-duplicated order.
- Completion includes an explicit authoritative fixture terminal record; absence,
  timeout, or disconnect cannot infer completion.
- Unknown preserves an unrecognized safe record as observable unknown content
  without promoting a new discriminator.
- Malformed supplies bounded invalid structures and expected stable validator
  errors; raw invalid data is never treated as a passing case.
- Partial failure keeps healthy synthetic source results and a source-qualified
  safe error for the failed source.
- Source collision reuses external thread/run strings across two sources and
  proves distinct source-qualified fixture keys.

### Capability-manifest invariants

Every capability entry records state, observation time, adapter version, contract
version, evidence class, and a safe reason when not available. Fixture cases may
set only deliberately simulated product-demo cells to `available` with
`evidenceClass: "fixture"`. Provider/runtime-specific cells remain `gated`,
`unknown`, or `unavailable`; fixture evidence can never use `live-contract`.

Unknown and permission-denied are not empty success. Gated HITL/checkpoint/stream
operations remain non-callable even when the corpus contains a presentation case.

### Validator and stable diagnostics

`validate.py` uses only the Python standard library, reads only this corpus, emits
stable sorted output, and performs no socket, subprocess, environment-secret, or
wall-clock access. It validates:

- corpus/schema/index integrity and exact version support;
- unique/normalized IDs, fixed clock derivation, sequence/order, and case coverage;
- source qualification and collision behavior;
- capability metadata and fixture/live evidence separation;
- ordered interrupt array alignment and repeated-name preservation;
- expected replay dedupe, terminal authority, unknown/malformed handling, and
  partial-failure assertions;
- exact sorted SHA-256 hashes for all governed data/schema assets;
- scrub rules for credential-shaped field names/content, `authRef`, authorization
  material, private keys, token-like values, operational endpoints, external URLs,
  real-looking repositories/actors, and unsafe path content;
- zero external host/URL entries and an allow-listed standard-library import set;
- positive cases pass, each negative case fails with exactly its declared stable
  rule code, and no expected diagnostic disappears; and
- committed, staged, unstaged, and untracked scope against the exact two governed
  path patterns when `--verify-scope` is used.

Stable rule-code families are `FIXTURE_SCHEMA`, `FIXTURE_ID`, `FIXTURE_CLOCK`,
`FIXTURE_ORDER`, `FIXTURE_CAPABILITY`, `FIXTURE_INTERRUPT`, `FIXTURE_HASH`,
`FIXTURE_SCRUB`, `FIXTURE_NETWORK`, and `FIXTURE_EXPECTATION`. Review may refine
suffixes without changing the required failure classes.

The deterministic validation report records corpus version/digest, sorted case
IDs, rule-code coverage, scrub match count, external URL/host count, and validator
import allow-list. It contains no runtime timestamp. The no-external-network
evidence states only what this read-only validator proves; it cannot be reused as
evidence that future API, browser, or provider consumers made no network calls.

## Milestones

### Milestone 1 — Freeze the fixture-only contract

Create the README, corpus index, structural schema documents, fixed clock/ID
policy, capability manifests, and case inventory. Record every gate/fallback next
to the affected case and keep fixture field names distinct from public wire
authority.

Acceptance:

- all declared files are under `internal/fixtures/product-demo/**`;
- every required positive case is indexed exactly once;
- the two-source collision and capability-state matrices are explicit; and
- independent API/domain/SDK/security reviewers confirm no provider wire or live
  capability was invented.

### Milestone 2 — Add positive and intentional negative cases

Author every required synthetic scenario and one negative fixture per stable
failure class. Keep data bounded, synthetic, source-qualified, and deterministically
ordered.

Acceptance:

- positive coverage includes start/content/tool/ordered interrupt/checkpoint/
  reconnect/replay/completion/unknown/malformed/partial failure/source collision;
- replay and repeated-action cases have explicit expected order;
- malformed fixtures stay only in the negative harness; and
- scrub review finds no credential, real identity, endpoint, repository content,
  external URL, or production-like payload.

### Milestone 3 — Prove deterministic validation

Implement the standard-library validator, read-only scope check, deterministic
hash update mode, read-only validation mode, and stable evidence reports.

Acceptance:

- two read-only runs produce byte-identical output and no diff;
- each negative fixture fails only with its declared rule code;
- hash, scrub, and no-external-network checks are part of the required command;
- all committed/staged/unstaged/untracked paths are within the exact allow-list;
  and
- `docs/plans/**` hashes remain unchanged from the base.

### Milestone 4 — Independent review handoff

Update the living sections and retain exact commands/results, corpus digest, file
inventory, known unindexed-plan diagnostic, gate ledger, and downstream deferrals.
Stop at independent Agent Review.

Acceptance:

- the implementation author does not approve, index, merge, or begin consumer
  work;
- reviewers accept or return bounded rework against only the two governed paths;
  and
- API adapters, TypeScript consumers, product-demo services, and live parity
  remain separate reviewed cells.

## Progress

- [x] 2026-07-23 AEST — Draft candidate authored at exact base/branch/worktree;
  no fixture implementation performed.
- [ ] Independent plan review confirms ownership, disjoint paths, gates,
  dependencies, case semantics, and install-free validation.
- [ ] Milestone 1 complete; exact fixture contract and inventory retained.
- [ ] Milestone 2 complete; positive and negative corpus retained.
- [ ] Milestone 3 complete; deterministic validator and evidence retained.
- [ ] Milestone 4 complete; fresh independent implementation review handed off.

## Surprises & Discoveries

- 2026-07-23 AEST — The current TypeScript source cell was reopened after external
  review. Evidence:
  `docs/exec-plans/active/DW-EXEC-M1-TS-PACKAGES-SCAFFOLD.md`.
  Consequence: this corpus may use canonical specification vocabulary but cannot
  freeze or claim executable parity with the active TypeScript implementation.
- 2026-07-23 AEST — The current docs index contains all existing active plans and
  passes before this candidate is added. Consequence: this cell must retain the
  expected unindexed-plan diagnostic and leave index registration to the
  coordinator.
- 2026-07-23 AEST — The existing external fixture paths are
  `internal/fixtures/{architecture,worktree,docs}/**`. Consequence:
  `internal/fixtures/product-demo/**` is collision-free and must remain exact.

## Decision Log

- 2026-07-23 AEST — Decision: make the corpus JSON and keep its validator
  standard-library-only. Rationale: Python and TypeScript conformance harnesses
  need one neutral data source without a third lockfile. Consequence: consumers
  import data, not this validator as product code.
- 2026-07-23 AEST — Decision: distinguish fixture envelope semantics from the
  future production event wire. Rationale: Pydantic/OpenAPI/event authority and
  exact upstream event names are not established in this cell. Consequence:
  later API work maps reviewed cases deliberately rather than serializing fixture
  JSON as `/api/v1`.
- 2026-07-23 AEST — Decision: include gated interrupt/checkpoint/reconnect cases
  without enabling their live operations. Rationale: deterministic fallback and
  presentation states need coverage while runtime gates stay open. Consequence:
  manifests remain gated/unknown and no provider request is encoded.
- 2026-07-23 AEST — Decision: keep validator evidence deterministic and
  claim-limited. Rationale: wall-clock stamps and broad "no network" claims would
  make hashes unstable and overstate proof. Consequence: reports describe only
  corpus and validator properties; consumer network proof is downstream.

## Detailed implementation approach

1. Reconfirm exact base ancestry, branch, worktree, terminal API/agent plans,
   active TS plan, and clean scope before editing.
2. Create the documented directory layout and corpus index with fixed version,
   epoch, ID prefixes, case order, and capability manifests.
3. Add small positive cases, then the negative rule-code matrix. Do not derive
   payloads from provider docs, external research fixtures, prototype network
   captures, or live services.
4. Implement `validate.py` as a read-only standard-library checker. Add an
   explicit maintainer-only hash/report update mode that writes only the two
   deterministic evidence files; ordinary `--check` never writes.
5. Run the exact install-free validation below twice, confirm scope and legacy
   preservation, update this plan, and commit only the two governed path sets.
6. Hand the commit to fresh independent review. Do not run package tooling or
   start API/web/product-demo processes.

## Validation and proof

All future implementation checks run from repository root without dependency
installation:

```text
test "$(git branch --show-current)" = "codex/contracts/wave1-fixture-corpus"
git merge-base --is-ancestor fff1bfd278d550d01de6e8d74f553f45c4003a8c HEAD
PYTHONDONTWRITEBYTECODE=1 python3 internal/fixtures/product-demo/validate.py --check
PYTHONDONTWRITEBYTECODE=1 python3 internal/fixtures/product-demo/validate.py --check
PYTHONDONTWRITEBYTECODE=1 python3 internal/fixtures/product-demo/validate.py --verify-scope --repo . --base fff1bfd278d550d01de6e8d74f553f45c4003a8c --include-untracked
python3 -B tools/docs/generate.py --check
python3 -B tools/docs/check.py
git diff --check
git diff --check fff1bfd278d550d01de6e8d74f553f45c4003a8c...HEAD
git diff --name-only fff1bfd278d550d01de6e8d74f553f45c4003a8c...HEAD
git status --short
```

Required observations:

- each validator run reports the same corpus digest, sorted case inventory, zero
  scrub matches, zero external hosts/URLs, full negative rule-code coverage, and
  no writes;
- `--verify-scope` fails on any committed, staged, unstaged, or untracked path
  outside `internal/fixtures/product-demo/**` and this plan;
- generated docs remain drift-free;
- docs validation has no failure other than the exact coordinator-owned
  unindexed active-plan diagnostic until the index is updated elsewhere;
- base-relative and worktree whitespace checks pass;
- the final implementation commit contains only governed paths; and
- the final author handoff is clean.

Retain in this plan:

- exact command, exit code, and concise output;
- case/file inventory and corpus SHA-256 digest;
- positive-case and negative-rule-code coverage;
- scrub/no-external-network report summary;
- base-relative changed-file inventory and scope result;
- exact known unindexed-plan diagnostic;
- fresh independent reviewer identity/result; and
- explicit statement that no API, agent, TS consumer, app integration, provider
  contract, live parity, external network, credential, or `docs/plans/**` change
  occurred.

The plan-authoring step may run only documentation/static checks because the
fixture validator does not yet exist. It must commit this one plan file only and
report the expected unindexed-plan check without editing the index.

## Idempotence, rollback, and recovery

All corpus inputs use fixed clocks and IDs. `--check` is read-only and rerunnable;
the explicit hash/report update mode is deterministic, then a second `--check`
must produce no diff. A partial validator failure leaves all source files and
diagnostics intact. Recovery changes only the invalid governed fixture or this
plan; it never weakens a rule, deletes a negative case, changes external evidence,
or edits a consumer to make the corpus pass.

Before integration, rollback is one reviewed revert of only this cell's commit.
There is no database, external run, registry, deployment, credential, or live
state to clean up. If a later accepted production schema conflicts with this
corpus, create a versioned corpus migration or superseding reviewed plan; do not
rewrite prior evidence in place or claim historical live parity.

`SPIKE-STREAM-001` and every other gate in front matter retains its documented
fallback. A failed or delayed gate does not block fixture validation; it blocks
the corresponding live/runtime claim. A failed TS re-review blocks TypeScript
consumer parity, not the neutral corpus.

## Rollout and handoff

There is no production rollout. After fresh independent acceptance, hand the
exact fixture commit, corpus digest, validation transcript, gate ledger, known
index diagnostic, and clean scope proof to the coordinator.

Downstream reviewed cells may then:

1. make `apps/api` Pydantic/source conformance consume the corpus;
2. make `internal/adapter-tests` and accepted `packages/domain`/`packages/sdk`
   decode and reduce the same cases;
3. compose the API-backed product demo and prove real local-service isolation; and
4. map accepted external contract transcripts only after their named spikes pass.

Those cells own generated contracts, package locks/tooling, application/network
isolation, fixture/live parity, responsive UI proof, and scenario completion.
This issue hands off at Agent Review/Human Review and cannot declare Done,
register itself in the index, or start consumer implementation.

## Outcomes & Retrospective

Pending implementation and independent review. At completion, compare the actual
case/rule inventory and corpus digest with this purpose, list every deviation and
deferred consumer, record the exact accepted commit, and leave all live runtime
gates visibly open unless independently accepted elsewhere.
