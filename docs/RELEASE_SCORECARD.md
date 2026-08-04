---
title: Deep Work v1 release scorecard
status: active
last_reviewed: 2026-08-04
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
`dbde97738c2159b720c7f9abe1256b00603936f0`, with the reviewed scorecard state
at `f9bab6e02e40c113606776c3cdc3c75249a597d6`. Exact installed LangChain HITL
contract evidence is pinned at `8b1b7f5cfa23a5528b39a446337e1663379fe4b5`,
and the normalized ordered-review implementation plus independent review fixes are
pinned at `e11efe03fb75754639b20c71bbc18982586bfb60`, reviewed 2026-08-03 PDT.
The API-backed deterministic coding-to-draft-PR slice, including exact-revision,
sandbox-provenance, retry-reconciliation, phone review and reopen proof, is pinned
at `8acd3db9dce29ee9b8a20de5363b604315a17ca5`. Server-derived session identity,
tenant/workspace task ownership, scoped prompt settings and identity-partitioned
browser drafts are pinned at `2559cc1`, `6cef9cd`, `4b796b7` and `8a0e53e`;
their two-identity browser restart proof is pinned at `b803fcb`. Root toolchain
enforcement and its regression tests are pinned at `91a6875`. The authenticated,
operator-allowlisted classic source read check and its settings interaction are
pinned at `dea1c0c8e8c59556dbdd4ffbe9d81aee2460ed30`; its independent-review fixes
for mandatory authentication, tenant/workspace authority, server-owned target
resolution, evidence-qualified capability state, OpenAPI parity and bounded UI
lifecycle are pinned at `bde957234e27498a7e349968da6a0b99c1058e3e`.
The blocking OSS metadata, attribution, trademark-asset and workflow-pin audit is
pinned at `e383fddbc8a72eefd5ef326685c1a0622a28c42d`.
Verified stopped-application backup/restore for the paired local SQLite task and
settings stores is pinned at `369c24910acc68e7e2ccf913ae6c87ffad0b7043`.
The pinned official SDK's fail-closed no-redirect transport contract is locked at
`7dd365a401dbd55bae52ac30634aad03bac0ccce`.
Configured-runtime identity, the authenticated canonical runtime-status contract,
and the designed source-registry-backed Agents route are pinned at
`f24785eaa58433ca93a31f157bde93472d1dfd13`. The hosted golden-journey gate now
blocks fixture runtime, missing source capabilities, browser console errors,
failed API requests and non-success API responses at
`cbe50d1a59e39dfe6983da2a0d982c0cbe69c6ff`. The production-mode local
non-fixture journey, including graph-alias resolution to the configured assistant,
silent-stream reconciliation, browser authoritative refresh and exact task-route
acceptance, is pinned at `a326c84b6ecf0cf7c08e6d07735f5a96701626cb`.
The authenticated local SQLite application-job proof, including tenant/workspace
idempotency, concurrent API/worker first startup, separate-worker completion,
API restart/read-back, lease expiry recovery and bounded dead-letter behavior, is
pinned at `c28ef9b136307016600d2d84c031c96d46f4ea2c`.
The real local PostgreSQL/Alembic/outbox implementation and guarded integration
proof are pinned at `ef0bcc852ddae90c92a3144b16922c7d067799a7`: packaged
migrations round-trip and pass drift checks, job plus outbox insertion is atomic,
eight concurrent `SKIP LOCKED` workers claim uniquely, session scope remains
isolated, and a separate API/worker process cycle survives restart. The existing
v1 SQLite job response remains compatible and PostgreSQL durability is exposed by
the additive `/api/v1/durable-jobs` route.
The sealed local product-demo gate now runs the designed journey in two clean,
same-commit worktrees against separate real API, web, worker, PostgreSQL, object
and telemetry cells. Its retained receipt binds both execution commits, the
reviewed driver/browser blobs, browser artifacts and exact reservation release;
the driver alone can produce only `pending-receipt` evidence. This is local
credential-free proof and changes neither the hosted nor release-accepted column.

Authenticated task-create reconciliation is pinned at `30b9e64`, `4797081` and
`bb0d830`, with independent review fixes at `2daeaeb` and reconnect read
serialization at `52297c3`. The API now durably claims the scoped task before a
real source start, fingerprints pre-redaction input, and permits unrelated keys
to start concurrently. The browser persists one exact request before POST,
partitions it with an opaque tenant/workspace/actor scope, serializes tabs,
bounds half-open creates, reconciles lost responses after reload and API restart,
and blocks late navigation. Local proof covers desktop, phone, two-tab and
restart cases plus the uncertain-dispatch visual state. It does not prove an
external provider's own once-only semantics or any hosted execution.

