# The deepagents harness

*Condensed findings (agent-researched 2026-07-21, verified against live sources). Key facts and sources only; full reports available on request.*

## KEY FACTS
- Python `deepagents` latest stable is 0.6.12 (2026-06-25) with the 0.7.0 alpha train at 0.7.0a7 (2026-07-14); JS `deepagents` latest is 1.11.1 (2026-07-17); both release roughly weekly under MIT.
- The harness is a thin opinionated layer: `create_deep_agent()` / `createDeepAgent()` assemble a middleware stack and call LangChain's `create_agent()`, which runs on the LangGraph runtime (state, checkpoints, streaming, interrupts) — no new runtime is introduced.
- Default main-agent middleware order: TodoList -> Skills (if skills=) -> Filesystem -> SubAgent -> Summarization -> PatchToolCalls -> AsyncSubAgent (if any) -> user middleware -> profile extras -> tool exclusion -> Anthropic/Bedrock/Fireworks prompt-caching -> Memory (if memory=) -> HumanInTheLoop (if interrupt_on=); user middleware with a matching `.name` replaces the default in place (>=0.7.0a3).
- Built-in tools: write_todos, ls, read_file (multimodal), write_file, edit_file, delete (0.7a1+), glob, grep, execute (sandbox backends only), task, plus async-subagent tools (start/check/update/cancel/list_async_task) and optional QuickJS `eval` with programmatic tool calling.
- Backends are pluggable via BackendProtocol: StateBackend (default, thread-scoped in LangGraph state), FilesystemBackend (local disk), LocalShellBackend (disk + unsandboxed shell), StoreBackend (cross-thread LangGraph BaseStore with namespace factories), ContextHubBackend (LangSmith Hub), CompositeBackend (path-prefix router), and SandboxBackendProtocol sandboxes.
- Sandbox providers: LangSmith (langsmith[sandbox]), AWS AgentCore, Daytona, E2B, Modal, Runloop, Vercel, NVIDIA OpenShell in Python (packages langchain-daytona/e2b/modal/runloop/vercel-sandbox); JS has @langchain/daytona, @langchain/deno, @langchain/modal, @langchain/node-vfs; both agent-in-sandbox and sandbox-as-tool patterns are supported.
- Subagents come in three forms — declarative SubAgent dicts (name/description/system_prompt + optional tools/model/middleware/interrupt_on/skills/permissions/response_format), CompiledSubAgent runnables, and AsyncSubAgent remote background tasks via Agent Protocol (graph_id/url/headers) — with an auto-added `general-purpose` subagent behind the `task` tool.
- Long-term memory = AGENTS.md files passed via memory= (always loaded into the system prompt, agent-editable via edit_file) plus skills (SKILL.md progressive disclosure per the agentskills.io spec); scope is controlled by routing /memories/ and /skills/ to StoreBackend namespaces (per-user, per-assistant, per-thread).
- Threads/persistence ride on LangGraph: thread_id in config.configurable, checkpointer required for HITL, DeepAgentState uses a DeltaChannel messages reducer to keep checkpoint growth linear; LangSmith Deployment auto-provisions checkpointer and store.
- Human-in-the-loop uses interrupt_on={tool: True|InterruptOnConfig} with decisions approve/edit/reject/respond, conditional `when` predicates, batched multi-tool interrupts, and resume via Command(resume={'decisions': [...]}); filesystem permissions (allow/deny/interrupt, first-match-wins) can auto-generate interrupts.
- Streaming has a beta typed API — agent.stream_events(input, version='v3') — with projections stream.messages/tool_calls/values/output plus Deep-Agents-specific stream.subagents (per-task handles with name/path/status and nested projections); JS mirrors it via streamEvents v3 with run.subagents and custom streamTransformers under run.extensions.
- There are two CLIs: deepagents-code 0.1.44 (`dcode`, the Claude-Code-like terminal agent with config.toml, hooks, plugins, remote-sandbox flags, ACP server) and deepagents-cli 0.2.2 (deployment tooling: init/dev/deploy to Managed Deep Agents /v1/deepagents/*).
- The Python monorepo langchain-ai/deepagents (26.6k stars) contains libs/{deepagents, code, cli, acp, evals, talon, partners{daytona,modal,quickjs,runloop,vercel}} plus 14 examples; the JS monorepo langchain-ai/deepagentsjs contains libs/{deepagents, acp, providers{daytona,deno,modal,node-vfs,quickjs}, standard-tests}.
- Model support is provider-agnostic via 'provider:model' strings (init_chat_model), with per-model HarnessProfiles (prompt suffix, excluded tools/middleware, extra middleware, general-purpose-subagent toggles) registered in code or from YAML config; built-in profiles exist for Anthropic, OpenAI Codex, and NVIDIA models.
- Production guidance points at Managed Deep Agents (LangSmith-hosted, private preview/beta) or self-hosted LangGraph deployments (langgraph.json / langgraph build), with the harness claiming built-in multi-tenancy, RBAC, and per-user sandbox scoping versus Claude Agent SDK.

## OPEN QUESTIONS
- Exact 0.7.0 stable release date (still alpha a7 as of 2026-07-14) and its final breaking-change list beyond the deprecations noted (backend factories, BackendContext removal, model=None removal slated for 1.0.0).
- Whether Python has E2B/AgentCore partner code in-tree (E2B ships as third-party langchain-e2b; AgentCore integration location not verified in libs/partners which only shows daytona/modal/quickjs/runloop/vercel).
- JS parity gaps: no data-analysis doc page and no async-subagents divergences verified in depth; JS sandbox provider coverage lacks E2B/Runloop/Vercel equivalents in the deepagentsjs repo.
- Contents of the `openwiki/` directory and the deepagents GitHub Action (`action.yml`/ACTION.md) — likely a PR/issue agent action, not inspected.
- Full deepagents-code flag list beyond those documented (cli-reference.mdx was read partially) and the complete hooks payload schemas.
- GitHub MCP tooling in this session was scoped to a single repo, so repo trees were taken via web fetch/raw files; a few directory listings (e.g., libs/evals internals, JS standard-tests) were not exhaustively enumerated.
- Talon's full channel adapter list beyond WhatsApp and its cron tool API details.
- The precise general-purpose subagent default prompt text (DEFAULT_SUBAGENT_PROMPT) and TASK_SYSTEM_PROMPT contents were not captured verbatim.

## SOURCES
- Deep Agents overview (official docs) — https://docs.langchain.com/oss/python/deepagents/overview
- Customization — default middleware stack — https://docs.langchain.com/oss/python/deepagents/customization
- Backends — https://docs.langchain.com/oss/python/deepagents/backends
- Sandboxes — https://docs.langchain.com/oss/python/deepagents/sandboxes
- Sandbox integrations index — https://docs.langchain.com/oss/python/integrations/sandboxes
- Subagents — https://docs.langchain.com/oss/python/deepagents/subagents
- Memory — https://docs.langchain.com/oss/python/deepagents/memory
- Skills — https://docs.langchain.com/oss/python/deepagents/skills
- Human-in-the-loop — https://docs.langchain.com/oss/python/deepagents/human-in-the-loop
- Event streaming (v3) — https://docs.langchain.com/oss/python/deepagents/event-streaming
- Streaming (LangGraph modes) — https://docs.langchain.com/oss/python/deepagents/streaming
- Tools & MCP — https://docs.langchain.com/oss/python/deepagents/tools
- Interpreters (QuickJS/PTC) — https://docs.langchain.com/oss/python/deepagents/interpreters
- Going to production — https://docs.langchain.com/oss/python/deepagents/going-to-production
- Comparison with Claude Agent SDK — https://docs.langchain.com/oss/python/deepagents/comparison
- Deep Agents Code overview / quickstart / CLI reference / config / hooks / remote sandboxes — https://docs.langchain.com/oss/python/deepagents/code/overview
- Frontend overview — https://docs.langchain.com/oss/python/deepagents/frontend/overview
- langchain-ai/deepagents repo (README, libs/README, libs/ARCHITECTURE.md, libs/deepagents/CHANGELOG.md, libs/talon/README.md, libs/cli/README.md) — https://github.com/langchain-ai/deepagents
- langchain-ai/deepagentsjs repo (libs/deepagents/src: agent.ts, types.ts, index.ts; libs/providers) — https://github.com/langchain-ai/deepagentsjs
- deepagents on PyPI (0.6.12 / 0.7.0a7 sdist inspected) — https://pypi.org/project/deepagents/
- deepagents on npm (1.11.1 tarball inspected) — https://www.npmjs.com/package/deepagents
- deepagents-code on PyPI — https://pypi.org/project/deepagents-code/
- deepagents-cli on PyPI — https://pypi.org/project/deepagents-cli/
- langchain-plugins (cross-tool plugin marketplace) — https://github.com/langchain-ai/langchain-plugins
