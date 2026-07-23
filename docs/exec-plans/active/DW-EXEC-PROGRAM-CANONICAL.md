---
exec_plan_id: DW-EXEC-PROGRAM-CANONICAL
title: Canonical Deep Work v1 through v3 program coordination
status: active
superseded_by: null
owner: program-coordinator
reviewed_by: [program-sponsor, architecture, product]
reviewed_at: 2026-07-23
primary_feature_id: DW-FND-001
supporting_feature_ids: [DW-QUAL-001, DW-FUT-101, DW-FUT-102, DW-FUT-103, DW-FUT-201, DW-FUT-202, DW-FUT-203, DW-FUT-204, DW-FUT-205, DW-FUT-206, DW-FUT-207, DW-FUT-301]
issue: local:DW-PROGRAM-001
created: 2026-07-23
last_updated: 2026-07-23
base_commit: 500eaa7faff57def970963160b3d8f1e90c94398
last_verified_commit: 8323084697fe9d7c1aac1c2b07fadf66cc92dff5
risk: high
governed_paths: [docs/exec-plans/active/DW-EXEC-PROGRAM-CANONICAL.md, docs/exec-plans/index.md]
contract_gates: [SPIKE-WORKTREE-001, SPIKE-SYMPHONY-001]
decision_gates: [DEC-032, DEC-039]
gate_review_status: reviewed-with-gates
gate_reviewed_by: [program-sponsor, architecture, product]
gate_reviewed_at: 2026-07-23
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, docs/PRODUCT_SENSE.md, docs/PLANS.md, docs/product-specs/index.md, docs/product-specs/acceptance-scenarios.md, docs/design-docs/architecture/application-architecture.md, docs/design-docs/engineering/conventions.md, docs/design-docs/decisions/index.md, docs/SECURITY.md, docs/RELIABILITY.md, docs/QUALITY_SCORE.md]
scenario_ids: [E2E-V1-01-FIRST-VALUE, E2E-V1-02-TRUTHFUL-RUNTIME, E2E-V1-03-DURABLE-CORE, E2E-V1-04-CREDENTIAL-BOUNDARY, E2E-V1-05-RECONNECT, E2E-V1-06-ORDERED-APPROVAL, E2E-V1-07-CODING-DRAFT-PR, E2E-V1-08-RESPONSIVE-ACCESS, E2E-V1-09-SECURITY-RECOVERY, E2E-V1-10-PERFORMANCE, E2E-V1-11-CONTRIBUTOR, E2E-V1-12-OPERATIONAL-RELEASE]
dispatch_kind: program
dispatch_ready: false
agent_review_required: true
dependencies: []
blockers: []
---

# Canonical Deep Work v1 through v3 program coordination

## Purpose and observable result

Keep the complete canonical Deep Work program resumable from repository state
while bounded, independently reviewed work cells implement and verify v1, v1.x,
v2, and v3. This plan coordinates the graph; owning product specifications and
cell ExecPlans remain the authority for feature outcomes and implementation.

## Context and orientation

Wave 0 is reviewed at `500eaa7faff57def970963160b3d8f1e90c94398`, and
Wave 0.1 dispatch hardening completed at
`3dbe6629d8053380ab6a8bff6d2fcb462f854256`. The active Wave 1 scaffold plan is
a non-dispatchable umbrella. Root TypeScript declarations are terminal; the API
and agent package implementations are committed in isolated worktrees and under
independent review; the TypeScript package cell is at final plan review. Classic
responsive web remains the public baseline; every unproved external capability
stays disabled with its documented fallback.

## Scope

### In scope

- Current wave, work graph, agents, branches, worktrees, reviews, integration
  commits, scenario coverage, contract gates, decisions, evidence, blockers, and
  next dispatches.
- Acyclic decomposition from stable product specifications into reviewed cells.
- Independent review and bounded rework before local integration commits.

### Non-goals

- Replacing a feature specification or cell ExecPlan.
- Granting production, push, merge, deploy, publish, signing, credential, or
  destructive authority.
- Enabling Symphony or creating `WORKFLOW.md` before its spike passes.

### Permissions and risk boundary

