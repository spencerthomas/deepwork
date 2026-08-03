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
| Architecture boundaries | 3/4 | 3/4 | Executable import checker `tools/architecture/check.py` runs in `pnpm check-architecture` and CI with negative fixtures that must fail | Broaden coverage; promote remaining report-mode rules to blocking |
| External runtime contracts | 1/4 | 1/4 | Pinned evidence and deterministic fallbacks; named live-contract spikes still open | Complete named live-contract spikes |
| Fixture/demo proof | 0/4 | 4/4 | `make test-e2e-demo` proves branded sign-in → agent choice → compose → plan review → approve → progress → useful result → evidence/files/trace → reopen through the real application API contract at product commit `b726909` | Keep the browser journey and API fixture parity gates green |
| Application implementation | 0/4 | 3/4 | The API-backed task lifecycle and designed web shell are implemented; `make test-visual` binds the prototype reference and reviewed desktop/phone screenshots at gate commit `48e2102` | Complete the partial and absent release scenarios named in the live scorecard |
| Accessibility/security/reliability proof | 1/4 | 3/4 | The axe-core journey, responsive shell, reduced-motion behavior, synthetic credential-canary boundary, narrow endpoint/loopback/CORS checks, SSE replay and SQLite recovery are mechanically checked. No tenant-aware implementation or accepted tenant/SSRF abuse pack exists yet, and this is not the full assistive-technology, resilience or 320px matrix. | Complete `E2E-V1-08` and `E2E-V1-09` retained proof |
| Orchestration | 2/4 | 2/4 | Manual worktree process accepted; Symphony gated | Keep Symphony gated by SPIKE-SYMPHONY-001 |

Scale: 0 absent, 1 specified, 2 reviewed, 3 mechanically checked, 4 executable and
reproducibly proven. Scores require linked evidence and decrease when evidence
drifts.

Release readiness is not yet demonstrated. The credential-free local product
lifecycle and blocking visual contract are delivered and executed. The hosted
acceptance job is installed but has not run in this recovery, and no canonical v1
scenario is release-accepted. [`RELEASE_SCORECARD.md`](RELEASE_SCORECARD.md) is the
source of truth for the remaining behavior and proof gaps.
