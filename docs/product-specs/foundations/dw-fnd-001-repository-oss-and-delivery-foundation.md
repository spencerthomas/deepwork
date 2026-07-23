---
feature_id: DW-FND-001
title: Repository, OSS, and delivery foundation
release: v1
status: canonical-spec
decision_status: accepted-with-open-gates
implementation_readiness: not-ready
owners: [platform, developer-experience]
surfaces: [repository, ci, previews, releases]
runtime_scopes: [any]
source_refs: [SRC-DW, SRC-DP, SRC-DA, SRC-LCPY, SRC-LCJS, SRC-LG, SRC-HE, SRC-EXEC, SRC-SYM, SRC-FASTAPI, SRC-NEXT, SRC-RUST]
evidence_pins:
  canonical_plan: 06f0515
  frontend: 26c698b
  deepagents: 7794b61
  langchain_python: 592055e
  langchainjs: ee76ea0
  langgraph: 31f90df
dependencies: []
contract_gates: [SPIKE-HARNESS-DOCS-001, SPIKE-HARNESS-ARCH-001, SPIKE-WORKTREE-001, SPIKE-DEV-OBS-001, SPIKE-DOC-GARDEN-001, SPIKE-SYMPHONY-001]
last_reviewed: 2026-07-23
---

# Repository, OSS, and delivery foundation

## User outcome

A contributor can clone one canonical monorepo, run a representative Deep Work experience without credentials, change one bounded package, and receive reproducible local and CI feedback. A maintainer can produce an attributable, reversible release without inheriting build bypasses or generated-prototype debt.

This is a proposed foundation prepared for review. It is not implementation-ready until the repository structure, supported toolchain versions, license, contribution model, and release policy are accepted in review.

## Evidence and confidence

| Evidence | Classification | Confidence | Planning consequence |
|---|---|---:|---|
| The canonical repository at `06f0515` contains plans and UI tokens, not a production application scaffold. | Direct repository evidence | High | Create the runtime scaffold in the canonical repository only after this proposal is approved. |
| The sibling frontend at `8866d39` demonstrates routes, shell patterns, and visual intent but contains generated-prototype conventions and build debt. | Direct repository evidence | High | Treat it as a one-way interaction source; do not copy its lockfile, bypasses, `.DS_Store` files, or ownership model. |
| The selected product stack is Python 3.12/FastAPI/Postgres, a separate Python agent package, Next.js 16, Tauri v2, and TypeScript SDK/UI packages. | Proposed architecture decision | Medium until review | Structure both Python and TypeScript workspaces without making either ecosystem own the other. |
| Fixture/live parity and a no-credential contributor path are release requirements. | Product-plan requirement | High | CI and package boundaries must support deterministic fixture mode from the first scaffold change. |
| Classic LangSmith Deployment is the public baseline; MDA and Fleet are capability-gated. | Audited external-contract posture | High for baseline; low for gated tiers | Repository structure may contain adapters, but cannot make private-beta contracts a build prerequisite. |
| The pinned Deep Agents and LangChain Python repositories use independently versioned package-local Python environments, `uv`, package `Makefile` commands, Ruff, typed public APIs, and isolated test classes. | Direct source evidence at `SRC-DA`/`SRC-LCPY` | High for contributor method | Give API and agent separate manifests, locks, commands, and releases; use the closest reference type checker for each package. |
| The pinned LangChain.js repository uses pnpm/Turbo, strict ES2022 ESM, Oxfmt/Oxlint, explicit exports, standard adapter tests, clean consumers, and Changesets. | Direct source evidence at `SRC-LCJS` | High for TypeScript package practice | Match its modularity and release hygiene without copying legacy compatibility settings a greenfield product does not need. |

No live external runtime contract is introduced by this plan. Runtime verification remains owned by `SPIKE-STREAM-001`, `SPIKE-AUTH-001`, `SPIKE-MDA-001`, and `SPIKE-FLEET-001` in their feature plans.

## Scope, ownership, and non-goals

### In scope

