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
`c7e0ea6`, product journey through `b726909`, and blocking browser gates at
`48e2102`, reviewed 2026-08-03 PDT.

| Program scenario | Implemented | Browser-proven | Hosted-proven | Release-accepted | Current evidence and exact gap |
|---|---|---|---|---|---|
| `E2E-V1-01-FIRST-VALUE` | Partial | Partial | No | No | Branded API-key sign-in, fixture agent choice, compose, plan approval, progress, useful result, evidence/files/trace and reopen pass in `tests/e2e/demo-task-journey.spec.ts`. A pinned live classic deployment, authorized-workspace choice, clean-account timing and retained provider correlation remain open. |
| `E2E-V1-02-TRUTHFUL-RUNTIME` | Partial | Partial | No | No | The agent chooser is registry-backed and unsupported capability states remain explanatory. The required classic/MDA/Fleet/unsupported account matrix and negative request ledger are not proven. |
| `E2E-V1-03-DURABLE-CORE` | Partial | No | No | No | API idempotency, optional SQLite recovery and stream tests exist. The complete application-job/draft/notification process-kill and once-only convergence story is not implemented or browser-proven. |
| `E2E-V1-04-CREDENTIAL-BOUNDARY` | Partial | No | No | No | Access-key login now stays on the same-origin server boundary and credential/security tests exist. Private-source plus GitHub operation and the full bundle/storage/cache/bridge/sandbox/telemetry scan remain open. |
| `E2E-V1-05-RECONNECT` | Partial | No | No | No | SSE replay, hydration and reconnect contracts have API coverage. The named active-task disconnect, replica loss, replay expiry and worker restart sequence lacks browser and hosted proof. |
| `E2E-V1-06-ORDERED-APPROVAL` | Partial | Partial | No | No | One real ordered plan decision passes at desktop and phone widths in the golden journey. Repeated-name multi-action editing, two-device racing, stale rejection and retained accessibility/audit proof remain open. |
| `E2E-V1-07-CODING-DRAFT-PR` | No | No | No | No | Repository authorization, sandbox provenance, exact-SHA review, draft PR retry, authoritative CI and phone merge review are outside the delivered recovery slice. |
| `E2E-V1-08-RESPONSIVE-ACCESS` | Partial | Partial | No | No | Blocking 1440x1000 and 390x844 screenshots cover the designed routes and golden journey; the existing accessibility suite remains green. The full 320px, 200% zoom, screen-reader, switch, touch, high-contrast and reduced-motion matrix is not retained. |
| `E2E-V1-09-SECURITY-RECOVERY` | Partial | No | No | No | Tenant, SSRF, credential, CORS, stale mutation and SQLite recovery tests cover individual boundaries. The accepted cross-boundary abuse pack and restore comparison are not complete. |
| `E2E-V1-10-PERFORMANCE` | No | No | No | No | No accepted 1,000-task dataset, reference device/load profile, latency, frame, memory or assistive-navigation proof exists. |
| `E2E-V1-11-CONTRIBUTOR` | Partial | No | No | No | Stable bootstrap/check/browser commands and fixture levels exist. Two independent clean-machine contributor runs, intentional drift repair and license/trademark proof remain open. |
| `E2E-V1-12-OPERATIONAL-RELEASE` | Partial | No | No | No | The product renders retained event trace plus an explicit external-trace unavailable state, and the hosted journey is fail-closed. Staged promotion, migration/restore, failure injection, alert/runbook proof and rollback have not run. |

## Golden-journey recovery slice

The recovery slice is locally browser-proven at both product and visual layers:

1. branded sign-in/connect;
2. choose a real registry agent;
3. compose and dispatch;
4. review the proposed plan;
5. approve through the ordered decision contract;
6. observe live `Running` progress;
7. receive a useful result;
8. inspect evidence, downloadable files and retained/external trace truth; and
9. return to the inbox and reopen the same completed task.

The proof owners are `tests/e2e/demo-task-journey.spec.ts` and
`tests/visual/product-journey.spec.ts`. The visual suite binds the accepted
prototype commit recorded in `tests/visual/reference/manifest.json` and compares
reviewed canonical screenshots under `tests/visual/expected/`.

## Blocking gates

| Gate | Command | Current state | What it can prove |
|---|---|---|---|
| Technical fixture journey | `make test-e2e-demo` | Passing locally | API-backed local product behavior, accessibility and loopback network contract |
| Route and journey visuals | `make test-visual` | Passing locally and required by `verify` CI | Binding desktop/phone screenshot contract plus the golden journey states |
| Hosted golden journey | `make test-hosted` | Installed, fail-closed, not executed in this recovery | Hosted behavior only when `DEEPWORK_HOSTED_URL` and `DEEPWORK_E2E_ACCESS_KEY` are supplied by the protected `hosted-acceptance` environment |

The hosted column remains `No` until that protected job completes and its retained
trace/screenshots are reviewed. The release-accepted column remains `No` until the
scenario's complete proof packet is explicitly accepted; accepting this recovery
direction did not accept any v1 release scenario.
