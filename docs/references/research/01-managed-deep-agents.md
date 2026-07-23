# Managed Deep Agents & LangSmith Deployment

*Condensed findings (agent-researched 2026-07-21, verified against live sources). Key facts and sources only; full reports available on request.*

## KEY FACTS
- Managed Deep Agents (MDA) is LangChain's hosted runtime for code-first Deep Agents, announced at Interrupt 26 with private beta starting May 13, 2026; it is LangSmith Cloud US-region only, CLI-first, and the programmatic create/update/invoke API is gated during beta (contact LangChain team).
- MDA ships as the `managed-deepagents` package (PyPI stable 0.3.1 / dev 0.4.0.dev72 via `pip install --pre`; npm `managed-deepagents@dev` = 0.4.0-dev.72) exposing define_deep_agent/defineDeepAgent, define_identity, define_schedule, define_sandbox, define_mcp_servers, and the `mda` CLI (init/dev/deploy).
- `mda deploy` compiles to .mda/build, forwards non-reserved .env entries as hosted deployment secrets, syncs instructions.md and skills/** to a per-deployment Context Hub repo (memory at /memories/AGENTS.md is preserved), creates a hosted LangGraph deployment, and reconciles schedules/ as LangSmith crons; build limit 200 MB.
- The managed runtime owns backend, store, checkpointer, memory, skills, and system prompt — authors control model ("{provider}:{model_id}" via init_chat_model), tools, middleware, subagents, permissions, interrupt_on, response_format, context_schema.
- MDA identity is opt-in and fail-closed: presets (private-assistant, multi-tenant-saas, shared-bot, internal-tool, service), trusted_backend ingress (X-MDA-Ingress-Secret/X-MDA-Actor-Id/X-MDA-Tenant-Id headers) or validated_token ingress with built-in providers (Auth0, Clerk, Okta, Cognito, Entra, Google, Supabase, OIDC, GitHub, guest tokens via POST /identity/guest signed with MDA_GUEST_SIGNING_KEY), yielding a frozen runtime.identity envelope in tools/middleware.
- MDA sandboxes are per-thread LangSmith Sandboxes configured via define_sandbox(LangSmithSandbox, scope="thread", idle_ttl_seconds, default_timeout) with an optional sandbox/setup.sh provisioning script.
- LangGraph Platform is now 'LangSmith Deployment'; the runtime is 'Agent Server' (langgraph-api 0.11.1 on PyPI, licensed Elastic-2.0 — source-available, NOT OSI open source), deployable as Cloud, self-hosted control plane, Hybrid, or standalone container (needs Postgres, Redis, and a LangSmith license key).
- Classic deployment uses langgraph.json (dependencies, graphs, auth, http, checkpointer.ttl, webhooks, api_version, base_image) plus langgraph-cli 0.4.31 / @langchain/langgraph-cli 1.4.3; `langgraph deploy` (beta) builds+pushes+deploys to Cloud in one step with --deployment-type serverless|dedicated (new pricing) or dev|prod (legacy until Oct 1, 2026).
- New usage-based pricing bills LangChain Compute Units (compute) + LangChain Storage Units (storage); Serverless deployments scale to zero (beta) on shared infra, Dedicated are always-on with private Postgres; sizes S/M/L (Serverless 1-4 vCPU / 2-9 GiB); LangSmith Deployment requires Plus plan or above.
- Agent Server API surface: assistants (+versions/schemas/subgraphs), threads (+state/history/copy/prune/commands), thread runs (create/stream/wait/join/cancel), stateless runs (/runs, /runs/batch), crons (/runs/crons), store, MCP endpoint (/mcp exposes each agent as an MCP tool), A2A (/a2a/{assistant_id}), system (/ok,/info,/metrics,/docs,/openapi.json); auth via X-Api-Key or custom auth.
- Custom end-user auth = langgraph_sdk.Auth referenced from langgraph.json ('auth.path'); @auth.authenticate returns identity + custom fields exposed as config.configurable.langgraph_auth_user; @auth.on handlers add owner-based resource filters; MDA's identity feature auto-generates this handler.
- Client SDKs: langgraph-sdk 0.4.2 (Python) and @langchain/langgraph-sdk 1.9.27 (JS) with get_client/Client and RemoteGraph; the React useStream hook now lives in @langchain/react 1.0.28 (plus @langchain/vue, @langchain/svelte, @langchain/angular injectStream) with deep-agents projections: stream.messages, stream.values (todos), stream.subagents, interrupts, tool-call state.
- Run semantics: double-texting strategies enqueue (default)/reject/interrupt/rollback via multitask_strategy; stream modes values/updates/messages-tuple/custom/debug/events; webhook param on run-create endpoints; Cloud enforces a non-configurable 1-hour API connection timeout (BG_JOB_TIMEOUT_SECS extends background execution); max 1 concurrent run per thread; N_JOBS_PER_WORKER default 10.
- Agent Builder was renamed LangSmith Fleet (March 2026): no-code agents built on Deep Agents running on Agent Server, callable via LangGraph SDK with a PAT + 'X-Auth-Scheme: langsmith-api-key', and exportable to MIT-licensed Deep Agents code via fleet-deepagents-export.
- LangSmith Sandboxes are GA in all four SaaS regions with snapshots, service URLs, auth proxy, S3/GCS/Git mounts, fractional vCPU with 2x burst, and memory-preserving stop/start — installed via pip 'langsmith[sandbox]' (SandboxClient) and used by Deep Agents through the LangSmithSandbox backend.

## OPEN QUESTIONS
- Exact shape of the gated Managed Deep Agents runtime API (/v1/deepagents/*) — the blog describes 'durable threads, streaming runs, checkpointing, HITL via /v1/deepagents API' and deepagents-cli 0.2.0 targets it, but docs removed all API-driven creation/update/invocation examples during private beta; per-endpoint schemas are unverifiable without beta API docs.
- Whether a deployed MDA agent's standard Agent Server endpoints (threads/runs/stream) are officially supported for external clients during beta, or only the identity/guest and connector capability routes — docs say programmatic invocation is 'not yet documented', while identity docs show langgraph_sdk clients hitting the deployment URL directly.
- Concrete LCU/LSU dollar rates and Serverless scale-to-zero inactivity window (pricing page has a calculator; rates not embedded in docs; window explicitly 'may change').
- Where the managed-deepagents package source lives (langchain-ai/deepagents repo has libs/cli for deepagents-cli; GitHub access from this session was restricted so I could not enumerate the repo tree to confirm whether managed-deepagents is open-sourced or closed).
- MDA rate limits/quotas per key/workspace/agent (explicitly unpublished during private beta).
- Whether MDA supports response streaming details / useStream against MDA deployments is documented anywhere beyond generic Agent Server behavior (not found in the MDA doc set).
- Fleet self-hosted production readiness (marked beta, 'contact sales').

## SOURCES
- Managed Deep Agents overview (private beta) — https://docs.langchain.com/langsmith/managed-deep-agents-overview
- How Managed Deep Agents work — https://docs.langchain.com/langsmith/managed-deep-agents-how-it-works
- Managed Deep Agents CLI reference (mda) — https://docs.langchain.com/langsmith/managed-deep-agents-cli
- Managed Deep Agents quickstart — https://docs.langchain.com/langsmith/managed-deep-agents-quickstart
- Deploy a Managed Deep Agent — https://docs.langchain.com/langsmith/managed-deep-agents-deploy
- Add identity to Managed Deep Agents — https://docs.langchain.com/langsmith/managed-deep-agents-identity
- Managed Deep Agents schedules — https://docs.langchain.com/langsmith/managed-deep-agents-schedules
- Managed Deep Agents connectors (MCP + LangSmith capabilities) — https://docs.langchain.com/langsmith/managed-deep-agents-connectors
- Blog: Managed Deep Agents — the fastest way to ship a production deep agent (May 13, 2026) — https://www.langchain.com/blog/introducing-managed-deep-agents
- LangSmith Deployment overview — https://docs.langchain.com/langsmith/deployment
- Agent Server concepts + architecture — https://docs.langchain.com/langsmith/agent-server
- Agent Server API reference (endpoint groups) — https://docs.langchain.com/langsmith/server-api-ref
- LangGraph CLI + langgraph.json reference (incl. langgraph deploy) — https://docs.langchain.com/langsmith/cli
- Application structure (langgraph.json) — https://docs.langchain.com/langsmith/application-structure
- Custom authentication (langgraph_sdk.Auth) — https://docs.langchain.com/langsmith/custom-auth
- Double-texting strategies — https://docs.langchain.com/langsmith/double-texting
- Cloud platform features (Serverless/Dedicated, sizes, autoscaling) — https://docs.langchain.com/langsmith/cloud-platform-features
- LangSmith Deployment billing (LCU/LSU, Oct 1 2026 transition) — https://docs.langchain.com/langsmith/billing
- Self-host standalone Agent Server — https://docs.langchain.com/langsmith/deploy-standalone-server
- LangSmith Sandboxes — https://docs.langchain.com/langsmith/sandboxes
- Use RemoteGraph — https://docs.langchain.com/langsmith/use-remote-graph
- Frontend overview — useStream in @langchain/react — https://docs.langchain.com/oss/javascript/langchain/frontend/overview
- Deep Agents frontend (useStream subagent projections) — https://docs.langchain.com/oss/javascript/deepagents/frontend/overview
- LangSmith Fleet (Agent Builder rename) — https://docs.langchain.com/langsmith/fleet/index
- Use Fleet agents in code — https://docs.langchain.com/langsmith/fleet/code
- Control Plane API reference — https://docs.langchain.com/langsmith/api-ref-control-plane
- Agent Server changelog (v0.11, release cadence) — https://docs.langchain.com/langsmith/agent-server-changelog
- managed-deepagents on PyPI — https://pypi.org/project/managed-deepagents/
- managed-deepagents on npm — https://www.npmjs.com/package/managed-deepagents
- langgraph-api on PyPI (Elastic-2.0 license) — https://pypi.org/project/langgraph-api/
- deepagents CLI CHANGELOG (v0.2.0 Managed API migration) — https://github.com/langchain-ai/deepagents/blob/main/libs/cli/CHANGELOG.md
- Interrupt 26: Introducing Managed Deep Agents (YouTube) — https://www.youtube.com/watch?v=LdQpoK2TzSo
- March 2026 LangChain newsletter (Fleet rename) — https://www.langchain.com/blog/march-2026-langchain-newsletter
