# Source ledger

## Frozen repositories

| ID | Repository or artifact | Revision | Verified | Use |
|---|---|---:|---:|---|
| SRC-FE | `deep-work-frontend` | `26c698b30ff08d5122cfaeedbd4a95296a7884f4` | 2026-07-23 | Accepted route, component, visual, interaction, and fixture baseline; evidence only, never runtime authority |
| SRC-LC | `langchain-docs-reference` | `7b9215d708e0b57e6fbae7b5d0762c4118b8e309` | 2026-07-22 | Official LangChain, LangSmith, Deep Agents, and frontend contracts |
| SRC-DW | `deepwork` | `06f051554bf938e919af5ab7855974098fbf3d2a` | 2026-07-22 | Current product intent and roadmap |
| SRC-DP | `docs/plans/2026-07-22-001-feat-deepwork-v1-delivery-plan.md` | 986 lines; SHA-256 `3f4b6ed96054289426ac6c53ee6b4702484a934067a11b5761c0d68d756e3b0c`; untracked | 2026-07-23 | Accepted preservation baseline for an uncertain legacy proposal; not promoted to canonical authority |
| SRC-DA | `langchain-packages/deepagents` | `7794b61a6e76230e8c7a49bdce808b3728305914` | 2026-07-23 | Python package conventions, public exports, agent composition, CLI/code/ACP/evals/Talon, and reuse evidence; not deployed-service authority |
| SRC-LCPY | `langchain-packages/langchain` | `592055e15e138f5369dce95dd049ce22430996e2` | 2026-07-23 | Mature Python public-API, typing, package, test, and release conventions; not Deep Work application architecture authority |
| SRC-LCJS | `langchain-packages/langchainjs` | `ee76ea0347fb611153e5ec7d0e70fa405f5293a3` | 2026-07-23 | TypeScript package graph, ESM, schema, conformance-test, Oxc, and release conventions; not React product-architecture authority |
| SRC-LG | `langchain-packages/langgraph` | `31f90df3e6b0268fa77fd2d118a917d420b84a68` | 2026-07-23 | Official SDK/package and protocol implementation evidence; installed public API and live behavior still require a pinned spike |

## Official engineering-method sources

These sources govern the proposed repository and contributor method. They do not
establish Deep Work product scope or LangChain hosted-service contracts.