| Program scenario | Implemented | Browser-proven | Hosted-proven | Release-accepted | Current evidence and exact gap |
|---|---|---|---|---|---|
| `E2E-V1-01-FIRST-VALUE` | Partial | Partial | No | No | Branded API-key sign-in, truthful fixture origin, compose, plan approval, progress, useful result, derived exports, evidence/trace and reopen pass in `tests/e2e/demo-task-journey.spec.ts`. The sealed dual-stack gate repeats the complete designed path in two concurrent API-backed cells, selects the immutable API registry agent, exercises the ordered review, retains task/run-bound evidence and reopens after API restart. The designed `/agents` route renders the exact source registry in provider order, retains source identity, marks the default agent, reports per-agent task activity and links management to workspace settings; API-mode empty/error states never fall back to invented fixture-era cards. Desktop and phone browser cases now lose both the initial create response and automatic reconciliation response, reload the locked composer, replay the exact key/body, and prove the task-ID delta contains one task; a two-tab case proves both tabs adopt that identity. A production-mode local non-fixture acceptance run proves the same path against the real local LangGraph Agent Server. Its model is a deterministic keyless stand-in, so none of this is provider-backed or hosted proof. The protected hosted journey has not run. |
| `E2E-V1-02-TRUTHFUL-RUNTIME` | Partial | Partial | No | No | The real-mode chooser and designed Agents route are registry-backed, block on registry failure, preserve provider order/default identity and retain the chosen agent through detail, trace and reopen. Browser-only fixture mode has no registry; the API-backed product-demo fixture runtime exposes one immutable selectable `deepwork-fixture-planner` registry record and retains its identity. Authenticated `GET /api/v1/runtime/status` identifies the configured `fixture`, `local-agent-server` or `classic-deployment` adapter and its mechanics without claiming a provider readiness check; the deprecated demo path is a guarded compatibility alias and `/health` remains process-only. Contract tests cover local and classic variants, authentication, fixed OpenAPI enums and external-provider differences. The local non-fixture journey proves graph-alias resolution to the real configured assistant UUID and authoritative task-state reconciliation when the Agent Server stream is silent. Hosted acceptance still requires a non-fixture `local-source` runtime with both task-loop and source capabilities available. `POST /api/v1/sources/probes` resolves one server-owned target only after session and tenant/workspace authorization and never accepts provider URLs or credentials from the browser. Provider invocation qualification, durable source registration, dynamic multi-registration task routing and the required classic/MDA/Fleet/unsupported account matrix remain open. |
| `E2E-V1-03-DURABLE-CORE` | Partial | Partial | No | No | `make test-recovery` creates and completes a real API-backed fixture task, stops the API process, restarts it against the same test-owned SQLite database, and proves a fresh browser context reopens the exact task/result/evidence/trace/events/files without duplicate IDs or a second task. A second restart case loses both create responses, restarts the API, signs in again, replays the exact persisted key/body, and proves one retained task and one `task.created` event. Two `TaskService` instances sharing one SQLite file prove the durable task claim commits before source start and only one source start occurs; unrelated keys enter source start concurrently. The same gate snapshots the stopped task and settings databases into a verified bundle, restores into another new directory, and proves a fresh application returns the identical completed task, useful result, complete event stream, inbox listing and workspace prompt. Commit `c28ef9b136307016600d2d84c031c96d46f4ea2c` adds the backward-compatible local SQLite application-job queue. Commit `ef0bcc852ddae90c92a3144b16922c7d067799a7` adds real PostgreSQL/Alembic durability behind the additive `/api/v1/durable-jobs` contract: accepted work and one outbox row commit atomically, scoped idempotency survives restart, concurrent `SKIP LOCKED` workers claim uniquely, and lease expiry, retry and bounded dead-letter transitions remain transactional. This is local mechanism proof only and earns no additional browser or hosted credit. Saved drafts, notification intent, real job handlers, whole-application PostgreSQL/object state, exact-boundary process kills, replica/failover convergence and provider-owned once-only effects remain unimplemented or unproven. |
| `E2E-V1-04-CREDENTIAL-BOUNDARY` | Partial | Partial | No | No | Access-key login stays on the same-origin server boundary and returns no script-readable session token. A blocking synthetic-canary journey inspects the login response and scans browser storage, cache/service-worker state, public API/schema responses, built browser assets and retained test artifacts. Server-held keys now bind immutable tenant/workspace/actor context; a separate two-identity browser journey proves cross-tenant negative results without returning tenant IDs. The former PAT/token-in-sandbox fallback has been removed and private GitHub is explicitly `proxy-unavailable`. A real private-source/GitHub proxy operation plus desktop bridge, sandbox and telemetry proof remain open. |
| `E2E-V1-05-RECONNECT` | Partial | Partial | No | No | `make test-recovery` proves a completed task remains visible during an intentional API outage, a re-run fails without changing the original task, and the same persisted task reopens after API restart and fresh sign-in. It also proves an unresolved create receipt survives restart and resolves to the original task without another create. Native browser EventSource cases prove active-task disconnect recovery, one bounded authoritative hydration per disconnect episode, late-read rollback protection, duplicate-event suppression, continued retry after a timed-out hydration, useful last-known state during failure, and honest recovered/unconfirmed status. A timed-out recovery now suppresses overlapping periodic detail refreshes, retaining exactly one recovery read for the episode. API contract tests separately cover replay cursor handling. The local SQLite proof at `c28ef9b136307016600d2d84c031c96d46f4ea2c` and PostgreSQL proof at `ef0bcc852ddae90c92a3144b16922c7d067799a7` each complete accepted work in a separate worker while the API is stopped and read the same terminal job after API restart. Replica loss, replay expiry, interrupted non-fixture handlers, whole-application PostgreSQL recovery, hosted execution and release acceptance remain unproven. |
| `E2E-V1-06-ORDERED-APPROVAL` | Partial | Partial | No | No | The normalized API/domain/SDK/web contract now preserves repeated action names by position, aligns `actionRequests[]` with `reviewConfigs[]`, requires an explicit complete decision vector, supports a mixed approve/edit/reject result, binds idempotency to the reviewed string version, persists replay identity across SQLite reopen, and emits an edited `plan.updated` event before the redacted aggregate `decision.recorded` audit event. The local golden journey explicitly chooses all three actions, edits the second immutable-position plan step, posts `/decision-batch`, observes live progress and the edited result, inspects evidence/files/trace, and reopens. Three two-browser cases prove preflight stale rejection with no mutation and post-preflight conflict reconciliation with one audit event; cross-device plan edits remove obsolete controls, and legacy inbox shortcuts focus the ordered review instead of silently deciding it. The classic source publishes only its bounded legacy interrupt and rejects the batch endpoint because live provider stale, duplicate, authorization, transport-failure and post-resume semantics remain unproven. Hosted and release acceptance remain open. |
| `E2E-V1-07-CODING-DRAFT-PR` | Partial | Partial | No | No | The real task API now accepts an explicitly bound coding journey and repository identity, rejects partial or malformed bindings before task creation, retains terminal-only coding outcomes through SQLite reopen, and exposes exact base/head SHAs, setup/cleanup and snapshot provenance, changed files, one retained draft PR after a deterministic create-timeout reconciliation, and clearly labelled fixture CI. The designed phone journey performs fresh branded sign-in, chooses Coding review, composes, submits every ordered approval, observes completion, inspects the review, confirms merge is unavailable, returns to Tasks and reopens the same draft PR. `tests/e2e/coding-draft-pr.spec.ts` also proves dispatch waits for the real agent-registry response. This is credential-free deterministic fixture proof: repository authorization, a real sandbox, GitHub audit/token boundary, authoritative CI, stale-head phone merge prevention, hosted execution and release acceptance remain open. |
| `E2E-V1-08-RESPONSIVE-ACCESS` | Partial | Partial | No | No | Blocking 1440x1000 and 390x844 screenshots cover all 12 designed route references and the golden journey, including the locked uncertain-dispatch warning and reachable `Check task` action at both widths. The sealed product-demo retains true 390x844 viewport PNGs rather than full-page composites and asserts horizontal overflow, sticky-header and fixed-bottom-navigation geometry in both cells before accepting their digests. `tests/e2e/assistive-access.spec.ts` completes the API-backed review journey by keyboard; proves truthful lifecycle announcements and completion focus; exercises Run-panel arrow tabs and More focus entry/trap/Escape/restore/replacement-modal focus; retains computed reduced-motion and forced-colors checks; and completes compose, approve, Files inspection and reopen in a fresh 320x800 touch context with no horizontal overflow and measured 24px targets. The full 18-case browser gate, including phone-width stale-decision focus recovery, and the six-case visual gate with light/dark WCAG 2.2 A/AA scans pass. Actual 200% browser zoom, VoiceOver/NVDA/JAWS, Switch Control, a real phone and Windows High Contrast remain unaccepted, so this scenario stays Partial. |
| `E2E-V1-09-SECURITY-RECOVERY` | Partial | Partial | No | No | Access keys now bind immutable server-derived tenant/workspace/actor context. Task ownership is retained in the v5 SQLite schema and enforced before every task read, result, trace, SSE, cancel, decision, batch and plan mutation; foreign identifiers return the same safe not-found contract. Prompt settings partition by tenant plus workspace; browser drafts and unresolved dispatches partition by a stable opaque tenant/workspace/actor scope without returning tenant IDs; and both local job repositories scope idempotency and reads by tenant plus workspace. Same-tenant foreign-workspace job IDs return the same safe not-found contract and public responses omit identity and internal worker errors. The PostgreSQL integration gate additionally proves session-scoped HTTP reads and rejects any destructive test target that is not a literal loopback IP, the Psycopg driver, an explicit `deepwork_test*` database and a query-free URL. `make test-recovery` includes a real two-identity, same-workspace-name browser journey with zero-effect foreign requests before and after restart. Its local backup pack additionally checks file and logical hashes, schema/version state and SQLite integrity; refuses existing output and symbolic-link inputs; rejects a tampered database before exposing restored output; and proves exact task/result/event/listing/prompt recovery. Source checks fail startup without authentication, authorize the configured target against server-derived tenant/workspace identity, accept neither provider URL nor credential from the browser, and preserve the adapter's exact normalized allowlist as defense in depth. The pinned official SDK is regression-tested with HTTP redirect following disabled, while foreign workspaces receive a safe unavailable result with zero probe calls. Credential, endpoint-shape, loopback, CORS and stale-mutation tests cover additional individual boundaries. The bundle manifest is deliberately classified as unsigned integrity evidence, not untrusted-source authenticity. DNS resolution/rebinding still requires deployed egress enforcement, and the canonical webhook/object/untrusted-content/sandbox/egress/PostgreSQL/object-store/updater abuse and restore pack is incomplete, so this is not a passing scenario. |
| `E2E-V1-10-PERFORMANCE` | Partial | Partial | No | No | `make test-performance` runs versioned synthetic 1,000-task inbox and 1,001-event task-detail profiles against the production web bundle at 1440x1000 and 390x844. Inbox paging caps the DOM at 50 rows while full-set search and exact-result keyboard opening remain usable; the latest local search p75 was 27.79 ms desktop and 27.05 ms phone against the provisional 200 ms budget. The task thread keeps at most 100 recent/active-review items, Stream keeps at most 100 rows, stable cursor-anchored history does not shift under appends, and bulk replay proves all 1,001 ordered event IDs across 11 pages from latest to oldest and back while result, Sources, Files and Details remain inspectable (226.27 ms desktop; 232.67 ms phone against 4,000 ms). A separate EventSource-boundary profile dispatches every event in its own browser task, measures through the committed result and next paint, validates the exact credentialed subscription, retains all 1,001 events, and closes terminal replay after reopen. It completed in 2,490.10 ms desktop and 2,459.60 ms phone against 5,000 ms, with maximum timer lag 31.20 ms and 14.70 ms and no observed greater-than-50 ms Long Task against 100 ms safety ceilings. The six-case gate is CI-blocking. This remains short synthetic local delivery proof, not native network chunking/backpressure, long-duration retained-memory/frame scaling, multi-source, large subagent/file/diff, reconnect, reference-device, hosted-load or manual-AT qualification. |
| `E2E-V1-11-CONTRIBUTOR` | Partial | No | No | No | The supported root `make check` is green under Node 24/pnpm 11: architecture enforcement, formatting, lint, type checks, 80 domain tests, 73 SDK tests, 32 UI tests, 338 web tests, 415 passing API tests with 7 opt-in skips, the 116-case contract-only gate, 100 agent tests and reproducible package builds pass. The product-demo unit gate adds 53 passing tests plus 34 allocator subtests, including repeated-namespace release, post-release receipt recovery, clean exact-seal provenance and exact network-probe checks. The opt-in `make test-postgres` gate adds five passing real-PostgreSQL migration, concurrency, recovery, HTTP and separate-process cases. `make doctor` fails closed on unsupported toolchains. `make check-oss` blocks missing MIT metadata across all five JavaScript manifests and both Python projects, missing attribution/non-affiliation/runtime-license statements, provider-named logo or commercial-font assets, and mutable GitHub Action tags; all 14 action uses are full-SHA pinned, four intentional legal/branding drift cases pass, 1,340 source files are scanned and both built Python wheels declare MIT. The architecture gate separately proves deliberate illegal-edge and generated-view drift diagnostics. This is one implementation-machine run, not the required two independent clean-machine contributor trials. Transitive-dependency legal review, complete built-artifact attribution, timed PR/proof packets and contributor feedback also remain open. |
| `E2E-V1-12-OPERATIONAL-RELEASE` | Partial | No | No | No | The product renders retained event trace plus an explicit external-trace unavailable state. The hosted journey fails closed without its protected URL/key, rejects fixture runtime and missing source capabilities, requires the exact persisted task route, and blocks browser console errors, failed API requests and non-success API responses. The same gate passes against the production web bundle and real local LangGraph Agent Server with a deterministic keyless model stand-in; that local run is implementation evidence only, not hosted or provider-backed release evidence. A documented local-only stopped-application SQLite backup/restore path emits integrity evidence and round-trips application task/settings state. The disposable local PostgreSQL gate now exercises packaged migration downgrade-to-base, upgrade-to-head and schema drift checking, but it is not a production migration rollback or application-data restore rehearsal. Staged promotion, production PostgreSQL/object restore, failure injection, alert/runbook proof and artifact rollback have not run. |

