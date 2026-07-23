---
exec_plan_id: DW-EXEC-M1-PRODUCT-DEMO-API-RUNTIME-LOCK
title: Pin the product-demo PostgreSQL runtime manifest and lock
status: draft
superseded_by: null
owner: api-runtime-lock-integrator
reviewed_by: []
reviewed_at: null
primary_feature_id: DW-FND-003
supporting_feature_ids: [DW-FND-001, DW-FND-004, DW-FND-005, DW-QUAL-001]
issue: local:DW-M1-PRODUCT-DEMO-API-RUNTIME-LOCK-001
created: 2026-07-23
last_updated: 2026-07-23
base_commit: cad9d8a778c88f837d690d79ba84735660531f9d
last_verified_commit: null
risk: medium
governed_paths: [apps/api/pyproject.toml, apps/api/uv.lock, docs/exec-plans/active/DW-EXEC-M1-PRODUCT-DEMO-API-RUNTIME-LOCK.md]
contract_gates: []
decision_gates: [DEC-002, DEC-024, DEC-026]
gate_review_status: unreviewed
gate_reviewed_by: []
gate_reviewed_at: null
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, apps/api/AGENTS.md, docs/AGENTS.md, docs/PLANS.md, docs/SECURITY.md, docs/RELIABILITY.md, docs/design-docs/architecture/application-architecture.md, docs/design-docs/engineering/conventions.md, docs/design-docs/decisions/index.md, docs/product-specs/foundations/dw-fnd-001-repository-oss-and-delivery-foundation.md, docs/product-specs/foundations/dw-fnd-003-application-service-state-and-security.md, docs/product-specs/foundations/dw-fnd-004-sdk-stream-and-fixture-contracts.md, docs/product-specs/foundations/dw-fnd-005-domain-identity-status-and-audit-model.md, docs/product-specs/quality/dw-qual-001-accessibility-performance-security-testing-and-release.md, docs/exec-plans/active/DW-EXEC-M1-FIXTURE-API-CONSUMER.md, docs/exec-plans/completed/DW-EXEC-M1-API-SCAFFOLD.md]
scenario_ids: [AC-DW-FND-003-05, AC-DW-FND-004-04, AC-DW-FND-005-01]
dispatch_kind: cell
dispatch_ready: false
agent_review_required: true
dependencies: [DW-EXEC-M1-FIXTURE-API-CONSUMER]
blockers: []
---

# Pin the product-demo PostgreSQL runtime manifest and lock

## Context and dispatch identity

This is a planning draft, not a runnable packet. The branch and worktree are
created only after `DW-EXEC-M1-FIXTURE-API-CONSUMER` is terminal at an exact
independently accepted commit. The Coordinator replaces the planning base above
with that exact integrated dependency SHA, records reviewer acceptance, and then
dispatches one manifest/lock-only worker.

The future worker changes exactly:

```text
apps/api/pyproject.toml
apps/api/uv.lock
docs/exec-plans/active/DW-EXEC-M1-PRODUCT-DEMO-API-RUNTIME-LOCK.md
```

It must not edit API source, tests, `apps/api/Makefile`, the OpenAPI exporter or
artifact, a root file, another package, generated output, an index, a canonical
plan, or `docs/plans/**`.

## Purpose and observable result

Extend the already accepted `deepwork-api` distribution manifest and lock with
the canonical PostgreSQL stack needed by the product demo:

- SQLAlchemy 2 async application persistence;
- Alembic migrations; and
- the reviewed Psycopg 3 async PostgreSQL driver/package family.

Every direct dependency is an exact `==` pin in `apps/api/pyproject.toml`; every
transitive artifact is frozen with integrity metadata in `apps/api/uv.lock`.
After one explicitly authorized package-index/bootstrap phase, the complete API
doctor/check/package/import matrix and lock verification rerun offline with
Python downloads disabled.

This cell resolves dependencies only. It implements no SQLAlchemy model,
migration, adapter, transaction, outbox, worker, API route, OpenAPI change, or
database service. It supports bounded evidence for the acceptance IDs in front
matter, completes none of them, and earns zero `E2E-V1-*` or live-contract
credit.

## Context and scope

The accepted API consumer owns final command/projection ports, `202` intake,
cookie/Origin/CSRF behavior, Pydantic contracts, the OpenAPI exporter, and all
application source. This cell may not alter those semantics to make a dependency
install.

