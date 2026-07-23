# Research: openwiki + opengpts (agent a0c25ea2aac8b1a11, completed 2026-07-21)

## openwiki — TL;DR
- NOT a web wiki app. TypeScript **CLI** using deepagents to generate/maintain agent-consumable wikis (Markdown, Google OKF v0.1 format). Code mode (repo docs in `openwiki/`) + Personal mode (`~/.openwiki/wiki` from connectors: Gmail, Notion, GitHub, X, web, HN).
- Built on **deepagents ^1.11.1 (JS)** + langchain ^1.5.3. `createDeepAgent({ model, tools, checkpointer, backend, middleware, skills, permissions, systemPrompt })`.
- **CompositeBackend** routing: custom `OpenWikiLocalShellBackend` (shell exec, 100KB output cap, 120s timeout) primary + read-only `FilesystemBackend` mounted at `/skills/` + a write-restricted docs-only backend. Virtual FS mode on.
- Middleware: index-consistency middleware + OKF format middleware. Skills dir mounted with write-deny **permissions** (deepagents 1.11 has skills + permissions API in production).
- Checkpointing: SQLite at `~/.openwiki/openwiki.sqlite` for interactive threads (thread id = `openwiki-{sha256}-{ts}-{random}`); in-memory for one-shot runs; git-hash skip-if-unchanged.
- No `langgraph.json` — does NOT target LangGraph/LangSmith Deployment. Deployment = CLI + CI templates (GH Actions/GitLab/Bitbucket auto-PR) + built-in cron scheduler (`src/schedules.ts`).
- UI: Ink 5 + React 18 terminal app. Progress = `agent.streamEvents(..., {version:"v3"})` → typed events (`text`, `tool_start`, `tool_end`, `debug`) via `onEvent` adapter.
- Models: Anthropic, OpenAI (+base URL), Gemini, Vertex, Bedrock, OpenRouter, Cloudflare, **ChatGPT OAuth** (BYO subscription). MCP stdio with credential-isolated child envs.
- Status: ALIVE. 12.7k stars, v0.2.1 released 2026-07-20, daily commits, LangChain staff maintained (Brace Sproul, Colin Francis). MIT, Node >=22, pnpm, vitest.

### Borrow for Deep Work
1. streamEvents→typed-progress-events adapter (one seam shared by web/mobile/desktop renderers).
2. CompositeBackend with scoped sub-backends + write-deny permissions (workspace isolation pattern).
3. Checkpointer split: durable for interactive threads, ephemeral for batch; deterministic thread ids; skip-run-if-unchanged.
4. CI/cron as deployment for recurring agent work; index/manifest middleware.
5. AVOID for UI guidance (no web UI) and for managed-deployment validation (none).

## opengpts — TL;DR
- 2023–24 GPTs/Assistants clone. **Archived 2026-02-24.** Real dev ended mid-2024. 6.7k stars.
- Domain model to keep: assistants (named shareable configs) → threads → runs — proto-LangGraph-Platform; managed deep agents gives this for free.
- Borrow: schema-driven assistant config UI (forms rendered from backend config schema), tool-checkbox allowlist per assistant, per-assistant file upload.
- Obsolete: LangServe, MessageGraph, pickle checkpoints, fetch-event-source SSE, react-query v3, self-managed Postgres/Redis, Helm/Cloud Run recipes. Use LangGraph Server API + useStream instead.
- Cautionary tale: checkpoint-format migration broke old threads → version thread/checkpoint schema from day one.

## Open questions carried forward
- deepagents 1.11 `permissions` API exact shape (matters for Deep Work permission prompts).
- OKF v0.1 stability (candidate for Deep Work memory/wiki format).
