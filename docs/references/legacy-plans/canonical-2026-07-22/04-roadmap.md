# 04 · Roadmap to v1

*Deep Work planning docs · 2026-07-21. Build-to-v1 first, then open wide (Codex-CLI/Zed staging pattern): develop in the open repo but market/announce at v1.*

## Milestones

### M0 — Foundations & de-risking spikes (week 1–2)

- Monorepo scaffold (pnpm + Turborepo + changesets + biome; apps/web, packages/{agent,sdk,ui}) per [05](05-oss-setup.md); CI (typecheck/lint/test/build); Vercel previews.
- `packages/ui` seeded from the committed tokens; shadcn re-theme; shell chrome (navbar/tabs/sidebar/rail) against static data.
- **Spike 1 — OAuth**: probe LangSmith `/.well-known/oauth-authorization-server` (scopes), DCR a public client, test bearer acceptance on api.smith.langchain.com vs control plane vs `*.langgraph.app`. Output: auth decision memo (OAuth-first vs key-first at launch).
- **Spike 2 — MDA loop**: with the beta account, `mda init/dev/deploy` a minimal agent; verify external `useStream` against the deployment URL with identity presets; verify `/v2/deployments` + tarball upload from our own code (not the CLI).
- **Spike 3 — stream contract**: golden-transcript tests of protocol v2 against `langgraph dev` (content blocks, tools channel, HITL respond, subagent namespaces, resume with Last-Event-ID).
- Exit: the three riskiest unknowns are facts; shell renders.

### M1 — The task loop (week 3–6)

- `packages/agent` v0: deepagents project (research + writing task types; no sandbox yet), deployable via `mda` and `langgraph dev`.
- Agent-source registry (connect MDA deployment / any deployment URL / `langgraph dev`), key-proxy server route, org/workspace picker (API-key path; OAuth if Spike 1 green).
- Task inbox (threads.search aggregation, status chips, filters) + New-task composer.
- Task detail: streaming narration, tool-call cards, todos tray, steering composer with queue/interrupt, trace links.
- Exit: dispatch → watch → steer → done, from the web app, against a real MDA deployment. **First dogfood release.**

### M2 — Approvals + coding tasks (week 7–11)

- HITL end-to-end: `interrupt_on` config in agent; approvals inbox + interrupt cards (batch, edit, reject/respond); plan-approval flow in task detail.
- Verification: `RubricMiddleware` wired into templates (rubric field in composer; verdicts/iterations in the run panel); fault-tolerance middleware stack in `packages/agent`.
- Execution: thread-scoped LangSmith Sandbox backend, environment = snapshot + `setup.sh` editor; GitHub App (install flow, repo picker) + zero-token proxy-callback route; `commit_and_open_pr` → draft PR; files-changed rail via connector routes; diff review with batched line comments.
- Sub-agent cards; branching/fork-from-checkpoint.
- Exit: the Codex-parity loop — coding task to reviewed draft PR — works, with approvals from the web UI.

### M3 — Fleet manager + schedules (week 12–15)

- Agents index/detail (deployments + `/v1/deepagents/*` + Fleet read); file-first config editor (instructions/skills/memory via Context Hub; MCP connectors; per-tool Auto/Ask matrix); template gallery + create/deploy wizard; Fleet-export import/export.
- Schedules CRUD (crons API) + Activity feed; untrusted-payload rendering.
- Org-intelligence Layers 0–1 ([doc 07](07-org-intelligence.md)): `org-memory/` starter template + onboarding seeding interview; tracing-metadata conventions; org-analyst schedule template (langsmith-mcp-server digests); Insights config provisioning (or deep links if the beta API probe fails).
- `dcode` companion: *Continue in terminal* handoff (`--sandbox-id`), plugins screen wired to the Claude/Codex-compatible marketplace format.
- Exit: an org's agents are manageable from Deep Work without touching smith.langchain.com (except gated Fleet CRUD, which links out).

### M4 — Multi-surface + v1 hardening (week 16–19)

- PWA (manifest, Web Push via run-completion webhooks, offline shell, bottom bar, one-tap approvals).
- Tauri desktop (tray, native notifications, deep links, device-flow sign-in, updater).
- Polish: command palette, keyboard nav, empty states, a11y pass (AA both themes, reduced motion), performance (virtualization, lazy subagent mounts).
- Docs: quickstart ("15 minutes to first PR"), self-deploy guide, agent-authoring guide; community files.
- Exit: **v1 release criteria** (below) all green → tag v1.0.0, announce.

## v1 release criteria

1. Sign-in → deployed agent → first completed task with draft PR **< 15 min** (measured with a fresh account).
2. Full loop (dispatch/steer/approve/diff/merge) completes **from a phone** (installed PWA).
3. Fleet agent connected and driven through inbox + approvals without smith.langchain.com.
4. Trace link on 100% of runs; agent config round-trips through Fleet-export format.
5. Zero secrets in sandboxes (verified by test); untrusted-payload boundaries on all webhook/schedule content.
6. CI green on typecheck/lint/test; docs cover quickstart + deploy + architecture; MIT + trademark hygiene audited.

## Post-v1 backlog (explicitly deferred)

Pure-OSS backend tier (protocol server / Aegra adapter) · native Expo apps · Slack/Linear channels for task creation · chat-to-configure agent builder · GitLab · multi-repo tasks/worktree parallelism · team RBAC surfaces · evals integration (LangSmith datasets from task outcomes) · goal lifecycle (dcode-style draft→review→amend on top of RubricMiddleware) · async-subagent supervisor pattern (parallel workstreams as linked tasks) · interpreter/PTC templates hardening as the beta stabilizes · ACP server for editor integrations (Zed/JetBrains) · A2A/MCP exposure of Deep Work agents documented for interop · **org-intelligence ladder** ([doc 07](07-org-intelligence.md)): v1.x memory-synthesis review loop → v2 OKF knowledge base (openwiki) + structured data plane (dbt-mcp, data-analyst template) → v3 Graphiti temporal org graph.

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| MDA invocation API stays design-partner-gated past beta | Med | High | Classic Deployment + `langgraph dev` are fully public and feature-equivalent for v1 scope; MDA-specific bits (identity presets, managed sandboxes) degrade to documented classic patterns; leverage the LangChain relationship |
| `deployment_type: managed_deep_agent` rejected for non-beta orgs (affects *users*, not just us) | Med | Med | Deploy wizard detects and falls back to classic `langgraph.json` deployment of the same agent |
| OAuth scopes insufficient for control plane / data plane | Med | Med | Key-based auth is a complete fallback; OAuth ships whenever scope coverage allows |
| Frontend SDK v1 churn (weekly 1.0.x releases) | High | Low-Med | Pinned versions, golden-transcript contract tests, small adapter layer in `packages/sdk` |
| Beta features shift under us (MDA 0.4.0-dev channel) | High | Low-Med | Track dev channel in CI against a canary deployment; feature-flag dev-channel-only UI (per-user memory, Slack channels) |
| Trademark/brand friction | Low | Med | Hygiene rules already encoded (naming, fonts, disclaimer); resolve direct with LangChain given the contribution intent |
| Scope creep toward Fleet parity | Med | Med | The cut line in [01](01-vision.md) is the contract; anything not listed needs a roadmap PR |

## Open questions (tracked, non-blocking)

- OAuth `scopes_supported` reality (M0 Spike 1 resolves).
- Whether Fleet self-config-via-chat works over the public run API (would enable richer Fleet management without CRUD APIs).
- MDA quotas/pricing at GA (cost guidance docs placeholder until published).
- Whether LangChain wants this upstreamed (affects naming/branding timeline, not architecture).
