---
title: Deep Work v1 release scorecard
status: active
last_reviewed: 2026-08-03
owners: [product, quality, release]
source_scenarios: docs/product-specs/acceptance-scenarios.md
---

# Deep Work v1 release scorecard

This is the live release truth for the twelve canonical `E2E-V1-*` scenarios.
It deliberately separates four questions that previous status prose blurred:

- **Implemented** — every behavior required by the release story exists.
- **Browser-proven** — the complete story has current retained browser evidence.
- **Hosted-proven** — the complete story passed against the configured hosted
  application, without fixture fallback.
- **Release-accepted** — the named release owner accepted the retained proof.

`Partial` is not a passing state. A scenario becomes `Yes` only when its entire
story and required proof packet are present. Hosted and release evidence cannot be
inferred from local fixtures, screenshots, unit tests, configuration, or a green
build.

## Current scorecard

Evidence snapshot: recovery branch `product/golden-journey-recovery`, base
`c7e0ea6cd2fce6187d96f0da06957320641c4a4e`, product journey through
`b7269091b1f1881b42235d634379a6916e349ede`, blocking browser gates through
`48e21024a0bf9691c2d8a9531be7f210e4547b45`, security fail-closed hardening
through `36dad6d0833c479df808c0a69b7ab8022be5d5ed`, and contributor-gate repairs
through `9fd1fc143fee769954869d36f0642975b29f564e`. Adversarial-review fixes are
pinned at `265da2a1f2cfb53a9ce0ad02c1f3169881801b01`. Durable completed-task
restart/reopen proof is pinned at `8b4b8c9ca404e9e08369440bce4a88fed24d964d`,
and blocking assistive-interaction proof is pinned at
`16d79c2268132e9a6f737b1b543e33d29b46e806`. The bounded 1,000-task inbox and
1,001-event task-detail browser performance slice is pinned at
`2085a909dcec575beaa8fbea8fdb308eef90731e` (bounded-history feature commit
`361ccaf6cb0000b3953075b42650ddde3c40743b` and review fix
`770f923d57cc8d9a9d5465b34f75b65103597033`). Active-stream recovery and its
four-case browser gate are pinned at `9dfd3f0fa0c295e942765c157d7698c671c3c683`,
and two-device stale-approval prevention and reconciliation are pinned at
`dbde97738c2159b720c7f9abe1256b00603936f0`, reviewed 2026-08-03 PDT.

