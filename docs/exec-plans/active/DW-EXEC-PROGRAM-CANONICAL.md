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
last_verified_commit: e3aae38e5fdcfcecc64e09155b5835c941d39bbf
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
a non-dispatchable umbrella. Root TypeScript declarations and both Python package
lanes are terminal. TypeScript package source is integrated through
`c145091039e6228dc85705d80165abe7cacd2ebb`, but a superseding fresh review of
exact source candidate `1bf66e1df2169297572b78acd58f6906a1987b21`
returned `REWORK REQUIRED`. The existing owner is repairing indirect CommonJS
loader, TypeScript reference-directive, CSS escaped-identifier, and plan-
overstatement findings without installing or creating a lock. The coordinator
retains the paused sequential TypeScript lock and executable-verification cells.

The worktree/architecture harness is integrated through `cdcfc1c`; its real-tree
checker passes while web/desktop coverage and the real two-stack product demo
remain dependency-gated. Corrected LangChain evidence is integrated through
`48dc5e6`, and auth/header evidence through `6d9da2d`; every live-dependent row
remains blocked and no capability was enabled. Documentation, attachment,
plan-approval, research/writing, and three coding-contract workers own disjoint
external paths. The fixture-corpus plan is reviewed and sealed at dispatch seed
`dff977b` without creating any corpus yet. Classic responsive web remains the
public baseline; every unproved external capability stays disabled with its
documented fallback.

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
| DW-M1-API-SCAFFOLD | 1 | completed (`2a4d8eb`) | `3dbe662` | `apps/api/**` | W0.1 | terminal with open contract fallbacks |
| DW-M1-AGENT-SCAFFOLD | 1 | completed (`cd3c00f`) | `3dbe662` | `packages/agent/**` | W0.1 | terminal with open contract fallbacks |
| DW-M1-TS-SCAFFOLD | 1 | fourth bounded rework active after `1bf66e1` review | `c145091` integrated as unaccepted evidence / owner at `1bf66e1` | `packages/domain/**`, `packages/sdk/**`, `packages/ui/**` | root TS terminal | close indirect-loader, TS-directive, CSS-escape, and plan-overstatement findings; fresh review |
| DW-M1-TS-LOCK-001 | 1 | blocked before execution | freshly accepted TS source | `pnpm-lock.yaml` and lock ExecPlan | TS source terminal | pinned Node/pnpm first-lock, frozen install, no-drift |
| DW-M1-TS-VERIFY-001 | 1 | pending | terminal lock cell | package-local executable checks/fixes | TS lock terminal | independent executable review |
| DW-EXT-W1-WORKTREE-ARCH-HARNESS | 1 | integrated (`a9be010`, adaptation `cdcfc1c`) | `8518782` / seed `7eb7900` | `tools/architecture/**`, `tools/worktree/**`, harness fixtures/research/packet | web/desktop coverage and real product-demo peer absent | keep `SPIKE-HARNESS-ARCH-001` and `SPIKE-WORKTREE-001` open |
| DW-EXT-W1-LANGCHAIN-CONTRACT-RESEARCH | 1 | integrated blocked evidence (`48dc5e6`) | `8518782` / seed `4c03e09` | `tools/contract-spikes/langchain/**`, LangChain research/packet | all 11 rows blocked on package/live evidence | enable nothing; await approved package index/classic sandbox |
| DW-EXT-W1-DOCS-HARNESS-ACCEPTANCE | 1 | active external | `b9d2444` / seed `552dca0` | `tools/docs/**`, docs fixtures/research/packet | current canonical corpus | await independently reviewed commit SHA |
| DW-EXT-W1-AUTH-HEADER-CONTRACT-RESEARCH | 1 | integrated blocked evidence (`6d9da2d`) | `b9d2444` / seed `9efbca4` | `tools/contract-spikes/auth/**`, auth research/packet | 432 blocked, 184 rejected, zero accepted-live; origin/header conflicts open | keep `SPIKE-AUTH-002` and Agent Server origin discovery unresolved |
| DW-EXT-W1-FIRST-TASK-SAFE-ATTACHMENTS | 1 | active external | `fff1bfd` / seed `e0f1087` | attachment contract probe/research/packet | public evidence; live object/scanner/runtime rows blocked | await independently reviewed clean commit SHA |
| DW-EXT-W1-FIRST-TASK-PLAN-APPROVAL | 1 | active external, offline harness only | `fff1bfd` / seed `886f6b1` | plan-approval contract probe/research/packet | HITL/compose/config rows blocked; live sandbox absent | await independently reviewed clean commit SHA; no target-spike acceptance |
| DW-EXT-W1-RESEARCH-WRITING-OUTCOME-CONTRACT | 1 | active external | `fff1bfd` / seed `ab13e25` | research/writing outcome probe/research/packet | upstream/public-package/live evidence blockers | await independently reviewed clean commit; zero E2E credit |
| DW-EXT-W1-CODING-SANDBOX-CONTRACT-RESEARCH | 1 | active external offline phase | `b224310` / seed `5a518c4` | sandbox contract probe/research/packet | public/index evidence; sanctioned live sandbox absent | await reviewed commit; live rows blocked |
| DW-EXT-W1-CODING-GITHUB-CONTRACT-RESEARCH | 1 | active external offline phase | `b224310` / seed `cb8c6ee` | GitHub contract probe/research/packet | consumes accepted sandbox evidence for live proxy/egress | no PAT; zero or exactly one authorized draft PR |
| DW-EXT-W1-CODING-REVIEW-SURFACES-CONTRACT-RESEARCH | 1 | active external offline phase | `b224310` / seed `f3d937f` | review-surface contract probe/research/packet | consumes accepted sandbox and GitHub evidence for live rows | no fake PTY/browser; await reviewed commit |
| DW-M1-FIXTURE-CONTRACT | 1 | active implementation from reviewed dispatch seed | reviewed seed `dff977b` | `internal/fixtures/product-demo/**` plus living plan | terminal API/agent; no TS/install dependency | independently review install-free 13-positive/12-negative corpus |
| DW-M1-INTEGRATION | 1 | next visible-product cell; plan preparation pending | accepted TS verification and fixture corpus | shared/root, `apps/web/**`, generated outputs | terminal TS executable proof and accepted fixture corpus only | compose one credential-free product demo with blocked/offline research fallbacks |
| DW-W2-DURABLE-CORE-PLANNING | 2 | read-only decomposition active; no implementation dispatch | current coordinator integration | plan-only paths to be made disjoint before dispatch | demo/isolation gate before any colliding full stack | prepare persistence/session/object/job cells for post-demo fan-out |
| Waves 2-6 | 2-6 | pending | accepted predecessor | bounded per reviewed plan | prior exit gates | v1 scenario qualification |
| v1.x, v2, v3 | later | pending | accepted release predecessor | discovery-derived cells | reviewed discovery gates | executable plans |

