---
exec_plan_id: DW-EXEC-M1-PRODUCT-DEMO-INTEGRATION
title: Credential-free full product-demo integration and isolation acceptance
status: draft
superseded_by: null
owner: product-demo-integration
reviewed_by: []
reviewed_at: null
primary_feature_id: DW-FND-001
supporting_feature_ids: [DW-FND-002, DW-FND-003, DW-FND-004, DW-FND-005, DW-QUAL-001]
issue: local:DW-M1-PRODUCT-DEMO-001
created: 2026-07-23
last_updated: 2026-07-23
base_commit: 9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2
last_verified_commit: null
risk: high
governed_paths: [apps/api/src/deepwork_api/adapters/product_demo/**, apps/api/src/deepwork_api/bootstrap/product_demo.py, apps/api/src/deepwork_api/workers/product_demo_stack.py, apps/api/tests/integration_tests/product_demo/**, apps/web/src/product-demo/**, apps/web/tests/product-demo/**, tools/product_demo/**, docs/proposals/2026-07-23-product-demo-cells-drafts/DW-EXEC-M1-PRODUCT-DEMO-INTEGRATION.md]
contract_gates: [SPIKE-HARNESS-ARCH-001, SPIKE-WORKTREE-001, SPIKE-DEV-OBS-001, SPIKE-STREAM-001, SPIKE-HITL-001, SPIKE-ARTIFACT-001, SPIKE-MDA-001, SPIKE-FLEET-001, SPIKE-DIRECT-STREAM-001]
decision_gates: [DEC-023, DEC-026, DEC-033, DEC-034, DEC-035, DEC-038]
gate_review_status: unreviewed
gate_reviewed_by: []
gate_reviewed_at: null
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, docs/AGENTS.md, docs/PLANS.md, docs/SECURITY.md, docs/RELIABILITY.md, docs/QUALITY_SCORE.md, docs/design-docs/architecture/application-architecture.md, docs/design-docs/engineering/conventions.md, docs/design-docs/decisions/index.md, docs/product-specs/foundations/dw-fnd-001-repository-oss-and-delivery-foundation.md, docs/product-specs/foundations/dw-fnd-002-design-system-shell-and-demo-mode.md, docs/product-specs/foundations/dw-fnd-003-application-service-state-and-security.md, docs/product-specs/foundations/dw-fnd-004-sdk-stream-and-fixture-contracts.md, docs/product-specs/foundations/dw-fnd-005-domain-identity-status-and-audit-model.md, docs/product-specs/quality/dw-qual-001-accessibility-performance-security-testing-and-release.md, docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md, docs/exec-plans/active/DW-EXEC-M1-FIXTURE-API-CONSUMER.md, docs/exec-plans/active/DW-EXEC-M1-PRODUCT-DEMO-API-RUNTIME-LOCK.md, docs/exec-plans/active/DW-EXEC-M1-WEB-SHELL-HARNESS.md, docs/exec-plans/active/DW-EXEC-M1-WEB-LOCK-EXTENSION.md, docs/exec-plans/active/DW-EXEC-M1-WEB-TS-REVERIFY.md, docs/exec-plans/active/DW-EXEC-M1-TS-PACKAGES-SCAFFOLD.md, docs/exec-plans/external/DW-EXT-W1-WORKTREE-ARCH-HARNESS.md]
scenario_ids: [AC-DW-FND-001-01, AC-DW-FND-001-02, AC-DW-FND-001-05, AC-DW-FND-001-07, AC-DW-FND-002-01, AC-DW-FND-002-02, AC-DW-FND-003-05, AC-DW-FND-004-04, AC-DW-FND-004-05, AC-DW-FND-005-01, AC-DW-QUAL-001-07]
dispatch_kind: cell
dispatch_ready: false
agent_review_required: true
dependencies: [DW-EXEC-M1-FIXTURE-CONTRACT, DW-EXEC-M1-FIXTURE-API-CONSUMER, local:DW-M1-PRODUCT-DEMO-API-RUNTIME-LOCK-001, local:DW-M1-FIXTURE-API-SDK-CONTRACT-001, local:DW-M1-WEB-TS-REVERIFY-001]
blockers: [local:DW-M1-DUAL-STACK-POLICY-EXCEPTION-001]
---

# Credential-free full product-demo integration and isolation acceptance

Plan state: **prepared for independent review**. This plan is an unindexed,
non-dispatchable draft carried over from an external planning bundle. Its
dependency list names `local:DW-M1-PRODUCT-DEMO-API-RUNTIME-LOCK-001` and
`local:DW-M1-WEB-TS-REVERIFY-001` (both other drafts in this same archive) and
`local:DW-M1-FIXTURE-API-SDK-CONTRACT-001`, which resolves only to an unindexed
draft in PR #9's `docs/proposals/2026-07-23-ts-proof-consumer-drafts/` archive.
None of these are accepted, reviewed, or indexed ExecPlans. A sibling draft in
this archive (`DW-EXEC-M1-FIXTURE-API-CONSUMER.md`) references a commit SHA
(`3fbdb01be06152cc39e50f6378dfb625daed8998`) that does not exist in repo
history; because this plan depends transitively on that consumer, resolve that
reference too before treating this bundle as executable. Treat every claim
below as proposed, not authoritative, until a coordinator
independently reviews, rebases, and resolves all dependency and commit
references, and promotes a rewritten version to `docs/exec-plans/active/`.

## Purpose and observable result

Compose the independently accepted fixture corpus, API/worker consumer,
TypeScript fixture consumer, and responsive web shell into Deep Work's only
full-stack/product-demo implementation worktree. One stack runs:

- the real accepted Next.js web app;
- the real accepted FastAPI fixture API;
- the bounded `apps/api` product-demo worker;
- real local PostgreSQL for demo state/job/outbox rows;
- a loopback fixture object service for bounded synthetic bytes;
- a loopback fixture OTLP/telemetry recorder; and
- the reviewed `tools/product_demo/worktree_driver.py` process supervisor.

The same reviewed driver then starts two simultaneous stacks from two clean roots,
proves distinct workspace resources, rejects deliberate collisions before
startup, demonstrates bidirectional no-cross-observation, restarts each stack
without rotating its reservation, tears down one while the peer remains healthy,
and proves exact scoped cleanup. The accepted evidence closes
`SPIKE-WORKTREE-001`; the synthetic allocator self-test alone does not.

The result requires no external provider/model/GitHub/notification credential and
makes no non-loopback runtime request. Optional LangChain/auth/attachment/HITL,
research, writing, coding, MDA, Fleet, PWA, push, and desktop rows remain
unavailable or gated and never block the credential-free product demo.

This plan contributes bounded fixture evidence to the scenario IDs in front
matter. It completes zero `E2E-V1-*` scenarios. In particular, an early web shell
plus `/health` demonstration is a useful pre-integration smoke only; it is not the
full product demo, does not close `SPIKE-WORKTREE-001`, and does not complete
`AC-DW-FND-001-01` or `AC-DW-QUAL-001-07`.

Status is **draft, prepared for independent review**. The rejected one-file draft
at `2f5ba825` is not accepted authority and is not reused. Execution begins only
after every persistent dependency below is terminal at an exact independently
accepted commit.

## Context and orientation

The exact plan-authoring base is
`9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2`. At that base:

- the worktree/architecture harness is implemented and its synthetic allocator
  proof passes, but its real matrix is `implemented-not-accepted`;
- `tools/worktree/harness.py` deliberately blocks because
  `tools/product_demo/worktree_driver.py` and
  `tools/product_demo/worktree-driver-contract.json` do not exist;
- the harness allocates four collision-free loopback ports (`api`, `web`,
  `worker`, `telemetry`), a database, schema, object prefix, browser origin and
  storage key, telemetry namespace, logs/proof paths, and process identities;
- `apps/api` has liveness and honest non-durable fixture status only;
- `apps/web` does not exist;
- the fixture candidate
  `8291218590e3f6a91a5383ae91d6e909e71b1fbe` remains under fresh independent
  review; and
- the TS candidate `1bf66e1` and the previous product-demo draft `2f5ba825` are
  both `REWORK REQUIRED`.

The existing harness is the verifier and reservation authority. This plan does
not edit `tools/worktree/**`, `internal/fixtures/worktree/**`, retained harness
evidence, or `internal/adapter-tests/**`. The product-demo driver consumes its two
owned private manifests and returns evidence in the exact schema already enforced
by `tools/worktree/harness.py`.

## Scope

### In scope

- Only the exact governed paths in front matter and this living ExecPlan.
- Product-demo Postgres/object/telemetry adapters under
  `apps/api/src/deepwork_api/adapters/product_demo/**`.
- Exact stack bootstrap in
  `apps/api/src/deepwork_api/bootstrap/product_demo.py`.
- Exact durable fixture worker loop in
  `apps/api/src/deepwork_api/workers/product_demo_stack.py`; it leases only
  product-demo rows from the injected schema, invokes the accepted
  `workers/product_demo.py` application function, writes bounded synthetic object
  evidence, emits sanitized telemetry, and exposes deterministic readiness through
  the driver's process-control channel.
- API integration tests under
  `apps/api/tests/integration_tests/product_demo/**`.
- App-level product-demo repository injection and integrated state tests only
  under `apps/web/src/product-demo/**` and
  `apps/web/tests/product-demo/**`. Existing shell/routes/packages are consumed
  read-only except for these exact integration seams.
- `tools/product_demo/worktree_driver.py`,
  `tools/product_demo/worktree-driver-contract.json`, driver tests, and bounded
  fixture service helpers under `tools/product_demo/**`.
- One early single-stack shell/health smoke with a permanent
  `Demo data · Product demo` base marker plus a separate explicit incomplete
  proof-tier label.
- One real single-stack integrated fixture journey through web -> API ->
  Postgres/outbox -> worker -> object service -> telemetry.
- The harness-controlled two-root matrix, collision/failure injection, restart,
  no-cross-observation, scoped teardown, cleanup recovery, retained receipt, and
  verification.
- A non-circular review/seal lifecycle for the driver and exact contract.
- Numeric disk/memory/cache/object/log/evidence preflight and fail-closed cleanup.

### Non-goals

- Root `package.json`, `pnpm-workspace.yaml`, `pnpm-lock.yaml`, `turbo.json`,
  root `Makefile`, `.node-version`, `.npmrc`, generated docs, program/index plans,
  `docs/plans/**`, `internal/adapter-tests/**`, fixture corpus, architecture/
  worktree harness source, or sibling repositories.
- A new TypeScript importer, dependency, or lock change. If an integration seam
  reveals one, stop and route it through the Coordinator's lock-extension and full
  TS re-verification sequence before resuming.
- Live provider/auth/source, real object cloud, external OTLP backend, external
  database, model execution, GitHub, email/push, deployment, production migration,
  or real credential.
- Claiming browser-local harness screenshots or API health as full-stack proof.
- Replacing the `apps/api` worker with a tools-only simulation.
- Closing `SPIKE-DEV-OBS-001` from the fixture recorder or promoting any external
  runtime capability.
- Broad cleanup, killing by unverified PID/name, deleting outside exact namespace
  paths, pulling container images/packages, installing tools, or using unresolved
  globs/environment variables.
- Completing a feature scenario, release criterion, or any `E2E-V1-*` scenario.

### Permissions and risk boundary

- This is the only application/full-stack product-demo authoring worktree until
  `SPIKE-WORKTREE-001` is accepted. Package/docs cells may remain parallel only
  when their paths are disjoint.
- The second root used by final acceptance is a clean, detached, acceptance-only
  peer at the exact sealed commit. It is not a second authoring worktree.
- No install, image pull, registry access, external network, credential,
  production data, push, merge, deploy, publish, or destructive migration is
  authorized.
- All services bind `127.0.0.1` or a namespace-owned Unix socket. The driver
  clears proxy variables and uses an allow-listed child environment.
- PostgreSQL runs with fixture-only local trust on a namespace-owned Unix socket;
  no password/token is generated or recorded. The object and telemetry fixture
  services accept only loopback plus exact namespace headers generated from the
  private reservation; those values never enter public evidence.
- Cleanup operates only on verified child PIDs/process groups, exact reservation
  paths, exact database/schema, exact object prefix, and exact evidence namespace.
  It refuses broad or mismatched targets.
- Independent architecture, product/UX, security/reliability, and developer-
  experience review is mandatory for the plan, unsealed implementation candidate,
  mechanical seal, and final evidence. The author cannot self-approve.

## Authoritative sources and prerequisites

### Persistent dependency DAG

Every direct row in front matter is a terminal dependency, not a transient
milestone:

| Stable dependency | Exact terminal requirement | Current state |
|---|---|---|
| `DW-EXEC-M1-FIXTURE-CONTRACT` | Accepted corpus implementation SHA/digest, independent `ACCEPT`, exact scope/validator evidence | Nonterminal at this plan-authoring base. |
| `DW-EXEC-M1-FIXTURE-API-CONSUMER` | Final command/projection ports, `202` wire, cookie/Origin/CSRF, deterministic OpenAPI, process-local fallback, independent acceptance | Draft in this bundle. |
| `local:DW-M1-PRODUCT-DEMO-API-RUNTIME-LOCK-001` | Exact SQLAlchemy 2/Alembic/Psycopg 3 pins, API lock digest, frozen offline package/import/OpenAPI proof | Draft in this bundle; starts only after API consumer terminal. |
| `local:DW-M1-FIXTURE-API-SDK-CONTRACT-001` | Accepted generated client from the terminal API OpenAPI plus handwritten public SDK transport/mapping and adapter conformance | Concurrent separately owned draft; absent from this checkout until integrated. |
| `local:DW-M1-WEB-TS-REVERIFY-001` | Immutable final-lock proof across domain/SDK/UI, generated client, private adapter tests, web, and browser-local harness | Draft in this bundle; depends on terminal web lock. |

The correct transitive private corpus-consumer alias is
`local:DW-M1-FIXTURE-TS-CONSUMER-001`, not the previous invalid
`local:DW-M1-TS-FIXTURE-CONSUMER-001`. It feeds the API-SDK bridge's conformance
work but does not supply public HTTP transport itself, so the product demo depends
on the terminal bridge rather than listing the private consumer as a transport
owner.

The full DAG is:

```text
TS source -> first TS lock -> TS verify -> private fixture TS consumer --\
fixture corpus -> API consumer -> API-SDK bridge -------------------------+\
                         \-> product-demo API runtime lock -----------------+-> product demo
TS verify -> terminal web source -----------------------------------------/
{terminal web source, terminal API-SDK bridge} -> web lock -> web reverify -/
```

The API consumer may run alongside the disjoint TS chain after fixture
acceptance. The runtime-manifest cell is package-only and follows the API
consumer. The web source is a whole terminal static cell before the lock
extension; there is no dependency on a mid-plan importer milestone. Product-demo
execution waits until every direct row is terminal at one Coordinator integration
base. No dependency points back to this plan.

### Canonical dual-stack policy blocker

`AGENTS.md`, `docs/PLANS.md`, and the canonical program currently permit at most
one running full-stack/product-demo worktree until `SPIKE-WORKTREE-001` passes.
The final matrix in this plan necessarily starts two complete product-demo stacks
to produce the evidence that can close that spike. Calling one checkout
“acceptance-only” does not itself override the canonical rule.

Therefore `local:DW-M1-DUAL-STACK-POLICY-EXCEPTION-001` is an explicit terminal
blocker. Before this plan may become dispatch-ready, a separate canonical-owner
change must be independently reviewed and accepted with exactly this narrow
exception:

> For the single final `SPIKE-WORKTREE-001` acceptance exercise only, the
> Coordinator may run one sealed, read-only acceptance root and one clean,
> detached, read-only peer at the identical sealed commit. The harness must
> allocate and preflight all resources before startup, prohibit edits, installs,
> provider/external traffic, credentials, and concurrent full-stack authoring,
> retain scoped evidence, stop both stacks, prove cleanup, and remove the peer.
> Failure preserves the one-active-full-stack fallback and grants no spike
> acceptance.

This plan proposes that exact text but does not edit `AGENTS.md`,
`DW-EXEC-PROGRAM-CANONICAL.md`, `docs/PLANS.md`, or the decision register. Until a
reviewed canonical change installs the exception and the Coordinator records its
full SHA, execution remains single-stack and this plan remains non-dispatchable.
After an accepted exercise, ordinary full-stack authoring remains serial until
the Coordinator separately integrates the evidence and closes
`SPIKE-WORKTREE-001`.

### Root/generated/lock ownership

- Root manifests, workspace declarations, Turbo, `pnpm-lock.yaml`, and root
  `Makefile` remain Coordinator-owned.
- The accepted web and SDK manifests are already final inputs. The terminal
  `local:DW-M1-WEB-LOCK-EXTENSION-001` owns only `pnpm-lock.yaml` with exactly
  zero manifest delta; `local:DW-M1-WEB-TS-REVERIFY-001` proves the immutable
  result. If integration needs any new importer/dependency, stop and create a new
  source-owner -> lock -> reverify chain.
- The API consumer owns deterministic
  `apps/api/openapi/deepwork-api-v1.json`; the API-SDK bridge consumes it
  read-only and owns `docs/generated/openapi.json` plus bounded SDK/adapter
  generated outputs. This plan consumes both accepted artifacts read-only and
  requires zero drift; it never hand-edits or regenerates them.
- `local:DW-M1-PRODUCT-DEMO-API-RUNTIME-LOCK-001` owns only
  `apps/api/pyproject.toml` and `apps/api/uv.lock`. The product-demo integration
  may use the accepted packages but cannot change either file.
- `internal/adapter-tests/**` stays with the separately accepted TS fixture
  consumer/API-SDK bridge chain and never becomes product-demo ownership.

### Optional capability fallbacks

All open provider/platform gates remain unavailable:

| Optional row | Product-demo fallback |
|---|---|
| LangChain/classic live source and auth | Synthetic fixture source; no provider request |
| HITL submit/plan approval | Read-only ordered fixture with gated submit |
| Attachments/artifacts | Bounded synthetic object metadata and fixture bytes only |
| Research/writing verification | Fixture unavailable/manual evidence label |
| Coding/sandbox/GitHub/terminal/browser | Unavailable with safe explanation and no outbound action |
| MDA/Fleet/direct stream | Gated/unknown; no route or guessed request |
| PWA/push/Tauri | Ordinary responsive loopback web; no install/push/native claim |

## Interfaces and invariants

### Final composition paths and responsibilities

```text
apps/api/src/deepwork_api/adapters/product_demo/
  postgres.py       # exact schema/job/projection adapter
  objects.py        # loopback fixture object client
  telemetry.py      # loopback fixture OTLP client
apps/api/src/deepwork_api/bootstrap/product_demo.py
apps/api/src/deepwork_api/workers/product_demo_stack.py
apps/api/tests/integration_tests/product_demo/**

apps/web/src/product-demo/
  integration.tsx    # replaces accepted disabled seam; explicit mode composition
  repository.ts     # accepted SDK ports -> fixture API
  provider.tsx      # explicit composition only
  marker.tsx        # persistent base marker plus proof-tier disclosure
apps/web/tests/product-demo/**

tools/product_demo/
  worktree_driver.py
  worktree-driver-contract.json
  services/object_service.py
  services/telemetry_service.py
  tests/**
```

Existing API domain/application/contracts/worker consumer and existing web
shell/routes are read-only dependencies unless an exact governed seam above is
insufficient. Any broader path need returns the plan to review.

The app-local `repository.ts` calls only the accepted public
`@deepwork/sdk/product-demo` `ProductDemoFixtureClient`. The accepted TS fixture
consumer owns loopback URL/method/body/response mapping through
`createProductDemoFixtureClient`; `apps/web/src/product-demo/**` supplies the
driver-issued origin/session inputs and normalized app callbacks but contains no
raw `fetch`, URL construction, wire DTO decoding, or deep import. If that public
entry is absent or differs at terminal dependency review, this plan remains
blocked rather than recreating transport locally.

`integration.tsx` is the only file imported by the accepted shell. It reads the
explicit immutable composition mode supplied by the web bootstrap: `ui-harness`
continues to return the accepted disabled seam, while `product-demo` composes
`provider.tsx`, `repository.ts`, and `marker.tsx`. It never switches modes after
an error and never falls back from API-backed product demo to browser fixtures.

### Exact service topology

For each private harness manifest:

| Component | Binding/storage | Process/cleanup rule |
|---|---|---|
| Web | `http://127.0.0.1:<ports.web>`; browser key exactly `browser.storage_key` | Driver-owned process group; no external origin |
| API | `http://127.0.0.1:<ports.api>` | Driver-owned process group; fixture mode and corpus digest required |
| Worker | No public listener; readiness/control over a namespace-owned Unix socket. The reserved `<ports.worker>` is used by the object fixture service. | Exact worker child PID/process group; leases only manifest database/schema |
| PostgreSQL | Namespace-owned data directory and Unix socket under `workspace_path`; TCP disabled | Exact postmaster PID and data/socket path; exact database/schema dropped before data dir removal |
| Object service | `http://127.0.0.1:<ports.worker>`; bytes under exact `object_prefix` inside namespace storage | Exact child PID; delete only prefix, then empty namespace root |
| Telemetry | `http://127.0.0.1:<ports.telemetry>`; records exact manifest resource attributes | Exact child PID; delete only namespace telemetry files |
| Logs/proof | Exact `logs_path` and `proof_path`; private manifests/tokens never copied | Evidence sanitized before harness receipt; cleanup records absence |
| Browser | Pre-existing browser binary and automation runtime pinned by the accepted web lock; one driver-owned profile/context beneath the namespace `workspace_path` | Exact browser PID/process group/profile; context uses only manifest origin/storage key and is destroyed before namespace cleanup |

The reserved port label remains unchanged for harness compatibility; the driver
records that `ports.worker` is the product-demo auxiliary service port while the
worker control channel is a private Unix socket. No additional unreserved
loopback port is opened.

All namespace directories and browser/Postgres/object/telemetry state roots are
created mode `0700`; private manifest copies, service capabilities, cookies,
receipts, and socket files are mode `0600` (Unix socket parent remains `0700`).
The driver rejects symlinks, group/world permissions, wrong ownership, or a
platform that cannot enforce those modes.

The driver generates distinct 256-bit ephemeral capabilities for API session/
mutation, object writer, telemetry writer, and worker control after reservation.
They are stored only in the private `0700` namespace root as `0600` files, never
printed or placed in retained/public evidence, and never equal or derive from the
harness teardown token, receipt key, run nonce, namespace, port, or public
manifest values. The browser receives an HttpOnly, SameSite=Strict loopback
session cookie and a separate CSRF nonce through the exact web bootstrap. API
mutations require exact manifest Origin, namespace/session binding, CSRF
cookie/header match, and canonical request digest. Object/telemetry/worker
channels accept only their own capability. Wrong-origin, wrong-namespace,
missing/wrong-token, cross-stack-token, and teardown-token-as-service-token
probes are required in both directions and must fail without revealing whether a
peer resource exists.

### PostgreSQL, object, worker, and telemetry behavior

- PostgreSQL is a real local server executable discovered by `doctor`; the driver
  never downloads it. It creates only the manifest database and schema.
- The schema has bounded product-demo tables for fixture session/projection,
  idempotency, job/outbox, object metadata, and sanitized audit. It contains no
  migration claim outside the demo namespace.
- In full-stack mode API advance is the sole command-intake owner: one
  transaction writes the namespace/session-scoped idempotency record and one
  immutable pending command/outbox row, then returns `202 pending`. It does not
  advance or expose a new projection.
- `product_demo_stack.py` leases one row with bounded expiry, invokes the accepted
  pure `process_fixture_step`, and is the sole durable projection-transition
  owner. It writes a bounded synthetic object when required; then one database
  transaction compares the immutable input digest/current projection, writes the
  next projection and object metadata/audit, and marks the job terminal. A crash
  after object write but before commit reconciles the same object checksum and
  commits once; a digest mismatch is a blocked conflict. Telemetry is emitted
  after commit under the same correlation ID and may mark observability degraded
  but cannot change product success. API reads expose the new projection only
  after that worker transaction commits.
- Durable idempotency is uniquely scoped by
  `(namespace, synthetic_session_id, operation, idempotency_key)` and stores a
  canonical request SHA-256. Same scope/key plus the same digest returns the
  original command/result; a different digest is `409` with no new job/effect.
  Retention is the namespace lifetime with a hard maximum of `4,096` rows per
  namespace; capacity rejects new commands and never evicts silently.
- The object service is a standard-library loopback fixture service with exact
  namespace/prefix, content type, size, checksum, and no directory traversal.
- The telemetry service is a standard-library loopback fixture OTLP-shaped
  recorder. It accepts only bounded JSON, exact namespace attributes, and
  redacted identifiers. It proves local correlation, not an external collector or
  `SPIKE-DEV-OBS-001`.
- The API exposes dependency readiness distinct from process liveness. Web shows
  partial/error/stale states when worker, database, object, or telemetry is
  unavailable and never falls back to browser fixtures.
- The accepted shell already imports the stable
  `apps/web/src/product-demo/integration.tsx` seam. This plan replaces only that
  subtree; it does not edit accepted root layout, routes, or shell composition.
- Every product-demo route preserves the non-dismissible base marker
  `Demo data · Product demo`. A second adjacent text label reports
  `Proof tier: shell/health smoke`, `Proof tier: single-stack product demo`, or
  `Proof tier: dual-stack worktree acceptance`. Proof tier never replaces or
  weakens the base demo-data disclosure.

### Browser lifecycle and fail-closed egress

`doctor` requires the already-cached browser executable/runtime named by the
accepted frozen web lock, records its version and executable SHA-256, and fails
with `processes_started: 0` if it is absent; no browser download is allowed. Each
stack gets a distinct driver-owned profile/context below its `0700`
`workspace_path`, exact manifest origin, and exact storage key. The driver records
browser PID/process-group identity, reloads that context during restart proof,
probes the peer origin/storage key in both directions, closes the context/profile,
and proves the PID group and profile absent during cleanup.

Before importing application code, Python processes install the reviewed socket/
DNS guard and Node processes load the reviewed `--require` guard. Both permit
only Unix sockets owned by the namespace and the exact allocated `127.0.0.1`
ports, reject DNS and every other IPv4/IPv6 destination, and append sanitized
attempt classes to the namespace egress log. Browser automation aborts every
request/navigation outside its exact manifest origin/static assets/API allowlist
and launches with external DNS resolution disabled. PostgreSQL TCP is disabled.
In parallel, the driver samples every child process tree's open sockets at
`250 ms`; an observation gap over `1,000 ms` while a child is alive, a guard
installation failure, an unclassified socket, or any non-loopback attempt stops
the run and triggers recovery cleanup. Tests deliberately attempt DNS, public
IPv4/IPv6, wrong loopback ports, peer ports/origin, WebSocket/EventSource/beacon,
and raw Python/Node/browser socket paths. The retained network sidecar reports
allowed/rejected classes and zero unguarded/non-loopback attempts without raw
addresses or capabilities.

### Early smoke versus real acceptance

| Proof tier | Components | Allowed claim |
|---|---|---|
| `shell-health-smoke` | Web shell, API `/health`, persistent base marker plus `Proof tier: shell/health smoke` | Route/build/loopback health only; zero persistence/worker/object/telemetry/isolation claim |
| `single-stack-product-demo` | Web, API, worker, PostgreSQL, object, telemetry | One integrated fixture journey and failure recovery in one namespace |
| `dual-stack-worktree-acceptance` | Two simultaneous complete stacks plus harness receipt/verifier | Required evidence for `SPIKE-WORKTREE-001` and bounded contribution to `AC-DW-FND-001-05` |

Only the third tier can close the spike. None proves a live provider or E2E release
scenario.

### Driver static contract

`worktree-driver-contract.json` has exactly the fields required by the existing
harness:

```text
components
contract_version
credential_free
driver_path
driver_sha256
loopback_only
protocol
reviewed_repository_commit
```

It sets protocol `deepwork-dual-product-demo-v1`, contract version `1`,
canonical driver path, components containing exactly at least web/API/worker/
postgres/object/telemetry, `credential_free: true`, and `loopback_only: true`.
`driver_sha256` is the exact SHA-256 of the driver bytes. No extra field is added
because the harness rejects an inexact schema.

### Reproducible non-circular seal

The driver contract's Git provenance is sealed without asking one commit to
contain its own hash:

1. **Unsealed implementation candidate `C`.** Commit all governed implementation
   paths. Compute and store the exact driver SHA-256. Set
   `reviewed_repository_commit` temporarily to the known ancestor implementation
   base. `doctor` must fail closed because that ancestor lacks the reviewed driver
   blobs. Run all component/unit/single-stack checks that do not require the
   harness seal.
2. **Fresh review of `C`.** Architecture, product/UX, security/reliability, and DX
   reviewers inspect the exact commit and return `ACCEPT` or rework. No author
   self-approval.
3. **Coordinator seal commit `S`.** After acceptance, the Coordinator changes
   only `reviewed_repository_commit` in
   `worktree-driver-contract.json` from the ancestor to exact `C`; driver bytes and
   all other semantic contract fields remain byte/semantically unchanged.
4. **Seal proof.** Prove `S^ == C`, the diff is exactly the single JSON field,
   `C` contains the driver and contract blobs, current driver bytes equal the blob
   at `C`, `driver_sha256` matches both, and canonical contract semantics excluding
   `reviewed_repository_commit` are identical at `C` and `S`.
5. **Driver readiness.** At `S`, `tools/worktree/harness.py doctor --root .`
   returns `static-contract-ready`. Create the clean peer at exact `S`; both roots
   must report the same driver SHA and reviewed commit.
6. **Acceptance execution and review.** Run dual exercise/verify, retain private
   receipt plus sanitized evidence, and obtain fresh review of exact `S` plus
   evidence. Any driver or semantic contract change invalidates the seal and
   repeats from step 1 with a new candidate.

This lifecycle is non-circular because `C` is reviewed before its hash is written
into descendant `S`, while the harness deliberately excludes only
`reviewed_repository_commit` from semantic comparison.

### Receipt-compatible sealed acceptance bundle

The fixed harness v1 `exercise.json` schema cannot gain fields, and its
`allocation_digests` map must remain exactly the two namespace allocation
digests. It is never extended or overloaded. The sealed driver writes these seven
sanitized sidecars plus one bundle manifest beside `exercise.json`, each with
exact top-level keys and no extras:

| Sidecar | Exact top-level keys | Exact record purpose |
|---|---|---|
| `collision.json` | `schema_version,evidence_class,run_nonce,driver_revision,driver_sha256,cases,status` | `cases[]`: `id,target,expected,actual,processes_started,resources_reserved,result_digest` |
| `failure-matrix.json` | same, replacing `cases` with `failures` | `failures[]`: `id,stage,injection,expected,recovery,cleanup,result_digest` |
| `resource-samples.json` | `schema_version,evidence_class,run_nonce,driver_revision,driver_sha256,limits,cache_inventory,samples,maxima,monitor_gaps,status` | monotonic timestamp, namespace/process-group tree RSS, exact-root bytes, sockets, and bound maxima/gaps |
| `network-egress.json` | `schema_version,evidence_class,run_nonce,driver_revision,driver_sha256,guards,probes,attempt_summary,status` | guard installation plus allowed/rejected destination classes; no raw token/address |
| `browser-acceptance.json` | `schema_version,evidence_class,run_nonce,driver_revision,driver_sha256,viewports,states,accessibility,artifacts,status` | API-backed/N/A state rows, marker/tier, keyboard/focus/announcement, contrast/motion/a11y evidence |
| `secret-scan.json` | `schema_version,evidence_class,run_nonce,driver_revision,driver_sha256,scanned_paths,rule_ids,findings,status` | sanitized leak scan with zero secret/raw-private-manifest findings |
| `peer-cache.json` | `schema_version,evidence_class,run_nonce,driver_revision,driver_sha256,source_root,peer_root,source_inventory,peer_inventory,bytes,cleanup,status` | offline copied-runtime identity and exact peer-cache cleanup |
| `bundle-manifest.json` | `schema_version,evidence_class,run_nonce,driver_revision,driver_sha256,sidecars,status` | `sidecars` maps exactly `collision.json,failure-matrix.json,resource-samples.json,network-egress.json,browser-acceptance.json,secret-scan.json,peer-cache.json` to full SHA-256 values |

Every record digest is SHA-256 over canonical JSON excluding its digest field.
Every sidecar is at most `3,145,728` bytes, regular, non-symlinked, mode `0600`,
and matches the invocation run nonce/revision/driver SHA. `dual-exercise`
canonicalizes `bundle-manifest.json`, computes its full SHA-256, and sets the
harness-native `exercise_id` to exactly `p` plus the first 63 lowercase hex
characters of that digest. This 252-bit content-derived ID satisfies the existing
64-character synthetic-ID grammar without changing any harness key. The existing
receipt HMAC already binds `exercise_id`; it therefore binds the content-derived
bundle identifier while `allocation_digests` remains canonical.

The sealed `verify-bundle` subcommand requires canonical harness `verify` to pass,
enforces every exact sidecar/nested schema, recomputes each record/file/bundle
digest, and checks that `exercise_id == "p" +
sha256(canonical_bundle_manifest)[:63]`. Missing, extra, oversized, mismatched, or
non-passing evidence is rejection. Fresh reviewers inspect the sealed driver
tests for this derivation. Thus the seven sidecars are transitively identified by a
252-bit bundle digest carried in the HMAC-bound native `exercise_id`, without
changing `tools/worktree/**`, overloading allocation digests, adding a forbidden
evidence key, or reusing the private receipt authority.

### Offline acceptance-peer preparation

The clean peer contains tracked bytes at exact seal `S` but no ignored runtime
artifacts. After seal proof and before harness reservation, the sealed
`prepare-peer` subcommand copies only these already-accepted ignored runtime
roots from the primary: `apps/api/.venv`, `apps/web/.next` built with Next
standalone output, and `apps/web/.browser-cache`. It never installs, resolves, or
downloads. It rejects an existing peer target, hard link/device/FIFO/socket,
absolute symlink, symlink escaping its copied root, and any external symlink
except the exact system Python executable already recorded by API verification
with matching SHA-256.

Copy occurs into mode-`0700` temporary siblings in the peer and is atomically
renamed only after regular-file relative-path/size/SHA-256/mode inventories match
the primary. Combined copied bytes must be at most `4,294,967,296`; insufficient
peer disk fails before harness reservation. Git status in both roots remains
clean because these exact paths are ignored. `dual-exercise` records both
inventories in `peer-cache.json` and, after all peer children exit, deletes only
the copied peer roots by their verified inode/device/inventory, records absence,
and never deletes primary caches. If exercise does not start,
`clear-peer-cache` performs the same verified peer-only cleanup. The Coordinator
owns this acceptance-only preparation; it is not a second authoring lane.

### Numeric resource preflight

Before reservation or process start, `driver doctor` and the harness wrapper fail
closed unless all are true:

- free bytes on both checkout/temp state filesystems: at least
  `12,884,901,888` (12 GiB);
- available physical memory: at least `6,442,450,944` (6 GiB);
- maximum observed combined child-tree RSS for two stacks:
  `4,294,967,296` bytes (4 GiB);
- maximum per-stack persistent disk allocation: `2,147,483,648` bytes (2 GiB);
- required pre-existing tool/image/dependency cache footprint:
  `4,294,967,296` bytes (4 GiB) or less, with every required artifact already
  present; no pull/download is attempted. On the primary, the sealed driver
  derives only `apps/api/.uv-cache`, `apps/api/.venv`, `node_modules/.pnpm`,
  `apps/web/.next`, and `apps/web/.browser-cache`; on the peer it permits only the
  three copied runtime roots above. The accepted API/web verification cells must
  prepare them, including standalone web output, and ignore build/browser caches.
  Missing, duplicate, unapproved-symlinked, group/world-writable, or broader
  parent roots fail. The driver inventories only approved regular files/symlinks
  from those roots as relative path, bytes, mode, target class, and SHA-256 before
  startup and after teardown;
- PostgreSQL data limit per stack: `536,870,912` bytes (512 MiB);
- object bytes per stack: `134,217,728` bytes (128 MiB);
- browser Cache Storage/local harness storage per stack: `67,108,864` bytes
  (64 MiB);
- logs per stack: `134,217,728` bytes (128 MiB);
- proof/evidence per stack: `268,435,456` bytes (256 MiB); and
- every allocated port/socket/path is absent and both manifest allocations are
  distinct before any child starts.

From before the first child starts until every child exits, a monitor samples at
`50 ms`: the summed RSS of each process group including descendants, combined
dual-stack RSS, and open sockets. It also records every portable OS-reported
per-child high-water mark at exit. It samples exact namespace
data/cache/log/proof roots at `1,000 ms`, plus immediately before/after injected
failure, restart, and teardown. A monitor gap over `250 ms` while any child is
alive is itself failure.
Crossing a limit stops new work, records a sanitized resource failure, and
invokes exact recovery cleanup. The complete bounded sample log, observed maxima,
monitor gaps, cache inventories/hashes, and limit verdict are written to the
resource sidecar and identified by the receipt-compatible bundle above. The
evidence is explicitly `observed-sampled-rss`, not proof that no sub-50-ms
transient existed. A resource failure or observed over-limit sample cannot be
converted into a passing isolation result; platforms offering an accepted
cgroup/job-object group limit additionally enforce and record the same 4 GiB
hard ceiling, but that optional stronger mechanism is not claimed where absent.

### Collision and failure matrix

- duplicate namespace/reservation;
- pre-bound API/web/object/telemetry port;
- existing database or schema;
- existing object prefix;
- browser storage-key reuse;
- telemetry namespace reuse;
- proof/log path reuse or unsafe symlink/permissions;
- invalid/mismatched private manifest;
- wrong origin/namespace/service capability, cross-stack capability, and
  attempted teardown-token reuse at API/object/telemetry/worker boundaries;
- same scoped idempotency key with a different canonical request digest and
  namespace capacity exhaustion;
- DNS/public IPv4/public IPv6/wrong-loopback-port/raw-runtime egress attempts;
- API, worker, Postgres, object, telemetry, and web startup failure;
- worker crash after object success before acknowledgement;
- API restart and browser reload;
- peer teardown while the other remains ready; and
- recovery cleanup after driver failure/timeout.

Every preflight collision produces zero started processes and no partial
reservation. Every injected runtime failure either recovers deterministically or
produces a blocked/failed result plus complete scoped cleanup evidence.

## Full-stack state matrix

| State | Integrated behavior | Proof |
|---|---|---|
| Preflight loading | No reservation/process until numeric/tool/path checks pass | Doctor JSON |
| Missing local tool/cache | Blocked with exact requirement; no download | `processes_started: 0` |
| Shell/health smoke | Marker plus process health; explicit incomplete tier | Screenshot/health JSON |
| Product-demo a11y/reflow | API-backed provider at 320px and desktop; persistent base marker and proof tier; keyboard/focus/announcement, non-color status, reduced-motion, forced-colors, and automated accessibility | Browser trace, DOM assertions, screenshots, accessibility report |
| Fixture empty | API-backed empty projection stored in namespace DB | Web/API/DB correlation |
| Success | Advance -> transaction/job -> worker -> object/telemetry -> web projection | One correlation/idempotency chain |
| Partial source failure | Healthy fixture rows plus source-scoped error | Same corpus expectation |
| Offline/browser disconnect | Web read-only/stale; server work continues | Reconnect without duplicate |
| API unavailable | Web source-scoped error; no browser fixture fallback | Request/DOM proof |
| Worker unavailable | Accepted job visible pending/degraded; no false completion | DB/readiness proof |
| PostgreSQL unavailable | Readiness fails; mutations stop | No in-memory success |
| Object unavailable | Worker classifies retryable failure; no missing artifact success | Job/object evidence |
| Telemetry unavailable | Product result follows stated policy; observability degraded visibly | No fabricated telemetry |
| Permission/gated/unavailable | Typed fallback; zero external request | Network summary |
| Stale mutation | Conflict; no second job/effect | Idempotency/audit proof |
| Same key/different digest | `409`; original command/result retained | DB unique-key/digest proof |
| Wrong origin/namespace/capability | Deny before lookup/mutation; no peer disclosure | Bidirectional negative probes |
| Worker crash after effect | Restart reconciles one object and one terminal job | At-most-once effect |
| API restart | DB state retained; new process identity; web rehydrates | Projection digest parity |
| Browser reload | Exact storage key and current server projection | No cross-root cache |
| Unknown/malformed record | Safe bounded error/projection | No process crash |
| Resource limit exceeded | Stop/blocked, sanitized evidence, scoped cleanup | Limit sample and cleanup |
| Peer cross-observation attempt | `not-observed` in all eight dimensions both ways | Harness matrix |
| First peer teardown | Other stack remains ready and unchanged | Ordered cleanup record |
| Final cleanup | Processes/ports/DB/schema/objects/storage/telemetry/logs/proof absent | Harness verifier/receipt |

## Milestones

### Milestone 1 — Verify terminal inputs and freeze composition

Record exact accepted commits for every dependency, confirm one final shared TS
lock/re-verification result, and verify the governed-path collision schedule.

Acceptance:

- every dependency row has exact commit plus independent verdict;
- corpus is read-only and both consumers name the same digest;
- no root/generated/internal-adapter path is assigned to this worktree;
- this is the only full-stack authoring worktree.

### Milestone 2 — Prove the early shell/health smoke honestly

Wire the accepted shell to accepted API health through the app-level integration
provider without database/worker/object/telemetry.

Acceptance:

- base marker remains `Demo data · Product demo` and the adjacent tier says
  `Proof tier: shell/health smoke`;
- request uses only loopback Deep Work API;
- proof explicitly reports incomplete components and zero isolation claim;
- no feature/E2E/spike completion is recorded.

### Milestone 3 — Compose one complete stack

Implement exact adapters/bootstrap/worker, fixture services, and driver
single-stack lifecycle.

Acceptance:

- all six components become ready;
- one deterministic corpus journey crosses every component;
- failure/restart/idempotency/resource-limit matrix passes;
- API-backed browser proof at 320px and desktop covers persistent base/tier
  labels, keyboard/focus/announcement transitions, non-color status, reduced
  motion, forced colors, and automated accessibility;
- every accepted shell state is listed as exercised through the API-backed
  provider or `N/A` with an exact reason that the state is browser-local-only and
  no full-stack claim is made;
- external network attempts and external credentials are zero.

### Milestone 4 — Create and independently accept unsealed candidate

Commit exact implementation candidate `C`, run all unsealed checks, and obtain the
four requested independent review perspectives.

Acceptance:

- only governed paths changed;
- driver SHA matches contract and candidate blob;
- `doctor` fails only on the expected unsealed reviewed-commit provenance;
- all review findings are corrected in a new exact candidate before acceptance.

### Milestone 5 — Coordinator seal and dual-stack acceptance

Create mechanical seal `S`, clean peer at `S`, run harness exercise and verifier,
and retain exact evidence.

Acceptance:

- seal proof is exact and non-circular;
- two stacks are concurrently ready and distinct across every harness dimension;
- deliberate collision fails before startup;
- bidirectional cross-observation returns `not-observed`;
- restart, peer survival, cleanup, private receipt, and final verifier pass;
- `SPIKE-WORKTREE-001` may be closed only after fresh independent evidence review.

### Milestone 6 — Final handoff

Record results in this plan, keep program/index/generated changes Coordinator-
owned, and hand exact commits/evidence to the Coordinator.

Acceptance:

- clean worktree and exact changed-file inventory;
- final reviewers state `ACCEPT` or exact rework;
- scenario contributions and zero E2E completion are explicit;
- no service/process/reservation/acceptance peer remains after handoff.

## Progress

- [x] 2026-07-23 AEST — Drafted from current harness/API/TS/UI sources and
  rejected-draft findings; prepared for independent plan review.
- [ ] 2026-07-23 AEST — All seven persistent dependencies terminal at exact
  accepted commits.
- [ ] 2026-07-23 AEST — Early shell/health smoke recorded as incomplete.
- [ ] 2026-07-23 AEST — Single complete stack and failure/resource matrix pass.
- [ ] 2026-07-23 AEST — Exact unsealed candidate accepted by independent review.
- [ ] 2026-07-23 AEST — Coordinator seal, dual-stack exercise, verifier, receipt,
  and cleanup accepted.
- [ ] 2026-07-23 AEST — Coordinator handoff complete with zero E2E completion.

## Surprises & Discoveries

- 2026-07-23 AEST — The harness contract has an exact eight-key schema and verifies
  immutable driver Git blobs. Evidence: `tools/worktree/harness.py`.
  Consequence: image/tool/resource details live in reviewed driver code and proof,
  not extra contract keys.
- 2026-07-23 AEST — The harness allocates four ports for six components.
  Consequence: API/web/object/telemetry use the four loopback ports; worker and
  Postgres use namespace-owned Unix sockets, with the object service on the
  reserved `worker` port.
- 2026-07-23 AEST — The prior product-demo draft was rework-required for missing
  persistent dependencies, root/lock ownership, seal lifecycle, worker path, and
  resource limits. Consequence: every item is explicit in this plan and the
  rejected draft is not authority.
- 2026-07-23 AEST — `SPIKE-WORKTREE-001` self-test evidence is intentionally
  `implemented-not-accepted`. Consequence: only the real dual-stack exercise and
  verifier can close it.

## Decision Log

- 2026-07-23 AEST — Decision: one full-stack authoring worktree plus one
  acceptance-only clean peer. Rationale: canonical pre-spike concurrency limit.
  Consequence: no parallel full-stack writer exists.
- 2026-07-23 AEST — Decision: use the existing harness as reservation, receipt,
  evidence-schema, and verifier authority. Rationale: duplicate orchestration
  would weaken reviewed boundaries. Consequence: product-demo tools implement only
  the missing driver/services.
- 2026-07-23 AEST — Decision: real local PostgreSQL, standard-library object and
  telemetry fixture services. Rationale: the demo needs actual durability/service
  boundaries without external downloads or credentials. Consequence: doctor
  fails closed if the local Postgres executable/cache is absent.
- 2026-07-23 AEST — Decision: retain the application worker in `apps/api`.
  Rationale: tools cannot substitute for application worker behavior.
  Consequence: driver supervises but does not implement job semantics.
- 2026-07-23 AEST — Decision: seal with accepted candidate `C` and descendant
  mechanical commit `S`. Rationale: a commit cannot contain its own hash.
  Consequence: semantic contract and driver bytes are reviewed at `C`; `S`
  changes provenance only.
- 2026-07-23 AEST — Decision: no `AC-DW-QUAL-001-05` or E2E claim. Rationale:
  full release accessibility/E2E requires broader live/release evidence.
  Consequence: this plan uses bounded feature contributions only.

## Detailed implementation approach

1. Coordinator verifies exact terminal dependency commits and prepares one clean
   product-demo worktree at their integration base.
2. Run driver-design static review against the existing harness parser/evidence
   schema before adding code.
3. Add Postgres/object/telemetry adapters and `product_demo_stack.py` under exact
   API paths; reuse accepted API consumer application behavior.
4. Add web product-demo repository/provider/marker under exact app paths; reuse
   accepted shell and TS consumer public exports.
5. Add fixture object/telemetry services and driver with `doctor`,
   `prepare-peer`, `clear-peer-cache`, `shell-health-smoke`, `single`,
   `browser-acceptance`, `single-cleanup`, `dual-exercise`, `cleanup`, and
   `verify-bundle` subcommands. `dual-exercise`/`cleanup` accept exactly the
   arguments issued by the harness; `single-cleanup` is the bounded author-only
   cleanup and cannot consume harness dual-reservation manifests.
6. Add resource preflight, child environment allow-list, process-group ownership,
   readiness, failure injection, RSS/disk sampling, restart, evidence, and scoped
   cleanup.
7. Run component and one-stack integration checks. Create candidate `C`, compute
   exact driver SHA, and stop for fresh review.
8. Correct findings only inside governed paths and repeat candidate review.
9. Coordinator creates seal `S` by changing only the contract provenance field,
   proves it mechanically, and creates clean acceptance peer at exact `S`.
10. Run harness exercise and verify, including deliberate collision/failure,
    review sanitized evidence, clean both stacks/peer, and hand off.

## Validation and proof

### Plan-authoring candidate

```text
test "$(git branch --show-current)" = "external/planning/w1-product-demo-cells"
test "$(git rev-parse HEAD^)" = "9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2"
python3 -B tools/docs/generate.py --check
python3 -B tools/docs/check.py
git diff --check 9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2 HEAD
git diff --name-only 9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2 HEAD
test -z "$(git status --porcelain)"
```

Before reviewed dependency registration/index transition, docs check is expected
to exit `1` for this file with these eleven draft/dependency diagnostics:

1. active ExecPlan is not indexed;
2. unsupported active ExecPlan status `draft`;
3. unknown dependency `local:DW-M1-TS-VERIFY-001`;
4. unknown dependency `local:DW-M1-TS-FIXTURE-CONSUMER-001`;
5. unknown dependency `local:DW-M1-WEB-TS-REVERIFY-001`;
6. independent non-owner reviewer metadata missing;
7. completed gate reviewer metadata missing;
8. `reviewed_at` is not a date;
9. `gate_reviewed_at` is not a date;
10. `last_verified_commit` is not an existing full commit; and
11. `gate_review_status` is not `reviewed-with-gates`.

The Coordinator must create/register the three missing active dependency plans
before this plan can transition to reviewed/dispatchable. Diagnostics may not be
suppressed by deleting the persistent dependencies.

### Component and single-stack checks

Exact implementation commands:

```text
make -C apps/api check
make -C apps/api package-check
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter ./apps/web test
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter ./apps/web build
python3 -m unittest discover -s tools/product_demo/tests -p 'test_*.py'
python3 tools/product_demo/worktree_driver.py doctor --root . --require-free-disk-bytes 12884901888 --require-available-memory-bytes 6442450944 --max-cache-bytes 4294967296 --max-stack-disk-bytes 2147483648 --max-dual-peak-rss-bytes 4294967296
python3 tools/product_demo/worktree_driver.py shell-health-smoke --root . --namespace dw-smoke --evidence-dir .deepwork/proof/dw-smoke
python3 tools/product_demo/worktree_driver.py single --root . --namespace dw-single --evidence-dir .deepwork/proof/dw-single --case partial-failure
python3 tools/product_demo/worktree_driver.py browser-acceptance --root . --namespace dw-single --evidence-dir .deepwork/proof/dw-single/browser --viewports 320x800,1440x900 --require-keyboard-focus --require-announcements --require-non-color-status --require-reduced-motion --require-forced-colors --require-automated-a11y
python3 tools/product_demo/worktree_driver.py single-cleanup --root . --namespace dw-single --evidence-dir .deepwork/proof/dw-single
python3 tools/architecture/check.py --root . --graph tools/architecture/graph.json --fixtures internal/fixtures/architecture --verify-negative
python3 -B tools/docs/generate.py --check
python3 -B tools/docs/check.py
```

The author-owned smoke/single/browser/single-cleanup commands use driver-created
private reservations compatible with the same isolation library but do not emit
spike acceptance. The browser report must distinguish exercised API-backed
states from shell-only `N/A` rows with reasons and show the persistent base marker
plus proof-tier label in every viewport/state. Final dual acceptance runs only
through the harness.

### Exact seal proof

```text
candidate_c="<exact independently accepted unsealed commit>"
seal_s="$(git rev-parse HEAD)"
test "${#candidate_c}" -eq 40
git cat-file -e "${candidate_c}^{commit}"
test "$(git rev-parse "${seal_s}^")" = "$candidate_c"
test "$(git diff --name-only "$candidate_c" "$seal_s")" = "tools/product_demo/worktree-driver-contract.json"
git diff --check "$candidate_c" "$seal_s"
python3 -B -c 'import hashlib,json,pathlib,subprocess,sys; c=sys.argv[1]; p=pathlib.Path("tools/product_demo/worktree_driver.py"); q=pathlib.Path("tools/product_demo/worktree-driver-contract.json"); now=json.loads(q.read_text()); old=json.loads(subprocess.check_output(["git","show",f"{c}:{q.as_posix()}"],text=True)); assert hashlib.sha256(p.read_bytes()).hexdigest()==now["driver_sha256"]; assert subprocess.check_output(["git","show",f"{c}:{p.as_posix()}"])==p.read_bytes(); assert {k:v for k,v in old.items() if k!="reviewed_repository_commit"}=={k:v for k,v in now.items() if k!="reviewed_repository_commit"}; assert now["reviewed_repository_commit"]==c' "$candidate_c"
python3 tools/worktree/harness.py doctor --root .
test -z "$(git status --porcelain)"
```

Expected seal observation: `doctor` reports `static-contract-ready`, exact
driver SHA, exact reviewed commit `C`, semantic contract digest, and no other
change from `C` to `S`.

### Final dual-stack matrix

At sealed commit `S`, with an acceptance-only peer also at `S`:

```text
seal_s="<exact sealed commit S>"
acceptance_root="$(pwd -P)"
peer_root="<absolute clean acceptance-only peer at exact seal S>"
evidence_checkout="<absolute clean coordinator-owned harness-evidence checkout>"
self_test_dir="${evidence_checkout}/docs/references/research/harness-isolation/evidence/self-test"
product_demo_dir="${evidence_checkout}/docs/references/research/harness-isolation/evidence/product-demo"
test "$(git rev-parse HEAD)" = "$seal_s"
test "$(git -C "$peer_root" rev-parse HEAD)" = "$seal_s"
test -z "$(git status --porcelain)"
test -z "$(git -C "$peer_root" status --porcelain)"
test -z "$(git -C "$evidence_checkout" status --porcelain)"
python3 tools/product_demo/worktree_driver.py prepare-peer --root "$acceptance_root" --peer-root "$peer_root" --evidence-dir "$product_demo_dir" --max-cache-bytes 4294967296
test -z "$(git status --porcelain)"
test -z "$(git -C "$peer_root" status --porcelain)"
python3 -m unittest discover -s tools/architecture/tests -p 'test_*.py'
python3 tools/architecture/check.py --root . --graph tools/architecture/graph.json
python3 tools/architecture/check.py --root . --graph tools/architecture/graph.json --fixtures internal/fixtures/architecture --verify-negative
python3 -m unittest discover -s tools/worktree/tests -p 'test_*.py'
python3 tools/worktree/harness.py doctor --root .
python3 tools/worktree/harness.py self-test --root "$acceptance_root" --fixtures internal/fixtures/worktree --evidence-dir "$self_test_dir"
python3 tools/worktree/harness.py exercise --root "$acceptance_root" --peer-root "$peer_root" --namespace-a dw-iso-a --namespace-b dw-iso-b --evidence-dir "$product_demo_dir"
python3 tools/worktree/harness.py verify --evidence-dir "$product_demo_dir" --require-no-cross-observation --require-clean-teardown
python3 tools/product_demo/worktree_driver.py verify-bundle --evidence-dir "$product_demo_dir" --require-hmac-bound-bundle-id
python3 -B tools/docs/generate.py --check
python3 -B tools/docs/check.py
git diff --check
test -z "$(git status --porcelain)"
test -z "$(git -C "$peer_root" status --porcelain)"
test -n "$(git -C "$evidence_checkout" status --porcelain --untracked-files=all)"
test -z "$(git -C "$evidence_checkout" status --porcelain --untracked-files=all | awk '{print $2}' | grep -Ev '^docs/references/research/harness-isolation/evidence/(self-test|product-demo)/')"
```

The acceptance root and peer stay clean. The canonical retained paths are written
only in the separate clean Coordinator-owned evidence checkout, never by this
product-demo worktree. After bundle verification, fresh evidence review inspects
that exact diff and the Coordinator alone commits the bounded evidence paths in a
separate context. The product-demo worker cannot edit those reference files to
manufacture success.

Required final observations:

- both roots have identical sealed driver/contract provenance;
- both complete stacks are concurrently ready;
- allocation/cross-observation/restart/teardown digests and all seven sidecar
  digests validate transitively against the private receipt;
- all required dimensions differ and every bidirectional probe is
  `not-observed`;
- first teardown preserves peer readiness;
- all processes, ports, database/schema, object/browser/telemetry namespace,
  logs, proof, reservations, and copied peer runtime caches are absent after
  cleanup;
- deliberate collision evidence starts zero processes;
- RSS/disk/cache limits remain within numeric budgets;
- network summary contains only allocated loopback/Unix-socket traffic;
- no external credential or raw private manifest enters retained evidence;
- feature scenario rows are contribution-only; and
- completed `E2E-V1-*` count is exactly zero.

## Idempotence, rollback, and recovery

- Driver preflight is read-only. Reservation is atomic and occurs only after all
  numeric/tool/path checks pass.
- Stack startup is staged PostgreSQL -> object/telemetry -> worker -> API -> web.
  Failure at any stage stops later starts and invokes recovery cleanup for exact
  already-owned resources.
- API command intake and worker effects converge only under the scoped
  namespace/session/operation key plus canonical request digest defined above.
  Worker restart reconciles object checksum and job outcome without duplicate
  projection or effect; a digest conflict remains blocked.
- Restart reuses the exact reserved ports/database/schema/prefix/storage/
  telemetry/log/proof allocation and records new process identities.
- Cleanup first validates private manifest ownership, child process start
  identity, canonical paths, and exact DB/schema/prefix. It refuses a broad path,
  peer resource, symlink, unowned PID, or missing ownership token.
- Cleanup is resumable through the existing harness `recover` protocol and
  two-reservation release transaction. A failed cleanup remains blocked and does
  not discard reservation evidence.
- The unsealed candidate cannot run final acceptance. A changed driver or semantic
  contract after seal invalidates readiness and repeats review/seal; no in-place
  hash edit is accepted.
- Rollback is Coordinator-owned and takes exact `integration_base`, `candidate_c`,
  `seal_s`, `acceptance_root`, `peer_root`, and `product_demo_dir` inputs. It
  first stops new browser/API commands, then selects exactly one evidence branch.
  For a previously accepted exercise, reservations are already released, so it
  must not call `recover`:

```text
python3 tools/worktree/harness.py verify --evidence-dir "$product_demo_dir" --require-no-cross-observation --require-clean-teardown
python3 tools/product_demo/worktree_driver.py verify-bundle --evidence-dir "$product_demo_dir" --require-hmac-bound-bundle-id
python3 tools/product_demo/worktree_driver.py clear-peer-cache --root "$acceptance_root" --peer-root "$peer_root" --evidence-dir "$product_demo_dir" --expect-absent
```

  For exact retained blocker evidence with
  `recovery: reservation-retained`, it must not call product-demo `verify`;
  instead it runs:

```text
python3 tools/worktree/harness.py recover --root "$acceptance_root" --peer-root "$peer_root" --namespace-a dw-iso-a --namespace-b dw-iso-b --evidence-dir "$product_demo_dir"
python3 -B -c 'import json,pathlib; d=json.loads((pathlib.Path(__import__("sys").argv[1])/"exercise.json").read_text()); assert d["evidence_class"]=="product-demo-blocker"; assert d["status"]=="blocked"; assert d["acceptance"]=="implemented-not-accepted"; assert d["recovery"]=="cleanup-proven"; assert d["resources_reserved"]==0; assert d["processes_started"]==0' "$product_demo_dir"
python3 tools/product_demo/worktree_driver.py clear-peer-cache --root "$acceptance_root" --peer-root "$peer_root" --evidence-dir "$product_demo_dir"
```

  Only after the selected branch returns zero and peer runtime roots are absent
  does the common reviewed revert run:

```text
test "$(git rev-parse "${candidate_c}^")" = "$integration_base"
test "$(git rev-parse "${seal_s}^")" = "$candidate_c"
git revert --no-edit "$seal_s"
git revert --no-edit "$candidate_c"
git diff --quiet "$integration_base" HEAD -- apps/api/src/deepwork_api/adapters/product_demo apps/api/src/deepwork_api/bootstrap/product_demo.py apps/api/src/deepwork_api/workers/product_demo_stack.py apps/api/tests/integration_tests/product_demo apps/web/src/product-demo apps/web/tests/product-demo tools/product_demo
make -C apps/api check
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter ./apps/web test
python3 tools/architecture/check.py --root . --graph tools/architecture/graph.json
python3 -B tools/docs/generate.py --check
python3 -B tools/docs/check.py
test -z "$(git status --porcelain)"
```

  Revert cannot begin unless the compatible accepted or blocker cleanup branch
  passes. If cleanup, revert, or a postcondition fails, stop, preserve the private
  reservation/evidence and exact failure, and keep the branch blocked for a
  reviewed recovery; do not discard ownership state, kill by name, hand-edit a
  lock/schema, or delete broadly. No external authoritative work exists, and
  root/lock/schema compatibility changes require their own plans.

## Rollout and handoff

The product demo has no production rollout. It is a contributor/acceptance stack
that remains fixture-labelled and loopback-only.

Final handoff to the Coordinator includes:

- exact accepted dependency SHAs and verdicts;
- unsealed candidate `C`, seal `S`, driver SHA, semantic digest, and seal proof;
- exact commands, exit codes, concise observations, resource samples, and
  evidence/receipt references;
- exact changed-file list under governed paths;
- independent architecture, product/UX, security/reliability, and DX review
  verdicts for candidate, seal, and final evidence;
- `SPIKE-WORKTREE-001` close recommendation or exact blocker;
- confirmation that root/generated/lock/index/program/internal-adapter/corpus/
  sibling/live-provider paths were not changed;
- confirmation that no external credential/network/install/push/merge/deploy
  occurred; and
- explicit bounded feature contributions with zero `E2E-V1-*` completion.

The Coordinator alone updates the program ledger, spike status, generated/index
views, integrates reviewed commits, and removes the acceptance peer/worktree after
successful verification.

## Outcomes & Retrospective

Pending implementation. Completion must distinguish shell/health smoke,
single-stack integration, and dual-stack worktree acceptance; record exact
resource/collision/failure/cleanup evidence; compare actual peak/disk/cache usage
with the numeric budgets; preserve all optional capability fallbacks; and state
whether `SPIKE-WORKTREE-001` is accepted. No outcome may promote fixture evidence
to a live contract or claim any `E2E-V1-*` scenario complete.
