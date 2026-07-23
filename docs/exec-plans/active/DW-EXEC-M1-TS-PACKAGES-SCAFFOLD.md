---
exec_plan_id: DW-EXEC-M1-TS-PACKAGES-SCAFFOLD
title: Wave 1 TypeScript domain, SDK, and UI package scaffold
status: reviewed
superseded_by: null
owner: typescript-packages
reviewed_by: [ts-package-boundary-reviewer]
reviewed_at: 2026-07-23
primary_feature_id: DW-FND-001
supporting_feature_ids: [DW-FND-002, DW-FND-004, DW-FND-005]
issue: local:DW-M1-TS-SCAFFOLD
created: 2026-07-23
last_updated: 2026-07-23
base_commit: b1189ce7a1236fbc6b7751a0552159687e940521
last_verified_commit: b1189ce7a1236fbc6b7751a0552159687e940521
risk: medium
governed_paths: [packages/domain/**, packages/sdk/**, packages/ui/**, docs/exec-plans/active/DW-EXEC-M1-TS-PACKAGES-SCAFFOLD.md]
contract_gates: [SPIKE-HARNESS-ARCH-001]
decision_gates: [DEC-022, DEC-025, DEC-031, DEC-042]
gate_review_status: reviewed-with-gates
gate_reviewed_by: [ts-package-boundary-reviewer]
gate_reviewed_at: 2026-07-23
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, packages/ui/AGENTS.md, docs/PLANS.md, docs/exec-plans/active/DW-EXEC-M1-REPOSITORY-SCAFFOLD.md, docs/design-docs/architecture/application-architecture.md, docs/design-docs/engineering/conventions.md, docs/design-docs/decisions/index.md, docs/product-specs/foundations/dw-fnd-001-repository-oss-and-delivery-foundation.md, docs/product-specs/foundations/dw-fnd-002-design-system-shell-and-demo-mode.md, docs/product-specs/foundations/dw-fnd-004-sdk-stream-and-fixture-contracts.md, docs/product-specs/foundations/dw-fnd-005-domain-identity-status-and-audit-model.md]
scenario_ids: [AC-DW-FND-001-03, AC-DW-FND-002-06, AC-DW-FND-004-06, AC-DW-FND-005-01]
dispatch_kind: cell
dispatch_ready: true
agent_review_required: true
dependencies: [local:DW-M1-ROOT-TS-001]
blockers: []
---

# Wave 1 TypeScript domain, SDK, and UI package scaffold

## Purpose and observable result

Create independently reviewable package-local scaffolds for Deep Work's pure
TypeScript domain model, browser-safe SDK boundary, and accessible presentational
UI boundary. After the reviewed root declarations/workspace/shared-configuration
baseline is terminal, this cell authors package manifests, source, and tests and
retains static JSON and structure evidence. It does not generate a lock, install
dependencies, or claim executable build, test, pack, or clean-consumer success.

This plan authors the package surfaces and tests intended to contribute evidence
to `AC-DW-FND-001-03`, `AC-DW-FND-002-06`, `AC-DW-FND-004-06`, and the package-
level identity slice of `AC-DW-FND-005-01`. Those executable contributions remain
unverified until sequential downstream lock integration and package verification
complete; this cell claims only reviewed source and static evidence.

## Context and orientation

The exact reviewed base is
`b1189ce7a1236fbc6b7751a0552159687e940521`. That terminal root-dependency commit
records `local:DW-M1-ROOT-TS-001` completed after adding the reviewed Node/pnpm/
Turbo/TypeScript declarations, workspace metadata, and shared configuration. It
contains no shared lock. At this base, `packages/ui` contains design tokens, a
Tailwind preset, guidance, and a README; `packages/domain` and `packages/sdk` do
not yet exist. The first shared pnpm lock and frozen install belong to the later
coordinator cell `local:DW-M1-TS-LOCK-001`. Generated contracts, fixtures,
architecture tooling, `apps/web`, and product-demo composition are also outside
this cell.

The legal client direction is app to SDK/UI to domain. Domain is pure and
framework-neutral. SDK may depend on domain but not UI or React. UI may depend on
domain but never SDK, networking, routes, fixtures, generated DTOs, provider
payloads, environment access, or secret-bearing types.

## Scope

### In scope

- `packages/domain/**`: a strict ES2022 ESM package with explicit public exports
  for the smallest source-qualified identity, evidence-bearing capability/status,
  and safe view-state values needed by the Wave 1 fixture shell.
- `packages/sdk/**`: a browser-safe package boundary with explicit public exports,
  typed query/mutation and stream service ports, safe error categories, and
  DTO-to-domain mapping seams. Generated OpenAPI transport and live provider
  behavior remain absent until coordinator-owned contracts exist.
- `packages/ui/**`: preserve the existing token and Tailwind sources while adding
  the package boundary and the smallest semantic, accessible status/shell
  primitive that consumes domain values through props and callbacks only.
- Package-local manifests, TypeScript configuration, source, tests, public export
  maps, README guidance, and package-local no-network/clean-consumer checks as
  authored test cases, without executing dependency-backed tooling in this cell.
- Static JSON parsing, file inventory, import-structure inspection, scope checks,
  and whitespace validation that require no package install or shared lock.
- This living ExecPlan and no other documentation.

### Non-goals

- Root `package.json`, `pnpm-workspace.yaml`, `pnpm-lock.yaml`, Turbo/shared
  TypeScript/Oxfmt/Oxlint/Vitest configuration, Changesets, CI, or generated docs.
- `apps/web`, routes, Next.js composition, fixture ownership, Storybook hosting,
  product-demo integration, browser E2E, or migration from `deep-work-frontend`.
- OpenAPI generation, hand-written generated DTOs, real HTTP/stream transports,
  provider SDKs, source fan-out, credentials, authentication, persistence, or
  external contract claims.
- Editing architecture tools, product specifications, acceptance registries,
  umbrella/program plans, or any path outside the four governed entries.
- Installing dependencies, creating or updating any lock, executing package
  format/lint/typecheck/test/build/pack/consumer commands, publishing, pushing,
  merging, deploying, or using production/external credentials.

### Permissions and risk boundary

- Allowed paths are exactly the `governed_paths` entries in front matter.
- External systems and credentials: none. Unit tests must deny or fail on outbound
  network use; package code must not read environment secrets.
- Destructive, migration, release, deployment, publishing, signing, push, and
  merge operations are prohibited.
- Risk is medium because three public package boundaries and their dependency
  direction are established, but this cell owns no production state or external
  effect.
- Cross-review is required from architecture, TypeScript/developer-experience,
  accessibility for UI, and security for browser-safe/secret-free boundaries.
  The author cannot approve this plan or its implementation.

## Authoritative sources and prerequisites

- Product owner: `DW-FND-001`; supporting scope: `DW-FND-002`, `DW-FND-004`, and
  `DW-FND-005`.
- Architecture authority: root `ARCHITECTURE.md` and
  `docs/design-docs/architecture/application-architecture.md`.
- Engineering authority: `docs/design-docs/engineering/conventions.md`, root
  `AGENTS.md`, and `packages/ui/AGENTS.md`.
- `local:DW-M1-ROOT-TS-001` is an exact blocking coordinator prerequisite. It owns
  only the reviewed root declarations, workspace metadata, and shared
  configuration baseline; it does not own or supply a lock. It must land as a
  completed, independently reviewed terminal-success cell at this base or a
  reviewed successor before this plan can be promoted from draft or become
  dispatch-ready. Until then, this cell must not implement package sources,
  manufacture a lock, or silently substitute global tooling. After completion,
  cross-review verifies its terminal-success reference in `dependencies`.
- This cell hands its reviewed manifests, source, tests, and static evidence first
  to coordinator cell `local:DW-M1-TS-LOCK-001`. That cell creates the first shared
  lock with `corepack pnpm install --lockfile-only`, runs the frozen install, and
  reruns the same lockfile-only command to prove no drift. Only after that cell is
  terminal-success may sequential cell `local:DW-M1-TS-VERIFY-001` execute package
  validation and make reviewed package-local fixes. Neither downstream cell is a
  prerequisite or dependency of this authoring cell.
- `SPIKE-HARNESS-ARCH-001` remains open. Its deterministic fallback is package-
  local negative import tests plus explicit architecture review; this cell does
  not change the coordinator-owned architecture checker or claim the spike passed.
- `DEC-022`, `DEC-025`, `DEC-031`, and `DEC-042` require reviewer confirmation of
  the pure domain boundary, TypeScript method, enforceable import direction, and
  separation between ordinary query state and stream/domain state. Until review,
  this plan remains draft and non-dispatchable.

## Interfaces and invariants

### `packages/domain`

- Export opaque/source-qualified identifiers rather than unqualified provider IDs.
- Export evidence-bearing capability values with state, observation time,
  adapter/contract version, evidence class, and a safe reason where applicable.
- Export pure status/view-state types and guards needed by the initial UI/SDK
  boundary. No HTTP DTO, provider payload, React component, browser API, Node-only
  API, environment access, generated transport, or side effect is allowed.
- Public functions are deterministic and test source collision, unknown values,
  and safe serialization boundaries without containing credentials or raw content.

### `packages/sdk`

- Depend only on the domain package and deliberately package-local dependencies.
- Expose framework-neutral query/mutation and stream service interfaces as
  separate public contracts; no React hooks or cache implementation is introduced.
- Provide seams for later generated transport and mapping without inventing an API
  route, wire field, cursor, provider header, or live success response.
- Export safe error categories and capability-unavailable behavior. Any not-yet-
  generated transport is explicitly unavailable rather than represented by a
  plausible mock.

### `packages/ui`

- Preserve `tokens.css` and `tailwind.preset.mjs` as token sources.
- Depend on domain values through public exports and accept data/actions via typed
  props. Never import SDK/network/routes/fixtures/generated DTOs/provider types.
- The initial primitive uses native semantics, accurate accessible names, visible
  focus, non-color status, reduced-motion/high-contrast-safe styling, narrow
  reflow, and no unsafe raw HTML.
- Components own transient presentation state only. Capability and authorization
  decisions remain outside UI.

### Cross-package invariants

- Dependency direction is `sdk -> domain` and `ui -> domain`; no other internal
  edge is legal.
- Packages expose only named public entry points. Tests and consumers do not deep
  import `src/**` or unpublished implementation paths.
- Local ESM imports include explicit `.js` runtime extensions after compilation.
- No package contains real actors, repositories, endpoints, credentials, signed
  URLs, production content, generated transport, or copied prototype fixtures.

## Milestones

### Milestone 1 — Package contracts are explicit

- Create the domain, SDK, and UI package-local manifests/configuration and narrow
  export maps without changing the root workspace or shared lock.
- Document distribution/import names, supported entry points, and package-local
  commands reserved for the later executable-verification cell.
- Preserve current UI token exports and avoid introducing a second token source.

Acceptance:

- The diff is confined to governed paths and contains no root/shared/generated
  file.
- Public export maps contain no deep or provider-specific surface.
- Evidence: updated `Progress`, exact file inventory, and `git diff --check` result
  recorded in this plan.

### Milestone 2 — Domain and SDK source/test contracts are authored

- Implement the smallest source-qualified domain values and pure guards and author
  deterministic unit tests, including identical upstream IDs from two sources.
- Establish separate SDK query/mutation and stream ports, safe unavailable/error
  behavior, and compile-time/runtime import-boundary tests that require no network.
- Leave generated transport and all real endpoints absent.

Acceptance:

- Source and deterministic test cases cover the package-level identity-collision
  slice of `AC-DW-FND-005-01`; no test-pass or application/source integration
  completion is claimed in this cell.
- Source and tests encode unknown MDA capability as unavailable without a guessed
  request, as the intended later package-level contribution to `AC-DW-FND-004-06`.
- Negative import test cases are present for SDK-to-UI, domain-to-framework, and
  provider/network imports; their executable failure behavior is deferred.
- Evidence: exact source/test inventory and static import-structure review recorded
  in this plan; no fixture or unexecuted test is represented as live proof.

### Milestone 3 — UI primitive source/test contract is authored

- Add the minimal semantic status/shell primitive using domain values and existing
  tokens, plus behavior/accessibility tests for applicable unknown, unavailable,
  loading, error, and success states.
- Author tests for non-color meaning, unknown/unavailable capability presentation,
  accessible naming, long/localized content, and unsafe-content handling without
  adding an app route. Complete responsive layout/focus proof remains application-
  owned.

Acceptance:

- UI imports domain public exports and never imports SDK or networking.
- Source and test cases encode the `AC-DW-FND-002-06` expectation that an unknown
  capability never becomes an enabled-looking success state; this cell does not
  claim the tests passed.
- Evidence: exact UI source/test inventory, semantic source inspection, and static
  boundary review recorded in this plan. Executable accessibility and consumer
  results belong to `local:DW-M1-TS-VERIFY-001`.

### Milestone 4 — Static review and sequential integration handoff

- Run only the install-free static JSON, structure, scope, and whitespace checks
  defined below; do not invoke package scripts or infer executable success.
- Record exact changed files, static validation output, deviations, and reviewer
  findings, then hand the reviewed package manifests/source/tests to
  `local:DW-M1-TS-LOCK-001`.
- Record `local:DW-M1-TS-VERIFY-001` as the sequential consumer of the successful
  lock-integration result for executable package validation, clean-consumer proof,
  and any reviewed package-local fixes. Stop before either downstream cell, app,
  or generated-contract work.

Acceptance:

- Architecture, accessibility, security, and package review accepts the bounded
  diff or returns explicit rework.
- No root/shared file, generated artifact, sibling repository, or external system
  changed.
- No executable format, lint, typecheck, test, build, pack, accessibility, or
  consumer result is claimed by this cell.

## Progress

- [x] 2026-07-23 14:00 AEST — Draft plan created from the reviewed Wave 0.1 base;
  no implementation performed.
- [x] 2026-07-23 AEST — `local:DW-M1-ROOT-TS-001` is terminal at
  `b1189ce7a1236fbc6b7751a0552159687e940521`, with reviewed root declarations,
  workspace metadata, and shared-configuration evidence and no lock.
- [x] 2026-07-23 AEST — Independent cross-review accepted the bounded paths,
  architecture/SDK/UI/security/accessibility boundaries, open-gate fallback,
  scenario qualification, no-network/no-lock permissions, and exact sequential
  declarations -> package manifests/source/static review -> coordinator lock ->
  executable verification handoff. Dispatch metadata is complete.
- [x] 2026-07-23 AEST — Milestone 1 complete: package manifests, strict local
  compiler profiles, named public exports, and package guidance authored without
  changing the root workspace or creating a lock.
- [x] 2026-07-23 AEST — Milestone 2 complete: source-qualified domain values,
  evidence-bearing capabilities, separate SDK ports, unavailable seams, public-
  entry tests, boundary checks, and a network-denial test authored but not run.
- [x] 2026-07-23 AEST — Milestone 3 complete: token-preserving semantic status
  primitive, styles, and accessibility/unsafe-content tests authored but not run.
- [x] 2026-07-23 AEST — Milestone 4 author static review complete: every permitted
  JSON/inventory/import/scope/whitespace command exited zero. Independent review
  and downstream handoff acceptance remain pending.
- [x] 2026-07-23 AEST — Independent implementation review returned three bounded
  findings: `package-check` duplicated architecture checking instead of proving a
  packed consumer; forbidden-import coverage lacked intentional failing fixtures;
  and the component stylesheet introduced a parallel raw geometry scale.
- [x] 2026-07-23 AEST — Bounded rework authored distinct pack/offline-consumer
  scripts, stable rule-coded negative fixtures/tests, and canonical UI geometry
  tokens with intrinsic wrapping. The permitted static suite was rerun cleanly;
  every executable check remains unexecuted pending fresh independent re-review.
- [ ] Handoff accepted by `local:DW-M1-TS-LOCK-001`; after its terminal success,
  executable validation proceeds separately in `local:DW-M1-TS-VERIFY-001`.

## Surprises & Discoveries

- 2026-07-23 14:00 AEST — The reviewed base has no root TypeScript workspace or
  shared lock and only the existing UI token files. Consequence: the cell cannot
  claim executable install/build proof until coordinator-owned integration makes
  the frozen toolchain available; it must not create a package-local lock.
- 2026-07-23 15:00 AEST — Root sequencing review established that
  `local:DW-M1-ROOT-TS-001` intentionally supplies declarations/workspace/shared
  configuration without a lock. Consequence: this cell ends after source/static
  review, then hands sequentially to lock integration and executable verification.
- 2026-07-23 AEST — The current branch terminates at root completion commit
  `b1189ce7a1236fbc6b7751a0552159687e940521`; its parent implementation contains
  the exact Node 24.18.0, pnpm 10.34.5, Turbo 2.10.6, TypeScript 7.0.2, Oxfmt
  0.60.0, and Oxlint 1.75.0 declarations plus strict shared ES2022 profiles.
  Consequence: the dependency is satisfied without package manifests, install,
  generated files, or `pnpm-lock.yaml` being present.
- 2026-07-23 AEST — The draft import-inventory command contained a bracketed quote
  expression that the documentation checker interpreted as an internal Markdown
  link. Consequence: the review rewrote only that install-free search expression;
  it does not broaden the search, package scope, or execution permissions.
- 2026-07-23 AEST — The shared compiler base deliberately excludes DOM globals.
  Consequence: SDK and UI opt into `DOM` locally while domain retains `ES2022`
  only; tests and Vitest aliases remain package-local and unexecuted.
- 2026-07-23 AEST — Initial authoring left `tokens.css` and
  `tailwind.preset.mjs` byte-unchanged, but independent review found raw component
  geometry in `status-panel.css`. Consequence: the rework adds shared spacing,
  type, measure, touch-target, border, and focus tokens to the canonical sources;
  the component now consumes them and uses intrinsic flex wrapping without a raw
  viewport breakpoint.
- 2026-07-23 AEST — Initial `package-check` scripts aliased architecture checks,
  and green scans alone did not prove forbidden examples fail. Consequence: each
  package now owns separate unexecuted clean-archive/offline-consumer and
  rule-coded green-plus-negative-fixture checks.

## Decision Log

- 2026-07-23 14:00 AEST — Decision: use `DW-FND-001` as the single primary owner
  and treat `DW-FND-002/004/005` as supporting boundaries. Rationale: this is a
  repository/package scaffold, not a complete UI, transport, or domain feature.
  Consequence: scenario evidence is explicitly partial where broader product
  integration remains outside the cell. Approved by:
  `ts-package-boundary-reviewer`.
- 2026-07-23 14:00 AEST — Decision: do not create generated transport, fixtures,
  root manifests, shared configuration, or locks in this lane. Rationale: those
  are coordinator-owned shared integration paths. Consequence: final executable
  package proof waits for coordinator integration. Approved by:
  `ts-package-boundary-reviewer`.
- 2026-07-23 15:00 AEST — Decision: split package authoring, lock integration, and
  executable verification into sequential cells. Rationale: the first lock cannot
  be resolved until package manifests exist, while this governed lane cannot own
  the shared lock. Consequence: `local:DW-M1-TS-LOCK-001` performs first-lock/
  frozen/no-drift integration and `local:DW-M1-TS-VERIFY-001` performs executable
  validation and package-local fixes. Approved by:
  `ts-package-boundary-reviewer`.
- 2026-07-23 AEST — Decision: accept this cell for dispatch with
  `SPIKE-HARNESS-ARCH-001` still open. Rationale: the cell authors package-local
  negative import tests and receives explicit architecture review but neither
  edits nor claims the coordinator-owned executable architecture checker.
  Consequence: only source/static evidence may be recorded here; enforcement and
  executable test claims remain downstream. Approved by:
  `ts-package-boundary-reviewer`.

## Detailed implementation approach

1. Inventory the existing UI token exports and reserve deliberate package names and
   public entry points for domain, SDK, and UI.
2. Add the pure domain package first, including identity/capability/status values
   and unit tests; do not import SDK or framework code.
3. Add the SDK port/mapping skeleton against domain public exports. Keep generated
   and live transport absent, and encode unavailable behavior explicitly in source
   and tests for later execution.
4. Add the UI package boundary and one accessible primitive against domain public
   exports while preserving token sources and prohibiting SDK/network imports.
5. Run only static JSON/structure/scope checks, update living sections, and hand
   the exact reviewed manifests/source/tests diff to `local:DW-M1-TS-LOCK-001`.
   Do not execute package tooling; `local:DW-M1-TS-VERIFY-001` owns that work after
   successful lock integration.

## Validation and proof

Run from repository root after `local:DW-M1-ROOT-TS-001` supplies the reviewed root
declarations/workspace/shared-configuration baseline. These are the only checks
this cell may execute; they require no dependency install or shared lock:

```text
python3 -m json.tool packages/domain/package.json >/dev/null
python3 -m json.tool packages/sdk/package.json >/dev/null
python3 -m json.tool packages/ui/package.json >/dev/null
python3 -m json.tool packages/domain/tsconfig.json >/dev/null
python3 -m json.tool packages/sdk/tsconfig.json >/dev/null
python3 -m json.tool packages/ui/tsconfig.json >/dev/null
rg --files packages/domain packages/sdk packages/ui | sort
rg -n '"exports"|"type"|"scripts"|"dependencies"' packages/domain/package.json packages/sdk/package.json packages/ui/package.json
rg -n -e '@deepwork/(domain|sdk|ui)' -e 'from .*\b(react|next|node:)' packages/domain packages/sdk packages/ui
git diff --check
git status --short
```

Required retained evidence in this plan:

- command, exit code, and concise sanitized output for every static check;
- exact package manifest, source, and test inventory;
- static import findings for domain, SDK, and UI directions;
- source-level UI semantics/accessibility review notes for the initial primitive;
- source/test inspection showing network denial is authored but not yet executed;
- exact changed-file inventory showing only governed paths; and
- explicit deferral of all executable package proof to the two downstream cells.

The implementation may not invoke `pnpm`, weaken checks, fetch an unreviewed tool
globally, add a package-local lock, or treat authored/unexecuted tests as passing
evidence.

`local:DW-M1-TS-LOCK-001` subsequently owns this exact integration sequence:

```text
corepack pnpm install --lockfile-only
lock_snapshot="$(mktemp)"
cp pnpm-lock.yaml "$lock_snapshot"
corepack pnpm install --frozen-lockfile
corepack pnpm install --lockfile-only
cmp "$lock_snapshot" pnpm-lock.yaml
rm "$lock_snapshot"
```

The lock cell records the `cmp` exit code and removes only the exact temporary file
returned by `mktemp`. This compares the newly created lock directly and does not
mistake an untracked first lock for a clean `git diff`.

Only after that cell is terminal-success does `local:DW-M1-TS-VERIFY-001` run the
package-scoped format, lint, typecheck, test, build, pack, clean-consumer, network-
denial, and accessibility checks and make any reviewed fixes within package paths.

Independent planning review evidence on 2026-07-23 AEST:

```text
git rev-parse HEAD -> b1189ce7a1236fbc6b7751a0552159687e940521
root JSON declarations/shared compiler profiles parse -> pass
terminal root plan is completed and reviewed -> pass
test ! -e pnpm-lock.yaml -> pass
package inventory at base -> only packages/ui tokens/guidance; no domain or SDK
python3 tools/docs/generate.py --check -> verified 6 generated documents
python3 tools/docs/check.py -> one expected coordinator-owned unindexed-plan error
git diff --check -> pass
```

The reviewer confirmed that this cell may author declarations, manifests, source,
and tests and retain static evidence only. It may not invoke pnpm, install, create
a lock, execute authored tests, or claim build/pack/consumer/accessibility success.
The coordinator lock cell and subsequent executable-verification cell remain
strictly sequential and independently reviewed.

Author implementation evidence on 2026-07-23 AEST:

```text
python3 -m json.tool packages/domain/package.json >/dev/null -> exit 0
python3 -m json.tool packages/sdk/package.json >/dev/null -> exit 0
python3 -m json.tool packages/ui/package.json >/dev/null -> exit 0
python3 -m json.tool packages/domain/tsconfig.json >/dev/null -> exit 0
python3 -m json.tool packages/sdk/tsconfig.json >/dev/null -> exit 0
python3 -m json.tool packages/ui/tsconfig.json >/dev/null -> exit 0
rg --files packages/domain packages/sdk packages/ui | sort -> exit 0; inventory below
rg manifest exports/type/scripts/dependencies -> exit 0; all three packages are ESM
  with scripts and exports; SDK/UI declare only the domain internal dependency
rg package/framework imports -> exit 0; findings summarized below
git diff --check -> exit 0; no output
git status --short -> exit 0; only governed package paths changed before this
  living-plan update
```

Exact package inventory:

```text
packages/domain/AGENTS.md
packages/domain/README.md
packages/domain/package.json
packages/domain/scripts/check-boundaries.mjs
packages/domain/scripts/package-check.mjs
packages/domain/src/capability.ts
packages/domain/src/identity.ts
packages/domain/src/index.ts
packages/domain/src/view-state.ts
packages/domain/tests/boundaries.test.mjs
packages/domain/tests/capability.test.ts
packages/domain/tests/fixtures/negative/browser-network.fixture.ts
packages/domain/tests/fixtures/negative/framework-side-effect.fixture.ts
packages/domain/tests/fixtures/negative/provider-network-side-effect.fixture.ts
packages/domain/tests/identity.test.ts
packages/domain/tests/view-state.test.ts
packages/domain/tsconfig.json
packages/domain/tsconfig.test.json
packages/domain/vitest.config.ts
packages/sdk/AGENTS.md
packages/sdk/README.md
packages/sdk/package.json
packages/sdk/scripts/check-boundaries.mjs
packages/sdk/scripts/package-check.mjs
packages/sdk/src/index.ts
packages/sdk/src/mapping.ts
packages/sdk/src/ports.ts
packages/sdk/src/result.ts
packages/sdk/src/unavailable.ts
packages/sdk/tests/boundaries.test.mjs
packages/sdk/tests/fixtures/negative/provider-side-effect.fixture.ts
packages/sdk/tests/fixtures/negative/raw-network.fixture.ts
packages/sdk/tests/fixtures/negative/ui-side-effect.fixture.ts
packages/sdk/tests/public-api.test.ts
packages/sdk/tests/unavailable.test.ts
packages/sdk/tsconfig.json
packages/sdk/tsconfig.test.json
packages/sdk/vitest.config.ts
packages/ui/AGENTS.md
packages/ui/README.md
packages/ui/package.json
packages/ui/scripts/check-boundaries.mjs
packages/ui/scripts/package-check.mjs
packages/ui/src/index.ts
packages/ui/src/status-panel.tsx
packages/ui/status-panel.css
packages/ui/tailwind.preset.mjs
packages/ui/tests/boundaries.test.mjs
packages/ui/tests/fixtures/negative/provider-side-effect.fixture.ts
packages/ui/tests/fixtures/negative/raw-network.fixture.ts
packages/ui/tests/fixtures/negative/sdk-side-effect.fixture.ts
packages/ui/tests/status-panel.test.tsx
packages/ui/tokens.css
packages/ui/tsconfig.json
packages/ui/tsconfig.test.json
packages/ui/vitest.config.ts
```

Static import findings:

- Domain shipped source imports only explicit local `.js` modules. Node imports
  occur only in package-local checks, the negative-test harness, and Vitest alias
  config. Intentional excluded fixtures cover React, browser/raw-network, Axios,
  and LangGraph SDK failures with stable rule codes.
- SDK shipped source imports `@deepwork/domain` and explicit local `.js` modules;
  it has no UI, React, Next.js, Node, provider, or network import. Its Node imports
  are confined to package-local checks, the negative-test harness, and Vitest
  config. Intentional excluded fixtures cover UI, LangGraph SDK, Axios, fetch,
  and EventSource failures with stable rule codes.
- UI shipped source imports `@deepwork/domain`, React, and an explicit local `.js`
  module. It has no SDK, Next.js, provider, route, generated, environment, network,
  or runtime CSS-loader import. Node imports are confined to package-local checks,
  the negative-test harness, and Vitest config. Intentional excluded fixtures
  cover SDK, LangGraph SDK, Axios, fetch, and WebSocket failures.
- Tests import named package entry points rather than implementation paths.

Source-level UI review:

- `StatusPanel` uses a labelled native `section`, native heading and button,
  polite loading status, assertive error role, explicit visible state text, and a
  non-color mark. Unknown/unavailable variants cannot accept an action.
- Styles use canonical token variables for product geometry, `:focus-visible`,
  forced-colors support, no animation, overflow wrapping, and intrinsic flex-wrap
  reflow without a raw viewport breakpoint.
- Display inputs are strings rendered as React text; no raw-HTML API exists. The
  authored test covers markup-shaped input and long localized content.

Network denial is authored, not executed: `packages/sdk/tests/unavailable.test.ts`
replaces `globalThis.fetch` with a throwing spy and asserts that an unknown
capability returns `capability-unavailable` without calling it. Package structural
scripts also reject network primitives from shipped source. Neither the test nor
those Node scripts ran in this cell.

Changed-file scope is exactly the three package inventories above plus this
living plan. Rework deliberately updates the canonical UI token and Tailwind
preset sources to absorb component geometry; no second token source was created.
No root/shared/index/generated/app path, lock, external system, or credential
changed.

Distinct `package-check` scripts are authored, not executed. Each packs built
output, inspects non-empty public files and export targets, rejects private-source,
lock, and `workspace:` leakage, installs only packed local archives into an empty
temporary consumer with pnpm offline mode, and imports the public JavaScript
entry. SDK/UI include the packed domain archive; UI additionally verifies the
token, status CSS, and Tailwind preset entries and uses the pinned React already
expected in the offline store. Temporary paths come from `mkdtemp` and only that
exact directory is removed in `finally`.

Author rework static evidence on 2026-07-23 AEST:

```text
six permitted package-manifest/main-tsconfig JSON parses -> exit 0; no output
rg --files packages/domain packages/sdk packages/ui | sort -> exit 0; exact
  inventory above, including 3 clean-package scripts, 3 negative-test harnesses,
  and 9 intentional negative fixtures
rg manifest exports/type/scripts/dependencies -> exit 0; all packages retain ESM,
  named exports, and distinct script declarations
rg package/framework imports -> exit 0; shipped edges remain sdk -> domain and
  ui -> domain + React; reported sdk/ui cross-imports are intentional fixtures or
  rule/check text, not shipped source
git diff --check -> exit 0; no output
git status --short -> exit 0; only the three governed packages and this living
  plan changed
```

No `check-architecture`, `package-check`, Vitest, formatter, linter, compiler,
build, pack, pnpm, install, lock, consumer, accessibility, or network command was
executed during rework.

Executable format, lint, typecheck, unit, build, pack, package structural,
network-denial, accessibility, and clean-consumer proof remains explicitly
deferred. `local:DW-M1-TS-LOCK-001` first owns dependency resolution, first-lock,
frozen-install, and lock-no-drift proof; only after its terminal success does
`local:DW-M1-TS-VERIFY-001` own those executable package checks and reviewed
package-local fixes.

## Idempotence, rollback, and recovery

Package scaffolding is additive and owns no production state. Static checks must
be safe to rerun without an install or lock. An invalid manifest or structure
check preserves source and diagnostics; recovery changes only files within the
governed package. Do not delete existing UI tokens, rewrite unrelated history,
regenerate shared artifacts, or edit root configuration to make a local check
pass.

Before downstream integration, rollback is deletion/reversion of only the reviewed
lane diff. Later lock or verification recovery belongs to those sequential cells
and must preserve other accepted lanes. Publishing is out of scope, so there is no
registry rollback or version overwrite.

## Rollout and handoff

There is no production rollout. The lane hands its reviewed commit, exact diff,
static evidence, known limitations, and package manifests/source/tests to
`local:DW-M1-TS-LOCK-001`. That coordinator cell alone creates the first shared
lock using lockfile-only, proves the frozen install, and proves lockfile-only
no-drift. Its terminal result then hands sequentially to
`local:DW-M1-TS-VERIFY-001` for executable package checks and package-local fixes.
Other shared configuration, architecture tooling, generated output, `apps/web`,
and product-demo composition remain coordinator owned.

Cross-review must change this plan from `draft` to `reviewed`, complete reviewer
and gate-review metadata, confirm blockers/dependencies, and deliberately set
`dispatch_ready: true` before implementation. Any scope expansion returns the plan
to draft review.

## Outcomes & Retrospective

Authored and reworked the bounded package surfaces from the reviewed base:
source-qualified domain identities, safe capability summaries and state guards;
distinct browser-safe SDK query/mutation/stream ports and explicit unavailable
factories; and one semantic React status primitive consuming the domain public
surface and canonical token sources. Package-local public-entry, collision,
unknown-capability, network-denial, unsafe-content, and accessibility-oriented
tests are present. Architecture checks retain green-source scans and prove
intentional forbidden side-effect imports/raw APIs produce stable rule codes.
Package checks are separate clean-archive/offline-consumer harnesses rather than
aliases for architecture checking.

The author ran only the permitted install-free JSON, inventory, import, scope,
and whitespace checks, all with exit zero. No package executable, dependency
install, lock operation, test, build, pack, clean consumer, accessibility runner,
or network request ran, so none is claimed as passing. There were no scope
deviations. The initial independent findings were addressed, but fresh independent
implementation review is still required. `SPIKE-HARNESS-ARCH-001` remains open,
and sequential proof remains with
`local:DW-M1-TS-LOCK-001` followed by `local:DW-M1-TS-VERIFY-001`.
