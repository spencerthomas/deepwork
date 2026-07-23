# Feature specs

*Deep Work planning docs · 2026-07-22. The layer between the strategic plan ([01–08](../)) and implementation: one spec per feature area. v1 specs are **implementation-ready** (scope, design, contracts, edge cases, acceptance criteria, ordered task breakdown); post-v1 specs are **design-complete** (everything except the task breakdown, which would be speculative). Decisions and open questions are tracked centrally in the [decision log](../decisions.md) — specs cite D-/P-/O- IDs from it.*

**Status legend:** `draft` (written, not yet reviewed with Tom) → `reviewed` (walked through, questions answered) → `locked` (binding for implementation; changes need a PR touching this doc).

## Spec template

Every spec uses the same numbered sections so cross-referencing stays cheap: **1 Scope** (in/out) · **2 Dependencies & seams** · **3 Design** (architecture/UX incl. loading/empty/error/degraded states for UI surfaces) · **4 Contracts** (data shapes, endpoints, config schemas) · **5 Edge cases & failure modes** · **6 Security & privacy** · **7 Acceptance criteria** · **8 Task breakdown** (implementation-ready specs; design-complete specs carry *Adoption triggers & sequencing* instead) · **9 Open questions** · **10 Risks**.

## Catalog

### Foundations (M0)

| Spec | Area | Milestone | Depth | Status |
|---|---|---|---|---|
| [F01](01-monorepo-and-oss-infra.md) | Monorepo & OSS infrastructure — scaffold, toolchain, CI, releases, community files | M0 | impl-ready | draft |
| [F02](02-m0-spikes.md) | M0 de-risking spikes — OAuth probe, MDA loop, stream-contract golden transcripts | M0 | impl-ready | draft |
| [F03](03-design-system-and-ui-package.md) | Design system & `packages/ui` — tokens, components, fixtures, Storybook | M0 | impl-ready | draft |
| [F07](07-app-shell-and-navigation.md) | App shell & navigation — chrome, tabs, sidebar/rail, command palette, responsive | M0 | impl-ready | draft |

### Platform layer (M0–M2)

| Spec | Area | Milestone | Depth | Status |
|---|---|---|---|---|
| [F04](04-sdk-and-agent-sources.md) | `packages/sdk` & agent sources — source registry, control-plane client, normalization, DataProvider | M1 | impl-ready | draft |
| [F05](05-auth-and-identity.md) | Auth & identity — Sign in with LangSmith, API-key fallback, the three auth planes | M1 | impl-ready | draft |
| [F28](28-backend-glue-service.md) | Backend glue service (`apps/server`, Python/FastAPI) — proxies, GitHub tokens, push fan-out (P-005) | M0–M2 | impl-ready | draft |
| [F06](06-onboarding-and-deploy.md) | Onboarding & deploy wizard — org picker, agent deploy/connect, 15-minute north star | M1–M3 | impl-ready | draft |

### The task loop (M1–M2)

| Spec | Area | Milestone | Depth | Status |
|---|---|---|---|---|
| [F08](08-task-inbox.md) | Task inbox — aggregation, grouping, filters, new-task composer | M1 | impl-ready | draft |
| [F09](09-task-detail-and-streaming.md) | Task detail & streaming — narration, tool/subagent cards, todos, steering, branching | M1 | impl-ready | draft |
| [F10](10-approvals-inbox.md) | Approvals inbox — v1 HITL contract end-to-end | M2 | impl-ready | draft |
| [F11](11-execution-and-environments.md) | Execution & environments — sandboxes, snapshots, `setup.sh`, egress | M2 | impl-ready | draft |
| [F12](12-github-and-git-flow.md) | GitHub integration & git flow — GitHub App, zero-token proxy, branches, draft PRs | M2 | impl-ready | draft |
| [F13](13-files-diff-and-review.md) | Files, diff & review — file browser, diff takeover, line comments, artifacts, terminal pane | M2 | impl-ready | draft |

### The agent (M1–M2)

| Spec | Area | Milestone | Depth | Status |
|---|---|---|---|---|
| [F14](14-agent-package.md) | `packages/agent` — deepagents composition, middleware, tools, identity, connectors | M1–M2 | impl-ready | draft |
| [F15](15-task-templates.md) | Task-type templates — coding/research/writing as assistant configs, profiles | M1–M2 | impl-ready | draft |
| [F16](16-verification-and-rubrics.md) | Verification & rubrics — RubricMiddleware, verification panel; goal lifecycle (v1.x) | M2 | impl-ready | draft |

### Fleet manager & operations (M3)

| Spec | Area | Milestone | Depth | Status |
|---|---|---|---|---|
| [F17](17-fleet-manager.md) | Fleet manager — agents index/detail, file-first config editor, Auto/Ask matrix, deploy | M3 | impl-ready | draft |
| [F18](18-schedules-and-activity.md) | Schedules & Activity — crons CRUD, activity feed, untrusted-payload boundaries | M3 | impl-ready | draft |
| [F22](22-org-intelligence-v1.md) | Org intelligence v1 (Layers 0–1) — org-memory template, tracing conventions, org-analyst, Insights | M3 | impl-ready | draft |
| [F25](25-dcode-integration.md) | dcode integration — continue-in-terminal, plugins screen, shared conventions | M3 (+v2 parts) | impl-ready | draft |

### Surfaces & delivery (M4)

| Spec | Area | Milestone | Depth | Status |
|---|---|---|---|---|
| [F19](19-notifications-and-push.md) | Notifications & push — one run-completion pipeline for all surfaces | M4 | impl-ready | draft |
| [F20](20-pwa-and-mobile.md) | PWA & mobile — manifest, offline shell, bottom bar, one-tap approve; Expo (post-v1) | M4 | impl-ready | draft |
| [F21](21-desktop-tauri.md) | Desktop (Tauri v2) — tray, notifications, deep links, updater, device-flow sign-in | M4 | impl-ready | draft |

### Post-v1 (design-complete)

| Spec | Area | Horizon | Depth | Status |
|---|---|---|---|---|
| [F23](23-org-intelligence-v1x-consolidation.md) | Org intelligence v1.x (Layer 2) — consolidation agent + memory review loop | v1.x | design-complete | draft |
| [F24](24-org-intelligence-v2-v3.md) | Org intelligence v2–v3 (Layers 3–5) — OKF/openwiki, structured data plane, Graphiti | v2–v3 | design-complete | draft |
| [F26](26-oss-selfhost-tier.md) | Pure-OSS self-host tier — protocol server / Aegra, feature-loss matrix | post-v1 | design-complete | draft |
| [F27](27-interop-acp-a2a.md) | Interop — ACP editor integrations, A2A/MCP exposure | post-v1 | design-complete | draft |

## Review process

Specs are drafted in full, then reviewed with Tom in batches (foundations → platform → task loop → agent → fleet/ops → surfaces → post-v1). Each spec's §9 lists the questions that need Tom's answers; triaged questions roll up into the [decision log](../decisions.md). A spec flips to `reviewed` when its batch session closes, and to `locked` when its milestone starts.
