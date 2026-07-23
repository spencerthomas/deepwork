# 08 · deepagents feature map

*Deep Work planning docs · 2026-07-22. deepagents is the core of this project — everything else flows from it. This map covers **every** feature set in the deepagents docs (including beta/preview items) and states exactly how Deep Work uses it, or why not. Verified against docs.langchain.com on this date. Python `deepagents` 0.6.x (0.7 alpha train) unless noted.*

Legend: ✅ = in v1 plan · 🔜 = planned post-v1 (flagged/experimental first) · 🧭 = consciously not used, reason given.

## Get started

| Feature | Use in Deep Work | Where |
|---|---|---|
| **Overview / Quickstart / Customization** | ✅ `create_deep_agent` composition is the whole of `packages/agent` — defaults + middleware overrides-by-`.name` (≥0.7.0a3), no forked harness. | [02 §3](02-architecture.md) |
| **Models** | ✅ `provider:model` strings via `init_chat_model`; per-task-template model defaults; user-selectable in task composer and agent config. | 02 §3 |
| **Comparison (vs Claude Agent SDK)** | ✅ Source for positioning copy: built-in multi-tenancy, RBAC, per-user sandbox scoping are the harness's claimed edges — Deep Work's UI makes them visible. | [01](01-vision.md) |
| **Deep Agents Code (`dcode`)** | ✅ The local companion CLI: sandbox-id handoff, shared AGENTS.md/skills, plugins; its goals UX is the reference for ours. | 02 §9, [research 14](../research/14-dcode.md) |
| **Changelog** | ✅ Watched in CI (renovate groups `@langchain/*`/deepagents; canary deployment tracks the 0.7 alpha / MDA dev channel). | [05](05-oss-setup.md) |

## Deployment

| Feature | Use in Deep Work | Where |
|---|---|---|
| **Managed Deep Agents** (beta) | ✅ Primary runtime target; `packages/agent` stays a valid `mda` project. | 02 §2, research 20 |
| **Going to production** | ✅ Classic `langgraph.json` deployment is the public fallback tier. | 02 §2 |
| **Fault tolerance** | ✅ **Adopted wholesale as the agent's reliability stack** — `ModelRetryMiddleware` + `ToolRetryMiddleware` (transient, exponential backoff), `ToolErrorMiddleware` (LLM-recoverable → error ToolMessage), `ModelFallbackMiddleware` (provider outage), `ModelCallLimitMiddleware`/`ToolCallLimitMiddleware` (runaway caps), HITL for user-fixable. This is the direct answer to open-swe v1's top failure mode (fallback exhaustion, provider fragility). Limit-hit and fallback events surface in the task detail rail. | 02 §3 (middleware) |

## Execution environment

| Feature | Use in Deep Work | Where |
|---|---|---|
| **Tools** | ✅ Built-ins + ~15 curated task tools; custom tools return structured Results. | 02 §3 |
| **Backends** | ✅ StateBackend default (non-coding tasks); CompositeBackend routing; sandbox backends per environment; ContextHub/Store for memory scopes. | 02 §3–4, [07](07-org-intelligence.md) |
| **Permissions** | ✅ `FilesystemPermission` allow/deny/interrupt rules (first-match-wins) guard paths; UI note: they do **not** cover `execute`/MCP tools — the per-tool Auto/Ask matrix compiles to `interrupt_on` for those. | 02 §3, [03 §3.4](03-ui-spec.md) |
| **Multimodality** | ✅ `read_file` returns content blocks for images/video/audio/PDF/PPT; custom tools may return media. UI: FileViewer renders media blocks, composer accepts image attachments (v0 concept already has attachments). Agent guidance encodes the documented pattern: store large media in the backend, pass paths — summarization drops media blocks from older turns, so nothing important lives only as an image in history. | 03 §4, 02 §3 |
| **Sandboxes** | ✅ Thread-scoped LangSmith Sandboxes; snapshot = environment; auth-proxy GitHub pattern. | 02 §4 |
| **Interpreters** (beta) + **Dynamic subagents** (beta) | 🔜 `CodeInterpreterMiddleware` (QuickJS) enabled **per task template**, flagged: research/data templates get PTC (loops/retries/parallel batches over selected tools without model turns) and dynamic subagents (code-driven fan-out/verification over many items). UI: interpreter executions render as a collapsed code card in the thread. Not in the default coding template (sandboxes cover it). Beta → behind a template flag until stable. | 02 §3; backlog in [04](04-roadmap.md) |
| **Event streaming** (beta) + **Streaming** | ✅ `stream_events` v3 typed projections on the server side; the client consumes the Agent Streaming Protocol via `@langchain/react` (the pinned UI contract). | 02 §7, 03 §5 |

## Context management

