---
title: Deep Work quality score
status: active
last_reviewed: 2026-08-04
owners: [quality, developer-experience]
---

# Deep Work quality score

This score distinguishes planning readiness from runtime readiness. A green
documentation harness is not evidence that application behavior exists; the
current column below is backed by executed runtime evidence where noted.

The `Wave 0` column is the accepted planning-lock baseline. The `Current` column
reflects the delivered runtime as of the review date and moves with linked
evidence.

| Dimension | Wave 0 | Current | Evidence for current score | Next gate |
|---|---:|---:|---|---|
| Canonical knowledge and navigation | 4/4 | 4/4 | Root map, topical docs, indexes, 39 stable specs; `tools/docs/check.py` green and CI-enforced | Keep docs checks green |
| Product scope and acceptance | 4/4 | 4/4 | 179 feature scenarios and 12 v1 program scenarios; the live [`RELEASE_SCORECARD.md`](RELEASE_SCORECARD.md) tracks four independent evidence states | Complete and accept each scenario proof packet |
| Architecture boundaries | 3/4 | 3/4 | Executable import checker `tools/architecture/check.py` and all implemented package boundary checks pass in the root `make check`; negative fixtures must fail. The dependency-gated desktop zone is not implemented. | Add the desktop zone after `DW-M1-TS-SCAFFOLD`; broaden coverage and promote remaining report-mode rules to blocking |
| External runtime contracts | 1/4 | 1/4 | Pinned evidence and deterministic fallbacks; a production-mode local browser run now completes the golden journey through the real local LangGraph Agent Server with a deterministic keyless model stand-in at `a326c84b6ecf0cf7c08e6d07735f5a96701626cb`. Provider-backed execution, named live-contract spikes and hosted proof remain open. | Complete named live-contract spikes and protected hosted acceptance |
| Fixture/demo proof | 0/4 | 4/4 | `make test-e2e-demo` proves branded sign-in → agent/journey choice → compose → plan review → approve → progress → useful result → evidence/files/trace → reopen through the real application API contract. The sealed `make test-product-demo` gate repeats that journey concurrently in two clean same-commit worktrees backed by separate real API, web, worker, PostgreSQL, object and telemetry cells; its receipt binds task/run-qualified evidence, browser artifacts, both execution commits and exact reservation release. Commit `8acd3db9dce29ee9b8a20de5363b604315a17ca5` adds the explicitly labelled coding fixture path with exact-revision, sandbox-provenance, retry-reconciled draft PR, non-authoritative CI, phone review and reopen proof. | Keep the browser journey, API fixture parity and sealed dual-stack gates green |
| Application implementation | 0/4 | 3/4 | The API-backed task lifecycle and designed web shell are implemented; `make test-visual` binds the immutable prototype reference plus reviewed desktop/phone journey and coding-review screenshots through `8acd3db9dce29ee9b8a20de5363b604315a17ca5`. Commit `1a80096` upgrades the reference gate to full-resolution sRGB comparison with mutation tests; its contract-only route matrix passes, while the current-head production-browser rerun is blocked by workstation `ENOSPC` and is not claimed green. | Rerun the production-browser gate on a healthy-volume runner and complete the partial and absent release scenarios named in the live scorecard |
| Accessibility/security/reliability proof | 1/4 | 3/4 | Light/dark axe-core scans and `tests/e2e/assistive-access.spec.ts` mechanically prove keyboard dispatch/approval/inspection, truthful lifecycle announcements, completion and modal focus behavior, reduced motion, forced colors, and a fresh 320x800 protocol-touch journey with Files inspection, reopen, no overflow and measured targets at `16d79c2268132e9a6f737b1b543e33d29b46e806`. The synthetic credential boundary, endpoint/loopback/CORS checks, SSE replay and SQLite recovery also pass; `make test-recovery` proves completed-task API restart and fresh-browser reopen at `8b4b8c9ca404e9e08369440bce4a88fed24d964d`. Commits `80cf434` through `7b65f96`, reviewed at `1a80096`, add non-owner plan-edit routing, token-fenced source commits, transient and bounded-permanent stream behavior, bounded replay/receipt retention and real OS-process kill/takeover proof. Commit `c28ef9b136307016600d2d84c031c96d46f4ea2c` adds local authenticated SQLite API/worker recovery, and `ef0bcc852ddae90c92a3144b16922c7d067799a7` adds real local PostgreSQL/Alembic/outbox proof with atomic enqueue, scoped idempotency and reads, eight-worker unique claims, transactional lease/retry/dead-letter recovery and separate API/worker restart. Actual assistive technology, browser zoom, real devices, Windows High Contrast, replica/object recovery, real job handlers, hosted failover and the complete tenant/SSRF abuse pack remain unaccepted. | Complete `E2E-V1-05`, `E2E-V1-08`, and `E2E-V1-09` retained proof |
| Performance proof | 0/4 | 3/4 | `make test-performance` executes six versioned synthetic 1,000-task/1,001-event cases at desktop and phone widths against the production bundle. Commit `2085a909dcec575beaa8fbea8fdb308eef90731e` caps observed inbox rows at 50 and Stream rows at 100; proves full-set search, keyboard opening, stable gap-free history, current plan/approval retention, result/source/file/detail inspection, one-event-per-browser-task incremental delivery through committed render, exact credentialed subscription, and terminal replay closure. Provisional inbox p75 stays below 200 ms, bulk replay below 4,000 ms, incremental completion below 5,000 ms, and timer lag/Long Tasks below 100 ms. The CI job installs pinned Chromium before the gate. This is short synthetic local proof, not native network/backpressure, long-duration retained-memory/frame scaling, accepted-device, hosted-load or manual-AT qualification. | Add native incremental/reconnect and duration/volume scaling with retained-memory/frame reports, complete the remaining `E2E-V1-10` surfaces, and obtain reference-profile acceptance |
| Orchestration | 2/4 | 2/4 | Manual worktree process accepted; Symphony gated | Keep Symphony gated by SPIKE-SYMPHONY-001 |

Scale: 0 absent, 1 specified, 2 reviewed, 3 mechanically checked, 4 executable and
reproducibly proven. Scores require linked evidence and decrease when evidence
drifts.

Release readiness is not yet demonstrated. The credential-free local product
lifecycle and blocking visual contract are delivered; the current-head
contract-only visual matrix is green, while a production-browser rerun is blocked
by the full workstation volume and is not claimed. The hosted
acceptance test also passes locally against the production web bundle and real
local LangGraph Agent Server with a deterministic keyless model stand-in. Its
protected hosted invocation now additionally requires the exact CI commit to be
reported by both deployed services. No reviewed hosted URL/access key/build pair
is configured; the protected hosted journey has not run, and no
canonical v1 scenario is release-accepted.
[`RELEASE_SCORECARD.md`](RELEASE_SCORECARD.md) is the source of truth for the
remaining behavior and proof gaps.
