# Research: Deep Agents Code (dcode) — reviewed inline from official docs, 2026-07-22

## What it is
OSS terminal coding agent on the Deep Agents SDK (`deepagents-code` PyPI 0.1.44, `dcode` binary; install `curl -LsSf https://langch.in/dcode | bash`). Any model/provider, switchable. LangSmith tracing built-in. ACP server (Zed/JetBrains). Interactive + non-interactive (`dcode -n "task"`).

## Feature inventory (docs pages: overview, quickstart, configuration, config-file, cli-reference, approval-modes, credentials, goals-and-rubrics, hooks, mcp-tools, memory-and-skills, plugins, providers, remote-sandboxes, subagents, changelog)
- **Memory**: auto-saved topic-organized markdown in `~/.deepagents/<agent>/memories/` (memory-first protocol: research → response → learning); `AGENTS.md` global (`~/.deepagents/<agent>/AGENTS.md`) + project (`.deepagents/AGENTS.md` at git root), both appended to system prompt; extra memory files must be referenced from AGENTS.md; `/remember` to force memory/skill updates.
- **Skills**: agentskills.io SKILL.md dirs, discovered at startup by frontmatter name/description, `/reload` re-discovers. Same spec as deepagents harness + Context Hub skills.
- **Goals & rubrics** (⭐ adopt into Deep Work task model): `/goal <objective>` → agent DRAFTS acceptance criteria → inline review (accept/edit/revise/cancel) → goal persists across turns, each turn GRADED against criteria until completion approved; amend/pause/resume; `/goal model`, `/goal max-iterations`. `/rubric set|next|file` = known criteria as quality gate (sticky or one-turn); `--rubric` flag in non-interactive mode.
- **Remote sandboxes**: sandbox-as-tool pattern (LLM loop local, tool calls remote). Providers: LangSmith (default, included), AgentCore, Daytona, Modal, Runloop, Vercel (extras via `/install X`), E2B (third-party pkg). **`--sandbox-id` reattach to existing sandbox** (⭐ enables terminal attach to a Deep Work thread's LangSmith sandbox), `--sandbox-snapshot-name` (langsmith+runloop), `--sandbox-setup` script. Third-party provider protocol: `get_or_create(sandbox_id=...)`, capability flags in config.toml.
- **Plugins & marketplaces** (⭐ shared ecosystem): skills + MCP servers packaged; supports **Claude- and Codex-style plugin manifests and marketplace catalogs**; sources: gh owner/repo[@ref], https git, marketplace JSON URL, local; `/plugins` UI + `dcode plugin` CLI (`install code-review@acme-tools`, enable/disable, `--json`); namespaced skill invocation `/skill:plugin@marketplace:skill`. langchain-ai/langchain-plugins = cross-tool marketplace (dcode + Claude Code + Codex).
- **Hooks**: `~/.deepagents/hooks.json` — external commands subscribed to lifecycle events (e.g. session.start, task.complete), JSON payload on stdin, fire-and-forget background.
- **Approval modes + credentials pages** exist (per-tool approval controls; provider credential management incl. ChatGPT OAuth per openwiki research).
- Context compaction (summarize + offload originals).

## Integration into Deep Work plans (decisions)
1. **dcode IS Deep Work's local CLI — build no CLI.** The "Claude Code" to Deep Work's "web". Document `dcode` as the companion; Deep Work quickstart installs it.
2. **Cross-surface handoff**: Deep Work task detail exposes "Continue in terminal" → copyable `dcode --sandbox langsmith --sandbox-id <thread-sandbox-name>` (the sandbox name IS the LangSmith sandbox id from MDA runtime). Also project `.deepagents/AGENTS.md` conventions shared between cloud agent and dcode.
3. **Adopt goals/rubrics into the Deep Work task model**: task creation can attach a goal (agent drafts acceptance criteria → approval flow = richer plan-approval) or rubric; grading loop = cheap-verification pillar. Cloud parity via response_format/middleware in packages/agent (needs design; dcode's implementation is the reference).
4. **Plugins**: Deep Work's config "plugins" screen (already in the v0 concept!) maps to the Claude/Codex-compatible marketplace format; org marketplace = a repo; same plugins usable in dcode locally and (where remote-MCP/skills compatible) in cloud agents.
5. **Memory conventions shared**: `~/.deepagents` layout ↔ Context Hub repos: org memory sync between dcode local memories and Deep Work org memory is a v2 feature (needs mapping design; both are markdown-file-first).
6. **Hooks**: dcode hooks can notify Deep Work (POST to app) of local sessions → Activity feed sees local + cloud work (v2, optional).

## OSS-first policy reinforcement (user directive)
Consume upstream: deepagents, deepagents-code, @langchain/react, langgraph-sdk, langchain-auth, langsmith[sandbox], managed-deepagents. Build only: apps (web/desktop/mobile), packages/sdk glue, packages/agent composition, packages/ui, server routes. No forks; weekly dependency refresh; upstream issues/PRs when gaps found.