Canonical `DEC-002`, `DEC-024`, and `DEC-026` accept Python 3.12,
FastAPI/Pydantic, SQLAlchemy 2/Alembic/PostgreSQL, an independently locked
`apps/api`, and a transactional Postgres job/outbox direction. Psycopg 3 async is
the proposed concrete driver for this packet because it supports SQLAlchemy's
async dialect without a subprocess shim. Independent plan review must explicitly
accept that driver family before dispatch; otherwise the packet remains draft.
The implementation worker then records exact current versions, wheel tags,
hashes, license/provenance, Python 3.12 compatibility, and supported PostgreSQL
range before writing the direct exact pins.

Forbidden substitutions include:

- invoking `psql` or another process as an application driver;
- SQLite/in-memory persistence represented as PostgreSQL proof;
- Redis, Celery, Kafka, another queue, or an ORM/migration framework;
- an editable, Git, local-path, private-index, credential-bearing, or unpinned
  dependency;
- changing FastAPI/Pydantic or unrelated development dependencies opportunistically;
- a production database, credential, customer data, image pull, migration, push,
  merge, or deployment.

## Interfaces and invariants

- `apps/api/pyproject.toml` remains Python `==3.12.*` and retains the existing
  build backend, distribution name, entry points, strict mypy/Pydantic policy,
  test policy, and exact existing pins.
- Only the three approved persistence package families and unavoidable
  transitive lock records may be added.
- `apps/api/uv.lock` is the only dependency lock; no package-local alternative,
  requirements export, or root Python environment is introduced.
- The accepted `apps/api/Makefile` remains byte-identical. Its exact commands are
  the package interface:

```text
make -C apps/api bootstrap
make -C apps/api doctor
make -C apps/api check
make -C apps/api package-check
make -C apps/api openapi-check
```

- `bootstrap` is the only command permitted online and only when the Coordinator
  explicitly authorizes public package-index access after provenance review.
  Every final validation uses `uv --offline --no-python-downloads`, a frozen
  lock, the project-local `.venv`, and the project-local cache.
- Built wheel metadata declares the runtime dependencies. An isolated installed
  wheel imports SQLAlchemy, Alembic, Psycopg, `deepwork_api`, and both console
  entry points without a source checkout path.
- OpenAPI remains byte-identical. Runtime dependency resolution cannot alter
  route/model generation.

## State matrix

| State | Required behavior |
|---|---|
| API consumer nonterminal | Do not create the runtime-lock worktree. |
| Driver family not independently accepted | Keep this packet draft; do not select a substitute. |
| Package-index access not authorized | Attempt only the accepted offline cache; if incomplete, report `blocked-package-index-evidence`. |
| Python/toolchain mismatch | Stop before manifest or lock mutation. |
| Existing pin would change | Stop and return the exact solver conflict; no opportunistic upgrade. |
| Unsupported wheel/platform or missing integrity | Reject the candidate. |
| Editable/Git/path/private/credential source appears | Reject and scrub evidence. |
| First lock succeeds | Snapshot its bytes and full digest before any install. |
| Repeated offline resolution drifts | Fail with the exact safe package record; do not commit. |
| Frozen offline install fails | Fail; do not weaken pins or enable lifecycle/network fallback. |
| Package/wheel import fails | Fail and preserve exact public exception class. |
| OpenAPI changes | Fail and return to the owning API contract; do not normalize drift. |
| All proof passes | Commit only manifest, lock, and this living packet; stop for independent review. |

## Milestones

1. Verify the exact terminal API consumer SHA, accepted OpenAPI digest, clean
   worktree, Python/uv paths, public-index policy, and three-file scope.
2. Record and independently review the exact SQLAlchemy 2, Alembic, and Psycopg 3
   direct versions plus artifact provenance before editing the manifest.
3. Add only exact direct pins, produce the lock once, inspect every changed
   resolution, and retain the first lock digest.
4. Prove repeated lock generation is byte-identical, frozen install succeeds,
   the wheel declares/imports the runtime stack, all API checks pass, OpenAPI is
   unchanged, and final execution works offline.
5. Commit the bounded candidate, obtain fresh Python API, database/reliability,
   and supply-chain/security verdicts, and return the clean terminal SHA to the
   Coordinator.

## Exact validation

The reviewed worker records the exact executable paths and runs:

