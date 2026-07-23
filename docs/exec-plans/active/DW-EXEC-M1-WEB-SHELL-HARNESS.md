---
exec_plan_id: DW-EXEC-M1-WEB-SHELL-HARNESS
title: Responsive browser-local web shell source and importer
status: draft
superseded_by: null
owner: web-shell
reviewed_by: []
reviewed_at: null
primary_feature_id: DW-FND-002
supporting_feature_ids: [DW-FND-001, DW-FND-004, DW-FND-005, DW-SURF-001, DW-QUAL-001]
issue: local:DW-M1-WEB-SHELL-HARNESS
created: 2026-07-23
last_updated: 2026-07-23
base_commit: 9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2
last_verified_commit: null
risk: medium
governed_paths: [apps/web/**, docs/exec-plans/active/DW-EXEC-M1-WEB-SHELL-HARNESS.md]
contract_gates: [SPIKE-HARNESS-ARCH-001, SPIKE-PWA-001]
decision_gates: [DEC-004, DEC-006, DEC-007, DEC-033, DEC-034, DEC-042]
gate_review_status: unreviewed
gate_reviewed_by: []
gate_reviewed_at: null
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, docs/AGENTS.md, docs/PLANS.md, docs/DESIGN.md, docs/FRONTEND.md, docs/SECURITY.md, docs/RELIABILITY.md, docs/design-docs/architecture/application-architecture.md, docs/design-docs/engineering/conventions.md, docs/design-docs/decisions/index.md, docs/product-specs/foundations/dw-fnd-001-repository-oss-and-delivery-foundation.md, docs/product-specs/foundations/dw-fnd-002-design-system-shell-and-demo-mode.md, docs/product-specs/foundations/dw-fnd-004-sdk-stream-and-fixture-contracts.md, docs/product-specs/foundations/dw-fnd-005-domain-identity-status-and-audit-model.md, docs/product-specs/surfaces/dw-surf-001-responsive-web-pwa-offline-and-push.md, docs/product-specs/quality/dw-qual-001-accessibility-performance-security-testing-and-release.md, docs/exec-plans/active/DW-EXEC-M1-TS-PACKAGES-SCAFFOLD.md]
scenario_ids: [AC-DW-FND-002-01, AC-DW-FND-002-02, AC-DW-FND-002-03, AC-DW-FND-002-05, AC-DW-FND-002-06, AC-DW-SURF-001-01, AC-DW-QUAL-001-05]
dispatch_kind: cell
dispatch_ready: false
agent_review_required: true
dependencies: [local:DW-M1-TS-VERIFY-001]
blockers: []
---

# Responsive browser-local web shell harness

## Purpose and observable result

Create and independently accept the static `apps/web` source/importer for Deep
Work's accessible responsive composition root: five primary destinations—Tasks,
Approvals, Agents, Schedules, and Activity—plus the Settings utility route. The
source contains an unmistakable browser-local UI harness, deterministic
presentation states, responsive behavior from 320 CSS pixels through desktop,
and the exact tests/runners that the downstream web lock and re-verification
cells execute.

The shell permanently marks the session as `Demo data · UI harness` and explains
that persistence, worker/recovery, service failures, and full integration are not
under test. It never claims API-backed product-demo proof or live-provider proof.

This source-only cell contributes design/static shell slices of `AC-DW-FND-002-01`,
`AC-DW-FND-002-02`, `AC-DW-FND-002-03`, `AC-DW-FND-002-05`, and
`AC-DW-FND-002-06`. It contributes responsive component/shell evidence only to
`AC-DW-SURF-001-01` and `AC-DW-QUAL-001-05`; it does not complete either scenario.
It completes zero `E2E-V1-*` scenarios.

Status is **draft, prepared for independent review**. Execution starts only after
terminal `local:DW-M1-TS-VERIFY-001`. This cell terminates at an independently
accepted static source/importer commit. It performs no install, build, test, or
browser run. The separate `local:DW-M1-WEB-LOCK-EXTENSION-001` consumes that
terminal source together with the terminal API-SDK bridge; only
`local:DW-M1-WEB-TS-REVERIFY-001` may make executable/browser claims.

## Context and orientation

The exact plan-authoring base is
`9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2`. `apps/web` does not exist at that
base. Existing client seeds are:

- `packages/domain` source-qualified identity, capability evidence, task status,
  and view-state values;
- `packages/sdk` browser-safe query/mutation/stream ports and typed unavailable
  results;
- `packages/ui` tokens plus one accessible `StatusPanel`;
- root Node 24, pnpm 10, Turbo, and TypeScript declarations without a shared
  `pnpm-lock.yaml`; and
- the sibling frontend at
  `26c698b30ff08d5122cfaeedbd4a95296a7884f4`, which is visual/interaction
  evidence only and cannot be imported, modified, or treated as behavior proof.

The TypeScript candidate `1bf66e1` is `REWORK REQUIRED`. No exact accepted TS
executable-verification commit exists for this plan yet. The shell plan may be
reviewed now, but no implementation dispatch can infer acceptance from the
current checkout.

The browser-local harness and API-backed product demo are separate proof levels.
This plan owns only the former. It uses the same route/component boundaries
intended for later SDK injection, but its repository is an in-process,
browser-local state adapter selected explicitly at composition. A failed live or
API request can never activate it because this cell makes no such request.

## Scope

### In scope

- Only `apps/web/**` and this living ExecPlan.
- Next.js App Router package/source/test/config owned by `apps/web`.
- Primary routes `/tasks`, `/approvals`, `/agents`, `/schedules`, and
  `/activity`; utility `/settings`; safe not-found route.
- Semantic banner/header, primary navigation, contextual navigation, `main`,
  optional complementary region, and polite status region.
- Desktop/tablet/phone navigation with direct phone access to Tasks, Approvals,
  and Agents; Schedules, Activity, Settings, workspace, and account in a labelled
  More/account surface within two actions.
- Persistent, non-dismissible `Demo data · UI harness` marker, synthetic
  workspace/actor/source labels, limitations link/region, reset, and exit/reload.
- Browser-local deterministic repository selected only by a build/test harness
  entry. It persists no credentials or live identity and is resettable.
- Shared design token consumption from `@deepwork/ui/tokens.css` and
  `@deepwork/ui/status-panel.css`. App CSS may compose layout using token
  variables but may not fork the token system.
- Loading, empty, partial, error, offline, permission-denied, stale,
  reconnecting, cancelled, success, capability-unavailable, unknown,
  UI-harness-only, and narrow/mobile state fixtures.
- Visible focus, logical keyboard order, skip link, focus restoration, modality,
  touch targets, non-color status, reduced motion, forced colors, 320px reflow,
  200% text zoom, 400% browser zoom/reflow, safe areas, and virtual-keyboard-safe
  composition.
- Source for no-request guards, route/component tests, accessibility tests,
  responsive browser proof, screenshot matrix, and network summary. This cell
  statically reviews their presence and boundaries; it does not execute them.

### Non-goals

- Editing root `package.json`, `pnpm-workspace.yaml`, `pnpm-lock.yaml`,
  `turbo.json`, root `Makefile`, TypeScript packages, `internal/fixtures/**`,
  `internal/adapter-tests/**`, generated docs, index/program plans, or
  `docs/plans/**`.
- API, SDK transport implementation, provider source, authentication, live
  session, worker, Postgres, object storage, telemetry, product-demo driver, or
  full-stack persistence/recovery.
- PWA installation, service worker, push, offline mutation queue, Tauri, native
  mobile, or platform qualification. `SPIKE-PWA-001` remains open and ordinary
  responsive web is the fallback.
- Feature-complete task/approval/agent/schedule/activity business journeys.
  Destination pages are bounded shell/state fixtures.
- Copying prototype code, lockfiles, generated conventions, mock network calls,
  simulated upstream success, or a UI control presented as live capability.
- Completing `AC-DW-SURF-001-01`, `AC-DW-QUAL-001-05`, a full feature scenario,
  or any `E2E-V1-*` scenario.

### Permissions and risk boundary

- Writes are limited to the two governed path entries in front matter.
- No install, dependency resolution, lock generation, external network, service
  startup, credential, sibling edit, push, merge, deploy, or destructive action.
- This source/importer cell may not run the local Next.js process, package
  manager, test runner, build, or browser. Those actions belong only to
  `local:DW-M1-WEB-TS-REVERIFY-001` after the web lock extension is terminal.
- The authored browser tests must fail closed after the initial loopback document
  and same-origin static assets if `fetch`, XHR, WebSocket, EventSource,
  `sendBeacon`, service-worker registration, or external navigation occurs.
- Product/UX, accessibility, frontend architecture, security, and developer-
  experience review are required. The author cannot approve the plan or result.

## Authoritative sources and prerequisites

### Persistent dependency and lock sequence

| Stable cell | Terminal evidence required | Current state |
|---|---|---|
| `local:DW-M1-TS-VERIFY-001` | Exact terminal package source, first lock, offline executable proof, and public domain/SDK/UI exports | Not represented in this checkout; candidate `1bf66e1` is `REWORK REQUIRED` and cannot satisfy it. |

Planning review does not require the cell to be terminal. Implementation dispatch
does. No UI source is allowed to use current unverified package behavior as a
stable contract.

If `apps/web/package.json` adds a new workspace importer or dependency not present
in the accepted first lock, the sequence is:

1. this web worker authors and statically reviews the final importer/manifest
   under `apps/web/**`;
2. a fresh reviewer accepts and terminalizes this exact web source/importer cell;
3. the separately owned `local:DW-M1-FIXTURE-API-SDK-CONTRACT-001` terminalizes
   the generated client and SDK mapping independently;
4. `local:DW-M1-WEB-LOCK-EXTENSION-001` consumes both terminal cells and changes
   only `pnpm-lock.yaml`; all manifests remain byte-identical; and
5. `local:DW-M1-WEB-TS-REVERIFY-001` runs the complete frozen
   packages/generated/adapter/web and browser proof.

There is no mid-plan “accepted importer” dependency. This whole cell is terminal
before the lock extension starts, so the mechanically enforced DAG is acyclic.

### Runtime capability fallbacks

MDA, Fleet, live streams, HITL submission, attachments, plan enforcement,
research/coding tools, schedules, PWA, push, and desktop rows use
unavailable/gated fixtures. Their absence never blocks this shell. The harness
does not construct a request for any optional row.

## Interfaces and invariants

### Intended route/composition layout

```text
apps/web/
  .gitignore          # includes .browser-cache/
  AGENTS.md
  README.md
  package.json
  next.config.*
  tsconfig.json
  src/
    app/
      layout.tsx
      page.tsx
      tasks/page.tsx
      approvals/page.tsx
      agents/page.tsx
      schedules/page.tsx
      activity/page.tsx
      settings/page.tsx
      not-found.tsx
    shell/
      app-shell.tsx
      primary-navigation.tsx
      mobile-navigation.tsx
      context-surface.tsx
      demo-marker.tsx
      focus-manager.tsx
    harness/
      fixture-repository.ts
      fixture-scenarios.ts
      no-network.ts
      harness-provider.tsx
    product-demo/
      integration.tsx
    styles/
      app.css
  scripts/
    browser-proof.mjs
    harness-reset.mjs
  tests/
  evidence/DW-M1-WEB-SHELL-HARNESS/
```

Names may be refined inside `apps/web`, but route ownership, harness isolation,
and package boundaries must remain obvious and tested.

`app-shell.tsx` consumes one stable integration component exported by
`src/product-demo/integration.tsx`. In this shell cell that component is a
no-request, disabled seam which returns typed `unavailable` unless the explicit
`ui-harness` provider is selected. The later full product-demo plan alone may
replace files under `src/product-demo/**` with its API-backed provider and marker;
it must not edit the accepted root layout, routes, or shell to splice itself in.
This pre-owned seam prevents the integration cell from broadening its paths or
creating a new importer.

### Shell contract

```text
mode = "ui-harness"
destinations = tasks | approvals | agents | schedules | activity
utility = settings
connectivity = online | offline | reconnecting
freshness = current | stale
capability = available | unavailable | gated | permission-denied | unknown
view = loading | empty | partial | error | success | cancelled
```

- `mode` is selected once at the application composition root and cannot change
  because a repository operation fails.
- The visible marker is present in every route, modal/sheet context, screenshot,
  and narrow viewport. It is text plus icon and not dismissible.
- Synthetic identity uses stable `fx_`-prefixed values and contains no endpoint,
  credential, repository, customer, or real actor.
- Presentational components receive normalized props/callbacks. No component
  imports fixtures, constructs URLs, calls `fetch`, or decides authorization.
- `apps/web` imports only public `@deepwork/domain`, `@deepwork/sdk`, and
  `@deepwork/ui` exports. The harness implements browser-local ports at the app
  composition root; `packages/ui` never imports the harness or SDK.
- Status fixtures do not advertise live-provider support. Any `available` value
  is labelled simulated fixture evidence; external/gated capabilities remain
  unavailable with reasons.

### No-network harness

The harness stores only its selected scenario, logical fixture step, and
non-sensitive layout preference under a versioned
`deepwork:ui-harness:*` browser key. It registers no service worker and writes no
cookie, IndexedDB provider cache, credential, cursor, or outbound intent.

Tests install fail-closed guards for `fetch`, `XMLHttpRequest`, `WebSocket`,
`EventSource`, `navigator.sendBeacon`, and service-worker registration before
application code. Browser proof permits only the loopback document and static
asset requests needed to load the local app. Any application/API/external request
fails the test and records method plus sanitized destination class.

### Exact browser-proof lifecycle

`apps/web/package.json` pins `browser-proof` to
`node scripts/browser-proof.mjs` and `harness-reset` to
`node scripts/harness-reset.mjs`. Both accept only the arguments shown in
validation. `browser-proof` starts the already-built app in a child process group
on `127.0.0.1:43120`, refuses a pre-bound port, waits for readiness, launches the
accepted cached browser, runs the route/state/viewport/accessibility matrix,
writes bounded sanitized evidence, and always terminates browser/server groups.
`harness-reset` starts the same build, clears only `deepwork:ui-harness:*` in that
exact origin, proves cookies/IndexedDB/Cache Storage/service workers are absent,
writes its reset receipt, and performs the same cleanup. Either runner fails if
the port, child process group, or browser profile survives.

### State matrix

| State fixture | Required shell behavior | Recovery/transition |
|---|---|---|
| Initial loading | Stable landmarks/skeletons; marker already visible; no guessed actor | Resolve selected fixture |
| Empty | Heading, explanation, one safe browser-local action | Reset/select fixture |
| Partial | Healthy synthetic content retained; affected source named | Retry/select state |
| Error | Region-level alert, safe detail, focusable retry | Retry/reset |
| Offline cold | Shell and explanation only; no credential validity claim | Select online fixture |
| Offline warm | Bounded synthetic last-known content, timestamp, read-only | Reconnect fixture; no replay |
| Permission denied | Preserve allowed navigation; explain missing permission | Change fixture/source |
| Stale | Keep content and timestamp; destructive/approval controls disabled | Refresh fixture |
| Reconnecting | Preserve content, route, scroll, and focus; bounded status | Current or full-reset fixture |
| Cancelled | Text/icon terminal state from explicit fixture only | Inspect/retry fixture |
| Success | Explicit synthetic result and provenance | Navigate/reset |
| Capability unavailable | Omit/disable action with safe reason | Select capable simulated row |
| Capability unknown/gated | No guessed action/request | Explain contract gate |
| UI harness active | Persistent limitations marker on every route | Start separate product demo externally |
| Narrow/mobile | Bottom navigation plus labelled More/account; sheets restore focus | Preserve route/state across resize |
| Reduced motion | Remove nonessential transition/pulse/scroll animation | Information unchanged |
| Forced colors/high contrast | System colors preserve boundaries/focus/status text | Actions remain operable |
| 200% text / 400% zoom | Reflow without page-level horizontal scroll or clipped action | Document order preserved |
| Virtual keyboard/safe area | Focused control remains visible; content scrolls | Draft/state retained |
| Route not found | Accessible in-shell error and safe Tasks link | Return to allowed destination |

## Milestones

### Milestone 1 — Establish the importer and explicit harness boundary

Author `apps/web` manifest/config, route skeleton, browser-local repository, and
no-request guards against the exact accepted package interfaces.

Acceptance:

- `apps/web` imports public package entry points only;
- no raw network/service-worker/provider code exists;
- the persistent marker is part of root layout;
- Next config emits deterministic standalone output for the later offline
  acceptance peer; build proof records its inventory and no runtime download;
- importer candidate is committed and independently reviewed before any root lock
  extension.
- app-local ignore rules reserve `apps/web/.browser-cache/` for the later pinned,
  pre-existing product-demo browser runtime; this shell does not download or use
  it.

### Milestone 2 — Compose the five-destination responsive shell

Implement semantic desktop/tablet/phone navigation and the Settings utility
route using shared tokens.

Acceptance:

- all primary/utility destinations are reachable within the stated action count;
- 320px, text zoom, forced colors, reduced motion, keyboard order, skip link,
  sheet modality, and focus restoration have deterministic tests;
- no app-specific token duplicates the shared token source.

### Milestone 3 — Cover the complete bounded state matrix

Add deterministic fixtures and state surfaces for every row above.

Acceptance:

- state selection is browser-local, resettable, and visible;
- fixture/live/UI-harness proof levels cannot be confused;
- unavailable/gated optional rows require no external dependency;
- state changes do not steal focus or flood announcements.

### Milestone 4 — Terminal static source/importer handoff

Commit the complete web source, manifest, tests, proof runners, and disabled
product-demo seam; obtain independent source/architecture/product/security
review; and terminalize this whole cell before any lock extension begins.

Acceptance:

- root/lock/package-source/generated/adapter changes are absent;
- no package, build, test, server, or browser command ran in this cell;
- static architecture/source review confirms the final manifest, scripts,
  public imports, no-request guard, persistent marker, state matrix, and
  responsive/a11y assertions are present;
- exact terminal source SHA and independent verdict are handed to
  `local:DW-M1-WEB-LOCK-EXTENSION-001`;
- executable/browser acceptance remains explicitly pending
  `local:DW-M1-WEB-TS-REVERIFY-001`; and
- reviewers record contribution-only scope and zero E2E/live completion.

## Progress

- [x] 2026-07-23 AEST — Drafted against canonical design/frontend/accessibility
  contracts and current package source; prepared for independent plan review.
- [ ] 2026-07-23 AEST — Exact terminal TypeScript verification dependency
  accepted.
- [ ] 2026-07-23 AEST — Shell, state matrix, browser-local guards, tests, and
  runners authored without package execution.
- [ ] 2026-07-23 AEST — Static source/importer candidate accepted as this cell's
  terminal result and handed to the web lock owner.
- [ ] 2026-07-23 AEST — Downstream lock/reverification remains separately owned
  and unclaimed by this cell.

## Surprises & Discoveries

- 2026-07-23 AEST — `apps/web` is absent while package seeds already exist.
  Evidence: base file inventory. Consequence: the plan establishes a new app
  composition root without modifying packages or root ownership.
- 2026-07-23 AEST — The current TS candidate is rework-required and there is no
  shared lock. Consequence: plan review can proceed, but build claims cannot.
- 2026-07-23 AEST — The accepted prototype's Interrupt/Resume control is local
  simulated state. Evidence: `docs/FRONTEND.md`. Consequence: this shell uses
  unavailable/gated state and makes no runtime-control claim.
- 2026-07-23 AEST — `AC-DW-QUAL-001-05` is a release-wide manual accessibility
  journey. Consequence: this plan claims a bounded shell contribution only.
- 2026-07-23 AEST — Review found that a mid-plan importer handoff cannot satisfy
  the repository's terminal-dependency validator. Consequence: this entire cell
  now ends at independently accepted static source/importer; lock and executable
  browser proof are two later cells.

## Decision Log

- 2026-07-23 AEST — Decision: five primary destinations and Settings utility
  route. Rationale: `DEC-007` and canonical frontend architecture. Consequence:
  prototype-only destinations are not silently promoted.
- 2026-07-23 AEST — Decision: persistent `Demo data · UI harness` disclosure.
  Rationale: browser-local state cannot prove services/persistence. Consequence:
  every visual artifact carries its proof tier.
- 2026-07-23 AEST — Decision: no silent demo/live fallback. Rationale: failures
  must remain honest. Consequence: mode selection is immutable for the session.
- 2026-07-23 AEST — Decision: consume existing shared tokens but do not edit UI.
  Rationale: this plan governs `apps/web/**` only. Consequence: missing token needs
  become reviewed follow-ups, not local literals.
- 2026-07-23 AEST — Decision: lock extension and full re-verification are separate
  sequential cells. Rationale: root/lock ownership and terminal dependency form
  must remain acyclic. Consequence: the web author terminalizes the complete
  static source/importer without executing it; the lock owner consumes that
  terminal result, and the re-verifier alone owns executable/browser evidence.

## Detailed implementation approach

1. Verify branch/base/cleanliness and exact terminal TS verification commit.
2. Create `apps/web` guidance, manifest, strict config, and route skeleton using
   only accepted public package exports.
3. Add root-layout semantics, persistent harness marker, primary/utility
   navigation, responsive sheets/More, skip/focus manager, and shared token CSS
   imports.
4. Implement an injected browser-local repository and deterministic scenario
   catalog inside `apps/web/src/harness`; add no product transport.
5. Add the disabled `src/product-demo/integration.tsx` composition seam; prove it
   returns typed unavailable and issues no request in this cell.
6. Add fail-closed request/service-worker guards before application composition.
7. Add destination fixture views and every state-matrix row using normalized
   capability/view values.
8. Perform only install-free static source/manifest/script/architecture review.
9. Commit the complete source/importer candidate and stop for independent review.
10. After acceptance, terminalize this cell and hand the exact SHA to the
    lock-extension owner. Do not run package or browser commands here.

## Validation and proof

### Plan-authoring candidate

```text
test "$(git branch --show-current)" = "external/planning/w1-product-demo-cells"
test "$(git rev-parse HEAD^)" = "9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2"
python3 -B tools/docs/generate.py --check
python3 -B tools/docs/check.py
git diff --check 9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2 HEAD
git diff --name-only 9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2 HEAD
test -z "$(git status --porcelain)"
```

Before the reviewed/index transition, docs check is expected to exit `1` for this
file with the following nine draft/dependency diagnostics:

1. active ExecPlan is not indexed;
2. unsupported active ExecPlan status `draft`;
3. unknown dependency `local:DW-M1-TS-VERIFY-001` until its active plan exists;
4. independent non-owner reviewer metadata missing;
5. completed gate reviewer metadata missing;
6. `reviewed_at` is not a date;
7. `gate_reviewed_at` is not a date;
8. `last_verified_commit` is not an existing full commit; and
9. `gate_review_status` is not `reviewed-with-gates`.

### Static importer candidate before lock extension

```text
dispatch_commit="<exact reviewed 40-character dispatch commit>"
web_candidate="$(git rev-parse HEAD)"
test "${#dispatch_commit}" -eq 40
git cat-file -e "${dispatch_commit}^{commit}"
test "${#web_candidate}" -eq 40
git cat-file -e "${web_candidate}^{commit}"
python3 tools/architecture/check.py --root . --graph tools/architecture/graph.json
python3 -B tools/docs/generate.py --check
git diff --check "$dispatch_commit" "$web_candidate"
git diff --name-only "$dispatch_commit" "$web_candidate"
test -z "$(git status --porcelain)"
```

### Downstream executable proof contract

This cell must not execute the following proof. It freezes the script names and
assertions so `local:DW-M1-WEB-TS-REVERIFY-001` can run them after
`local:DW-M1-WEB-LOCK-EXTENSION-001` without changing source:

- route/viewport matrix at 320, 375, 768, and desktop reference widths;
- 200% text and 400% reflow observations;
- keyboard/skip/focus/sheet restoration log;
- reduced-motion and forced-colors screenshots;
- automated accessibility report with zero serious violations;
- console summary with zero runtime/hydration errors;
- request summary with zero API/external/application requests after initial local
  bundle loading; and
- explicit `AC-DW-QUAL-001-05 contribution only`, no product-demo/live proof, and
  zero `E2E-V1-*` completion.

If the re-verifier discovers a missing or failing script, it returns the exact
failure to this source owner. It may not repair source or weaken an assertion.
Any successor source commit requires a successor lock extension and complete
re-verification.

## Idempotence, rollback, and recovery

- Scenario selection and reset are deterministic browser-local operations.
  Reset clears only the versioned harness key and reconstructs fixed synthetic
  state.
- No sensitive mutation is queued. Offline/reconnect fixtures change local
  presentation state only and are never replayed to a service.
- A failed live/API path cannot route to this harness because no live/API
  repository exists in the cell.
- This cell creates no build/browser state, so interruption leaves only tracked
  source changes inside governed paths.
- If the downstream lock or re-verification fails, preserve this terminal static
  source commit and return the exact failure. Do not weaken scripts, modify the
  source under a proof-only cell, or hand-edit the lock.
- Rollback input is exact `web_candidate` plus its reviewed parent. The
  Coordinator first rolls back any dependent re-verification outcome and web lock
  commit, confirms no web process/browser profile remains from those later
  cells, verifies this candidate diff is only `apps/web/**` plus this plan, then
  creates `git revert --no-edit "$web_candidate"`. A conflict or postcondition
  failure leaves rollback blocked with exact evidence; no root/lock file is
  hand-edited and no backend/external state exists.

## Rollout and handoff

There is no live rollout. The browser-local harness may be used for component and
route review only after its explicit marker and no-request guard are accepted.
The handoff to the Coordinator includes:

- exact terminal TS verification input SHA;
- exact web candidate SHA and changed files;
- static architecture/source/manifest/script review results;
- independent product/UX, accessibility, frontend architecture, security, and DX
  verdicts; and
- explicit statement that package/browser execution, API, product-demo, Postgres,
  worker, object, telemetry, live provider, PWA/push, root/lock, generated/index,
  and E2E completion remain outside this cell.

The later product-demo integration consumes the accepted shell and replaces only
the app-level repository injection through its own exact sequential paths. It
cannot cite this harness as API-backed proof.

## Outcomes & Retrospective

Pending implementation. Completion must record whether every route/state and
responsive/accessibility invariant passed, identify accepted TS/lock inputs, list
any deferred token or component need, and preserve the distinction between
browser-local shell evidence, full product-demo evidence, and live-provider
evidence. `AC-DW-SURF-001-01` and `AC-DW-QUAL-001-05` remain contribution-only;
all `E2E-V1-*` rows remain incomplete.