- The coordinator owns shared/root integration and the two governed plan paths.
- Cell agents edit only their disjoint governed paths in isolated worktrees.
- Until `SPIKE-WORKTREE-001` passes, at most one full-stack application or
  product-demo worktree may run. Package-only and documentation-only worktrees
  with disjoint paths may run in parallel.
- Implementation authors never approve their own work.

## Authoritative sources and prerequisites

The front-matter authority list is exhaustive for program coordination. Each cell
adds its owning product spec and any accepted contract evidence. The starting
commit is the reviewed Wave 0 baseline; Wave 1 worktrees use the reviewed Wave 0.1
successor after its independent review and local commit.

## Interfaces and invariants

- One primary feature ID and one reviewed ExecPlan own each implementation cell.
- Dependencies are acyclic; governed paths, root manifests, locks, migrations,
  generated contracts, fixtures, and integration files do not overlap.
- Every enabled behavior maps to retained scenario evidence. Fixture proof never
  becomes live-contract proof.
- Unsupported optional capabilities remain unavailable and cannot block the
  classic responsive-web baseline.

## Work graph

| Cell | Wave | State | Base | Governed paths | Dependencies | Next gate |
|---|---:|---|---|---|---|---|
| DW-W0.1-DISPATCH-HARDENING | 0.1 | completed (`3dbe662`) | `500eaa7` | docs/checker and program records | none | terminal |
| DW-M1-ROOT-TS-001 | 1 | completed (`8323084`) | `3dbe662` | root TS declarations/config | W0.1 | terminal |
| DW-M1-API-SCAFFOLD | 1 | implementation committed (`d0ae220`) | `3dbe662` | `apps/api/**` | W0.1 | independent implementation review |
| DW-M1-AGENT-SCAFFOLD | 1 | implementation committed (`6f82e55`) | `3dbe662` | `packages/agent/**` | W0.1 | independent implementation review |
| DW-M1-TS-SCAFFOLD | 1 | plan re-review | `b1189ce` | `packages/domain/**`, `packages/sdk/**`, `packages/ui/**` | root TS terminal | reviewed cell ExecPlan |
| DW-M1-INTEGRATION | 1 | pending | accepted lane commits | shared/root, `apps/web/**`, generated outputs | Wave 1 lanes | lane reviews accepted |
| Waves 2-6 | 2-6 | pending | accepted predecessor | bounded per reviewed plan | prior exit gates | v1 scenario qualification |
| v1.x, v2, v3 | later | pending | accepted release predecessor | discovery-derived cells | reviewed discovery gates | executable plans |

The graph is acyclic. Root/shared ownership remains with the coordinator until a
later reviewed cell explicitly reassigns it.

## Active agents, branches, and worktrees

| Role | Cell | Branch | Worktree | State |
|---|---|---|---|---|
| coordinator | program/root TS integration | `claude/deepwork-project-planning-3y91wd` | `/Users/tomspencer/dev/deepwork/deepwork-planning` | root TS terminal; coordinating reviews |
| API author/reviewer | API authored; TS plan review | `codex/api/wave1-scaffold` | `/Users/tomspencer/dev/deepwork/worktrees/w1-api` | API committed; reviewing TS plan in its worktree |
| agent author/API reviewer | agent authored; API review | `codex/agent/wave1-scaffold` | `/Users/tomspencer/dev/deepwork/worktrees/w1-agent` | agent committed; reviewing API worktree |
| TS planner/agent reviewer | root/TS planning; agent review | `codex/domain/wave1-ts-scaffold` | `/Users/tomspencer/dev/deepwork/worktrees/w1-ts` | root dependency integrated; reviewing agent worktree |

## Progress

- [x] 2026-07-23 13:00 AEST — Program directive accepted; repository baseline
  verified at `500eaa7faff57def970963160b3d8f1e90c94398`.
- [x] 2026-07-23 — Wave 0.1 schema, authority, gate, dispatch, concurrency, and
  roadmap hardening validated, independently reviewed, and committed at
  `3dbe6629d8053380ab6a8bff6d2fcb462f854256`.
- [x] 2026-07-23 — Root TypeScript declarations/config completed and independently
  reviewed through `8323084697fe9d7c1aac1c2b07fadf66cc92dff5`; no lock or
  executable package claim made.
- [ ] Wave 1 API and agent implementations pass independent review and integrate;
  TypeScript packages complete their reviewed authoring, lock, and verification
  sequence.
