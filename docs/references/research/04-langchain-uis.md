# LangChain first-party agent frontends

*Condensed findings (agent-researched 2026-07-21, verified against live sources). Key facts and sources only; full reports available on request.*

## KEY FACTS
- deep-agents-ui was ARCHIVED on Jun 28, 2026 (last commit 2026-05-14) with no named successor; open-agent-platform was deprecated 2026-02-25 in favor of Agent Builder, which has since been renamed LangSmith Fleet (hosted, closed-source, smith.langchain.com/agents).
- agent-chat-ui is the only actively maintained LangChain OSS chat frontend (last commit 2026-07-15): Next.js ^15.5.18, React 19, Tailwind v4 (@import "tailwindcss", oklch shadcn CSS vars), @langchain/langgraph-sdk ^1.8.10 v0 useStream, framer-motion, nuqs, sonner; scaffold via npx create-agent-chat-app (v0.1.6); demo at agentchat.vercel.app.
- The recommended modern foundation is the v1 frontend SDK @langchain/react (latest 1.0.28, wraps @langchain/langgraph-sdk 1.9.27): exports StreamProvider, useStream/useStreamContext, selector hooks useMessages/useToolCalls/useValues, stream.subagents (Map of SubagentDiscoverySnapshot), AssembledToolCall {name,callId,id,namespace,input/args,output,status:running|finished|error,error}, stream.disconnect() for join/rejoin, headless-tool helpers, and useSubmissionQueue; sibling packages @langchain/vue, @langchain/svelte, @langchain/angular (injectStream).
- Subagent rendering in v1: SubagentDiscoverySnapshot {id = task tool-call id, name, namespace, status running|complete|error, taskInput, output} carries no messages; useMessages(stream, snapshot)/useToolCalls(stream, snapshot) lazily subscribe to that subagent's namespace — demonstrated in deployment-cookbook js-langsmith (Vite 8 + React 19 + @langchain/react ^1.0.26 + deepagents JS).
- deep-agents-ui (Next 16, Tailwind v3.4 + radix-colors, shadcn baseColor slate) renders deepagents harness state directly from useStream values: todos (pending/in_progress/completed) and files (Record<string,string>), with FileViewDialog (Prism highlight + edit + save via client.threads.updateState(threadId,{values:{files}})) and subagent cards derived from 'task' tool calls with args.subagent_type.
- HITL interrupt schema across the stack: interrupt.value = {action_requests:[{name,args,description?}], review_configs:[{action_name/actionName, allowed_decisions/allowedDecisions}]}; resume via stream.submit(null,{command:{resume:{decisions:[{type:approve|reject|edit|respond,...}]}}}); agent-chat-ui validates snake_case (isAgentInboxInterruptSchema), deep-agents-ui uses camelCase — v1 docs standardize camelCase HITLRequest with decisions approve/reject/edit/respond.
- Connection env vars: agent-chat-ui uses NEXT_PUBLIC_API_URL, NEXT_PUBLIC_ASSISTANT_ID (default 'agent'), NEXT_PUBLIC_AUTH_SCHEME (langsmith-api-key for Fleet/Agent Builder deployments), plus production proxy LANGGRAPH_API_URL + LANGSMITH_API_KEY consumed by langgraph-nextjs-api-passthrough in app/api/[..._path]/route.ts (initApiPassthrough, runtime edge); deep-agents-ui instead stores {deploymentUrl, assistantId, langsmithApiKey} in localStorage['deep-agent-config'] and sends X-Api-Key directly from the browser.
- Assistant resolution convention: if assistantId is a UUID, call client.assistants.get / search threads by metadata.assistant_id; if it is a graph name, search assistants by graphId picking metadata.created_by==='system', and search threads by metadata.graph_id.
- Thread history is always client.threads.search({metadata:{assistant_id|graph_id}, limit, sortBy:'updated_at', sortOrder:'desc', status?}) with titles derived from the first human message; deep-agents-ui adds SWR-infinite pagination plus a status filter (idle/busy/interrupted/error) and interrupt-count badges.
- agent-chat-ui submits with streamMode:['values'], streamSubgraphs:true, streamResumable:true, multimodal content blocks, ensureToolCallsHaveResponses (fake 'do-not-render-' tool messages for dangling tool_calls), and supports branching/time-travel via getMessagesMetadata().firstSeenState.parent_checkpoint + setBranch; its artifact.tsx implements a portal-based right-hand artifact panel (grid-cols-[3fr_2fr]) fed by gen-UI components through LoadExternalComponent meta={{ui, artifact}}.
- Gen-UI plumbing (v0): onCustomEvent + uiMessageReducer from @langchain/langgraph-sdk/react-ui maintain values.ui; LoadExternalComponent renders server-registered components matched by metadata.message_id / tool_call_id with namespace = graphId.
- Deep-agents docs frontend patterns (/oss/javascript/deepagents/frontend/): subagent-streaming, todo-list (stream.values.todos), and sandbox — an IDE pattern exposing sandbox files via custom Hono routes in langgraph.json http.app (GET /sandbox/:threadId/tree, GET /sandbox/:threadId/file) with per-thread LangSmithSandbox resolved from thread metadata; live demos at ui-patterns.langchain.com.
- Managed Deep Agents (private beta, mda CLI) deploys to a normal hosted LangGraph deployment, so any useStream/agent-chat-ui client connects to it by deployment URL; frontend auth via identity.ts presets — trusted_backend (proxy with MDA_INGRESS_SECRET) or validated_token (Authorization: Bearer verified via JWKS/OIDC/introspection, incl. Supabase session.access_token, or MDA-signed guest tokens claimed at POST /identity/guest) — which scopes threads/memory per actor/tenant.
- OAP remains the best open reference for multi-deployment config (NEXT_PUBLIC_DEPLOYMENTS JSON array of {id, deploymentUrl, tenantId, name, isDefault, defaultGraphId}) and Supabase-auth-to-LangGraph wiring (Authorization Bearer + x-supabase-access-token headers, or /api/langgraph/proxy/{deploymentId}/* passthrough gated by NEXT_PUBLIC_USE_LANGSMITH_AUTH).
- agent-inbox (active, dev.agentinbox.ai) uses the older HumanInterrupt/HumanResponse schema {action_request:{action,args}, config:{allow_accept,allow_edit,allow_respond,allow_ignore}} — agent-chat-ui embeds its components under src/components/thread/agent-inbox/ with the newer decisions schema.
- LangSmith Fleet agents can be exported and run on OSS deepagents via the fleet-deepagents-export PyPI package (reads AGENTS.md system prompt, tools.json MCP connections, subagent definitions, skills) — a portability path between the hosted product and a self-built UI.

## OPEN QUESTIONS
- Exact reason/announcement for deep-agents-ui archival (no deprecation notice in README; inferred successor = LangSmith Fleet + @langchain/react patterns).
- Whether LangSmith 'Agent Chat' exists as a distinct embeddable product beyond Studio's Chat mode and Fleet's chat surface — docs only show Studio chat mode and Fleet; no separate 'Agent Chat' hosted app found other than agentchat.vercel.app.
- Python-side (langgraph-sdk PyPI) equivalents of the v1 frontend selector APIs were not checked (out of scope for UI).
- The @langchain/react v1 UseStreamOptions full field list (from @langchain/langgraph-sdk/stream) was not fully dumped — confirmed fields: apiUrl, apiKey, assistantId, threadId, adapter/AgentServerOptions; legacy v0 list fully captured.
- Whether Managed Deep Agents beta deployments expose the /ui gen-UI component endpoint and custom http.app routes (sandbox file APIs) identically to standard Agent Server deployments.
- deployment-cookbook js-next/js-nuxt/js-sveltekit variants were not individually diffed (assumed same chat feature set as js-langsmith per README).

## SOURCES
- langchain-ai/deep-agents-ui (archived Jun 28, 2026) — https://github.com/langchain-ai/deep-agents-ui
- langchain-ai/agent-chat-ui — https://github.com/langchain-ai/agent-chat-ui
- langchain-ai/open-agent-platform (deprecated) — https://github.com/langchain-ai/open-agent-platform
- langchain-ai/deployment-cookbook (js-langsmith Vite chat UI) — https://github.com/langchain-ai/deployment-cookbook
- langchain-ai/agent-inbox — https://github.com/langchain-ai/agent-inbox
- langchain-ai/fleet-deepagents-export — https://github.com/langchain-ai/fleet-deepagents-export
- LangChain docs — Frontend overview (v1 SDK) — https://docs.langchain.com/oss/javascript/langchain/frontend/overview
- LangChain docs — Frontend tool calling (AssembledToolCall) — https://docs.langchain.com/oss/javascript/langchain/frontend/tool-calling
- LangChain docs — Frontend human-in-the-loop (HITLRequest/decisions) — https://docs.langchain.com/oss/javascript/langchain/frontend/human-in-the-loop
- LangChain docs — Frontend join & rejoin streams — https://docs.langchain.com/oss/javascript/langchain/frontend/join-rejoin
- LangChain docs — Deep Agents frontend overview — https://docs.langchain.com/oss/javascript/deepagents/frontend/overview
- LangChain docs — Deep Agents subagent streaming — https://docs.langchain.com/oss/javascript/deepagents/frontend/subagent-streaming
- LangChain docs — Deep Agents sandbox IDE pattern — https://docs.langchain.com/oss/javascript/deepagents/frontend/sandbox
- LangChain docs — Agent Chat UI connect guide — https://docs.langchain.com/oss/javascript/langchain/ui
- LangChain docs — Deploy Vite + LangSmith (chat UI accordion) — https://docs.langchain.com/langsmith/deploy-vite-langsmith
- LangChain docs — Managed Deep Agents: how it works — https://docs.langchain.com/langsmith/managed-deep-agents-how-it-works
- LangChain docs — Managed Deep Agents: identity (ingress, guest tokens) — https://docs.langchain.com/langsmith/managed-deep-agents-identity
- LangChain docs — LangSmith Fleet (Agent Builder renamed) — https://docs.langchain.com/langsmith/fleet
- npm — @langchain/react (v1.0.28) — https://www.npmjs.com/package/@langchain/react
- npm — @langchain/langgraph-sdk (1.9.27) — https://www.npmjs.com/package/@langchain/langgraph-sdk
- npm — langgraph-nextjs-api-passthrough — https://www.npmjs.com/package/langgraph-nextjs-api-passthrough
- npm — create-agent-chat-app (0.1.6) — https://www.npmjs.com/package/create-agent-chat-app
- UI patterns live demos — https://ui-patterns.langchain.com
