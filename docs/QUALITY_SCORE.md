---
title: Deep Work quality score
status: active
last_reviewed: 2026-08-03
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
| External runtime contracts | 1/4 | 1/4 | Pinned evidence and deterministic fallbacks; named live-contract spikes still open | Complete named live-contract spikes |
| Fixture/demo proof | 0/4 | 4/4 | `make test-e2e-demo` proves branded sign-in → agent choice → compose → plan review → approve → progress → useful result → evidence/files/trace → reopen through the real application API contract at product commit `b726909` | Keep the browser journey and API fixture parity gates green |
| Application implementation | 0/4 | 3/4 | The API-backed task lifecycle and designed web shell are implemented; `make test-visual` binds the prototype reference and reviewed desktop/phone screenshots at gate commit `48e2102` | Complete the partial and absent release scenarios named in the live scorecard |
| Accessibility/security/reliability proof | 1/4 | 3/4 | Light/dark axe-core scans and `tests/e2e/assistive-access.spec.ts` now mechanically prove keyboard dispatch/approval/inspection, truthful lifecycle announcements, completion and modal focus behavior, reduced motion, forced colors, and a fresh 320x800 protocol-touch journey with Files inspection, reopen, no overflow and measured targets at `16d79c2268132e9a6f737b1b543e33d29b46e806`. The synthetic credential boundary, endpoint/loopback/CORS checks, SSE replay and SQLite recovery also pass; `make test-recovery` proves completed-task API restart and fresh-browser reopen at `8b4b8c9ca404e9e08369440bce4a88fed24d964d`. Actual assistive technology, browser zoom, real devices, Windows High Contrast, active-work/Postgres recovery and the tenant/SSRF abuse pack remain unaccepted. | Complete `E2E-V1-05`, `E2E-V1-08`, and `E2E-V1-09` retained proof |
| Performance proof | 0/4 | 3/4 | `make test-performance` executes a versioned synthetic 1,000-task API-contract profile at desktop and phone widths against the production bundle. Commit `261a5c69cfa9ede0c1426cfb8377ba522a77782b` caps observed task rows at 50 and proves URL pagination, full-set search, keyboard opening and provisional p75 interaction below 200 ms. It is local Chromium proof, not an accepted reference-device, frame, memory, long-stream, hosted-load or manual-AT qualification. | Complete the remaining `E2E-V1-10` load surfaces and obtain reference-profile acceptance |
| Orchestration | 2/4 | 2/4 | Manual worktree process accepted; Symphony gated | Keep Symphony gated by SPIKE-SYMPHONY-001 |

Scale: 0 absent, 1 specified, 2 reviewed, 3 mechanically checked, 4 executable and
reproducibly proven. Scores require linked evidence and decrease when evidence
drifts.

Release readiness is not yet demonstrated. The credential-free local product
lifecycle and blocking visual contract are delivered and executed. The hosted
acceptance job is installed but has not run in this recovery, and no canonical v1
scenario is release-accepted. [`RELEASE_SCORECARD.md`](RELEASE_SCORECARD.md) is the
source of truth for the remaining behavior and proof gaps.
