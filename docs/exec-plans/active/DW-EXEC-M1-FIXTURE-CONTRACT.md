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
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, docs/AGENTS.md, docs/PLANS.md, docs/SECURITY.md, docs/RELIABILITY.md, docs/design-docs/engineering/conventions.md, docs/design-docs/decisions/index.md, docs/product-specs/acceptance-scenarios.md, docs/product-specs/foundations/dw-fnd-001-repository-oss-and-delivery-foundation.md, docs/product-specs/foundations/dw-fnd-002-design-system-shell-and-demo-mode.md, docs/product-specs/foundations/dw-fnd-003-application-service-state-and-security.md, docs/product-specs/foundations/dw-fnd-004-sdk-stream-and-fixture-contracts.md, docs/product-specs/foundations/dw-fnd-005-domain-identity-status-and-audit-model.md, docs/product-specs/quality/dw-qual-001-accessibility-performance-security-testing-and-release.md, docs/exec-plans/active/DW-EXEC-M1-REPOSITORY-SCAFFOLD.md, docs/exec-plans/completed/DW-EXEC-M1-API-SCAFFOLD.md, docs/exec-plans/completed/DW-EXEC-M1-AGENT-SCAFFOLD.md]
scenario_ids: [AC-DW-FND-004-04, AC-DW-FND-004-05, AC-DW-FND-004-06, AC-DW-FND-001-07, AC-DW-FND-002-06, AC-DW-FND-003-05, AC-DW-FND-005-01]
dispatch_kind: cell
dispatch_ready: false
agent_review_required: true
dependencies: [local:DW-M1-API-001, local:DW-M1-AGENT-001]
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

The exact product/dependency base is
`fff1bfd278d550d01de6e8d74f553f45c4003a8c`, the branch is
`codex/contracts/wave1-fixture-corpus`, and the worktree is
`/Users/tomspencer/dev/deepwork/worktrees/w1-fixture-contract`.
This bounded plan-rework task starts from clean commit
`d2cb53c2301a6dd6c5c5b402990314dbebfff825`. That commit is a plan-authoring
base, not implementation authority. The exact independently accepted plan
candidate must receive a separate coordinator-owned reviewed/dispatch transition
before any fixture implementation starts.

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
  external review found correctness and proof gaps. It is not a dependency,
  blocker, or authority for this cell. The corpus uses only canonical
  product-specification vocabulary, and accepted TypeScript code is a downstream
  consumer.
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
  checkpoint observation, reconnect, duplicate replay, fixed-logical-tick delay,
  completion, unknown event, malformed input classification, and partial-source
  failure.
- A source-collision case in which two synthetic sources deliberately reuse the
  same external thread and run strings while retaining distinct qualified keys.
- Intentional negative cases that prove stable validator rule codes for schema,
  ID, clock, ordering, capability, interrupt alignment, hash, scrub, network, and
  expectation failures, including an exact logical-delay arithmetic mismatch
  under the clock family.
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

- Plan-author/rework authority is exactly
  `docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md`.
- After the exact draft plan candidate is independently accepted, the
  coordinator alone may perform the pre-implementation reviewed/dispatch
  transition described below. That transition may change only this plan and
  `docs/exec-plans/index.md`; it is not fixture implementation authority.
- Implementation-author allowed paths, starting only from the exact reviewed
  dispatch commit handed off by the coordinator, are exactly
  `internal/fixtures/product-demo/**` and
  `docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md`.
- Any post-implementation plan/index status transition is coordinator-only and
  has its own narrower accepted-implementation-to-transition range and proof
  scope. Neither coordinator transition broadens implementation authority or
  front-matter `governed_paths`.
- No dependency installation, package index access, provider/service access,
  credential, live account, production data, or external network is permitted.
- No destructive operation, migration, release, deployment, publication, push,
  merge, or automatic index/program update is permitted.
- The existing `docs/plans/**` bytes must remain unchanged.
- Risk is medium because the corpus is intended to become a cross-language
  conformance input. Fixture contracts can mislead downstream work if they
  accidentally encode an unverified provider or product wire.
