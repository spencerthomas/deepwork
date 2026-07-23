---
exec_plan_id: DW-EXEC-M1-FIXTURE-API-CONSUMER
title: Credential-free fixture API consumer
status: draft
superseded_by: null
owner: api-fixture-consumer
reviewed_by: []
reviewed_at: null
primary_feature_id: DW-FND-004
supporting_feature_ids: [DW-FND-001, DW-FND-003, DW-FND-005]
issue: local:DW-M1-FIXTURE-API-CONSUMER
created: 2026-07-23
last_updated: 2026-07-23
base_commit: 9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2
last_verified_commit: null
risk: medium
governed_paths: [apps/api/**, docs/exec-plans/active/DW-EXEC-M1-FIXTURE-API-CONSUMER.md]
contract_gates: [SPIKE-STREAM-001, SPIKE-HITL-001, SPIKE-CHECKPOINT-001, SPIKE-MDA-001, SPIKE-FLEET-001, SPIKE-DIRECT-STREAM-001]
decision_gates: [DEC-023, DEC-026, DEC-033, DEC-034, DEC-035, DEC-036, DEC-037]
gate_review_status: unreviewed
gate_reviewed_by: []
gate_reviewed_at: null
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, apps/api/AGENTS.md, docs/AGENTS.md, docs/PLANS.md, docs/SECURITY.md, docs/RELIABILITY.md, docs/design-docs/architecture/application-architecture.md, docs/design-docs/engineering/conventions.md, docs/design-docs/decisions/index.md, docs/product-specs/foundations/dw-fnd-001-repository-oss-and-delivery-foundation.md, docs/product-specs/foundations/dw-fnd-003-application-service-state-and-security.md, docs/product-specs/foundations/dw-fnd-004-sdk-stream-and-fixture-contracts.md, docs/product-specs/foundations/dw-fnd-005-domain-identity-status-and-audit-model.md, docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md, docs/exec-plans/completed/DW-EXEC-M1-API-SCAFFOLD.md]
scenario_ids: [AC-DW-FND-001-07, AC-DW-FND-003-05, AC-DW-FND-004-04, AC-DW-FND-004-05, AC-DW-FND-005-01]
dispatch_kind: cell
dispatch_ready: false
agent_review_required: true
dependencies: [DW-EXEC-M1-FIXTURE-CONTRACT]
blockers: []
---

# Credential-free fixture API consumer

## Purpose and observable result

Extend the independently installable `apps/api` distribution so a loopback-only
fixture API can read the independently accepted
`internal/fixtures/product-demo/**` corpus, map its synthetic identities,
capability evidence, ordered records, authoritative terminal facts, and
source-qualified failures into explicit Deep Work application contracts, and
exercise the same mapping through a bounded worker function. The result remains
credential-free, deterministic, network-denied, and explicitly non-durable.

This cell contributes API evidence to `AC-DW-FND-004-04`,
`AC-DW-FND-004-05`, `AC-DW-FND-005-01`, and the unavailable-capability slices of
`AC-DW-FND-001-07` and `AC-DW-FND-003-05`. It completes none of those feature
scenarios and completes zero `E2E-V1-*` scenarios. It is not the browser-local UI
harness, the API-backed full product demo, a live source adapter, a normalized
provider stream, a durable job system, or proof of any external runtime.

Status is **draft, prepared for independent review**. Planning is complete enough
to review, but execution is blocked until the Coordinator records an exact
independently accepted fixture-corpus implementation commit and transitions this
plan through the reviewed/indexed dispatch gate.

## Context and orientation

The exact plan-authoring base is
`9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2`. At that base:

- `apps/api` is a Python 3.12 FastAPI distribution with separate
  `deepwork-api` and `deepwork-worker` entry points;
- `/health` proves process liveness only and `/api/v1/demo/status` reports a
  fixture scaffold whose live capabilities are unavailable;
- `deepwork-worker --check` reports that durability is unavailable;
- there is no corpus consumer, event projection, source aggregation, Postgres
  adapter, object adapter, or durable worker loop;
- the fixture candidate
  `8291218590e3f6a91a5383ae91d6e909e71b1fbe` is under fresh independent review
  and is not accepted dependency evidence; and
- the TypeScript candidate `1bf66e1` is `REWORK REQUIRED`. This API-only cell
  neither consumes nor waits for TypeScript source, a shared lock, or TypeScript
  verification and may execute alongside those sequential cells after fixture
  acceptance.

The corpus is private, language-neutral input. Its `caseId`, case category,
fixture sequence, logical tick, and expected assertions are test-corpus
concepts—not public `/api/v1` wire fields by default. The consumer loads accepted
JSON data through a deliberate repository port and maps it once into application
domain values. It does not import `validate.py`, execute the corpus validator,
shell out to it, or serialize a corpus document directly as an API response.

## Scope

### In scope

- Only `apps/api/**` and this living ExecPlan.
- A read-only corpus path supplied explicitly at bootstrap; no environment scan,
  sibling lookup, package-data copy, mutation, or hidden fallback path.
- Pure Python domain values for source-qualified fixture identity, capability
  evidence, ordered record classification, freshness/terminal authority, and
  source-scoped failure.
- A port for loading one accepted corpus index/case and a fixture adapter that
  parses bounded JSON through explicit internal models.
- Application use cases that expose catalog, case projection, deterministic
  logical-tick advancement, and reset of in-memory projection state.
- Pydantic `/api/v1/demo/**` response/request contracts that are visibly
  `mode: fixture`, contain only synthetic values, and never expose corpus
  implementation fields accidentally.
- An exact bounded worker implementation at
  `apps/api/src/deepwork_api/workers/product_demo.py`. It consumes one validated
  `FixtureStepJob`, invokes the same application reducer, and returns a
  `FixtureStepResult`. In this cell it has no lease, database, object service, or
  retry claim and reports `durability: unavailable`.
- Bootstrap wiring under `apps/api/src/deepwork_api/bootstrap/{api,worker}.py`
  for explicit `--fixture-corpus`, `--fixture-case`, and logical-tick arguments.
- Unit and contract tests under `apps/api/tests/**`, including socket denial,
  import-boundary checks, malformed/collision/partial-failure cases, API/worker
  parity, and wheel/public-import proof through existing package commands.
- Living progress, decisions, evidence, and handoff in this file.

### Non-goals

- Editing `internal/fixtures/product-demo/**`, running its validator as production
  code, or weakening its accepted schema/hashes.
- Editing root manifests, `pnpm-lock.yaml`, Turbo, root `Makefile`, TypeScript
  packages, `internal/adapter-tests/**`, `apps/web/**`, generated docs, the
  ExecPlan index, program plans, or `docs/plans/**`.
- Postgres, SQLAlchemy, migrations, outbox leases, object storage, telemetry
  service, process supervisor, dual-stack exercise, or full product-demo reset.
- A provider endpoint, credential, `authRef`, provider cursor, real actor,
  operational URL, generic proxy, direct browser stream, or external network.
- Treating ordered interrupt, checkpoint, replay, or terminal fixture records as
  proof that a live source supports HITL, branching, resumability, or streaming.
- Completing a whole feature scenario, release criterion, or `E2E-V1-*` row.

### Permissions and risk boundary

- Allowed writes are exactly the two governed path entries in front matter.
- `internal/fixtures/product-demo/**` is read-only and must match the exact
  accepted dependency commit.
- No install, dependency resolution, provider call, service startup, credential,
  push, merge, deployment, migration, publication, or destructive action is
  authorized by this plan.
- Runtime/tests deny IP sockets. The existing asyncio-local Unix socket exception
  remains limited to test-framework mechanics.
- Architecture, API-contract, and security/reliability reviewers are required.
  The author cannot set review metadata or self-approve.

## Authoritative sources and prerequisites

### Persistent dependency gate

Execution requires exactly one nonterminal dependency:

| Dependency | Required terminal evidence | Current state |
|---|---|---|
| `DW-EXEC-M1-FIXTURE-CONTRACT` | Exact accepted implementation SHA; independent `ACCEPT`; corpus digest; green validator and scope proof; Coordinator-reviewed dispatch/terminal transition | Blocked. Candidate `8291218590e3f6a91a5383ae91d6e909e71b1fbe` is under review, not accepted. |

The completed API scaffold at
`3fbdb01be06152cc39e50f6378dfb625daed8998` is inherited baseline evidence, not a
nonterminal dependency. TypeScript source, lock, fixture consumer, and verification
are deliberately absent from this cell's dependency list. The API cell may execute
concurrently with them once fixture acceptance is terminal because its governed
paths are disjoint.

Before dispatch, the Coordinator records the exact accepted fixture commit in
this plan, verifies it is an ancestor of the implementation base, confirms that
`internal/fixtures/product-demo/**` is unchanged at dispatch, adds the reviewed
plan to the index in a separate coordinator-owned transition, and sets
`dispatch_ready: true`. Chat statements, the plan-only fixture commit, or a
candidate under review are not sufficient.

### External contract fallbacks

All contract gates remain open. Corpus presentation rows for stream, HITL,
checkpoint, MDA, Fleet, or direct streaming map to `gated`, `unknown`, or
`unavailable` application capabilities unless a later live-contract plan accepts
the exact external operation. The API must make no request for those rows.

## Interfaces and invariants

### Exact intended module boundary

```text
apps/api/src/deepwork_api/
  domain/product_demo.py
  ports/product_demo.py
  application/product_demo.py
  adapters/fixture/product_demo.py
  contracts/product_demo.py
  transport/product_demo.py
  workers/product_demo.py
  bootstrap/api.py
  bootstrap/worker.py
```

The implementation may split tests or private helpers inside these layer
directories, but it may not move corpus parsing into transport, put FastAPI or
Pydantic in domain/application, or introduce a second package.

### Domain and mapping contract

- `FixtureSourceKey`, `FixtureThreadKey`, and `FixtureRunKey` retain `sourceId`;
  identical provider-native thread/run strings never collide.
- `FixtureCapabilityEvidence` accepts only
  `available|unavailable|gated|permission-denied|unknown`, fixed observation
  time, adapter/contract versions, `evidenceClass: fixture`, and a safe reason
  for every non-available state.
- `available` is accepted only for corpus cells explicitly marked as simulated
  product-demo behavior. A fixture never maps to `documented` or
  `live-contract`.
- Ordered records retain unique event ID and fixture sequence. Replay duplicates
  are ignored by durable ID while their expected retained/ignored classification
  remains test evidence.
- Disconnect and logical delay are never terminal. Only an explicit
  authoritative fixture completion/failure/cancellation record may set a
  terminal projection.
- Unknown records remain a bounded `unknown` projection. Malformed upstream-like
  values return a safe contract classification and never crash or become success.
- Partial failure returns healthy source projections plus source-qualified safe
  failures; it is not an all-empty response.
- Corpus paths, raw expected assertions, negative fixtures, hashes, validator
  internals, and arbitrary raw payloads do not enter the public response.

### Public fixture API

The implementation pins these fixture-only resource families:

```text
GET  /api/v1/demo/catalog
GET  /api/v1/demo/cases/{case_id}
POST /api/v1/demo/cases/{case_id}/advance
POST /api/v1/demo/reset
```

Every response includes `mode: "fixture"`, corpus version/digest, synthetic
workspace/source identity, observed logical tick, evidence class, and a safe
capability/freshness summary. Mutation requests require a synthetic session ID,
expected logical tick, and idempotency key. They mutate process-local fixture
projection only. Reset returns the fixed starting projection and cannot affect
files, sources, Postgres, objects, or another process.

Unknown case IDs return a stable not-found problem without path disclosure.
Stale ticks return an explicit conflict. Idempotency is scoped by
`(synthetic_session_id, case_id, operation, idempotency_key)` and retains the
SHA-256 of a canonical request containing expected/target ticks. Reuse with the
same digest returns the original result; reuse with a different digest returns a
stable conflict and changes nothing. Each process accepts at most 1,024 retained
keys per synthetic session, 32 active sessions, 8,192 keys total, and
`16,777,216` serialized result bytes total. Synthetic session IDs match
`^fxs_[a-z0-9]{16,48}$`; idempotency keys are 1–64 printable ASCII characters
excluding whitespace/control characters. A new session/key/result is rejected
before mutation when any capacity would be exceeded. Nothing is silently evicted;
explicit reset clears that session and frees its exact retained budget. Request
bodies cannot supply paths, endpoints, headers, credentials, raw events, or
arbitrary URLs.

### Worker contract

`apps/api/src/deepwork_api/workers/product_demo.py` owns:

```text
FixtureStepJob(synthetic_session_id, case_id, operation, expected_tick,
               target_tick, idempotency_key, canonical_request_sha256)
FixtureStepResult(synthetic_session_id, case_id, operation, previous_tick,
                  current_tick, emitted_event_ids, projection_digest,
                  canonical_request_sha256, durability="unavailable")
process_fixture_step(job, repository, reducer) -> FixtureStepResult
```

The worker function is pure except for its injected read-only repository and
in-memory projection store. The CLI invokes it once and emits one sorted JSON
result. It does not poll, sleep, bind a port, lease work, write the corpus, or
claim accepted background durability. The later full-stack integration plan may
wire an accepted Postgres job adapter around this pure application function.
That adapter, not this function, owns namespace scope, leasing, and durable
transaction semantics; it must not replace the function with a `tools/`
imitation.

### Exact corpus ingestion limits

The loader receives the canonical accepted
`internal/fixtures/product-demo` root and accepted digest explicitly. It resolves
the root once, requires every consumed path to remain beneath it, rejects a
symlink at any component, opens each file with `O_NOFOLLOW` where supported, and
checks the opened descriptor is a regular file owned by the expected checkout.
Digest and JSON parsing use the same immutable bytes read from that descriptor;
an inode/device/size/mtime change before parse completion fails closed.

The total bytes read per load are at most `8,388,608`, each file is at most
`2,097,152`, nesting depth is at most `32`, total JSON containers/scalars are at
most `50,000`, an object has at most `256` keys, an array has at most `10,000`
items, and a decoded string has at most `65,536` Unicode scalar values. Exceeding
any bound fails before projection. Tests cover symlink/path escape, non-regular
file, replacement between resolution/open/read, oversized file/corpus, depth,
container, array, key, and string limits.

## State matrix

| Input/state | API/worker behavior | Required evidence |
|---|---|---|
| Corpus dependency absent or digest mismatch | Fail before app readiness with a sanitized fixture-dependency error | No fallback to built-in/live data; zero socket attempts |
| Catalog loading | Bounded read and parse; no wall clock/environment read | Stable sorted response |
| Healthy case | Source-qualified projection and fixture evidence | API/worker reducer parity |
| Empty fixture projection | Typed empty result with evaluated case/source | Not capability-unavailable |
| Unavailable capability | `unavailable` plus safe corpus reason; omit/disable the action | No route construction or application/external request |
| Unknown capability | `unknown` plus safe reason; no request | No guessed route or method |
| Gated capability | `gated` plus named safe reason | No success value |
| Permission-denied fixture | Source-qualified denial; healthy rows remain | No existence or credential leak |
| Partial source failure | Healthy results plus failed-source problem | Stable ordering and pagination-free bounded result |
| Source ID collision | Distinct qualified keys and projections | Collision contract test |
| Duplicate replay record | Apply once; retain ignored-ID evidence only in tests | Same projection digest |
| Out-of-order or malformed record | Safe contract error for affected case | No partial invented terminal state |
| Logical delay before release tick | Record absent through tick 43 | No sleep or wall-clock read |
| Logical delay at release tick | Record visible exactly once at tick 44 | Deterministic event list |
| Disconnect/reconnect record | Preserve durable projection and mark recovery boundary | No cancel/fail inference |
| Explicit completion | Terminal only from authoritative record | Completion ID retained |
| Stale advance | `409`-style fixture conflict; no state change | Current tick returned safely |
| Duplicate advance | Original result under idempotency key | No duplicate events |
| Same scoped key, different request digest | Stable conflict; no state change | Original result/digest retained |
| Idempotency capacity reached | Reject new key; retain all existing keys | No silent eviction/replay |
| Session/process/byte capacity reached | Reject before mutation; exact budget remains | Bounded memory and reset recovery |
| Reset | Return fixed starting digest for this process | No file/service mutation |
| Worker invoked without fixture mode | Refuse with unavailable result | No background loop |

## Milestones

### Milestone 1 — Freeze the read-only consumer contract

Add domain/port/application/parser contracts and corpus provenance checks without
HTTP or worker behavior.

Acceptance:

- accepted corpus data loads through an explicit path and digest;
- product code imports JSON data, not corpus Python modules;
- parser rejects negative/raw schema documents and path escape;
- no file under `internal/fixtures/product-demo/**` changes.

### Milestone 2 — Expose honest fixture API behavior

Add Pydantic mapping and `/api/v1/demo/**` routes for catalog, projection,
advance, and reset.

Acceptance:

- identity, capability, replay, delay, terminal, malformed, collision, and
  partial-failure cases map as specified;
- the OpenAPI schema contains no `authRef`, credential, arbitrary URL/header,
  provider cursor, corpus path, or live success claim;
- every unit/contract test denies unexpected sockets.

### Milestone 3 — Prove the bounded API worker path

Add `workers/product_demo.py` and explicit one-shot CLI wiring.

Acceptance:

- API and worker use the same application reducer;
- worker output is deterministic and `durability: unavailable`;
- no sleep, polling, lease, database, object, telemetry, or tools substitute is
  introduced.

### Milestone 4 — Package and independent-review handoff

Run package/static checks, retain exact output, and hand an exact clean commit to
fresh review.

Acceptance:

- `make -C apps/api check` and `make -C apps/api package-check` pass offline;
- architecture and docs checks have only the plan-transition diagnostics stated
  below;
- changed paths are exactly `apps/api/**` and this plan;
- independent architecture/API/security review returns `ACCEPT` before any
  coordinator terminal transition.

## Progress

- [x] 2026-07-23 AEST — Drafted from the exact base and current API/corpus
  contracts; prepared for independent plan review.
- [ ] 2026-07-23 AEST — Coordinator records exact accepted fixture implementation
  commit and reviewed dispatch transition.
- [ ] 2026-07-23 AEST — Milestones 1–3 implemented in the bounded API worktree.
- [ ] 2026-07-23 AEST — Offline package, socket-denial, schema, scope, and
  architecture proof retained.
- [ ] 2026-07-23 AEST — Fresh independent implementation review accepted and
  coordinator handoff completed.

## Surprises & Discoveries

- 2026-07-23 AEST — The current worker is only a `--check` smoke path with
  unavailable durability. Evidence:
  `apps/api/src/deepwork_api/bootstrap/worker.py`. Consequence: this plan names an
  exact application worker function and preserves its non-durable truth.
- 2026-07-23 AEST — Corpus case categories and expectations are explicitly not
  public API fields. Evidence: the fixture contract's envelope section.
  Consequence: consumers map data through internal types and never serialize raw
  corpus documents.
- 2026-07-23 AEST — The fixture candidate remains under review and the TS
  candidate requires rework. Consequence: fixture acceptance is the only start
  dependency; TS lock/verification stays parallel and non-blocking.

## Decision Log

- 2026-07-23 AEST — Decision: keep the API consumer in `apps/api/**` only.
  Rationale: Python owns provider/fixture adapters and API contracts; TS and web
  are separate consumers. Consequence: no shared lock or frontend collision.
- 2026-07-23 AEST — Decision: make corpus loading an injected read-only port.
  Rationale: an installed API wheel must not silently bundle or discover a
  mutable repository corpus. Consequence: product-demo bootstrap passes the exact
  accepted path and digest.
- 2026-07-23 AEST — Decision: retain a one-shot non-durable worker function.
  Rationale: it proves worker/application mapping without inventing Postgres
  acceptance. Consequence: the full product-demo integration later supplies
  durable adapters and process lifecycle.
- 2026-07-23 AEST — Decision: all live/gated rows remain unavailable.
  Rationale: fixture evidence cannot promote an external contract. Consequence:
  optional LangChain/auth/HITL/attachment/research/coding rows never block this
  credential-free cell.

## Detailed implementation approach

1. Verify the exact accepted fixture SHA, corpus digest, clean worktree, branch,
   and allowed-path boundary before editing.
2. Add internal domain values and a `ProductDemoCorpusPort`; ensure domain imports
   only standard-library pure helpers.
3. Implement `adapters/fixture/product_demo.py` with the exact byte/depth/count,
   canonical-path, regular-file, no-follow, and replacement checks above,
   explicit accepted schema version, safe field extraction, and no
   validator/module/subprocess use.
4. Add application projection and idempotent logical-tick use cases.
5. Add Pydantic request/response mapping and the four fixture-only routes.
6. Add `workers/product_demo.py`; wire API/worker bootstraps only when the explicit
   fixture arguments are present and fail closed otherwise.
7. Add unit/contract/architecture/public-import/OpenAPI/no-socket tests.
8. Run exact validation, update living evidence, commit only governed paths, and
   stop for independent review.

## Validation and proof

### Plan-authoring candidate

From repository root:

```text
test "$(git branch --show-current)" = "external/planning/w1-product-demo-cells"
test "$(git rev-parse HEAD^)" = "9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2"
python3 -B tools/docs/generate.py --check
python3 -B tools/docs/check.py
git diff --check 9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2 HEAD
git diff --name-only 9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2 HEAD
test -z "$(git status --porcelain)"
```

Before the Coordinator's reviewed/index transition, docs check is expected to
exit `1` for this file with exactly these eight draft diagnostics and no
implementation diagnostic:

1. active ExecPlan is not indexed;
2. unsupported active ExecPlan status `draft`;
3. independent non-owner reviewer metadata missing;
4. completed gate reviewer metadata missing;
5. `reviewed_at` is not a date;
6. `gate_reviewed_at` is not a date;
7. `last_verified_commit` is not an existing full commit; and
8. `gate_review_status` is not `reviewed-with-gates`.

### Implementation candidate

After the exact reviewed dispatch transition:

```text
accepted_fixture_commit="<exact accepted 40-character fixture implementation commit>"
dispatch_commit="<exact reviewed 40-character dispatch commit>"
test "${#accepted_fixture_commit}" -eq 40
git cat-file -e "${accepted_fixture_commit}^{commit}"
git merge-base --is-ancestor "$accepted_fixture_commit" HEAD
test "${#dispatch_commit}" -eq 40
git cat-file -e "${dispatch_commit}^{commit}"
git cat-file -e "${accepted_fixture_commit}:internal/fixtures/product-demo/corpus.json"
PYTHONDONTWRITEBYTECODE=1 python3 internal/fixtures/product-demo/validate.py --check
make -C apps/api check
make -C apps/api package-check
python3 tools/architecture/check.py --root . --graph tools/architecture/graph.json
python3 tools/architecture/check.py --root . --graph tools/architecture/graph.json --fixtures internal/fixtures/architecture --verify-negative
python3 -B tools/docs/generate.py --check
python3 -B tools/docs/check.py
git diff --check "$dispatch_commit" HEAD
git diff --name-only "$dispatch_commit" HEAD
test -z "$(git status --porcelain)"
```

The corpus validator command is a separate dependency-integrity proof run by the
reviewer. Neither API nor worker imports or invokes it. Required retained evidence:

- exact accepted fixture SHA and corpus digest;
- identical API/worker projection digests for the selected cases;
- source-collision, replay, logical-delay, explicit-terminal, unknown, malformed,
  permission, unavailable-with-reason, gated, and partial-failure results,
  including proof that unavailable actions construct no request;
- OpenAPI secret/path/URL scan;
- socket-denial and package-check output;
- architecture result and exact changed-file list; and
- explicit zero `E2E-V1-*` completion.

## Idempotence, rollback, and recovery

- Parsing and projection are deterministic for the same corpus digest, case, and
  logical tick. No wall clock, random ID, sleep, environment, or network value
  affects output.
- Duplicate advance/worker jobs converge by idempotency key and projection digest.
- Key reuse is scoped and payload-bound as specified above; a mismatched digest or
  capacity exhaustion is a conflict, never an eviction or unrelated replay.
- Interrupted implementation is recovered by resetting only modified
  `apps/api/**` files through a new bounded change; the corpus is never rewritten.
- API restart loses process-local demo state and reports that fact. It does not
  claim durability. Reset recreates the fixed start state.
- A corpus version/digest mismatch fails readiness. There is no automatic schema
  upgrade or fallback to embedded data.
- Rollback input is the exact accepted implementation candidate
  `api_candidate` and its reviewed parent `dispatch_commit`. With no API/worker
  process running, the Coordinator verifies that
  `git diff --name-only "${api_candidate}^" "$api_candidate"` is confined to
  `apps/api/**` plus this plan, creates `git revert --no-edit "$api_candidate"`,
  then reruns `make -C apps/api check`, `make -C apps/api package-check`,
  architecture checks, docs checks, and a clean-status check. If the revert
  conflicts or any postcondition fails, the branch remains blocked with the
  exact conflict/output retained; no corpus or external state is changed.
- Any driver/full-stack need discovered here becomes a finding for
  `DW-EXEC-M1-PRODUCT-DEMO-INTEGRATION`; it must not expand this plan's paths.

## Rollout and handoff

This cell is fixture-only and has no deployment rollout. After independent
implementation acceptance, hand the Coordinator:

- exact candidate SHA and parent/dispatch SHA;
- exact accepted fixture SHA/digest;
- commands, exit codes, concise observations, and proof paths;
- changed-file list;
- reviewer identity/verdict and unresolved gates; and
- confirmation of no TypeScript, web, fixture-corpus, root, generated, index,
  live-provider, credential, external-network, push, merge, or deployment change.

The Coordinator may make a separate metadata/index transition. API acceptance
unblocks only the full product-demo integration dependency; it does not enable a
live source or close a feature/E2E scenario.

## Outcomes & Retrospective

Pending implementation. Completion must compare the accepted API/worker mapping
against this purpose, record deviations and proof, name the exact fixture
dependency commit, preserve every open contract fallback, and state that
full-stack persistence/isolation, TypeScript parity, web behavior, live behavior,
and all `E2E-V1-*` scenarios remain outside this cell.
