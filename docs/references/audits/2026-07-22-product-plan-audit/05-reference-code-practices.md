# LangChain reference-code and engineering-practice audit

Status: staged evaluation; no runtime or canonical plan is changed
Audit date: 2026-07-23
Architecture companion: [`../architecture/application-architecture.md`](../architecture/application-architecture.md)
Engineering companion: [`../architecture/engineering-conventions.md`](../architecture/engineering-conventions.md)

## Verdict

Deep Work should feel native to LangChain contributors on the Python side and
familiar to LangChain.js contributors on the TypeScript side. That means
matching the community's method—small independently testable packages, explicit
public surfaces, typed boundaries, async-first behavior, package-local commands,
standard adapter suites, contract recordings, focused pull requests, and
reproducible releases—rather than copying every historical compatibility choice
or embedding upstream internals.

The reference code strengthens the staged stack choice:

- Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL, and a
  separately running worker for the Deep Work application service;
- a separately deployable Python agent package composed from public Deep Agents,
  LangChain, and LangGraph APIs;
- Next.js 16, React 19, and strict TypeScript for the responsive web/PWA;
- Tauri v2 as a narrowly privileged host around the trusted web origin;
- Expo/React Native only after measured PWA gaps justify a separate native app;
- a small framework-neutral TypeScript domain package between application,
  SDK, UI, fixtures, and future native clients.

It also changes several existing planning assumptions. The browser-facing SDK
must not own secret-bearing provider adapters or expose credential references.
The Python service should be the default upstream integration and stream
boundary. Deep Work should consume official stream, deployment, sandbox,
middleware, and editor-protocol packages where their pinned public contracts
fit instead of rebuilding them.

## Frozen reference snapshots

| ID | Repository | Commit | Engineering use | Authority limit |
|---|---|---|---|---|
| `SRC-DA` | `langchain-packages/deepagents` | `7794b61a6e76230e8c7a49bdce808b3728305914` | Python package practice, agent composition, CLI/code/ACP/evals/Talon and middleware evidence | Alpha/beta internals are not stable product contracts |
| `SRC-LCPY` | `langchain-packages/langchain` | `592055e15e138f5369dce95dd049ce22430996e2` | Mature Python public-API, typing, test, package and release discipline | Library conventions do not define Deep Work application architecture |
| `SRC-LCJS` | `langchain-packages/langchainjs` | `ee76ea0347fb611153e5ec7d0e70fa405f5293a3` | TypeScript package graph, ESM, Oxc, schema, standard-test and release practice | Its broad runtime/legacy compatibility burden is not a greenfield requirement |
| `SRC-LG` | `langchain-packages/langgraph` | `31f90df3e6b0268fa77fd2d118a917d420b84a68` | Official Python/TypeScript SDK boundaries and protocol-v2 stream implementation evidence | Installed public API and live-server behavior still require a pinned contract spike |

All four repositories were read locally at the commits above. They are source
references, not dependencies by path and not permission to vendor code.

## Evidence precedence inside a reference repository

Reference repositories contain occasional prose drift. Deep Work therefore uses
this order when deriving engineering practice:

1. passing tests and executable configuration;
2. current package manifests, lockfiles, generated artifacts, and export maps;
3. the closest applicable `AGENTS.md`;
4. contributor guides and READMEs;
5. examples and comments.

This order applies only to engineering conventions. External service behavior
still follows the proposal-wide rule: accepted live-contract evidence, then
installed/generated public contracts, then official documentation, then source
implementation evidence.

## Deep Agents findings

### Practices to adopt

The Deep Agents snapshot is a monorepo of independently versioned Python
packages. Its packages have their own `pyproject.toml`, dependency groups,
public metadata, build backend, local editable sources, tests, and usually a
package-local lock and `Makefile`. The root guidance standardizes the contributor
loop around `uv`, `make`, Ruff, a type checker, and pytest.

Deep Work should adopt:

- package-local `pyproject.toml`, `uv.lock`, `Makefile`, README, tests, and
  package metadata for `apps/api` and `packages/agent`;
- root commands that fan out to package commands without pretending the API and
  deployable agent share one release or dependency range;
- Ruff with a broad `ALL` posture, formatter-compatible documented exceptions,
  absolute imports, Google docstrings, complete type annotations, and narrow
  inline suppressions;
