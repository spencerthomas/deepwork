# Post-review integration and merge map

Status: staged proposal. This file describes a future integration; it does not
authorize changes outside `docs/proposals/2026-07-22-product-plan-audit/`.

Current measured validation and drift are recorded in the
[proposal integrity report](integrity-report.md).

## Protected evidence

| Evidence set | Pin | Role |
|---|---|---|
| Canonical Deep Work planning repository | `06f051554bf938e919af5ab7855974098fbf3d2a` | Product/plan baseline to reconcile, not preserve as unquestioned truth |
| Frontend prototype | `8866d39a2888e358091208063693f260cff6d261` | Interaction/visual evidence only; one-way migration |
| LangChain documentation | `7b9215d708e0b57e6fbae7b5d0762c4118b8e309` | Pinned primary runtime prose evidence |
| Deep Agents | `7794b61a6e76230e8c7a49bdce808b3728305914` | Python engineering/reuse evidence |
| LangChain Python | `592055e15e138f5369dce95dd049ce22430996e2` | Python public API/type/test evidence |
| LangChain.js | `ee76ea0347fb611153e5ec7d0e70fa405f5293a3` | TypeScript package/conformance/release evidence |
| LangGraph | `31f90df3e6b0268fa77fd2d118a917d420b84a68` | SDK/package evidence; public/live behavior remains spike-gated |
| Protected delivery-plan observation | 957 lines; SHA-256 `5e6a30202417d6261e2bd4e973e7b71d92171e9a8cbf8031753a93c1632bf813` | Frozen evidence observed on 2026-07-22, before concurrent drift |
| OpenAI Harness Engineering | Published 2026-02-11; accessed 2026-07-23 | Repository-harness method |
| OpenAI ExecPlan guidance | Published 2025-10-07; accessed 2026-07-23 | Living implementation-plan method |
| OpenAI Symphony | `openai/symphony@1f3219bb1ea5f69a1305dc594e79b0db57c113c5` | Engineering-preview orchestration evidence |

## Current integrity exception

G0 is currently **failing**. A read-only reconciliation observed:

- the protected delivery-plan path at 986 lines with SHA-256
  `3f4b6ed96054289426ac6c53ee6b4702484a934067a11b5761c0d68d756e3b0c`, not the
  frozen 957-line artifact; and
- ten additional untracked files outside this proposal under `docs/plans/`.

The sibling frontend is currently at `26c698b30ff08d5122cfaeedbd4a95296a7884f4`,
not the audited `8866d39` pin, and has three untracked `.DS_Store` files. The pinned
commit remains locally available, so the existing audit is reproducible but does
not claim to cover the newer checkout.

Their ownership is unknown. This proposal does not edit, delete, move, or normalize
them. Before integration, the owner must either restore the frozen artifact or
review and accept a new explicitly hashed baseline, then classify every unrelated
file. “Tracked diff is empty” is not sufficient while untracked scope has changed.

## Review gates

No canonical or prototype file changes until G0-G8 pass.

| Gate | Required result |
|---|---|
| G0 — package integrity | Proposal links/IDs/counts pass; all proposal work is isolated; protected evidence has a stable accepted hash; unrelated untracked files are reconciled. |
| G1 — evidence | Every material external claim has a primary source, pin/version/tier/date, and confidence classification. Engineering method is separate from runtime authority. |
| G2 — runtime contracts | Classic deployment is public baseline; gated adapters are capability-detected; unsupported Fleet CRUD, `/v1/deepagents/*`, global thread search, arbitrary connector routes, and `mda deploy` reimplementation are absent; every disagreement has a spike/fallback. |
| G3 — product decisions | Audience/team compatibility, auth fallback, durable state, five-tab IA, lifecycle actions, no force-resolve, settings ownership, save/deploy, mobile split, memory review, and future boundary are accepted. |
| G4 — application architecture | Python API/worker/Postgres/outbox/objects/secrets, independent agent package, one application stream, domain/SDK/UI graph, state/credential matrices, source aggregation, PWA, and gated Tauri are accepted. |
| G5 — Harness architecture | Canonical document taxonomy, short progressive `AGENTS.md`, root architecture, two fixture modes, machine graph/check, living ExecPlans, generated views, worktree isolation, quality/debt/gardening, and proof loop are accepted. |
| G6 — coverage/readiness | Every route, tab, settings section, delivery unit, criterion, backlog item, and Harness concern has one owner; all v1 plans contain the required states/interfaces/fallback/security/accessibility/metrics/rollout/scenarios; no enabled unverified contract is labelled ready. |
| G7 — Symphony pilot policy | Revision, tracker adapter, state/label/blocker model, pre-workspace dispatch gate, safe workspace, credentials/network/approval, concurrency, reconciliation/retry/restart, distinct Agent Review, Human Review, emergency stop, cleanup, and fallback are accepted through `SPIKE-SYMPHONY-001`. If not, manual dispatch is the accepted implementation path and `WORKFLOW.md` is not installed. |
| G8 — specialist review | Product, runtime contracts, architecture/platform, security/privacy, frontend/accessibility, desktop, documentation/developer experience, and OSS maintainers approve their boundaries. |

