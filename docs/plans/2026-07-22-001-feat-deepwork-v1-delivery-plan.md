---
title: "feat: Deep Work v1 — Full Delivery Plan"
type: feat
status: active
date: 2026-07-22
origin: docs/plan/04-roadmap.md
---

# feat: Deep Work v1 — Full Delivery Plan

> **Revision 2026-07-23 — architecture + conventions update.** Two decisions reshape this plan; read them alongside it:
> - [application-architecture.md](application-architecture.md) — adds a **stateless Python backend (`apps/api`, FastAPI)** shared by web/desktop/mobile; control-plane/auth/push glue moves out of Next.js route handlers; the run stream stays **client-direct** via `useStream`. Web+desktop share one Next app; **mobile is a focused PWA** (see [features/08-mobile-and-surfaces.md](features/08-mobile-and-surfaces.md)).
> - [code-conventions.md](code-conventions.md) — Deep Work matches **canonical LangChain conventions** to maximize OSS-community contribution. **Toolchain change: oxlint + oxfmt (not biome)**; Python packages follow `langchain-ai/langchain` (uv/ruff `ALL`/mypy strict/Google docstrings); TS libs follow `langchain-ai/langchainjs` (tsdown/snake_case modules/`.js` imports/named exports); the Next app keeps framework-native conventions.
>
> New unit added: **U7b — `apps/api` Python backend** ([features/07b-api-backend.md](features/07b-api-backend.md)). Affected: U1 (oxlint/oxfmt + `internal/` + uv workspace), U6 (Python conventions), U7 (langchainjs conventions + backend client), U8 (auth moves to `apps/api`), U15/U16 (control-plane/push become `apps/api` endpoints). The R-IDs and U-IDs below are updated inline where they name toolchain or backend specifics; unaffected units are unchanged.

## Summary

Turn the existing visual prototype and planning docs into a shippable v1 of Deep Work: an open-source operations room for LangChain/LangSmith agents. The UI layer is essentially done (`deep-work-frontend` — 53 files, all mock data). Delivery means scaffolding the monorepo, wiring real data and auth underneath the existing screens, rebuilding approvals on the correct HITL contract, adding sandbox/coding-task surfaces, and rounding out with PWA/Tauri and community-facing docs. All implementation follows the spec in `docs/plan/` — particularly the milestone map in [04-roadmap.md](docs/plan/04-roadmap.md) and the frontend evaluation in [06-frontend-implementation.md](docs/plan/06-frontend-implementation.md).

---

## Problem Frame

Deep Work has thorough architecture, design, and a pixel-complete UI prototype, but zero deployed software. The three de-risking spikes in M0 (OAuth, MDA loop, stream contract) resolve the unknowns that could invalidate architecture decisions made on paper. Until those are facts, real implementation risks wasted effort. The canonical delivery vehicle — the monorepo — does not yet exist.

---

## Requirements

- R1. Monorepo scaffold (pnpm + Turborepo + changesets + **oxlint + oxfmt**, plus a **uv Python workspace**) with `apps/{web,desktop,mobile,api}`, `packages/{agent,sdk,ui}`, `internal/{tsconfig,build}` and CI. *(rev: oxlint/oxfmt not biome; adds `apps/api` + `internal/`)*
- R1b. **Python backend `apps/api`** (FastAPI, stateless, no DB) owns auth + control-plane + push + webhooks + gh-token brokering for all client surfaces; the run stream is **not** proxied through it. *(new)*
- R2. `deep-work-frontend` imported as `apps/web`; hygiene applied (strict TS, **oxlint/oxfmt**, vitest, nuqs URL state, lockfile regenerated). Next app keeps framework-native file conventions.
- R3. M0 spikes (OAuth, MDA loop, stream contract) produce written decision memos before M1 implementation begins.
- R4. `packages/sdk` exposes an `AgentSource` registry and `DataProvider` interface consumed by all UI components.
- R5. `packages/agent` is a deployable deepagents project supporting research + writing task types without sandbox.
- R6. Live task inbox, new-task composer, and task detail stream via `@langchain/react` `useStream`.
- R7. Sign-in is functional: OAuth (if Spike 1 green) or API-key, terminated by the **`apps/api` auth endpoints**; the Next app keeps only a thin same-origin session/callback route. *(rev: auth in Python backend, not Next route handlers)*
- R8. Approvals surface is re-grounded on the v1 HITL contract (`HITLRequest` → decisions approve/edit/reject/respond).
- R9. Coding-task surfaces: Files/Git tabs wire to sandbox connector routes; diff view promotes to full-width takeover with batched line comments; GitHub App flow is functional.
- R10. Fleet manager, agent builder, and schedules wire to `/v1/deepagents/*` and crons API.
- R11. PWA (manifest, Web Push, offline shell) ships; Tauri desktop wraps the web app.
- R12. v1 release criteria from [04-roadmap.md](docs/plan/04-roadmap.md) §v1 release criteria all pass.
- R13. Docs ship: quickstart (≤15 min to first PR), self-deploy guide, agent-authoring guide.

---

## Scope Boundaries

- Observability charts remain bound to LangSmith stats the key can read cheaply; no re-implementation of LangSmith's own dashboards.
- Browser/computer-use card ships feature-flagged off for v1; it is a Fleet-only capability not in the deepagents harness.
- Terminal pane is read-only in v1.
- GitHub-only for repo integration; GitLab deferred.
- No team RBAC surfaces; single-user/personal-workspace scope for v1.
- No evals integration, no Slack/Linear task creation, no Expo native apps, no ACP/A2A server.
- Org-intelligence ladder beyond Layers 0–1 (memory + analyst schedule template) is post-v1.
- Fleet self-config-via-chat: deferred pending public Fleet CRUD API availability.

### Deferred to Follow-Up Work

- Pure-OSS backend tier (protocol server / Aegra adapter): separate post-v1 project.
- Multi-repo worktree parallelism: separate issue after v1 ships.
- Goal lifecycle / draft→review→amend (dcode-style on RubricMiddleware): v1.x.
- Async-subagent supervisor pattern (parallel workstreams as linked tasks): v1.x.
- Org-intelligence v2 (OKF knowledge base / openwiki) and v3 (Graphiti temporal org graph): per [07-org-intelligence.md](docs/plan/07-org-intelligence.md).

---

## Context & Research

### Relevant Code and Patterns

- UI prototype seed: `deep-work-frontend/` (all 53 files — becomes `apps/web`)
- Mock data / fixture source: `deep-work-frontend/lib/data.ts` (becomes `packages/ui/fixtures`)
- Design token source: `packages/ui/tokens.css` + `packages/ui/tailwind.preset.mjs`
- Full spec: `docs/plan/01-vision.md` through `docs/plan/08-deepagents-feature-map.md`
- OSS setup spec: `docs/plan/05-oss-setup.md` (toolchain, CI matrix, version pins)
- UI spec: `docs/plan/03-ui-spec.md` (pixel measurements, component inventory, screen contracts)
- Architecture spec: `docs/plan/02-architecture.md` (runtime tiers, auth planes, streaming/data plane)
- Frontend evaluation: `docs/plan/06-frontend-implementation.md` (gap analysis, phase map)
- LangChain docs reference: `langchain-docs-reference/` (cloned shallow for local reference)

### External References

- `@langchain/react` useStream API and HITL contract (see `docs/research/`)
- LangSmith control-plane API: `/v2/deployments`, tarball upload, threads.search, crons
- MDA beta docs: `mda init/dev/deploy`, `/v1/deepagents/*`
- LangSmith OAuth discovery: `/.well-known/oauth-authorization-server`

---

## Key Technical Decisions

