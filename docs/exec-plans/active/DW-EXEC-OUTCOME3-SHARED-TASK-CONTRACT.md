---
exec_plan_id: DW-EXEC-OUTCOME3-SHARED-TASK-CONTRACT
title: Outcome 3 shared task domain and client contract
status: active
superseded_by: null
owner: task-domain-sdk
reviewed_by: []
reviewed_at: null
primary_feature_id: DW-FND-004
supporting_feature_ids: [DW-FND-005]
issue: local:DW-OUTCOME3-TASK-CONTRACT
created: 2026-07-23
last_updated: 2026-07-23
base_commit: 314140b1adfbb6490e9453eec810d1258ced41ab
last_verified_commit: 314140b1adfbb6490e9453eec810d1258ced41ab
risk: medium
governed_paths: [packages/domain/src/**, packages/domain/tests/**, packages/domain/README.md, packages/sdk/src/**, packages/sdk/tests/**, packages/sdk/README.md, docs/exec-plans/active/DW-EXEC-OUTCOME3-SHARED-TASK-CONTRACT.md]
contract_gates: [SPIKE-STREAM-001, SPIKE-HITL-001]
decision_gates: []
gate_review_status: implementation-bounded-to-accepted-local-contract
gate_reviewed_by: []
gate_reviewed_at: null
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, docs/AGENTS.md, packages/domain/AGENTS.md, packages/sdk/AGENTS.md, docs/product-specs/foundations/dw-fnd-004-sdk-stream-and-fixture-contracts.md, docs/product-specs/foundations/dw-fnd-005-domain-identity-status-and-audit-model.md, apps/api/src/deepwork_api/contracts/tasks.py, apps/api/src/deepwork_api/transport/tasks.py, apps/web/src/lib/task-types.ts, apps/web/src/lib/http-task-client.ts, apps/web/src/lib/task-normalizers.ts, apps/web/src/lib/sse.ts]
scenario_ids: [AC-DW-FND-004-01, AC-DW-FND-004-02, AC-DW-FND-004-03, AC-DW-FND-004-06, AC-DW-FND-005-01]
dispatch_kind: cell
dispatch_ready: true
agent_review_required: true
dependencies: []
blockers: []
---

# Outcome 3 shared task domain and client contract

## Purpose and observable result

Make `@deepwork/domain` and `@deepwork/sdk` the one browser-safe task contract
used by web, Tauri, and future clients. The finished packages expose immutable,
source-qualified identities; client-safe task, plan, evidence, interrupt,
decision, receipt, detail, result, and event values; a pure replay-safe reducer;
and separate query, mutation, and stream service ports.

The implementation consumes only the accepted current `/api/v1` task contract.
It does not invent provider fields, upstream cursors, endpoints, headers, or
runtime actions. The SDK receives the authorized source identity as mapping
context because the current local wire contract does not expose a reusable
provider/source record. Unknown or malformed wire values fail closed.

This cell contributes package-level evidence to:

- `AC-DW-FND-004-01`: replay deduplication and deterministic ordering;
- `AC-DW-FND-004-02`: explicit hydration/reconnect boundaries without terminal
  inference;
- `AC-DW-FND-004-03`: exact interrupt, plan-revision, and decision-receipt
  correlation for the accepted single-decision local contract;
- `AC-DW-FND-004-06`: no guessed request for unknown provider capability; and
- `AC-DW-FND-005-01`: identical upstream IDs remain distinct across sources.

The cell does not claim live provider, full application, protocol-v2, or
multi-action HITL acceptance. Those remain gated by their accepted spikes and
downstream integration.

## Context and orientation

The exact clean base is
`314140b1adfbb6490e9453eec810d1258ced41ab`. At that base,
`packages/domain` contains source-qualified thread/run keys, capability evidence,
and status vocabularies. `packages/sdk` contains generic query/mutation/stream
ports and typed unavailable results. Outcome 2 added the accepted local task API
and web client under `apps/api` and `apps/web`; both are read-only evidence for
this packet.

The accepted public task contract exposes:

- `POST /api/v1/tasks`, `GET /api/v1/tasks`, `GET /api/v1/tasks/{taskId}`,
  `GET /api/v1/tasks/{taskId}/result`;
- `PATCH /api/v1/tasks/{taskId}/plan` and
  `POST /api/v1/tasks/{taskId}/decisions`;
- `GET /api/v1/tasks/{taskId}/events` as named SSE with application event IDs;
- task statuses `queued`, `running`, `waiting-approval`, `completed`, `rejected`,
  and `failed`;
- events `task.created`, `run.started`, `content.delta`, `plan.proposed`,
  `plan.updated`, `evidence.recorded`, `interrupt.requested`,
  `decision.recorded`, and `run.completed`; and
- decision values `approve`, `reject`, and `respond`.

No current wire response exposes thread identity, provider cursor, raw provider
payload, cancel/retry/checkpoint behavior, or a reusable credential/source
record. This cell represents absent behavior as unavailable and does not add
those fields to the accepted wire types.

## Scope

### In scope

- Opaque source, thread, run, interrupt, evidence, application event, and task
  identities, with every external runtime identity qualified by source and its
  full parent context.
- Immutable client-safe values for current task summaries/details/results,
  evidence/provenance metadata, editable plans, pending interrupts, decisions,
  plan-edit receipts, decision receipts, and normalized application events.
- A pure task projection and reducer with:
  - attention precedence;
  - orthogonal reconnect, stale, and source-health flags;
  - monotonic application-event sequences and plan revisions, without inventing
    a separate task resource version;
  - exact task/run/interrupt/decision receipt correlation;
  - source-qualified replay deduplication;
  - deterministic handling of duplicate and out-of-order events; and
  - no terminal inference from disconnect, source failure, missing events, or
    unsubscribe.
- Strict wire validators/mappers for only the accepted current `/api/v1` values.
- Separate `TaskQueryService`, `TaskMutationService`, and `TaskStreamService`
  ports, including an explicit stream subscription whose `unsubscribe` operation
  is not cancellation.
- Deterministic package tests with SDK network primitives denied globally.
- Package README and this living plan.

### Non-goals

- Any edit to `apps/**`, `packages/ui/**`, manifests, lockfiles, shared/root
  files, generated documentation/indexes, `docs/plans/**`, scanner behavior or
  scanner fixtures, sibling repositories, or external systems.
- React hooks, caches, route construction, raw `fetch`, `EventSource`, provider
  SDKs, provider cursors, environment reads, credential or `authRef` types,
  server secrets, generic upstream protocols, or live network calls.
- Cancellation, retry, branching, checkpoints, multi-source aggregation, or
  multi-action HITL requests not present in the accepted current `/api/v1`
  contract.
- Installing packages, changing the shared lock, integrating, resetting,
  cleaning other worktrees, pushing, merging, deploying, or self-approving.

### Permissions and risk boundary

- Writes are confined to the exact `governed_paths` above. Existing
  `packages/domain/tests/fixtures/**`, `packages/sdk/tests/fixtures/**`, package
  scanner scripts, and scanner behavior are read-only.
- No credential, live source, provider endpoint, or public network is required.
- Risk is medium because this establishes public package semantics consumed by
  multiple clients. It has no production data or external side effect.
- The author validates and commits the bounded diff, then stops. Coordinator task
  `019f8e39-7c94-75f0-b003-d334d7770c35` is the sole reviewer/integrator.

## Authoritative sources and precedence

1. Accepted current application contract:
   `apps/api/src/deepwork_api/contracts/tasks.py` and
   `apps/api/src/deepwork_api/transport/tasks.py`.
2. Accepted Outcome 2 client correlation behavior:
   `apps/web/src/lib/task-types.ts`, `http-task-client.ts`,
   `task-normalizers.ts`, and `sse.ts`.
3. Package and architecture rules in root/package `AGENTS.md` files and
   `ARCHITECTURE.md`.
4. Stable intent, fallback, and acceptance in `DW-FND-004` and `DW-FND-005`.

When these sources differ, the public API wire shape wins for mapping. The stable
spec wins for pure identity and reducer safety. An unsupported provider or future
wire field remains unavailable rather than being guessed.

## Interfaces and invariants

### Domain

- Opaque constructors reject empty, padded, control-bearing, or oversized
  identity values. Source-qualified keys serialize deterministically.
- Accepted user text uses Unicode code-point bounds: objective 8,000; plan step
  1,000; decision comment 1,000. Invalid input is rejected with no truncation.
- Every opaque identity is bounded to 200 Unicode code points and rejects
  unsupported controls and unpaired surrogates, so accepted composite keys have
  total deterministic serialization.
- Plan revisions and application-event sequences use distinct exported semantic
  bounds even though both accepted maxima are currently `2_147_483_647`.
- A task projection retains durable status facts separately from orthogonal
  connection/source flags. Pending current interrupt owns attention while
  preserving active-run evidence. Authoritative cancellation wins only when an
  accepted cancellation event exists; the current wire contract has none.
- Event identity includes source, task, thread, run, and application event ID.
  Exact replay is ignored; conflicting replay, gaps, impossible local event
  transitions, post-terminal mutation, or nested identity drift quarantine the
  projection until authoritative hydration. Older/equal revisions never replace
  newer state, and equal-cursor hydration clears quarantine only when it is
  semantically identical.
- Decision effects clear an interrupt only when source, task, run, interrupt, and
  expected plan revision correlate and the decision belongs to the interrupt's
  current allowed set. The local revision guard is omitted intentionally from
  the unchanged HTTP payload. `respond` and plan edit remain distinct actions.
- A result is attached only as a correlated `TaskResult` for the same
  source/task/thread/run, and detail mapping requires exact terminal/result
  coherence.
- Evidence exposes bounded metadata and provenance only, never raw provider
  values or unbounded content.

### SDK

- `TaskQueryService` reads accepted task list/detail/result shapes.
- `TaskMutationService` creates tasks, edits the current plan, and records the
  exact accepted decision request.
- `TaskStreamService` subscribes to normalized application events and returns a
  subscription with an idempotent `unsubscribe`; it exposes no cancel operation.
- Stream observers receive bounded `connected`, `recovered`, or `hydrated`
  boundaries. Only explicit authoritative `recovered`/`hydrated` input advances
  the replay cursor; reconnect alone never proves recovery.
- Wire inputs are `unknown`. Mapping succeeds only for exact records, declared
  enum values, finite integers, bounded strings, and arrays within accepted
  bounds. Unknown fields or variants fail with a typed contract error.
- Mapping context supplies the authorized source (and thread where the current
  application binding already knows it); no provider identity is inferred from a
  task or assistant label.
- Accepted application Problems require exact HTTP status/code pairs and map to
  SDK-owned safe messages. Cursor-invalid uses hydrate/reconnect semantics;
  current interrupt/decision/plan conflicts require an authoritative refetch;
  unknown failures remain bounded and non-retryable.
- The SDK has no endpoint construction, raw HTTP/stream implementation, provider
  import, environment access, secret reference, React dependency, or network
  fallback.

## Milestones

### Milestone 1 — Plan and accepted contract inventory

- Verify branch/base/cleanliness and read every governing source.
- Record accepted wire fields, statuses, events, bounds, and correlation rules.
- Create this living plan before code changes.

Acceptance: exact base, governed paths, authoritative sources, risks, acceptance
IDs, commands, and non-goals are present in this plan.

### Milestone 2 — Domain task contract and reducer

- Add identities and immutable domain values.
- Add the pure projection/reducer and selectors.
- Test cross-source collisions, replay/duplicate/out-of-order behavior,
  revision monotonicity, receipt correlation, respond/edit distinction,
  disconnect preservation, and attention precedence.

Acceptance: domain tests cover every required reducer and identity case through
the public package entry.

### Milestone 3 — SDK services and fail-closed wire mapping

- Add exact accepted wire shapes as private input contracts and public mapping
  functions from `unknown`.
- Add separate task query/mutation/stream service ports and service constructors
  over injected generated/application transports.
- Test malformed/unknown wire values, stale/mismatched receipts, bounds, service
  separation, unsubscribe-not-cancel, and globally network-denied behavior.

Acceptance: no request is guessed, no raw provider value is exported, and every
accepted response/event either maps to immutable domain state or fails closed.

### Milestone 4 — Validation, commit, and handoff

- Run the exact package, documentation, architecture, diff, and scope commands.
- Update `Progress`, discoveries, decisions, and retrospective with exact results.
- Commit only governed files, verify clean worktree, and send immutable SHA,
  file list, commands/results, acceptance contributions, and honest gaps to the
  Coordinator.

Acceptance: every required command is recorded; `docs/plans/**` is unchanged;
the worktree is clean after commit; no integration/push/deploy occurs.

## Executable validation

Run from the repository root without installing or changing locks:

```bash
pnpm --filter @deepwork/domain format-check
pnpm --filter @deepwork/domain lint
pnpm --filter @deepwork/domain typecheck
pnpm --filter @deepwork/domain test
pnpm --filter @deepwork/domain build
pnpm --filter @deepwork/domain check-architecture
pnpm --filter @deepwork/domain package-check
pnpm --filter @deepwork/sdk format-check
pnpm --filter @deepwork/sdk lint
pnpm --filter @deepwork/sdk typecheck
pnpm --filter @deepwork/sdk test
pnpm --filter @deepwork/sdk build
pnpm --filter @deepwork/sdk check-architecture
pnpm --filter @deepwork/sdk package-check
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
git diff --check 314140b1adfbb6490e9453eec810d1258ced41ab
git diff --name-only 314140b1adfbb6490e9453eec810d1258ced41ab
git diff --name-only 314140b1adfbb6490e9453eec810d1258ced41ab -- docs/plans
git status --short
```

If a package command fails because the accepted base lacks a required offline
tool artifact, record the exact failure as a blocker; do not install or substitute
another toolchain. Package checks may write only their declared reproducible build
or temporary output and must not change manifests or the lock.

## Recovery and rollback

- Before commit, revert only this packet's governed-file changes if the contract
  cannot be made safe. Never reset the worktree or touch another lane.
- Reducer/mapping failures are repaired by narrowing accepted input or retaining
  the last safe projection; no malformed event is partially applied.
- If API evidence changes during implementation, stop mapping the affected shape,
  record the drift, and request a successor packet. Do not edit `apps/**`.
- Integration rollback is Coordinator-owned. Package consumers can remain on the
  prior public exports because this packet adds no external side effect.

## Progress

- [x] 2026-07-23 AEST — Activation received for worktree
      `/Users/tomspencer/dev/deepwork/worktrees/task-domain-sdk`, branch
      `product/task-domain-sdk`, exact base
      `314140b1adfbb6490e9453eec810d1258ced41ab`.
- [x] 2026-07-23 AEST — Branch, HEAD, clean state, and governed path boundaries
      verified before editing.
- [x] 2026-07-23 AEST — Root/docs/package instructions, architecture, both stable
      foundation specs, and accepted Outcome 2 API/web contracts read in full.
- [x] 2026-07-23 AEST — Milestone 1 living plan created before implementation.
- [x] 2026-07-23 AEST — Milestone 2 domain implementation complete, including
      composite identity coherence, accepted local transition table, terminal
      immutability, bounded evidence, correlated results, and 65 focused tests.
- [x] 2026-07-23 AEST — Milestone 3 SDK implementation complete, including exact
      mapping, full mutation binding/revision guards, explicit recovery boundaries,
      canonical Problem mapping, replay quarantine, and 58 network-denied tests.
- [x] 2026-07-23 AEST — Immutable candidate `1508a943` independently reviewed;
      review correctly rejected nullable checkpoint replay fingerprints and an
      invalid success-before-result `TaskDetail`.
- [x] 2026-07-23 AEST — Successor fixes implemented: authoritative checkpoints
      retain bounded non-null fingerprints, successful completion uses an
      explicit projection-level pending-result state, equal-cursor authoritative
      result hydration converges, incoherent hydration quarantines, and public
      aggregate constructors strip caller-only fields.
- [x] 2026-07-23 AEST — Milestone 4 bounded successor validation complete;
      immutable commit and Coordinator handoff follow this recorded source state.

## Surprises and discoveries

- 2026-07-23 AEST — The current accepted wire contract intentionally contains no
  `sourceId` or `threadId`. Consequence: the SDK mapper must require authorized
  source/thread binding context and must never infer a source from task/run IDs.
- 2026-07-23 AEST — The current web normalizer accepts historical status aliases
  and ignores malformed streamed plans. Consequence: the reusable SDK will accept
  only current API enum values and fail closed; compatibility aliases remain an
  app-owned migration concern.
- 2026-07-23 AEST — The stable specs describe multi-action HITL and provider
  protocol recovery, but the accepted current API exposes one decision for one
  local interrupt and application-owned SSE replay. Consequence: this packet
  proves exact single-interrupt correlation and application replay only; broader
  HITL/provider claims remain gated.
- 2026-07-23 AEST — The current API exposes `lastEventId` as an application
  replay cursor but no independent optimistic task resource version.
  Consequence: the public model uses `lastEventSequence`, never a fabricated
  `taskRevision`.
- 2026-07-23 AEST — The accepted local runner has a specific event transition
  order and a single pending interrupt. Consequence: well-shaped events that are
  impossible in the current queued/running/needs-review/terminal state are
  quarantined rather than generalized into a future provider protocol.

## Decision log

- 2026-07-23 — Decision: qualify every runtime identity with explicit SDK mapping
  context rather than adding unaccepted fields to wire DTOs. Rationale: source
  identity is mandatory for safety but absent from the current API response.
- 2026-07-23 — Decision: model wire input as `unknown` and require exact keys.
  Rationale: client-safe mapping must reject provider leakage and contract drift.
- 2026-07-23 — Decision: retain durable task status independently from
  reconnect/stale/source health. Rationale: disconnect and outage are not
  authoritative task outcomes.
- 2026-07-23 — Decision: expose injected transports and service ports only.
  Rationale: route construction, raw fetch/SSE, credentials, and provider
  protocol belong outside this bounded SDK package.
- 2026-07-23 — Decision: treat stream reopening as non-authoritative
  `connected`; only a validated `recovered` or `hydrated` boundary may establish
  recovery. Rationale: connection state is orthogonal to replay completeness.
- 2026-07-23 — Decision: retain at most 256 projected evidence records and 2,048
  replay fingerprints/keys. Rationale: every untrusted collection requires a
  deterministic memory bound and overflow must fail closed.
- 2026-07-23 — Decision: a success event may advance projection facts and cursor
  while `resultPending` retains the last valid public detail. Rationale: the
  accepted event announces result availability, but only the correlated result
  or authoritative detail contains the result required by the public success
  invariant.
- 2026-07-23 — Decision: seed hydration with a bounded canonical detail
  fingerprint and suppress checkpoint event replay only when the detail proves
  its exact semantics. Rationale: the API detail does not expose arbitrary prior
  event payloads, so ambiguous replay must fail closed rather than use a wildcard.
- 2026-07-23 — Decision: the rotating interrupt identity plus plan revision is
  only the current local single-action concurrency boundary. Rationale: it does
  not prove the stable specification's general ordered multi-action HITL model.

## Validation record

Source and deterministic checks completed with the bundled Node runtime and the
Coordinator-authorized ignored package-local dependency copies:

- domain build passed;
- domain focused tests passed: 6 files, 65 tests;
- domain test typecheck passed with the explicit `ES2022,DOM` library supplement;
- SDK build and test typecheck passed;
- SDK focused tests passed: 6 files, 58 tests, with browser and Node network
  primitives denied by the package setup;
- domain and SDK architecture checks passed;
- changed source/test/docs lint passed, with one pre-existing sparse-array warning
  in `packages/domain/tests/capability.test.ts`;
- all 17 changed governed files passed `oxfmt --check`;
- generated documentation check passed: 6 documents; and
- package-wide format checks reported only existing formatting drift in unchanged
  package files.

Dependency/integration-backed checks remain explicitly blocked rather than
substituted:

- the unmodified domain `tsconfig.test.json` omits host/DOM globals required by
  the linked Vitest declarations; the exact package typecheck reports those
  external declaration errors, while the source-equivalent supplemented
  typecheck passes;
- domain `package-check` packs successfully, then the offline clean-consumer
  install stops at missing
  `@typescript/typescript-darwin-arm64-7.0.2.tgz`;
- SDK `package-check` packs both archives, then the offline clean-consumer install
  stops because registry metadata for `@deepwork/domain@0.0.0` is unavailable;
  no network or install fallback was used; and
- `tools/docs/check.py` awaits Coordinator-owned index and independent reviewer/
  gate metadata for this new active plan. The worker cannot edit the generated
  index or self-approve.

Validation infrastructure disposition:

- the untracked root dependency symlink was moved intact, without touching its
  target, to
  `/private/tmp/task-domain-sdk-validation-link.RXndxc/node_modules`;
- the ignored `packages/domain/node_modules` and `packages/sdk/node_modules`
  validation copies remain in place as authorized; and
- the earlier preserved
  `/private/tmp/task-domain-sdk-partial.qZR9iL/node_modules` and
  `/private/tmp/task-domain-sdk-offline-node_modules.PU8mB2/node_modules` trees
  were not touched.

Successor validation after immutable review:

- direct domain build with the bundled Node/TypeScript runtime passed;
- domain source and tests passed a temporary-path direct TypeScript check; the
  temporary review config was removed before commit;
- changed domain source/tests passed direct `oxfmt --check` and `oxlint`;
- direct ESM probes against built output passed checkpoint exact/conflicting
  replay, completion-pending-result equal-cursor convergence, incoherent
  hydration rejection, and aggregate constructor secret stripping; and
- dependency-backed Vitest and architecture reruns are temporarily blocked
  because an independent reviewer accidentally started and interrupted a
  managed workspace install, leaving ignored root `node_modules/.pnpm` and
  breaking the authorized package-local relative dependency links. The artifact
  is preserved untouched; no cleanup, restoration, install, or further `pnpm`
  command was attempted without Coordinator authorization.

## Outcomes and retrospective

Implementation and deterministic package validation are complete. Independent
review and integration remain Coordinator-owned. The candidate handoff records
the immutable commit, exact commands/results, acceptance contributions, and
remaining provider/application gaps without promoting package tests to full
product proof.