- `ty` for the Deep Agents-facing agent package and strict `mypy` with the
  Pydantic plugin for the FastAPI/application package;
- `tests/unit_tests/` for network-denied deterministic tests and
  `tests/integration_tests/` for explicitly credentialed tests;
- explicit public exports, keyword-only additive parameters, beta warnings,
  and compatibility review before changing a public signature;
- conventional pull-request titles with mandatory scopes, scoped branch names,
  concise public-facing descriptions, and explanation of why a change belongs;
- package-local search, commands, and ownership rather than broad monorepo
  assumptions.

### Upstream components to reuse or evaluate

| Upstream surface | Snapshot evidence | Deep Work posture |
|---|---|---|
| `deepagents.create_deep_agent` | Public agent composition delegates to LangChain `create_agent` | Use as the default agent construction seam; do not rebuild graph assembly without a missing capability |
| `RubricMiddleware` | Exported from `deepagents`; decorated beta; owns structured rubric iteration and stream events | Replace the delivery plan's custom middleware task with a pinned reuse/conformance spike; wrap only product persistence and presentation |
| `deepagents-cli` | Official `init`, `dev`, and `deploy` package | Invoke or hand off to the supported CLI; never recreate deployment packaging with guessed APIs |
| `deepagents-code` | Beta coding product with sandbox, MCP, approvals, persistent memory, and a client/server shape; currently pins an alpha Deep Agents build | Treat as coding-journey evidence and evaluate a headless adapter in a bounded spike; do not embed its Textual UI or internal modules in v1 |
| `deepagents-acp` | Alpha Agent Client Protocol package | Use the official package for a future editor adapter after a public-surface spike; do not invent a competing protocol bridge |
| sandbox partner packages | Optional public packages for supported providers | Implement Deep Work provider ports over stable partner APIs and run one common conformance suite |
| `deepagents-evals` | Separate alpha evaluation package and benchmark harness | Keep behavioral evals separate from deterministic unit/contract tests and ordinary release gates |
| `deepagents-talon` | Experimental alpha local host for one operator, channels, and simple schedules | Borrow Protocol/lifecycle/redaction patterns; consider only a future local sidecar adapter, never the hosted v1 backend |

### Practices not to copy

- Do not import another package's private modules because an example or adjacent
  package currently does so.
- Do not treat in-memory checkpoints, local JSON files, environment/TOML
  credentials, unsandboxed local shell execution, or single-process scheduling
  as hosted durability or tenancy.
- Do not claim alpha/beta package presence proves product readiness.
- Do not add every model, provider, sandbox, or channel to Deep Work's default
  install. Integrations stay optional and capability-tested.
- Do not combine product API, worker, agent runtime, scheduler, and channel host
  into one event loop merely because Talon demonstrates local composition.

## LangChain Python findings

The mature LangChain packages reinforce stable public interfaces, explicit
package exports, strict typing at important boundaries, Pydantic-aware checking,
Google docstrings, absolute imports, and a strong unit/integration split.

Deep Work should use the same type-selection logic:

| Need | Preferred Python type |
|---|---|
| HTTP, configuration, persistence input/output, or untrusted provider boundary | Pydantic v2 model with explicit validation and serialization |
| LangGraph state, event fragments, or structurally composed protocol data | `TypedDict`, `Literal`, and discriminated unions |
| Internal immutable value with no validation/serialization boundary | Frozen, slotted dataclass |
| Replaceable source, storage, notification, sandbox, or clock behavior | Narrow `Protocol` with async methods and conformance tests |
| Stable user-facing package API | Explicit export from `__init__.py`, `__all__`, documentation, and compatibility tests |

Application code should translate provider exceptions once at an adapter into a
small `DeepWorkError` hierarchy. It should avoid a generic upstream client in
routers and avoid leaking provider models into domain, persistence, or response
objects.

## LangChain.js findings

### Practices to adopt

The TypeScript snapshot uses pinned pnpm workspaces, Turborepo, shared internal
configuration packages, strict ES2022/ESM, explicit package export maps, runtime
schema validation, standard integration suites, clean consumer tests, and
Changesets.

Deep Work should adopt:

- one pinned pnpm version, Node 24 for development/CI, and package-local
  `build`, `typecheck`, `test`, and `test:integration` scripts orchestrated by
  Turbo;
