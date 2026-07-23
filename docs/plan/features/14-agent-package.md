# F14 · `packages/agent`

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M1–M2 · Depth: implementation-ready*

Sources: [02 · Architecture](../02-architecture.md) (§3 core; §2, §4–§7, §10) · [08 · deepagents feature map](../08-deepagents-feature-map.md) · [04 · Roadmap](../04-roadmap.md) (M1/M2) · [05 · OSS setup](../05-oss-setup.md) · [research 02 · deepagents harness](../../research/02-deepagents-harness.md) · [research 10 · open-swe/Fleet](../../research/10-openswe-fleet.md) · [research 01 · MDA](../../research/01-managed-deep-agents.md) · [research 20 · MDA API gap-fill](../../research/20-gapfill-mda-api.md) · [research 21 · UI contract](../../research/21-gapfill-ui-contract.md) · [research 06 · sandboxes](../../research/06-execution-sandboxes.md) · [decisions](../decisions.md)

## 1. Scope

This spec owns the **composition** of `packages/agent`: the deepagents/`mda` project layout, the `create_deep_agent`/`define_deep_agent` assembly, the middleware stack (order + config), the curated tool set, sub-agents, `identity.py`, connector modules, schedules scaffold, sandbox config, `instructions.md`, and the package's test strategy. Python-first (D-008). Composition, not framework: we consume `deepagents` as a versioned package and never fork the harness ([02 §8](../02-architecture.md)).

Out of scope (neighbors own it): task-template catalog and per-template overlays → [F15](./15-task-templates.md) · rubric/verification config and verdict UX → [F16](./16-verification-and-rubrics.md) · stream rendering and task-detail UI → F09 ([catalog](./README.md)) · environment/snapshot lifecycle, sandbox infra, egress editor → [F11](./11-execution-and-environments.md) · GitHub App, zero-token callback route, git conventions → [F12](./12-github-and-git-flow.md) + [F28](./28-backend-glue-service.md) · auth planes and threat model → [F05](./05-auth-and-identity.md) (F14 only *ships* `identity.py`) · CI mechanics → [F01](./01-monorepo-and-oss-infra.md) · files/diff UI consuming the connector routes → F13 ([catalog](./README.md)).

Milestones: **M1** ships v0 (research + writing task types, no sandbox, deployable via `mda` and `langgraph dev`); **M2** adds the reliability stack, HITL gating, sandbox tools, `commit_and_open_pr`, and connector routes ([roadmap](../04-roadmap.md)).

## 2. Dependencies & seams