- One canonical monorepo with pinned pnpm/Turborepo tasks for TypeScript and root `make` fan-out over independently locked Python packages.
- Harness-oriented repository knowledge: short root/nested `AGENTS.md`, root `ARCHITECTURE.md`, reviewed `WORKFLOW.md`, canonical topical/design/product/ExecPlan/reference/generated docs, evidence-backed quality score, and owned debt tracker.
- A machine-readable package/layer/domain/environment graph, structural tests, generated architecture/package views, actionable diagnostics, and an owned expiring exception lifecycle.
- Python 3.12 FastAPI application service in `apps/api` and isolated Python Deep Agents package in `packages/agent`, each with its own `pyproject.toml`, `uv.lock`, `Makefile`, tests, and release identity.
- Next.js 16/React 19 web/PWA in `apps/web`, Tauri v2 host in `apps/desktop`, and TypeScript `packages/domain`, `packages/sdk`, and `packages/ui` plus language-neutral `internal/fixtures` and TypeScript `internal/adapter-tests`; Python source conformance stays with `apps/api`.
- Two explicit fixture levels: a browser-local UI harness and an API-backed product demo with per-worktree API/worker/Postgres/object/telemetry isolation.
- Pinned manifests and lockfiles, deterministic bootstrap, developer commands, dependency-boundary checks, and targeted workspace tasks.
- Oxfmt/Oxlint for TypeScript; Ruff plus `ty` for the Deep Agents-facing agent package; Ruff plus strict `mypy` with the Pydantic plugin for the FastAPI package; pytest for Python.
- CI jobs for format, lint, typecheck, unit, contract, integration, build, fixture smoke, dependency/license review, and secret scanning.
- Vercel Git previews for web fixture builds without a duplicate deployment workflow.
- Changesets for publishable TypeScript contracts and an explicit release/version policy for Python artifacts.
- MIT licensing proposal, trademark guidance, security policy, contribution guide, issue forms, pull-request template, support boundary, and code of conduct.
- Reproducible provenance, changelog, artifact checksums, and rollback metadata for releases.
- A pinned, security-reviewed Symphony pilot whose eligible issues link one product spec and one living ExecPlan, form an acyclic blocker graph, and pass a distinct Agent Review before Human Review.

### Ownership

- Platform owns workspace manifests, CI, release automation, signing interfaces, and shared developer commands.
- Developer Experience owns bootstrap documentation, contributor diagnostics, templates, and local feedback quality.
- Package owners own package-specific tests and public-contract changes; they cannot relax repository-wide gates locally.
- Security reviews action pinning, secret handling, supply-chain controls, artifact provenance, and disclosure policy.
- Product approves which capabilities fixture mode must represent before migration begins.
- Maintainers keep package scopes, `AGENTS.md`, good-first-issue labels, standard-test harnesses, and the no-credential contributor path understandable to contributors who know LangChain but not Deep Work.
- Documentation owners maintain indexes, governed-path freshness, generated views, living-plan state, and the quality score; architecture owners maintain the graph, diagnostics, and exceptions.
- The orchestration owner maintains the pinned Symphony revision, tracker adapter, host credential policy, workspace/retry/reconciliation behavior, emergency disable, and `WORKFLOW.md`. Agents cannot self-grant `agent-ready` or merge authority.

### Non-goals

- Production cloud topology, database hosting, runtime credentials, or deployment-provider selection.
- Implementing application features, upstream LangChain packages, a documentation site, native mobile, or public launch marketing.
- Reimplementing `mda deploy`, public Fleet CRUD, global thread search, or unsupported `/v1/deepagents/*` routes.
- Copying the sibling prototype wholesale or allowing canonical packages to import from it.
- CLA/governance automation before the maintainer model is accepted.

## Proposed interfaces

