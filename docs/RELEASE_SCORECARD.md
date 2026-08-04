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

| Program scenario | Implemented | Browser-proven | Hosted-proven | Release-accepted | Current evidence and exact gap |
|---|---|---|---|---|---|
| `E2E-V1-01-FIRST-VALUE` | Partial | Partial | No | No | Branded API-key sign-in, truthful fixture origin, compose, plan approval, progress, useful result, derived exports, evidence/trace and reopen pass in `tests/e2e/demo-task-journey.spec.ts`. A signed-in API workspace can now enter an assistant ID for its server-owned classic deployment target and run a credentialed, read-only identity check in the designed Runtime settings shell. The real-agent path retains the selected `agentId`, including the default agent with its workspace prompt, and hosted acceptance actively chooses a registry agent. Source save/select correctly remain blocked because invocation and stream qualification have not run, and the protected hosted journey has not run. |
| `E2E-V1-02-TRUTHFUL-RUNTIME` | Partial | Partial | No | No | The real-mode chooser is registry-backed, blocks on registry failure, and retains the chosen agent identity through detail, trace and reopen; fixture mode declares that no registry exists. `POST /api/v1/sources/probes` now resolves one server-owned target only after session and tenant/workspace authorization, performs the bounded classic assistant lookup for its exact normalized operator allowlist, accepts neither provider URLs nor credentials from the browser, and never permits save from read evidence alone. Every capability carries evidence class, observation time, adapter version, contract version and a coherent safe reason when unavailable. The browser proves unavailable and qualified presentation states, while only the unavailable state is full-stack local proof; the qualified UI response is deterministic interception over a separately contract-tested API shape. Invocation qualification, durable source registration, dynamic task routing and the required classic/MDA/Fleet/unsupported account matrix remain open. |
| `E2E-V1-03-DURABLE-CORE` | Partial | Partial | No | No | `make test-recovery` creates and completes a real API-backed fixture task, stops the API process, restarts it against the same test-owned SQLite database, and proves a fresh browser context reopens the exact task/result/evidence/trace/events/files without duplicate IDs or a second task. The same gate now snapshots the stopped task and settings databases into a new verified bundle, restores into another new directory, and proves a fresh application returns the identical completed task, useful result, complete event stream, inbox listing and workspace prompt. This is local SQLite recovery only. The complete Postgres application-job/draft/notification process-kill, worker/outbox and once-only convergence story is not implemented or proven. |
| `E2E-V1-04-CREDENTIAL-BOUNDARY` | Partial | Partial | No | No | Access-key login stays on the same-origin server boundary and returns no script-readable session token. A blocking synthetic-canary journey inspects the login response and scans browser storage, cache/service-worker state, public API/schema responses, built browser assets and retained test artifacts. Server-held keys now bind immutable tenant/workspace/actor context; a separate two-identity browser journey proves cross-tenant negative results without returning tenant IDs. The former PAT/token-in-sandbox fallback has been removed and private GitHub is explicitly `proxy-unavailable`. A real private-source/GitHub proxy operation plus desktop bridge, sandbox and telemetry proof remain open. |
| `E2E-V1-05-RECONNECT` | Partial | Partial | No | No | `make test-recovery` proves a completed task remains visible during an intentional API outage, a re-run fails without changing the original task, and the same persisted task reopens after API restart and fresh sign-in. Native browser EventSource cases now prove active-task disconnect recovery, one bounded authoritative hydration per disconnect episode, late-read rollback protection, duplicate-event suppression, continued retry after a timed-out hydration, useful last-known state during failure, and honest recovered/unconfirmed status. API contract tests separately cover replay cursor handling. Replica loss, replay expiry, worker restart, hosted execution and release acceptance remain unproven. |
| `E2E-V1-06-ORDERED-APPROVAL` | Partial | Partial | No | No | The normalized API/domain/SDK/web contract now preserves repeated action names by position, aligns `actionRequests[]` with `reviewConfigs[]`, requires an explicit complete decision vector, supports a mixed approve/edit/reject result, binds idempotency to the reviewed string version, persists replay identity across SQLite reopen, and emits an edited `plan.updated` event before the redacted aggregate `decision.recorded` audit event. The local golden journey explicitly chooses all three actions, edits the second immutable-position plan step, posts `/decision-batch`, observes live progress and the edited result, inspects evidence/files/trace, and reopens. Three two-browser cases prove preflight stale rejection with no mutation and post-preflight conflict reconciliation with one audit event; cross-device plan edits remove obsolete controls, and legacy inbox shortcuts focus the ordered review instead of silently deciding it. The classic source publishes only its bounded legacy interrupt and rejects the batch endpoint because live provider stale, duplicate, authorization, transport-failure and post-resume semantics remain unproven. Hosted and release acceptance remain open. |
| `E2E-V1-07-CODING-DRAFT-PR` | Partial | Partial | No | No | The real task API now accepts an explicitly bound coding journey and repository identity, rejects partial or malformed bindings before task creation, retains terminal-only coding outcomes through SQLite reopen, and exposes exact base/head SHAs, setup/cleanup and snapshot provenance, changed files, one retained draft PR after a deterministic create-timeout reconciliation, and clearly labelled fixture CI. The designed phone journey performs fresh branded sign-in, chooses Coding review, composes, submits every ordered approval, observes completion, inspects the review, confirms merge is unavailable, returns to Tasks and reopens the same draft PR. `tests/e2e/coding-draft-pr.spec.ts` also proves dispatch waits for the real agent-registry response. This is credential-free deterministic fixture proof: repository authorization, a real sandbox, GitHub audit/token boundary, authoritative CI, stale-head phone merge prevention, hosted execution and release acceptance remain open. |
| `E2E-V1-08-RESPONSIVE-ACCESS` | Partial | Partial | No | No | Blocking 1440x1000 and 390x844 screenshots cover all 12 designed route references and the golden journey. `tests/e2e/assistive-access.spec.ts` now completes the API-backed review journey by keyboard; proves truthful lifecycle announcements and completion focus; exercises Run-panel arrow tabs and More focus entry/trap/Escape/restore/replacement-modal focus; retains computed reduced-motion and forced-colors checks; and completes compose, approve, Files inspection and reopen in a fresh 320x800 touch context with no horizontal overflow and measured 24px targets. The full ten-test browser gate, including phone-width stale-decision focus recovery, and light/dark WCAG 2.2 A/AA scans pass. Actual 200% browser zoom, VoiceOver/NVDA/JAWS, Switch Control, a real phone and Windows High Contrast remain unaccepted, so this scenario stays Partial. |
| `E2E-V1-09-SECURITY-RECOVERY` | Partial | Partial | No | No | Access keys now bind immutable server-derived tenant/workspace/actor context. Task ownership is retained in the v5 SQLite schema and enforced before every task read, result, trace, SSE, cancel, decision, batch and plan mutation; foreign identifiers return the same safe not-found contract. Prompt settings partition by tenant plus workspace, while browser drafts partition by workspace plus actor and have no generic API fallback. `make test-recovery` includes a real two-identity, same-workspace-name browser journey with zero-effect foreign requests before and after restart. Its local backup pack additionally checks file and logical hashes, schema/version state and SQLite integrity; refuses existing output and symbolic-link inputs; rejects a tampered database before exposing restored output; and proves exact task/result/event/listing/prompt recovery. Source checks fail startup without authentication, authorize the configured target against server-derived tenant/workspace identity, accept neither provider URL nor credential from the browser, and preserve the adapter's exact normalized allowlist as defense in depth. The pinned official SDK is regression-tested with HTTP redirect following disabled, while foreign workspaces receive a safe unavailable result with zero probe calls. Credential, endpoint-shape, loopback, CORS and stale-mutation tests cover additional individual boundaries. The bundle manifest is deliberately classified as unsigned integrity evidence, not untrusted-source authenticity. DNS resolution/rebinding still requires deployed egress enforcement, and the canonical webhook/object/untrusted-content/sandbox/egress/Postgres/object-store/updater abuse and restore pack is incomplete, so this is not a passing scenario. |
| `E2E-V1-10-PERFORMANCE` | Partial | Partial | No | No | `make test-performance` runs versioned synthetic 1,000-task inbox and 1,001-event task-detail profiles against the production web bundle at 1440x1000 and 390x844. Inbox paging caps the DOM at 50 rows while full-set search and exact-result keyboard opening remain usable; the latest local search p75 was 27.79 ms desktop and 27.05 ms phone against the provisional 200 ms budget. The task thread keeps at most 100 recent/active-review items, Stream keeps at most 100 rows, stable cursor-anchored history does not shift under appends, and bulk replay proves all 1,001 ordered event IDs across 11 pages from latest to oldest and back while result, Sources, Files and Details remain inspectable (226.27 ms desktop; 232.67 ms phone against 4,000 ms). A separate EventSource-boundary profile dispatches every event in its own browser task, measures through the committed result and next paint, validates the exact credentialed subscription, retains all 1,001 events, and closes terminal replay after reopen. It completed in 2,490.10 ms desktop and 2,459.60 ms phone against 5,000 ms, with maximum timer lag 31.20 ms and 14.70 ms and no observed greater-than-50 ms Long Task against 100 ms safety ceilings. The six-case gate is CI-blocking. This remains short synthetic local delivery proof, not native network chunking/backpressure, long-duration retained-memory/frame scaling, multi-source, large subagent/file/diff, reconnect, reference-device, hosted-load or manual-AT qualification. |
| `E2E-V1-11-CONTRIBUTOR` | Partial | No | No | No | The supported root `make check` is green under Node 24/pnpm 11: architecture enforcement, formatting, lint, type checks, 80 domain tests, 73 SDK tests, 32 UI tests, 329 web tests, 379 passing API tests plus the 102-passing contract-only gate, 100 agent tests and reproducible package builds pass. `make doctor` fails closed on unsupported toolchains. `make check-oss` now blocks missing MIT metadata across all five JavaScript manifests and both Python projects, missing attribution/non-affiliation/runtime-license statements, provider-named logo or commercial-font assets, and mutable GitHub Action tags; all 14 action uses are full-SHA pinned, four intentional legal/branding drift cases pass, 1,316 tracked files are scanned and both built Python wheels declare MIT. The architecture gate separately proves deliberate illegal-edge and generated-view drift diagnostics. This is one implementation-machine run, not the required two independent clean-machine contributor trials. Transitive-dependency legal review, complete built-artifact attribution, timed PR/proof packets and contributor feedback also remain open. |
| `E2E-V1-12-OPERATIONAL-RELEASE` | Partial | No | No | No | The product renders retained event trace plus an explicit external-trace unavailable state, and the hosted journey is fail-closed. A documented local-only stopped-application SQLite backup/restore path now emits integrity evidence and round-trips application task/settings state, but it is neither the production Postgres/object backup contract nor a migration rollback rehearsal. Staged promotion, production migration/restore, failure injection, alert/runbook proof and artifact rollback have not run. |