- Required review is independent: SDK/domain contract, API contract, security,
  developer-experience, and product-fixture reviewers. The plan or implementation
  author cannot record reviewer identity, mark the plan reviewed, set
  `dispatch_ready: true`, accept gates, edit the index, or approve the
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
- There is no TypeScript source dependency. Corpus implementation relies on the
  canonical specifications and decisions, not the current package implementation.
  Executable TS decoding/reduction remains downstream and cannot claim parity
  until fresh TS-source acceptance, lock integration, and executable verification
  are independently terminal.
- `docs/exec-plans/index.md` registration is coordinator-owned. The complete
  draft/review diagnostic set, including the unindexed-plan error, remains an
  expected plan-candidate result. After independent plan acceptance, the
  coordinator must clear all eight diagnostics and make the plan dispatch-ready
  before implementation; the diagnostics are not permission for either author to
  edit the index or reviewer fields.

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
  update_evidence.py
  validate.py
  verify_scope.py
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
    logical-delay.json
    completion.json
    unknown.json
    malformed-input.json
    partial-failure.json
    source-collision.json
  negative/
    matrix.json
    invalid-logical-delay.json
    invalid-logical-delay-visibility.json
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
- an integer logical tick plus fixed RFC 3339 UTC timestamps derived from
  `tickEpoch: "2026-07-23T00:00:00Z"` and `tickDurationMs: 250`, where timestamp
  at tick `N` is exactly epoch plus `N * 250` milliseconds, never a wall-clock
  read;
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
- Logical delay uses only the corpus clock. The case enqueues one content record
  at tick `41`, declares `delayTicks: 3`, releases it at tick `44`, and completes
  at tick `45`. The derived enqueue, last-pre-release, release, and completion
  timestamps are exactly `2026-07-23T00:00:10.250Z`,
  `2026-07-23T00:00:10.750Z`, `2026-07-23T00:00:11.000Z`, and
  `2026-07-23T00:00:11.250Z`. Its exact expectations assert that the content
  record is absent through tick `43`, becomes visible exactly once at tick `44`,
  and that visible record IDs at ticks `40`, `43`, `44`, and `45` are respectively
  `[fx_record_delay_start]`, `[fx_record_delay_start]`,
  `[fx_record_delay_start, fx_record_delay_content]`, and
  `[fx_record_delay_start, fx_record_delay_content,
  fx_record_delay_complete]`. The deterministic release order is
  `fx_record_delay_start`, `fx_record_delay_content`,
  `fx_record_delay_complete`; no sleep, timeout, monotonic-clock read, performance
  target, or real elapsed-time claim is permitted.
- Completion includes an explicit authoritative fixture terminal record; absence,
  timeout, or disconnect cannot infer completion.
- Unknown preserves an unrecognized safe record as observable unknown content
  without promoting a new discriminator.
- Malformed input uses a schema-valid fixture envelope whose bounded `input`
  member contains the deliberately malformed upstream-like value and whose
  expectation names the safe classification. This positive case proves
  classification without making invalid corpus structure pass. Raw
  envelope/schema-invalid documents live only under `negative/` and must fail
  with their declared validator rule code.
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

### Pure corpus validator and stable diagnostics

`validate.py` uses only the Python standard library, reads only this corpus, emits
stable sorted output, and performs no Git inspection, socket, subprocess,
environment read, or wall-clock access. It validates:

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
  rule code, and no expected diagnostic disappears.

Stable rule-code families are `FIXTURE_SCHEMA`, `FIXTURE_ID`, `FIXTURE_CLOCK`,
`FIXTURE_ORDER`, `FIXTURE_CAPABILITY`, `FIXTURE_INTERRUPT`, `FIXTURE_HASH`,
`FIXTURE_SCRUB`, `FIXTURE_NETWORK`, and `FIXTURE_EXPECTATION`. Review may refine
suffixes without changing the required failure classes.

`negative/invalid-logical-delay.json` is mandatory in addition to the
one-per-family matrix. It keeps the envelope otherwise valid but declares
enqueue tick `41`, `delayTicks: 3`, and release tick `43`; it must fail with
exactly `FIXTURE_CLOCK_DELAY_MISMATCH` because `41 + 3 != 43`.
`negative/invalid-logical-delay-visibility.json` keeps the release arithmetic
valid but includes the content record in expected visibility at tick `43`; it
must fail with exactly `FIXTURE_EXPECTATION_DELAY_VISIBILITY`. These are
logical-clock contract checks and must never sample or wait for wall time.