```text
apps/
  api/          Python 3.12 FastAPI application service; /api/v1 and OpenAPI
  web/          Next.js 16 / React 19 responsive web and qualified PWA cells
  desktop/      Tauri v2 host over the same web/API contracts
packages/
  domain/       Framework-neutral TypeScript identities, normalized schemas, errors, capabilities, and reducers
  agent/        Isolated Python deepagents runtime project
  sdk/          Browser-safe TypeScript client for the Deep Work API and application stream
  ui/           Presentation components and design tokens
internal/
  fixtures/     Private schema-valid JSON/TypeScript fixture corpus
  adapter-tests/ TypeScript application-client, DTO, and reducer conformance suites
  tsconfig/     Strict shared TypeScript configuration
tools/
  architecture/ Machine-readable graph and structural checks
  docs/         Index, metadata, link, living-plan, freshness, and generated checks
  worktree/     Collision-free demo resources and proof paths
docs/
  design-docs/  Durable rationale and decisions
  product-specs/ Stable-ID product outcomes and contracts
  exec-plans/   Active/completed living implementation plans and debt
  generated/    Reproducible schema/API/package/architecture/coverage/issue views
  references/   Pinned external and legacy evidence
```

Proposed dependency direction:

- `packages/domain` imports no SDK, UI, React, Next.js, Tauri, provider client, environment, or credential code.
- `packages/sdk` and `packages/ui` may consume `packages/domain`; neither may depend on the other.
- `apps/web` may consume domain, SDK, and UI. `apps/desktop` hosts the exact trusted web origin and consumes only explicit native bridge contracts; there is no separate v1 mobile app package.
- `packages/ui` cannot import `packages/sdk`, runtime clients, React application routes, fixtures, or provider payloads.
- `packages/sdk` cannot import `packages/ui`, provider SDKs, Next.js/Tauri modules, or server credential types.
- `apps/api` may consume shared Python application modules but not presentation code.
- `packages/agent` may consume pinned LangChain/deepagents packages but cannot import FastAPI application persistence or Deep Work credential tables.
- The generated OpenAPI artifact is the reviewable seam between FastAPI `/api/v1` and the TypeScript SDK; generated code cannot silently change public semantics.
- `apps/api` owns provider capability detection, secret-bearing source adapters, upstream streaming, and per-source aggregation. Public source views expose credential health, never server `authRef` values.
- Fixture adapters and the private fixture corpus implement the same normalized contract as live adapters and cannot depend on a live source.

Boundary tests enforce these rules. The repository contains no browser-callable raw credential, credential reference, generic upstream-proxy contract, or default direct browser-to-deployment path. `SPIKE-DIRECT-STREAM-001` gates any future exception.

## Primary journeys

### Contributor: first useful change

1. Clone the canonical repository on a supported platform.
2. Run the documented prerequisite check and one bootstrap command.
3. Start either the browser-local UI harness without services or the API-backed product demo without external credentials. The product demo uses isolated local fixture Postgres/object/worker/telemetry services.
4. Change one component or normalized fixture and run the affected checks.
5. Open a pull request; CI selects the affected packages plus repository-wide policy checks.
6. Review the Vercel fixture preview and merge only after required ownership and checks pass.

### Agent: Symphony-dispatched bounded change

1. A maintainer accepts the product spec/decisions, reviews a self-contained active ExecPlan, clears blockers, and applies `agent-ready` to a low-risk issue.
2. Symphony reconciles eligibility and creates the deterministic isolated workspace without passing its tracker credential to the child process.
3. The agent reads root/scoped guidance, architecture, product spec, ExecPlan, and workflow; it starts the worktree-qualified demo/telemetry stack where the issue touches the application.
4. The agent keeps plan progress/discoveries/decisions current, runs package plus architecture/docs/contract/demo checks, and attaches the required proof packet.
5. The issue moves to Agent Review and then Human Review. It does not self-approve, waive gates, or merge risky work.
6. Crash, restart, retry, state change, cancellation, terminal cleanup, and follow-up work preserve tracker/PR evidence and never duplicate an external effect.

### API or agent contributor

1. Start a disposable local Postgres for application-service tests or run isolated Python unit tests without it.
2. Change either FastAPI `/api/v1` behavior or the separate agent package.
3. Regenerate and review OpenAPI/SDK changes only when the API contract changes.
4. Run captured contract tests; live external tests remain opt-in and secret-scoped.
5. Confirm the package boundary prevents agent runtime code from reading application-service credentials.

### Maintainer release and rollback