## Golden-journey recovery slice

The recovery slice is locally browser-proven at both product and visual layers
for the credential-free fixture source. The same UI and API contracts support the
real source, while the real-source choice and execution remain hosted-unproven:

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
| Technical fixture journey | `make test-e2e-demo` | Passing locally: 13 browser tests | API-backed local product behavior, light/dark WCAG scans, keyboard and 320px touch completion, lifecycle/focus behavior, coding review and registry-race protection, two-device stale-decision prevention and post-preflight conflict reconciliation, guarded classic source-check presentation, reduced motion, forced colors and the loopback network contract |
| Durable, reconnect and tenant recovery | `make test-recovery` | Passing locally: 6 API backup/restore checks plus 5 browser cases; required by the main CI verification job | Real API stop/restart against test-owned SQLite; verified stopped-database backup into and restore from new directories; exact task/result/event/listing/prompt comparison; tamper, symlink and overwrite rejection; two-identity task/prompt/draft isolation and zero-effect foreign task requests; plus active native-EventSource disconnect episodes, exactly-once hydration per episode, stale/late snapshot rejection, duplicate suppression, bounded failure and resumed terminal progress. Not Postgres worker/replica/object recovery, replay-expiry, the complete abuse/restore pack, or hosted recovery |
| Credential boundary | `make test-security-boundary` | Passing locally and required before hosted acceptance | Synthetic access-key canary absence from browser/public/retained artifacts plus fail-closed private-GitHub source policy |
| Contributor OSS hygiene | `make check-oss` (included by `make check`) | Passing locally: 4 intentional-drift tests, 5 JavaScript manifests, 2 Python projects, 14 full-SHA action references and 1,316 tracked files | Root/project MIT metadata, README attribution/non-affiliation/runtime boundary, provider-mark/commercial-font filename exclusions and immutable action pins. Built wheels were separately inspected as MIT. Not a legal opinion, transitive-dependency approval, complete distributed-artifact notice pack, or an independent clean-machine contributor trial |
| Route and journey visuals | `make test-visual` | Passing locally and required by the separate `visual-acceptance` CI job | Immutable prototype source, complete route mapping, desktop/phone screenshot contract, 320px reflow and golden-journey states |
| Inbox and long-stream performance | `make test-performance` | Six cases pass locally at desktop and phone widths and are required by the main CI verification job | Versioned synthetic 1,000-task and 1,001-event bulk/incremental profiles; maximum 50 inbox rows and 100 Stream rows; stable complete history traversal; result/source/file/detail inspection; post-render responsiveness, exact subscription and terminal-replay closure. Not native network/backpressure, long-duration memory/frame, accepted-device, hosted-load or manual-AT proof |
| Hosted golden journey | `make test-hosted` | Attempted locally; failed closed because no reviewed `DEEPWORK_HOSTED_URL` or `DEEPWORK_E2E_ACCESS_KEY` was configured | Real registry choice, non-fixture source, retained result and reopen only when both values are supplied by the protected `hosted-acceptance` environment |

The hosted column remains `No` until that protected job completes and its safe
failure screenshots are reviewed. Credential-bearing Playwright traces are never
retained. The release-accepted column remains `No` until the
scenario's complete proof packet is explicitly accepted; accepting this recovery
direction did not accept any v1 release scenario.