- [ ] Waves 2-6 complete; 179 feature and 12 v1 release scenarios pass.
- [ ] v1.x, v2, and v3 discovery briefs become reviewed executable plans and are
  implemented or retained behind exact human/external blocker entries.

## Surprises & Discoveries

- 2026-07-23 — Observation: the pre-hardening checker passed even though the
  active plan used unsupported status and metadata. Evidence:
  `python3 tools/docs/check.py` at `500eaa7`. Consequence: dispatch validation is
  a mandatory Wave 0.1 gate.
- 2026-07-23 — Observation: `docs/plans/**` is pre-existing untracked evidence.
  Consequence: it remains byte-preserved and outside every governed path.
- 2026-07-23 — Observation: independent review found readiness did not fail
  closed for blockers/dependencies and the Wave 1 umbrella was too broad to
  dispatch as one cell. Consequence: validate references and cycles, derive safe
  readiness, and keep the umbrella non-dispatchable.
- 2026-07-23 — Observation: independent re-review accepted the bounded Wave 0.1
  patch after those corrections. Consequence: create the authorized local commit
  and use it as the base for scoped Wave 1 planning worktrees.
- 2026-07-23 — Observation: the implementation host exposes Node 20/pnpm 9 while
  the canonical repository pins Node 24.18.0/pnpm 10.34.5. Consequence: root
  declarations were statically verified without an install; the sequential lock
  cell must provision the pinned toolchain before executable TypeScript proof.
- 2026-07-23 — Observation: independent review caught DOM libraries in the
  universal TypeScript base. Consequence: the accepted base is ES2022-only and
  browser-owning packages must opt into DOM libraries locally.

## Decision Log

- 2026-07-23 — Decision: treat `500eaa7` as the reviewed Wave 0 planning
  baseline. Rationale: explicit program directive and committed integration
  record. Consequence: all implementation work descends from its reviewed Wave
  0.1 successor. Approved by: program sponsor.
- 2026-07-23 — Decision: use manual isolated worktrees; keep full-stack work
  serial until `SPIKE-WORKTREE-001` passes. Consequence: package/documentation
  lanes may be parallel, while product-demo composition remains coordinator-owned.
- 2026-07-23 — Decision: split TypeScript root declarations, package source,
  first shared lock, and executable verification into sequential evidence cells.
  Rationale: the lock must include reviewed importers and frozen/no-drift proof
  cannot truthfully precede them.

## Detailed implementation approach

Complete Wave 0.1 in the current tree, run negative validator tests and canonical
checks, dispatch a fresh review-only agent, address bounded findings, and create
one attributable local commit. Then create reviewed, disjoint lane ExecPlans and
worktrees at that commit, refill up to three worker/reviewer slots without
overlapping shared files, and integrate only accepted commits.

## Validation and proof

Wave 0.1 proof:

```text
python3 -m unittest discover -s tools/docs/tests -p 'test_*.py'
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
git diff --check
```

Every later cell records exact feature and release scenario IDs, commands,
environment, sanitized evidence path, independent review outcome, rollback, and
integration commit in its own plan and summarizes the result here.

## Idempotence, rollback, and recovery

Plan and checker changes are additive and safely rerunnable. Generated files are
changed only through their generator. If a cell fails, preserve its branch,
worktree, logs, proof, and plan state; do not reset unrelated work. Revert only an
accepted integration commit if rollback is authorized and the compatibility
matrix allows it.

## Rollout and handoff

Wave transitions occur only after predecessor exit evidence and independent
review. Program reports record the integration commit; completed, active, blocked,
and next cells; branches/worktrees; validation; scenario coverage; contract gates
and fallbacks; conflicts/decisions; and exact human/external blockers.

## Outcomes & Retrospective

Wave 0.1 and the root TypeScript declaration/configuration cell are terminal.
API and agent package implementations are locally committed with full author
validation and are undergoing fresh cross-review. The TypeScript package plan is
under final review against its now-terminal root prerequisite. No protected
`docs/plans/**` file, external credential, production system, push, merge,
deployment, or publication has been touched. The terminal outcome remains the
verified complete canonical vision through v3, or an exact blocker ledger after
every independent DAG branch is exhausted.
