---
title: Deep Work quality score
status: active
last_reviewed: 2026-07-23
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
| Product scope and acceptance | 4/4 | 4/4 | 179 feature scenarios and 12 v1 program scenarios | Keep coverage in sync with delivery |
| Architecture boundaries | 3/4 | 3/4 | Executable import checker `tools/architecture/check.py` runs in `pnpm check-architecture` and CI with negative fixtures that must fail | Broaden coverage; promote remaining report-mode rules to blocking |
| External runtime contracts | 1/4 | 1/4 | Pinned evidence and deterministic fallbacks; named live-contract spikes still open | Complete named live-contract spikes |
| Fixture/demo proof | 0/4 | 4/4 | Credential-free product runs the full task lifecycle end-to-end (create → editable plan → ordered approval → prompt-specific result → replayable stream); `make test-e2e-demo` proves the API-backed journey in installed Chrome with loopback-only network traffic; product-demo fixture corpus validates | Keep the browser journey and fixture parity gates green |
| Application implementation | 0/4 | 3/4 | `apps/api` (tasks, HITL, SSE, results, optional SQLite) and `apps/web` (five destinations) build and test green; `packages/{domain,sdk,ui,agent}` build and test green in CI | Durable core (auth, outbox/jobs), then live-source integration |
| Accessibility/security/reliability proof | 1/4 | 2/4 | a11y (skip links, landmarks, reduced-motion) merged; SSRF/tenant/credential-boundary/CORS and SSE replay/reconnect + SQLite-recovery covered by tests | Add executable accessibility and load/resilience harnesses |
| Orchestration | 2/4 | 2/4 | Manual worktree process accepted; Symphony gated | Keep Symphony gated by SPIKE-SYMPHONY-001 |

Scale: 0 absent, 1 specified, 2 reviewed, 3 mechanically checked, 4 executable and
reproducibly proven. Scores require linked evidence and decrease when evidence
drifts.

Release readiness is not yet demonstrated. The credential-free local product
lifecycle is delivered and executed, but release-blocking gates — authentication,
durable jobs and recovery, and proven live-provider contracts — remain open, so a
full v1 release must not be inferred from the current local-product result.