| Dependency | Version / channel | Why |
|---|---|---|
| `deepagents` (py) | exact-pin an 0.7.0 alpha, **≥0.7.0a3** (working assumption: `0.7.0a7`, open-swe v2's pin) | middleware overrides-by-`.name` need ≥0.7.0a3 ([08](../08-deepagents-feature-map.md)); `delete` tool needs 0.7a1+; `RubricMiddleware` ≥0.6.5. Conflicts with [05](../05-oss-setup.md)'s 0.6.12 pin → §9 Q1 |
| `managed-deepagents` | **0.4.0-dev channel** | per-user memory slices + channels + `deliver_to` exist only there ([research 20](../../research/20-gapfill-mda-api.md)) |
| `langsmith[sandbox]` | per [05] pins | `LangSmithSandbox` backend (M2) |
| `langchain-mcp-adapters` | ^0.3 | MCP tool loading on classic tiers ([research 06](../../research/06-execution-sandboxes.md)) |
| `langgraph-cli` | per [05] pins | `langgraph dev` for local dev + contract tests |
| uv · ruff · pytest | [05] toolchain | non-JS workspace in the pnpm monorepo, shared with `apps/server` (P-005, per [F01](./01-monorepo-and-oss-infra.md)) |

**Interim exception (pin conflict):** the scaffold exact-pins the 0.7 alpha per §9 Q1's proposal, superseding [05](../05-oss-setup.md)'s 0.6.12 pin, pending batch-1 ratification of the decision-log entry.

| Neighbor | Seam |
|---|---|
| [F15 templates](./15-task-templates.md) | Templates are **assistant configs over this one agent**, not codebases ([02 §3](../02-architecture.md)). F14 owns the config surface (`context_schema`: model, sandbox on/off, interpreter flag, rubric ref, tool exclusions, Auto/Ask matrix → `interrupt_on`); F15 owns the values. |
| [F16 verification](./16-verification-and-rubrics.md) | F14 reserves the `RubricMiddleware` slot in the stack (§3.3); grader config, rubric schema, verdict surfacing are F16's. |
| F09 (stream/task detail) | Consumes the reliability-surfacing contract (§3.3.4, §4): cap/fallback events observable on `messages`/`lifecycle` — no bespoke channels. |
| [F11 environments](./11-execution-and-environments.md) | F14 ships `sandbox/__init__.py` + default `setup.sh`; F11 owns snapshots, the environment editor, egress allow-lists. |
| [F12 GitHub](./12-github-and-git-flow.md) / [F28 glue](./28-backend-glue-service.md) | `commit_and_open_pr` + auto-PR middleware assume the zero-secret token path: sandbox auth-proxy **callback** → `apps/server` mints GitHub App tokens (P-005; [02 §4](../02-architecture.md)). |
| [F05 auth](./05-auth-and-identity.md) | F14 ships `identity.py` presets + the classic-tier `langgraph_sdk.Auth` module; F05 owns semantics, flows, threat model. |
| [F04 SDK](./04-sdk-and-agent-sources.md) | Python emits snake_case (HITL payloads, state keys); SDK normalizes (D-011). Steering-queue write path is an F04 contract (§4). |
| [F02 spikes](./02-m0-spikes.md) / [F01 CI](./01-monorepo-and-oss-infra.md) | Spike 2 validates `mda init/dev/deploy` (O-003); Spike 3 golden transcripts seed this package's contract tests; F01 runs ruff/pytest/contract jobs. |

Decisions cited: D-004 (runtime-agnostic agent code), D-008 (Python-first), D-011 (SDK wire normalization), P-005 (FastAPI `apps/server`, provisional), O-003 (MDA gating probe, provisional).

## 3. Design

### 3.1 Project layout — a valid `mda` project root ([02 §3](../02-architecture.md))

| File | Contains | Why |
|---|---|---|
| `pyproject.toml` | uv project; exact pins (§2); ruff/pytest config | rides the pnpm monorepo as a non-JS workspace ([05](../05-oss-setup.md)) |
| `langgraph.json` | `graphs: {agent: agent.py:agent}`, `checkpointer.ttl`, `http.app` (classic mount of §3.8 routes) | classic-tier + `langgraph dev` entry; `mda deploy` generates its own into `.mda/build` (`_mda_auth`, `_mda_http`) so no collision ([research 20](../../research/20-gapfill-mda-api.md)) |
| `agent.py` | exports `agent` from `define_deep_agent(...)` (MDA wrapper over the `create_deep_agent` composition). Authors control exactly: model, tools, middleware, subagents, permissions, `interrupt_on`, `response_format`, `context_schema` ([research 01](../../research/01-managed-deep-agents.md)) | single composition point; everything else in the package feeds it |
| `instructions.md` | system prompt (§3.9) | synced per-deployment to Context Hub by `mda deploy` |
| `tools/` | `fetch_url.py`, `http_request.py`, `commit_and_open_pr.py`; structured Results | the non-built-in third of the curated set (§3.4) |
| `middleware/` | `steering.py`, `auto_pr.py`, `reliability.py` (config of stock fault-tolerance middleware — no reimplementation) | §3.3 |
| `connectors/mcp.py` | `define_mcp_servers(...)` — remote HTTP/SSE only, static bearer, tools prefixed `server__tool` ([research 06](../../research/06-execution-sandboxes.md)) | MCP-first connector strategy ([08](../08-deepagents-feature-map.md)) |
| `connectors/deepwork.py` | connector with `http(ctx)` hook → identity-enforced `/connectors/deepwork/*` routes (§3.8) | the MDA-sanctioned replacement for custom `http.app` routes ([research 20](../../research/20-gapfill-mda-api.md)) |
| `schedules/` | `define_schedule(...)` modules (§3.10) | reconciled as Agent Server crons on deploy |
| `skills/<name>/SKILL.md` | agentskills.io progressive-disclosure skills; starter set | synced to Context Hub; org skills merge there ([02 §3](../02-architecture.md)) |
| `sandbox/__init__.py` | `define_sandbox(LangSmithSandbox, scope="thread", idle_ttl_seconds=600, ...)` + `proxy_config` passthrough (callbacks for GitHub tokens — F12) | per-thread sandboxes, Codex-style ([02 §4](../02-architecture.md)) |
| `sandbox/setup.sh` | environment provisioning; uploaded to `/tmp/mda-setup.sh`, run once ([research 20]) | warm-start via snapshots is F11's side |
| `identity.py` | `define_identity(preset=...)` (§3.7) | fail-closed identity; preset switch per deployment |
| `tests/` | §3.11 suites | the constraints below are tests, not prose |

### 3.2 Composition

`create_deep_agent()` assembles the middleware stack and calls `create_agent()` on the LangGraph runtime — no new runtime ([research 02](../../research/02-deepagents-harness.md)). Rules:

- **Runtime-agnostic (D-004)**: no backend/store/checkpointer configured anywhere in agent code — MDA forbids it; other tiers provision it; this is also what keeps the agent Fleet-export-compatible ([02 §2](../02-architecture.md)). Enforced by test (§3.11).
- **Overrides-by-name (≥0.7.0a3)**: a user middleware with a matching `.name` replaces the default in place ([08](../08-deepagents-feature-map.md)). Used *only* to retune a default (e.g. Summarization params); all Deep Work additions use new names and append in the user slot.
- **Models**: `provider:model` strings via `init_chat_model`; built-in `HarnessProfile`s (Anthropic / OpenAI Codex / NVIDIA) used as-is, YAML-loadable; per-template profile overlays → F15 ([02 §3], [research 02]).

### 3.3 Middleware stack — order and config

Harness default order ([research 02]): TodoList → Skills → Filesystem → SubAgents → Summarization → PatchToolCalls → (AsyncSubAgent, not composed in v1) → **user middleware** → profile extras → tool exclusion → prompt caching (Anthropic/Bedrock/Fireworks) → Memory → HumanInTheLoop. Deep Work's user slot, in list order:

| # | Middleware | Origin | Config (v1 defaults; ⚠ = working assumption, §9 Q3) |
|---|---|---|---|
| u1 | `ModelCallLimitMiddleware` / `ToolCallLimitMiddleware` | stock | ⚠ caps: 100 model calls / 250 tool calls per run; templates may lower (F15). Outermost so caps count retries/fallbacks |
| u2 | `ModelFallbackMiddleware` | stock | chain per template primary; default: primary provider → cross-provider equivalent (open-swe v1's top failure class; [08]) |
| u3 | `ModelRetryMiddleware` | stock | transient model errors; exponential backoff ⚠ (max 2 retries, 1s initial, ×2 + jitter). Inside fallback: retry primary, then fall through |
| u4 | `ToolRetryMiddleware` | stock | transient tool errors (timeout/429/5xx), same backoff family ⚠ |
| u5 | `ToolErrorMiddleware` | stock | non-transient tool exceptions → **error `ToolMessage`** (`status='error'`) so the model self-corrects; HITL for user-fixable ([08]) |
| u6 | `RubricMiddleware` (slot) | stock, beta ≥0.6.5 | reserved; enabled + configured per template → [F16](./16-verification-and-rubrics.md) |
| u7 | `CodeInterpreterMiddleware` (slot) | stock, beta | per-template flag (research/data), off by default → F15 ([08]) |
| u8 | auto-draft-PR (`middleware/auto_pr.py`) | ours | §3.3.2; coding templates only |
| u9 | steering (`middleware/steering.py`) | ours | §3.3.1; **last** so its `before_model` hook runs closest to the model call |

**3.3.1 Steering middleware** — open-swe's `check_message_queue_before_model` pattern ([research 10](../../research/10-openswe-fleet.md)), Deep Work's half of double-texting (`multitask_strategy` enqueue default + this; [02 §7]):

- *Injection point*: `before_model` hook. Drains a dedicated state channel (`steering_queue`, name provisional) of user messages posted mid-run by the steering composer, appending them as `HumanMessage`s immediately before the model call.
- *Ordering guarantees*: harness defaults precede the user slot, so injection happens **after Summarization** — a steered message can never be compacted in the same step it arrives. Positioned last in the user slot so no wrapper sits between injection and the call.
- *Dedupe*: each queued entry carries a client-generated id; consumed ids are recorded in state; injection is idempotent across model retries, checkpoint replays, and interrupt-resume — at most once per thread. Drain + append happen in one state update (single reducer step): a crash cannot drop or double-inject. Empty queue = strict no-op (no state write).
- *Client write path* (how the queue is appended while a run is live) is an [F04](./04-sdk-and-agent-sources.md) contract; open-swe's plumbing was not inspected → §9 Q2.

**3.3.2 Auto-draft-PR middleware** (open-swe precedent, [research 10]): fires at agent-loop end when **all** hold: (1) sandbox backend attached; (2) work branch `deepwork/<task>` has commits or a dirty tree beyond clone state; (3) no PR recorded for this thread (state `pr_url` empty); (4) the model did not already call `commit_and_open_pr` this run. Behavior: same implementation as the tool — commit, push, open **draft** PR via the proxy-callback token path (F12) — then write `pr_url` + branch to state for the run panel. Never fires on non-coding templates (F15 flag); never flips draft→ready (human action).

**3.3.3 Reliability stack** — adopted wholesale as configuration ([08](../08-deepagents-feature-map.md)): rows u1–u5 above. `middleware/reliability.py` is a single config module so upstream param renames touch one file.

**3.3.4 How limit/fallback events surface (seam F09)** — normative: every reliability event that changes run outcome must be observable in the protocol-v2 stream with **no bespoke channels**: (a) cap hit → the loop ends with an explanatory assistant message (open-swe's `notify_step_limit_reached` precedent, [research 10]) arriving on `messages`, run status on `lifecycle`; (b) fallback engaged → subsequent messages carry the fallback model id in response metadata; (c) retries are silent in-stream (LangSmith trace only, [02 §10]). F14 asserts (a)/(b) in golden transcripts ([F02](./02-m0-spikes.md) Spike 3 set); F09 renders the "run capped" notice and fallback chip. Exact upstream event shapes unverified → §9 Q4.

### 3.4 Tools — the curated ~15 ([02 §3](../02-architecture.md); curation beats count, [research 10])

| Tool | Source | One-line contract | Default gate |
|---|---|---|---|
| `write_todos` | built-in | replace the todo list → `values.todos {content, status}` | Auto |
| `ls` / `glob` / `grep` | built-in | list / pattern-match / search backend paths | Auto |
| `read_file` | built-in | read path; multimodal content blocks (image/PDF/AV) ([08]) | Auto |
| `write_file` / `edit_file` | built-in | create / string-replace edit | Auto, subject to §3.5 rules |
| `delete` | built-in (0.7a1+) | remove path | Auto, subject to §3.5 rules |
| `task` | built-in | spawn declarative or general-purpose sub-agent (§3.6) | Auto |
| `execute` | built-in (sandbox backends only) | run a shell command in the thread sandbox | **`interrupt_on`** with `when` predicate — coding default: allow-listed safe commands Auto, rest Ask ([02 §3]) |
| `fetch_url` | ours | GET a URL → readable text/markdown + status (structured Result) | Auto |
| `http_request` | ours | arbitrary HTTP call (method/headers/body) → structured response | Auto; Ask-able via the per-tool matrix |
| `commit_and_open_pr` | ours | commit work branch, push, open **draft** PR → URL | **`interrupt_on`** (approve/edit/reject) |
| MCP tools | `connectors/mcp.py` | remote connector tools, `server__tool`-prefixed | **`interrupt_on`** for any user-flagged tool ([02 §3]) |

13 named + MCP-loaded ≈ the "~15". Non-sandbox templates exclude `execute` + `commit_and_open_pr` via tool exclusion (template config, F15).

### 3.5 `FilesystemPermission` rules — allow/deny/interrupt, **first-match-wins** ([02 §3], [research 02]). They cover filesystem tools only — **not** `execute` or MCP tools; those need `interrupt_on`, which is exactly what the Auto/Ask UI compiles to ([08]). Default ruleset (templates may tighten, F15): (1) deny write `/memories/org/**` (org memory is review-loop-only, [07 §2](../07-org-intelligence.md)); (2) interrupt write `/memories/**` (memory edits reviewable); (3) allow everything else. Rules apply identically over StateBackend and sandbox backends.

### 3.6 Sub-agents & models

- **Declarative `SubAgent`s** (dicts: name/description/system_prompt + optional tools/model/middleware/interrupt_on/skills/permissions/response_format, [research 02]): `research` (fetch_url/http_request + read-only FS; long-context summarizing prompt) and `review` (read-only FS + grep/glob; feeds review/verification flows — grading itself is F16). The **auto general-purpose sub-agent stays on** behind `task` ([02 §3]).
- Per-sub-agent `provider:model` overrides allowed; profiles per §3.2. Template-level overlays deferred to [F15](./15-task-templates.md).
- `AsyncSubAgent` is **not** composed in v1 — the v1.x supervisor pattern per [08](../08-deepagents-feature-map.md); v1 parallelism = separate threads/tasks.

### 3.7 `identity.py` — `define_identity(preset=...)`, selected per deployment (env-driven; working assumption `DEEPWORK_IDENTITY_PRESET`, default `private-assistant`). Both presets are fail-closed ([research 01], [research 20]):

| Preset | Implies |
|---|---|
| `private-assistant` | solo operator: single-actor scoping; ingress = `trusted_backend` headers forwarded by `apps/server` (X-MDA-Ingress-Secret + X-MDA-Actor-Id); threads/store/memory scoped to that actor |
| `multi-tenant-saas` | team: actor **and** tenant scoping (X-MDA-Tenant-Id or `validated_token` claims); `metadata.owner` stamped on threads; store access 403s outside the identity namespace; per-tenant memory slices |

Upstream also ships `shared-bot`, `internal-tool`, `service` — not composed in v1. Tools/middleware/connectors read the frozen `runtime.identity` envelope (`{actor{type,id,email}, tenant?, source{provider, threadId?}}`, [research 20]). `mda dev` sets `MDA_LOCAL_DEV=1` (synthetic actor `mda:local-dev`). Classic tiers: F14 ships the equivalent generated `langgraph_sdk.Auth` module; semantics and flows are [F05](./05-auth-and-identity.md)'s.

### 3.8 `connectors/deepwork.py` route inventory — identity-enforced by default (`ctx.router` secure; `ctx.router.public.*` **not** used in v1; [research 20]). Every route resolves the caller's identity envelope and verifies thread ownership (`metadata.owner`) before touching the sandbox.

| Route | Returns | Consumer |
|---|---|---|
| `GET /connectors/deepwork/sandbox/{thread_id}/tree` | file tree (path, type, size) | F13 files rail ([02 §4]) |
| `GET /connectors/deepwork/sandbox/{thread_id}/file?path=` | file content + mime (base64 for binary) | F13 viewer |
| `GET /connectors/deepwork/sandbox/{thread_id}/diff` *(proposed)* | unified diff, work branch vs base | F13 diff review (M2 roadmap implies it; shape → §4) |

On classic tiers the same handlers mount via `langgraph.json` `http.app` ([02 §4]); auth parity there is an F05 open item (§9 Q6).

### 3.9 `instructions.md` — baked vs Hub-synced

**Baked** (in-repo, the deploy-time source): role and operating principles; tool-use and todo discipline; the multimodal rule (store media in the backend, pass paths — Summarization drops media blocks from older turns, [08]); untrusted-content boundaries for schedule/webhook payloads ([02 §10]); git-flow conventions (branch naming, draft-PR etiquette — details F12). **Hub-synced**: `mda deploy` syncs `instructions.md` + `skills/**` to a per-deployment Context Hub repo; post-deploy edits happen there (fleet-manager editor, M3); `/memories/AGENTS.md` is preserved across deploys ([research 01]); org memory mounts read-only at `/memories/org` ([07 §2](../07-org-intelligence.md)). Template-specific prompt deltas do **not** live here — they are assistant configs (F15). Redeploy-overwrite semantics → §9 Q5.

### 3.10 `schedules/` — `define_schedule(...)`: 5-field cron + exactly one of `prompt|input`; thread mode ephemeral (default) or persistent `{id}`; optional timezone and `deliver_to` (dev channel); `mda deploy` deletes and recreates MDA-owned crons after the revision reaches DEPLOYED ([research 20]). v1 ships the directory with one commented example only; real schedule templates are F15/M3 territory.

### 3.11 Testing strategy — constraints as tests

- **pytest units**: composition snapshot (middleware names **in order**, exact tool inventory, `interrupt_on` map, permission-rule order); steering dedupe/idempotency; auto-PR trigger matrix; reliability fault injection with fake models/tools (transient → retried; fatal tool → error ToolMessage; provider outage → fallback chain; caps → limit message); identity preset selection.
- **Runtime-agnostic (D-004) as a test**: static check that the composition passes no `checkpointer`/`store`/backend kwargs and imports no checkpointer/store modules; plus the project must boot under both `langgraph dev` and `mda dev`.
- **Contract tests** (`langgraph dev`, seeded from Spike 3 goldens — [F02](./02-m0-spikes.md)): protocol-v2 content blocks, tools-channel lifecycle, HITL round-trip (Python snake_case payload → SDK normalization, D-011), sub-agent namespaces (`tools:<toolCallId>`), `Last-Event-ID` resume, cap/fallback transcripts (§3.3.4). Run in CI ([F01](./01-monorepo-and-oss-infra.md)).
- **Fleet-export compatibility as a test**: map the composition to the Fleet-export layout (`AGENTS.md`, `config.json`, `tools.json`, `subagents/`, `skills/`) and round-trip via `fleet-deepagents-export` conventions, preserving tools/sub-agents/skills ([02 §6]; v1 release criterion 4).
- **TS mirror**: explicitly **out of v1 scope** — the docs are unambiguous (D-008; [02 §11] "Python first, mirroring open-swe v2"); noted in §9 Q10 only as a post-adoption possibility.

## 4. Contracts

| Contract | Shape | Consumer |
|---|---|---|
| Graph export | `agent.py:agent`, graph id `agent` (one graph in v1) | all runtimes |
| Todos | `values.todos: {content, status: pending\|in_progress\|completed}[]` ([research 21]) | F09 |
| Files | `values.files: Record<path, {content, encoding: 'utf-8'\|'base64'}>` (Python FileData) | F09/F13 via SDK (D-011) |
| Interrupts | v1 HITL payload, Python snake_case `{action_requests, review_configs}`; resume `{decisions:[approve\|edit\|reject\|respond]}` in order ([research 21]) | F04 normalizes; F09/approvals render |
| Sub-agents | namespaces `tools:<toolCallId>`; discovery via root `tools`/`values` events | F09 |
| Steering queue | state keys `steering_queue` / consumed-ids (names provisional); entries `{id, message}` | F04 writes, §3.3.1 drains |
| Reliability surfacing | cap → final assistant message + `lifecycle` status; fallback → response-metadata model id; retries trace-only | F09 (§3.3.4) |
| Connector routes | §3.8 table; additive changes only under `/connectors/deepwork/` | F13, F11 |
| Template config surface | `context_schema` fields: template id, model, sandbox flag, interpreter flag, rubric ref, tool exclusions, Auto/Ask → `interrupt_on` | F15 (values), F17 (editor) |

## 5. Edge cases & failure modes

- **Fallback exhaustion** (open-swe v1's top failure, [research 10]): run ends in error state with the queue and checkpoints intact; resumable; never a silent hang.
- **Steering vs retries/replays**: id-dedupe makes injection idempotent; messages queued during an interrupt wait are drained on resume, before the next model call.
- **Cap hit mid-tool**: the in-flight tool completes or errors first; the limit message follows — no truncated ToolMessage.
- **Sandbox idle-expired** (`idle_ttl` 600s) mid-thread: auto-recreate + `setup.sh` re-run ([02 §4]); `execute` sees a latency spike, not an error. Connector routes against an expired sandbox return the canonical expired-sandbox error — HTTP `410`, body `{"code": "sandbox_expired", "thread_id": "..."}` (defined in F11, consumed by F13; UI may offer re-warm).
- **MCP server down / bearer expired**: transient → ToolRetry; persistent → error ToolMessage via ToolError; static-bearer rotation is a deployment-secret update.
- **`commit_and_open_pr` idempotence**: nothing to commit → structured no-op Result; PR already open → returns the existing URL (auto-PR condition 3 also prevents refire).
- **Summarization drops media blocks** → baked instruction: media to backend, paths in context ([08]).
- **1 concurrent run per thread; enqueue default** ([research 01]): double-texting mid-run = queue (steering) or interrupt — the UI makes the choice explicit ([02 §7]).
- **Misconfigured template leaks `execute`** into a non-sandbox config: tool exclusion is the guard; if bypassed, `execute` without a sandbox backend errors through the ToolError path (defense in depth).
- **`langgraph dev` has no identity**: synthetic local actor; connector routes unauthenticated locally — labeled local-only (F05).

## 6. Security & privacy

- **Zero secrets in agent state or sandbox**: credentials never live in graph state (open-swe v1 pain: keys lost on checkpoint restart, [research 10]); GitHub creds only via the auth-proxy callback (TTL-bound, fail-closed 502; [research 20]) — `commit_and_open_pr`/auto-PR never accept, store, or log tokens.
- **Identity fail-closed** (F05 owns the model): `metadata.owner` stamping; store 403 outside the identity namespace; run-metadata conventions (`task_type/agent/actor/tenant/surface`, [02 §10]) applied in composition for org observability.
- **Connector routes**: secure-by-default router, thread-ownership check, no public routes in v1 (§3.8).
- **Untrusted content**: schedule/webhook payloads render inside boundary markers; `instructions.md` bakes the prompt-injection defense ([02 §10]).
- **MCP**: remote HTTP/SSE only, bearer from deployment secrets (never client-supplied); user-flagged tools gated via `interrupt_on`.
- **Filesystem**: org memory write-denied (§3.5); permissions **not** covering `execute`/MCP is documented *and* negatively tested so no one assumes coverage.
- **Egress**: sandbox default HTTP/S open + raw TCP blocked; per-environment allow-lists are F11's editor ([02 §4]).

## 7. Acceptance criteria

1. `mda dev` boots the project; `langgraph dev` serves the same graph (public-path fallback proven; O-003).
2. Runtime-agnostic test green: no backend/store/checkpointer in agent code (D-004).
3. Middleware-order snapshot matches §3.3 exactly; override-by-name behavior verified against the pinned version.
4. Tool-inventory test: exact curated set; `execute`/`commit_and_open_pr` absent from non-sandbox configs.
5. `interrupt_on` defaults gate `execute` + `commit_and_open_pr`; decisions round-trip in the contract suite.
6. Permissions: first-match-wins verified; `/memories/org` write denied; negative test proves `execute`/MCP are not intercepted by permissions.
7. Steering: a message enqueued mid-run is injected exactly once before the next model call; duplicate ids ignored; visible in the golden transcript.
8. Reliability fault-injection suite green (retry, error ToolMessage, fallback chain, both caps); cap event visible as a message in the transcript.
9. Auto-PR trigger matrix green; draft-PR URL lands in state; no fire on non-coding templates.
10. Fleet-export round-trip green (release criterion 4).
11. Full golden-transcript contract suite green in CI against `langgraph dev` (F01/F02).

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | Package scaffold: uv project, pins (§2), ruff/pytest, layout stubs | [F01](./01-monorepo-and-oss-infra.md) workspace | `uv sync` green in monorepo; layout matches §3.1 |
| 2 | `agent.py` v0: model strings, built-ins minus `execute`, GP sub-agent, harness defaults | 1 | boots under `langgraph dev`; composition snapshot test passes |
| 3 | `instructions.md` v0 (baked sections §3.9) | 1 | served as system prompt in dev; content checklist reviewed |
| 4 | `tools/`: `fetch_url` + `http_request` with structured Results | 2 | unit tests; visible in tool inventory test |
| 5 | Runtime-agnostic lint + composition snapshot in CI | 2 | AC2, AC3 wired into F01 pipeline |
| 6 | Steering middleware + dedupe/idempotency tests | 2 | AC7; queue contract published to [F04](./04-sdk-and-agent-sources.md) |
| 7 | `identity.py` presets + local-dev path + classic `Auth` module | 2 | preset-switch test; `mda dev` synthetic actor; F05 review |
| 8 | Contract-test harness on `langgraph dev`, seeded from Spike 3 goldens | 2, [F02](./02-m0-spikes.md) | M1 transcript subset of AC11 green |
| 9 | Reliability stack config + fault-injection suite | 2 | AC8; §3.3.4 transcript recorded for F09 |
| 10 | Sub-agents `research`/`review` + per-sub-agent models | 2 | `task` spawns both; namespace transcript captured |
| 11 | `sandbox/` + `execute` + permissions ruleset | 2, [F11](./11-execution-and-environments.md) | AC4/AC6; execute smoke in a real thread sandbox (M2) |
| 12 | `commit_and_open_pr` + auto-PR middleware | 11, [F12](./12-github-and-git-flow.md) | AC5/AC9; coding-task → draft PR e2e (M2 exit) |
| 13 | `connectors/mcp.py` + `connectors/deepwork.py` (tree/file, diff proposal) | 11 | routes identity-enforced; F13 renders against them |
| 14 | `schedules/` scaffold + example; `skills/` starter set | 2 | cron reconcile observed in Spike 2 deploy replay |
| 15 | Fleet-export round-trip harness | 2 | AC10 in CI |

## 9. Open questions

1. **Version pin conflict**: [05](../05-oss-setup.md) pins `deepagents` 0.6.12 ("watch 0.7.0") but this spec requires ≥0.7.0a3 (overrides-by-name) and 0.7a1 (`delete`); open-swe v2 ships on `0.7.0a7`. Proposal: exact-pin the alpha like open-swe; interim exception in effect (§2) — the scaffold pins the alpha, superseding 05's pin, pending batch-1 ratification via a decision-log entry.
2. **Steering queue write path**: how the client appends to state mid-run (state-update command vs enqueue-run folding) — open-swe's `dispatch.py`/`reconcile.py` were not inspected ([research 10] open question). The pattern is grounded; the plumbing is not. Blocks T6 detail.
3. **Reliability middleware params**: exact upstream kwarg names/defaults for retry backoff, fallback chains, limit counters — and wrap-nesting semantics (retry-inside-fallback, whether limits count retried attempts) — unverified; pin during T9.
4. **Protocol shape of cap/fallback events**: message injection vs `lifecycle` vs anything else — Spike 3 transcript decides the F09 rendering contract (§3.3.4 states the requirement either way).
5. **`instructions.md` redeploy semantics**: does `mda deploy` overwrite Hub-side edits made via the fleet manager? ([research 01] confirms only that `/memories/AGENTS.md` is preserved.)
6. **Connector-route auth on classic tiers**: `http.app` mounts lack the MDA identity envelope — what enforces ownership there? (F05 seam.)
7. **`PatchToolCalls` middleware semantics** are undocumented in our research — left at defaults; verify no interaction with ToolError.
8. **GP sub-agent prompt**: `DEFAULT_SUBAGENT_PROMPT`/`TASK_SYSTEM_PROMPT` verbatim contents not captured ([research 02]) — decide whether an overlay is needed.
9. **MDA beta constraints on user middleware**: docs say authors control middleware ([research 01]); whether the beta runtime restricts any of §3.3 in practice — Spike 2 verifies.
10. **TS mirror of `packages/agent`**: consciously out of v1 (D-008); revisit only if LangChain adoption wants JS parity.

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| 0.7.0 alpha-train churn (breaking changes before stable) | High | Med | exact pin + canary CI against the dev channel ([roadmap risk register](../04-roadmap.md)); composition-snapshot tests fail loudly on drift |
| MDA gating (O-003) blocks `mda dev/deploy` validation | Med | Med | `langgraph dev` + classic deployment are the fully public, contract-tested path ([02 §12]); MDA-only bits (presets, managed sandbox) degrade to documented classic patterns |
| Steering plumbing assumption wrong (§9 Q2) | Med | Med | isolated in `middleware/steering.py`; fallback = double-texting `interrupt` strategy only, queue semantics kept client-side |
| Reliability middleware API drift / param renames | Med | Low | single config module (`reliability.py`); fault-injection suite pins behavior, not names |
| Middleware default order changes silently upstream | Med | Med | order snapshot test (AC3) |
| `managed-deepagents` 0.4.0-dev churn (identity/schedules) | High | Low-Med | identity/schedule code isolated to two files; dev-channel-only features flagged ([roadmap](../04-roadmap.md)) |
| Fleet-export format drift breaks round-trip | Low | Med | round-trip test in CI (AC10); format ships as a versioned MIT package ([research 10]) |
