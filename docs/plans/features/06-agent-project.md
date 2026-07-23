# U6 · `packages/agent` v0 — the deepagents project

*Feature deep-dive · 2026-07-23 · Milestone M1 · Status: planning*
*Parent: [../2026-07-22-001-feat-deepwork-v1-delivery-plan.md](../2026-07-22-001-feat-deepwork-v1-delivery-plan.md) · Specs: [../../plan/02-architecture.md](../../plan/02-architecture.md) §3, [../../plan/08-deepagents-feature-map.md](../../plan/08-deepagents-feature-map.md), [../code-conventions.md](../code-conventions.md) §2*

> **Conventions:** follows LangChain Python conventions exactly ([code-conventions.md](../code-conventions.md) §2) — one of the two Python packages a LangChain contributor feels at home in. Peer to the Python backend ([07b-api-backend.md](07b-api-backend.md)): the agent is the *runtime that runs inside LangSmith*; the backend is the *glue clients call*.

---

## Goal

Build the first real, deployable Deep Work agent — a deepagents project that is a valid `mda` project root (and also classic-deployable via `langgraph.json`). It serves **three task types via assistant configs, not separate codebases**: research, writing, and a **basic coding** type. This is the runtime the whole M1 task loop dispatches against.

Guiding principle from the architecture: **compose on the harness, don't fork it.** Everything here is configuration and middleware composition over the deepagents framework — not new framework machinery.

---

## Decisions taken

### D1 — Model/provider-agnostic; LangChain platform is the default substrate

**The agent is never bound to a single model or vendor.** Per user direction:

- **Model selection uses LangChain's `provider:model` string convention** (`init_chat_model`) — model is config, chosen per assistant/task, never hardcoded in agent logic.
- **The LangChain/LangSmith platform is the default substrate** for the three infrastructure concerns:
  - **Model access** — prefer LangChain-brokered model providers as the zero-config default (the platform provides model access), so a fresh deploy works without the user pasting a raw provider key.
  - **Sandboxes** — LangSmith Sandboxes (arch §4), not a third-party sandbox vendor.
  - **Tracing** — LangSmith tracing, the ground-truth observability surface (arch §10).
- **OpenRouter is a first-class provider option** — wired alongside the harness profiles so users get breadth (one gateway, many models) without per-vendor key sprawl.
- **Harness profiles** (Anthropic / OpenAI / NVIDIA ship in deepagents) are all available; none is the forced default. `ModelFallbackMiddleware` spans providers, which this vendor-neutral posture makes natural (e.g. OpenRouter or a second provider as automatic fallback on outage).

This is the OSS-neutrality stance: Deep Work is a client over the LangChain ecosystem, agnostic to which model sits behind it. Model choice surfaces in the composer + agent-builder (first-class picker) rather than living in code.

### D2 — Minimal RubricMiddleware hook in U6; full verification in U12