The deterministic validation report records corpus version/digest, sorted case
IDs, rule-code coverage, scrub match count, external URL/host count, and validator
import allow-list. It contains no runtime timestamp. The no-external-network
evidence states only what this read-only validator proves; it cannot be reused as
evidence that future API, browser, or provider consumers made no network calls.

### Linked-worktree-safe Git scope runner and proof scopes

`verify_scope.py` is a separate standard-library-only repository-policy helper.
It contains no corpus validation and may invoke only a fixed `git` executable
through `subprocess.run` without a shell. It accepts the repository path, one of
the two named proof scopes below, and exact full base and candidate commits, then:

1. resolves the worktree root with `git -C <repo> rev-parse --show-toplevel`;
2. resolves and records the linked-worktree-safe absolute Git directory and
   common directory with `git rev-parse --path-format=absolute --git-dir` and
   `--git-common-dir`, instead of assuming `.git` is a directory;
3. reads committed and staged/unstaged name-status records using NUL-delimited
   Git output so both old and new paths of copies/renames are checked;
4. reads untracked paths with
   `git ls-files --others --exclude-standard -z`; and
5. rejects symbolic or nonexistent commit arguments and rejects absolute,
   parent-traversing, undecodable, or out-of-allow-list paths.

The runner has exactly two post-dispatch proof scopes:

1. `implementation` compares the exact reviewed dispatch commit handed off by
   the coordinator with the exact full
   implementation candidate commit. Its allow-list is exactly
   `internal/fixtures/product-demo/**` plus
   `docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md`.
2. `coordinator-transition` compares the exact accepted implementation commit
   with the exact full coordinator transition commit. Its allow-list is exactly
   `docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md` plus
   `docs/exec-plans/index.md`.

Both scopes cover their explicit committed range plus staged changes, unstaged
changes, and untracked files independently. The runner rejects a candidate that
is not the checked-out `HEAD`, records both full commits and the selected
allow-list, and names every state and path; an empty state remains explicit. The
coordinator scope is not implementation permission: no implementation agent may
edit `docs/exec-plans/index.md`, select the coordinator transition as its
implementation proof, or include index changes in the implementation candidate.
The coordinator may use the second scope only after independent acceptance of the
first scope's exact implementation commit. The pre-implementation plan transition
cannot rely on this not-yet-implemented runner and instead uses the fixed Git and
docs commands below. The runner performs no network access, arbitrary command
execution, corpus mutation, or Git mutation.

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
  reconnect/replay/logical delay/completion/unknown/malformed-input
  classification/partial failure/source collision;
- `corpus.json` indexes exactly those 13 positive case files once each, while
  `negative/matrix.json` indexes exactly 12 single-code negative files: one for
  each of the 10 stable rule-code families plus the two mandatory logical-delay
  negatives;
- replay and repeated-action cases have explicit expected order;
- logical delay uses the exact tick-41 plus three ticks equals tick-44 release
  model, proves absence through tick 43 and one-time visibility from tick 44, and
  has the exact clock-mismatch and early-visibility negative diagnostics;
- the positive malformed-input case has a schema-valid envelope and expected safe
  classification, while raw schema-invalid fixtures stay only under `negative/`;
  and
- scrub review finds no credential, real identity, endpoint, repository content,
  external URL, or production-like payload.

### Milestone 3 — Prove deterministic validation

Implement the pure standard-library corpus validator, a separate deterministic
evidence writer, the separate linked-worktree-safe Git scope runner, and stable
evidence reports.

Acceptance:

- two consecutive `update_evidence.py --write` runs report the same target
  SHA-256 values, and the second reports no updated file;
- the following `update_evidence.py --check` independently renders every target
  twice in memory, proves those byte sets identical, and proves they match disk;
- each negative fixture fails only with its declared rule code;
- hash, scrub, and no-external-network checks are part of the required command;
- corpus validation invokes no subprocess and reads no Git or environment state;
- the explicit evidence writer is the only corpus helper that may update hashes
  and deterministic reports;