## Golden-journey recovery slice

The recovery slice is locally browser-proven at both product and visual layers
for the credential-free fixture source. It is also locally browser-proven in a
production-mode non-fixture run against the real local LangGraph Agent Server,
using a deterministic keyless model stand-in. This validates the source-backed UI
and API integration without claiming provider-backed or hosted execution:

1. branded sign-in/connect;
2. show the truthful fixture source locally, or choose a real registry agent in
   real-source mode and retain its identity on the task;
3. compose and dispatch;
4. review the proposed plan;
5. explicitly review every repeated ordered action, edit where allowed, and submit
   one complete versioned decision vector in fixture mode; classic mode retains its
   exact bounded legacy fallback;
6. observe live `Running` progress;
7. receive a useful result;
8. inspect evidence, clearly labelled browser-derived exports and retained/external
   trace truth; and
9. return to the inbox and reopen the same completed task.

The proof owners are `tests/e2e/demo-task-journey.spec.ts`,
`tests/e2e/coding-draft-pr.spec.ts`, `tests/e2e/assistive-access.spec.ts`,
`tests/e2e/approval-race.spec.ts`,
`tests/recovery/durable-reopen.spec.ts`,
`tests/recovery/tenant-workspace-foundation.spec.ts`, and
`tests/visual/product-journey.spec.ts`.
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
| Technical fixture journey | `make test-e2e-demo` | Passing locally: 18 browser tests | API-backed local product behavior, light/dark WCAG scans, keyboard and 320px touch completion, lifecycle/focus behavior, coding review and registry-race protection, source-backed designed Agents rendering with normal-path request suppression, desktop/phone lost-create reconciliation, two-tab adoption, authoritative rejection recovery, two-device stale-decision prevention and post-preflight conflict reconciliation, guarded classic source-check presentation, reduced motion, forced colors and the loopback network contract |
| Durable, reconnect and tenant recovery | `make test-recovery` | Passing locally: 6 API backup/restore checks plus 6 browser cases; required by the main CI verification job | Real API stop/restart against test-owned SQLite; verified stopped-database backup into and restore from new directories; exact task/result/event/listing/prompt comparison; unresolved create replay after restart with one task and one create event; tamper, symlink and overwrite rejection; two-identity task/prompt/draft isolation and zero-effect foreign task requests; plus active native-EventSource disconnect episodes, exactly-once hydration per episode, stale/late snapshot rejection, duplicate suppression, bounded failure and resumed terminal progress. Not Postgres worker/replica/object recovery, replay-expiry, the complete abuse/restore pack, or hosted recovery |
| PostgreSQL job/outbox | `make test-postgres` | Passing locally: 5 integration cases against a guarded disposable loopback PostgreSQL database | Packaged migration upgrade/downgrade and drift checks; atomic job/outbox insert; tenant/workspace idempotency and read isolation; eight concurrent `SKIP LOCKED` worker claims; lease expiry, retry and dead-letter transitions; additive HTTP schema; separate API/worker restart and read-back. Local mechanism proof only, not replica/object/whole-application/hosted/release proof |
| Credential boundary | `make test-security-boundary` | Passing locally and required before hosted acceptance | Synthetic access-key canary absence from browser/public/retained artifacts plus fail-closed private-GitHub source policy |
| Contributor OSS hygiene | `make check-oss` (included by `make check`) | Passing locally: 4 intentional-drift tests, 5 JavaScript manifests, 2 Python projects, 14 full-SHA action references and 1,340 source files | Root/project MIT metadata, README attribution/non-affiliation/runtime boundary, provider-mark/commercial-font filename exclusions and immutable action pins. Built wheels were separately inspected as MIT. Not a legal opinion, transitive-dependency approval, complete distributed-artifact notice pack, or an independent clean-machine contributor trial |
| Route and journey visuals | `make test-visual` | Passing locally: 6 blocking cases; required by the separate `visual-acceptance` CI job | Immutable prototype source, complete route mapping, desktop/phone screenshot contract including the four-agent source-registry Fleet, uncertain-dispatch recovery, 320px reflow and golden-journey states |
| Sealed dual-stack product demo | `DEEPWORK_PRODUCT_DEMO_PEER=<clean-seal-peer> DEEPWORK_PRODUCT_DEMO_EVIDENCE=/tmp/deepwork-product-demo-sealed make test-product-demo` | Passing locally through the canonical harness; accepted receipt retained separately from raw driver evidence | Two concurrent same-commit clean worktrees; real web/API/worker/PostgreSQL/object/telemetry cells; complete desktop/phone journey and restart/reopen; exact five-probe browser origin policy per desktop cell; 16 bidirectional isolation observations; artifact digests; idempotent reservation release and crash-recoverable receipt finalization. Local only: no OS-level server-process egress sandbox, provider, hosted or release proof |
| Production-mode local non-fixture journey | `DEEPWORK_HOSTED_URL=http://127.0.0.1:3000 DEEPWORK_E2E_ACCESS_KEY=<test-owned-key> pnpm test:hosted` with `DEEPWORK_REAL_AGENT=1`, `DEEPWORK_AGENT_FAKE=1`, `DEEPWORK_AGENT_NO_RELOAD=1` and `DEEPWORK_WEB_PRODUCTION=1` | Passing locally: 1 complete browser journey in 10.2s | The production web bundle on the real API and real local LangGraph Agent Server; registry agent choice, compose, plan/approval, silent-stream state reconciliation, useful result, evidence/files/trace and exact-task reopen. The keyless deterministic model stand-in means this is neither provider-backed nor hosted proof |
| Inbox and long-stream performance | `make test-performance` | Six cases pass locally at desktop and phone widths and are required by the main CI verification job | Versioned synthetic 1,000-task and 1,001-event bulk/incremental profiles; maximum 50 inbox rows and 100 Stream rows; stable complete history traversal; result/source/file/detail inspection; post-render responsiveness, exact subscription and terminal-replay closure. Not native network/backpressure, long-duration memory/frame, accepted-device, hosted-load or manual-AT proof |
| Hosted golden journey | `make test-hosted` | Locally characterized against fixture mode: correctly stops at the explicit non-fixture runtime assertion. The protected run remains unavailable because no reviewed `DEEPWORK_HOSTED_URL` or `DEEPWORK_E2E_ACCESS_KEY` is configured | Authenticated non-fixture runtime and required source capabilities; real registry choice; complete retained result and reopen; zero browser page/console errors; zero failed API requests or non-success API responses. It proves these only when the protected `hosted-acceptance` environment supplies both values |

The hosted column remains `No` until that protected job completes and its safe
failure screenshots are reviewed. Credential-bearing Playwright traces are never
retained. The release-accepted column remains `No` until the
scenario's complete proof packet is explicitly accepted; accepting this recovery
direction did not accept any v1 release scenario.