1. Review changesets, Python version metadata, migrations, dependency deltas, license report, and unresolved security findings.
2. Build signed/checksummed artifacts from a pinned commit in protected CI.
3. publish only approved artifacts and record provenance and minimum compatible versions.
4. Verify fixture smoke, API migration compatibility, and Tauri/web channel health.
5. Roll back the application or package revision independently using recorded artifacts; never rewrite published history.

## Complete state matrix

| State | Required behavior | Recovery or guardrail |
|---|---|---|
| Fresh clone | Prerequisite check states supported Node, pnpm, Python, uv, Rust/Tauri-optional versions. | Exact install guidance; desktop prerequisites do not block web/API work. |
| Bootstrap loading | Show phase and package currently resolving without leaking environment values. | Interrupt safely; rerun idempotently. |
| No credentials / empty environment | Fixture web build, unit tests, and static checks succeed. | Live and signing jobs are explicitly skipped, not reported as passed. |
| Missing required tool | Fail before modifying lockfiles and name the exact missing or incompatible version. | Install/upgrade and rerun. |
| Dependency resolution error | Preserve prior lockfiles and display the responsible ecosystem/package. | Retry from documented cache-clean boundary; no blanket lockfile recreation. |
| Offline with warm dependency cache | Permit tasks whose inputs are present; report skipped network checks honestly. | Reconnect for installs, vulnerability feeds, preview, or publication. |
| Offline with cold cache | Stop with an actionable network requirement. | No partially successful bootstrap claim. |
| Permission denied | Read-only contributors can run checks; protected publish/sign/migration operations remain unavailable. | Explain the repository/environment permission needed. |
| CI queued or loading | Show job ownership, affected packages, and commit. | Cancelled/superseded builds do not publish artifacts. |
| CI partial failure | Isolate job, package, platform, and reproduction command. | Healthy jobs remain evidence; release stays blocked. |
| Preview unavailable | Required CI remains independent; preview failure is visible on the pull request. | Retry Vercel preview without bypassing build gates. |
| Stale generated SDK/OpenAPI | Contract check fails with the exact generated diff. | Regenerate using pinned tools and review semantic changes. |
| Fixture/live contract drift | Parity suite fails before merge. | Update normalized contract and both adapters deliberately. |
| Reconnect after interrupted task | Workspace commands resume/restart deterministically; they do not claim an external run resumed. | External stream semantics defer to `SPIKE-STREAM-001`. |
| Mobile contributor | Fixture preview is reviewable from phone; full local toolchain is not promised on mobile. | Link to CI artifacts and desktop setup. |
| Release candidate | All required artifacts, migrations, provenance, notes, and compatibility checks are present. | Missing evidence blocks publication. |
| Publish partially fails | Record which immutable artifacts exist; never overwrite them. | Retry only missing artifacts or issue a new patch version. |
| Rollback | Previous compatible artifact and migration strategy are available. | Preserve audit trail and user data; escalate irreversible migration. |
| Documentation drift | Docs check identifies owner, governed path, last verified commit, and stale/generated/index problem. | Repair the source or document; never hand-edit generated output or lower the quality score silently. |
| Illegal architecture edge | Structural check names importing file, violated edge, legal boundary, architecture anchor, and local command. | Move code to the owning layer or record a reviewed expiring exception; secret/tenant edges cannot be waived. |
| Second demo worktree | Allocate distinct ports, database/schema, object prefix, browser origin/storage, telemetry, and proof path. | If isolation is not proven, permit only one active full-product demo and parallelize package/docs work. |
| Symphony issue blocked/ineligible | No new workspace/session starts; an active attempt stops at the configured reconciliation boundary. | Record the concrete blocker and resume only after an authorized state change. |
| Symphony process restart | Reconcile tracker and preserved workspace; do not recreate an existing PR or external effect. | Fall back to manual single-agent dispatch with the same issue and ExecPlan. |

## Runtime capability and fallback