The graph is acyclic. Root/shared ownership remains with the coordinator until a
later reviewed cell explicitly reassigns it.

## Active agents, branches, and worktrees

| Role | Cell | Branch | Worktree | State |
|---|---|---|---|---|
| coordinator | Wave 1 integration | `claude/deepwork-project-planning-3y91wd` | `/Users/tomspencer/dev/deepwork/deepwork-planning` | sole integrator; TS lock paused; coordinating source rework and external results |
| API lane | authored API; reviewed agent/TS plan | `codex/api/wave1-scaffold` | `/Users/tomspencer/dev/deepwork/worktrees/w1-api` | completed and integrated |
| agent lane | authored agent; reviewed API/TS source | `codex/agent/wave1-scaffold` | `/Users/tomspencer/dev/deepwork/worktrees/w1-agent` | completed and integrated; returned TS findings |
| TS lane | bounded source rework after superseding review | `codex/domain/wave1-ts-scaffold` | `/Users/tomspencer/dev/deepwork/worktrees/w1-ts` | existing owner fixing four findings after rejected `1bf66e1`; no install/lock; lock paused |
| external docs accelerator | documentation-harness acceptance | `external/platform/documentation-harness-acceptance` | `/Users/tomspencer/dev/deepwork/worktrees/external-documentation-harness-acceptance` | recovery task `019f8da0-35cf-7d43-b6bb-c4b0cc78aaee`; external-owned; active |
| external attachment accelerator | safe first-task files | `external/research/first-task-safe-attachments` | `/Users/tomspencer/dev/deepwork/worktrees/external-first-task-safe-attachments` | continuation task `019f8da0-3f42-7542-b985-718e0e4aa763`; external-owned; active |
| external plan accelerator | plan before execution | `external/research/first-task-plan-approval` | `/Users/tomspencer/dev/deepwork/worktrees/external-first-task-plan-approval` | continuation task `019f8da0-487d-7233-a8b2-097f2063988f`; external-owned; active |
| external research/writing accelerator | verifiable outcome contract | `external/research/research-writing-outcome-contract` | `/Users/tomspencer/dev/deepwork/worktrees/external-research-writing-outcome-contract` | task `019f8da1-001f-7a72-80e8-fc98d89cd31c`; seed `ab13e25`; active |
| external coding sandbox accelerator | coding sandbox contracts | `external/research/coding-sandbox-contracts` | `/Users/tomspencer/dev/deepwork/worktrees/external-coding-sandbox-contracts` | task `019f8db1-7c00-7d22-a0a3-a986b060c137`; seed `5a518c4`; active |
| external coding GitHub accelerator | GitHub/App/proxy/CI contracts | `external/research/coding-github-contracts` | `/Users/tomspencer/dev/deepwork/worktrees/external-coding-github-contracts` | task `019f8db1-85b4-7d20-81d4-4f032433d699`; seed `cb8c6ee`; active |
| external coding review accelerator | file/diff/terminal/browser contracts | `external/research/coding-review-surfaces-contracts` | `/Users/tomspencer/dev/deepwork/worktrees/external-coding-review-surfaces-contracts` | task `019f8db1-9109-7d62-aa73-5e275dff9e77`; seed `f3d937f`; active |
| fixture corpus lane | reviewed install-free corpus plan | `codex/contracts/wave1-fixture-corpus` | `/Users/tomspencer/dev/deepwork/worktrees/w1-fixture-contract` | task `019f8db6-b09a-7f42-8233-9c20a9ffc496`; exact seed `dff977b`; active |

