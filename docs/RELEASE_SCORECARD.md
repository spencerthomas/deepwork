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
`c7e0ea6`, product journey through `b726909`, blocking browser gates through
`48e2102`, plus the independent-review hardening set, reviewed
2026-08-03 PDT.

| Program scenario | Implemented | Browser-proven | Hosted-proven | Release-accepted | Current evidence and exact gap |
|---|---|---|---|---|---|
| `E2E-V1-01-FIRST-VALUE` | Partial | Partial | No | No | Branded API-key sign-in, truthful fixture origin, compose, plan approval, progress, useful result, derived exports, evidence/trace and reopen pass in `tests/e2e/demo-task-journey.spec.ts`. The real-agent path now retains the selected `agentId`, and hosted acceptance actively chooses a registry agent, but that protected hosted journey has not run. |
| `E2E-V1-02-TRUTHFUL-RUNTIME` | Partial | Partial | No | No | The real-mode chooser is registry-backed, blocks on registry failure, and retains the chosen agent identity through detail, trace and reopen; fixture mode declares that no registry exists. The required classic/MDA/Fleet/unsupported account matrix and negative request ledger are not proven. |
| `E2E-V1-03-DURABLE-CORE` | Partial | No | No | No | API idempotency, optional SQLite recovery and stream tests exist. The complete application-job/draft/notification process-kill and once-only convergence story is not implemented or browser-proven. |
| `E2E-V1-04-CREDENTIAL-BOUNDARY` | Partial | Partial | No | No | Access-key login stays on the same-origin server boundary. A blocking synthetic-canary journey scans browser storage, cache/service-worker state, public API/schema responses, built browser assets and retained test artifacts. The former PAT/token-in-sandbox fallback has been removed and private GitHub is explicitly `proxy-unavailable`. A real private-source/GitHub proxy operation plus desktop bridge, sandbox and telemetry proof remain open. |
| `E2E-V1-05-RECONNECT` | Partial | No | No | No | SSE replay, hydration and reconnect contracts have API coverage. The named active-task disconnect, replica loss, replay expiry and worker restart sequence lacks browser and hosted proof. |
| `E2E-V1-06-ORDERED-APPROVAL` | Partial | Partial | No | No | One real ordered plan decision passes at desktop and phone widths in the golden journey. Repeated-name multi-action editing, two-device racing, stale rejection and retained accessibility/audit proof remain open. |
| `E2E-V1-07-CODING-DRAFT-PR` | No | No | No | No | Repository authorization, sandbox provenance, exact-SHA review, draft PR retry, authoritative CI and phone merge review are outside the delivered recovery slice. |
| `E2E-V1-08-RESPONSIVE-ACCESS` | Partial | Partial | No | No | Blocking 1440x1000 and 390x844 screenshots cover all 12 designed route references and the golden journey; a separate 320px overflow check covers the primary shell routes, and the existing accessibility suite remains green. The 200% zoom, screen-reader, switch, touch, high-contrast and reduced-motion matrix is not retained. |
| `E2E-V1-09-SECURITY-RECOVERY` | Partial | No | No | No | Narrow credential, endpoint-shape, loopback, CORS, stale-mutation and SQLite recovery tests cover individual boundaries. There is no tenant-aware implementation or accepted tenant/SSRF/redirect/webhook/object/sandbox/updater abuse pack, restore comparison, or zero-unauthorized-effect proof. |
| `E2E-V1-10-PERFORMANCE` | No | No | No | No | No accepted 1,000-task dataset, reference device/load profile, latency, frame, memory or assistive-navigation proof exists. |
| `E2E-V1-11-CONTRIBUTOR` | Partial | No | No | No | Stable bootstrap/check/browser commands and fixture levels exist. Two independent clean-machine contributor runs, intentional drift repair and license/trademark proof remain open. |
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

The proof owners are `tests/e2e/demo-task-journey.spec.ts` and
`tests/visual/product-journey.spec.ts`. The visual suite verifies immutable hashes
for the accepted prototype commit recorded in
`tests/visual/reference/prototype/manifest.json`, maps all 12 route references to
current canonical captures, enforces reviewed perceptual deltas, and compares the
full-resolution screenshots under `tests/visual/expected/` in a pinned browser and
platform job.

## Blocking gates

| Gate | Command | Current state | What it can prove |
|---|---|---|---|
| Technical fixture journey | `make test-e2e-demo` | Passing locally | API-backed local product behavior, accessibility and loopback network contract |
| Credential boundary | `make test-security-boundary` | Passing locally and required before hosted acceptance | Synthetic access-key canary absence from browser/public/retained artifacts plus fail-closed private-GitHub source policy |
| Route and journey visuals | `make test-visual` | Passing locally and required by the separate `visual-acceptance` CI job | Immutable prototype source, complete route mapping, desktop/phone screenshot contract, 320px reflow and golden-journey states |
| Hosted golden journey | `make test-hosted` | Installed, fail-closed, not executed in this recovery | Real registry choice, non-fixture source, retained result and reopen only when `DEEPWORK_HOSTED_URL` and `DEEPWORK_E2E_ACCESS_KEY` are supplied by the protected `hosted-acceptance` environment |

The hosted column remains `No` until that protected job completes and its safe
failure screenshots are reviewed. Credential-bearing Playwright traces are never
retained. The release-accepted column remains `No` until the
scenario's complete proof packet is explicitly accepted; accepting this recovery
direction did not accept any v1 release scenario.
