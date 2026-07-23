---
exec_plan_id: DW-EXEC-M1-REPOSITORY-SCAFFOLD
title: Wave 1 credential-free monorepo and fixture skeleton
status: reviewed
superseded_by: null
owner: platform
reviewed_by: [architecture, developer-experience, security]
reviewed_at: 2026-07-23
primary_feature_id: DW-FND-001
supporting_feature_ids: [DW-FND-002, DW-FND-003, DW-FND-004, DW-FND-005, DW-QUAL-001]
issue: local:DW-M1-PLATFORM-001
created: 2026-07-23
last_updated: 2026-07-23
base_commit: 500eaa7faff57def970963160b3d8f1e90c94398
last_verified_commit: 500eaa7faff57def970963160b3d8f1e90c94398
risk: high
governed_paths: [Makefile, package.json, pnpm-workspace.yaml, pnpm-lock.yaml, turbo.json, apps/api/**, apps/web/**, apps/desktop/**, packages/agent/**, packages/domain/**, packages/sdk/**, packages/ui/**, internal/fixtures/**, internal/adapter-tests/**, tools/**, docs/generated/**, docs/exec-plans/active/DW-EXEC-M1-REPOSITORY-SCAFFOLD.md, docs/exec-plans/tech-debt-tracker.md, docs/QUALITY_SCORE.md]
contract_gates: [SPIKE-HARNESS-DOCS-001, SPIKE-HARNESS-ARCH-001, SPIKE-WORKTREE-001]
decision_gates: [DEC-002, DEC-003, DEC-004, DEC-025, DEC-031, DEC-032, DEC-033, DEC-035, DEC-038, DEC-042, DEC-043]
gate_review_status: reviewed-with-gates
gate_reviewed_by: [architecture, developer-experience, security]
gate_reviewed_at: 2026-07-23
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, docs/PLANS.md, docs/design-docs/architecture/application-architecture.md, docs/design-docs/engineering/conventions.md, docs/design-docs/decisions/index.md, docs/product-specs/foundations/dw-fnd-001-repository-oss-and-delivery-foundation.md, docs/product-specs/foundations/dw-fnd-002-design-system-shell-and-demo-mode.md, docs/product-specs/foundations/dw-fnd-003-application-service-state-and-security.md, docs/product-specs/foundations/dw-fnd-004-sdk-stream-and-fixture-contracts.md, docs/product-specs/foundations/dw-fnd-005-domain-identity-status-and-audit-model.md, docs/product-specs/quality/dw-qual-001-accessibility-performance-security-testing-and-release.md, docs/SECURITY.md, docs/RELIABILITY.md, docs/references/source-ledger.md]
scenario_ids: [AC-DW-FND-001-01, AC-DW-FND-001-03, AC-DW-FND-001-05, AC-DW-FND-001-06]
orchestration: manual-codex-worktree
dispatch_kind: program
dispatch_ready: false
agent_review_required: true
dependencies: []
blockers: []
---

# Wave 1 credential-free monorepo and fixture skeleton

## Purpose and user-visible outcome

After this change, a new contributor can clone Deep Work, run one documented
bootstrap command, build independently locked Python and TypeScript packages, open
a clearly labelled credential-free shell, and receive actionable failures for
illegal architecture edges or generated drift. No live provider, credential,
deployment, production database, PWA push, Tauri capability, or product feature is
implemented.

This is the non-dispatchable Wave 1 umbrella plan. It is intentionally smaller
than all product delivery, but broader than one safe worktree: bounded API, agent,
and TypeScript cells require their own reviewed plans and disjoint governed paths
before implementation. The coordinator alone integrates shared/root files,
`apps/web`, generated outputs, and product-demo composition.

## Context and orientation

Read in this order:

1. root `AGENTS.md` and `ARCHITECTURE.md`;
2. `docs/PLANS.md`, especially Wave 1;
3. `docs/design-docs/architecture/application-architecture.md`;
4. `docs/design-docs/engineering/conventions.md`;
5. `docs/product-specs/foundations/dw-fnd-001-repository-oss-and-delivery-foundation.md`;
6. `DW-FND-002` through `DW-FND-005` and `DW-QUAL-001`;
7. `docs/SECURITY.md`, `docs/RELIABILITY.md`, and this ExecPlan.

The sibling frontend is interaction evidence only and is out of scope. Do not copy
or modify it. `docs/plans/` is uncertain legacy evidence and is also out of scope.

## Scope

### In scope

- Root contributor command harness and pinned toolchain declarations.
- pnpm/Turborepo workspace skeleton for `apps/web`, `packages/domain`,
  `packages/sdk`, and the existing `packages/ui`, with explicit public exports.
- Independent Python 3.12 projects for `apps/api` and `packages/agent`, each with
  its own `pyproject.toml`, `uv.lock`, environment, Makefile, import package, and
  network-denied unit smoke test.
- Planned `apps/desktop` directory with a boundary README/AGENTS file only unless
  a separate Tauri toolchain decision is included in the reviewed change. Do not
  add remote-origin native capability yet.
- Language-neutral deterministic fixtures, one browser-local UI harness state,
  and the smallest API-backed product-demo health/shell path that can run without
  provider traffic or credentials.
- Architecture graph/check evolution from documentation-only manifest to actual
  package/import enforcement for the scaffolded paths.
- Deterministic generated package/architecture views and, once FastAPI exists,
  OpenAPI generation with drift checking.
- Package-local and root documentation explaining exact build/test commands.

### Out of scope

- Authentication, sessions beyond a fixture actor, OAuth, API-key storage, secret
  brokers, source registration, LangSmith/MDA/Fleet calls, streaming provider
  protocols, HITL, sandbox/GitHub integration, notifications, PWA push, Tauri
  native capability, deployment, CI, publishing, signing, or production hosting.
- Migrating UI routes/components from `deep-work-frontend`.
- Editing canonical feature outcomes to match an implementation shortcut.
- Installing Symphony or creating executable `WORKFLOW.md`.

### Permissions and risk boundary

- The governed paths in front matter are the complete implementation boundary.
- External systems, production credentials, destructive operations, deployment,
  publishing, signing, pushing, and merging are prohibited.
- The three open contract gates use their documented deterministic fallbacks.
  Architecture enforcement remains review-backed until its spike passes, and
  full-stack worktree concurrency remains serial.
- Architecture, developer-experience, and security review are required before
  integration. The implementation author cannot approve the change.

## Coordinator-owned umbrella paths

The coordinator may create or edit these paths during reviewed integration. No
worker receives this broad path set from the umbrella plan; each worker plan must
contain a disjoint subset.

- root `Makefile`, `package.json`, `pnpm-workspace.yaml`, `pnpm-lock.yaml`,
  `turbo.json`, toolchain/version/config files, contributor docs, and `.gitignore`;
- `apps/api/**`, `apps/web/**`, and boundary-only `apps/desktop/**`;
- `packages/agent/**`, `packages/domain/**`, `packages/sdk/**`, and `packages/ui/**`;
- `internal/fixtures/**`, `internal/adapter-tests/**`, `tools/**`, and generated
  documentation derived by those tools;
- this ExecPlan, relevant nested `AGENTS.md`, and debt/quality records.

Do not edit `docs/plans/**`, `docs/proposals/**`, `docs/references/legacy-plans/**`,
or any sibling repository. If a canonical decision is insufficient, record the
question in this plan and stop that cell rather than changing scope silently.

## Architecture and interfaces to establish

### Python

`apps/api` exposes a minimal FastAPI application from a public package entry point
and a deterministic `/health` plus fixture-only product-demo endpoint. Its source
tree already follows `domain -> ports -> application <- transport/adapters`, with
concrete wiring only in `bootstrap`. Persistence may be an in-memory fixture
adapter for this change; do not imply production durability.

`packages/agent` is separately installable and exposes a typed graph factory or
placeholder public entry point without importing `apps/api`. It may use a
deterministic no-network test double; do not call upstream services. Exact public
Deep Agents/LangGraph package pins must be justified from the pinned references or
left as a minimal package boundary if compatibility cannot be proven locally.
Both Python distributions include typed public exports and a `py.typed` marker;
their clean-wheel tests verify that the marker is packaged.

### TypeScript

`packages/domain` has no React, Next.js, SDK, fetch, environment, provider,
generated DTO, credential, Node-only, or Tauri import. It exports the smallest
qualified identity/capability/status types used by the fixture shell.

`packages/sdk` depends on domain and generated Deep Work transport only. It exposes
separate query/mutation and stream interfaces, even if the initial implementation
contains only fixture health/query behavior.

`packages/ui` depends on domain plus presentation libraries and exports one
accessible shell/status primitive. It must not depend on SDK/network/routes/
fixtures/generated DTOs/provider types.

`apps/web` is the composition root. It renders a persistent fixture banner, five
canonical navigation destinations, and honest unavailable states. No component
constructs provider or application URLs directly.

### Fixtures and generated outputs

Versioned JSON fixtures carry evidence class, source-qualified identity, capability
state, observed time, contract/adapter version, and safe reason. They contain no
real endpoint, token, actor data, repository content, or plausible live success.

Generated files carry a source and generation command. A clean run produces no
diff; manual edits fail. OpenAPI is generated only when the API contract exists.

## Milestones

### M1 — Pin the scaffold method

- Record exact Node, pnpm, Python, uv, TypeScript, FastAPI/Pydantic, lint, format,
  and test versions with compatibility evidence.
- Confirm local availability and clean-install behavior before committing locks.
- Add a decision-log entry for any deviation from accepted conventions.

Exit: a clean checkout can identify required tools without global hidden state.

### M2 — Create legal package boundaries

- Scaffold the four TypeScript roots and two independent Python projects.
- Add explicit exports, minimal imports, package-local tests, and nested guidance.
- Extend the architecture checker with positive and intentional negative fixtures.

Exit: packages build/import through public entry points; illegal UI-to-SDK,
domain-to-framework, API-to-agent, and transport-to-adapter edges fail clearly.

### M3 — Prove fixture honesty

- Add one browser-local shell fixture with no network.
- Add the smallest loopback API-backed product-demo shell/health path.
- Make fixture evidence permanent in the UI and structured logs.
- Deny external network in unit/fixture tests and scan fixtures for credential-like
  data.

Exit: UI harness and product demo are visibly distinct; neither can imply a live
source capability.

### M4 — Establish reproducible commands and generation

- Implement root `doctor`, `bootstrap`, `dev-demo`, `check`,
  `check-architecture`, and `check-docs` fan-out with package-local equivalents.
- Generate package/architecture views and OpenAPI if applicable.
- Ensure a second run is clean and failures name the owning package and repair.

Exit: all documented commands exist and generated drift is detectable.

### M5 — Review handoff

- Update Progress, Discoveries, Decision Log, validation transcript, and outcomes.
- Update `docs/QUALITY_SCORE.md` and close only objectively satisfied debt rows.
- List exact changed files and confirm no sibling/legacy/provider scope changed.
- Stop for human review; do not begin UI migration or live contracts.

## Progress

- [x] 2026-07-23 — Plan created and reviewed as the Wave 0 handoff.
- [ ] M1 — toolchain method pinned.
- [ ] M2 — package boundaries scaffolded.
- [ ] M3 — fixture honesty proven.
- [ ] M4 — reproducible commands and generation proven.
- [ ] M5 — review packet complete.

## Surprises and discoveries

None yet. Record dated evidence here, including missing local tools, incompatible
pins, unexpectedly coupled imports, or commands that require network/global state.

## Decision log

- 2026-07-23: Manual Codex worktree dispatch is required. Symphony and
  `WORKFLOW.md` remain gated by `SPIKE-SYMPHONY-001`.
- 2026-07-23: This change may create root manifests and locks because that is its
  explicit scope; it may not use them to introduce live providers or product
  features.
- 2026-07-23: Tauri receives at most a boundary placeholder. Native capability and
  remote-origin decisions remain gated.

## Validation and acceptance

At minimum, record exact results for:

```text
make doctor
make bootstrap
make check-docs
make check-architecture
make check
make dev-demo
git diff --exit-code after deterministic generation
```

If the final names differ, update canonical guidance and this plan in the same
review. Do not replace a missing command with an unrelated passing check.

Executable acceptance:

1. Given a clean clone without credentials, bootstrap and all no-network unit
   checks complete from documented commands.
2. Given each Python project, a clean package-local environment builds, installs,
   imports its public entry point, and does not import the other application.
3. Given each TypeScript package, a clean consumer imports only declared exports;
   intentional forbidden edges fail with an actionable architecture rule.
4. Given the UI harness, no network call occurs and the interface permanently
   identifies deterministic fixture evidence.
5. Given the API-backed product demo, only loopback/internal fixture services are
   contacted and the UI cannot advertise an unproven live capability.
6. Given generated artifacts, regeneration produces no diff; a deliberate manual
   edit is detected.
7. Given two worktrees if the full stack exists, their ports, database/schema,
   objects, browser storage, telemetry, and proof paths do not collide. If the full
   isolation stack is not in this bounded change, leave `DEBT-004` open and do not
   claim `SPIKE-WORKTREE-001` passed.

## Detailed implementation approach

Create the independently locked package boundaries in disjoint cells, then let the
coordinator integrate root manifests, locks, generated outputs, `apps/web`, and the
product-demo composition. Each cell runs package-local checks and receives an
independent review before its accepted commit is integrated.

## Recovery and safe retry

Scaffold steps must be additive and independently testable. Do not delete user or
legacy files to recover. On a failed dependency install, preserve manifest/lock
evidence, revert only files owned by this ExecPlan through a reviewed patch, and
retry from a clean package environment. No command may use production credentials,
external provider traffic, destructive database operations, signing, publishing,
deployment, automatic merge, or sibling-repository writes.

Until `SPIKE-WORKTREE-001` passes, at most one full-stack application or product-
demo worktree may run. Package-only and documentation-only worktrees with disjoint
governed paths may run in parallel.

## Rollout and handoff

This credential-free scaffold has no production rollout. Accepted package cells
hand sanitized validation evidence and exact commits to the coordinator. The
coordinator composes the single allowed product demo, reruns root checks, records
the next reviewed base, and leaves every live capability disabled.

## Outcomes and retrospective

Pending. Complete with delivered behavior, deferred cells, validation evidence,
remaining debt, and the exact base commit for the next reviewed ExecPlan.