## Progress

- [x] 2026-07-23 13:00 AEST — Program directive accepted; repository baseline
  verified at `500eaa7faff57def970963160b3d8f1e90c94398`.
- [x] 2026-07-23 — Wave 0.1 schema, authority, gate, dispatch, concurrency, and
  roadmap hardening validated, independently reviewed, and committed at
  `3dbe6629d8053380ab6a8bff6d2fcb462f854256`.
- [x] 2026-07-23 — Root TypeScript declarations/config completed and independently
  reviewed through `8323084697fe9d7c1aac1c2b07fadf66cc92dff5`; no lock or
  executable package claim made.
- [x] 2026-07-23 — Fixture-only API and independent agent package implementations
  passed fresh cross-review after bounded rework and integrated locally through
  `2a4d8eb937bfe5d43669377567d46b2651972242`.
- [x] 2026-07-23 — TypeScript package source/static authoring passed two internal
  review rounds after bounded rework and integrated locally through
  `03b019ab6a5d71e2911a6019013a089cca098101`; no executable claim was made.
- [ ] 2026-07-23 — A superseding exact-candidate review of `1bf66e1` found three
  remaining false-green scanner paths: parenthesized/indirect CommonJS loaders,
  TypeScript reference directives, and CSS escaped identifiers. It also required
  plan wording to distinguish authored checks from executed proof. A fourth
  bounded rework is active in the original package lane; the architecture
  checker/tool-config classification remains separately accepted at `cdcfc1c`.
  The coordinator has run no install or lock command.
