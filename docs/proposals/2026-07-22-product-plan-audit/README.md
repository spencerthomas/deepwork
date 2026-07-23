# Deep Work product-plan audit

Status: **proposed for review**
Created: 2026-07-22
Canonical plans changed by this proposal package: **none**

This package audits the current Deep Work prototype, the pinned LangChain documentation checkout, the product vision, the existing delivery plan, pinned LangChain/Deep Agents/LangGraph/LangChain.js reference code, and the official OpenAI Harness/ExecPlan/Symphony method. It then proposes a complete, traceable plan library, application architecture, repository harness, contributor method, and issue-driven implementation roadmap without intentionally changing `docs/plan/`, `docs/plans/`, either sibling repository, or runtime code.

## Frozen baselines

| Source | Commit or artifact | Role |
|---|---|---|
| `deep-work-frontend` | `8866d39` | Visual and interaction evidence only |
| `langchain-docs-reference` | `7b9215d` | Primary documentation snapshot for external contracts |
| `deepwork` | `06f0515` | Canonical vision, architecture, UI specification, and roadmap |
| Existing delivery plan | 957-line untracked file at `docs/plans/2026-07-22-001-feat-deepwork-v1-delivery-plan.md` | Preserved evidence; not edited by this proposal |
| `langchain-packages/deepagents` | `7794b61` | Python engineering, public reuse, agent, CLI/code/ACP/evals/Talon evidence; not service-contract authority |
| `langchain-packages/langchain` | `592055e` | Mature Python typing/package/test/public-API evidence |
| `langchain-packages/langchainjs` | `ee76ea0` | TypeScript package, conformance, Oxc, and release evidence |
| `langchain-packages/langgraph` | `31f90df` | Official SDK/package/recovery evidence; public/live behavior remains spike-gated |
| OpenAI Harness Engineering | Published 2026-02-11; accessed 2026-07-23 | Agent-first repository and architecture-enforcement method |
| OpenAI ExecPlan guidance | Published 2025-10-07; accessed 2026-07-23 | Living implementation-plan method |
| `openai/symphony` | `1f3219b`; accessed 2026-07-23 | Engineering-preview issue orchestration specification and workflow evidence |

## Reading order

1. Start with the [consolidated final plan and roadmap](FINAL-PLAN.md).
2. Read the six files in [`audits/`](audits/) in numerical order for evidence and findings.
3. Review the [source ledger](catalog/source-ledger.md), [glossary](catalog/glossary.md), [decision register](catalog/decision-register.md), and [acceptance-scenario index](catalog/acceptance-scenario-index.md).
4. Review the staged [application architecture](architecture/application-architecture.md) and [engineering/contributor conventions](architecture/engineering-conventions.md).
5. Use the [feature catalog](catalog/feature-catalog.md) and [coverage matrix](catalog/coverage-matrix.md) to find the owning plan for every experience and cross-cutting architecture/harness concern.
6. Review the detailed proposed v1 plans in [`plans/v1/`](plans/v1/) and the discovery-gated future briefs in the later-release folders. A proposal remains non-canonical and is never labelled implementation-ready while a contract or decision gate is open.
7. Review the staged [root architecture](harness/proposed-ARCHITECTURE.md), [living ExecPlan template](harness/exec-plan-template.md), [fail-closed Symphony workflow](harness/proposed-WORKFLOW.md), and [work-item template](harness/symphony-work-item-template.md).
8. Review the staged agent instructions and [placement map](agent-guidance/placement-map.md).
9. Read the [integrity report](integration/integrity-report.md), then use the [merge map](integration/merge-map.md) only after the package is accepted and G0 is restored.

## Proposed application architecture

The original plans define the agent runtime but do not define the application backend needed by the product. This proposal adopts the following v1 architecture for review:

- **Application service:** One independently locked Python 3.12/FastAPI/Pydantic/SQLAlchemy/Alembic distribution with separately deployed API and worker entry points. PostgreSQL owns sessions, server-only credential references, source registrations, idempotency/outbox/jobs, projections, and audit; S3-compatible storage owns approved application attachments/imports/exports.
- **Agent package:** A separate Python `deepagents` project deployed first to a classic LangSmith Deployment. Managed Deep Agents is a capability-detected private-beta adapter and remains CLI-managed.
- **Web and mobile v1:** Next.js 16, React 19, and TypeScript for the complete responsive web phone experience. Install/PWA/push cells enable per qualified browser after `SPIKE-PWA-001`; ordinary responsive web and in-app state are the fallback. Mobile-native remains post-v1.
- **Desktop v1:** Tauri v2 loads the trusted hosted Next.js application and adds secure native storage, deep links, tray state, notifications, and updates. It consumes the same FastAPI contract and does not duplicate product logic.
- **Shared client layer:** Pure `packages/domain`, browser-safe `packages/sdk`, and presentational `packages/ui`, plus private fixtures/conformance harnesses. Generated OpenAPI types remain inside SDK transport/mapping and raw wire contracts never enter presentation components.
- **Stream boundary:** Web/PWA/Tauri consume one normalized FastAPI application stream. Python adapters compose pinned public upstream SDKs and keep credentials/provider cursors server-side. Browser-direct streaming is an optional separately proven optimization, not the v1 baseline.
- **External runtime:** LangSmith control-plane and per-deployment Agent Server APIs remain separate from the application service. The application service is not a replacement Agent Server.