After integration, G9 runs clean-clone, package, generated-contract, architecture,
docs, fixture/product-demo, security, accessibility, and traceability validation.

## Target canonical knowledge structure

```text
deepwork/
├── AGENTS.md
├── ARCHITECTURE.md
├── WORKFLOW.md                     # only after accepted Symphony spike
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md                     # disclosure entry point
├── tools/{architecture,docs,worktree}/
└── docs/
    ├── AGENTS.md
    ├── DESIGN.md
    ├── FRONTEND.md
    ├── PLANS.md
    ├── PRODUCT_SENSE.md
    ├── QUALITY_SCORE.md
    ├── RELIABILITY.md
    ├── SECURITY.md
    ├── design-docs/{index.md,core-beliefs.md,architecture/,decisions/,engineering/}
    ├── exec-plans/{index.md,active/,completed/,templates/,tech-debt-tracker.md}
    ├── generated/{README.md,db-schema.md,openapi.json,package-graph.md,architecture-graph.md,feature-coverage.md,issue-map.md,route-inventory.md}
    ├── product-specs/{index.md,glossary.md,foundations/,onboarding/,tasks/,approvals/,coding/,agents/,operations/,surfaces/,quality/,future/}
    └── references/{index.md,source-ledger.md,audits/,contracts/,research/,legacy-plans/,design-system-reference-llms.txt,uv-llms.txt}
```

This taxonomy supersedes the old split between `docs/plan/` and `docs/plans/`.
Do not copy old and new authorities side by side. Preserve historical sources
under `docs/references/legacy-plans/` and update inbound links in the same change.

## Proposal-to-canonical destinations

| Proposal source | Exact destination after review | Integration action |
|---|---|---|
| `FINAL-PLAN.md` | `docs/PLANS.md` | Adopt as the program roadmap and planning-system entry point; replace proposal/integrity text with accepted state and link the ExecPlan template. |
| `harness/proposed-ARCHITECTURE.md` | `ARCHITECTURE.md` | Install concise canonical map after reconciling accepted application architecture and package names. |
| `architecture/application-architecture.md` | `docs/design-docs/architecture/application-architecture.md` | Preserve full rationale, diagrams, state/credential ownership, failures, tradeoffs, and accepted ADR links. |
| `architecture/engineering-conventions.md` | `docs/design-docs/engineering/conventions.md` plus `CONTRIBUTING.md` | Keep technical convention detail in design docs; extract contributor entry path/community workflow without duplication. |
| `harness/exec-plan-template.md` | `docs/exec-plans/templates/feature.md` | Install required living sections and validation/recovery contract. |
| `harness/symphony-work-item-template.md` | selected tracker issue template | Install only after adapter/state schema acceptance. |
| `harness/proposed-WORKFLOW.md` | `WORKFLOW.md` | Replace explicit spike placeholders with accepted typed values and install only after `SPIKE-SYMPHONY-001`. |
| `catalog/source-ledger.md` | `docs/references/source-ledger.md` | Preserve full pins, confidence classes, accepted spike memos, and supersession. |
| `catalog/glossary.md` | `docs/product-specs/glossary.md` | Make canonical vocabulary and external-term mappings available to every spec. |
| `catalog/decision-register.md` | `docs/design-docs/decisions/index.md` | Split accepted decisions into ADRs where needed; retain unresolved spikes with owner/fallback. |
| `catalog/feature-catalog.md`, `catalog/coverage-matrix.md`, and `catalog/acceptance-scenario-index.md` | sources for `docs/generated/feature-coverage.md` | Generate one-owner scope plus criterion -> E2E -> feature-scenario traceability from product-spec metadata; do not maintain a second manual table after migration. |
| `audits/01-frontend.md` through `06-harness-and-orchestration.md` | `docs/references/audits/2026-07-22-product-plan-audit/` | Preserve as evidence; apply accepted findings to canonical docs/specs rather than treating audits as ongoing authority. |
| `agent-guidance/proposed-AGENTS.*.md` | destinations below | Reconcile and install together after their directories/canonical links exist. |

