# Documentation agent instructions

These instructions apply under `docs/` in addition to root `AGENTS.md`.

## Document roles

- `docs/PRODUCT_SENSE.md` owns product promise and judgment; `docs/PLANS.md` owns
  roadmap, release acceptance, and when an ExecPlan is required.
- `docs/DESIGN.md`, `FRONTEND.md`, `SECURITY.md`, `RELIABILITY.md`, and
  `QUALITY_SCORE.md` own cross-cutting standards.
- `docs/design-docs/` contains indexed accepted rationale and decisions.
- `docs/product-specs/` contains stable-ID outcomes, states, interfaces, rollout,
  and acceptance. A product spec is not an implementation log.
- `docs/exec-plans/active/` contains self-contained living implementation state.
  Completed work moves intact to `completed/`; owned debt stays in the tracker.
- `docs/generated/` is machine-owned. Change its source and regenerate.
- `docs/references/` preserves pinned research, audits, and legacy evidence below
  accepted decisions. `docs/proposals/` remains review history, not authority.
- Original `docs/plan/`, `docs/research/`, and uncertain `docs/plans/` paths are
  preserved in Wave 0. Do not edit, normalize, or promote them implicitly.

## Source and claim discipline

Pin repository evidence to a full commit and external behavior to package/API
version, access tier, region, date, and evidence class. Precedence is accepted live
contract, installed public/generated API, official primary docs, accepted Deep Work
decision/spec, then research/prototype evidence.

When sources conflict, record a decision or spike and keep its deterministic
fallback active. Never assert public Fleet CRUD, `/v1/deepagents/*`, arbitrary MDA
connector routes, global thread search, application-owned `mda deploy`, or a
provider resume/header contract without accepted evidence.

## Product-spec standard

Every feature has one stable owner. Keep user outcome, evidence/confidence, scope,
ownership, journeys, complete applicable state matrix, interfaces, capability
fallback, persistence/security, responsive/accessibility behavior, metrics,
dependencies, rollout/rollback, and executable acceptance. Open contract gates may
coexist with an accepted spec, but the affected capability is not implementation-
ready. Later-release briefs retain explicit discovery gates. An empty
`contract_gates: []` means the reviewed feature currently has no external contract
gate; it does not mean review was skipped. Non-empty gates stay open until enabled
behavior has accepted evidence or deliberately ships its stated fallback.

Use the glossary precisely: task/thread/run/checkpoint; agent/assistant/deployment/
source; environment/snapshot/sandbox; interrupt/approval/decision; file/artifact/
attachment; and org/workspace/tenant/actor are not interchangeable.

## ExecPlans

An active ExecPlan is understandable from the checkout alone. Include bounded
outcome, context, allowed paths, non-goals, permissions, milestones, interfaces,
exact validation, recovery, and maintained `Progress`, `Surprises and discoveries`,
`Decision log`, and `Outcomes and retrospective` sections. Link stable product
scope rather than duplicating it. Include `superseded_by` in metadata and update it
when a replacement plan becomes canonical.

## Validation

Run from repository root:

```bash
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
```

The check covers canonical links, front matter, duplicate/dangling feature,
scenario, spike and source IDs, release/scenario counts, generated drift, canonical
indexing, architecture-manifest syntax, the absence of executable `WORKFLOW.md`,
and byte preservation of uncertain `docs/plans/` files.

Do not weaken a count or exclude a canonical path merely to make validation pass.
Repair the owning source or record an explicit reviewed amendment.
