# Execution model & sandboxes

*Condensed findings (agent-researched 2026-07-21, verified against live sources). Key facts and sources only; full reports available on request.*

## KEY FACTS
- deepagents (PyPI 0.6.12, npm 1.11.1) exposes execution via pluggable backends: StateBackend (default, thread-scoped LangGraph state), FilesystemBackend(root_dir, virtual_mode=True), LocalShellBackend (adds `execute` via subprocess, no isolation), StoreBackend, ContextHubBackend, CompositeBackend (path routing), and sandbox backends which add an `execute` shell tool.
- Official sandbox backend packages: langsmith[sandbox] (LangSmithSandbox, first-party GA), langchain-daytona 0.0.7 (DaytonaSandbox), langchain-e2b 0.0.5 (E2BSandbox), langchain-modal 0.0.5 (ModalSandbox), langchain-runloop 0.0.6 (RunloopSandbox), langchain-vercel-sandbox 0.0.1 (VercelSandbox), langchain-aws+bedrock-agentcore (AgentCoreSandbox); all follow the 'sandbox as tool' pattern (agent loop outside, tool calls hit provider API).
- Managed Deep Agents (private beta, LangSmith Cloud US-only, CLI-first — no published invocation API) uses package managed-deepagents 0.3.1 and the mda CLI; the hosted runtime owns backend/store/checkpointer/memory/skills/system-prompt, and gives each thread its own sandbox configured via sandbox/__init__.py exporting define_sandbox(LangSmithSandbox, scope="thread", idle_ttl_seconds=600) with sandbox/setup.sh run once at provisioning (Codex-style env setup script).
- LangSmith Sandboxes are GA (GCP US/EU/APAC, AWS US) with SandboxClient API: create_sandbox(snapshot_id, idle_ttl_seconds default 600, delete_after_stop_seconds ~14d, proxy_config, mount_config), sb.run() streaming with CommandHandle/reconnect, sb.write/read, service URLs, TCP tunnels, snapshots from Docker images/Dockerfiles or capture_snapshot from a running sandbox; REST base /v2/sandboxes/boxes.
- The LangSmith sandbox auth proxy injects credentials into outbound requests (workspace_secret/plaintext/opaque header rules matched by host glob) and controls egress (default: HTTP/S open, all raw TCP blocked; allow_list can open host:port) — the documented GitHub pattern mints a short-lived GitHub App installation token outside the sandbox and PATCHes opaque proxy rules so `GH_TOKEN=dummy gh` and git-over-HTTPS work with zero tokens inside the sandbox.
- Open SWE (github.com/langchain-ai/open-swe) is LangChain's own OSS coding-agent reference built on create_deep_agent: GitHub App auth (GITHUB_APP_ID/GITHUB_APP_PRIVATE_KEY/GITHUB_APP_INSTALLATION_ID, RS256 JWT, POST /app/installations/{id}/access_tokens, token cache + per-repo down-scoping), webhook-driven runs (issues, @-mentions, PR events → dispatch_agent_run with stable thread ids), thread-named LangSmith sandboxes from a required snapshot (2 vCPU / ~8GB / 32GB defaults), and draft-PR creation by the agent running gh in the sandbox.
- MCP support: langchain-mcp-adapters 0.3.0 MultiServerMCPClient({name: {transport: http|sse|stdio, url|command, headers, auth: httpx.Auth}}).get_tools() feeds create_deep_agent(tools=...); Managed Deep Agents instead uses connectors/mcp.py define_mcp_servers (remote http/sse only, stdio rejected, static bearer headers, tool names prefixed server__tool); dcode auto-discovers Claude Code-compatible .mcp.json.
- Human-in-the-loop in deepagents: create_deep_agent(interrupt_on={tool: True|False|{allowed_decisions:[approve,edit,reject,respond], when: predicate}}, checkpointer=REQUIRED); interrupts surface as result.interrupts[0].value {action_requests, review_configs}, batched for multiple calls, resumed with Command(resume={decisions:[{type: approve|edit|reject|respond,...}]}); subagents can override interrupt_on.
- FilesystemPermission(operations=[read|write], paths=[glob], mode=allow|deny|interrupt) rules (deepagents>=0.5.2, interrupt mode >=0.6.8) gate only the built-in filesystem tools — they do NOT cover the sandbox execute tool, custom tools, or MCP tools, so command approval must go through interrupt_on or sandbox isolation.
- Deep Agents Code (deepagents-code 0.1.44, binary dcode) is the local-CLI fallback: local shell execution by default, remote execution via --sandbox {langsmith|agentcore|daytona|modal|runloop|vercel}, --sandbox-id reattach, --sandbox-snapshot-name, and --sandbox-setup shell script with ${VAR} expansion from local .env (e.g. git clone with x-access-token URL).
- FilesystemBackend default virtual_mode=False provides no security even with root_dir set; docs mandate virtual_mode=True and wrapping in CompositeBackend so internal agent artifacts (/large_tool_results/, /conversation_history/) stay in state rather than on disk.
- Sandbox lifecycle patterns are thread-scoped (sandbox name f"thread-{thread_id}", lookup via client.list_sandboxes(), TTL cleanup) or assistant-scoped (shared, needs snapshot resets); on LangSmith Deployment use an async graph factory receiving RunnableConfig to resolve the sandbox per run.
- Sandbox mounts (langsmith[sandbox]>=0.8.16) attach S3/GCS buckets and public-only Git repos (git_mount with branch/tag ref and refresh_interval_seconds) under /mnt/mounts; private repo access must go through the auth-proxy clone pattern instead.
- Custom execution backends implement BackendProtocol: ls/read/grep/glob/write/edit returning structured Result types with in-band errors; sandbox backends add execute; this is the extension point for adding new sandbox providers (contributing guide exists).
- Recommended v1: OSS deepagents app on LangSmith Deployment + thread-scoped LangSmithSandbox (per-project snapshot as the 'environment' image) + GitHub App token → opaque proxy rules → agent runs gh/git in sandbox and opens draft PRs, with interrupt_on-based approve/edit/reject UI; local fallback = dcode-style LocalShellBackend with user PAT; Managed Deep Agents as an optional hosted target once its API leaves CLI-first beta.

