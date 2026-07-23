---
title: Deep Work quality score
status: active
last_reviewed: 2026-07-23
owners: [quality, developer-experience]
---

# Deep Work quality score

This score distinguishes Wave 0 planning readiness from runtime readiness. A green
documentation harness is not evidence that application behavior exists.

| Dimension | Wave 0 score | Evidence | Next gate |
|---|---:|---|---|
| Canonical knowledge and navigation | 4/4 | Root map, topical docs, indexes, 39 stable specs | Keep docs checks green |
| Product scope and acceptance | 4/4 | 179 feature scenarios and 12 v1 program scenarios | Decompose scaffold work |
| Architecture boundaries | 3/4 | Canonical map and machine manifest | Add executable import checks in Wave 1 |
| External runtime contracts | 1/4 | Pinned evidence and deterministic fallbacks | Complete named live-contract spikes |
| Fixture/demo proof | 0/4 | Planned only | Scaffold both fixture levels |
| Application implementation | 0/4 | No runtime packages yet | Execute Wave 1 scaffold ExecPlan |
| Accessibility/security/reliability proof | 1/4 | Canonical requirements and scenarios | Add executable harnesses with runtime |
| Orchestration | 2/4 | Manual worktree process accepted | Keep Symphony gated by SPIKE-SYMPHONY-001 |

Scale: 0 absent, 1 specified, 2 reviewed, 3 mechanically checked, 4 executable and
reproducibly proven. Scores require linked evidence and decrease when evidence
drifts. Runtime release readiness is currently **0/4** and must not be inferred
from the Wave 0 result.
