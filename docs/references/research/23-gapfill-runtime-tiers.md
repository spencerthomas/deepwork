# Gap-fill: runtime tiers, licensing & pure-OSS fallback

*Condensed findings (agent-researched 2026-07-21, verified against live sources). Key facts and sources only; full reports available on request.*

## KEY FACTS
- langgraph-api 0.11.1 (PyPI) is Elastic-2.0; its two operative restrictions are (1) no providing the software to third parties as a hosted/managed service and (2) no moving/changing/disabling/circumventing license-key functionality — but the PyPI wheel's langgraph_license/validation.py is a literal noop stub ('No license check is performed'); enforcement lives in the langchain/langgraph-api Docker images.
- langgraph dev (langgraph-cli 0.4.31 MIT + langgraph-api/langgraph-runtime-inmem 0.31.1, both Elastic-2.0) requires NO LangSmith API key and does no license check; only phone-home is one anonymous CLI analytics event per command (disable: LANGGRAPH_CLI_NO_ANALYTICS=1); state persists to local .langgraph_api/ dir; docs: 'no data leaves the machine' unless tracing enabled.
- Standalone self-hosted Agent Server needs Postgres>=14 + Redis>=5 + LANGSMITH_API_KEY, and per langgraph-cli verbatim: 'For local dev, requires env var LANGSMITH_API_KEY with access to LangSmith Deployment. For production use, requires a license key in env var LANGGRAPH_CLOUD_LICENSE_KEY'; docs require an Enterprise plan for self-hosted and egress to https://beacon.langchain.com unless air-gapped-licensed.
- The historical free self-hosted tier (Self-Hosted Lite 1M nodes / Developer-plan 100k nodes-mo) has vanished from current docs and pricing — as of July 2026 there is no documented free standalone-container tier.
- Cloud deployments require Plus plan ($39/seat/mo, includes 1 free Serverless Small deployment); Developer plan ($0, 1 seat, 5k traces/mo) includes NO deployment; metering is LCU $1.50 / LSU $1.00 with published per-vCPU-hour rates.
- @langchain/react 1.0.28 useStream is fully backend-pluggable: UseStreamOptions is a discriminated union — AgentServerOptions (built-in 'sse'/'websocket' transports + fetch override) vs CustomAdapterOptions whose `transport:` takes any AgentServerAdapter (open/send/events/openEventStream/close + optional getState/getHistory), so a non-Agent-Server backend is officially supported.
- @langchain/langgraph-sdk 1.9.27 (MIT) exports HttpAgentServerAdapter({apiUrl, paths?, defaultHeaders?, onRequest?, fetch?, webSocketFactory?}) plus ProtocolSseTransportAdapter/ProtocolWebSocketTransportAdapter, speaking the open Agent Streaming Protocol (CDDL spec in langchain-ai/agent-protocol; MIT @langchain/protocol 0.0.18 type bindings).
- LangChain officially documents self-implementing the protocol server in your own framework (Next.js/SvelteKit/Nuxt/Hono on Cloudflare/Deno) via the MIT deployment-cookbook repo: minimum three routes — POST /api/threads/:id/commands, POST /api/threads/:id/stream (SSE), GET|POST /api/threads/:id/state — plus threads list/delete/history for the sidebar, using MIT checkpointers (langgraph-checkpoint-postgres 3.1.0 py / @langchain/langgraph-checkpoint-postgres 1.0.4 js).
- A pure-OSS custom server loses these Agent Server features: double-texting strategies (docs: 'not available in the LangGraph open source framework'), resumable joinStream/Last-Event-ID replay (unless the adapter's replay-buffer contract is reimplemented), crons, run webhooks, assistants CRUD+versioning, /mcp endpoint, /a2a endpoint + agent card, Studio integration, and the durable background-run task queue.
- Aegra (github.com/ibbybuilds/aegra; aegra-api 0.9.24 on PyPI, Apache-2.0, released 2026-07-05) is an actively maintained FastAPI+Postgres drop-in reimplementation of the LangGraph Platform API — a viable OSS backend for legacy langgraph-sdk Client compatibility.
- LangSmith Sandboxes ARE usable on the free Developer plan: 5 LCU + 1 LSU of sandbox usage free per month on Developer/Plus, capped at 10 sandboxes on Developer; SDK is `pip install langsmith[sandbox]` / SandboxClient; the langsmith SDK itself is MIT (0.10.9); zero-cloud fallback = deepagents LocalShellBackend(virtual_mode=...)/FilesystemBackend (MIT, verified in 0.6.12 source).
- Managed Deep Agents is private beta, LangSmith Cloud US region only, CLI-first (mda from managed-deepagents 0.3.1 MIT; public API examples removed), self-hosted/hybrid unsupported, no published quotas; the managed runtime owns backend/store/checkpointer/memory/skills and the system prompt (instructions.md + skills/ + /memories/AGENTS.md in Context Hub).
- 'LangGraph Platform' was renamed 'LangSmith Deployment' (and LangGraph Studio → LangSmith Studio) per changelog.langchain.com, October 13 2025; APIs/pricing/contracts unchanged.
- Version/license map (2026-07-21): langgraph 1.2.9 MIT, langgraph-sdk 0.4.2 MIT, deepagents 0.6.12 py / 1.11.1 js MIT, @langchain/langgraph-cli 1.4.3 MIT, @langchain/core 1.2.3, @langchain/langgraph 1.4.8; Elastic-2.0: langgraph-api 0.11.1 and langgraph-runtime-inmem 0.31.1 only.
- Recommended v1 architecture seam: one frontend on useStream covering all tiers — built-in SSE/WS transport for Agent Server tiers, HttpAgentServerAdapter/custom AgentServerAdapter for the pure-OSS default tier — with deepagents agent modules kept runtime-agnostic (no backend/store/checkpointer in the agent definition, matching MDA's constraint).

## OPEN QUESTIONS
- Whether any free node-execution quota still exists for the standalone Agent Server run with only a free LangSmith API key (historical Self-Hosted Lite 1M nodes / Developer 100k nodes-mo tiers are gone from docs/pricing; forum threads from 2025 were never answered by staff; enforcement behavior of the Docker image's license validation — hard fail vs warn vs node cap — could not be inspected).
- Managed Deep Agents beta pricing/billing (not listed on langchain.com/pricing; presumably free during private beta but unconfirmed) and its GA timeline/API surface (programmatic API 'removed' during beta).
- Exact behavior of the enforcing license check in the langchain/langgraph-api Docker image at startup without LANGGRAPH_CLOUD_LICENSE_KEY (docs imply free-API-key local testing works, but the node/run quota, if any, is undocumented; could not pull/inspect the image in this environment).
- Whether Elastic-2.0 'hosted or managed service' clause would bar a Deep Work user from offering a multi-tenant SaaS whose backend is Agent Server (LangChain's own FAQ/legal guidance on internal-product-vs-resale line not found in docs; needs legal review or LangChain confirmation).
- Sandbox free-tier LCU/LSU conversion into concrete CPU-hours/GB-months (pricing page gives unit prices but not the sandbox metering formula), and any hard concurrent-sandbox limit on Plus (10-sandbox cap documented only for Developer).
- Whether @langchain/vue/svelte/angular expose the identical CustomAdapterOptions branch as @langchain/react (docs imply yes — all four listed as protocol clients — but only the react/sdk .d.ts were inspected).
- GitHub MCP access in this session was restricted to spencerthomas/deepwork, so langchain-ai/langgraph-api repo issues/discussions could not be enumerated directly (worked around via PyPI wheel extraction, docs, and web sources).

## SOURCES
- Self-host standalone servers — Docs by LangChain — https://docs.langchain.com/langsmith/deploy-standalone-server
- Local development & testing (langgraph dev vs up) — https://docs.langchain.com/langsmith/local-dev-testing
- LangGraph CLI reference (up/dev/build/deploy) — https://docs.langchain.com/langsmith/cli
- Data storage and privacy (CLI telemetry, dev server, standalone license checks) — https://docs.langchain.com/langsmith/data-storage-and-privacy
- Self-hosted egress to beacon.langchain.com — https://docs.langchain.com/langsmith/self-host-egress
- Deploy to self-hosted (Enterprise plan requirement, topologies) — https://docs.langchain.com/langsmith/deploy-to-self-hosted-overview
- Deploy to Cloud overview (Plus plan requirement) — https://docs.langchain.com/langsmith/deploy-to-cloud-overview
- Hybrid deployment — https://docs.langchain.com/langsmith/hybrid
- LangChain pricing (plans, LCU/LSU, sandbox free tier) — https://www.langchain.com/pricing
- Double texting (LSD-only feature) — https://docs.langchain.com/langsmith/double-texting
- Streaming (joinStream, Last-Event-ID resumability) — https://docs.langchain.com/langsmith/streaming
- Cron jobs — https://docs.langchain.com/langsmith/cron-jobs
- MCP endpoint in Agent Server — https://docs.langchain.com/langsmith/server-mcp
- A2A endpoint in Agent Server — https://docs.langchain.com/langsmith/server-a2a
- LangSmith Sandboxes — https://docs.langchain.com/langsmith/sandboxes
- Sandbox SDK usage — https://docs.langchain.com/langsmith/sandbox-sdk
- Managed Deep Agents overview (private beta) — https://docs.langchain.com/langsmith/managed-deep-agents-overview
- Deploy a Managed Deep Agent — https://docs.langchain.com/langsmith/managed-deep-agents-deploy
- Deploy full-stack web apps (self-implemented protocol servers) — https://docs.langchain.com/langsmith/deploy-frameworks-and-platforms
- Agent Server changelog (v0.11, protocol v2) — https://docs.langchain.com/langsmith/agent-server-changelog
- Product naming changes: LangSmith Deployment (Oct 2025) — https://changelog.langchain.com/announcements/product-naming-changes-langsmith-deployment-and-langsmith-studio
- langgraph-api on PyPI (Elastic-2.0, 0.11.1) — https://pypi.org/project/langgraph-api/
- langgraph-runtime-inmem on PyPI (Elastic-2.0) — https://pypi.org/project/langgraph-runtime-inmem/
- langgraph-checkpoint-postgres on PyPI (MIT) — https://pypi.org/project/langgraph-checkpoint-postgres/
- langsmith on PyPI (MIT, sandbox extra) — https://pypi.org/project/langsmith/
- @langchain/langgraph-sdk on npm (1.9.27, MIT) — https://www.npmjs.com/package/@langchain/langgraph-sdk
- @langchain/react on npm (1.0.28, MIT) — https://www.npmjs.com/package/@langchain/react
- @langchain/protocol on npm (0.0.18, MIT; CDDL source of truth) — https://www.npmjs.com/package/@langchain/protocol
- langchain-ai/agent-protocol (streaming protocol.cddl) — https://github.com/langchain-ai/agent-protocol/tree/main/streaming
- langchain-ai/deployment-cookbook (MIT reference implementations) — https://github.com/langchain-ai/deployment-cookbook
- langchain-ai/helm (langgraph-cloud chart) — https://github.com/langchain-ai/helm/blob/main/charts/langgraph-cloud/README.md
- Aegra — open-source LangGraph Platform alternative (Apache-2.0) — https://github.com/ibbybuilds/aegra
- aegra-api on PyPI (0.9.24, Apache-2.0) — https://pypi.org/project/aegra-api/
- Forum: standalone container 1M node execution limit (unanswered) — https://forum.langchain.com/t/langgraph-standalone-container-1-million-nodes-execution-limit/484
- Forum: deployment models with licence vs free — https://forum.langchain.com/t/deployment-models-with-licence-vs-free/912
- LangGraph is MIT-Licensed, but Your Production Deployment Might Not Be (Mar 2026) — https://rvernica.github.io/2026/03/langchain-license
- managed-deepagents on PyPI (mda CLI, MIT) — https://pypi.org/project/managed-deepagents/
