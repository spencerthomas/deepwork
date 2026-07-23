# Gap-fill: MDA API surface & CLI duality

*Condensed findings (agent-researched 2026-07-21, verified against live sources). Key facts and sources only; full reports available on request.*

## KEY FACTS
- deepagents-cli 0.2.2's api_client.py fully specifies the /v1/deepagents/* control-plane REST surface (agents CRUD + health, mcp-servers CRUD + /mcp/tools + oauth-provider + auth-sessions, Hub directory get/commit) at https://api.smith.langchain.com with X-Api-Key auth — but it contains NO thread/run/invoke endpoints; that part of the API is design-partner-gated during beta.
- The mda CLI (managed-deepagents 0.3.1 stable / 0.4.0.dev72, Rust binary, runtime version 0.0.15 built 2026-07-18) deploys via the standard LangSmith control plane: POST /v2/deployments (source=internal_source, langgraph_config_path, secrets[], plus an undocumented managed_deep_agent marker), POST /v2/deployments/{id}/upload-url -> signed GCS PUT (200 MB cap), /revisions polling, and reconciles schedules by calling POST /runs/crons(/search) on the deployment's own Agent Server API.
- CLI duality verdict: deepagents-cli (config-first, /v1/deepagents, last release 2026-06-07) and mda (code-first, /v2/deployments, actively released through 2026-07-18) are separate layers; docs say verbatim 'Do not use older deepagents mcp-servers ... examples for Managed Deep Agents projects' — mda is the canonical MDA deploy path as of July 2026.
- A deployed MDA agent IS a standard hosted LangGraph Agent Server: mda generates langgraph.json with graphs, a langgraph_sdk.Auth custom-auth module (_mda_auth), an http.app module (_mda_http), and configurable_headers allowlisting x-mda-actor-id/x-mda-tenant-id; the full assistants/threads/runs/crons/store/MCP(/mcp)/A2A(/a2a/{assistant_id}) API plus stream_resumable, Last-Event-ID resume, multitask_strategy (enqueue default), webhook, if_not_exists, on_disconnect params are available at the deployment URL.
- Direct external client access is OFFICIALLY documented for beta users: the MDA identity docs show langgraph_sdk get_client(url=deployment_url, headers={Authorization: Bearer <token>}) and POST {deploymentUrl}/connectors/langsmith/capabilities/{id}; auth is either trusted_backend (X-MDA-Ingress-Secret + X-MDA-Actor-Id [+ X-MDA-Tenant-Id]) or validated_token (Bearer JWT via JWKS/OIDC/introspection, or HS256 guest tokens from public POST /identity/guest signed with MDA_GUEST_SIGNING_KEY).
- Custom client-facing HTTP routes on the deployment ARE supported via the connector protocol: any module under connectors/ exporting a branded connector with an http(ctx) hook mounts identity-enforced routes under /connectors/{kind}/... (secure by default, ctx.router.public.* opt-out) — the sanctioned home for Deep Work's sandbox file-browser endpoints; raw http.app/custom langgraph.json routes and the gen-UI /ui endpoint are NOT author-controllable on MDA.
- Sandbox proxy_config answer: define_sandbox passes all non-managed kwargs verbatim into langsmith SandboxClient.create_sandbox (TS types: 'MDA invents no schema'), so static proxy_config incl. access_control and callbacks is author-configurable; runtime patching is also possible via the documented PATCH /v2/sandboxes/boxes/{name} opaque-rule pattern (Open SWE GitHub App flow), but the MDA sandbox name is runtime-generated, so the proxy_config 'callbacks' mechanism (proxy POSTs {host,port} to your endpoint, you return {headers}, ttl 60-3600s, fail-closed 502) is the cleanest zero-secret GitHub-token design for per-thread sandboxes.
- No MDA-specific rate limits are published during private beta ('contact your LangChain team'); applicable platform limits: LangSmith gateway rate-limit table (e.g. 2000/10s general, 15/10s POST /runs/query), 200 MB deploy tarball cap, sandbox callback TTL 60-3600s, sandbox idle_ttl default 600s, autoscaling is automatic on Cloud deployments.
- MDA ingress auth internals (from _identity_auth.py): MDA_INGRESS_SECRET compared constant-time against x-mda-ingress-secret; public bypass routes are POST /identity/guest, GET /identity/{provider}/callback, and POST /channels/{name}/events (Slack-signature verified); thread scoping stamps metadata.owner (actor|tenant|channel) and store access fails closed 403 outside the identity namespace; mda dev sets MDA_LOCAL_DEV=1 with synthetic actor mda:local-dev.
- The 0.4.0.dev line adds Slack channels (define_slack_channel, POST /channels/{name}/events, Connect-with-Slack account linking under /identity/slack/*, schedule deliver_to destinations) and per-actor/tenant Context Hub user-memory repos (/memories/user/AGENTS.md) — none of which exist in stable 0.3.1, so Deep Work should target the dev channel.
- define_schedule requires 5-field cron + exactly one of prompt|input, with thread mode ephemeral (default) or persistent {id}, optional timezone and deliver_to {channel, to: provider_thread|provider_conversation, auto_post}; mda deploy deletes and recreates MDA-owned crons on the Agent Server after the revision reaches DEPLOYED (skipped with --no-wait).
- mda deploy auth key order is LANGGRAPH_HOST_API_KEY -> LANGSMITH_API_KEY -> LANGCHAIN_API_KEY (.env before shell env), org-scoped keys need LANGSMITH_TENANT_ID/--tenant-id, host backend is https://api.host.langchain.com with fallback checks against https://api.smith.langchain.com, and reserved platform vars are never forwarded as deployment secrets.
- MDA runtime seam: authored tools/middleware receive ManagedDeepAgentRuntime with identity ({actor{type,id,email}, tenant?, source{provider: http|slack|schedule|cli|studio, threadId?}, claims?}), channel, and credentials (custom mode: runtime.credentials.for_(CredentialTarget{kind: subagent|mcp|connection|langsmith}) via in-process resolver or MDA_TOKEN_EXCHANGE_SECRET-signed token-exchange endpoint).
- Managed sandboxes are resolved lazily per scope key (thread:{thread_id} default, or agent:{assistant_id}), cached in-process, provisioned once by uploading sandbox/setup.sh to /tmp/mda-setup.sh; the resolved LangSmithSandbox backend exposes execute/ls/read/grep/glob/write/edit/delete/uploadFiles/downloadFiles and id (= the LangSmith sandbox name usable with the /v2/sandboxes REST API).
- The LangSmith sandbox platform additionally offers service URLs (sb.service(port) -> shareable browser_url for web-app previews), TCP tunnels, snapshots, Git/S3/GCS mounts, preserve_memory_on_stop, and fractional vCPU — all usable from Deep Work's backend with the workspace API key.

## OPEN QUESTIONS
- The exact shape of the design-partner /v1/deepagents run/thread/invoke endpoints (the May 2026 blog says they exist; no published client code or docs reveal paths/payloads — only agents/mcp-servers/auth-sessions/health/Hub-directory are recoverable).
- Whether the `managed_deep_agent` key observed in the mda binary's /v2/deployments payload is a boolean flag, an object, or a deployment_type enum value (binary strings interleave keys; public deployments-v2 docs do not list it).
- Whether MDA deployments enable the /mcp and /a2a endpoints by default or require env flags (they are standard Agent Server features and nothing in the generated langgraph.json disables them, but no MDA doc explicitly confirms).
- Whether langsmith SandboxClient.create_sandbox in the Python SDK version pinned by the MDA runtime accepts proxy_config verbatim (confirmed in docs SDK examples and TS type contract; did not disassemble the pinned python langsmith wheel).
- How author code is meant to discover the MDA-generated per-thread sandbox name for the PATCH-based proxy pattern (only the private in-process cache or backend.id expose it; no public runtime API), reinforcing the callback-based design.
- Actual per-workspace MDA beta quotas (deployments per workspace, concurrent sandboxes, cron count) — explicitly unpublished; must come from the beta contact.
- Whether the /ui gen-UI endpoint could be enabled on MDA by a future langgraph.json 'ui' passthrough (agent.tsx is currently only an entry-point extension, no ui key emitted).

## SOURCES
- Managed Deep Agents overview (docs) — https://docs.langchain.com/langsmith/managed-deep-agents-overview
- How Managed Deep Agents work (docs) — https://docs.langchain.com/langsmith/managed-deep-agents-how-it-works
- Managed Deep Agents CLI reference (docs) — https://docs.langchain.com/langsmith/managed-deep-agents-cli
- Add identity to Managed Deep Agents (docs) — https://docs.langchain.com/langsmith/managed-deep-agents-identity
- Deploy an agent — Managed Deep Agents (docs) — https://docs.langchain.com/langsmith/managed-deep-agents-deploy
- Connectors index — Managed Deep Agents (docs) — https://docs.langchain.com/langsmith/managed-deep-agents-connectors
- LangSmith connector capabilities (docs) — https://docs.langchain.com/langsmith/managed-deep-agents-connectors/langsmith
- Schedules — Managed Deep Agents (docs) — https://docs.langchain.com/langsmith/managed-deep-agents-schedules
- Sandbox auth proxy (docs) — https://docs.langchain.com/langsmith/sandbox-auth-proxy
- Sandbox SDK (docs) — https://docs.langchain.com/langsmith/sandbox-sdk
- Sandbox service URLs (docs) — https://docs.langchain.com/langsmith/sandbox-service-urls
- Create Deployment — Control Plane API v2 (docs) — https://docs.langchain.com/langsmith/api-ref-control-plane
- Agent Server API reference (docs) — https://docs.langchain.com/langsmith/server-api-ref
- A2A endpoint in Agent Server (docs) — https://docs.langchain.com/langsmith/server-a2a
- MCP endpoint in Agent Server (docs) — https://docs.langchain.com/langsmith/server-mcp
- Double texting (docs) — https://docs.langchain.com/langsmith/double-texting
- Streaming (docs) — https://docs.langchain.com/langsmith/streaming
- Cloud architecture and rate limits (docs) — https://docs.langchain.com/langsmith/cloud
- LangSmith changelog (docs) — https://docs.langchain.com/langsmith/changelog
- Blog: Managed Deep Agents — the fastest way to ship a production deep agent — https://www.langchain.com/blog/introducing-managed-deep-agents
- managed-deepagents on PyPI — https://pypi.org/project/managed-deepagents/
- deepagents-cli on PyPI — https://pypi.org/project/deepagents-cli/
- deepagents-cli README (libs/cli, langchain-ai/deepagents) — https://github.com/langchain-ai/deepagents/blob/main/libs/cli/README.md
- deepagents-cli CHANGELOG (libs/cli, langchain-ai/deepagents) — https://github.com/langchain-ai/deepagents/blob/main/libs/cli/CHANGELOG.md
- managed-deepagents-sdk (repo homepage, per package metadata) — https://github.com/langchain-ai/managed-deepagents-sdk
- managed-deepagents on npm — https://www.npmjs.com/package/managed-deepagents