- [x] 2026-07-23 — External accelerators became active from exact implementation
  base `85187827e018d4aeee4a4e4bd685de49cb2f5a6a`, seed commits `7eb7900` and
  `4c03e09`, in their supplied worktrees. The coordinator will not duplicate
  their scopes and remains sole integrator.
- [x] 2026-07-23 — Documentation-harness and API-key/header packets passed
  independent read-only review, were recorded at `35b3adb`, and became active
  external tasks from seeds `552dca0` and `9efbca4`. Their paths remain
  external-owned.
- [x] 2026-07-23 — Safe-attachment and plan-approval packets passed independent
  read-only review at `0891678`; both are dispatch-only research cells from
  `fff1bfd`. Plan approval remains offline-harness-only and cannot accept its
  target spikes on that base.
- [x] 2026-07-23 — Safe-attachment and plan-approval workers became active from
  seeds `e0f1087` and `886f6b1`; their paths remain externally owned.
- [x] 2026-07-23 — Research/writing outcome packet passed final independent
  review at `7fedc6a`; all upstream/package/live dependencies remain blocked and
  the packet credits zero E2E acceptance.
- [x] 2026-07-23 — The worktree/architecture harness and its real-tree source-root
  adaptation integrated through `cdcfc1c`. Architecture, worktree, doctor, and
  self-test proof is green, but real web/desktop coverage and dual-stack
  acceptance remain open, so neither harness/worktree spike is closed.
- [x] 2026-07-23 — Corrected LangChain contract evidence integrated through
  `48dc5e6`; all 11 rows remain `blocked-live-evidence`, and no runtime capability
  was enabled.
- [x] 2026-07-23 — Auth/header evidence integrated through `6d9da2d`: 616 matrix
  rows, 432 blocked, 184 locally rejected, and zero accepted live. `SPIKE-AUTH-002`,
  the organization-header conflict, and Agent Server origin discovery stay open.
- [x] 2026-07-23 — Three reviewed coding-contract packets were accepted at
  `c718387` and seeded independently at `5a518c4`, `cb8c6ee`, and `f3d937f`.
  Offline workers are active; live proof remains ordered sandbox to GitHub to
  review surfaces, with no PAT, fake PTY/browser, or E2E credit.
- [x] 2026-07-23 — The fixture-corpus plan fixed its dispatch lifecycle and
  deterministic latency case, passed independent review at `7e404d9`, and was
  sealed at exact implementation seed `dff977b`. The install-free corpus worker
  is active as task `019f8db6-b09a-7f42-8233-9c20a9ffc496`.
- [ ] Complete TypeScript source rework, then the coordinator-owned lock and executable-verification
  sequence.
- [ ] Independently accept the fixture corpus, then dispatch the one permitted
  credential-free `apps/web` product-demo cell as soon as TypeScript executable
  proof is terminal. Optional attachment, plan-approval, research/writing, and
  coding live rows are not prerequisites; consume their blocked/offline fallbacks.
- [ ] Prepare reviewed, path-disjoint Wave 2 durable-core cells now, but do not
  start a colliding full stack before the demo/isolation gate.
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
- 2026-07-23 — Observation: initial Python package checks overstated proof: the
  agent verifier rewrote stale hashes, while the API eagerly loaded framework
  modules and left non-bootstrap downloads possible. Consequence: accepted cells
  now use immutable double-build evidence, lazy public imports, fail-closed offline
  commands, installed-launcher execution, and exact wheel-content scans.
- 2026-07-23 — Observation: first TS source review found `package-check` aliased to
  architecture scanning, promised negative fixtures absent, and component scale
  constants outside `tokens.css`. Consequence: source stays unintegrated until
  clean-consumer proof is authored, negative cases exist, and UI values consume
  the canonical token source.
- 2026-07-23 — Observation: the first TS repair still covered only a subset of
  scanner rule codes. Consequence: a second bounded repair completed the matrix;
  fresh review accepted exact emitted/declared counts of domain 9, SDK 9, and UI
  10 before local integration.