- the Git scope runner resolves linked-worktree metadata through fixed Git
  commands and never imports or mutates the corpus;
- the exact reviewed-dispatch-to-implementation-candidate committed range and
  every staged, unstaged, and untracked path are within the `implementation`
  allow-list; and
- `docs/plans/**` hashes remain unchanged from the base.

### Milestone 4 — Independent review handoff

Update the living sections and retain exact commands/results, corpus digest, file
inventory, the complete draft-state docs-check diagnostic set, gate ledger, and
downstream deferrals. Stop at independent Agent Review.

Acceptance:

- the implementation author does not approve, index, merge, or begin consumer
  work;
- reviewers accept or return bounded rework against only the two governed paths;
- an accepted plan review hands the coordinator the exact accepted draft-plan
  commit and the metadata/index transition needed before initial dispatch;
- the reviewed dispatch commit exists before implementation and is the exact base
  handed to the implementation author;
- an accepted implementation review later hands the coordinator the exact
  accepted implementation commit for any completion/status transition;
- the coordinator transition compares that accepted implementation commit with
  its exact transition commit and changes only this plan plus
  `docs/exec-plans/index.md`; and
- API adapters, TypeScript consumers, product-demo services, and live parity
  remain separate reviewed cells.

## Progress

- [x] 2026-07-23 AEST — Draft candidate authored at exact base/branch/worktree;
  no fixture implementation performed.
- [x] 2026-07-23 AEST — Independent plan review returned four bounded findings;
  plan-only rework reconciled malformed-input semantics, split corpus/scope
  validation, removed the nonterminal TS machine dependency, and documented the
  complete draft-to-reviewed docs transition. Fresh review remains pending.
- [x] 2026-07-23 AEST — Final plan-only review finding resolved: evidence update
  now has an exact two-write/zero-second-update proof followed by a double-render
  byte comparison against disk. Fresh review remains pending.
- [x] 2026-07-23 AEST — Final independent scope finding resolved: implementation
  proof is reviewed-dispatch-to-exact-candidate with fixture/plan paths only,
  while a later coordinator transition is
  accepted-implementation-to-exact-transition with plan/index paths only.
  Implementation agents remain forbidden from editing the index. Fresh review
  remains pending.
- [x] 2026-07-23 AEST — Bounded rework from
  `d2cb53c2301a6dd6c5c5b402990314dbebfff825` removes the circular initial
  dispatch transition and adds the DW-FND-004 fixed-logical-tick delay plus its
  exact negative coverage. Fresh independent plan review remains pending; no
  fixture implementation performed.
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
  Consequence: canonical specifications are sufficient for this neutral corpus;
  the TS cell is neither a dependency nor a blocker, and executable TS parity is
  a downstream claim.
- 2026-07-23 AEST — The current docs index contains all existing active plans and
  passes before this candidate is added. Consequence: this cell must retain all
  eight expected draft/review diagnostics and leave review metadata plus index
  registration to independent reviewers/the coordinator.
- 2026-07-23 AEST — The existing external fixture paths are
  `internal/fixtures/{architecture,worktree,docs}/**`. Consequence:
  `internal/fixtures/product-demo/**` is collision-free and must remain exact.
- 2026-07-23 AEST — `DW-FND-004` explicitly requires latency and failure cases,
  while its fixture evidence remains below live-contract evidence. Consequence:
  this corpus includes a fixed logical-delay schedule with exact tick assertions
  and negative arithmetic/visibility diagnostics, but claims no wall-clock,
  performance, provider, transport, or application latency result.
- 2026-07-23 AEST — At plan commit
  `5b55c65aec90422a85959d3ba53f04eaa216b286`,
  `python3 -B tools/docs/check.py` reported exactly these eight draft/review
  diagnostics and no others:

  ```text
  active ExecPlan is not indexed: docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md
  docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md has unsupported active ExecPlan status 'draft'; expected reviewed or active
  docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md requires independent non-owner reviewer metadata
  docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md requires completed gate reviewer metadata
  docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md metadata reviewed_at must be YYYY-MM-DD
  docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md metadata gate_reviewed_at must be YYYY-MM-DD
  docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md metadata last_verified_commit must name an existing full commit
  docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md gate_review_status must be reviewed-with-gates for its gate arrays
  ```

  Consequence: the author keeps truthful draft metadata and
  `dispatch_ready: false`; every diagnostic must be cleared by the independent
  review/coordinator transition below before dispatch.

