---
exec_plan_id: DW-EXEC-PRODUCT-RECOVERY-GOLDEN-JOURNEY
title: Restore the designed Deep Work golden journey
status: active
superseded_by: null
owner: product-recovery
reviewed_by: [product-owner]
reviewed_at: 2026-08-03
primary_feature_id: DW-QUAL-001
supporting_feature_ids: [DW-FND-002, DW-ONB-001, DW-TASK-002, DW-TASK-003, DW-HITL-001, DW-SURF-001]
issue: local:DW-PRODUCT-RECOVERY-001
created: 2026-08-03
last_updated: 2026-08-03
base_commit: c7e0ea6cd2fce6187d96f0da06957320641c4a4e
last_verified_commit: 48e21024a0bf9691c2d8a9531be7f210e4547b45
risk: high
governed_paths: [.github/workflows/**, apps/api/**, apps/web/**, tests/**, playwright.config.ts, package.json, Makefile, docs/PLANS.md, docs/QUALITY_SCORE.md, docs/RELEASE_SCORECARD.md, docs/exec-plans/index.md, docs/exec-plans/active/DW-EXEC-PRODUCT-RECOVERY-GOLDEN-JOURNEY.md]
contract_gates: []
decision_gates: [DEC-033]
gate_review_status: reviewed-with-gates
gate_reviewed_by: [product-owner]
gate_reviewed_at: 2026-08-03
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, docs/PRODUCT_SENSE.md, docs/DESIGN.md, docs/FRONTEND.md, docs/PLANS.md, docs/product-specs/acceptance-scenarios.md, docs/product-specs/foundations/dw-fnd-002-design-system-shell-and-demo-mode.md, docs/product-specs/onboarding/DW-ONB-001-auth-session-workspace-demo.md, docs/product-specs/tasks/DW-TASK-002-composer-templates-attachments-rubric-plan.md, docs/product-specs/tasks/DW-TASK-003-detail-streaming-tools-reasoning-todos-reconnect.md, docs/product-specs/approvals/DW-HITL-001-ordered-approvals-plan-stale-mobile.md, docs/product-specs/surfaces/dw-surf-001-responsive-web-pwa-offline-and-push.md]
scenario_ids: [E2E-V1-01-FIRST-VALUE, E2E-V1-02-TRUTHFUL-RUNTIME, E2E-V1-06-ORDERED-APPROVAL, E2E-V1-08-RESPONSIVE-ACCESS, E2E-V1-11-CONTRIBUTOR, E2E-V1-12-OPERATIONAL-RELEASE]
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
- Visual evidence: sibling `deep-work-frontend` at exact commit `26c698b`.
- Behavior: existing `/api/v1` task, decision, stream, trace, agent, schedule, and
  session contracts at base `c7e0ea6`.
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

## Progress

- [x] 2026-08-03 00:00 PDT — Product-owner recovery directive accepted and clean
  worktree created from exact base `c7e0ea6`.
- [x] 2026-08-03 — Binding visual baseline complete at `5752de3`.
- [x] 2026-08-03 — Designed shell and entry complete at `990a956`.
- [x] 2026-08-03 — Golden task journey complete at `b726909`.
- [x] 2026-08-03 — Blocking browser gates complete at `48e2102`.
- [x] 2026-08-03 — Live release scorecard complete; hosted and release columns
  remain explicitly unproven.
- [x] 2026-08-03 — Independent local review complete. Review fixes bind the
  prototype pixels, harden hosted credential handling, retain selected agent
  identity, guard decision races and fail orphaned SQLite fixture runs closed.
- [x] 2026-08-03 — Final verification and delivery handoff complete. API, web,
  documentation, local browser and visual acceptance pass; existing base
  architecture, API typing and API formatting debt remains explicitly recorded.

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
- 2026-08-03 — Broad checks still expose base-branch debt outside this recovery:
  14 pre-existing mypy findings in five files, four ruff-format findings in
  untouched files, and ten architecture findings. The recovery adds no mypy or
  ruff-format failure; `run-panel.tsx` is listed by architecture for a pre-existing
  trace fetch.

## Decision Log

- 2026-08-03 — The pinned prototype is binding visual/interaction evidence while
  existing application contracts remain runtime authority. Approved by:
  product-owner.
- 2026-08-03 — Visual and hosted gates are separate: fixture screenshots cannot
  satisfy hosted proof, and hosted reachability cannot satisfy visual parity.
  Approved by: product-owner.

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

## Validation and proof

```text
make doctor
make check-docs
make check-architecture
make check
make test-unit
make test-contract
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
reflow, a fail-closed real-source hosted journey, and the 12-scenario scorecard.

Independent review found and the branch fixed a stale decision-receipt race,
unretained agent identity, overlapping mobile overlays, secret-bearing hosted
traces, a fixture restart orphan, and an unqualified screenshot environment. The
real hosted journey and every release-acceptance column remain unproven because no
protected hosted credentials or release-owner acceptance were available in this
recovery. No push, merge, deployment, secret change or release acceptance occurred.
