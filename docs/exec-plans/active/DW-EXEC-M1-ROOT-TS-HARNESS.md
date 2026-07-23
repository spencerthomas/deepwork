---
exec_plan_id: DW-EXEC-M1-ROOT-TS-HARNESS
title: Root TypeScript workspace baseline
status: reviewed
superseded_by: null
owner: program-coordinator
reviewed_by: [ts-package-planner-reviewer, root-ts-implementation-reviewer]
reviewed_at: 2026-07-23
primary_feature_id: DW-FND-001
supporting_feature_ids: [DW-FND-002, DW-FND-004, DW-FND-005]
issue: local:DW-M1-ROOT-TS-001
created: 2026-07-23
last_updated: 2026-07-23
base_commit: 3dbe6629d8053380ab6a8bff6d2fcb462f854256
last_verified_commit: 3dbe6629d8053380ab6a8bff6d2fcb462f854256
risk: medium
governed_paths: [package.json, pnpm-workspace.yaml, turbo.json, .node-version, .npmrc, internal/tsconfig/**, docs/exec-plans/active/DW-EXEC-M1-ROOT-TS-HARNESS.md]
contract_gates: [SPIKE-HARNESS-ARCH-001]
decision_gates: [DEC-025, DEC-031]
gate_review_status: reviewed-with-gates
gate_reviewed_by: [ts-package-planner-reviewer]
gate_reviewed_at: 2026-07-23
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, docs/PLANS.md, docs/design-docs/architecture/application-architecture.md, docs/design-docs/engineering/conventions.md, docs/design-docs/decisions/index.md, docs/product-specs/foundations/dw-fnd-001-repository-oss-and-delivery-foundation.md, docs/SECURITY.md]
scenario_ids: [AC-DW-FND-001-03]
dispatch_kind: cell
dispatch_ready: true
agent_review_required: true
dependencies: []
blockers: []
---

# Root TypeScript workspace baseline

## Purpose and observable result

Create the smallest pinned root pnpm/Turbo and shared TypeScript configuration
needed for the disjoint domain, SDK, and UI source/manifests lane to begin. This
cell owns no lock, package source, package importer, or web application and makes
no frozen-install/build claim.

## Context and orientation

The reviewed Wave 0.1 commit deliberately keeps root manifests and the future
single TypeScript lock coordinator-owned. Workspace/tool declarations and shared
compiler profiles must exist before package workers can author compatible package
manifests. The lock cannot be generated truthfully until those importers exist.

## Scope

### In scope

- Pin Node 24, pnpm 10, Turbo, TypeScript, Oxfmt, and Oxlint at reviewed exact
  versions compatible with the canonical conventions.
- Declare only `apps/*`, `packages/*`, and `internal/*` workspace roots.
- Add strict ES2022 shared compiler profiles under `internal/tsconfig/**`.
- Leave `pnpm-lock.yaml` absent for the later coordinator lock-integration cell
  that consumes reviewed package manifests.

### Non-goals

- Package source/manifests, `pnpm-lock.yaml`, dependency resolution/installation,
  `apps/web`, Next.js, React, Zod, testing libraries, generated contracts,
  fixtures, root Makefile, CI, product demo, or runtime code.
- Provider packages, credentials, external service calls, publishing, deployment,
  push, merge, or sibling changes.

### Permissions and risk boundary

- Only the exact governed paths in front matter may change.
- No package-index, runtime, provider, or other external network access is needed.
- Exact tool declarations must contain no local source path, credential, or
  unreviewed package.

## Authoritative sources and prerequisites

- Base: `3dbe6629d8053380ab6a8bff6d2fcb462f854256`.
- The Wave 1 umbrella is planning context carried by that reviewed base, not a
  nonterminal DAG dependency.
- `SPIKE-HARNESS-ARCH-001` remains open; manual boundary review is the fallback.

## Interfaces and invariants

- One root pnpm lock; no package-level npm/yarn/pnpm lock.
- Strict ES2022 ESM defaults include `strict`, `isolatedModules`,
  `noImplicitReturns`, `noFallthroughCasesInSwitch`, `noUncheckedIndexedAccess`,
  casing checks, `allowJs: false`, and a contract profile with
  `skipLibCheck: false`.
- Root scripts fan out through Turbo but contain no product logic.
- The root workspace does not import or depend on package source.

## Milestones

### Milestone 1 — Declare the workspace toolchain

Add exact engine/package-manager declarations, workspace globs, Turbo task graph,
and formatter/linter/compiler development dependencies without resolving them.

Acceptance:

- Standard-library validation reports the exact Node, pnpm, Turbo, TypeScript,
  Oxfmt, and Oxlint declarations and accepted workspace globs.
- `pnpm-lock.yaml` remains absent.

### Milestone 2 — Publish strict shared compiler profiles

Add base, library, and contract JSON configurations without references to package
source that does not yet exist.

Acceptance:

- JSON files parse and contain the canonical strict options.
- Shared JSON profiles parse and contain the exact canonical strict options.

## Progress

- [x] 2026-07-23 — Independent review accepted pins, paths, gates, commands, and
  the declarations -> package manifests -> lock integration sequence.
- [x] 2026-07-23 — Toolchain/workspace manifests complete; no lock generated.
- [x] 2026-07-23 — Shared compiler profiles and deterministic validation complete.
- [x] 2026-07-23 — Independent implementation review accepted; baseline ready
  for the TypeScript source/manifests cell and later lock-integration cell.

## Surprises & Discoveries

- None yet. Record unavailable/cached toolchains, package incompatibility, lock
  nondeterminism, or platform constraints with exact evidence.
- 2026-07-23 — Review found that generating a lock before workspace importers
  exist would make the first frozen install stale. Consequence: this cell excludes
  the lock and a later coordinator cell owns first lock integration.
- 2026-07-23 — The implementation host currently provides Node `v20.18.0`,
  Corepack `0.29.3`, and pnpm `9.12.1`. Consequence: this cell records and
  statically validates the canonical Node 24/pnpm 10 declarations without
  changing the host or making install/build claims.

## Decision Log

- 2026-07-23 — Decision: split root TypeScript ownership from package source.
  Rationale: the coordinator owns shared manifests/locks and worker governed paths
  must remain disjoint. Consequence: TS package dispatch waits for this cell.
- 2026-07-23 — Decision: keep shared compiler profiles path-independent.
  Rationale: `rootDir`, `outDir`, and build-info paths resolve relative to the
  configuration that declares them. Consequence: each consuming package owns
  those paths while inheriting strict language and emit policy here.
- 2026-07-23 — Decision: keep the universal base library set to `ES2022` only.
  Rationale: browser globals in the base would weaken the pure domain boundary.
  Consequence: browser-owning packages must opt into `DOM` libraries locally.

## Detailed implementation approach

Verify available Node/Corepack versions without installing, select exact stable
pins consistent with accepted conventions, add the minimal manifests/configs, and
run JSON, pin, workspace-glob, no-lock, secret/local-path, and diff checks. Do not
add package dependencies on behalf of future workers.

## Validation and proof

```text
node --version
corepack --version
python3 -m json.tool package.json
python3 -m json.tool turbo.json
python3 -m json.tool internal/tsconfig/base.json
test ! -e pnpm-lock.yaml
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
git diff --check
```

Retain sanitized command output in the plan. Exact declarations are implementation
evidence; no install, build, fixture, or live product capability is claimed.

Implementation evidence on 2026-07-23:

```text
node --version       -> v20.18.0 (host observation; canonical pin is 24.18.0)
corepack --version   -> 0.29.3
pnpm --version       -> 9.12.1 (host observation; canonical pin is 10.34.5)
JSON parse/pin/workspace/strict-option assertions -> pass
test ! -e pnpm-lock.yaml -> pass
secret/local-path scan -> pass
python3 tools/docs/generate.py --check -> verified 6 generated documents
python3 tools/docs/check.py -> documentation validation passed
git diff --check -> pass
```

Independent implementation review confirmed the exact registry pins exist and
support Node 24, Turbo dependency/task semantics are valid, shared profiles are
path-independent, the universal base exposes no DOM globals, and no lock,
install, build, secret, or local-path claim entered the cell.

## Idempotence, rollback, and recovery

Validation is rerunnable. If an available local tool conflicts with the canonical
declaration, preserve the exact output and keep dependent work non-ready. Rollback
is one local commit reverting only governed paths; no external state exists.

## Rollout and handoff

After independent review, the completed plan/commit becomes terminal dependency
`local:DW-M1-ROOT-TS-001`. The TS source/manifests cell may then incorporate the
baseline. A separate coordinator-owned lock-integration cell generates the first
lock with exact `corepack pnpm install --lockfile-only`, then runs frozen install
and a second lockfile-only no-drift check after package manifests exist. No
production rollout applies.

## Outcomes & Retrospective

Delivered the exact Node 24.18.0/pnpm 10.34.5 root declaration, pinned Turbo,
TypeScript, Oxfmt, and Oxlint development tools, the three canonical workspace
globs, a bounded Turbo task graph, and strict ES2022 base/library/contract
profiles. Independent review found and removed DOM libraries from the universal
base before acceptance. No lock or dependency installation was created, so the
later package-manifest, lock-integration, and executable-verification cells retain
their intended evidence boundaries.