| ID | Source | Revision or date | Verified | Use and limitation |
|---|---|---|---|---|
| SRC-HE | [OpenAI Harness Engineering](https://openai.com/index/harness-engineering/) | Published 2026-02-11 | 2026-07-23 | Short `AGENTS.md` map, repository-local knowledge, living plans, generated docs, architecture enforcement, agent-legible feedback, quality grading, and recurring gardening. Principle/method authority, not a library contract. |
| SRC-EXEC | [Codex ExecPlan guidance](https://developers.openai.com/cookbook/articles/codex_exec_plans) | Published 2025-10-07 | 2026-07-23 | Self-contained living implementation plans with progress, discoveries, decisions, outcomes, exact validation, interfaces, and recovery. Method authority, not feature scope. |
| SRC-SYM | [OpenAI Symphony article](https://openai.com/index/open-source-codex-orchestration-symphony/) plus [SPEC](https://github.com/openai/symphony/blob/1f3219bb1ea5f69a1305dc594e79b0db57c113c5/SPEC.md) and [example workflow](https://github.com/openai/symphony/blob/1f3219bb1ea5f69a1305dc594e79b0db57c113c5/elixir/WORKFLOW.md) | `openai/symphony@1f3219bb1ea5f69a1305dc594e79b0db57c113c5`; engineering preview | 2026-07-23 | Issue-driven scheduling, blocker DAG, isolated workspaces, repository-owned policy, reconciliation, bounded concurrency, backoff, and Human Review handoff. Requires `SPIKE-SYMPHONY-001`; not the product worker or a proven GitHub tracker adapter. |

## Framework decision evidence

Framework documentation supports review of the proposed stack but does not make a
version selection implementation-ready. The scaffold change must pin packages and
record compatibility evidence.

| ID | Official source | Verified | Planning conclusion |
|---|---|---|---|
| SRC-FASTAPI | [FastAPI larger applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/) and [deployment workers](https://fastapi.tiangolo.com/deployment/server-workers/) | 2026-07-23 | FastAPI provides modular routers/dependencies/OpenAPI and documented process deployment. Deep Work still owns its hexagonal boundary, API/worker split, transactions, and operations. |
| SRC-SQLA | [SQLAlchemy 2.0 session transactions](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html) and [session concurrency](https://docs.sqlalchemy.org/en/20/orm/session_basics.html) | 2026-07-23 | Use explicit per-request/per-job transaction scope; never share one mutable `AsyncSession` across concurrent tasks. Exact SQLAlchemy/Alembic/driver pins remain scaffold decisions. |
| SRC-NEXT | [Next.js App Router documentation](https://nextjs.org/docs/app/getting-started) | 2026-07-23 | Next.js supports the proposed route/layout web layer. It does not justify moving durable application state, jobs, or provider secrets into the web process. |
| SRC-QUERY | [TanStack Query v5 React overview](https://tanstack.com/query/latest/docs/framework/react/overview) | 2026-07-23 | Candidate owner for ordinary asynchronous server state only. Active stream/reducer and durable application authority remain separate; adoption requires the frontend ADR in `DW-SURF-001`. |
| SRC-PWA | [MDN PWA offline/background guide](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Offline_and_background_operation) and [PWA capability guidance](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/What_is_a_progressive_web_app) | 2026-07-23 | Service-worker, push, and background behavior are capability- and browser-dependent. V1 must feature-detect and ship a safe responsive-web fallback; no offline mutation is assumed. |
| SRC-TAURI | [Tauri v2 capability reference](https://v2.tauri.app/reference/acl/capability/) and [signed updater guide](https://v2.tauri.app/plugin/updater/) | 2026-07-23 | Remote content with native capability is security-sensitive and must use exact URL/capability allow-lists plus signed update qualification. The remote-origin host remains gated by `SPIKE-DESKTOP-001`. |
| SRC-RUST | [Rust stable-channel guidance](https://doc.rust-lang.org/book/appendix-07-nightly-rust.html) and [Rust 2024 formatting edition](https://doc.rust-lang.org/edition-guide/rust-2024/rustfmt-style-edition.html) | 2026-07-23 | Pin stable Rust through `rust-toolchain.toml`, record edition/MSRV, and enforce rustfmt, Clippy, Cargo tests, and dependency audit for the Tauri host. |
| SRC-EXPO | [Expo SecureStore documentation](https://docs.expo.dev/versions/v54.0.0/sdk/securestore/) | 2026-07-23 | Native secure storage has platform behavior and limits; this supports a future discovery gate only. It does not prove the browser SDK, session, or stream transport is native-safe. |

## Confidence labels

| Label | Meaning | Planning rule |
|---|---|---|
| `documented` | Current official documentation or generated contract explicitly supports the claim. | May be planned, with a pinned minimum version. |
| `gated` | Real but private-beta, region-, plan-, permission-, or version-gated. | Require capability detection and a deterministic fallback. |
| `inferred` | Supported by source behavior or internal research but absent from the public contract. | Require a spike before implementation. |
| `contradicted` | A higher-precedence source says the current plan is wrong. | Remove or rewrite the claim before a plan becomes ready. |
| `unknown` | Evidence is insufficient or internally inconsistent. | Add a bounded spike and do not delegate the decision to implementation. |

## Frontend rebaseline note

The original 2026-07-22 audit used `8866d39`. A read-only comparison to the
accepted `26c698b` baseline found two changed files:
`components/sidebar-nav.tsx` and `components/task-detail.tsx`. The delta adds a
sidebar adjustment and a local-state Interrupt/Resume interaction. It does not
prove provider interruption, resume, streaming, persistence, replay, or recovery.
The preserved original audit plus the
[2026-07-23 refresh](audits/2026-07-23-frontend-refresh.md) form the accepted UI
evidence set.

## Legacy-plan preservation note

The previously frozen 957-line observation was superseded before Wave 0 began by
the exact 986-line `SRC-DP` baseline above and ten additional uncertain files.
Wave 0 did not edit those originals. Byte-for-byte reference copies and their
hashes are recorded in
[the unreviewed legacy manifest](legacy-plans/unreviewed-2026-07-22/README.md).
These artifacts remain evidence only; `docs/PLANS.md` and `docs/product-specs/`
are the canonical planning authorities.

## High-value LangChain evidence

| Topic | Primary local evidence | Current conclusion |
|---|---|---|
| Deep Agents frontend projections | `src/oss/deepagents/frontend/overview.mdx` | Messages, values, todos, tools, and subagent projections are documented. |
| Message queues | `src/oss/langchain/frontend/message-queues.mdx` | Use `submit` with a multitask strategy; do not invent `send`. |
| Time travel | `src/oss/langchain/frontend/time-travel.mdx` | `forkFrom` creates an alternate path in the same thread history. |
| HITL | `src/oss/deepagents/human-in-the-loop.mdx` and `src/oss/langchain/frontend/human-in-the-loop.mdx` | Preserve aligned action/review arrays and one ordered decision per action; the exact frontend resume helper must be pinned by a spike. |
| Stream recovery | `src/langsmith/event-streaming.mdx` | Protocol-v2 uses durable event identifiers and a sequence cursor; legacy `Last-Event-ID` must not be assumed. |
| Managed Deep Agents | `src/langsmith/managed-deep-agents-overview.mdx` | Private beta, US-only, and CLI-first; public API-driven lifecycle is not a v1 baseline. |
| MDA connectors | `src/langsmith/managed-deep-agents-connectors/` | MCP and constrained LangSmith connectors are documented; arbitrary custom app routes are not. |
| MDA identity | `src/langsmith/managed-deep-agents-identity.mdx` | Trusted-backend and validated-token identity are documented but separate from operator authentication. |
| MDA schedules | `src/langsmith/managed-deep-agents-schedules.mdx` | Source-declared schedules are reconciled by deployment; they are not ordinary mutable UI records. |
| Context Hub | `src/langsmith/managed-deep-agents-memory.mdx` and `manage-contexts-sdk.mdx` | Instructions, skills, user memory, and org memory have distinct ownership and write boundaries. |
| Classic deployment | `src/langsmith/deploy-with-control-plane.mdx` | Public, supported baseline for programmatic application integration. |

## High-value reference-code evidence

Reference implementation evidence guides Deep Work's engineering method and
reuse posture. It does not outrank an accepted live contract or authorize
imports from private upstream modules.

| Topic | Pinned local evidence | Current conclusion |
|---|---|---|
| Deep Agents contributor method | `SRC-DA`: `AGENTS.md`, `libs/DEVELOPMENT.md`, package `pyproject.toml`/`Makefile` files | Use package-local uv environments, Ruff, type checking, pytest, explicit package commands, scoped Conventional Commits, and stable public surfaces. |
| Deep Agents agent composition | `SRC-DA`: `libs/deepagents/deepagents/graph.py` and package exports | Compose the deployable agent from public Deep Agents/LangChain APIs; keep application service state outside the graph package. |
| Rubric verification | `SRC-DA`: `libs/deepagents/deepagents/middleware/rubric.py` and public exports | A beta `RubricMiddleware` already exists; pin and conformance-test it rather than implementing a competing middleware by default. |
| Deployment tooling | `SRC-DA`: `libs/cli` package/entry points | Use or hand off to official deployment tooling; do not recreate its packaging/deploy workflow from guessed routes. |
| Coding and editor integrations | `SRC-DA`: `libs/code`, `libs/acp`, and sandbox partner packages | Treat coding UI/runtime behavior as reuse-spike evidence; public beta/alpha surfaces must be pinned and private internals remain off limits. |
| Local channel host | `SRC-DA`: `libs/talon` README, interfaces, host, schedules, and package metadata | Talon is experimental single-operator prior art and a possible future sidecar, not the hosted application backend, scheduler, or HITL contract. |
| Python service rigor | `SRC-LCPY`: `AGENTS.md` and `libs/core/pyproject.toml` | Use strict `mypy` plus Pydantic plugin for FastAPI/application boundaries, Google docstrings, absolute imports, public compatibility review, and isolated unit/integration tests. |
| TypeScript package core | `SRC-LCJS`: `libs/langchain-core`, explicit exports, `internal/tsconfig` | Add framework-neutral `packages/domain`; keep providers, React, and environment concerns out of its dependency graph. |
| TypeScript tooling | `SRC-LCJS`: root `package.json`, `turbo.json`, `.oxfmtrc.jsonc`, `.oxlintrc.jsonc` | Pin pnpm/Node, use Turbo, strict ES2022 ESM, Oxfmt/Oxlint, explicit exports, and package-filtered commands. |
| Adapter standard tests | `SRC-LCJS`: `internal/standard-tests` and provider uses | Every source adapter must pass a shared conformance suite in addition to unit and credentialed integration tests. |
| Protocol-v2 stream mechanics | `SRC-LG`: `libs/sdk-py/langgraph_sdk/stream/controller.py` and public SDK package | Compose the pinned official async SDK for cursor/replay/dedupe/reconnect; do not rewrite protocol mechanics in React. |

## Evidence maintenance

- Every feature plan lists its source IDs and any exact documentation paths it depends on.
- A package upgrade that changes a public contract invalidates the associated `ready` status until contract tests pass.
- Prototype types and fixtures never establish an API contract.
- Source-code internals never establish a public hosted contract. Use them to
  understand engineering practice or to motivate a pinned public-surface spike.
- Inside a reference repository, passing tests/executable configuration outrank
  manifests/generated artifacts, which outrank `AGENTS.md`, contributor prose,
  READMEs, and examples when deriving engineering practice.
- Accepted spike memos are added here with the exact server, SDK, package, account tier, region, and date tested.