## Decision Log

- 2026-07-23 AEST — Decision: make the corpus JSON and keep its validator
  standard-library-only. Rationale: Python and TypeScript conformance harnesses
  need one neutral data source without a third lockfile. Consequence: consumers
  import data, not this validator as product code.
- 2026-07-23 AEST — Decision: separate corpus validation from Git scope
  enforcement. Rationale: a deterministic content validator must not acquire
  subprocess/repository authority, while linked worktrees require Git-aware scope
  inspection. Consequence: `validate.py` is pure and `verify_scope.py` invokes
  only fixed, NUL-delimited Git queries without a shell.
- 2026-07-23 AEST — Decision: use a schema-valid positive envelope for malformed
  input classification. Rationale: a positive corpus case cannot simultaneously
  be schema-invalid and expected to pass. Consequence: raw invalid envelopes exist
  only as declared negative fixtures.
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
- 2026-07-23 AEST — Decision: model required fixture latency as logical delay
  with a 250-millisecond timestamp derivation unit, enqueue tick 41, three delay
  ticks, and release tick 44. Rationale: DW-FND-004 requires a latency case but
  deterministic corpus validation cannot sample elapsed time. Consequence:
  release arithmetic, pre-release absence, and one-time visibility are exact
  assertions with exact negative rule codes; performance remains downstream.
- 2026-07-23 AEST — Decision: use distinct implementation and coordinator
  transition scope proofs. Rationale: the fixture implementation allow-list must
  exclude the coordinator-owned index, while the reviewed metadata/index
  transitions necessarily may change it. Consequence: the coordinator first
  promotes an independently accepted draft-plan commit to a reviewed,
  dispatch-ready commit using only plan/index paths; implementation then proves
  only the reviewed-dispatch-to-candidate fixture/plan range. Any later
  post-implementation metadata transition starts from the independently accepted
  implementation commit and remains plan/index only.

## Detailed implementation approach

1. Before fixture implementation, require the exact independently accepted plan
   candidate and the exact coordinator-owned reviewed dispatch commit described
   below. Reconfirm that the dispatch commit descends from the accepted plan
   candidate, that the original product/dependency base
   `fff1bfd278d550d01de6e8d74f553f45c4003a8c` remains an ancestor, and that
   branch, worktree, terminal API/agent dependencies, no TS machine dependency,
   and clean scope still match.
2. Create the documented directory layout and corpus index with fixed version,
   epoch, ID prefixes, case order, and capability manifests.
3. Add small positive cases, including the schema-valid malformed-input
   classification envelope and the exact logical-delay case, then add raw invalid
   documents only through the negative rule-code matrix, including
   `invalid-logical-delay.json`. Do not derive payloads from provider docs,
   external research fixtures, prototype network captures, or live services.
4. Implement `validate.py` as a pure read-only standard-library checker that
   never writes or invokes a subprocess.
5. Implement `update_evidence.py` as the explicit maintainer-only deterministic
   writer for the hash manifest and two evidence reports. It performs no Git,
   network, environment-secret, or wall-clock access. `--write` renders target
   bytes, atomically replaces only changed targets, prints each target SHA-256,
   and prints a sorted `updated_files` list. `--check` performs two independent
   in-memory renders, byte-compares them, byte-compares the result with every
   on-disk target, prints the same sorted target digests plus
   `render_passes=2`, `render_byte_identical=true`, and
   `disk_byte_identical=true`, and writes nothing. Either mode exits nonzero on
   disagreement.
6. Implement `verify_scope.py` separately with fixed, shell-free Git queries,
   linked-worktree-safe root/Git-directory discovery, and the two exact proof
   scopes above. The implementation agent may invoke only `--scope
   implementation` and may not edit the index.