### Stack rationale

Python is the proposed application-service language because the selected agent package, contract spikes, sandbox/runtime adapters, official stream clients, and operational jobs center on the Python LangChain stack. Keeping those server-side integrations in one typed Python service avoids making Next.js routes or a browser SDK a second integration authority. The agent package still stays independently deployable: `apps/api` calls runtime contracts and never imports the graph as application business logic.

Next.js remains the right web layer because the audited prototype is already React/Next.js and the product needs a responsive PWA, but it is a client of the durable service rather than the owner of sessions, credentials, webhooks, jobs, or cross-source state. TypeScript remains the shared client/domain language through generated OpenAPI types, explicit SDK services/mappers, and the pure domain package. A standalone TypeScript service could satisfy the same boundary, but it would not remove the need for Postgres, migrations, background work, or a service independent of the web process.

Tauri is proposed for v1 desktop because the desktop outcome is host integration around the same product, not a second UI. Expo is deferred until native mobile capabilities justify a separate client beyond the PWA's task, approval, artifact, push, and deep-link journeys.

## Proposed harness and orchestration

- Root `AGENTS.md` stays a short map into `ARCHITECTURE.md`, topical docs, product specs, active ExecPlans, and stable commands. Nested guidance contains only directory-local ownership and checks.
- The accepted 39 stable-ID plans become durable product specifications. `FINAL-PLAN.md` becomes the program roadmap. Complex implementation gets a separate self-contained living ExecPlan.
- A machine-readable architecture graph and structural tests enforce legal Python/TypeScript/package/browser/provider edges with actionable repair messages.
- The repository exposes two named fixture paths: a browser-local UI/component harness and an API-backed full-product demo with isolated Postgres/object/telemetry resources.
- Pinned Symphony is piloted as an external developer orchestrator only after `SPIKE-SYMPHONY-001` proves the tracker adapter, issue states and blockers, credential isolation, safe workspaces, reconciliation, retry/recovery, and Human Review handoff. It is not the Deep Work product worker.
- The proposed implementation roadmap is an exit-gated sequence. Feature specifications are decomposed into acyclic work items before Symphony; narrative feature dependencies are never copied blindly into tracker blockers.

## Source precedence

1. Accepted live-contract or spike memo against pinned package/server versions.
2. Generated schemas/types or official primary documentation for those pinned versions.
3. Accepted Deep Work decision records and canonical architecture, UI, vision, and roadmap documents.
4. Approved Deep Work feature plans.
5. Internal research notes.
6. Frontend prototype and fixtures.

For engineering practice inside a reference repository, use executable
configuration/tests, then manifests/locks/generated artifacts, then scoped
`AGENTS.md`, then prose/examples. This does not alter the external-contract
precedence above.

When two levels disagree, the higher source wins and the affected proposal must be updated. A plan cannot be marked `ready` while an external contract remains an unbounded assumption.

## Review boundary

Everything in this directory is a proposal. No draft `AGENTS.md` applies to the repository yet. No feature disposition, architecture choice, or interface becomes canonical until the review package is accepted and the merge map is executed deliberately.

## Package manifest

| Area | Contents |
|---|---|
| Program | One consolidated product, architecture, harness, orchestration, and exit-gated roadmap for review |
| Audits | Six pinned audits covering frontend, LangChain contracts, vision/scope, existing plans, reference-code/community practices, and Harness/ExecPlan/Symphony method |
| Architecture | Staged application architecture plus engineering and contributor conventions |
| Harness | Concise root architecture, living ExecPlan template, fail-closed Symphony workflow draft, and schedulable work-item template |
| Catalog | Source ledger, glossary, 39-feature catalog, one-owner coverage matrix, 179 feature-scenario IDs, 12 release E2E scenarios, and decision/spike register |
| Agent guidance | Placement map plus staged root, docs, web, API, desktop, domain, SDK, agent, UI, and frontend-sandbox drafts |
| Plan library | 28 v1 proposals, 3 v1.x briefs, 7 v2 briefs, and 1 v3 brief |
| Integration | Exact post-review canonical destinations, gates, sequencing, delivery-plan conversion, and current integrity report |

## Current integrity exception

All edits made for this consolidation remain inside this proposal directory.
However, the repository currently contains concurrently created untracked files
under `docs/plans/`, and the protected untracked delivery-plan artifact no longer
matches its frozen 957-line hash. Their ownership is unknown, so this proposal does
not edit, delete, or normalize them. Review gate G0 is therefore **not passing** and
integration must wait until the external changes are reconciled and a new explicit
baseline is accepted.

The sibling frontend checkout has also advanced from the audited `8866d39` pin to
`26c698b` and contains three untracked `.DS_Store` files. The audited commit remains
locally addressable and this package continues to describe that pin; reviewing the
newer frontend is a separate refresh, not an implicit update to this evidence set.