If a destination exists by integration time, reconcile it line by line and record
supersession. Never overwrite newer accepted guidance.

## Legacy canonical-plan reconciliation

| Current source at pin `06f0515` | New authority | Required action |
|---|---|---|
| `docs/plan/01-vision.md` | `docs/PRODUCT_SENSE.md` plus owning product specs | Resolve single-user/team, no-database, auth, scope, memory, and success contradictions; archive original. |
| `docs/plan/02-architecture.md` | root `ARCHITECTURE.md` plus detailed application design doc | Adopt API/worker/Postgres/outbox/object/secret, agent-package, client, stream, PWA/Tauri, and architecture-check decisions; archive original. |
| `docs/plan/03-ui-spec.md` | `docs/DESIGN.md`, `docs/FRONTEND.md`, product specs | Reconcile five-tab IA, route/tab/settings dispositions, complete state/responsive/accessibility model, and no force-resolve; archive original. |
| `docs/plan/04-roadmap.md` | `docs/PLANS.md` | Replace duplicated sequencing with the exit-gated program roadmap and generated issue/DAG map; archive original. |
| `docs/plan/05-oss-setup.md` | `DW-FND-001` product spec, engineering design doc, `CONTRIBUTING.md` | Adopt independent Python locks, TS/Rust method, Harness docs, fixture/worktree loop, checks, release/community policy; archive original. |
| `docs/plan/06-frontend-implementation.md` | frontend product specs plus a new active migration ExecPlan | Replace browser/provider and prototype ownership assumptions; preserve only reviewed one-way migration steps. |
| `docs/plan/07-org-intelligence.md` | operations/future product specs | Preserve reviewed Layers 0–1 and gated later layers; archive original. |
| `docs/plan/08-deepagents-feature-map.md` | `docs/references/` evidence plus owning product specs | Retain pinned reuse evidence without making private modules or hosted contracts canonical. |
| `docs/research/**` | `docs/references/research/**` | Preserve provenance/status and update links; research remains below accepted contracts/decisions. |

## Feature-plan destinations

Stable-ID proposal plans become durable product specifications, not ExecPlans:

```text
plans/v1/dw-fnd-*    -> docs/product-specs/foundations/
plans/v1/DW-ONB-*    -> docs/product-specs/onboarding/
plans/v1/DW-TASK-*   -> docs/product-specs/tasks/
plans/v1/DW-HITL-*   -> docs/product-specs/approvals/
plans/v1/DW-CODE-*   -> docs/product-specs/coding/
plans/v1/dw-agent-*  -> docs/product-specs/agents/
plans/v1/dw-ops-*    -> docs/product-specs/operations/
plans/v1/dw-surf-*   -> docs/product-specs/surfaces/
plans/v1/dw-qual-*   -> docs/product-specs/quality/
plans/v1x|v2|v3/**   -> docs/product-specs/future/<release>/
```

Keep every stable feature ID and filename. Normalize case only through a separately
reviewed all-links migration; do not silently rename IDs. Front matter gains
canonical status, owner, governed paths, accepted decisions, and scenario IDs.

Feature-level `dependencies` remain product integration context. Before Symphony,
decompose them into bounded work items and prove the generated blocker graph is
acyclic. Specifically split service/SDK/domain skeleton from live integration,
source connection from first-task completion, base stream from HITL, artifact
contract from coding activation, draft/version schema from deploy activation,
responsive web from PWA push, and web release from desktop/beta adapters.

## Protected delivery-plan disposition

The frozen 957-line delivery plan remains evidence. After G0 resolves its current
drift:

1. preserve the accepted evidence artifact under
   `docs/references/legacy-plans/2026-07-22-v1-delivery-plan.md` with original hash,
   status, and superseded-by link;
2. absorb useful U1–U19 ownership and sequencing into `docs/PLANS.md` and generated
   feature/issue traceability;
3. map every U1–U19 unit to stable feature IDs in the archived appendix;
4. remove duplicate implementation authority, stale paths, and unsupported
   contracts from the active planning system—not by rewriting historical evidence;
   and
5. preserve the move/supersession in version history.

This amends the earlier idea of editing the legacy file into a program index: the
consolidated reviewed final plan is the cleaner program authority and the legacy
artifact remains inspectable evidence.

## `AGENTS.md` destinations