7. Run the exact install-free corpus and documentation validation below twice,
   confirm legacy preservation, update this plan, and commit only the
   implementation-governed fixture/plan paths.
8. Resolve and retain the exact full implementation candidate commit, rerun the
   read-only `implementation` scope proof from the exact reviewed dispatch commit
   to that candidate, require a clean worktree, and hand that exact commit to
   fresh independent review. Do not run package tooling or start
   API/web/product-demo processes.

## Validation and proof

The current plan-authoring rework runs only these static checks from repository
root. `tools/docs/check.py` must exit `1` with exactly the retained eight
draft/review diagnostics; every other command must exit `0`. The exact candidate
range must contain only this plan:

```text
test "$(git branch --show-current)" = "codex/contracts/wave1-fixture-corpus"
test "$(git rev-parse HEAD^)" = "d2cb53c2301a6dd6c5c5b402990314dbebfff825"
git merge-base --is-ancestor fff1bfd278d550d01de6e8d74f553f45c4003a8c HEAD
python3 -B tools/docs/generate.py --check
python3 -B tools/docs/check.py
git diff --check d2cb53c2301a6dd6c5c5b402990314dbebfff825 HEAD
git diff --name-only d2cb53c2301a6dd6c5c5b402990314dbebfff825 HEAD
test -z "$(git status --porcelain)"
```

All future implementation checks run from repository root without dependency
installation and only after the exact reviewed dispatch commit is handed off:

```text
test "$(git branch --show-current)" = "codex/contracts/wave1-fixture-corpus"
git merge-base --is-ancestor fff1bfd278d550d01de6e8d74f553f45c4003a8c HEAD
PYTHONDONTWRITEBYTECODE=1 python3 internal/fixtures/product-demo/update_evidence.py --write
PYTHONDONTWRITEBYTECODE=1 python3 internal/fixtures/product-demo/update_evidence.py --write
PYTHONDONTWRITEBYTECODE=1 python3 internal/fixtures/product-demo/update_evidence.py --check
PYTHONDONTWRITEBYTECODE=1 python3 internal/fixtures/product-demo/validate.py --check
PYTHONDONTWRITEBYTECODE=1 python3 internal/fixtures/product-demo/validate.py --check
python3 -B tools/docs/generate.py --check
python3 -B tools/docs/check.py
git diff --check
git status --short
```

After committing only the implementation-governed fixture/plan paths, run the
candidate proof against the exact commit handed to review:

```text
implementation_commit="$(git rev-parse HEAD)"
reviewed_dispatch_commit="<exact 40-character coordinator dispatch commit>"
test "${#reviewed_dispatch_commit}" -eq 40
git cat-file -e "${reviewed_dispatch_commit}^{commit}"
test "${#implementation_commit}" -eq 40
git cat-file -e "${implementation_commit}^{commit}"
git merge-base --is-ancestor "$reviewed_dispatch_commit" "$implementation_commit"
PYTHONDONTWRITEBYTECODE=1 python3 internal/fixtures/product-demo/verify_scope.py --repo . --scope implementation --base "$reviewed_dispatch_commit" --candidate "$implementation_commit" --include-untracked
git diff --check "$reviewed_dispatch_commit" "$implementation_commit"
git diff --name-only "$reviewed_dispatch_commit" "$implementation_commit"
test -z "$(git status --porcelain)"
```

Required observations:

- both `--write` runs print identical sorted target SHA-256 values; the second
  prints an empty `updated_files` list;
- `update_evidence.py --check` reports two byte-identical in-memory render passes
  and byte identity with all on-disk evidence targets, then writes nothing;
- each validator run reports the same corpus digest, sorted case inventory, zero
  scrub matches, zero external hosts/URLs, full negative rule-code coverage, and
  no writes or subprocess invocation;
- validator output proves the logical-delay release equation `41 + 3 = 44`,
  absence through tick `43`, one-time visibility at tick `44`, completion at tick
  `45`, exact `FIXTURE_CLOCK_DELAY_MISMATCH` and
  `FIXTURE_EXPECTATION_DELAY_VISIBILITY` negative coverage, and zero wall-clock
  reads or waits;
