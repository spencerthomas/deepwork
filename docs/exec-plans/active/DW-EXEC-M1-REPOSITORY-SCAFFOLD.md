---
exec_plan_id: DW-EXEC-M1-REPOSITORY-SCAFFOLD
title: Wave 1 credential-free monorepo and fixture skeleton
status: reviewed-ready
created: 2026-07-23
updated: 2026-07-23
owners: [platform, developer-experience]
product_specs: [DW-FND-001, DW-FND-002, DW-FND-003, DW-FND-004, DW-FND-005, DW-QUAL-001]
scenario_ids: [AC-DW-FND-001-01, AC-DW-FND-001-03, AC-DW-FND-001-05, AC-DW-FND-001-06]
external_contracts: none
orchestration: manual-codex-worktree
base_commit: 06f051554bf938e919af5ab7855974098fbf3d2a
superseded_by: null
---

# Wave 1 credential-free monorepo and fixture skeleton

## Purpose and user-visible outcome

After this change, a new contributor can clone Deep Work, run one documented
bootstrap command, build independently locked Python and TypeScript packages, open
a clearly labelled credential-free shell, and receive actionable failures for
illegal architecture edges or generated drift. No live provider, credential,
deployment, production database, PWA push, Tauri capability, or product feature is
implemented.

This plan is the exact handoff for the next worktree agent. It is intentionally
smaller than all of Wave 1: create the package and command skeleton, prove public
imports and fixture honesty, and stop for review before frontend migration or live
integration.

## Canonical context to read

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

## Allowed paths

The next agent may create or edit:

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

## Recovery and safe retry

Scaffold steps must be additive and independently testable. Do not delete user or
legacy files to recover. On a failed dependency install, preserve manifest/lock
evidence, revert only files owned by this ExecPlan through a reviewed patch, and
retry from a clean package environment. No command may use production credentials,
external provider traffic, destructive database operations, signing, publishing,
deployment, automatic merge, or sibling-repository writes.

## Outcomes and retrospective

Pending. Complete with delivered behavior, deferred cells, validation evidence,
remaining debt, and the exact base commit for the next reviewed ExecPlan.