- Classic LangSmith Deployment remains the supported public runtime baseline, but fixture mode is the default contributor experience.
- MDA and Fleet adapters compile behind capability manifests and do not require private packages, endpoints, or credentials for bootstrap or CI.
- A source capability that has not passed its named spike is false in fixtures unless a fixture explicitly demonstrates the unavailable state.
- Live contract jobs are opt-in, pinned, and scoped by source. A missing live credential skips that external matrix cell with a visible reason; it does not weaken captured contract tests.
- If Tauri prerequisites or `SPIKE-DESKTOP-001` fail, web/PWA and API work continue and desktop packaging remains disabled.
- Native mobile is not part of the v1 repository acceptance path; mobile v1 is
  responsive Next.js, with install/PWA/push enabled only on qualified cells.

## Persistence and security

- Repository history stores no `.env*`, credentials, database dumps, provider payloads, signing keys, notarization secrets, or real trace/repository fixtures.
- Fixtures use synthetic IDs, actors, repositories, links, tool content, and timestamps; a fixture scrub check rejects known secret patterns and external production hosts.
- CI actions are commit-SHA pinned; third-party actions and dependencies receive license and provenance review.
- Protected environments isolate publishing, migrations, production previews, Tauri signing, and package registries with least-privilege short-lived credentials.
- Build outputs and caches are untrusted inputs across pull requests; privileged jobs never restore untrusted executable caches.
- Branch protection requires ownership review for workflows, lockfiles, release configuration, API schema, migrations, and security policy.
- Release metadata records source commit, toolchain, checksums, SBOM/provenance where supported, migrations, and rollback compatibility.
- No `ignoreBuildErrors`, blanket type suppression, unbounded `any`, silent formatter rewrites, or vendored upstream LangChain code.

## Responsive and accessible behavior

- The fixture preview must exercise the same responsive shell at 320 CSS pixels through desktop widths; repository acceptance cannot rely only on a desktop screenshot.
- CI/preview summaries use text labels in addition to color and expose stable links and plain-language recovery.
- Bootstrap and validation commands produce readable progress in screen readers and terminals without animation-only state, line-overwriting as the sole output, or color-only failures.
- Documentation headings, code blocks, tables, and link text are navigable; commands include non-mouse alternatives.
- Reduced-motion, high-contrast, keyboard-only, 200% zoom, and touch review are part of fixture smoke evidence through `DW-QUAL-001`.

## Metrics and guardrails

- Fresh-clone fixture preview: under 10 minutes on the documented reference machine after dependencies download.
- No-credential fixture start and build success rate: 100% on supported CI platforms.
- CI green rate for changes passing documented local checks: target above 95%, segmented by flaky/infrastructure/product failure.
- Median failed-check time-to-first-actionable diagnostic: under 2 minutes.
- Fixture/live normalized-contract parity: 100% for declared capabilities.
- Canonical imports from `deep-work-frontend`: zero after each migrated surface lands.
- Secrets committed or emitted by fixture/CI logs: zero.
- Guardrails: no release from a dirty/unpinned source, no skipped required job, no private-beta dependency in default install, and no destructive migration without a tested rollback or explicit irreversible approval.
- Canonical document index/ID/generated drift: zero; active ExecPlans with all living sections: 100%.
- Architecture graph violations and unrecorded exceptions: zero; expired exceptions: zero.
- Concurrent product-demo worktree collision rate: zero after the isolation spike.
- Symphony dispatch of blocked, unlabelled, or non-agent-ready work: zero; duplicate PR/external effect after retry/restart: zero.

## Dependencies, contract gates, rollout, and rollback

### Dependencies and review gates

- Product approval of package ownership, source precedence, OSS license, support boundary, and one-way prototype migration.
- Security approval of CI trust boundaries, secret scopes, dependency policy, publishing identities, and disclosure process.
- Maintainer approval of Node/Python/Rust support windows and generated OpenAPI review policy.
- Acceptance of the Harness document authority model, machine-readable architecture rules, two fixture modes, ExecPlan template, worktree isolation, and quality-score rubric.
- `SPIKE-SYMPHONY-001` acceptance of the exact tracker adapter/state/label/blocker model, credential boundary, workspace/retry/recovery behavior, and Human Review policy. Failure selects manual dispatch and does not block the repository harness.
- Runtime work remains gated by `SPIKE-AUTH-001`, `SPIKE-STREAM-001`, `SPIKE-MDA-001`, `SPIKE-FLEET-001`, and `SPIKE-DESKTOP-001`; this plan does not resolve those contracts.