| Staged draft | Destination | Merge condition |
|---|---|---|
| `proposed-AGENTS.root.md` | `AGENTS.md` | Canonical links/commands/package graph accepted; keep concise |
| `proposed-AGENTS.docs.md` | `docs/AGENTS.md` | New taxonomy/index/generated rules accepted |
| `proposed-AGENTS.apps-api.md` | `apps/api/AGENTS.md` | API/state/credential/layer model accepted and directory exists |
| `proposed-AGENTS.apps-web.md` | `apps/web/AGENTS.md` | Client/domain/SDK/fixture boundaries accepted |
| `proposed-AGENTS.apps-desktop.md` | `apps/desktop/AGENTS.md` | Tauri/Rust/remote-origin boundary accepted and directory exists |
| `proposed-AGENTS.packages-agent.md` | `packages/agent/AGENTS.md` | Agent layout/entry point/public API accepted |
| `proposed-AGENTS.packages-domain.md` | `packages/domain/AGENTS.md` | Pure domain graph accepted |
| `proposed-AGENTS.packages-sdk.md` | `packages/sdk/AGENTS.md` | Browser-safe/client-core boundaries accepted |
| `proposed-AGENTS.packages-ui.md` | `packages/ui/AGENTS.md` | Presentation-only dependency accepted |
| `proposed-AGENTS.frontend-sandbox.md` | sibling `deep-work-frontend/AGENTS.md` | Separate review/PR; never included in canonical copy operation |

Install canonical-monorepo drafts in one reviewed change. The sibling prototype
change is always separate.

## Symphony integration

1. Complete `SPIKE-SYMPHONY-001` against the pinned revision and selected tracker.
2. Record accepted adapter, issue scope/identity, states, labels, blocker semantics,
   dispatchable predicate, credentials, sandbox/approval, network, workspace root,
   hooks, concurrency, timeouts, retry/reconciliation, Human Review, cleanup, and
   emergency disable in the decision register.
3. Replace every placeholder in `harness/proposed-WORKFLOW.md`; validate it with
   the pinned implementation and generated Codex app-server schema.
4. Pilot one low-risk docs/fixture/package issue, then two independent issues at
   concurrency two. Run blocked/DAG, state-change stop, crash/restart,
   duplicate-effect/PR, credential exposure, and cleanup cases.
5. Install `WORKFLOW.md` and issue template only after evidence is accepted.
6. Start at maximum concurrency two. Migrations, production credentials, signing,
   publishing, external deployment, and automatic merge remain ineligible until a
   separately reviewed policy expands authority.
7. If the pilot fails, retain the issue/ExecPlan schema and use manual one-agent
   worktrees. Do not make product delivery depend on Symphony internals.

## Integration sequence

1. Restore or accept a new G0 baseline and classify every outside-proposal file.
2. Review `FINAL-PLAN.md`, decisions, spike owners/fallbacks, and specialist gates.
3. Create the target doc directories/indexes and install the accepted program,
   product-sense, architecture, topical, design, reference, generated, and ExecPlan
   sources with supersession metadata.
4. Copy accepted stable-ID plans into product-spec categories and generate coverage;
   archive legacy plans/research with updated links.
5. Install canonical `AGENTS.md` files, stable commands, architecture/docs manifests
   and checks, two fixture modes, worktree namespace, proof paths, quality score,
   and debt/gardening policy.
6. Preserve/archive the accepted legacy delivery plan and generate U1–U19 mapping.
7. Run the Symphony spike/pilot; install `WORKFLOW.md` only on acceptance.
8. Reconcile the frontend prototype in a separate change; never add it as a
   canonical dependency.
9. Run G9 from a clean checkout and attach the evidence manifest to the integration
   pull request.

## G9 validation

The integration pull request must show:

- clean `git diff`/untracked scope and accepted evidence hashes;
- zero broken/orphaned canonical links, duplicate IDs, missing owners/statuses,
  glossary conflicts, living-plan-section failures, or generated drift;
- 39 stable product specifications and one generated owner per covered surface;
- acyclic generated work-item blocker graph;
- intentional Python/TypeScript/browser/provider boundary violations fail with
  actionable diagnostics;
- independent API/agent builds and clean installs, TypeScript package consumers,
  deterministic OpenAPI/client generation, and no-network unit suites;
- UI harness plus isolated API-backed product demo acceptance;
- accessibility/security/fixture parity tests appropriate to the scaffold; and
- Symphony pilot evidence or the explicit manual-dispatch fallback decision.

Keep this proposal as the immutable review record. Later implementation changes
link back to accepted canonical sources, not to hidden chat context.
