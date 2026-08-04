---
exec_plan_id: DW-EXEC-PRODUCT-RECOVERY-GOLDEN-JOURNEY
title: Restore the designed Deep Work golden journey
status: active
superseded_by: null
owner: product-recovery
reviewed_by: [product-owner]
reviewed_at: 2026-08-03
primary_feature_id: DW-QUAL-001
supporting_feature_ids: [DW-FND-002, DW-ONB-001, DW-TASK-002, DW-TASK-003, DW-HITL-001, DW-CODE-001, DW-CODE-002, DW-CODE-003, DW-SURF-001]
issue: local:DW-PRODUCT-RECOVERY-001
created: 2026-08-03
last_updated: 2026-08-04
base_commit: c7e0ea6cd2fce6187d96f0da06957320641c4a4e
last_verified_commit: 1a80096ce27d2fc7925d7c66161ff38ca207dc72
risk: high
governed_paths: [.github/workflows/**, apps/api/**, apps/web/**, packages/agent/**, packages/domain/**, packages/sdk/**, packages/ui/**, tests/**, tools/architecture/**, tools/contract-spikes/**, tools/docs/**, tools/oss_audit/**, tools/product_demo/**, tools/worktree/**, ARCHITECTURE.md, dev, playwright.config.ts, playwright.hosted.config.ts, playwright.performance.config.ts, playwright.recovery.config.ts, playwright.security.config.ts, playwright.visual.config.ts, package.json, pnpm-lock.yaml, pnpm-workspace.yaml, pyproject.toml, .node-version, Makefile, docs/PLANS.md, docs/QUALITY_SCORE.md, docs/RELEASE_SCORECARD.md, docs/exec-plans/index.md, docs/exec-plans/active/DW-EXEC-PRODUCT-RECOVERY-GOLDEN-JOURNEY.md]
contract_gates: [SPIKE-HITL-001]
decision_gates: [DEC-033]
gate_review_status: reviewed-with-gates
gate_reviewed_by: [product-owner]
gate_reviewed_at: 2026-08-03
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, docs/PRODUCT_SENSE.md, docs/DESIGN.md, docs/FRONTEND.md, docs/PLANS.md, docs/product-specs/acceptance-scenarios.md, docs/product-specs/foundations/dw-fnd-002-design-system-shell-and-demo-mode.md, docs/product-specs/onboarding/DW-ONB-001-auth-session-workspace-demo.md, docs/product-specs/tasks/DW-TASK-002-composer-templates-attachments-rubric-plan.md, docs/product-specs/tasks/DW-TASK-003-detail-streaming-tools-reasoning-todos-reconnect.md, docs/product-specs/approvals/DW-HITL-001-ordered-approvals-plan-stale-mobile.md, docs/product-specs/coding/DW-CODE-001-sandbox-environments-snapshots-setup-egress.md, docs/product-specs/coding/DW-CODE-002-github-auth-repository-pr-ci-merge.md, docs/product-specs/coding/DW-CODE-003-files-diff-terminal-browser-phone.md, docs/product-specs/surfaces/dw-surf-001-responsive-web-pwa-offline-and-push.md]
scenario_ids: [E2E-V1-01-FIRST-VALUE, E2E-V1-02-TRUTHFUL-RUNTIME, E2E-V1-06-ORDERED-APPROVAL, E2E-V1-07-CODING-DRAFT-PR, E2E-V1-08-RESPONSIVE-ACCESS, E2E-V1-11-CONTRIBUTOR, E2E-V1-12-OPERATIONAL-RELEASE]
dispatch_kind: cell
dispatch_ready: true
agent_review_required: true
dependencies: []
blockers: []
---

# Restore the designed Deep Work golden journey

## Purpose and observable result

Restore product convergence around one browser-verifiable outcome: a user sees the
accepted Deep Work brand and shell, connects or enters the credential-free demo,
chooses an agent, composes a task, reviews and approves its plan, follows progress,
inspects a useful result with evidence/files/trace truth, and reopens the completed
task. The same journey must remain usable at desktop and phone widths.

The accepted `deep-work-frontend@26c698b30ff08d5122cfaeedbd4a95296a7884f4`
remains read-only source evidence. Route-scoped reference screenshots and a
machine-readable manifest copied one way into this repository become the binding
visual baseline; the sibling repository never becomes a runtime dependency.

## Context and orientation

At the base commit, the real API, fixture runner, source-backed task loop, approval
contract, task result, trace lookup, five-destination shell, agent registry, and
schedules exist. The shipped login is a bare access-key card; visual acceptance is
not enforced; the file and change surfaces are usually unavailable; the local
browser journey does not prove the designed route set; and the canonical roadmap
does not distinguish implemented, browser-proven, hosted-proven, and release-
accepted evidence.

The implementation must preserve runtime truth. A designed control whose real
contract is unavailable renders an explicit unavailable state or deterministic
fixture evidence; it never simulates provider success.

## Scope

### In scope

- Capture desktop and phone reference screenshots for login, task inbox, new task,
  task detail, approvals, agents, schedules, activity, and settings from the pinned
  sibling prototype.
- Port the accepted brand, shell, sign-in/connect, workspace, agent choice,
  composer, task history, approval, result, evidence, files, and trace interactions
  onto existing browser-safe application contracts.
- Complete and test one credential-free API-backed golden journey including reopen.
- Add blocking local visual comparison and separately configured hosted acceptance
  commands/workflows, including console and failed-network checks.
- Replace stale roadmap status prose with an evidence-backed twelve-scenario
  scorecard carrying four independent proof columns.

### Non-goals

- Provider OAuth, Fleet CRUD, invented connector APIs, arbitrary deployment
  automation, automatic merge, production credentials, or fake terminal/browser
  success.
- Editing, committing to, or adding a dependency on `deep-work-frontend`.
- Claiming a release scenario accepted from fixture or screenshot evidence alone.

### Permissions and risk boundary

- Work only in the isolated `product/golden-journey-recovery` worktree.
- Read the pinned sibling frontend and hosted validation deployment; do not mutate
  either. Never read, print, persist, or screenshot access-key values.
- Repository commits are allowed on the recovery branch. Push, merge, deploy,
  branch-protection changes, hosted-secret changes, and destructive cleanup remain
  prohibited without separate authority.
- Product-owner direction in the 2026-08-03 request reviews the bounded outcome and
  visual authority. A separate code review is still required before handoff.

## Authoritative sources and prerequisites

- Product and design: `docs/PRODUCT_SENSE.md`, `docs/DESIGN.md`, and
  `docs/FRONTEND.md`.
- Visual evidence: sibling `deep-work-frontend` at exact commit
  `26c698b30ff08d5122cfaeedbd4a95296a7884f4`.
- Behavior: existing `/api/v1` task, decision, stream, trace, agent, schedule, and
  session contracts at base `c7e0ea6cd2fce6187d96f0da06957320641c4a4e`.
- Acceptance: the six linked program scenarios and their stable feature scenarios.

## Interfaces and invariants

- Client direction remains app -> SDK/UI -> domain; no provider credentials or
  server-only references enter browser state, URLs, screenshots, logs, or fixtures.
- The access-key form posts only to `/api/v1/auth/login`; demo entry is explicit and
  causes no external side effect.
- Task creation remains idempotent through the existing task client; decisions use
  the ordered decision contract; re-opening hydrates the same task identity.
- Fixture artifacts and evidence identify their deterministic evidence class.
- Visual comparison covers 1440x1000 desktop and 390x844 phone viewports. WCAG 2.2
  AA, keyboard access, reduced motion, and 320 CSS-pixel reflow remain mandatory.
- Hosted acceptance never falls back to fixture mode and fails closed when its
  required URL or access-key secret is absent.

## Milestones

### Milestone 1 — Binding visual baseline

Capture the pinned prototype routes at both viewports, store sanitized images under
`tests/visual/reference/`, and add a manifest that maps every route/state/viewport
to its source commit and expected canonical destination.

Acceptance: the manifest is complete, every image is readable, and the capture
command reproduces the inventory without modifying the sibling checkout.

### Milestone 2 — Designed shell and entry

Port the branded sign-in/connect experience, responsive shell, workspace identity,
agent selection, and composer affordances onto the existing session/task/agent
contracts. Unsupported authentication and tool choices remain explicitly
unavailable.

Acceptance: focused component tests pass and desktop/phone screenshots match the
accepted layout within the reviewed screenshot threshold.

### Milestone 3 — Complete golden task journey

Extend deterministic API-backed evidence so the task history exposes plan review,
approval, progress, useful result, evidence, files and trace classification, then
reopens the completed task from the inbox without changing identity.

Acceptance: `make test-e2e-demo` executes the complete journey with loopback-only
traffic, no console errors, and assertions for every named outcome.

### Milestone 4 — Blocking browser gates

Add deterministic visual comparison and authenticated hosted acceptance commands to
the root contract and CI. Hosted proof uses only configured secret references and
fails rather than skipping when its required configuration is missing.

Acceptance: local visual tests fail on an intentional pixel change; hosted tests
target the deployed app, prohibit fixture fallback, complete the task lifecycle,
and retain only password-masked screenshots on failure.

### Milestone 5 — Live release scorecard

Replace stale plan status with `docs/RELEASE_SCORECARD.md`, one row per canonical
E2E scenario and separate implemented, browser-proven, hosted-proven, and release-
accepted columns. Every non-empty proof cell names an exact commit/environment and
artifact; unknown stays unknown.

Acceptance: documentation checks pass, no row infers release acceptance, and the
README/PLANS/QUALITY_SCORE status language agrees with the scorecard.

### Milestone 6 — Normalized ordered approval batch

Carry the installed positional HITL shape through the application API, pure domain,
browser SDK, and task/approvals UI. Fixture mode must exercise repeated action names,
per-position allowed decisions, edit-only-where-allowed, complete-vector validation,
expected-version stale rejection, idempotent duplicate handling, durable audit, and
desktop/phone interaction. The classic source adapter stays on its existing bounded
single-action fallback until live server evidence accepts ordered resume behavior.

Acceptance: focused API/domain/SDK/web tests and a two-width browser case prove one
complete repeated-name vector. A malformed or stale vector sends no provider request;
the scorecard continues to distinguish installed/local proof from hosted acceptance.

### Milestone 7 — Truthful coding-to-draft-PR fixture journey

Bind the accepted coding-review shell to an additive real task API contract. The
credential-free deterministic fixture exposes exact revision, sandbox, file,
draft-PR retry and non-authoritative CI evidence without claiming GitHub or hosted
provider execution. Partial bindings fail before task creation, coding evidence
appears only on a completed coding task, and the result survives SQLite reopen.

Acceptance: API/domain/SDK/web tests plus a phone browser journey prove fresh sign-in,
coding choice, ordered approval, progress, exact-SHA inspection, unavailable merge
and reopen. Real GitHub, authoritative CI, hosted proof and release acceptance stay
explicitly gated.

### Milestone 8 — PostgreSQL job/outbox durability

Replace the local-only SQLite job proof at the production boundary with an
Alembic-managed PostgreSQL repository using SQLAlchemy 2 and Psycopg 3. Preserve
the existing application port and HTTP/session contract while adding atomic
job/outbox acceptance, tenant/workspace idempotency, lease expiry, bounded retry,
dead-letter behavior, and `FOR UPDATE SKIP LOCKED` worker concurrency. SQLite
remains labelled local proof and may not satisfy this milestone.

Acceptance: an isolated local PostgreSQL cluster applies migrations from zero;
API and worker use separate processes; accepted work survives either process
stopping; duplicate intake produces one job and one outbox effect; expired leases
recover; concurrent workers do not double-complete; cross-tenant and cross-
workspace reads fail closed; downgrade/upgrade and clean reinstall checks pass.

### Milestone 9 — Sealed dual-stack product-demo proof

Rebase the archived product-demo draft onto the current runtime and implement the
reviewed worktree driver contract with two concurrent isolated stacks. Each stack
must contain the real web, API, worker, PostgreSQL, object and telemetry services;
the driver may not relabel SQLite or an in-process stub as PostgreSQL. Seal the
reviewed driver blob in an ancestor commit before binding its contract digest.

Acceptance: the harness proves collision-free namespaces and ports, sixteen
bidirectional isolation probes, process restart/read-back, browser golden journey,
task/run-qualified evidence and artifact digest binding, true 390x844 viewport
captures, exact clean execution commits, teardown and reservation release for both
stacks, plus idempotent recovery if receipt finalization is interrupted. This
is local product-demo proof only and does not populate hosted or release-accepted
scorecard columns.

## Progress

- [x] 2026-08-03 00:00 PDT — Product-owner recovery directive accepted and clean
  worktree created from exact base `c7e0ea6cd2fce6187d96f0da06957320641c4a4e`.
- [x] 2026-08-03 — Binding visual baseline complete at
  `5752de32bb04433f2def4b815cc444b52a47bfab`.
- [x] 2026-08-03 — Designed shell and entry complete at
  `990a9561faff0472132a9dbf4550cf52f6c023f3`.
- [x] 2026-08-03 — Golden task journey complete at
  `b7269091b1f1881b42235d634379a6916e349ede`.
- [x] 2026-08-03 — Blocking browser gates complete at
  `48e21024a0bf9691c2d8a9531be7f210e4547b45`.
- [x] 2026-08-03 — Live release scorecard complete; hosted and release columns
  remain explicitly unproven.
- [x] 2026-08-03 — Independent local review complete at
  `265da2a1f2cfb53a9ce0ad02c1f3169881801b01`. Review fixes bind the prototype
  pixels, harden hosted credential handling, retain selected agent identity,
  preserve default-agent prompt semantics, and guard decision races.
- [x] 2026-08-03 — Recovery-slice verification checkpoint complete. API, web,
  documentation, local browser and visual acceptance pass for the implemented
  slice; this ExecPlan stays active while the twelve-scenario scorecard retains
  unimplemented, hosted-unproven and release-unaccepted work.
- [x] 2026-08-03 — Exact installed HITL middleware and protocol-v3 command evidence
  pinned at `8b1b7f5cfa23a5528b39a446337e1663379fe4b5`; live classic-server semantics
  remain unavailable and product submission stays fail-closed beyond the current
  bounded contract.
- [x] 2026-08-03 — Normalized ordered approval batch completed at
  `e11efe03fb75754639b20c71bbc18982586bfb60` across the application API, domain,
  SDK and browser UI. Repeated-name mixed vectors, durable version-bound replay,
  edited-plan trace, explicit per-action choice, two-device stale/conflict safety,
  keyboard/touch access and desktop/phone screenshots pass locally. Classic batch
  resume, hosted proof and release acceptance remain gated.
- [x] 2026-08-03 — Truthful coding-to-draft-PR fixture journey completed at
  `8acd3db9dce29ee9b8a20de5363b604315a17ca5`. The additive task contract binds
  coding intent and repository identity, exposes terminal-only exact-revision and
  deterministic sandbox/PR/CI evidence, reconciles one retained draft PR after a
  simulated timeout, persists through SQLite reopen, blocks creation until the
  agent registry resolves, completes and reopens on a phone, and keeps real GitHub,
  authoritative CI, hosted execution, merge and release acceptance fail-closed.
- [x] 2026-08-04 — The source-backed local golden journey was repaired and
  re-proven through the production web bundle at `a326c84`; canonical status was
  reconciled at `a2c4b41`.
- [x] 2026-08-04 — Session-scoped SQLite job/API/worker recovery proof completed
  at `c28ef9b`; scorecard truth was reconciled at `e7a8ef9`. This is explicitly
  not PostgreSQL/outbox or product-demo proof.
- [x] 2026-08-04 — PostgreSQL job/outbox runtime, packaged Alembic migration and
  recovery proof completed at `ef0bcc852ddae90c92a3144b16922c7d067799a7`.
  The existing SQLite `/api/v1/jobs` response remains byte-compatible; the
  additive `/api/v1/durable-jobs` contract truthfully identifies the guarded
  PostgreSQL outbox implementation.
- [x] 2026-08-04 — Sealed dual-stack product-demo driver and local browser
  acceptance complete through the canonical harness. The accepted receipt binds
  both clean execution commits, exact driver/browser/contract provenance, two
  complete journeys, four restart/reopen observations, ten retained browser
  artifacts, sixteen bidirectional isolation observations and both reservation
  releases. Raw driver runs remain `pending-receipt`; interrupted finalization is
  recoverable and repeated namespace generations are regression-tested.
- [x] 2026-08-04 — Source recovery completed through non-owner plan-edit routing
  (`80cf434`), transient active-stream retry (`680ae40`), bounded replay/receipt
  retention (`1e5c065`) and real OS-process kill/takeover proof (`7b65f96`).
- [x] 2026-08-04 — Adversarial review correction completed at `1a80096`. Current
  lease tokens fence source-owned commits, accepted handoffs re-enter durable
  recovery, permanent stream outage terminates safely, API/domain/SDK contract
  fields align, PostgreSQL waits are bounded, migrations really downgrade and
  re-upgrade, the visual comparator is full-resolution/color-sensitive, and
  hosted acceptance binds both deployed services to the exact CI commit.
- [x] 2026-08-04 — Current focused verification passes 95 API tests, 80 domain
  tests, 73 SDK tests, 22 composer-dispatch tests, three TypeScript type checks,
  and the two-test 12-route desktop/phone visual reference contract.
- [ ] 2026-08-04 — Current-head production-browser rerun. The harness starts, but
  the nearly full workstation volume prevents Chromium from creating its profile
  (`ENOSPC`) before any application assertion. Prior browser proof is retained but
  is not relabelled as a current-head pass.
- [ ] Protected hosted browser proof and release-owner acceptance.

## Surprises & Discoveries

- 2026-08-03 — The base checkout is 56 commits behind `origin/main` in the protected
  dirty tree, so recovery is pinned to the user-requested commit and cannot borrow
  unreviewed local changes.
- 2026-08-03 — The formal v1 stories are intentionally much broader than the
  golden journey. The recovery materially advances six scenarios but completes no
  entire program story, so every hosted and release-accepted cell remains `No`.
- 2026-08-03 — Development-mode Fast Refresh made screenshot output unstable when
  Playwright wrote artifacts. The visual gate builds once and serves the production
  bundle, which makes the comparison deterministic without changing API behavior.
- 2026-08-03 — The first agent chooser forwarded `agentId` to execution but did
  not retain it in the task snapshot. The recovered contract now records it in
  `task.created`, projects it in list/detail responses, and renders it after reopen.
- 2026-08-03 — The cross-model adversarial reviewer could not run because its
  configured Claude CLI was not authenticated. Local correctness, security,
  contract, reliability, race, testing, standards, maintainability and agent-native
  reviewers still completed; the missing cross-model corroboration is explicit.
- 2026-08-03 — Broad checks initially exposed base-branch debt outside the visual
  recovery: 14 mypy findings, four ruff-format findings and ten architecture
  findings. The follow-on contributor-gate repair removed those findings without
  changing product behavior; the supported root `make check` now passes.
- 2026-08-03 — Final correctness, contract/security and product/browser reviewers
  found replay-version spoofing, API/SDK version drift, rejected batch events,
  missing edited-plan trace, stale cross-device controls and implicit approve-all
  behavior. The final contract binds and persists the reviewed version, uses the
  API string version end to end, maps positional audit types, emits `plan.updated`
  atomically, invalidates stale controls and requires an explicit choice for every
  action.
- 2026-08-04 — The archived product-demo packets are draft, unreviewed,
  non-dispatchable and pinned to obsolete dependencies. The current API lock has
  no SQLAlchemy, Alembic or Psycopg, while canonical architecture requires real
  PostgreSQL and a transactional outbox. Consequence: implement and prove the
  PostgreSQL boundary before sealing the dual-stack driver; do not manufacture a
  product-demo pass around SQLite.
- 2026-08-04 — The implementation volume reached 100% APFS capacity during the
  current-head browser rerun. Next and Chromium failed with `ENOSPC`; only failed
  generated `.next` and Playwright output were removed. This is an execution-host
  blocker, not browser acceptance evidence.

## Decision Log

- 2026-08-03 — The pinned prototype is binding visual/interaction evidence while
  existing application contracts remain runtime authority. Approved by:
  product-owner.
- 2026-08-03 — Visual and hosted gates are separate: fixture screenshots cannot
  satisfy hosted proof, and hosted reachability cannot satisfy visual parity.
  Approved by: product-owner.
- 2026-08-03 — Installed public packages are sufficient to freeze the normalized
  positional application shape and fixture behavior, but not to enable a classic
  provider batch resume. The provider adapter keeps its bounded fallback until a
  live transcript proves stale, duplicate, authorization, transport-failure and
  post-resume behavior. Approved by: product-owner.
- 2026-08-04 — Rebase the product-demo outcome into this active recovery plan and
  use the current application port/session contracts. Pin stable SQLAlchemy 2,
  Alembic and Psycopg 3 releases from official package metadata, retain exact
  package locks, and require real local PostgreSQL before product-demo acceptance.
  Approved by: product-owner directive to execute the roadmap through completion.
- 2026-08-04 — Hosted acceptance must bind the checked-out CI commit to both the
  API runtime status and the rendered web shell before exercising the journey.
  Configuration or reachability alone cannot populate the hosted-proof column.
  Approved by: product-owner directive for blocking hosted browser acceptance.

## Detailed implementation approach

1. Run the prototype and canonical fixture app with deterministic data; capture the
   route matrix at the two required viewports.
2. Port presentation primitives and interactions route by route, beginning with
   login/shell/composer and retaining all existing API boundaries.
3. Strengthen fixture/API projections and the browser journey for result evidence,
   file artifacts, trace truth and reopen.
4. Add visual and hosted Playwright projects plus root/CI commands.
5. Write the live scorecard from executable evidence, reconcile canonical status
   prose, regenerate documentation, and run the full repository gates.
6. Add a real PostgreSQL job/outbox repository with packaged migrations, atomic
   enqueue, scoped idempotency, concurrent worker leases, retry/dead-letter
   recovery and separate API/worker restart proof while preserving the existing
   v1 SQLite contract.
7. Build and seal the repository-reviewed dual-stack product-demo driver, then run
   its local browser/isolation acceptance before seeking protected hosted proof.

## Validation and proof

```text
make doctor
make check-docs
make check-architecture
make check
make test-unit
make test-contract
make test-postgres
make test-e2e-demo
make test-visual
make test-hosted
```

Retain screenshots, traces, console/network summaries, and scorecard evidence under
sanitized repository output paths. Fixture and hosted evidence remain labelled as
different proof classes.

## Idempotence, rollback, and recovery

Reference capture writes only deterministic repository artifacts and never edits
the sibling. Browser tasks use unique prompts and application task IDs; hosted
cleanup is not attempted without a tested API and separate authority. Every
milestone is committed only after its focused checks pass, so a failed later unit
can be retried without resetting or rewriting the protected checkout.

## Rollout and handoff

No deployment, push, merge, required-check registration, or secret configuration is
authorized by this plan. The completed branch hands exact commits, local proof,
hosted-test configuration requirements, residual findings, and the scorecard to the
product owner for those external actions.

## Outcomes & Retrospective

The branch now contains the designed shell, a complete credential-free supervised
task journey, retained result/evidence/export/trace inspection, reopen, immutable
prototype references, complete route mappings, desktop/phone screenshots, 320px
reflow, a truthful credential-free coding-to-draft-PR fixture journey, a fail-closed
real-source hosted journey, a real local PostgreSQL transactional job/outbox with
packaged migrations and separate API/worker restart proof, a sealed dual-stack
product-demo receipt with clean-source and crash-recovery guarantees, and the
12-scenario scorecard.

Independent review found and the branch fixed a stale decision-receipt race,
unretained agent identity, overlapping mobile overlays, secret-bearing hosted
traces, a fixture restart orphan, and an unqualified screenshot environment. The
real hosted journey and every release-acceptance column remain unproven because no
protected hosted credentials or release-owner acceptance were available in this
recovery. No push, merge, deployment, secret change or release acceptance occurred.
