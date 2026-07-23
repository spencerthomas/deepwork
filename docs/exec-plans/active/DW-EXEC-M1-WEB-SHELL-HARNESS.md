---
exec_plan_id: DW-EXEC-M1-WEB-SHELL-HARNESS
title: Responsive browser-local web shell harness
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
dependencies: [DW-EXEC-M1-TS-PACKAGES-SCAFFOLD, local:DW-M1-TS-LOCK-001]
blockers: []
---

# Responsive browser-local web shell harness

## Purpose and observable result

Create `apps/web` as the accessible, responsive composition root for Deep Work's
five primary destinations—Tasks, Approvals, Agents, Schedules, and Activity—plus
the Settings utility route. A contributor can open an unmistakable browser-local
UI harness, select deterministic presentation states, navigate from 320 CSS
pixels through desktop, and verify keyboard, focus, reduced-motion, zoom/reflow,
forced-colors, and mobile navigation behavior without an API, worker, Postgres,
object service, provider, credential, or application request.

The shell permanently marks the session as `Demo data · UI harness` and explains
that persistence, worker/recovery, service failures, and full integration are not
under test. It never claims API-backed product-demo proof or live-provider proof.

This cell contributes the shell slices of `AC-DW-FND-002-01`,
`AC-DW-FND-002-02`, `AC-DW-FND-002-03`, `AC-DW-FND-002-05`, and
`AC-DW-FND-002-06`. It contributes responsive component/shell evidence only to
`AC-DW-SURF-001-01` and `AC-DW-QUAL-001-05`; it does not complete either scenario.
It completes zero `E2E-V1-*` scenarios.

Status is **draft, prepared for independent review**. Planning and static review
are ready now. Source execution starts only from accepted TypeScript package
interfaces, and dependency-backed install/build/test proof waits for the
Coordinator-owned shared TypeScript lock.

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
source, first-lock, or executable-verification commit exists for this plan yet.
The shell plan may be reviewed now, but no implementation dispatch can infer
acceptance from the current checkout.

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
- No-request guards, route/component tests, accessibility tests, responsive
  browser proof, screenshot matrix, and network summary.

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
- The implementation may run the local Next.js process only after the shared
  lock cell is terminal and within its later authorized implementation task.
- Browser tests may load the loopback web origin. After the initial document and
  same-origin static assets, `fetch`, XHR, WebSocket, EventSource,
  `sendBeacon`, service-worker registration, and external navigation must record
  zero attempts.
- Product/UX, accessibility, frontend architecture, security, and developer-
  experience review are required. The author cannot approve the plan or result.

## Authoritative sources and prerequisites

### Persistent dependency and lock sequence

| Stable cell | Terminal evidence required | Current state |
|---|---|---|
| `DW-EXEC-M1-TS-PACKAGES-SCAFFOLD` / `local:DW-M1-TS-SCAFFOLD` | Exact independently accepted TS source commit with public domain/UI boundaries | Blocked; candidate `1bf66e1` is `REWORK REQUIRED`. |
| `local:DW-M1-TS-LOCK-001` | Coordinator-owned first `pnpm-lock.yaml`, offline frozen-install/no-drift proof, exact importer inventory | Not yet represented by an active ExecPlan in this checkout; execution/build proof is blocked. |

Planning review requires neither cell to be terminal. Implementation dispatch
requires both exact accepted commits. No UI source is allowed to use current
unverified package behavior as a stable contract.

If `apps/web/package.json` adds a new workspace importer or dependency not present
in the accepted first lock, the sequence is:

1. the web worker authors and statically reviews the importer under `apps/web/**`;
2. a fresh reviewer accepts the exact web importer/source candidate;
3. the Coordinator alone runs a separately reviewed lock-extension cell,
   `local:DW-M1-WEB-LOCK-EXTENSION-001`, changing only approved root/lock paths;
4. a separate `local:DW-M1-WEB-TS-REVERIFY-001` cell reruns the complete frozen
   TypeScript format/lint/type/test/build/package-consumer matrix for domain, SDK,
   UI, and web at the exact extended lock; and
5. only that terminal re-verification may support final web-shell acceptance or
   the later product-demo integration.

The web plan does not depend on its own terminal state, and the lock extension
depends only on an exact accepted importer candidate—not on a completed web
build—so the lifecycle is acyclic.

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

### Milestone 4 — Lock extension and full executable verification

If the web importer changes shared dependency resolution, stop the author lane,
hand the exact accepted importer commit to the Coordinator, wait for the lock
extension, then run the full TS re-verification cell.

Acceptance:

- root/lock changes are absent from the web candidate;
- accepted lock extension names the exact web importer commit;
- full TS re-verification passes at one frozen lock before final web review.

### Milestone 5 — Browser evidence and independent handoff

Run route/component/a11y/responsive/no-request/build proof and hand the exact
clean candidate to independent reviewers.

Acceptance:

- screenshot/state matrix identifies `UI harness`;
- request summary shows zero application/API/external requests;
- console has no hydration/accessibility/runtime error;
- changed paths are exactly `apps/web/**` and this plan;
- reviewers record contribution-only scope and zero E2E completion.

## Progress

- [x] 2026-07-23 AEST — Drafted against canonical design/frontend/accessibility
  contracts and current package source; prepared for independent plan review.
- [ ] 2026-07-23 AEST — Exact TS source and first-lock dependencies accepted.
- [ ] 2026-07-23 AEST — Importer candidate accepted and any required
  coordinator-owned lock extension completed.
