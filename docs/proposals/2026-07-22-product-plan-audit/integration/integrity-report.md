# Proposal integrity report

Status: **proposal-internal validation passes; cross-repository G0 fails**
Verified: 2026-07-23
Scope: `docs/proposals/2026-07-22-product-plan-audit/`

## Proposal validation

| Check | Result |
|---|---|
| Markdown files | 72 |
| Internal Markdown links | 0 broken |
| YAML front matter | 0 parse errors |
| Stable feature definitions | 39 unique; 0 dangling references |
| Release plan counts | 28 v1, 3 v1.x, 7 v2, 1 v3 |
| V1 plan metadata | all 28 use `contract_gates`; all 39 plans/briefs have `last_reviewed` |
| Runtime-scope metadata | all 39 use normalized `runtime_scopes`; 0 legacy/readiness-suffixed values |
| Decision/spike/source definitions | 43 decisions, 44 spikes, 19 sources; 0 dangling spike/source references |
| V1 product dependency graph | 0 cycles |
| Feature acceptance scenarios | 179 indexed; 0 ID/title mismatches |
| Program release scenarios | 12 unique; one owner for each of 12 v1 criteria |
| Frontend inventory | 13 routes, 7 top destinations, 8 run-panel tabs, 22 settings sections |

These results prove proposal consistency only. They do not accept an architecture
decision, close a live contract, run a release scenario, or make a feature ready.

## Pinned evidence availability

| Evidence | Expected pin | Verification |
|---|---|---|
| Canonical planning history | `06f051554bf938e919af5ab7855974098fbf3d2a` | Commit remains locally addressable; current planning HEAD is still this pin. |
| Frontend audit history | `8866d39a2888e358091208063693f260cff6d261` | Commit remains locally addressable. Current checkout has advanced; see below. |
| LangChain docs | `7b9215d708e0b57e6fbae7b5d0762c4118b8e309` | Current HEAD matches. |
| Deep Agents | `7794b61a6e76230e8c7a49bdce808b3728305914` | Current HEAD matches. |
| LangChain Python | `592055e15e138f5369dce95dd049ce22430996e2` | Current HEAD matches. |
| LangChain.js | `ee76ea0347fb611153e5ec7d0e70fa405f5293a3` | Current HEAD matches. |
| LangGraph | `31f90df3e6b0268fa77fd2d118a917d420b84a68` | Current HEAD matches. |

## G0 failures outside the proposal

The planning repository has no tracked diff, but it contains these eleven
untracked files under `docs/plans/`:

```text
docs/plans/2026-07-22-001-feat-deepwork-v1-delivery-plan.md
docs/plans/application-architecture.md
docs/plans/code-conventions.md
docs/plans/features/01-monorepo-scaffold.md
docs/plans/features/02-web-import-hygiene.md
docs/plans/features/03-oauth-spike.md
docs/plans/features/04-mda-loop-spike.md
docs/plans/features/05-stream-contract-spike.md
docs/plans/features/06-agent-project.md
docs/plans/features/07b-api-backend.md
docs/plans/features/08-mobile-and-surfaces.md
```

The protected delivery-plan observation was 957 lines with SHA-256
`5e6a30202417d6261e2bd4e973e7b71d92171e9a8cbf8031753a93c1632bf813`.
The current file is 986 lines with SHA-256
`3f4b6ed96054289426ac6c53ee6b4702484a934067a11b5761c0d68d756e3b0c`.
Its owner and intended baseline must be resolved; this proposal did not alter,
move, delete, or normalize it.

The sibling frontend checkout is now
`26c698b30ff08d5122cfaeedbd4a95296a7884f4`, rather than the audited `8866d39`
commit, and contains untracked `.DS_Store`, `app/.DS_Store`, and
`components/.DS_Store`. The pinned audit remains reproducible from Git history,
but the newer frontend requires an explicit refresh if it is to affect decisions.

## Required resolution

G0 can pass only after a maintainer:

1. identifies and reviews every outside-proposal file;
2. restores the frozen delivery-plan artifact or accepts a newly hashed evidence
   baseline without rewriting its history;
3. decides whether the newer frontend is in review scope and, if so, reruns the
   frontend inventory at an explicit new pin;
4. reruns this report and records a clean accepted baseline; and
5. executes the [merge map](merge-map.md) as a separate reviewed integration.

Until then, this proposal is complete as a review package but must not be copied
into canonical paths or used to dispatch implementation work.