## OPEN QUESTIONS
- Managed Deep Agents beta: exact invocation API (threads/runs endpoints) is deliberately undocumented during private beta — programmatic access requires contacting the LangChain beta team; unknown whether the managed per-thread sandbox's proxy_config can be patched at runtime (needed for the GitHub App opaque-rule pattern) or whether only sandbox/setup.sh customization is allowed.
- LangSmith Sandbox hard resource limits/pricing (max vCPUs, memory, concurrent sandboxes per workspace, per-minute cost) are not published in the docs pages read; Open SWE's env defaults (2 vCPU, ~8GB, 32GB fs) imply configurable create-time fields but ceilings unknown.
- Could not read Open SWE's dispatch.py/server.py to confirm the exact LangGraph SDK calls (client.runs.create vs streams) used by dispatch_agent_run, nor the ui/ auth flow details (GitHub OAuth app vs App user-auth) — repo access was partially blocked (api.github.com 403 via proxy; individual raw files and web tree pages fetched fine).
- Whether npm deepagents 1.x (JS) ships the full set of sandbox backend classes (LangSmithSandbox etc. are shown importable from "deepagents" in managed-deepagents TS examples) or whether some providers are Python-only.
- The docs changelog pages for deepagents were stub/empty in the docs MCP mirror, so the precise feature-to-version mapping beyond the noted gates (permissions>=0.5.2, interrupt mode>=0.6.8, Runtime arg>=0.5.2, conditional interrupts langchain>=1.3.3) is unverified.
- NVIDIA OpenShell sandbox integration package name and API were not read in detail (listed in the integrations index only).

## SOURCES
- Deep Agents — Backends (docs.langchain.com) — https://docs.langchain.com/oss/python/deepagents/backends
- Deep Agents — Sandboxes — https://docs.langchain.com/oss/python/deepagents/sandboxes
- Deep Agents — Sandbox integrations index — https://docs.langchain.com/oss/python/integrations/sandboxes
- Deep Agents — Human-in-the-loop — https://docs.langchain.com/oss/python/deepagents/human-in-the-loop
- Deep Agents — Permissions — https://docs.langchain.com/oss/python/deepagents/permissions
- Deep Agents — Tools (MCP section) — https://docs.langchain.com/oss/python/deepagents/tools
- Deep Agents — Interpreters — https://docs.langchain.com/oss/python/deepagents/interpreters
- Deep Agents Code — Use remote sandboxes — https://docs.langchain.com/oss/python/deepagents/code/remote-sandboxes
- Deep Agents Code — MCP tools (.mcp.json) — https://docs.langchain.com/oss/python/deepagents/code/mcp-tools
- Managed Deep Agents — Overview (private beta) — https://docs.langchain.com/langsmith/managed-deep-agents-overview
- Managed Deep Agents — How it works — https://docs.langchain.com/langsmith/managed-deep-agents-how-it-works
- Managed Deep Agents — Deploy (Configure a sandbox, secrets) — https://docs.langchain.com/langsmith/managed-deep-agents-deploy
- Managed Deep Agents — CLI reference (project file + agent definition reference) — https://docs.langchain.com/langsmith/managed-deep-agents-cli
- Managed Deep Agents — MCP connectors — https://docs.langchain.com/langsmith/managed-deep-agents-connectors/mcp
- LangSmith Sandboxes — Overview — https://docs.langchain.com/langsmith/sandboxes
- LangSmith Sandboxes — SDK usage — https://docs.langchain.com/langsmith/sandbox-sdk
- LangSmith Sandboxes — Auth proxy (GitHub example, egress control) — https://docs.langchain.com/langsmith/sandbox-auth-proxy
- LangSmith Sandboxes — Mounts (S3/GCS/git) — https://docs.langchain.com/langsmith/sandbox-mounts
- LangSmith Sandboxes — Snapshots — https://docs.langchain.com/langsmith/sandbox-snapshots
- LangChain docs — MCP adapters (auth, interceptors) — https://docs.langchain.com/oss/python/langchain/mcp
- Open SWE — README (langchain-ai/open-swe) — https://github.com/langchain-ai/open-swe
- Open SWE — agent/integrations/langsmith.py (sandbox provider + proxy patch) — https://github.com/langchain-ai/open-swe/blob/main/agent/integrations/langsmith.py
- Open SWE — agent/webhooks/github.py (webhook-driven runs) — https://github.com/langchain-ai/open-swe/blob/main/agent/webhooks/github.py
- Open SWE — agent/utils/github_app.py (GitHub App installation tokens) — https://github.com/langchain-ai/open-swe/blob/main/agent/utils/github_app.py
- PyPI — deepagents — https://pypi.org/project/deepagents/
- PyPI — deepagents-code — https://pypi.org/project/deepagents-code/
- PyPI — managed-deepagents — https://pypi.org/project/managed-deepagents/
- PyPI — langchain-mcp-adapters — https://pypi.org/project/langchain-mcp-adapters/
