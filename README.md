# Deep Work

**The open-source workspace for agents that do real work — built natively on the LangChain platform.**

Deep Work is a Codex / Claude-Cowork-class product experience delivered as an open-source contribution to the LangChain ecosystem. Sign in with your LangSmith org and get a multi-surface (web, desktop, mobile) workspace over your own agents: dispatch tasks, watch and steer live runs, approve sensitive actions, review diffs, and manage a fleet of managed deep agents — with every run traced in LangSmith and every byte of state living in *your* org.

> **Status: planning.** This repo currently contains the v1 project plan, architecture, and UI specification. See [`docs/plan/`](docs/plan/). Implementation follows the [roadmap](docs/plan/04-roadmap.md).

## What it is

- **A wrapper over the LangChain platform.** Deep Work owns almost no backend. Agents run on LangSmith-hosted runtimes (Managed Deep Agents / Agent Server), traces land in LangSmith, memory and skills live in Context Hub, execution happens in LangSmith Sandboxes. Deep Work is the product experience on top.
- **One client, every runtime rung.** Fleet agents, Managed Deep Agents, any LangSmith Deployment, a local `langgraph dev` server, or a pure-OSS self-hosted backend — all speak the same Agent Server API and streaming protocol, so the same task inbox, steering, and approvals UX works against each.
- **Managed agents that work like Fleet — in the open.** A create/configure/schedule/approve experience for deep agents (instructions, tools, connectors, sub-agents, skills, channels, schedules, per-tool approvals), provisioned programmatically onto your org.
- **Work, not just code.** Coding tasks get sandboxes, branches, and draft PRs; the same harness runs research, writing, and ops tasks. (Anthropic's own numbers: >90% of Cowork usage is non-coding.)

## The stack

| Layer | Technology |
|---|---|
| Agent harness | [`deepagents`](https://github.com/langchain-ai/deepagents) (Python / TS) |
| Hosted runtime | Managed Deep Agents (beta) · LangSmith Deployment · Agent Server |
| Execution | LangSmith Sandboxes (thread-scoped, snapshot environments) |
| Memory / skills | Context Hub (`AGENTS.md`, `skills/`, per-user memories) |
| Observability | LangSmith tracing (every run deep-links to its trace) |
| Frontend | `@langchain/react` `useStream` · Next.js · Tailwind · shadcn/ui |
| Desktop / mobile | Tauri v2 · PWA first, Expo later |

## Documentation

| Doc | Contents |
|---|---|
| [01 — Vision & v1 scope](docs/plan/01-vision.md) | Product definition, personas, pillars, v1 cut line |
| [02 — Architecture](docs/plan/02-architecture.md) | Runtime tiers, agent design, execution, auth, platform integration |
| [03 — UI specification](docs/plan/03-ui-spec.md) | Design language, app shell, screens, components, data contracts |
| [04 — Roadmap](docs/plan/04-roadmap.md) | Milestones to v1, risks, open questions |
| [05 — OSS setup](docs/plan/05-oss-setup.md) | License, repo structure, CI, conventions |
| [06 — Frontend implementation](docs/plan/06-frontend-implementation.md) | Evaluation of the [deep-work-frontend](https://github.com/spencerthomas/deep-work-frontend) concept + phased plan to make it `apps/web` |
| [Design brief](docs/design/deepwork-design-brief.html) | Visual brief with tokens, specimens, and screen concepts |
| [Research digest](docs/research/README.md) | Condensed findings that ground every decision above |

## License & affiliation

MIT. Deep Work is an independent open-source project built on LangChain technologies. It is **not affiliated with, endorsed by, or sponsored by LangChain, Inc.** "LangChain" and "LangSmith" are registered trademarks of LangChain, Inc., used here only to describe compatibility.