```text
api_consumer_commit="<exact terminal accepted API consumer SHA>"
dispatch_commit="<exact reviewed dispatch SHA>"
test "$(git rev-parse "$dispatch_commit")" = "$(git rev-parse HEAD^)"
git merge-base --is-ancestor "$api_consumer_commit" "$dispatch_commit"
git diff --quiet "$api_consumer_commit" "$dispatch_commit" -- apps/api/Makefile apps/api/scripts/export_openapi.py apps/api/openapi/deepwork-api-v1.json

# One explicitly authorized public-index resolution/bootstrap, or the same
# commands against a pre-provisioned accepted cache when access is not granted.
uv lock --project apps/api
uv sync --project apps/api --python 3.12 --frozen --all-groups --no-python-downloads

lock_snapshot="$(mktemp)"
cp apps/api/uv.lock "$lock_snapshot"
uv lock --project apps/api --check --offline --no-python-downloads
uv lock --project apps/api --offline --no-python-downloads
cmp "$lock_snapshot" apps/api/uv.lock
UV_OFFLINE=true uv sync --project apps/api --python 3.12 --frozen --all-groups --no-python-downloads
make -C apps/api doctor
make -C apps/api check
make -C apps/api package-check
make -C apps/api openapi-check
UV_OFFLINE=true uv run --project apps/api --frozen --no-python-downloads python -c 'import alembic,psycopg,sqlalchemy,deepwork_api; print(alembic.__version__,psycopg.__version__,sqlalchemy.__version__)'

python3 -B tools/docs/generate.py --check
python3 -B tools/docs/check.py
git diff --check "$dispatch_commit" HEAD
git diff --name-only "$dispatch_commit" HEAD
git diff --quiet "$dispatch_commit" HEAD -- apps/api/Makefile apps/api/scripts apps/api/openapi apps/api/src apps/api/tests
test -z "$(git status --porcelain)"
```

The worker additionally verifies the lock contains no Git/editable/path/private
source, the built wheel metadata names the exact three direct package families,
all resolved artifacts have accepted hashes, a second final offline check is
green, and the canonical OpenAPI digest equals the terminal API consumer digest.

## Progress

- [x] 2026-07-23 — Drafted the product-scoped runtime manifest/lock boundary and
  kept it dependency-gated.
- [ ] Independent plan review accepts the Psycopg 3 async driver family, commands,
  package-index boundary, and exact three-file scope.
- [ ] Coordinator records a real terminal API consumer base and dispatches the
  manifest/lock worktree.
- [ ] Worker pins, locks, proves offline reproducibility, and obtains fresh
  implementation review.

## Surprises and discoveries

- 2026-07-23 — The current API scaffold already owns its Makefile and deterministic
  OpenAPI commands in the upstream API consumer. Consequence: this lock cell must
  not edit command scripts to make dependency verification pass.
- 2026-07-23 — Canonical architecture accepts the persistence framework but does
  not itself pin a PostgreSQL driver artifact. Consequence: Psycopg 3 async is an
  explicit review gate here, not an implicit implementation choice.

## Decision log

- 2026-07-23 — Use one product-scoped API runtime-lock cell after the API wire is
  terminal. Rationale: manifest ownership must not overlap API contract work.
- 2026-07-23 — Propose Psycopg 3 async and reject a `psql` subprocess shim.
  Rationale: application persistence needs typed async driver semantics and
  packaging evidence.
- 2026-07-23 — Permit at most one explicit public-index bootstrap, then require
  frozen offline replay. Rationale: exact artifacts must be obtainable once and
  reproducible without ambient network or credentials.

## Recovery and rollback

Lock generation is idempotent for the same manifest, uv/Python pair, platform,
and accepted package cache. A solver/install/import failure leaves API source and
OpenAPI untouched and records the safe dependency conflict.

Rollback takes the exact reviewed runtime-lock candidate. The Coordinator first
stops downstream product-demo work, reverts that candidate, then runs the
accepted API consumer's offline check/package/OpenAPI matrix. If revert or proof
fails, the branch remains blocked; no lock is hand-edited and no database or
external state exists.

## Outcomes and retrospective

Pending review and implementation. Completion records exact package versions and
hashes, lock digest, platform/toolchain, online preflight if used, offline replay,
wheel/import evidence, unchanged OpenAPI digest, changed-file inventory, reviewer
verdicts, and all remaining contract gates. It grants zero feature, E2E, live
provider, database-service, migration, or deployment acceptance.