U6 wires `RubricMiddleware` (harness beta, ≥0.6.5) as a **pass-through**: the rubric field is plumbed from task input into a basic critique loop so the **writing** task type is genuinely differentiated (draft → critique → revise). The full verdict schema, iteration UI, and fault-tolerance hardening land in **U12**. This keeps v0 honest (writing isn't just a single-shot completion) without front-loading the whole verification surface.

### D3 — Three task types in v0, including a **scoped** basic coding type

Per user direction, pull a coding type into M1 to dogfood the full loop sooner. Scoped deliberately so it doesn't absorb all of M2:

| Task type | Tools on | Sandbox | In v0? |
|---|---|---|---|
| **Research** | web (`fetch_url`, `http_request`), filesystem (virtual) | no | ✅ |
| **Writing** | filesystem (virtual) + RubricMiddleware critique | no | ✅ |
| **Basic coding** | filesystem + `execute` against a LangSmith Sandbox; files visible in UI | **yes (thread-scoped)** | ✅ (scoped) |

**What the basic coding type includes in U6:** a thread-scoped LangSmith Sandbox, the `execute` tool, filesystem tools operating in the sandbox, and files surfaced through the agent's connector routes so the UI Files tab is real.

**What stays in U13 (M2):** GitHub App install + zero-token proxy callback, `commit_and_open_pr` → draft PR, diff-review takeover with batched line comments, PR/CI status. The v0 coding type produces and edits files in a sandbox — it does **not** open PRs yet.

**Consequence (flagged):** a basic coding type needs LangSmith Sandbox provisioning proven working. The U4 spike currently smoke-tests with a *no-sandbox* agent — so **add a sandbox smoke to U4** (or accept U6 as the first place sandbox provisioning is validated). Tracked in Dependencies below.

---

## Agent structure (valid `mda` project root)

Per architecture §3, the runtime-agnostic layout:

```
packages/agent/
  pyproject.toml         # uv; requires-python >=3.11; groups test/lint/typing/integration; hatchling
  uv.lock
  Makefile               # test / lint / format / type targets (LangChain-style)
  py.typed               # typed-package marker
  _version.py            # __version__ (kept in sync with pyproject via pre-commit)
  agent.py               # exports `agent` from define_deep_agent(...)
  instructions.md        # system prompt → synced to Context Hub per deployment
  tools/                 # curated ~15 tool set
  middleware/            # steering queue, reliability stack, minimal rubric
  connectors/
    deepwork.py          # http(ctx) hook → /connectors/deepwork/sandbox/:threadId/tree|file
  schedules/             # (stub in U6; wired in U16)
  skills/<name>/SKILL.md # progressive-disclosure skills
  sandbox/
    __init__.py          # define_sandbox(LangSmithSandbox, scope="thread", idle_ttl=600)
    setup.sh             # environment provisioning (basic coding type)
  identity.py            # define_identity(preset=...)  — per U4 outcome
  tests/
    unit_tests/          # no network (--disable-socket), tracing env unset
    integration_tests/   # langgraph dev / real deployment
```

**The design rule that makes multi-tier work:** the agent definition is **runtime-agnostic** — no backend/store/checkpointer configured in agent code (MDA forbids it; classic tiers provision it). This is also exactly what keeps the agent **Fleet-export-compatible**.

### LangChain Python conventions (applied here)

Per [code-conventions.md](../code-conventions.md) §2 — so the package reads like a langchain partner package:
- **uv** workspace member; groups `test`/`lint`/`typing`/`test_integration`; build-backend `hatchling`; `py.typed`; `_version.py`.
- **ruff** `select = ["ALL"]` + curated ignore; `ban-relative-imports = "all"`; **pydocstyle `google`**.
- **mypy** `strict = true`, `plugins = ["pydantic.mypy"]`.
- Every module opens with `from __future__ import annotations`; `X | None` not `Optional`; `collections.abc` types; keyword-only new params; **Google docstrings** (types in signatures, not docstrings); return types everywhere.
- Tests split `tests/unit_tests/` (socket-disabled, tracing unset via `env -u`) + `tests/integration_tests/`, mirroring source layout; `--strict-markers --strict-config`.
- Security bar: no dynamic-eval / unsafe deserialization of untrusted input; no bare `except`; `msg` variable for errors.
- Per-package `Makefile`: `make test` / `lint` / `format` / `type`.

---

## Composition detail

### Model config (D1)

- `provider:model` strings via `init_chat_model`; the resolved model comes from the assistant config, defaulting to a LangChain-brokered provider.
- OpenRouter wired as a provider (OpenAI-compatible base URL pattern) so `openrouter:<model>` works.
- Harness profiles available; `ModelFallbackMiddleware` configured with a cross-provider fallback chain.
- **No vendor string hardcoded in `agent.py`** — model is always resolved from config.

### Middleware stack

Adopted from deepagents defaults + ours (arch §3):

- **Defaults:** TodoList, Skills, Filesystem, SubAgents, Summarization, prompt caching.
- **Steering:** a `check_message_queue_before_model`-style middleware — mid-run user messages injected before each model call (powers queue-vs-interrupt in U10).
- **Reliability stack (adopted wholesale):** `ModelRetryMiddleware` + `ToolRetryMiddleware` (transient errors, exponential backoff), `ToolErrorMiddleware` (recoverable failures fed back as error ToolMessages), `ModelFallbackMiddleware` (provider outage — cross-provider per D1), `ModelCallLimitMiddleware` / `ToolCallLimitMiddleware` (runaway caps, surfaced in UI). Directly addresses open-swe v1's top failure class.
- **Verification:** `RubricMiddleware` minimal hook (D2).
- **Auto-draft-PR middleware:** **stubbed off in U6** (coding type has no PR yet); activated in U13.

### Tools (curated ~15 — curation beats count)

- deepagents built-ins: `write_todos`, `ls`/`read_file`/`write_file`/`edit_file`/`delete`/`glob`/`grep`, `task`.
- `execute` (basic coding type, sandbox tiers).
- `fetch_url`, `http_request` (research).
- `commit_and_open_pr` — **present but gated off in v0** (U13 turns it on).
- MCP-loaded connector tools (via `connectors/mcp.py`; minimal in U6, expanded U15).

### Sub-agents

- Declarative `SubAgent`s for research / review specializations; the auto general-purpose subagent stays on. Subagent output is what U14's `SubagentCard` renders.

### Task-type templates (the key structural move)

The **same agent** serves all three types via **assistant configs**, not separate codebases (arch §3). Each template sets: tools enabled, sandbox on/off, rubric defaults, model default. This is what lets the composer's "agent picker + task template" (U9) map to real backend configs.

### HITL

- `interrupt_on={tool: {allowed_decisions:[...], when: predicate}}` for `execute` (configurable), `commit_and_open_pr` (when it lands), and any MCP tool the user flags.
- Filesystem `permissions` (allow/deny/interrupt, first-match-wins) guard paths — note these do **not** cover `execute`/MCP, which is exactly why per-tool Auto/Ask (`interrupt_on`) exists (configured via U15's matrix).
- These interrupts surface as v1 `HITLRequest`s consumed by U11.

### Memory & skills

- `AGENTS.md` conventions; org/user memories under `/memories/` via Context Hub (per-user memory on the MDA `0.4.0-dev` channel — feature-flagged).
- Skills follow `SKILL.md` progressive disclosure.

---

## Deployment target

Determined by the **U4 spike outcome**:

- MDA available from our code → deploy via `mda` / `/v2/deployments`, author against the chosen identity preset.
- MDA gated → classic `langgraph.json` deploy; identity via generated `langgraph_sdk.Auth`.

Either way the **agent code does not change** (runtime-agnostic rule). U6 targets `langgraph dev` for local iteration and the U4-chosen tier for the first hosted deploy.

---

## Test scenarios

- **Happy path (research):** dispatching a research task returns a completed thread with narration + source (`fetch_url`) tool cards streamed.
- **Happy path (writing):** a writing task with a rubric triggers ≥1 critique iteration (D2 minimal loop) before finishing.
- **Happy path (basic coding):** a coding task provisions a thread-scoped sandbox, runs `execute`, writes files, and the files are readable via the connector route (visible in the UI Files tab).
- **Edge case:** empty rubric field → writing task completes with no critique loop.
- **Edge case:** model provider A errors → `ModelFallbackMiddleware` fails over to provider B (D1) and the task still completes.
- **Error path:** `fetch_url` network failure → `ToolErrorMiddleware` feeds the error back as a ToolMessage; the agent narrates the failure and marks the task failed rather than crashing.
- **Edge case:** `execute` flagged for interrupt → emits a `HITLRequest` (validates the U11 contract source).
- **Runtime-agnostic:** the identical agent runs on `langgraph dev` and the hosted tier with no code change.

---

## Verification

- `langgraph dev` starts the agent without errors.
- A research task dispatched via `curl`/`useStream` returns a completed thread with content blocks.
- A basic coding task produces files visible through the connector route.
- Cross-provider fallback demonstrably works (kill provider A, task completes on B).
- `pnpm turbo test --filter=@deepwork/agent` (→ `uv`/`pytest`) exits 0.
- No hardcoded provider/model string exists in `agent.py` (grep check).

---

## Open questions / deferred

- **Which LangChain-brokered model is the zero-config default** — depends on what the platform exposes for brokered access; pick the strongest generally-available default at build time (config, trivially changed). Not blocking the structure.
- **OpenRouter key handling** — whether the OpenRouter key rides the same key-proxy pattern as LangSmith or is a separate credential; decide alongside U8 auth.
- **Per-user memory (MDA 0.4.0-dev)** — feature-flagged; only on the dev channel. Off by default in v0.
- **CodeInterpreterMiddleware (QuickJS)** — per-template for research/data work; deferred (enable when a data/research template needs it).
- **Async subagents (supervisor pattern)** — v1.x, behind a flag (arch §3); not in v0.

---

## Dependencies

- **Upstream:** U1 (workspace, Python package stub); **U4** (deployment target + — newly — sandbox smoke for the basic coding type); U5 (stream shapes the agent must emit).
- **Downstream:** U7 (`AgentSource` targets this agent), U9/U10 (dispatch + stream against it), U11 (HITL source), U12 (rubric hardening), U13 (coding surfaces turn on `commit_and_open_pr` + auto-PR middleware), U14 (subagents), U15 (connector/tool config), U16 (schedules), U17 (org memory templates).
- **Action item:** extend **U4** with a thread-scoped LangSmith Sandbox smoke test so the basic coding type (D3) rests on validated sandbox provisioning.