- **Monorepo is canonical; v0 repo is a design sandbox.** Changes flow one-way from `deep-work-frontend` into `apps/web` — never blind-merged, only curated. (see origin: docs/plan/06-frontend-implementation.md §4 Decision 1)
- **IA consolidates to 6 tabs.** Config folds into Settings/Agent detail; Observability slims to counts + deep links and avoids re-implementing LangSmith dashboards. (see origin: docs/plan/06-frontend-implementation.md §4 Decision 2)
- **`lib/data.ts` becomes `packages/ui/fixtures` and stays forever** as demo mode + OSS contributor experience (no credentials required to run). (see origin: docs/plan/06-frontend-implementation.md §4 Decision 4)
- **Spikes resolve unknowns before M1 feature work.** OAuth, MDA loop, and stream contract are facts before any wiring begins. Each spike produces a written memo.
- **`DataProvider` interface pattern.** All UI components consume a `DataProvider` interface; two implementations: fixtures (always available) and live (requires credentials). This keeps the app runnable without a LangSmith account.
- **Key-proxy as auth baseline.** OAuth ships when Spike 1 confirms scope coverage; API key is the complete fallback. *(rev: terminated by `apps/api`, not a Next route)*
- **Approvals must be re-grounded from scratch** on `HITLRequest` → decisions contract. The current `Approval {kind: shell|write|network|commit}` shape cannot be salvaged — it maps to the legacy agent-inbox shape.
- **Stateless Python backend (`apps/api`).** *(new, rev 2026-07-23)* One FastAPI service (no DB) owns auth + control plane + push + webhooks for web/desktop/mobile, using first-class Python LangChain SDKs. The **run stream stays client-direct** (`useStream`) — never proxied. Rationale: [application-architecture.md](application-architecture.md).
- **Match canonical LangChain conventions for OSS adoption.** *(new, rev 2026-07-23)* **oxlint + oxfmt (not biome)**; Python = `langchain-ai/langchain` style; TS libs = `langchain-ai/langchainjs` style; Next app stays framework-native. Full contract: [code-conventions.md](code-conventions.md).
- **Web + desktop share one Next app; mobile is a focused PWA.** *(new, rev 2026-07-23)* Desktop = Tauri wrapping the web build; mobile ships a triage/approve subset (PWA → Expo later). See [features/08-mobile-and-surfaces.md](features/08-mobile-and-surfaces.md).

---

## Open Questions

### Resolved During Planning

- *Should we adopt the v0 frontend or rebuild?* Adopted — it is a complete rendering layer, weeks ahead on chrome work, well-decomposed, and token-faithful to the spec.
- *What is the canonical repo?* `deepwork/` monorepo. `deep-work-frontend` remains an external design sandbox.

### Deferred to Implementation

- *OAuth `scopes_supported` reality* — resolved by M0 Spike 1. Determines whether OAuth ships in M1 or API-key-only ships first.
- *MDA invocation API gate* — resolved by M0 Spike 2. If gated, classic LangGraph deployment is the fallback path.
- *Stream protocol v2 specifics* — resolved by M0 Spike 3. Golden-transcript tests define the contract before any `useStream` wiring.
- *Observability chart depth* — decided at M3 entry based on what the LangSmith API can return cheaply with a bearer token.
- *Fleet self-config-via-chat feasibility* — resolved by probing the public run API during M3.

---

## Output Structure

```
deepwork/                         (this repo — canonical monorepo · rev 2026-07-23)
  apps/
    web/                          (imported from deep-work-frontend in U2; Next.js)
    desktop/                      (Tauri wrapper, created in U18; wraps apps/web)
    mobile/                       (PWA v1 → Expo later, created in U18; focused subset)
    api/                          (Python FastAPI backend, created in U7b) *(new)*
  packages/
    agent/                        (deepagents Python project, created in U6)
    sdk/                          (TS: backend client + useStream adapters, created in U7)
    ui/
      tokens.css                  (already exists)
      tailwind.preset.mjs         (already exists)
      fixtures/                   (imported from lib/data.ts in U2)
      components/                 (primitives extracted in U2)
  internal/                       (shared TS build/config, created in U1) *(new)*
    tsconfig/                     (@deepwork/tsconfig — base.json)
    build/                        (@deepwork/build — tsdown wrapper)
  docs/
    plan/                         (existing spec docs)
    plans/                        (this file + application-architecture.md + code-conventions.md + features/)
    research/                     (existing research digests)
  .github/workflows/              (ci-ts.yml, ci-py.yml, release.yml — created in U1)
  pnpm-workspace.yaml             (apps/*, packages/*, internal/* — created in U1)
  turbo.json                      (created in U1)
  .oxlintrc.json                  (created in U1)  # oxlint (not biome)
  pyproject.toml                  (uv workspace root, created in U1) *(new)*
  package.json                    (TS workspace root, created in U1)
  AGENTS.md / CLAUDE.md           (contributor furniture, created in U1) *(new)*
```

---

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

```
┌─────────────────────────────────────────────────────────────┐
│  apps/web  (Next.js, App Router)                            │
│  ┌──────────┐  ┌──────────────────────────────────────────┐ │
│  │ fixtures │  │ DataProvider (live)                      │ │
│  │ (always  │  │  ├── packages/sdk: AgentSource registry  │ │
│  │ runnable)│  │  ├── packages/sdk: control-plane client  │ │
│  └──────────┘  │  └── @langchain/react: useStream         │ │
│       └────────┤                                          │ │
│           DataProvider interface (consumed by all pages)  │ │
│                └──────────────────────────────────────────┘ │
│                                                             │
│  Server routes (app/api/):                                  │
│    /api/langsmith-proxy  — key proxy passthrough            │
│    /api/auth/*           — OAuth / device-flow callback     │
│    /api/github-callback  — GitHub App token proxy           │
│    /api/push             — Web Push fan-out (M4)            │
└─────────────────────────────────────────────────────────────┘
         │ deploys to Vercel (apps/web)
         │ Tauri wraps (apps/desktop, M4)
┌────────▼────────────────────────┐
│  packages/sdk (TypeScript)      │
│  AgentSource registry           │
│  LangSmith control-plane client │
│  Normalized stream types        │
│  DataProvider implementations   │
└────────┬────────────────────────┘
         │ calls
┌────────▼────────────────────────┐
│  packages/agent (Python)        │
│  deepagents project             │
│  Research + writing task types  │
│  RubricMiddleware               │
│  deployable via mda / langgraph │
└─────────────────────────────────┘
```

Data flow for live task detail:
```
LangGraph deployment
  → SSE stream
  → @langchain/react useStream
  → stream projections (content blocks, AssembledToolCall, SubagentDiscovery,
                        values.todos, FileData, checkpoints)
  → DataProvider.live adapter in packages/sdk
  → existing renderers in apps/web components
     (narration card, ToolCard, SubagentCard, RunPanel tabs, ApprovalActions)
```

---

## Implementation Units

- U1. **Monorepo scaffold**

**Goal:** Bootstrap the canonical monorepo with the full toolchain so all subsequent work has a stable foundation with CI.

**Requirements:** R1

**Dependencies:** None

**Files:**
- Create: `package.json` (root — workspace root with pnpm)
- Create: `pnpm-workspace.yaml`
- Create: `turbo.json`
- Create: `biome.json`
- Create: `.github/workflows/ci.yml` (typecheck / lint / test / build matrix per `docs/plan/05-oss-setup.md`)
- Create: `.github/workflows/preview.yml` (Vercel preview on PR)
- Create: `packages/ui/package.json` (rename, add to workspace)