- the `implementation` scope runner records the exact reviewed base and exact
  full implementation candidate commit, reports linked worktree/common Git
  directories, and fails on any committed, staged, unstaged, or untracked path
  outside `internal/fixtures/product-demo/**` and this plan;
- generated docs remain drift-free;
- before independent review/index transition, docs validation reports exactly the
  eight draft/review diagnostics retained above and no others;
- base-relative and worktree whitespace checks pass;
- the exact implementation candidate commit contains only fixture/plan governed
  paths, contains no `docs/exec-plans/index.md` change, and is the commit handed
  to review; and
- the final author handoff is clean.

Retain in this plan:

- exact command, exit code, and concise output;
- case/file inventory and corpus SHA-256 digest;
- positive-case and negative-rule-code coverage, including both logical-delay
  diagnostics;
- scrub/no-external-network report summary;
- exact implementation commit, base-relative changed-file inventory, and
  `implementation` scope result;
- exact complete docs-check diagnostic set before transition and the later green
  result;
- fresh independent reviewer identity/result; and
- explicit statement that no API, agent, TS consumer, app integration, provider
  contract, live parity, external network, credential, or `docs/plans/**` change
  occurred.

The plan-authoring step may run only documentation/static checks because the
fixture validator does not yet exist. It must commit this one plan file only,
prove the exact range from
`d2cb53c2301a6dd6c5c5b402990314dbebfff825`, and report all eight expected
draft/review diagnostics without editing the index or claiming review.

### Required reviewed metadata and index transition before dispatch

This author/rework commit deliberately keeps `status: draft`,
`dispatch_ready: false`, empty reviewer fields, null review dates, null
`last_verified_commit`, and `gate_review_status: unreviewed`. The independent
plan reviewer reviews the exact plan-only candidate commit, not an implementation
commit. After acceptance, the coordinator—not the plan or implementation
author—must make one pre-implementation reviewed/dispatch transition that:

1. sets `status: reviewed`;
2. records at least one independent non-owner in `reviewed_by` and the actual
   `reviewed_at` date;
3. records `gate_review_status: reviewed-with-gates`, independent
   `gate_reviewed_by`, and the actual `gate_reviewed_at` date without closing the
   open runtime gates;
4. records the exact independently accepted draft-plan candidate as the existing
   full
   `last_verified_commit`;
5. adds this plan to `docs/exec-plans/index.md` in the coordinator-owned change;
6. sets `dispatch_ready: true` in the same reviewed transition, only after
   confirming `local:DW-M1-API-001` and `local:DW-M1-AGENT-001` remain terminal,
   `blockers: []` remains truthful, and every open gate retains its documented
   fallback;
7. leaves `base_commit`, `governed_paths`, `dependencies`, contract/decision gate
   arrays, risk, issue, and author permissions unchanged;
8. records in the plan body the exact accepted plan commit, independent plan
   verdict, reviewed metadata values, exact command results, and the exact
   two-file transition inventory; and
9. commits only this plan and `docs/exec-plans/index.md`, then hands the exact
   reviewed dispatch commit to the implementation author as the sole starting
   authority.

The coordinator proves that transition without relying on the not-yet-created
fixture scope runner:

```text
accepted_plan_commit="<exact independently accepted 40-character plan commit>"
test "${#accepted_plan_commit}" -eq 40
git cat-file -e "${accepted_plan_commit}^{commit}"
git merge-base --is-ancestor fff1bfd278d550d01de6e8d74f553f45c4003a8c "$accepted_plan_commit"
reviewed_dispatch_commit="$(git rev-parse HEAD)"
test "${#reviewed_dispatch_commit}" -eq 40
git cat-file -e "${reviewed_dispatch_commit}^{commit}"
test "$(git rev-parse "${reviewed_dispatch_commit}^")" = "$accepted_plan_commit"
git diff --quiet "$accepted_plan_commit" "$reviewed_dispatch_commit" -- . ':(exclude)docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md' ':(exclude)docs/exec-plans/index.md'
git diff --name-only "$accepted_plan_commit" "$reviewed_dispatch_commit"
python3 -B tools/docs/generate.py --check
python3 -B tools/docs/check.py
git diff --check "$accepted_plan_commit" "$reviewed_dispatch_commit"
test ! -e internal/fixtures/product-demo
test -z "$(git status --porcelain)"
```

