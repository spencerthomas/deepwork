---
exec_plan_id: DW-EXEC-M1-API-SCAFFOLD
title: Wave 1 independently installable fixture-only API scaffold
status: reviewed
superseded_by: null
owner: api
reviewed_by: [ts-package-reviewer]
reviewed_at: 2026-07-23
primary_feature_id: DW-FND-003
supporting_feature_ids: [DW-FND-001]
issue: local:DW-M1-API-001
created: 2026-07-23
last_updated: 2026-07-23
base_commit: 3dbe6629d8053380ab6a8bff6d2fcb462f854256
last_verified_commit: 3dbe6629d8053380ab6a8bff6d2fcb462f854256
risk: medium
governed_paths: [apps/api/**, docs/exec-plans/active/DW-EXEC-M1-API-SCAFFOLD.md]
contract_gates: [SPIKE-AUTH-002, SPIKE-SOURCE-001, SPIKE-STREAM-001]
decision_gates: [DEC-002, DEC-023, DEC-026, DEC-031, DEC-033, DEC-035]
gate_review_status: reviewed-with-gates
gate_reviewed_by: [ts-package-reviewer]
gate_reviewed_at: 2026-07-23
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, docs/exec-plans/active/DW-EXEC-M1-REPOSITORY-SCAFFOLD.md, docs/product-specs/foundations/dw-fnd-001-repository-oss-and-delivery-foundation.md, docs/product-specs/foundations/dw-fnd-003-application-service-state-and-security.md, docs/design-docs/architecture/application-architecture.md, docs/design-docs/engineering/conventions.md, docs/design-docs/decisions/index.md, docs/SECURITY.md]
scenario_ids: [AC-DW-FND-001-01, AC-DW-FND-001-03, AC-DW-FND-001-07, AC-DW-FND-003-05, AC-DW-FND-003-08]
dispatch_kind: cell
dispatch_ready: true
agent_review_required: true
dependencies: []
blockers: []
---

# Wave 1 independently installable fixture-only API scaffold

## Purpose and observable result

After this cell is implemented, a contributor can build and install `apps/api` as
an independent Python 3.12 distribution, import its deliberate public entry point,
start a minimal FastAPI process without credentials or external network access,
observe liveness and an unmistakably fixture-only product-demo status, and run a
separate worker-entry-point smoke check that makes no durability claim.

This cell contributes the API portion of the reviewed Wave 1 umbrella and the
foundation owned by `DW-FND-003`. It does not satisfy the complete application-
service, durable-core, source-adapter, stream, product-demo, or release scenarios.

## Context and orientation

The repository currently has canonical documentation and planning but no
`apps/api` runtime package. The accepted architecture assigns FastAPI, the worker,
application authorization, persistence, server-only credentials, source adapters,
and normalized upstream streaming to `apps/api`, while keeping the independent
agent graph in `packages/agent` and all TypeScript client semantics outside this
cell.

The Wave 1 umbrella authorizes a credential-free scaffold before external
contracts are available. This cell therefore establishes only the package and
hexagonal dependency seams needed for later work. Provider SDKs, database models,
credentials, migrations, durable jobs, real source calls, and a normalized task
stream remain absent.

## Scope

### In scope

- Create an independent Python 3.12 project under `apps/api` with its own
  `pyproject.toml`, `uv.lock`, package `Makefile`, README, scoped `AGENTS.md`, source
  tree, tests, distribution metadata, and `py.typed` marker.
- Pin reviewed Wave 1 versions of FastAPI, Pydantic, the ASGI server, Ruff, strict
  mypy with the Pydantic plugin, pytest, socket-denial support, and build tooling.
- Expose deliberate public imports and separate `deepwork-api` and
  `deepwork-worker` console entry points from one distribution.
- Implement a minimal FastAPI application factory, process liveness at `/health`,
  and a deterministic `GET /api/v1/demo/status` response that is permanently
  labelled `fixture`, reports all live/provider capabilities unavailable, and
  contains no plausible external success.
- Make the worker entry point support a deterministic configuration/import smoke
  mode that reports that no durable job backend is configured. It must not imply
  accepted work, retries, leases, or persistence.
- Establish the initial inward dependency shape:
  `transport/bootstrap -> application -> domain/ports`, with fixture adapters
  implementing ports and no framework imports in domain code.
- Add no-socket unit and contract tests, public-import tests, API/worker process
  smoke tests, OpenAPI secret-shape checks, build tests, and clean-wheel install
  proof contained wholly under `apps/api`.

### Non-goals

- Root manifests, root commands, CI, shared fixtures, generated documentation,
  generated TypeScript clients, `packages/**`, `apps/web/**`, or product-demo
  composition.
- PostgreSQL, SQLAlchemy models, Alembic migrations, outbox/jobs, object storage,
  sessions, tenancy persistence, credentials, source registrations, audit storage,
  or idempotent external effects.
- LangSmith, LangGraph, Deep Agents, MDA, Fleet, OAuth, API-key, GitHub, email,
  push, object-service, or other external SDK/client traffic.
- A task stream, source probe, generic proxy, provider cursor, HITL, cancellation,
  scheduling, deployment, or `/v1/deepagents/*` route.
- Claiming that the fixture endpoint is a live provider contract or that the
  worker smoke is durable background processing.

### Permissions and risk boundary

- Allowed paths are exactly `apps/api/**` and this ExecPlan.
- External systems, provider/service calls, and runtime network traffic are
  prohibited. The only permitted external access is an explicitly invoked
  bootstrap/lock step using reviewed public package indexes to resolve the pinned
  package-local `apps/api/uv.lock`; it uses no credential or private index.
- Imports, API/worker runtime, unit/contract tests, build verification, and
  clean-wheel behavior remain socket-denied or operate entirely from the resolved
  package-local environment. No other external access is permitted.
- Credentials, secret references, production data, and copied provider payloads
  are prohibited.
- Destructive database, migration, release, deployment, publication, push, merge,
  and sibling-repository operations are prohibited.
- Root/shared files and generated outputs are coordinator-owned and must not be
  changed to make package checks pass.
- Cross-review by API/platform, architecture, security, and developer-experience
  reviewers is required before `status`, gate-review metadata, verification commit,
  or `dispatch_ready` may change.

## Authoritative sources and prerequisites

- Product specifications:
  `docs/product-specs/foundations/dw-fnd-003-application-service-state-and-security.md`
  is the sole primary feature; `DW-FND-001` supplies package and contributor
  boundaries.
- Umbrella: `docs/exec-plans/active/DW-EXEC-M1-REPOSITORY-SCAFFOLD.md`.
- Architecture and decisions: `ARCHITECTURE.md`,
  `docs/design-docs/architecture/application-architecture.md`, and accepted
  `DEC-002`, `DEC-023`, `DEC-026`, `DEC-031`, `DEC-033`, and `DEC-035`.
- Engineering and security:
  `docs/design-docs/engineering/conventions.md`, `docs/SECURITY.md`, root
  `AGENTS.md`, and the scoped `apps/api/AGENTS.md` created by this cell.
- Exact reviewed base:
  `3dbe6629d8053380ab6a8bff6d2fcb462f854256`.
- The umbrella review contained in the exact base commit is a satisfied planning
  prerequisite rather than a dispatch dependency. This draft still requires its
  own independent metadata, gate, permission, and dispatch review.

### Contract gates and deterministic fallback

`SPIKE-AUTH-002`, `SPIKE-SOURCE-001`, and `SPIKE-STREAM-001` are open. This cell
does not attempt or satisfy them. Their fallback is enforced structurally:

- no authentication or workspace header is accepted as an external contract;
- no live source can be registered, probed, listed, or invoked;
- no task-stream endpoint or provider resume behavior exists; and
- the only product-facing behavior is explicitly synthetic fixture status.

If any implementation step would require one of these contracts, stop that step,
record the discovery here, and retain the unavailable behavior. An installed SDK,
example, or plausible mock does not clear a gate.

## Interfaces and invariants

- The distribution and import names must be explicit and stable after review. The
  proposed import package is `deepwork_api`; no module is imported through a
  repository-path alias.
- `create_app()` is the public application factory. Importing it performs no
  environment read, network call, filesystem mutation, or process start.
- `GET /health` proves process liveness only. It cannot imply database, worker,
  source, object-store, or external readiness.
- `GET /api/v1/demo/status` is fixture-only. Its Pydantic response includes an
  explicit fixture evidence class and unavailable live-capability state; it
  contains no `authRef`, credential, arbitrary endpoint, forwarding header, source
  cursor, provider payload, or reusable identifier.
- The API and worker are separate console entry points from one built artifact.
  The worker smoke clearly states `durability: unavailable` until the later
  PostgreSQL outbox/job cell is reviewed and implemented.
- Domain modules import only the standard library and deliberate typing helpers.
  Application modules depend on domain and ports. Transport and bootstrap may
  import FastAPI/Pydantic. Fixture adapters implement ports. No route directly
  imports a provider SDK or persistence record.
- `apps/api` must not import `packages/agent`, TypeScript packages, UI code,
  prototype fixtures, or sibling repositories.
- Unit and fixture tests deny outbound sockets. Loopback ASGI testing uses the
  in-process test transport and does not require an open network port.
- HTTP errors use stable safe codes/messages. Stack traces, environment values,
  provider prose, and secret-shaped fields never enter responses or retained
  evidence.
- The wheel contains declared public modules and `py.typed`, and excludes tests,
  evidence logs, local paths, caches, credentials, and repository-only fixtures.

## Milestones

### Milestone 1 — Independent project and package boundary

Create the package-local manifest, frozen lock, Makefile, README, scoped guidance,
source layout, deliberate exports, type marker, and test layout. Record exact pins
and why each direct dependency is required.

Acceptance:

- `apps/api` resolves without a root Python environment or `packages/agent`; only
  this explicit bootstrap may contact reviewed public package indexes.
- Command: `make -C apps/api doctor && make -C apps/api bootstrap`.
- Expected observation: Python 3.12 and `uv` compatibility are reported, the
  package-local frozen environment resolves from reviewed public package indexes,
  and no credential, private index, provider, or service is contacted.
- Evidence artifact: `apps/api/.artifacts/w1-api/m1-package-boundary.txt`.

### Milestone 2 — Honest API and worker entry points

Implement the layered application factory, liveness route, fixture-only demo
status, and separate worker smoke without persistence or external integrations.

Acceptance:

- Import and startup are side-effect free except for the explicitly started local
  process; fixture behavior is unmistakable and live capabilities are unavailable.
- Command: `make -C apps/api test`.
- Expected observation: unit/contract tests cover `/health`, fixture status,
  worker smoke, forbidden secret-shaped response fields, and zero outbound sockets.
- Evidence artifact: `apps/api/.artifacts/w1-api/m2-api-worker-tests.txt`.

### Milestone 3 — Strict package verification

Run formatter check, Ruff, strict mypy/Pydantic checks, contract tests, distribution
build, clean-wheel install/import, file-content inspection, and rerun proof.

Acceptance:

- The built wheel installs and imports outside the source checkout, contains
  `py.typed`, and contains no tests, artifact logs, source paths, or secret material.
- Command: `make -C apps/api check && make -C apps/api package-check`.
- Expected observation: all package-local checks pass twice with the frozen lock;
  the second run changes no governed file.
- Evidence artifact: `apps/api/.artifacts/w1-api/m3-package-check.txt`.

### Milestone 4 — Independent review handoff

Update the living sections, record exact validation output and changed paths, and
stop for a fresh reviewer. Do not integrate root commands, generated SDK output,
or the product demo in this cell.

Acceptance:

- Only governed paths differ from the exact base and all open gates remain listed
  with unavailable fallbacks.
- Command: `git diff --check && git diff --name-only 3dbe6629d8053380ab6a8bff6d2fcb462f854256`.
- Expected observation: every changed path is `apps/api/**` or this ExecPlan.
- Evidence artifact: this plan's Progress, Surprises & Discoveries, Decision Log,
  Validation and proof, and Outcomes & Retrospective sections.

## Progress

- [x] 2026-07-23 AEST — `ts-package-reviewer` accepted the plan; prerequisites,
  permissions, decisions, open-gate fallbacks, scenario qualification, and exact
  governed paths were verified for dispatch from the recorded base.
- [ ] Milestone 1 — Independent project and package boundary complete.
- [ ] Milestone 2 — Honest API and worker entry points complete.
- [ ] Milestone 3 — Strict package verification complete.
- [ ] Milestone 4 — Fresh independent review packet complete.

This plan is reviewed and dispatch-ready. No implementation milestone has started.

## Surprises & Discoveries

- 2026-07-23 AEST — Observation: the reviewed base contains the Wave 1 umbrella
  but no `apps/api` runtime package. Evidence: repository inspection at
  `3dbe6629d8053380ab6a8bff6d2fcb462f854256`. Consequence: this plan can establish
  the package boundary without preserving runtime compatibility, but cannot claim
  any durable or external behavior.

## Decision Log

- 2026-07-23 AEST — Decision: keep this cell credential-free, network-denied, and
  persistence-free. Rationale: the umbrella authorizes a fixture scaffold while
  the primary feature's auth, source, and stream gates remain open. Consequence:
  health and demo status are synthetic, and all live operations are absent.
  Approved by: `ts-package-reviewer`.
- 2026-07-23 AEST — Decision: expose API and worker smoke entry points from one
  independently built distribution without implementing durable jobs. Rationale:
  accepted architecture requires the shared artifact/process split, while durable
  outbox semantics belong to a later cell. Consequence: worker output must state
  that durability is unavailable. Approved by: `ts-package-reviewer`.
- 2026-07-23 AEST — Decision: accept this bounded cell for dispatch with
  `SPIKE-AUTH-002`, `SPIKE-SOURCE-001`, and `SPIKE-STREAM-001` still open.
  Rationale: the plan excludes the affected external behavior and makes fixture-
  only unavailable fallbacks mandatory. Consequence: implementation may start
  from the exact base but cannot add credentials, provider/service calls, or a
  task stream. Approved by: `ts-package-reviewer`.

## Detailed implementation approach

1. Create package-local guidance and tooling under `apps/api`, pin Python 3.12 and
   exact direct/development dependencies, and commit a package-local frozen lock.
2. Create `src/deepwork_api` with explicit public exports and the minimum
   `domain`, `ports`, `application`, `adapters/fixture`, `transport`, and `bootstrap`
   modules needed for health/demo status and the two entry points.
3. Model public responses with Pydantic rather than ORM or provider types. Keep
   fixture evidence and unavailable capability values explicit in the wire shape.
4. Add deterministic in-process ASGI tests, worker CLI tests, architecture import
   tests, secret-shape/OpenAPI scans, cancellation/resource-cleanup checks where
   applicable, and socket denial.
5. Build wheel and source distribution, install the wheel in a clean temporary
   environment, import only public symbols, exercise the entry points, and inspect
   artifact contents.
6. Record exact results and deviations in this plan, run validation twice, and
   stop for a fresh reviewer without changing root/shared files.

## Validation and proof

The implementation agent records exact versions, exit codes, and sanitized output
for:

```text
make -C apps/api doctor
make -C apps/api bootstrap
make -C apps/api format-check
make -C apps/api lint
make -C apps/api typecheck
make -C apps/api test
make -C apps/api contract
make -C apps/api build
make -C apps/api package-check
make -C apps/api check
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
git diff --check
git diff --name-only 3dbe6629d8053380ab6a8bff6d2fcb462f854256
```

Required proof:

- scenario mapping for `AC-DW-FND-001-01`, `AC-DW-FND-001-03`,
  `AC-DW-FND-001-07`, `AC-DW-FND-003-05`, and `AC-DW-FND-003-08`, explicitly
  distinguishing this cell's partial contribution from full scenario completion;
- clean build/install/import and `py.typed` proof from the built wheel;
- in-process `/health` and fixture-demo request/response evidence;
- worker smoke output showing no durable backend;
- socket-denial and no-external-request proof for imports, runtime, tests, and
  package behavior, separately identifying the one reviewed public-package-index
  bootstrap step;
- OpenAPI/response scan proving no `authRef`, credential, generic forwarding
  header, arbitrary endpoint, or provider cursor;
- exact governed-path diff and a second clean validation run; and
- retained sanitized logs under `apps/api/.artifacts/w1-api/`, excluded from built
  distributions, with concise results copied into this plan before review.

Browser, viewport, assistive-technology, database, migration, live-contract,
external telemetry, and full product-demo proof are not applicable to this
package-only cell and must not be reported as passing.

## Idempotence, rollback, and recovery

- Bootstrap and validation are package-local and safe to rerun from the frozen
  lock. A second successful run must not change governed files.
- A dependency-resolution failure preserves the prior manifest and lock evidence;
  recovery changes only `apps/api/**` through a reviewed patch.
- API/worker smoke processes must handle termination without leaving ports,
  subprocesses, temp files, or background tasks. In-process tests own and close all
  clients and resources.
- No database, migration, object, credential, runtime task, or external effect
  exists to roll back. The cell rolls back by reverting only its governed-path
  changes from the exact base.
- If the fixture route, public exports, or dependency pins fail cross-review, keep
  the plan draft, record the finding, and revise only this plan or `apps/api/**`.
- If an external contract becomes necessary, stop and retain the unavailable
  fallback; do not add credentials or network access.

## Rollout and handoff

There is no production rollout. After implementation and independent acceptance,
the cell hands the exact commit, built-artifact inspection, package-local command
transcript, scenario contribution map, open-gate ledger, and governed-path diff to
the coordinator. The coordinator alone may integrate root commands, generated
OpenAPI/SDK outputs, shared fixtures, `apps/web`, or product-demo composition.

The expected issue state after implementation is Agent Review, then Human Review.
The author does not approve its own work, set `dispatch_ready`, merge, push,
publish, deploy, or begin Wave 2 application-service behavior.

## Outcomes & Retrospective

Pending. At completion, record the exact delivered package behavior, public import
and entry-point names, dependency pins, validation evidence, deviations, remaining
open gates, deferred durable/application-service work, reviewer outcome, and the
accepted commit offered to the coordinator. Do not claim full `DW-FND-003` or any
release scenario complete from this scaffold.