**Approach:**
- Follow `docs/plan/05-oss-setup.md` exactly for toolchain choices, version pins, and CI matrix shape.
- Root `package.json` declares all workspace packages; Turborepo pipeline declares `build`, `test`, `lint`, `typecheck` tasks with correct `dependsOn`.
- Biome replaces ESLint/Prettier across the workspace; single `biome.json` at root.
- CI matrix: `typecheck`, `lint`, `test`, `build` — each as a separate job; build depends on typecheck + lint passing.
- Vercel project attached to `apps/web` path via root config.

**Patterns to follow:**
- `docs/plan/05-oss-setup.md` — authoritative on toolchain, version pins, and CI shape.

**Test scenarios:**
- Happy path: `pnpm install` at root resolves all workspace packages without conflicts.
- Happy path: `pnpm turbo build` completes in a clean environment.
- Happy path: CI workflow triggers on PR against main; all matrix jobs run.
- Edge case: a PR that breaks typecheck in `apps/web` causes CI to fail and blocks merge.

**Verification:**
- `pnpm turbo build` exits 0 from the repo root.
- GitHub Actions CI workflow runs and shows green on the scaffold.
- Vercel preview URL is generated on a test PR.

---

- U2. **Import `deep-work-frontend` as `apps/web` + apply hygiene**

**Goal:** Migrate the visual prototype into the monorepo as `apps/web` and apply the hygiene backlog so it is CI-clean and production-ready as a foundation.

**Requirements:** R2, R4

**Dependencies:** U1

**Files:**
- Create: `apps/web/` (copy of `deep-work-frontend/` contents)
- Create: `apps/web/package.json` (rename from `"my-project"`)
- Modify: `apps/web/next.config.mjs` (remove suppressed build errors flag, remove unoptimized images flag)
- Create: `apps/web/tsconfig.json` (strict mode)
- Move: `deep-work-frontend/lib/data.ts` → `packages/ui/fixtures/index.ts`
- Create: `packages/ui/components/` (extract `StatusChip`, `ToolCard`, `PageHeader`, `AppShell` primitives with stories)
- Modify: `apps/web/app/layout.tsx` (replace inline theme block with `packages/ui/tokens.css` import)
- Create: `apps/web/vitest.config.ts` + `apps/web/tests/setup.ts` (vitest + RTL scaffold)
- Modify: `apps/web/components/task-inbox.tsx` (replace useState filters with nuqs)
- Modify: `apps/web/components/task-detail.tsx` (replace useState filters with nuqs)
- Delete: `apps/web/app/config/page.tsx` (dead redirect — consolidate into settings)

**Approach:**
- Copy, don't move — `deep-work-frontend` remains a design sandbox; `apps/web` is the canonical copy.
- Regenerate `pnpm-lock.yaml` at workspace root after import; do not copy the v0 lockfile.
- Single token source: `packages/ui/tokens.css` is the authority. Remove any duplicated color/radius/font declarations from `apps/web`.
- nuqs URL state: inbox status filter, task detail tab selection, approvals kind/agent filters.
- Strict TS: fix or annotate with justification all suppressed errors surfaced by removing the build error bypass.
- Keep `packages/ui/fixtures/index.ts` as the permanent demo mode — it must keep the app runnable with zero credentials.
- IA consolidation: remove the 7th "Config" tab from app-shell nav; its content lives in Settings and Agent detail.

**Patterns to follow:**
- `docs/plan/06-frontend-implementation.md` §Phase A — the authoritative checklist.
- `packages/ui/tokens.css` — token naming convention.

**Test scenarios:**
- Happy path: `pnpm turbo build --filter=apps/web` exits 0 with no TypeScript errors.
- Happy path: opening `apps/web` in the browser with no env vars shows the full task inbox using fixture data.
- Edge case: nuqs URL state — navigating to `/tasks?status=running` renders the inbox pre-filtered to running tasks.
- Edge case: removing the build error bypass surfaces previously hidden type errors; each must be explicitly fixed, not suppressed without justification.
- Integration: `packages/ui/fixtures` imported in `apps/web` resolves correctly through the workspace.

**Verification:**
- `pnpm turbo typecheck --filter=apps/web` exits 0.
- App renders in Vercel preview with fixture data; all 10 pages load without console errors.
- `packages/ui/fixtures` is importable from `apps/web` and from a test file in `packages/ui`.

---

- U3. **M0 Spike 1 — OAuth probe**

**Goal:** Determine whether LangSmith OAuth is viable for v1 auth, producing a written decision memo that gates the M1 sign-in implementation.

**Requirements:** R7 (gates approach)

**Dependencies:** U1

**Files:**
- Create: `docs/spikes/2026-07-22-spike-oauth.md` (findings memo)

**Approach:**
- Probe `/.well-known/oauth-authorization-server` on `smith.langchain.com` for `scopes_supported` and `token_endpoint`.
- Register a public DCR client; test bearer token acceptance against `api.smith.langchain.com`, the LangGraph control plane, and a `*.langgraph.app` deployment.
- Document: which scopes are available, whether a single token works across all three surfaces, and whether device-flow is supported.
- Output a binary recommendation: **OAuth-first** (token covers all surfaces) vs **key-first** (key proxy is the v1 baseline; OAuth follows when scopes allow).

**Test scenarios:**
- Spike validation: a bearer token obtained via the probed OAuth flow is accepted by all three API surfaces.
- Spike validation: if any surface rejects the bearer, the memo documents which surface and proposes the fallback scope.

**Verification:**
- `docs/spikes/2026-07-22-spike-oauth.md` exists and contains a binary recommendation.
- The U8 sign-in implementation unit is updated with the chosen approach before work begins.

---

- U4. **M0 Spike 2 — MDA loop**

**Goal:** Verify the Managed Deep Agent invocation cycle end-to-end using the beta account, producing a written decision memo that gates `packages/agent` design.

**Requirements:** R5 (gates design)

**Dependencies:** U1

**Files:**
- Create: `docs/spikes/2026-07-22-spike-mda-loop.md` (findings memo)
- Create: `packages/agent/spike/` (minimal agent project used during the spike — throwaway)

**Approach:**
- Use `mda init/dev/deploy` to create a minimal agent with a single tool.
- Verify `useStream` from `@langchain/react` against the MDA deployment URL with identity presets.
- Verify `/v2/deployments` tarball upload from hand-crafted code (not the CLI) — this is required for the agent-source registry.
- Document: whether `deployment_type: managed_deep_agent` is gated; classic LangGraph fallback path if so; tarball upload API shape.

**Test scenarios:**
- Spike validation: a task dispatched from `useStream` against the MDA deployment reaches the agent and streams back content blocks.
- Spike validation: a tarball upload via the `/v2/deployments` API (not `mda deploy`) succeeds.
- Edge case: if MDA is gated for non-beta orgs, confirm classic `langgraph dev` + `langgraph deploy` is equivalent for v1 scope.

**Verification:**
- `docs/spikes/2026-07-22-spike-mda-loop.md` exists with findings and a binary recommendation on MDA vs classic deployment for `packages/agent`.

---

- U5. **M0 Spike 3 — Stream contract**

**Goal:** Produce golden-transcript tests of the LangGraph stream protocol v2 that become the contract for all `useStream` wiring in M1–M2.

**Requirements:** R6 (gates data layer)

**Dependencies:** U1

**Files:**
- Create: `packages/sdk/tests/golden/` (golden transcript fixture files — `.jsonl` or `.ndjson`)
- Create: `packages/sdk/tests/stream-contract.test.ts` (contract tests against golden transcripts)
- Create: `docs/spikes/2026-07-22-spike-stream-contract.md` (findings memo)