| Program scenario | Implemented | Browser-proven | Hosted-proven | Release-accepted | Current evidence and exact gap |
|---|---|---|---|---|---|
| `E2E-V1-01-FIRST-VALUE` | Partial | Partial | No | No | Branded API-key sign-in, truthful fixture origin, compose, plan approval, progress, useful result, derived exports, evidence/trace and reopen pass in `tests/e2e/demo-task-journey.spec.ts`. The real-agent path retains the selected `agentId`, including the default agent with its workspace prompt, and hosted acceptance actively chooses a registry agent; that protected hosted journey has not run. |
| `E2E-V1-02-TRUTHFUL-RUNTIME` | Partial | Partial | No | No | The real-mode chooser is registry-backed, blocks on registry failure, and retains the chosen agent identity through detail, trace and reopen; fixture mode declares that no registry exists. The required classic/MDA/Fleet/unsupported account matrix and negative request ledger are not proven. |
| `E2E-V1-03-DURABLE-CORE` | Partial | Partial | No | No | `make test-recovery` creates and completes a real API-backed fixture task, stops the API process, restarts it against the same test-owned SQLite database, and proves a fresh browser context reopens the exact task/result/evidence/trace/events/files without duplicate IDs or a second task. The complete Postgres application-job/draft/notification process-kill, worker/outbox and once-only convergence story is not implemented or proven. |
| `E2E-V1-04-CREDENTIAL-BOUNDARY` | Partial | Partial | No | No | Access-key login stays on the same-origin server boundary and returns no script-readable session token. A blocking synthetic-canary journey inspects the login response and scans browser storage, cache/service-worker state, public API/schema responses, built browser assets and retained test artifacts. The former PAT/token-in-sandbox fallback has been removed and private GitHub is explicitly `proxy-unavailable`. A real private-source/GitHub proxy operation plus desktop bridge, sandbox and telemetry proof remain open. |
| `E2E-V1-05-RECONNECT` | Partial | Partial | No | No | `make test-recovery` proves a completed task remains visible during an intentional API outage, a re-run fails without changing the original task, and the same persisted task reopens after API restart and fresh sign-in. Native browser EventSource cases now prove active-task disconnect recovery, one bounded authoritative hydration per disconnect episode, late-read rollback protection, duplicate-event suppression, continued retry after a timed-out hydration, useful last-known state during failure, and honest recovered/unconfirmed status. API contract tests separately cover replay cursor handling. Replica loss, replay expiry, worker restart, hosted execution and release acceptance remain unproven. |
| `E2E-V1-06-ORDERED-APPROVAL` | Partial | Partial | No | No | One real plan decision passes at desktop and phone widths in the golden journey. Three two-browser cases now prove that a stale phone task or inbox card re-fetches before mutation and sends no decision, and that the narrower race where another device wins after preflight is rejected by the real API, reconciled visibly, focused for keyboard/assistive use, and retains exactly one `decision.recorded` audit event. Synchronous per-task guards cover task-card, inbox-button and keyboard entry points; API contract tests separately prove identical-decision idempotency and conflicting-decision rejection. The current accepted API is explicitly a single bounded interrupt with no `actionRequests[]`/`reviewConfigs[]`, edit decision, expected batch version, or ordered decisions vector. Repeated-name multi-action editing therefore remains unimplemented and blocked on `SPIKE-HITL-001`; hosted and release acceptance remain open. |
| `E2E-V1-07-CODING-DRAFT-PR` | No | No | No | No | Repository authorization, sandbox provenance, exact-SHA review, draft PR retry, authoritative CI and phone merge review are outside the delivered recovery slice. |
| `E2E-V1-08-RESPONSIVE-ACCESS` | Partial | Partial | No | No | Blocking 1440x1000 and 390x844 screenshots cover all 12 designed route references and the golden journey. `tests/e2e/assistive-access.spec.ts` now completes the API-backed review journey by keyboard; proves truthful lifecycle announcements and completion focus; exercises Run-panel arrow tabs and More focus entry/trap/Escape/restore/replacement-modal focus; retains computed reduced-motion and forced-colors checks; and completes compose, approve, Files inspection and reopen in a fresh 320x800 touch context with no horizontal overflow and measured 24px targets. The full ten-test browser gate, including phone-width stale-decision focus recovery, and light/dark WCAG 2.2 A/AA scans pass. Actual 200% browser zoom, VoiceOver/NVDA/JAWS, Switch Control, a real phone and Windows High Contrast remain unaccepted, so this scenario stays Partial. |
| `E2E-V1-09-SECURITY-RECOVERY` | Partial | No | No | No | Narrow credential, endpoint-shape, loopback, CORS, stale-mutation and SQLite recovery tests cover individual boundaries. There is no tenant-aware implementation or accepted tenant/SSRF/redirect/webhook/object/sandbox/updater abuse pack, restore comparison, or zero-unauthorized-effect proof. |
| `E2E-V1-10-PERFORMANCE` | Partial | Partial | No | No | `make test-performance` runs versioned synthetic 1,000-task inbox and 1,001-event task-detail profiles against the production web bundle at 1440x1000 and 390x844. Inbox paging caps the DOM at 50 rows while full-set search and exact-result keyboard opening remain usable; the latest local search p75 was 27.79 ms desktop and 27.05 ms phone against the provisional 200 ms budget. The task thread keeps at most 100 recent/active-review items, Stream keeps at most 100 rows, stable cursor-anchored history does not shift under appends, and bulk replay proves all 1,001 ordered event IDs across 11 pages from latest to oldest and back while result, Sources, Files and Details remain inspectable (226.27 ms desktop; 232.67 ms phone against 4,000 ms). A separate EventSource-boundary profile dispatches every event in its own browser task, measures through the committed result and next paint, validates the exact credentialed subscription, retains all 1,001 events, and closes terminal replay after reopen. It completed in 2,490.10 ms desktop and 2,459.60 ms phone against 5,000 ms, with maximum timer lag 31.20 ms and 14.70 ms and no observed greater-than-50 ms Long Task against 100 ms safety ceilings. The six-case gate is CI-blocking. This remains short synthetic local delivery proof, not native network chunking/backpressure, long-duration retained-memory/frame scaling, multi-source, large subagent/file/diff, reconnect, reference-device, hosted-load or manual-AT qualification. |
| `E2E-V1-11-CONTRIBUTOR` | Partial | No | No | No | The supported root `make check` is green: architecture enforcement, formatting, lint, type checks, 74 domain tests, 60 SDK tests, 32 UI tests, 307 web tests, 314 API tests plus 77 API contract tests, 100 agent tests and reproducible package builds all pass. Two independent clean-machine contributor runs, intentional drift repair and license/trademark proof remain open. |
| `E2E-V1-12-OPERATIONAL-RELEASE` | Partial | No | No | No | The product renders retained event trace plus an explicit external-trace unavailable state, and the hosted journey is fail-closed. Staged promotion, migration/restore, failure injection, alert/runbook proof and rollback have not run. |