### Proposed rollout

1. Review and accept repository layout, owners, toolchain windows, and OSS policy.
2. Install the short canonical map/docs taxonomy, living ExecPlan template, architecture manifest/check, docs check, generated views, quality score, and debt tracker.
3. Scaffold workspace manifests, empty package boundaries, two fixture modes, worktree namespace, proof path, and CI policy without moving prototype code.
4. Establish FastAPI `/api/v1` OpenAPI generation and TypeScript SDK drift checks.
5. Add the Next.js fixture shell and Vercel preview; leave Tauri packaging optional until its spike passes.
6. Prove the low-risk Symphony pilot or record manual dispatch as the accepted fallback.
7. Selectively port audited prototype surfaces under explicit owning plans and acyclic work items.
8. Enable release provenance, changesets/versioning, platform builds, and clean-clone acceptance.

### Rollback

The initial scaffold is rollbackable by reverting its reviewed change because it owns no production data. After packages publish, roll back by restoring prior compatible application artifacts and issuing new package versions; never delete or overwrite published releases. Database rollback follows `DW-FND-003` and must preserve user state and audit evidence.

## Executable acceptance scenarios

```gherkin
Scenario: A clean contributor reaches a representative fixture experience
  Given a clean supported machine with no Deep Work environment variables
  When the contributor runs the documented prerequisite check and bootstrap
  And starts the fixture web application
  Then the Next.js task inbox renders synthetic data
  And no LangSmith, GitHub, Postgres, push, or signing credential is requested
  And the network-denied fixture smoke suite passes

Scenario: UI harness and product demo have explicit proof levels
  Given a contributor has no external credentials
  When they start the UI harness
  Then route and component states render without FastAPI or Postgres
  When they start the product demo
  Then fixture API, worker, Postgres, object service, web, and telemetry are healthy
  And only the product demo is accepted as end-to-end application parity evidence

Scenario: Package direction is enforced
  Given a pull request adds an import from packages/ui to packages/sdk
  When repository validation runs
  Then the dependency-boundary job fails
  And it names the importing file and allowed dependency direction

Scenario: A blocked Symphony issue cannot dispatch
  Given an issue is agent-ready but has a non-terminal required blocker
  When the pinned Symphony runner reconciles the tracker
  Then no workspace or coding session is created for that issue
  And clearing the blocker does not make it eligible until every other dispatch predicate is true

Scenario: Two agent worktrees are isolated
  Given two independent low-risk issues are eligible at concurrency two
  When each starts the product demo
  Then their paths, ports, database/schema, object prefix, browser origin/storage, telemetry, and proof artifacts differ
  And neither can read or stop the other's resources

Scenario: FastAPI and TypeScript contracts cannot drift silently
  Given a contributor changes a proposed /api/v1 response schema
  When the OpenAPI contract check runs without regenerating the TypeScript SDK
  Then CI fails with the schema and generated-client diff
  And no preview is eligible for release qualification

Scenario: Private beta is not a default prerequisite
  Given no MDA or Fleet credentials or private packages are available
  When a contributor installs and tests the repository
  Then default bootstrap and fixture tests succeed
  And MDA and Fleet capabilities are represented as unavailable

Scenario: A publish failure is recoverable and attributable
  Given a protected release build produces approved checksummed artifacts
  And one registry publication fails after another succeeds
  When the maintainer reviews release state
  Then the immutable published artifact is recorded
  And only the missing artifact can be retried or superseded by a new version
  And no artifact is overwritten

Scenario: OSS license and trademark posture is forkable and explicit
  Given a clean external fork and the complete source and built-artifact set
  When the legal and branding audit checks root license, notices, dependency
    licenses, generated and vendored attribution, package metadata, product naming,
    logos, contributor terms, security policy, and non-affiliation language
  Then every distributed artifact has compatible recorded provenance
  And no restricted LangChain or provider mark is presented as Deep Work ownership
  And a contributor can identify permitted use and the trademark boundary from the repository
```