The `git diff --name-only` output must be exactly this plan and
`docs/exec-plans/index.md`; docs validation must be green with none of the eight
draft diagnostics; the fixture directory must still be absent; and the worktree
must be clean. Those facts, the exact accepted plan verdict, and the exact
reviewed dispatch commit are the dispatch evidence. Only then may implementation
start. The implementation author may update fixture files and living narrative
evidence, but may not change the reviewed reviewer/gate fields,
`dispatch_ready`, the index, or the implementation base.

After fresh independent acceptance of the exact implementation commit, any
coordinator-owned metadata/index update remains a distinct non-dispatch range.
If used before a later separately authorized completion/archive step, it must set
`dispatch_ready: false`, update `last_verified_commit` to the exact accepted
implementation commit, retain the independent plan/gate metadata, change only
this active plan and (if necessary) its existing index entry, and use the
`coordinator-transition` runner scope:

```text
accepted_implementation_commit="<exact accepted 40-character implementation commit>"
test "${#accepted_implementation_commit}" -eq 40
git cat-file -e "${accepted_implementation_commit}^{commit}"
transition_commit="$(git rev-parse HEAD)"
test "${#transition_commit}" -eq 40
git cat-file -e "${transition_commit}^{commit}"
git merge-base --is-ancestor "$accepted_implementation_commit" "$transition_commit"
PYTHONDONTWRITEBYTECODE=1 python3 internal/fixtures/product-demo/verify_scope.py --repo . --scope coordinator-transition --base "$accepted_implementation_commit" --candidate "$transition_commit" --include-untracked
python3 -B tools/docs/generate.py --check
python3 -B tools/docs/check.py
git diff --check "$accepted_implementation_commit" "$transition_commit"
git diff --name-only "$accepted_implementation_commit" "$transition_commit"
test -z "$(git status --porcelain)"
```

That later metadata update is not required to authorize initial dispatch and
does not itself declare the ExecPlan completed or authorize a move to
`docs/exec-plans/completed/**`. This rework authorizes no coordinator mutation
and leaves the current draft metadata truthful.

## Idempotence, rollback, and recovery

All corpus inputs use fixed clocks and IDs. `validate.py --check` is read-only and
rerunnable. `update_evidence.py` is the sole deterministic writer for hashes and
reports. Two consecutive `--write` runs must print identical target digests and
the second must update nothing; the following `--check` must render every target
twice, prove both render sets byte-identical, and prove exact byte identity with
disk. A partial validator failure leaves all source files and diagnostics intact.
Implementation recovery changes only the invalid governed fixture or this plan;
it never weakens a rule, deletes a negative case, changes external evidence,
edits the index, or edits a consumer to make the corpus pass. A failed coordinator
dispatch transition is recovered only by changing this plan and/or
`docs/exec-plans/index.md` from the unchanged accepted plan commit and rerunning
its fixed Git/docs proof before implementation. A failed post-implementation
metadata transition is recovered by creating a new exact plan/index transition
commit and rerunning `coordinator-transition` from the unchanged accepted
implementation commit.

Before implementation, rollback is a reviewed revert of only the coordinator
dispatch transition, returning to the accepted draft-plan candidate. After
implementation, rollback keeps the ranges separate: revert any later coordinator
plan/index metadata transition independently from the accepted fixture/plan
implementation commit. There is no database, external run, registry, deployment,
credential, or live state to clean up. If a later accepted production schema
conflicts with this corpus, create a versioned corpus migration or superseding
reviewed plan; do not rewrite prior evidence in place or claim historical live
parity.

`SPIKE-STREAM-001` and every other gate in front matter retains its documented
fallback. A failed or delayed gate does not block fixture validation; it blocks
the corresponding live/runtime claim. A failed TS re-review blocks TypeScript
consumer parity, not the neutral corpus.

## Rollout and handoff

There is no production rollout. After fresh independent acceptance, hand the
exact fixture commit, corpus digest, validation transcript, gate ledger, complete
pre-transition docs diagnostic set, and clean scope proof to the coordinator.

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