- `apps/*`, `packages/*`, and private `internal/*` workspaces with explicit
  inputs, outputs, dependency order, and environment variables;
- ES2022, ESM, bundler resolution, strict TypeScript, declarations/source maps
  for libraries, `allowJs: false`, and contract CI that does not hide errors
  behind `skipLibCheck`;
- Oxc formatting/linting, including Oxfmt's 80-column, two-space, semicolon,
  double-quote, trailing-comma and LF conventions;
- `.js` extensions for local relative imports in library packages, named
  exports, and default exports only where Next.js requires them;
- Zod v4 for untrusted TypeScript boundaries and separate input versus
  normalized/defaulted output types;
- explicit browser-safe subpath exports, public TSDoc, cancellation via
  `AbortSignal`, typed errors, bounded async iteration, and no direct
  environment access outside host configuration modules;
- Vitest unit, integration, type, contract, and standard/conformance suites,
  plus packed-package/clean-consumer tests;
- Changesets for public TypeScript behavior and application releases kept
  separate from package releases.

### Required framework-neutral core

The staged package graph currently makes `packages/sdk` own normalized domain
types while forbidding `packages/ui` from importing the SDK. That leaves the UI
without an allowed canonical type source. LangChain.js solves the analogous
problem with a low-level core package.

Deep Work should add `packages/domain`:

```text
packages/domain
├── packages/sdk
├── packages/ui
└── internal/fixtures

apps/web -> packages/domain + packages/sdk + packages/ui
apps/desktop -> hosted apps/web + explicit native bridge
future apps/mobile -> packages/domain + packages/sdk; not DOM packages/ui
```

`packages/domain` owns stable identifiers, UI-safe entities, source capability
values, status and event reducers, safe error codes, and versioned normalized
schemas. It has no React, Next.js, Tauri, networking, provider, environment, or
credential dependency.

`packages/sdk` becomes the browser-safe Deep Work application API client,
stream client, OpenAPI DTO mapper, request cancellation layer, and optional
React bindings subpath. It does not probe LangSmith, hold `authRef`, construct
provider headers, or aggregate by calling multiple provider endpoints.

`apps/api` owns all secret-bearing provider adapters, capability detection, and
per-source aggregation. It returns a public source view with credential health,
never the server-side credential reference.

### Practices not to copy

- Do not adopt Zod 3/4 interoperability, CommonJS output, Deno/Bun/Workers
  compatibility, broad dependency overrides, or every legacy export solely
  because the mature library supports them.
- Do not copy `allowJs: true`, disabled strict property initialization,
  blanket `skipLibCheck`, disabled promise-safety checks, or broad lint
  exemptions into a greenfield product.
- Do not force LangChain `Runnable` names onto tasks, approvals, files,
  schedules, or product services.
- Do not make LangChain.js a React application-style authority; its strongest
  evidence is package and integration engineering.

## LangGraph findings

The Python SDK snapshot already implements protocol-v2 stream subscription,
shared SSE lifecycle, bounded event-ID deduplication, cursor-aware reopen,
reconnect with backoff/jitter, and clean async shutdown. This is strong evidence
that Deep Work should compose the pinned official SDK rather than recreate the
protocol in application code.

The architecture consequence is:

1. FastAPI owns the default upstream stream connection because provider
   credentials, source selection, authorization, and contract translation are
   server concerns.
2. The Python adapter composes the official async SDK and preserves upstream
   event/cursor values exactly.
3. FastAPI emits a versioned, normalized, browser-safe application stream.
4. The TypeScript SDK reconnects to the application stream and reduces only
   validated application events.
5. Direct browser-to-deployment streaming is an optional optimization only if a
   named auth/stream spike proves short-lived least-privilege credentials,
   CORS, replay, revocation, and identical normalized behavior.

`SPIKE-STREAM-001` still governs the exact installed public API and deployed
server behavior. Reading an internal controller is not permission to import it.

## Resulting package and dependency corrections