- 2026-07-23 — Observation: exact rule-code coverage did not prove that the
  package-local policy itself was complete. External review found clean-typecheck,
  global network-denial, allowlist/path-containment, packed TypeScript-consumer,
  immutability, retry, heading, timestamp, and run-key gaps. Consequence: rescind
  lock handoff and require bounded rework plus fresh review.
- 2026-07-23 — Observation: the harness passed against its original seed but the
  integrated tree added Node-run package tool configs. Consequence: architecture
  coverage is now derived from declared source markers, with explicit
  noncanonical/file/symlink rejection and positive Node-only Vitest-config proof,
  rather than deleting correct `node:url` package tooling.
- 2026-07-23 — Observation: public/installed auth evidence cannot resolve the
  organization-header conjunction or discover a trustworthy Agent Server origin.
  Consequence: integrate the 616-row matrix only as blocked/rejected evidence;
  keep all positive live behavior unavailable.
- 2026-07-23 — Observation: the first fixture plan made pre-dispatch acceptance
  depend on a future implementation commit and omitted deterministic latency.
  Consequence: seal the independently reviewed plan before implementation and
  require fixed-tick enqueue, release, visibility, and completion evidence.
- 2026-07-23 — Observation: multiple user-owned external accelerator tasks now
  run in dedicated worktrees from reviewed seed commits. Consequence: internal
  cells exclude every external allowed path, and the coordinator waits for an
  independently reviewed clean commit SHA before integration.
- 2026-07-23 — Observation: an initially reported acceptance of `1bf66e1` was
  superseded by a fresh exact-candidate `REWORK REQUIRED` verdict covering three
  scanner bypass families and one plan overstatement. Consequence: revert the
  premature completed-plan transition, retain the coordinator cherry-picks only
  as unaccepted evidence, route bounded work to the existing `w1-ts` owner, and
  keep the first shared lock paused.

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
- 2026-07-23 — Decision: keep every active external accelerator task externally
  owned and disjoint. Rationale: the user dispatched them as accelerators.
  Consequence: no internal agent duplicates those scopes; the coordinator is the
  sole integrator after independent review.
- 2026-07-23 — Decision: integrate LangChain and auth/header results only as
  bounded blocked/rejected contract evidence. Consequence: package-index,
  sanctioned-sandbox, header, and origin blockers remain explicit and no
  capability availability changes.
- 2026-07-23 — Decision: run coding research offline in parallel while preserving
  live order sandbox to GitHub to review surfaces. Consequence: no PAT, fabricated
  PTY/browser, live proxy, or draft-PR claim may substitute for the missing gates.
- 2026-07-23 — Decision: make terminal TypeScript executable proof plus the
  accepted fixture corpus the critical path to the credential-free `apps/web`
  demo. Consequence: optional research live rows neither block nor satisfy the
  demo; their documented unavailable/offline fallbacks are consumed.
- 2026-07-23 — Decision: prepare Wave 2 durable-core decomposition in parallel,
  but do not start a colliding full-stack worktree before the demo/isolation gate.
  Consequence: persistence, session, object, and job cells may fan out only after
  their reviewed plans and the gate permit it.

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

Wave 0.1, root TypeScript declarations, the fixture-only API package, and the
independent agent package are terminal local integration cells. TypeScript package
source is in its fourth bounded repair after rejected `1bf66e1`; lock and
executable claims remain downstream and paused. The architecture/worktree,
LangChain, and auth/header integrations are retained without closing their live or
real-product gates. Seven external research workers and the fixture-corpus worker
remain path-disjoint; no result is accepted without an independently reviewed
clean commit SHA. The next visible-product cell is one credential-free `apps/web`
demo after terminal TypeScript proof and fixture acceptance, while Wave 2
durable-core plans are prepared without starting another full stack.
No protected `docs/plans/**` file, external credential, production system, push,
merge, deployment, or publication has been touched. The terminal outcome remains
the verified complete canonical vision through v3, or an exact blocker ledger
after every independent DAG branch is exhausted.
