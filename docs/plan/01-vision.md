# 01 · Vision & v1 scope

*Deep Work planning docs · 2026-07-21*

## The problem

Every major lab now ships an "agent that does your work" product — OpenAI's unified ChatGPT app with Codex and Work modes, Anthropic's Claude Code / Cowork, Google's Jules, GitHub's Copilot coding agent. They share a product shape: a **task inbox**, sandboxed **environments**, **live steering**, **approvals**, **diff/PR review**, **schedules**, and **mobile reach**.

The LangChain ecosystem has every ingredient for this — the `deepagents` harness, Managed Deep Agents, LangSmith Deployment, Sandboxes, Context Hub, Fleet, tracing — but **no open-source product experience on top**. What exists today:

- **LangSmith Fleet** — the product experience, but proprietary and no-code-first.
- **open-swe** — the agent framework (deepagents-composed, mention-driven), with a functional dashboard but no inbox/fleet/mobile product surface.
- **dcode** — terminal only.
- **agent-chat-ui / agent-inbox** — single-purpose reference UIs; the richer `deep-agents-ui` was archived June 2026 with no successor.

Deep Work fills that slot: **the open-source, ecosystem-native product layer**.

## Product definition

> **Sign in with your LangSmith org. Get a Codex/Cowork-grade workspace over your own agents — web, desktop, and mobile — including a Fleet-like managed-agents experience. Everything runs in your org: your runtimes, your traces, your memory, your sandboxes.**

Deep Work is a *wrapper over the LangChain platform*, not a platform of its own. This is deliberate:

1. **It's the strongest open-source contribution shape.** Deep Work drives usage of LangChain's platform rather than competing with it, and is structured so LangChain could adopt it wholesale as a product.
2. **It keeps the trust story simple.** Deep Work stores essentially nothing; the user's LangSmith org is the source of truth for agents, threads, traces, memory, and execution.
3. **It exploits a real convergence.** Fleet agents, Managed Deep Agents, LangSmith Deployments, `langgraph dev`, and a self-hosted protocol server all expose the same Assistants/Threads/Runs API and Agent Streaming Protocol — so one client covers every rung of the runtime ladder.

## Personas

| Persona | Story |
|---|---|
| **Solo builder** (v1 primary) | Has a LangSmith account (free Developer tier works for dev). Signs in, deploys the Deep Work agent to their org (`mda deploy` or one-click), dispatches tasks from any device. |
| **Team on LangSmith** (v1 secondary) | An admin deploys Deep Work agents into the org; teammates use Deep Work with per-user identity (MDA identity providers / SSO). Shared inbox and fleet visibility. |
| **Fleet user** | Already builds agents in Fleet. Points Deep Work at them (public invoke API) for a better task/inbox/mobile experience than smith.langchain.com offers. |
| **Self-hoster** (post-v1) | No LangSmith account. Runs the pure-OSS backend tier (custom protocol server + Postgres checkpointer + local/BYO sandboxes). Reduced features, clearly labeled. |

## Product pillars

1. **The task loop** — dispatch → watch (streamed narration, tool calls, sub-agents, todos) → steer mid-run → review (files, diffs, artifacts, trace) → land (draft PR, document, report). Optimized for *cheap verification*: plans up front, todo progress, diffs, and trace links everywhere — industry data shows trust in unverified agent output is collapsing (29% trust, 66% cite "almost right" as the top frustration), so verification UX is the product.
2. **The approvals surface** — a cross-agent inbox of everything agents are waiting on (HITL interrupts: approve / edit / reject / respond), one tap from a push notification. Fleet's centralized approvals inbox is its headline differentiator; Deep Work matches it in the open.
3. **The fleet manager** — create, configure, and operate agents like Fleet does: instructions, tools/MCP connectors, sub-agents, skills, memory, channels (Slack), schedules, per-tool Auto/Ask. Provisioned programmatically onto your org via the control plane (`/v2/deployments`, `/v1/deepagents/*`, crons, Context Hub).

## What v1 is — and the cut line

**In v1:**

- Sign in with LangSmith (OAuth 2.1 + PKCE; device flow on desktop) with API-key fallback; org/workspace picker.
- Connect to agents on: Managed Deep Agents deployments, any LangSmith Deployment, Fleet agents (invoke/read), local `langgraph dev`.
- Task inbox (status-grouped, filterable), task detail with live streaming (messages, tool calls, sub-agent cards, todos), mid-run steering, double-texting.
- Approvals inbox on the v1 HITL contract (`decisions`: approve/edit/reject/respond), including batched interrupts.
- Coding tasks: thread-scoped LangSmith Sandbox, snapshot-based environments with `setup.sh`, GitHub App integration with zero-token-in-sandbox proxy, file browser, diff review, draft PR creation.
- Fleet manager v1: list/inspect agents across the org; create/update/deploy the Deep Work agent template via control plane; schedules (crons) CRUD; per-tool approval config.
- LangSmith trace deep links on every run; Context Hub-backed instructions/skills/memories editing (file-based, visible).
- Surfaces: responsive web app (Next.js), desktop via Tauri v2 (tray, notifications, deep links), mobile as installable PWA (push notifications via run-completion webhooks).
- Non-coding task types as first-class flows: research/report and content tasks using the same harness (no sandbox required), with artifact viewing.

**Cut from v1 (explicitly):**

- Native mobile apps (Expo) — PWA first; the architecture keeps the door open.
- Slack/Linear/Teams *channels* for task creation (open-swe and MDA `0.4.0-dev` cover Slack; Deep Work v1 consumes schedules + web/mobile entry points only).
- The pure-OSS self-hosted backend tier — designed for (transport abstraction), not shipped in v1.
- A visual agent-builder chat (Fleet's "build with AI") — v1 ships form + files-based configuration; chat-to-configure is post-v1.
- Multi-org/enterprise governance (RBAC editors, SCIM, audit UIs) — LangSmith already owns this; Deep Work respects but doesn't manage it.
- Non-GitHub git providers (GitLab was open-swe's most-requested and declined feature; same call here for v1).

## Success criteria for v1

1. A new user goes from `Sign in with LangSmith` → deployed Deep Work agent → first completed task with a draft PR in **under 15 minutes** (environment setup friction is the #1 documented pain in Codex/Claude-class products; this number is the north star).
2. The full task loop — dispatch, steer, approve, review diff, merge — is possible **from a phone**.
3. A Fleet user can point Deep Work at an existing Fleet agent and run the inbox/approvals loop without touching smith.langchain.com.
4. Every run has a one-click LangSmith trace link; every agent config is exportable as a standard deepagents project (Fleet-export-compatible format).
5. LangChain could fork this repo and ship it — code quality, conventions, and branding hygiene all support adoption.

## Non-goals

- Competing with LangSmith (tracing, evals, datasets) or Fleet's no-code builder.
- Being model-provider-opinionated: `provider:model` strings and harness profiles throughout (Anthropic, OpenAI, Gemini, NVIDIA, OpenRouter all supported by the harness).
- Owning user data: Deep Work stores auth material locally/client-side and defers everything else to the org.