## Golden-journey recovery slice

The recovery slice is locally browser-proven at both product and visual layers
for the credential-free fixture source. The same UI and API contracts support the
real source, while the real-source choice and execution remain hosted-unproven:

1. branded sign-in/connect;
2. show the truthful fixture source locally, or choose a real registry agent in
   real-source mode and retain its identity on the task;
3. compose and dispatch;
4. review the proposed plan;
5. approve through the ordered decision contract;
6. observe live `Running` progress;
7. receive a useful result;
8. inspect evidence, clearly labelled browser-derived exports and retained/external
   trace truth; and
9. return to the inbox and reopen the same completed task.

The proof owners are `tests/e2e/demo-task-journey.spec.ts`,
`tests/e2e/assistive-access.spec.ts`, `tests/e2e/approval-race.spec.ts`,
`tests/recovery/durable-reopen.spec.ts`, and `tests/visual/product-journey.spec.ts`.
The recovery suite owns a generated access key and absolute temporary SQLite
database, strips ambient source/provider configuration from the API child, stops
and restarts that real process, and uses a fresh browser context for reopen. Its
route-controlled native EventSource cases additionally exercise two disconnect
episodes, failed retries, delayed and stale API snapshots, duplicate replay,
bounded hydration failure, resumed terminal progress and task-scoped recovery
feedback without substituting a mock subscription client. The visual suite verifies immutable hashes
for the accepted prototype commit recorded in
`tests/visual/reference/prototype/manifest.json`, maps all 12 route references to
current canonical captures, enforces reviewed perceptual deltas, and compares the
full-resolution screenshots under `tests/visual/expected/` in a pinned browser and
platform job.

## Blocking gates

| Gate | Command | Current state | What it can prove |
|---|---|---|---|
| Technical fixture journey | `make test-e2e-demo` | Passing locally: 10 browser tests | API-backed local product behavior, light/dark WCAG scans, keyboard and 320px touch completion, lifecycle/focus behavior, two-device stale-decision prevention and post-preflight conflict reconciliation, reduced motion, forced colors and the loopback network contract |
| Durable and reconnect recovery | `make test-recovery` | Passing locally: 4 browser cases; required by the main CI verification job | Real API stop/restart against test-owned SQLite plus active native-EventSource disconnect episodes, exactly-once hydration per episode, stale/late snapshot rejection, duplicate suppression, bounded failure and resumed terminal progress; not Postgres worker/replica, replay-expiry, or hosted recovery |
| Credential boundary | `make test-security-boundary` | Passing locally and required before hosted acceptance | Synthetic access-key canary absence from browser/public/retained artifacts plus fail-closed private-GitHub source policy |
| Route and journey visuals | `make test-visual` | Passing locally and required by the separate `visual-acceptance` CI job | Immutable prototype source, complete route mapping, desktop/phone screenshot contract, 320px reflow and golden-journey states |
| Inbox and long-stream performance | `make test-performance` | Six cases pass locally at desktop and phone widths and are required by the main CI verification job | Versioned synthetic 1,000-task and 1,001-event bulk/incremental profiles; maximum 50 inbox rows and 100 Stream rows; stable complete history traversal; result/source/file/detail inspection; post-render responsiveness, exact subscription and terminal-replay closure. Not native network/backpressure, long-duration memory/frame, accepted-device, hosted-load or manual-AT proof |
| Hosted golden journey | `make test-hosted` | Installed, fail-closed, not executed in this recovery | Real registry choice, non-fixture source, retained result and reopen only when `DEEPWORK_HOSTED_URL` and `DEEPWORK_E2E_ACCESS_KEY` are supplied by the protected `hosted-acceptance` environment |

The hosted column remains `No` until that protected job completes and its safe
failure screenshots are reviewed. Credential-bearing Playwright traces are never
retained. The release-accepted column remains `No` until the
scenario's complete proof packet is explicitly accepted; accepting this recovery
direction did not accept any v1 release scenario.