```text
apps/web ─────────────┐
                     ├──> packages/sdk ───> packages/domain
                     └──> packages/ui  ───> packages/domain

apps/desktop ──> trusted hosted apps/web + narrow Tauri bridge

apps/api ──> application/domain ports ──> provider adapters
   │                                      ├── official langgraph-sdk
   │                                      ├── official langsmith SDK
   │                                      ├── GitHub/sandbox/push clients
   │                                      └── fixture adapters
   ├──> PostgreSQL
   ├──> S3-compatible object storage
   └──> Postgres outbox/job worker

packages/agent ──> public deepagents/LangChain/LangGraph packages

internal/fixtures ──> packages/domain
internal/adapter-tests ──> packages/domain + packages/sdk
```

Forbidden directions include UI to SDK, SDK to provider secrets, API to the
agent's Python internals, agent to application persistence, desktop to provider
credentials, and canonical code to the prototype or local reference checkouts.

## Corrections required in the staged plans

| Existing staged assumption | Reference-code result | Required correction |
|---|---|---|
| One root uv workspace owns API and agent | Reference Python packages are independently versioned/tested and carry package-local environments | Give API and agent separate manifests, locks, Makefiles, support ranges, and release identities; use root fan-out commands |
| Biome and an undecided Python type checker | LangChain.js uses Oxc; Deep Agents uses `ty`; LangChain core uses strict `mypy` with Pydantic plugin | Use Oxfmt/Oxlint; `ty` for agent; strict `mypy` for API; document exceptions |
| `packages/sdk` owns domain, upstream source probing, auth refs, and cross-source calls | LangChain.js core/provider separation and server secret boundary contradict this | Add `packages/domain`; move probing, credentials, and aggregation to FastAPI; make SDK an application client |
| Fixture records live in `packages/ui` or a public fixtures package | Reference standard tests and internal packages keep reusable test infrastructure private | Use `internal/fixtures` and `internal/adapter-tests`; UI stories consume them but do not own them |
| Custom rubric middleware in delivery unit U12 | Deep Agents exports beta `RubricMiddleware` | Replace implementation task with pin/reuse/conformance spike and product wrapper only |
| Rebuild stream resume/dedupe in TypeScript | Official LangGraph Python SDK already owns protocol mechanics | Compose pinned public SDK server-side; TS handles app-stream reconnect/reduction |
| Browser can carry an opaque `authRef` | A reference identifier still exposes server credential topology and invites misuse | Return only credential state, expiry/attention, and capability evidence in public source views |
| Direct browser-to-provider stream is the normal path | Multi-surface auth and server-only adapters require one safe boundary | Make FastAPI stream mediation the baseline; direct mode is a separately verified optimization/local mode |
| Evals are ordinary release tests | Deep Agents keeps evals as a separate package/harness | Separate deterministic tests from model/runtime quality evaluation and track both explicitly |

## Contributor-adoption design

The first public contribution path should look recognizably LangChain-like:

1. clone once and run a prerequisite/bootstrap check;
2. enter one package or use a root `make` fan-out command;
3. start deterministic fixture mode without credentials;
4. change a small adapter, reducer, component, or agent behavior;
5. run the package's `make format`, `make lint`, and `make test` (or the exact
   pnpm filtered equivalents);
6. run a shared conformance suite for an adapter change;
7. open a focused, scoped Conventional Commit pull request with user impact,
   rationale, docs/tests, and any AI assistance disclosed under project policy;
8. receive affected-package CI, a fixture preview, and a clear maintainer owner.

Good first issues should exercise real boundaries without requiring private
accounts: fixture scenarios, source capability error mapping, accessibility,
type tests, docs, safe normalizers, standard-test cases, and package consumers.

## Acceptance checks for this audit

Before the architecture/conventions proposal is accepted:

- all four reference commits appear in the source ledger with authority limits;
- `packages/domain`, `internal/fixtures`, and `internal/adapter-tests` appear in
  the architecture and staged dependency guidance;
- no browser-facing type contains `authRef`, provider tokens, or arbitrary
  forwarding headers;
- API and agent have separate proposed Python environments and exact local
  validation commands;
- Oxfmt/Oxlint replace Biome in the staged foundation plan;
- agent type checking is `ty`; API type checking is strict `mypy` with the
  Pydantic plugin;
- official SDK/middleware/CLI/sandbox/ACP candidates have reuse-versus-spike
  dispositions and no plan imports private upstream modules;
- adapter conformance, unit, integration, contract, type, E2E, clean-install,
  and eval suites have distinct purposes;
- the 957-line delivery plan remains byte-for-byte unchanged;
- no file outside this proposal folder is modified by this review.
