---
exec_plan_id: DW-EXEC-M1-AGENT-SCAFFOLD
title: Wave 1 independent Python agent package scaffold
status: completed
superseded_by: null
owner: agent
reviewed_by: [api-package-reviewer]
reviewed_at: 2026-07-23
primary_feature_id: DW-FND-001
supporting_feature_ids: [DW-AGENT-003, DW-AGENT-005, DW-QUAL-001]
issue: local:DW-M1-AGENT-001
created: 2026-07-23
last_updated: 2026-07-23
base_commit: 3dbe6629d8053380ab6a8bff6d2fcb462f854256
last_verified_commit: e991700cb25e5be8020ace8d905c5ecbefa6600e
risk: medium
governed_paths: [packages/agent/**, docs/exec-plans/completed/DW-EXEC-M1-AGENT-SCAFFOLD.md]
contract_gates: [SPIKE-HARNESS-ARCH-001, SPIKE-CONFIG-001]
decision_gates: [DEC-003, DEC-024, DEC-028, DEC-031, DEC-032, DEC-043]
gate_review_status: reviewed-with-gates
gate_reviewed_by: [api-package-reviewer]
gate_reviewed_at: 2026-07-23
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, docs/PLANS.md, docs/exec-plans/active/DW-EXEC-M1-REPOSITORY-SCAFFOLD.md, docs/design-docs/architecture/application-architecture.md, docs/design-docs/engineering/conventions.md, docs/design-docs/decisions/index.md, docs/product-specs/foundations/dw-fnd-001-repository-oss-and-delivery-foundation.md, docs/product-specs/agents/dw-agent-003-create-draft-import-export-and-deploy.md, docs/product-specs/agents/dw-agent-005-tools-connectors-permissions-skills-memory-and-subagents.md, docs/product-specs/quality/dw-qual-001-accessibility-performance-security-testing-and-release.md, docs/SECURITY.md, docs/references/source-ledger.md]
scenario_ids: [AC-DW-FND-001-03, AC-DW-FND-001-07]
dispatch_kind: cell
dispatch_ready: false
agent_review_required: true
dependencies: []
blockers: []
---

# Wave 1 independent Python agent package scaffold

## Purpose and observable result

Create one independently installable, independently locked Python 3.12 package
boundary under `packages/agent` that a contributor can build, install, import, type
check, and test without Deep Work credentials or application-service imports. The
package exposes deliberate typed public exports, a `py.typed` marker, and either a
verified graph factory/entry point or an explicitly unavailable placeholder when
the pinned public Deep Agents/LangGraph contract cannot yet be proved.

This cell contributes package-bounded evidence to `AC-DW-FND-001-03` and
`AC-DW-FND-001-07`. The clean-contributor and `E2E-V1-11-CONTRIBUTOR` journeys
remain downstream integration and release evidence; this cell does not claim them.

## Context and orientation

The Wave 1 umbrella plan separates `packages/agent` from the FastAPI application
service and from all TypeScript packages. `packages/agent` owns a portable agent
graph boundary, typed configuration/state, tools and middleware only when their
contracts are verified, plus package-local tests and evaluations. It must never
own FastAPI routes, application sessions, tenant tables, credential material, or
Deep Work API behavior.

The exact distribution, import, dependency, and graph-target names become public
compatibility choices. Canonical architecture proposes the import package
`deepwork_agent` and an explicit `langgraph.json` target; this cell must verify
those choices against installed public packages before exposing runtime behavior.
Reference repositories guide engineering method but are not deployed-runtime
authority.

## Scope

### In scope

- A package-local `pyproject.toml`, `uv.lock`, `Makefile`, `README.md`, and scoped
  `AGENTS.md` for an independent Python 3.12 distribution.
- `src/deepwork_agent/` with explicit `__all__`, complete public annotations,
  `py.typed`, and the smallest typed config/state and graph entry-point boundary.
- A reviewed `langgraph.json` only when its target shape is supported by pinned
  public package evidence; otherwise an explicit unavailable placeholder and a
  recorded gate remain.
- Package-local Ruff, `ty`, pytest, build, clean-wheel install/import, public-export,
  forbidden-import, and no-network tests.
- A deterministic package-local evidence directory for sanitized command
  transcripts and artifact manifests used by independent review.

### Non-goals

- A production agent graph, model call, provider adapter, live deployment, source
  registration, API route, database/session model, credential flow, or product UI.
- Implementing project import/export, deployment, MCP, connectors, memory,
  subagents, HITL, sandbox, schedules, or evaluation-quality claims from
  `DW-AGENT-003` or `DW-AGENT-005`.
- Editing root manifests, root locks, `apps/**`, another package, shared fixtures,
  generated documentation, architecture tooling, or the Wave 1 umbrella plan.
- Copying private upstream internals or inventing `/v1/deepagents/*`, MDA, Fleet,
  graph configuration, or deployment contracts.

### Permissions and risk boundary

- Governed paths are exactly `packages/agent/**` and this ExecPlan. Any required
  root/shared change is a coordinator-owned follow-up, not an expansion of this
  cell.
- External provider traffic, credentials, production data, destructive actions,
  deployment, publishing, signing, pushing, merging, and sibling-repository writes
  are prohibited.
- Dependency resolution may use only reviewed public package indexes during the
  implementation bootstrap. Unit, package, and fixture tests deny outbound
  network access and use no secret-bearing environment.
- Risk is medium because this cell establishes a public package and lockfile but
  has no application integration, production state, or external effect.
- The implementation author cannot approve this plan or its resulting diff.
  Independent agent/package and architecture review are required before dispatch
  and integration.

## Authoritative sources and prerequisites

- Owning product specification:
  `docs/product-specs/foundations/dw-fnd-001-repository-oss-and-delivery-foundation.md`.
- Wave 1 authority:
  `docs/exec-plans/active/DW-EXEC-M1-REPOSITORY-SCAFFOLD.md` at the exact base
  commit in front matter.
- Architecture and package layout: `ARCHITECTURE.md` and
  `docs/design-docs/architecture/application-architecture.md`.
- Engineering method: `docs/design-docs/engineering/conventions.md`, especially
  the independent Python project, Ruff, `ty`, uv, typed public API, clean-package,
  and network-denied test requirements.
- Security authority: `docs/SECURITY.md`, especially dependency provenance,
  credential exclusion, untrusted-content boundaries, and secret-free evidence.
- Relevant accepted decisions: `DEC-003`, `DEC-024`, `DEC-028`, `DEC-031`,
  `DEC-032`, and `DEC-043` in the decision register.
- Supporting constraints: `DW-AGENT-003` owns portable project declarations and
  `DW-AGENT-005` owns portable tool/policy declarations; this scaffold must leave
  legal extension points without implementing their gated outcomes.

No implementation may start while this plan remains draft. Cross-review must
confirm metadata, governed paths, scenario contribution, gate fallbacks, commands,
and the exact base, then change review/dispatch metadata in this plan.

## Contract and decision gates

- `SPIKE-HARNESS-ARCH-001` is open. Fallback: enforce the documented package
  boundary with package-local forbidden-import tests and independent architecture
  review; do not claim the repository-wide architecture spike passed.
- `SPIKE-CONFIG-001` is open. Fallback: ship only a typed, importable package
  boundary and an explicit runtime-unavailable result. Do not guess graph config,
  project fields, provider/model defaults, or deployment behavior.
- `SPIKE-WORKTREE-001` does not block this package-only cell. Until it passes, this
  worktree must not start a full-stack application or product demo; disjoint
  package/documentation work may proceed in parallel.
- The listed decisions are accepted architecture constraints, but their application
  to this bounded cell remains unreviewed until independent cross-review completes.

## Interfaces and invariants

- Distribution and import names are explicit and tested from a built wheel; the
  intended import root is `deepwork_agent` unless review records a supported
  alternative before implementation.
- Public symbols are exported deliberately through `deepwork_agent.__all__`, carry
  complete annotations and Google-style documentation, and do not re-export
  third-party implementation types.
- `py.typed` is present in the built wheel and visible to a clean consumer.
- The graph entry point, when present, is importable without a provider credential
  or network call. Importing the package has no side effects.
- `packages/agent` imports no `apps/api`, FastAPI, SQLAlchemy, application session,
  tenant, browser, TypeScript, or sibling package code.
- Configuration contains no credential material. Provider credentials, tenant
  identity, application sessions, database state, routes, and deployment control
  stay outside this package.
- Unit tests deny sockets. Any future live integration/evaluation test is separately
  marked, excluded from the default suite, and remains out of scope here.
- Package commands are deterministic, package-local, and do not depend on a root
  Python environment or hidden `PYTHONPATH` state.

## Milestones

### Milestone 1 - Pin the independent package method

- Verify Python 3.12 and uv availability and record exact versions.
- Select exact maintained, license-compatible package pins from public evidence.
- If Deep Agents/LangGraph compatibility cannot be proved, select the documented
  minimal-boundary fallback without adding speculative runtime dependencies.
- Record the distribution/import/graph-target decision in this plan.

Acceptance:

- `make -C packages/agent doctor` reports exact required and missing optional
  tools without modifying the checkout.
- `uv lock --project packages/agent --check` succeeds after the reviewed lock is
  created.
- Evidence: `packages/agent/evidence/DW-M1-AGENT-001/toolchain.txt` and
  `dependency-manifest.txt` contain sanitized version and provenance records.

### Milestone 2 - Establish typed public and graph boundaries

- Add package metadata, public exports, `py.typed`, typed configuration/state, and
  the verified graph target or explicit unavailable placeholder.
- Add package-local instructions and exact commands.
- Prove import-time behavior is credential-free and has no network or application
  dependency.

Acceptance:

- `make -C packages/agent lint` and `make -C packages/agent typecheck` succeed.
- `make -C packages/agent test` succeeds with outbound sockets disabled.
- Intentional forbidden-import fixtures fail with the importing file, forbidden
  boundary, and architecture source named.
- Evidence: `packages/agent/evidence/DW-M1-AGENT-001/checks.txt` and
  `public-api.txt`.

### Milestone 3 - Prove the built artifact in a clean consumer

- Build wheel and source distribution from the locked environment.
- Install the wheel into a clean temporary environment without repository import
  paths.
- Import every declared public symbol, inspect `py.typed`, and verify no
  application/runtime provider is contacted.

Acceptance:

- `make -C packages/agent build` produces only the expected package artifacts.
- `make -C packages/agent package-check` installs and verifies the wheel in a
  clean environment.
- A second build from the same source and lock produces an equivalent artifact
  manifest; no generated or lock drift remains.
- Evidence: `packages/agent/evidence/DW-M1-AGENT-001/artifacts.json` and
  `clean-wheel.txt`.

### Milestone 4 - Independent review handoff

- Update all living sections with exact commands, observations, evidence paths,
  deviations, and remaining gates.
- Provide the coordinator the exact implementation commit and changed-file list.
- Stop before root integration, product-demo composition, or any live contract.

Acceptance:

- An independent reviewer confirms package ownership, public API, dependency
  provenance, no-network proof, forbidden imports, clean artifact, scenario
  contribution, and scope containment.
- `git diff --name-only <base>...HEAD` contains only the two governed path classes.

## Detailed implementation approach

1. Create the package-local metadata and commands without touching root/shared
   files. Pin Python and uv semantics before resolving dependencies.
2. Implement the smallest typed `deepwork_agent` public surface. Prefer a public
   Deep Agents/LangGraph factory only if installed package evidence proves its
   import and target contract; otherwise expose a deterministic unavailable
   boundary with the gate and fallback named.
3. Add tests before runtime features: public exports, `py.typed`, no import side
   effects, socket denial, forbidden application imports, and config redaction.
4. Build and install the wheel in a clean temporary environment and retain a
   sanitized evidence manifest under the package path.
5. Rerun the package-local suite, update this plan, and hand the exact commit to a
   fresh reviewer. The coordinator alone decides whether and how to integrate it
   into root orchestration.

## Validation and proof

The implementation must make these package-local commands real and retain their
exact output; they do not exist merely because this plan names them:

```text
make -C packages/agent doctor
make -C packages/agent bootstrap
make -C packages/agent lock-check
make -C packages/agent format-check
make -C packages/agent lint
make -C packages/agent typecheck
make -C packages/agent test
make -C packages/agent build
make -C packages/agent package-check
git diff --check
git diff --name-only 3dbe6629d8053380ab6a8bff6d2fcb462f854256...HEAD
```

Expected proof:

- all default checks run without provider credentials or external runtime calls;
- a clean wheel consumer imports only deliberate public exports and finds
  `py.typed`;
- no package import resolves through the repository checkout or another Deep Work
  package;
- forbidden application-service dependencies fail with actionable diagnostics;
- runtime/config behavior not proved by accepted public evidence remains
  unavailable, not simulated; and
- changed files remain within the two governed path classes.

The coordinator must separately run root documentation, architecture, generated,
and integration checks after integration. This cell cannot edit those tools or
claim their success.

Implementation results at 2026-07-23 12:33 AEST:

- `doctor`, frozen `bootstrap`, Ruff format/lint, `ty`, pytest, build,
  clean-wheel installation, lock check, and `git diff --check` passed.
- The unit suite passed 11 tests with sockets disabled, including a direct blocked
  socket assertion and an AST import-boundary scan.
- The clean consumer used Python isolated mode, no `PYTHONPATH`, `--no-index`, and
  `--no-deps`; it found `py.typed`, imported every public export, and observed only
  the explicit `SPIKE-CONFIG-001` unavailable state.
- Two fresh builds produced identical SHA-256 values and the read-only package
  check matched them against reviewed evidence: wheel
  `d48e7e836f33a653f4fe0b628081555b4c6fce3717328d998be558ac39146378`
  and source distribution
  `a5f58d1f14a606fc46064395654fd8b82abc4ff7937f8f7d810b182e83e17c3a`.
- Evidence refresh is a separate explicit `make -C packages/agent
  update-evidence` action. The final frozen `make -C packages/agent check`
  verifies rather than rewrites the manifest and leaves tracked status clean.
- Sanitized proof is retained under
  `packages/agent/evidence/DW-M1-AGENT-001/`.

## Idempotence, rollback, and recovery

Package bootstrap, lint, type, test, build, and clean-consumer commands must be
safe to rerun. Failed dependency resolution preserves the proposed manifest and
error evidence, makes no root/shared change, and retries only after review of the
pin or fallback. Build and temporary consumer directories are package-local or
system-temporary and are cleaned without touching user data.

Before publication or production use, rollback is the reviewed reversion of this
cell's package-only commit. There are no migrations, durable records, external
deployments, published artifacts, or credentials to undo. If a public package
contract cannot be verified, retain the minimal unavailable boundary or stop the
cell; do not widen scope or delete unrelated files.

## Rollout and handoff

This scaffold has no production rollout. After independent review, hand the exact
accepted commit, dependency provenance, artifact manifest, command transcript,
and remaining gates to the coordinator. Root manifests, root command fan-out,
architecture tooling, generated views, API/web composition, and the product demo
remain coordinator-owned integration work.

The accepted package remains credential-free and runtime-unavailable wherever a
contract is unresolved. Later reviewed ExecPlans own portable project schema,
tools/policies, real graph behavior, external deployment, evaluations, and
product integration.

## Progress

- [x] 2026-07-23 - Draft cell plan created against exact base
  `3dbe6629d8053380ab6a8bff6d2fcb462f854256`; no implementation started.
- [x] 2026-07-23 - Independent `api-package-reviewer` cross-review accepted the
  metadata, authority, scenarios, gate fallbacks, commands, and governed paths.
- [x] 2026-07-23 - Plan promoted to `reviewed`; review and completed gate-review
  metadata recorded, blockers confirmed empty, and `dispatch_ready` set true.
- [x] 2026-07-23 12:20 AEST - Milestone 1 complete; Python/uv and exact public
  package pins retained in `toolchain.txt`, `dependency-manifest.txt`, and
  `uv.lock`.
- [x] 2026-07-23 12:28 AEST - Milestone 2 complete; deliberate typed exports,
  explicit unavailable graph boundary, forbidden-import fixtures, and 11 no-network
  unit tests pass.
- [x] 2026-07-23 12:33 AEST - Milestone 3 complete; wheel/sdist build, isolated
  no-index wheel install, `py.typed`, public exports, and reproducible hashes
  retained in the evidence directory.
- [x] 2026-07-23 - Independent review found the retained hashes were generated
  before the final source state and that verification rewrote its own expected
  evidence. Rework now separates explicit evidence refresh from immutable checks,
  compares two fresh builds, and proves the full frozen check leaves tracked
  status clean.
- [x] 2026-07-23 - Milestone 4 accepted by independent implementation review at
  integrated commit `e991700cb25e5be8020ace8d905c5ecbefa6600e`.

## Surprises and discoveries

- 2026-07-23 - The Wave 1 umbrella deliberately permits a minimal typed package
  boundary when exact Deep Agents/LangGraph compatibility cannot be proved.
  Consequence: runtime behavior is not a prerequisite for this scaffold and must
  remain explicitly unavailable rather than guessed.
- 2026-07-23 - `SPIKE-WORKTREE-001` limits concurrent full-stack/product-demo
  work, not disjoint package-only planning. Consequence: this lane may be reviewed
  in parallel but may not start a product demo.
- 2026-07-23 12:20 AEST - uv selected a cached managed CPython 3.12.11 for the
  frozen environment while the package doctor used Homebrew CPython 3.12.7.
  Consequence: `requires-python` is pinned to the reviewed Python 3.12 support
  line, and both exact execution versions are retained rather than implying one
  hidden interpreter.
- 2026-07-23 12:33 AEST - The minimal standard-library runtime package builds
  reproducibly without Deep Agents/LangChain/LangGraph dependencies. Consequence:
  `SPIKE-CONFIG-001` stays open, `langgraph.json` stays absent, and later runtime
  work can replace the explicit unavailable boundary only through a reviewed plan.
- 2026-07-23 12:34 AEST - A raw `uv lock --check` attempted to initialize uv's
  user cache outside the governed package and failed under workspace isolation.
  Consequence: `make -C packages/agent lock-check` now applies the same package-
  local cache/environment boundary as every other uv command.
- 2026-07-23 12:38 AEST - A PEP 517-only Hatchling requirement did not place its
  transitive build tools in the package lock. Consequence: exact Hatchling is also
  a locked development tool, and `make build` invokes it from the frozen package
  environment rather than resolving an isolated build environment at run time.
- 2026-07-23 - The first retained artifact hashes predated final build-tooling
  changes, while `package-check` silently replaced the expected manifest.
  Consequence: a green check did not prove that reviewed evidence matched the
  final source. The verifier now treats evidence as immutable by default and
  requires two matching fresh builds before comparison or explicit refresh.

## Decision log

- 2026-07-23 - Decision: `DW-FND-001` is the sole primary owner because this cell
  establishes repository/package contribution infrastructure, not an agent product
  workflow. `DW-AGENT-003`, `DW-AGENT-005`, and `DW-QUAL-001` are supporting
  constraints only. Rationale: their user outcomes remain gated and out of scope.
- 2026-07-23 - Decision: use risk `medium`. Rationale: the cell creates an
  independently locked public package surface, but cannot touch application state,
  shared integration files, credentials, or external systems.
- 2026-07-23 - Decision: keep `dispatch_ready: false`, reviewer fields empty, and
  gate review unreviewed. Rationale: the author cannot self-approve and a fresh
  cross-review is still required.
- 2026-07-23 - Decision: accept the independent `api-package-reviewer` cross-
  review and promote this bounded cell to dispatch-ready. Rationale: the reviewer
  confirmed the exact base, package-only scope, scenario contribution, gate
  fallbacks, validation contract, and disjoint governed paths. Approved by:
  `api-package-reviewer`.
- 2026-07-23 12:20 AEST - Decision: pin Hatchling 1.31.0, pytest 9.1.1,
  pytest-socket 0.8.0, Ruff 0.15.22, and ty 0.0.62 in the package-owned manifest
  and lock. Rationale: these current public-index releases resolved for Python
  3.12 with no runtime dependencies; exact hashes remain in `uv.lock`.
- 2026-07-23 12:28 AEST - Decision: expose `create_graph()` as a typed fail-closed
  boundary and omit `langgraph.json`. Rationale: the accepted fallback prohibits
  guessing configuration or graph-target contracts while `SPIKE-CONFIG-001` is
  open. Consequence: imports and artifact checks are real, but runtime capability
  remains explicitly unavailable.
- 2026-07-23 12:34 AEST - Decision: make lock verification a package-local Make
  target instead of relying on uv's default user cache. Rationale: all package
  commands must be reproducible inside governed paths without hidden home state.
- 2026-07-23 12:38 AEST - Decision: build through locked Hatchling instead of an
  ephemeral PEP 517 environment. Rationale: the package lock must cover the actual
  build backend and its transitive tools, not only lint/test/type dependencies.
- 2026-07-23 - Decision: make artifact evidence update an explicit maintainer
  action and keep `package-check` read-only. Rationale: verification cannot
  establish evidence integrity if it rewrites the expected result. Consequence:
  every check performs a second clean build, compares both artifact pairs, then
  compares the fresh manifest with the reviewed tracked JSON.

## Outcomes and retrospective

Implementation and rework are complete and independently accepted. The package is
independently locked, typed, formatted, linted, type-checked, network-denied,
buildable, clean-installable, and reproducible across two fresh builds. Artifact
evidence is refreshed only through an explicit action; ordinary verification is
immutable and leaves the tracked checkout clean. The accepted wheel hash is
`d48e7e836f33a653f4fe0b628081555b4c6fce3717328d998be558ac39146378`
and the accepted sdist hash is
`a5f58d1f14a606fc46064395654fd8b82abc4ff7937f8f7d810b182e83e17c3a`.
The package contributes enforceable package direction to `AC-DW-FND-001-03` and
proves private runtime packages are not a default prerequisite for
`AC-DW-FND-001-07`.

No external runtime, provider call, credential, `langgraph.json`, application
import, root/shared edit, migration, deployment, or publication was introduced.
`SPIKE-HARNESS-ARCH-001` and `SPIKE-CONFIG-001` remain open under their reviewed
fallbacks. Independent re-review accepted the immutable double-build proof and
clean worktree at the integrated commit.