- [ ] 2026-07-23 AEST — Shell, state matrix, and browser-local guards implemented.
- [ ] 2026-07-23 AEST — Full TypeScript and browser verification accepted.
- [ ] 2026-07-23 AEST — Fresh independent implementation review and Coordinator
  handoff complete.

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
  coordinator cells. Rationale: root/lock ownership and importer dependency form
  must remain acyclic. Consequence: the web author stops at an accepted importer
  candidate before the Coordinator resolves dependencies.

## Detailed implementation approach

1. Verify branch/base/cleanliness and exact accepted TS source/lock commits.
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
8. Commit the importer/source candidate and stop for independent review.
9. If required, hand it to the Coordinator's lock-extension and full TS
   re-verification cells; make no root edit locally.
10. Run browser matrix, console/request inspection, accessibility automation and
   manual keyboard/focus checks; retain sanitized evidence and stop for review.

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
3. unknown dependency `local:DW-M1-TS-LOCK-001` until its active plan exists;
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

### Executable proof after accepted lock/re-verification

The exact package scripts are owned by the accepted web manifest. At minimum:

```text
reviewed_lock_commit="<exact reviewed 40-character lock/reverification commit>"
test "${#reviewed_lock_commit}" -eq 40
git cat-file -e "${reviewed_lock_commit}^{commit}"
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter ./apps/web format-check
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter ./apps/web lint
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter ./apps/web typecheck
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter ./apps/web test
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter ./apps/web build
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile format-check
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile lint
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile typecheck
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile test
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile build
ui_evidence_dir="apps/web/evidence/DW-M1-WEB-SHELL-HARNESS"
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter ./apps/web browser-proof -- --host 127.0.0.1 --port 43120 --evidence-dir "$ui_evidence_dir" --viewports 320x800,375x812,768x1024,1440x900 --text-zoom 200 --browser-zoom 400 --require-keyboard-focus --require-reduced-motion --require-forced-colors --require-automated-a11y --require-no-application-requests
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter ./apps/web harness-reset -- --host 127.0.0.1 --port 43120 --storage-prefix deepwork:ui-harness: --evidence-dir "$ui_evidence_dir"
python3 -B -c 'import json,pathlib; d=json.loads(pathlib.Path("apps/web/evidence/DW-M1-WEB-SHELL-HARNESS/browser-proof.json").read_text()); assert d["status"]=="passed"; assert d["application_requests"]==0; assert d["serious_a11y_violations"]==0; assert d["server_process_absent"] and d["browser_process_absent"]'
python3 -B -c 'import json,pathlib; d=json.loads(pathlib.Path("apps/web/evidence/DW-M1-WEB-SHELL-HARNESS/reset.json").read_text()); assert d["status"]=="passed"; assert d["remaining_harness_keys"]==0; assert d["service_workers"]==0; assert d["server_process_absent"] and d["browser_process_absent"]'
python3 tools/architecture/check.py --root . --graph tools/architecture/graph.json --fixtures internal/fixtures/architecture --verify-negative
python3 -B tools/docs/generate.py --check
python3 -B tools/docs/check.py
git diff --check "$reviewed_lock_commit" HEAD
git diff --name-only "$reviewed_lock_commit" HEAD
test -z "$(git status --porcelain)"
```

Browser proof must retain:

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

## Idempotence, rollback, and recovery

- Scenario selection and reset are deterministic browser-local operations.
  Reset clears only the versioned harness key and reconstructs fixed synthetic
  state.
- No sensitive mutation is queued. Offline/reconnect fixtures change local
  presentation state only and are never replayed to a service.
- A failed live/API path cannot route to this harness because no live/API
  repository exists in the cell.
- Build/test interruption leaves no root or lock mutation. Package-local caches
  are removable through the reviewed package command; broad cleanup is forbidden.
- If the Coordinator cannot produce a frozen lock or full TS verification fails,
  retain the accepted static importer candidate, keep the plan active/non-ready,
  and report the exact blocker. Do not weaken scripts or hand-edit the lock.
- Rollback input is exact `web_candidate` plus its reviewed parent. With the local
  web process stopped, the Coordinator first runs the accepted
  `COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter ./apps/web
  harness-reset -- --host 127.0.0.1 --port 43120 --storage-prefix
  deepwork:ui-harness: --evidence-dir
  apps/web/evidence/DW-M1-WEB-SHELL-HARNESS` command against the versioned
  `deepwork:ui-harness:*` origin storage, verifies no service worker or other app
  storage remains, confirms the candidate diff is only `apps/web/**` plus this
  plan, and creates `git revert --no-edit "$web_candidate"`. It then reruns the
  frozen full TS verification, architecture/docs checks, and clean-status check
  at the reviewed lock. A conflict, storage cleanup failure, or verification
  failure leaves the rollback blocked with exact evidence; no root/lock file is
  hand-edited and no backend/external state exists.

## Rollout and handoff

There is no live rollout. The browser-local harness may be used for component and
route review only after its explicit marker and no-request guard are accepted.
The handoff to the Coordinator includes:

- exact TS source, first-lock, lock-extension (if any), and re-verification SHAs;
- exact web candidate SHA and changed files;
- package/browser commands and results;
- screenshot, a11y, console, and request summaries;
- independent product/UX, accessibility, frontend architecture, security, and DX
  verdicts; and
- explicit statement that API, product-demo, Postgres, worker, object, telemetry,
  live provider, PWA/push, root/lock, generated/index, and E2E completion remain
  outside this cell.

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
