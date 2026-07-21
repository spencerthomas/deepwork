# Research: open-swe + LangSmith Fleet (agent a5ea90111708be37d, completed 2026-07-21)

## open-swe — two lives in one repo (~10.4k stars, MIT, no releases/tags)
- **v1 (Aug 2025–early 2026)**: TS, hand-built manager/planner/programmer LangGraph graphs, Daytona sandboxes, GitHub issue labels (`open-swe`, `open-swe-auto`, `open-swe-max`, `open-swe-max-auto`), web UI at swe.langchain.com. Survives only in git history (snapshot commit `f246c81`).
- **v2 (relaunched 2026-03-17, ACTIVE — commits daily thru 2026-07-21)**: full **Python rewrite composed on deepagents** (`deepagents==0.7.0a7` py, `langgraph>=1.1.10`, `langchain>=1.3.9`). "Framework for internal coding agents." Positioned vs Stripe Minions, Ramp Inspect, Coinbase Cloudbot.

### v2 architecture
- langgraph.json: python 3.12, **5 graphs**: `agent`, `reviewer`, `analyzer`, `chat`, `scheduler`; FastAPI mounted via `http.app: agent.webapp:app` (webhooks /webhooks/slack, /webhooks/linear + dashboard API); **checkpointer TTL 30 days** (delete strategy, hourly sweep).
- Invocation: mention-driven — Slack (@bot in thread, `repo:owner/name`), Linear (`@openswe` comment, eyes-reaction ACK), GitHub PR comments. Web dashboard with chat. No issue-label flow anymore.
- Orchestration: deep agent + subagents (`task` tool) + middleware: `check_message_queue_before_model` (**double-texting/steering mechanism**), `notify_step_limit_reached`, `ToolErrorMiddleware`, auto-PR middleware.
- ~15 curated tools: `execute`, `fetch_url`, `http_request`, `commit_and_open_pr`, linear_*, slack_*, + deepagents built-ins (read/write/edit_file, ls/glob/grep, write_todos, task).
- Sandboxes pluggable: **Modal, Daytona, Runloop, E2B, LangSmith (default; snapshot UUID → DEFAULT_SANDBOX_SNAPSHOT_ID)**. Persistent sandbox per thread, auto-recreate; parallel tasks = separate sandboxes.
- Creds: GitHub ops via `GH_TOKEN=dummy gh` through **LangSmith credential proxy** (server-side, never exposed to model). Encryption keys for stored user creds.
- Context: repo `AGENTS.md` injected into system prompt; full Slack/Linear thread up front.
- HITL: explicit plan-approval tool re-added 2026-07-20 (#1777). Output = draft PRs + replies in source channel.

### v2 UI (ui/, "open-swe-dashboard")
- **TanStack Start + Vite 7 + React 19.2 + TS 5.9**, TanStack Router/Query, **Tailwind 4.2**, shadcn/Base UI, Lucide + Phosphor, **Monaco + Shiki**, Streamdown (streaming md), PWA (vite-plugin-pwa), pnpm, Vercel deploy w/ same-origin proxy rewrite.
- Uses `@langchain/langgraph-sdk` + React bindings (useStream) + `/dashboard/api/*` from mounted FastAPI.
- Auth: GitHub App, split OAuth: agent-runtime flow (LangSmith agent-auth provider) + dashboard-login flow; `DASHBOARD_JWT_SECRET`, `TOKEN_ENCRYPTION_KEY`. GH App perms: Contents, PRs, Issues, Checks RW; org-member read for access control. Allowlists in LangGraph Store, admin dashboard.
- v1 web (historical): Next.js 15 + React 19 + Tailwind 4 + shadcn + Zustand + SWR, Yarn+Turborepo monorepo `apps/{web,open-swe,docs,cli}` + `packages/shared`, `langgraph-nextjs-api-passthrough`.

### Lessons
- Compose on the harness (v2 thesis); tool curation > tool count (~15); meet users in existing surfaces; isolation-as-safety (full perms in disposable sandbox, no per-action prompts, server-side cred proxy).
- v1 pain: model fallback exhaustion, provider config fragility, API keys lost on checkpoint restart, GitLab requested+declined, no Docker image. → Deep Work: get multi-provider config + resumability right.

## LangSmith Fleet (= Agent Builder rebrand, announced 2026-03-19, GA on cloud; self-hosted beta)
- No-code enterprise agent workspace: "Agents for the whole company." Agents ARE deepagents on **LangSmith Agent Server** (standard LangGraph SDK/REST works: PAT `X-API-Key` + `X-Auth-Scheme: langsmith-api-key`, `<id>.us.langgraph.app`).
- Templates: **Executive Assistant**, **Software Engineer** ("ships code from Slack, Linear, GitHub in a sandbox" — hosted open-swe kin).
- Channels: Slack (generated app per agent), Gmail, MS Teams; **Schedules** (cron, UTC, per-schedule prompt). Channels/schedules need fixed-cred identity.
- HITL: per-tool **Auto vs Ask**; accept/reject + feedback; Slack-native approve/deny; **centralized cross-agent approvals inbox** (smith.langchain.com/agents/inbox) — their headline differentiator.
- Identity: **"Claws"** (fixed creds, required for channels/schedules) vs **"Assistants"** (per-user OAuth + audit). Immutable once set.
- Governance: per-agent Can clone/run/edit; RBAC + ABAC per MCP/integration; SCIM; workspace credential control; LangSmith tracing as audit.
- Memory: file-based (`AGENTS.md`, `tools.json`, `subagents/*`, `skills/*`, memories folder via write_file/edit_file). Self-updating agents (can rewrite own instructions/tools).
- Models: Fast/Pro/Max tiers, provider-abstracted, BYO OpenAI/Anthropic-compatible endpoints.
- Pricing (from 2026-07-15): **LCU units** — Free 5 LCU/org/mo; Plus $39/seat 25 LCU/org/mo; $1.50/LCU overage; model costs included.
- **Code export**: MIT `fleet-deepagents-export` (PyPI): ZIP of fleet/{AGENTS.md, config.json, tools.json, subagents/, skills/} → runnable local deepagents project w/ custom_tools.py, custom_middleware.py, custom_skills/, REPL cli.py.
- Fleet webhooks: publish hooks POST config + base64 ZIP (CI/CD for agents).

## Managed Deep Agents (the beta the user has access to) — DISTINCT from Fleet
- **Private beta, waitlist, US-only LangSmith Cloud. CLI-first: `mda init/dev/deploy`.** `managed-deepagents` package (Python/TS). Context-Hub-backed instructions/skills/memory. LangSmith sandboxes. Durable runs. API docs deliberately removed (CLI-only for now).
- Product ladder: **Fleet (no-code) → Managed Deep Agents (code-first, managed infra) → LangSmith Deployment (full custom) → OSS deepagents (self-host)**.

## Also discovered
- **Deep Agents Code (`dcode`)** — LangChain's OSS terminal coding agent on Deep Agents SDK (memory, skills, subagents, remote sandboxes, MCP, HITL) — the Claude Code analog. docs.langchain.com/oss/javascript/deepagents/code/overview.

## Deep Work positioning (implication)
- Deep Work = open-source, coding+work-first, multi-surface (web/mobile/desktop) client & framework — vs Fleet (proprietary no-code) and open-swe (framework, chat dashboard only, no mobile/desktop). Fleet's comparison page (vs Claude Cowork, Amazon Quick, Google Workspace Studio, MS Copilot) is a ready-made feature checklist for v1.

## Open questions carried forward
- v2 `analyzer`/`scheduler` graphs + dispatch.py/reconcile.py internals (task queue model).
- Managed Deep Agents API surface beyond CLI (private beta; user has access — can inspect firsthand).
- dcode maturity; whether LangChain plans its own Cowork-style surface.