**Approach:**
- Run `langgraph dev` locally against a minimal agent.
- Capture raw SSE frames for: content blocks, `AssembledToolCall`, HITL `interrupt` + `respond`, subagent namespaces, `values.todos`, `FileData` variants, resume with `Last-Event-ID`.
- Write contract tests that parse the golden transcripts and assert the shape of each projection type.
- Document any protocol v2 divergences from the `@langchain/react` type declarations.

**Test scenarios:**
- Contract test: golden transcript for content block stream round-trips through the SDK type parser without error.
- Contract test: golden transcript for `HITLRequest` → `decisions` interrupt+respond round-trip.
- Contract test: subagent namespace frames are correctly attributed to the owning subagent.
- Edge case: `Last-Event-ID` resume restores stream position correctly in the golden test.

**Verification:**
- `pnpm turbo test --filter=packages/sdk` exits 0 against the golden transcripts.
- `docs/spikes/2026-07-22-spike-stream-contract.md` exists with any protocol divergences documented.

---

- U6. **`packages/agent` v0 — deployable deepagents project**

**Goal:** Create the first deployable Deep Work agent supporting research and writing task types, without sandbox execution.

**Requirements:** R5

**Dependencies:** U4 (spike memo determines deployment target — MDA vs classic)

**Files:**
- Create: `packages/agent/` (deepagents Python project structure)
- Create: `packages/agent/pyproject.toml`
- Create: `packages/agent/deepwork_agent/` (agent source)
- Create: `packages/agent/deepwork_agent/__init__.py`
- Create: `packages/agent/deepwork_agent/agent.py` (main graph definition)
- Create: `packages/agent/deepwork_agent/tasks/research.py`
- Create: `packages/agent/deepwork_agent/tasks/writing.py`
- Create: `packages/agent/deepwork_agent/middleware/rubric.py` (`RubricMiddleware` v0)
- Create: `packages/agent/langgraph.json` (or `mda.json` per Spike 2 finding)
- Create: `packages/agent/tests/`

**Approach:**
- Follow `docs/plan/08-deepagents-feature-map.md` for which deepagents harness features to activate in v0.
- Research task type: web search + summarize tool pattern; sources annotated in thread narration.
- Writing task type: draft → RubricMiddleware critique loop → revision.
- No sandbox, no code execution, no file system tools in this unit.
- Deployable via `mda dev` (if Spike 2 showed MDA available) or `langgraph dev` (fallback).
- `RubricMiddleware` v0: rubric field plumbed from task input into the critique loop.

**Patterns to follow:**
- `docs/plan/08-deepagents-feature-map.md` — feature map.
- `docs/plan/02-architecture.md` §Deep Work agent design.

**Test scenarios:**
- Happy path: dispatching a research task returns a completed thread with narration + source tool calls visible in the stream.
- Happy path: dispatching a writing task with a rubric triggers at least one critique iteration before finishing.
- Edge case: a task with an empty rubric field completes without entering the critique loop.
- Error path: a network failure in the web search tool is caught; the agent narrates the failure and marks the task failed rather than crashing.

**Verification:**
- `langgraph dev` starts without errors.
- A research task dispatched via `curl` against the local server returns a completed thread with content blocks.
- `pnpm turbo test --filter=packages/agent` exits 0.

---

- U7. **`packages/sdk` — AgentSource registry + DataProvider interface**

**Goal:** Build the TypeScript control-plane client, AgentSource registry, and DataProvider interface that all UI components consume. The live implementation replaces the fixture implementation with zero UI changes.

**Requirements:** R4, R6

**Dependencies:** U5 (stream contract golden tests define the SDK types)

**Files:**
- Create: `packages/sdk/package.json`
- Create: `packages/sdk/src/index.ts`
- Create: `packages/sdk/src/agent-source.ts` (registry: MDA deployment / any URL / `langgraph dev`)
- Create: `packages/sdk/src/control-plane.ts` (LangSmith API client: threads.search, deployments, crons)
- Create: `packages/sdk/src/data-provider.ts` (interface + two implementations: fixtures, live)
- Create: `packages/sdk/src/stream/` (useStream adapters, normalized projection types from Spike 3 golden tests)
- Create: `packages/sdk/src/types.ts` (normalized domain types: Task, ThreadEvent, Approval, Agent, …)
- Create: `packages/sdk/tests/`
- Test: `packages/sdk/tests/stream-contract.test.ts` (from U5)

**Approach:**
- `DataProvider` interface: async methods for `listTasks()`, `getTask()`, `listApprovals()`, `listAgents()`, etc. — same shape for both fixtures and live implementations.
- Fixtures implementation wraps `packages/ui/fixtures/index.ts`; no network calls.
- Live implementation calls LangSmith control-plane API and wraps `@langchain/react` `useStream`.
- `AgentSource` registry: union type of `{type: "mda", deploymentId}` | `{type: "url", url}` | `{type: "dev", port}` — drives which API endpoint `useStream` connects to.
- Normalized types in `src/types.ts` decouple the UI from the raw `@langchain/react` projection shapes — the adapter layer lives here, not in components.

**Patterns to follow:**
- `docs/plan/02-architecture.md` §Control-plane API, §Streaming/data plane.
- `packages/sdk/tests/golden/` (from U5).

**Test scenarios:**
- Happy path: `DataProvider.fixtures.listTasks()` returns the fixture task list without any network call.
- Happy path: `AgentSource` registry serializes and deserializes all three source types round-trip.
- Contract test (from U5): normalized stream adapter maps all golden transcript projection types to SDK types without throwing.
- Edge case: a `DataProvider.live` instance with an invalid API key throws an `AuthError`, not a generic network error.

**Verification:**
- `pnpm turbo test --filter=packages/sdk` exits 0 against both fixture and golden-transcript tests.
- `apps/web` can import `DataProvider` from `packages/sdk` and use the fixture implementation with no env vars.

---

- U7b. **`apps/api` — Python backend (FastAPI, stateless)** *(new — rev 2026-07-23)*

**Goal:** Stand up the one backend all clients share: auth, LangSmith control plane, push fan-out, webhook ingestion, and GitHub-token brokering — via the Python `langsmith`/`langgraph-sdk`/`langchain-auth` SDKs. Stateless, no DB. Not in the run-stream byte path (clients stream `useStream` directly). Full detail: [features/07b-api-backend.md](features/07b-api-backend.md).

**Requirements:** R1b, R7 (and backs R6, R8, R10)

**Dependencies:** U1 (uv workspace + `apps/api` stub), U3 (auth posture), U4 (control-plane/deploy shapes), U5/U7 (stream-token consumed by SDK adapters)

**Files:** `apps/api/deepwork_api/{main,auth/*,control_plane/*,push/*,webhooks/*,github/*,clients/*,errors}.py`; `apps/api/tests/{unit_tests,integration_tests}/`

**Approach:** FastAPI endpoint surface under `/v1` — `auth/*` (OAuth PKCE, device flow, api-key, session, stream-token), control plane (`deployments`/`agents`/`threads`/`crons`/`hub`/`sandboxes`), `threads/:id/decisions` (HITL), `push/subscribe`, `webhooks/run|github`, internal `gh-token`. LangChain Python conventions ([code-conventions.md](code-conventions.md) §2). See the feature doc for the endpoint table and auth flow.

**Test scenarios:** valid api-key → session; `GET /v1/threads` returns aggregated inbox (mocked unit / real integration); `stream-token` mints a short-lived token; HITL decision resolves via `respond()`; secrets never appear in client responses; `gh-token` fails closed.

**Verification:** `make -C apps/api test` (unit socket-disabled + integration vs `langgraph dev`) passes; ruff/mypy clean; full loop drivable via the endpoints with the stream client-direct.