| Feature | Use in Deep Work | Where |
|---|---|---|
| **Skills** | ✅ agentskills.io SKILL.md progressive disclosure; org skills in Context Hub; plugins distribute them; skills browser in agent config. | 02 §3, 07 |
| **Memory** | ✅ AGENTS.md conventions; per-user/tenant/org scopes via Store/Context Hub namespaces; org memory read-only + review loop; consolidation agent. | 07 (the whole doc) |
| **Context engineering** | ✅ Compression (offloading + summarization) and isolation come free from the harness — the UI renders their artifacts honestly (summarized-history marker in thread; "context compacted" affordance). **Runtime context** (per-run config propagated to subagents) carries actor/tenant identity and connection metadata — this is the seam MDA's `runtime.identity` rides on. | 02 §3/§5, 03 §3.2 |
| **Profiles** (beta) | ✅ `HarnessProfile` per provider/model (prompt overlays, tool-description overrides, excluded tools/middleware, extra middleware, GP-subagent tuning), loadable from YAML — this is how Deep Work stays model-agnostic without per-model code paths; task templates may ship profile overlays. Built-ins for Anthropic/OpenAI/NVIDIA used as-is. | 02 §3 |

## Delegation

| Feature | Use in Deep Work | Where |
|---|---|---|
| **Subagents** (sync) | ✅ Declarative SubAgents per template + auto general-purpose; UI SubagentCards with lazy namespace subscription. | 02 §3, 03 §3.2 |
| **Async subagents** (preview) | 🔜 **The parallel-workstream mechanism**: supervisor launches background tasks via Agent Protocol (`start/check/update/cancel/list_async_task`), tracked in a dedicated `async_tasks` state channel that **survives context compaction**; ASGI transport for co-deployed graphs (same `langgraph.json`) is the recommended default. Deep Work v1 gets parallelism via separate threads/tasks (simpler, already planned); v1.x adds the **supervisor pattern** — a chat-facing agent that dispatches Deep Work worker graphs as async subagents with mid-flight steering — surfacing in the UI as linked task cards (each async task = a real thread = a real task-detail page). | 04 backlog; 02 §3 note |

## Steering

| Feature | Use in Deep Work | Where |
|---|---|---|
| **Human-in-the-loop** | ✅ `interrupt_on` + decisions contract; approvals inbox; plan approval; batched interrupts. | 02 §3/§5, 03 §3.3 |
| **Grading rubrics** (beta, ≥0.6.5) | ✅ **`RubricMiddleware` ships in the harness** — LLM-as-judge grader subagent reviews the transcript against a rubric, injects per-criterion feedback, loops until `satisfied`/`max_iterations`/`failed`. Deep Work tasks can attach a rubric at creation (composer field; templates ship defaults); the verification panel shows verdicts + iteration count; grader model configurable. dcode's `/goal` (agent-drafted criteria → human approval) layers the same machinery under a goal lifecycle — Deep Work adopts goals in v1.x using RubricMiddleware as the engine. | 02 §3/§9, 03 §3.2, 04 M2 |

## Frontend

| Feature | Use in Deep Work | Where |
|---|---|---|
| **Frontend overview + patterns** (subagent-streaming, todo-list, sandbox IDE) | ✅ The documented patterns are the UI spec's foundations — `useStream` projections, subagent cards, `values.todos`, sandbox file routes via connector/`http.app`. | 03 (throughout), research 21/22 |

## Protocols

| Feature | Use in Deep Work | Where |
|---|---|---|
| **MCP** | ✅ Connector strategy is MCP-first (`langchain-mcp-adapters` / MDA `define_mcp_servers`; remote HTTP/SSE on managed runtimes). | 02 §6, 07 §Layer 4 |
| **ACP** (`deepagents-acp`) | 🔜 Editor integrations for free: exposing the Deep Work agent over ACP puts it inside Zed/JetBrains/any ACP client with zero UI work from us. Post-v1, low effort; dcode already ships an ACP server locally. | 04 backlog |
| **A2A** (`/a2a/{assistant_id}` on Agent Server) | 🔜 Agent-to-agent interop: every deployed Deep Work agent is already an A2A server (and an MCP tool via `/mcp`) — other orgs' agents can delegate to it. Documented as an integration capability, no v1 work. | 02 §2 (API surface) |

## Use-case guides → task-template catalog

The docs' worked examples map 1:1 onto Deep Work's shipped task templates: **deep-research** → Research template; **data-analysis** → Data-analyst template (07 §Layer 4); **RAG** → knowledge-grounded variants (org memory / OKF mounts); **content-builder** → Writing template. Each template = prompt + tools + middleware set (interpreter on/off, rubric defaults, sandbox on/off) + profile overlays — configuration, not code.

## Corrections this audit produced

1. **Rubrics are a harness middleware, not a dcode-only feature** — cloud grading parity is an include, not a design task (previous docs implied otherwise; fixed in 02 §9).
2. **Async subagents** were unplanned — now the named v1.x mechanism for supervisor-driven parallel workstreams.
3. **Fault-tolerance middleware** existed as scattered notes — now the explicit reliability stack in the agent composition.
4. **Multimodal rendering** added to the FileViewer/composer specs with the store-in-backend guidance encoded in agent instructions.