---

- U8. **Sign-in wiring (clients → `apps/api` auth)** *(rev: auth logic lives in `apps/api` U7b; Next keeps only a thin session/callback route)*

**Goal:** Make sign-in functional against the `apps/api` auth endpoints: API-key path ships unconditionally; OAuth ships if Spike 1 memo is green. `apps/web` keeps only a same-origin callback/session route that delegates to `apps/api`.

**Requirements:** R7

**Dependencies:** U3 (spike memo gates OAuth approach), **U7b (auth endpoints)**, U7

**Files:**
- Create: `apps/web/app/api/langsmith-proxy/route.ts` (key-proxy passthrough)
- Create: `apps/web/app/api/auth/callback/route.ts` (OAuth callback — conditional on Spike 1 outcome)
- Create: `apps/web/app/api/auth/device/route.ts` (device-flow initiation — conditional)
- Modify: `apps/web/components/sign-in.tsx` (wire buttons to real auth flows; remove navigation-only stubs)
- Create: `apps/web/lib/auth.ts` (session handling, token storage in httpOnly cookie)

**Approach:**
- Key-proxy: forward all requests to `api.smith.langchain.com` with the stored API key as `Authorization: Bearer`. The key is never exposed to the browser.
- If Spike 1 is green: implement OAuth PKCE flow; callback route exchanges code for token, stores in httpOnly cookie, redirects to `/tasks`.
- If Spike 1 is red: key-only path ships; OAuth is a follow-up.
- Session: httpOnly `__deepwork_session` cookie; no `localStorage` for tokens.
- Sign-in screen: add an auth context provider that gates rendering of app routes.

**Test scenarios:**
- Happy path: entering a valid LangSmith API key in the sign-in form redirects to `/tasks` and the key-proxy route accepts subsequent API calls.
- Error path: entering an invalid API key shows a visible error message on the sign-in form; does not navigate.
- Error path: OAuth callback with a malformed `code` parameter returns a 400 and shows the sign-in error state.
- Security: the API key is never present in any client-side JS response body or visible in browser network responses (only the proxy's outbound request carries it).
- Edge case: an expired session cookie redirects the user to `/login` rather than showing a blank page or console error.

**Verification:**
- Signing in with a real LangSmith API key reaches `/tasks` and the inbox loads (may still be fixtures until U9).
- `curl localhost:3000/api/langsmith-proxy/v1/threads` with a valid cookie returns data from LangSmith.
- TypeScript strict mode: no `any` in `apps/web/lib/auth.ts`.

---

- U9. **Live task inbox + new-task composer**

**Goal:** Wire the task inbox and new-task composer to real LangSmith data via `packages/sdk`, replacing the fixture data path.

**Requirements:** R6

**Dependencies:** U7, U8

**Files:**
- Modify: `apps/web/components/task-inbox.tsx` (swap fixture data for `DataProvider.live.listTasks()`)
- Modify: `apps/web/app/tasks/new/page.tsx` (real submit via `DataProvider.live.dispatchTask()`)
- Modify: `apps/web/components/app-shell.tsx` (inject `DataProvider` via context; fixture vs live based on env)
- Create: `apps/web/components/data-provider-context.tsx`
- Test: `apps/web/tests/task-inbox.test.tsx`

**Approach:**
- Inject `DataProvider` at the app root via React context; components consume it via a `useDataProvider()` hook.
- `DataProvider.live.listTasks()` calls `threads.search` aggregation on the LangSmith control-plane.
- Status chips derive from thread status + interrupt counts (not the mock `TaskStatus` enum).
- New-task composer submit: calls `DataProvider.live.dispatchTask(agentSource, input)` → starts a new thread → navigates to the task detail page.
- Optimistic state: the composer shows a loading indicator until the thread is created.
- nuqs URL state already in place from U2; inbox filters (status, agent) drive the `threads.search` query params.

**Test scenarios:**
- Happy path: a signed-in user sees their real LangSmith threads in the inbox, grouped by status.
- Happy path: submitting a new task in the composer navigates to the task detail page of the newly created thread.
- Edge case: an inbox with zero threads shows the empty state (not a blank screen).
- Edge case: threads.search returns a next-page cursor; the inbox loads more on scroll.
- Error path: LangSmith API returns 401; inbox shows a re-auth prompt rather than a spinner.
- Integration: inbox status filter set to `running` via nuqs URL updates the `threads.search` query and filters results.

**Verification:**
- Opening `/tasks` with a valid session shows real threads from the connected LangSmith workspace.
- Submitting a new task creates a thread visible in LangSmith's UI and in the inbox after refresh.

---

- U10. **Live task detail — streaming thread**

**Goal:** Wire task detail to stream live thread events via `@langchain/react` `useStream`, mapping real projections onto existing renderers.

**Requirements:** R6

**Dependencies:** U7, U8, U9

**Files:**
- Modify: `apps/web/components/task-detail.tsx` (replace static thread array with `useStream` projection)
- Modify: `apps/web/components/run-context.tsx` (wire context from `values.*` projections)
- Modify: `apps/web/components/run-stream.tsx` (wire content blocks → narration cards)
- Modify: `apps/web/components/run-subagents.tsx` (wire `SubagentDiscoverySnapshot` → SubagentCard)
- Modify: `apps/web/components/run-panel.tsx` (wire Status tab to `values.todos`; Files tab to `FileData`; Trace tab to run URL)
- Create: `apps/web/components/subagent-card.tsx` (new component for `SubagentDiscoverySnapshot`)
- Modify: `apps/web/components/composer.tsx` (real submit: queue vs interrupt affordance via `stream.send()` / `stream.interrupt()`)
- Test: `apps/web/tests/task-detail.test.tsx`

**Approach:**
- `useStream(threadId, agentSource)` from `packages/sdk` wraps `@langchain/react`'s `useStream`.
- Content block projection → narration card renderer (already built, swap data source only).
- `AssembledToolCall` → `ToolCard` (including streaming output into the open card as chunks arrive).
- `values.todos` → RunPanel Status tab list + composer todo tray.
- `FileData` variants → RunPanel Files tab.
- `SubagentDiscoverySnapshot` → new `SubagentCard` component (name, status, current tool, interrupt count badge).
- Trace pill: real LangSmith run URL from stream metadata.
- Composer send: queue = `stream.send(message)` (double-texting allowed); interrupt = `stream.interrupt(message)` (pauses current step).
- Steering submit clears the input and shows an optimistic "message queued" state.

**Patterns to follow:**
- `packages/sdk/src/stream/` adapter types (from U7).
- `docs/plan/03-ui-spec.md` §Task detail screen contract.

**Test scenarios:**
- Happy path: opening a running task shows live streaming narration; new content blocks appear without page reload.
- Happy path: a tool call card shows streaming output as chunks arrive, then closes when the tool finishes.
- Happy path: `values.todos` from the stream renders in the RunPanel Status tab and the composer todo tray.
- Integration: dispatching a steering message via the composer sends it to the thread and a new narration card appears within 2 seconds.
- Edge case: opening a completed task (no active stream) renders the full static thread history from the thread store.
- Edge case: a task with subagents shows a SubagentCard for each discovered subagent with its own status.
- Error path: stream disconnection shows a "Reconnecting…" indicator; does not lose rendered history.

**Verification:**
- Opening a running task in the browser shows live streaming content from LangSmith.
- Steering a running task via the composer results in a visible response in the thread.

---

- U11. **Approvals — re-grounded on v1 HITL contract**

**Goal:** Rebuild the approvals surface on the real `HITLRequest` → decisions contract, replacing the legacy mock shape entirely.

**Requirements:** R8

**Dependencies:** U10 (stream wires interrupts; approvals hydrate from thread state)

**Files:**
- Modify: `apps/web/components/approval-actions.tsx` (rebuild on `HITLRequest` → decisions)
- Modify: `apps/web/app/approvals/page.tsx` (re-ground on real interrupt data)
- Modify: `packages/sdk/src/types.ts` (add `HITLRequest`, `HITLDecision`, `HITLCapability` types)
- Modify: `packages/sdk/src/stream/` (add HITL projection adapter)
- Test: `apps/web/tests/approvals.test.tsx`

**Approach:**
- Remove the `Approval {kind: shell|write|network|commit, command}` type and all references.
- `HITLRequest` shape from stream: `{id, toolName, args, reviewConfigs: {allowedDecisions, argSchemas}}`.
- Decision verbs: approve / edit / reject / respond (not "ignore" — that was the legacy shape).
- Per-arg edit forms: for each editable arg, show an edit input; Edit⇄Accept auto-switches the button.
- Batched interrupts: multiple tool calls in one interrupt render as a single card with per-call decision rows.
- Capability chips from `reviewConfigs.allowedDecisions` — only show the buttons the agent declared as allowed.
- Sidebar filters: derive from `toolName` values and `reviewConfigs`, not hardcoded kind enums.
- Schema-tolerant raw-JSON fallback: if `argSchemas` is absent, show raw JSON editor.
- Reject vs Mark resolved: kept strictly distinct — Reject sends a reject decision; Mark resolved is a UI-only dismissal for stale interrupts.
- Approvals inbox hydrates from `DataProvider.live.listInterrupts()` (threads.search filtered to interrupted status).

**Test scenarios:**
- Happy path: an interrupted task appears in the approvals inbox; approving it sends an approve decision and the task resumes streaming.
- Happy path: editing an arg before approving sends the mutated arg value in the decision.
- Happy path: a batched interrupt with 3 tool calls renders 3 decision rows; rejecting one and approving two sends a partial decision.
- Edge case: `allowedDecisions` = `["approve"]` only — edit and reject buttons are not rendered.
- Edge case: `argSchemas` absent — raw JSON editor shown for all args.
- Error path: sending a decision while the thread is no longer interrupted shows an error toast; does not leave the card in a loading state.
- Integration: approving an interrupt in the approvals inbox is reflected immediately in the task detail thread (stream resumes).

**Verification:**
- An agent with `interrupt_on` configured produces interrupts that appear in the approvals inbox and can be approved.
- The old `Approval {kind: shell|write|network|commit}` type is fully removed from `packages/sdk/src/types.ts` and `apps/web`.

---

- U12. **Verification — RubricMiddleware + fault-tolerance stack**

**Goal:** Wire the rubric field from the new-task composer through to the agent's `RubricMiddleware`, and surface verdicts and iterations in the RunPanel.

**Requirements:** R9 (partial — verification component of M2)

**Dependencies:** U10, U6

**Files:**
- Modify: `apps/web/components/new-task-composer.tsx` (add rubric field to task input)
- Modify: `packages/agent/deepwork_agent/middleware/rubric.py` (harden from v0 to full verdict schema)
- Modify: `apps/web/components/run-panel.tsx` (add Verification tab showing rubric verdict + iteration history)
- Modify: `packages/sdk/src/types.ts` (add `RubricVerdict`, `RubricIteration` types)
- Test: `apps/web/tests/verification-tab.test.tsx`
- Test: `packages/agent/tests/rubric_middleware_test.py`

**Approach:**
- Rubric field in composer: freetext area for success criteria; plumbed into task input as `input.rubric`.
- `RubricMiddleware` in `packages/agent`: on task completion, evaluate output against the rubric; if verdict = fail, iterate (up to N configured retries); surface `rubric_verdicts` in `values.*` on the stream.
- RunPanel Verification tab: list of `{iteration, verdict, critique, revised_output}` from `values.rubric_verdicts`.
- Fault-tolerance middleware stack: retry-on-tool-failure and dead-letter patterns per `docs/plan/02-architecture.md`.

**Test scenarios:**
- Happy path: a task with a rubric field triggers the critique loop; the Verification tab shows at least one verdict entry.
- Happy path: a task that fails the rubric on iteration 1 but passes on iteration 2 shows both verdict entries.
- Edge case: a task without a rubric field completes without entering the critique loop.
- Edge case: N iterations exhausted without passing — task marked failed with the final verdict visible.

**Verification:**
- Dispatching a writing task with a rubric from the composer shows iteration history in the Verification tab.
- `pnpm turbo test --filter=packages/agent` passes rubric middleware tests.

---

- U13. **Coding-task surfaces — sandbox, GitHub App, diff review**

**Goal:** Wire Files/Git tabs to sandbox connector routes, implement the GitHub App install flow, and promote the diff view to a full-width takeover with batched per-line comments.

**Requirements:** R9

**Dependencies:** U10, U11

**Files:**
- Modify: `apps/web/components/run-panel.tsx` (wire Files tab to `FileData` connector route)
- Modify: `apps/web/components/run-panel.tsx` (wire Git tab to PR/CI status connector route)
- Create: `apps/web/app/api/github-callback/route.ts` (GitHub App token proxy callback)
- Create: `apps/web/components/diff-review.tsx` (full-width takeover with per-line comment batching)
- Modify: `apps/web/app/settings/[[...section]]/page.tsx` (GitHub App install flow in git-section)
- Create: `apps/web/lib/github.ts` (GitHub App token exchange helper)
- Test: `apps/web/tests/diff-review.test.tsx`

**Approach:**
- Files tab: reads `FileData` variants from `values.files` in the stream; shows file tree + selected file contents.
- Git tab: reads PR status and CI check status from the GitHub connector route; shows draft PR link, CI status chips.
- GitHub App install: in settings git-section, "Connect GitHub" → GitHub App install → callback route exchanges installation token → stored in session. The token exchange happens server-side; the token is never returned to the browser.
- `commit_and_open_pr` tool call in the agent produces a draft PR URL visible in the Git tab.
- Diff review: clicking "Review diff" in the Git tab opens a full-width takeover modal; each file shows a GitHub-style diff; per-line comments are collected in a batch; "Submit review" batches them into a single steering message.
- Browser/computer-use card: keep the component; add a `featureFlag("browser-card")` guard that evaluates to `false` for v1.

**Test scenarios:**
- Happy path: a coding task that creates files shows them in the Files tab as `FileData` entries stream in.
- Happy path: a task that calls `commit_and_open_pr` shows a draft PR link in the Git tab.
- Happy path: opening the diff review takeover and adding per-line comments → submitting sends all comments as one batched steering message.
- Edge case: a task with no file changes shows an empty Files tab with the empty state, not a blank panel.
- Error path: GitHub App token is expired; Git tab shows a "Reconnect GitHub" prompt rather than a silent failure.

**Verification:**
- A coding task (dispatched against a real agent with sandbox access) shows files and a draft PR in the RunPanel.
- Per-line diff comments are delivered to the agent as a steering message.
- Browser card is hidden from the UI by default (feature flag off).

---

- U14. **Sub-agent cards + branching / fork-from-checkpoint**

**Goal:** Surface sub-agent runs as `SubagentCard` components in the task detail, and wire the branching/fork affordance for task checkpoints.

**Requirements:** R6 (completes M1/M2 thread projection coverage)

**Dependencies:** U10

**Files:**
- Modify: `apps/web/components/run-subagents.tsx` (wire to live `SubagentDiscoverySnapshot`)
- Modify: `apps/web/components/task-detail.tsx` (add fork-from-checkpoint affordance in thread)
- Modify: `packages/sdk/src/stream/` (add checkpoint projection adapter)
- Test: `apps/web/tests/subagent-card.test.tsx`

**Approach:**
- `SubagentCard`: name (from subagent namespace), status chip (running/done/failed), current tool name (from innermost content block), interrupt-count badge.
- Each subagent card expands to show its own thread view (nested, not a new page).
- Fork-from-checkpoint: each checkpoint in the thread history shows a "Fork" button; clicking creates a new thread resuming from that checkpoint's state.
- Interrupt-count badges in the app-shell tab (from `docs/plan/03-ui-spec.md` §AppShell).

**Test scenarios:**
- Happy path: a task with one subagent shows a `SubagentCard` for that subagent while it is running.
- Happy path: expanding a SubagentCard shows the subagent's thread events.
- Happy path: forking from a checkpoint creates a new thread visible in the inbox.
- Edge case: a SubagentCard for a failed subagent shows the error in its thread view on expand.
- Integration: the interrupt-count badge on the Approvals tab increments when a subagent produces an interrupt.

**Verification:**
- A multi-agent task shows SubagentCards for each subagent with correct status.
- Forking a checkpoint opens a new task in the inbox resuming from that point.

---

- U15. **Fleet manager — agents, builder, config**

**Goal:** Wire the agents index, agent builder, and configuration screens to the LangSmith control plane and `/v1/deepagents/*`.

**Requirements:** R10

**Dependencies:** U7, U8

**Files:**
- Modify: `apps/web/app/agents/page.tsx` (wire to live deployments API)
- Modify: `apps/web/app/agents/[id]/page.tsx` (wire to `/v1/deepagents/:id`)
- Modify: `apps/web/components/settings/connectors-section.tsx` (wire connector permission matrix to `interrupt_on` config)
- Create: `apps/web/components/agent-import-export.tsx` (Fleet-export import/export)
- Modify: `packages/sdk/src/control-plane.ts` (add agent CRUD methods)
- Test: `apps/web/tests/agent-builder.test.tsx`

**Approach:**
- Agents index: `GET /v2/deployments` + `/v1/deepagents/*` aggregation; cards show deployment status, last run, run count.
- Agent builder: maps agent config (instructions, skills, memory, MCP connectors, tool permissions) to `/v1/deepagents/:id` PATCH; auto-saves on blur.
- Connector permission matrix in settings: each connector × tool shows Auto/Ask selector that writes to `interrupt_on` config.
- Fleet-export: serialize agent config to JSON; import parses JSON and creates/updates the agent.
- Template gallery: read-only list of built-in agent templates; "Use this template" clones as a new agent.

**Test scenarios:**
- Happy path: the agents index shows real deployments from the connected LangSmith workspace.
- Happy path: saving an agent's instructions in the builder persists to LangSmith and is visible on next load.
- Happy path: importing a Fleet-export JSON creates a new agent with the config from the file.
- Edge case: a deployment that exists in LangSmith but not in `deepagents/*` still appears in the index (falls back to deployment metadata only).
- Error path: saving an invalid agent config (missing required field) shows a validation error in the builder, not a silent failure.

**Verification:**
- The agent builder round-trips: create → configure → save → reload shows the saved config.
- Fleet-export round-trip: export an agent → delete it → import → it reappears with the same config.

---

- U16. **Schedules + Activity feed**

**Goal:** Wire schedules to the LangSmith crons API and make the activity feed a live chronological stream.

**Requirements:** R10

**Dependencies:** U7, U8

**Files:**
- Modify: `apps/web/app/schedules/page.tsx` (wire to crons API)
- Modify: `apps/web/app/activity/page.tsx` (wire to threads.search aggregation)
- Modify: `packages/sdk/src/control-plane.ts` (add crons CRUD, activity feed methods)
- Test: `apps/web/tests/schedules.test.tsx`

**Approach:**
- Schedules: CRUD against LangSmith crons API; toggle on/paused; cron expression input with human-readable preview.
- Activity feed: `threads.search` with descending sort by `updated_at`; each entry links to the task detail page.
- Untrusted-payload rendering: activity feed items with webhook/schedule-sourced content are rendered via a text-safe renderer (DOMPurify sanitization or a component-based renderer); raw HTML injection into the DOM is explicitly prohibited for untrusted content.

**Test scenarios:**
- Happy path: creating a schedule via the UI creates a cron in LangSmith; it appears in the schedule list.
- Happy path: toggling a schedule to paused sends a PATCH to LangSmith and the status chip updates.
- Happy path: the activity feed shows the most recent thread events across all agents in reverse-chronological order.
- Security: a schedule that produces a thread event with HTML markup in the title does not render it as HTML in the activity feed.

**Verification:**
- A schedule created in Deep Work triggers a run in LangSmith at the configured time.
- The activity feed reflects the run in the feed entry.

---

- U17. **Org intelligence — Layers 0–1**

**Goal:** Ship the memory starter template, analyst schedule template, and LangSmith tracing-metadata conventions that constitute Layers 0–1 of the org intelligence ladder.

**Requirements:** R10 (org intelligence is part of M3 scope)

**Dependencies:** U6, U15, U16

**Files:**
- Create: `packages/agent/deepwork_agent/templates/org_memory.py` (org-memory starter template)
- Create: `packages/agent/deepwork_agent/templates/org_analyst.py` (analyst schedule template)
- Modify: `packages/agent/deepwork_agent/agent.py` (add tracing-metadata conventions)
- Modify: `apps/web/components/settings/memory-section.tsx` (wire Context Hub to real API)
- Create: `docs/plan/org-intelligence-layer0-setup.md` (onboarding seeding interview flow doc)
- Test: `packages/agent/tests/org_memory_template_test.py`

**Approach:**
- `org-memory/` starter template: onboarding seeding interview that populates the agent's Context Hub memory.
- Tracing-metadata conventions: every agent run tags traces with `deepwork.task_type`, `deepwork.agent_id`, `deepwork.rubric_verdict` in LangSmith metadata.
- Analyst schedule: daily/weekly job that reads recent traces via `langsmith-mcp-server`, synthesizes insights, and writes to `org-memory/`.
- Memory section in settings: wire the Context Hub (instructions/skills/memories) to `/v1/deepagents/:id/memory`.

**Test scenarios:**
- Happy path: running the onboarding seeding interview produces a populated `org-memory/` document.
- Happy path: running the analyst schedule produces an insights document in `org-memory/`.
- Happy path: traces from agent runs include the `deepwork.*` metadata tags in LangSmith.

**Verification:**
- An agent run appears in LangSmith with `deepwork.task_type` metadata.
- The analyst schedule can be dispatched manually and produces an org-memory document.

---

- U18. **PWA + Tauri desktop**

**Goal:** Ship the PWA manifest and Web Push notifications, and wrap the web app in a Tauri desktop application.

**Requirements:** R11

**Dependencies:** U9, U10, U16 (push requires run-completion webhooks)

**Files:**
- Create: `apps/web/public/manifest.json` (PWA manifest)
- Create: `apps/web/app/service-worker.ts` (offline shell caching)
- Create: `apps/web/app/api/push/route.ts` (Web Push fan-out from run webhooks)
- Create: `apps/desktop/` (Tauri v2 project wrapping `apps/web`)
- Create: `apps/desktop/src-tauri/tauri.conf.json`
- Create: `.github/workflows/desktop-build.yml` (Tauri build for Mac/Win/Linux)
- Modify: `apps/web/components/app-shell.tsx` (add bottom bar for mobile/PWA per spec §6)

**Approach:**
- PWA: manifest with Deep Work icon, `display: standalone`, start URL `/tasks`. Service worker caches the app shell for offline.
- Web Push: run-completion webhook → `apps/web/api/push/route.ts` → fan-out to subscribed push endpoints. One-tap approval notification action routes to the approvals inbox.
- Tauri: `apps/desktop/` wraps `apps/web` as a webview. Tray icon, native notifications (fire on same push event), deep links (`deepwork://task/:id`), device-flow sign-in, Tauri updater configured.
- Bottom bar: per `docs/plan/03-ui-spec.md` §6 mobile nav spec.

**Test scenarios:**
- Happy path: installing the PWA on iOS adds the Deep Work icon to the home screen; opening it shows the task inbox in standalone mode.
- Happy path: a run-completion event triggers a push notification; tapping it opens the task detail.
- Happy path: Tauri desktop app builds and installs; tray icon appears; native notification fires on run completion.
- Edge case: opening the PWA with no network shows the offline shell (app chrome visible, data shows last-fetched state).

**Verification:**
- Lighthouse PWA audit returns a passing score (installable + offline support).
- Tauri CI build produces signed artifacts for Mac.

---

- U19. **Polish, a11y, performance, and docs**

**Goal:** Apply the final quality pass: keyboard nav, a11y (WCAG AA, both themes, reduced motion), virtualization for large lists, empty states, and ship v1 docs.

**Requirements:** R12, R13

**Dependencies:** U1–U18

**Files:**
- Modify: various `apps/web/components/` (keyboard nav, focus rings, ARIA labels, reduced motion)
- Modify: `apps/web/components/task-inbox.tsx` (virtualization for large task lists)
- Modify: `apps/web/components/run-panel.tsx` (lazy mount of inactive tab content)
- Create: various empty-state components (`apps/web/components/empty-*.tsx`)
- Create: `docs/quickstart.md`
- Create: `docs/self-deploy.md`
- Create: `docs/agent-authoring.md`
- Create: `CONTRIBUTING.md`
- Create: `SECURITY.md`
- Create: `CODE_OF_CONDUCT.md`

**Approach:**
- Keyboard nav: `⌘K` command palette (already scaffolded), Tab order through all interactive surfaces, `Escape` closes modals/takeovers.
- a11y: WCAG AA contrast check both light and dark themes; all icon-only buttons have `aria-label`; reduced-motion: beam-field animation and status pulse animations respect `prefers-reduced-motion`.
- Virtualization: task inbox uses `@tanstack/react-virtual` for large lists (1000+ threads); subagent card list in run panel lazy-mounts on expand.
- Empty states: every list surface has a designed empty state (not a blank screen).
- v1 release criteria check: run through all 6 criteria in `docs/plan/04-roadmap.md` and confirm each is satisfied.
- Community files: CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md per `docs/plan/05-oss-setup.md`.

**Test scenarios:**
- a11y: axe-core scan on task inbox, task detail, and approvals returns zero violations.
- Keyboard: user can navigate the full task loop (sign in → dispatch task → view detail → approve interrupt) using keyboard only.
- Performance: task inbox with 500 threads renders without jank (no layout shifts during scroll).
- Reduced motion: with `prefers-reduced-motion: reduce`, no beam-field or pulse animations play.
- Docs: quickstart guide, followed by a new user with a LangSmith account, achieves a completed task with draft PR in under 15 minutes.

**Verification:**
- All v1 release criteria in `docs/plan/04-roadmap.md` are checked and confirmed.
- Lighthouse a11y score ≥ 90 on task inbox and task detail pages.
- `v1.0.0` tag created on main; announcement assets ready.

---

## System-Wide Impact

- **Interaction graph:** `DataProvider` context at the app root affects all pages simultaneously. Changes to the `AgentSource` registry in `packages/sdk` affect both `apps/web` and any future `apps/desktop`/`apps/mobile`.
- **Error propagation:** auth errors (401/403 from LangSmith) should surface as a re-auth prompt at the app root, not as individual per-component failures. The `DataProvider` interface owns this boundary.
- **State lifecycle risks:** `useStream` connections must be cleaned up on navigation away from task detail to avoid memory leaks. Fixture mode must remain fully functional when no session exists (U2 guard).
- **API surface parity:** `packages/sdk/src/types.ts` normalized types must stay in sync with both the `@langchain/react` projection shapes (evolving weekly) and the UI components. The adapter layer in `packages/sdk/src/stream/` is the decoupling seam; UI components never import `@langchain/react` directly.
- **Integration coverage:** the approvals surface (U11) depends on the stream wiring (U10) — the HITL interrupt must arrive via `useStream` for the approvals inbox to hydrate correctly. Unit tests that mock the stream adapter must use the golden transcripts from U5, not synthetic shapes.
- **Unchanged invariants:** `packages/ui/fixtures/index.ts` must remain importable and functional with zero environment variables at all times. CI should include a fixture-mode smoke test that runs with no `.env` set.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| MDA invocation API gated past beta for non-beta users | Classic `langgraph dev` + `langgraph deploy` is the complete fallback; M0 Spike 2 resolves which path M1 implements |
| `@langchain/react` v1 weekly churn breaks stream adapter | Pinned versions + golden-transcript contract tests (U5) catch regressions before merge; adapter layer in `packages/sdk` absorbs changes without touching UI components |
| OAuth scopes insufficient for all three API surfaces | Key-proxy is the complete auth baseline; OAuth ships only when Spike 1 confirms scope coverage |
| TypeScript strict mode reveals widespread errors in U2 | Strict TS pass is a dedicated step in U2 before any data wiring begins; easier to fix without concurrent changes |
| Approvals model mismatch harder to untangle than expected | U11 explicitly rebuilds on the correct contract from scratch rather than patching the legacy shape; golden transcript tests guard correctness |
| GitHub App token proxy callback security | The callback route exchanges code for token server-side; no token ever reaches the browser |
| v1 scope creep (org intelligence, Tauri, a11y) expanding past week 19 | Milestones are time-boxed per the roadmap; any M3/M4 item that slips moves to post-v1 backlog rather than delaying the v1 tag |

---

## Documentation / Operational Notes

- Vercel deployment: `apps/web` deploys automatically on merge to main; preview URLs per PR (configured in U1).
- Secrets: `LANGSMITH_API_KEY` is never committed; stored as a Vercel environment variable. `GITHUB_APP_PRIVATE_KEY` similarly.
- Tauri signing: Mac and Windows signing certificates must be configured in CI secrets before U18 ships.
- OSS announcement: held until v1.0.0 tag; develop in the open repo but market/announce at v1 (per `docs/plan/04-roadmap.md` Codex-CLI/Zed staging pattern).

---

## Sources & References

- **Origin documents:**
  - [docs/plan/04-roadmap.md](docs/plan/04-roadmap.md) — milestones, v1 release criteria, risk register
  - [docs/plan/06-frontend-implementation.md](docs/plan/06-frontend-implementation.md) — frontend evaluation, Phases A–F
  - [docs/plan/02-architecture.md](docs/plan/02-architecture.md) — runtime architecture, auth, streaming
  - [docs/plan/03-ui-spec.md](docs/plan/03-ui-spec.md) — UI contracts, component inventory
  - [docs/plan/05-oss-setup.md](docs/plan/05-oss-setup.md) — toolchain, CI, version pins
  - [docs/plan/08-deepagents-feature-map.md](docs/plan/08-deepagents-feature-map.md) — agent feature map
- Related code: `deep-work-frontend/` (all 53 files — seed for apps/web)
- Related code: `packages/ui/tokens.css`, `packages/ui/tailwind.preset.mjs`
- LangChain docs reference: `langchain-docs-reference/` (local shallow clone)
