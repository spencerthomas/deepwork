# Deep Work engineering and contributor conventions

Status: **canonical engineering direction; progressively enforced**
Created: 2026-07-23
Applies to: Deep Work monorepo, application service, agent package, web/PWA,
desktop host, shared TypeScript packages, tests, documentation, and contribution
workflow

This document defines how Deep Work should feel to engineers who already contribute to LangChain, LangGraph, Deep Agents, or LangChain.js. It deliberately adopts the community's working method—typed public boundaries, package-local tooling, standard adapter tests, executable examples, disciplined pull requests, and reproducible releases—without inheriting compatibility obligations that a new application does not yet have.

Acceptance of these conventions is not a claim that every tool or command already
exists. Wave 0 enforces the documentation subset. The active Wave 1 ExecPlan adds
the package and command harness; later stages make each rule executable.

## 1. Intended outcome

An experienced LangChain contributor should be able to:

1. identify the package that owns a change without learning the entire application;
2. bootstrap a credential-free fixture environment in 15 minutes or less;
3. use familiar `uv`, `make`, Ruff, pytest, pnpm, Turbo, Vitest, and Conventional Commit workflows;
4. add an agent-source or sandbox adapter by implementing a small port and running a shared conformance suite;
5. understand which interfaces are public, generated, experimental, or internal;
6. run the same package checks locally that branch protection runs in CI; and
7. contribute without access to a private LangSmith beta, paid provider, production database, or project secret.

"LangChain-community fit" does **not** mean copying every upstream directory or supporting every historical environment. Deep Work is an application with a Python integration boundary and a modern React client. It should share upstream discipline while keeping a smaller support matrix and a clear product architecture.

### Success measures

| Measure | Target before public contributor launch |
|---|---|
| Clean-clone, no-credential demo start | median at or below 15 minutes on supported macOS, Linux, and dev-container paths |
| First useful test | one documented command from the changed package; no root-wide test required for a leaf change |
| Unit-test network isolation | outbound sockets disabled by default in Python and TypeScript unit suites |
| Public contract drift | generated-code check fails in CI when OpenAPI or event schemas change without regeneration |
| Adapter parity | every enabled adapter passes the same capability-scoped conformance suite |
| Public change documentation | every user-visible package change has a Changeset or an explicit no-release classification |
| Contributor clarity | issue template names owner, files, local command, expected behavior, and acceptance check |

## 2. Evidence and source authority

### Pinned engineering references

These repositories are examples of engineering practice, not automatic authorities for Deep Work product behavior.

| Reference | Pinned commit | Practices used here |
|---|---|---|
| `langchain-packages/deepagents` | `7794b61a6e76230e8c7a49bdce808b3728305914` | independently tooled Python packages, `uv`, package locks, Makefiles, Ruff, `ty`, no-socket unit tests, Google docstrings, explicit public-API care, scoped branch and PR conventions |
| `langchain-packages/langchain` | `592055e15e138f5369dce95dd049ce22430996e2` | core/implementation/integration/test-layer separation, strict `mypy` with the Pydantic plugin, standardized adapter tests, typed public APIs |
| `langchain-packages/langchainjs` | `ee76ea0347fb611153e5ec7d0e70fa405f5293a3` | pnpm workspaces, Turborepo, Node 24 development baseline, strict ES2022 ESM, Oxfmt/Oxlint, named exports, explicit `.js` local imports, test taxonomy, Changesets |
| `langchain-packages/langgraph` | `31f90df3e6b0268fa77fd2d118a917d420b84a68` | explicit dependency maps, downstream testing, package-local `make format`, `make lint`, and `make test` loops |

Primary local evidence includes:

- `langchain-packages/deepagents/AGENTS.md`, `libs/DEVELOPMENT.md`, `libs/Makefile`, and package `pyproject.toml`/`Makefile` files;
- `langchain-packages/langchain/AGENTS.md`, `libs/core/pyproject.toml`, `libs/langchain_v1/pyproject.toml`, and `libs/standard-tests/`;
- `langchain-packages/langchainjs/AGENTS.md`, `CONTRIBUTING.md`, `package.json`, `internal/tsconfig/base.json`, `.oxlintrc.jsonc`, `.oxfmtrc.jsonc`, and its standard/environment/dependency-range tests; and
- `langchain-packages/langgraph/AGENTS.md` and library manifests.

### Two precedence ladders

Engineering style and external runtime behavior need different authority rules.

**For Deep Work engineering practice:**

1. accepted Deep Work architecture decision and executable repository configuration;
2. tests and generated artifacts that enforce that configuration;
3. the nearest approved `AGENTS.md` and package `CONTRIBUTING.md`;
4. this proposal and other accepted engineering plans;
5. patterns observed in pinned reference repositories; and
6. informal prose, examples, or personal preference.

**For an external LangChain/LangSmith contract:**

1. an accepted live-contract spike against pinned client and server versions;
2. the installed public API, generated schema, or generated client for those versions;
3. official version-matched documentation;
4. public upstream tests and reference implementations; and
5. undocumented upstream internals, examples, or inference.

An upstream implementation detail never becomes a Deep Work API merely because it exists in a reference checkout. If official prose, generated schemas, and package behavior disagree, the owning feature stays gated until a pinned-package/live-contract spike resolves the conflict.

## 3. Repository and package method

### Proposed ownership layout

```text
deepwork/
├── apps/
│   ├── api/                    # Python application service and worker entry points
│   ├── web/                    # Next.js web application and installable PWA
│   └── desktop/                # Tauri host; native bridge, packaging, updater
├── packages/
│   ├── agent/                  # independently deployable Python Deep Agents project
│   ├── domain/                 # pure TypeScript application identities and view models
│   ├── sdk/                    # typed client for the Deep Work application API and stream
│   └── ui/                     # accessible React components, tokens, and stories
├── internal/
│   ├── adapter-tests/          # private TypeScript DTO/reducer/client conformance
│   ├── fixtures/               # language-neutral, credential-free golden scenarios
│   └── tsconfig/               # shared TypeScript compiler profiles
├── docs/                       # architecture, plans, contributor and user documentation
├── .github/                    # workflows, templates, ownership, security automation
├── Makefile                    # stable cross-language façade; fans out, contains no product logic
├── package.json                # private pnpm/Turbo orchestration root
├── pnpm-workspace.yaml
├── pnpm-lock.yaml
└── turbo.json
```

Python packages that can deploy, publish, or resolve dependencies independently own their own `pyproject.toml`, `uv.lock`, `Makefile`, README, source tree, and tests. The repository should not force one root Python environment across `apps/api` and `packages/agent`; their deployment and upstream constraints differ. The root Makefile fans out to package Makefiles, as the Deep Agents reference does.

TypeScript packages share one pinned pnpm lock and Turbo graph. A shared TypeScript configuration may provide defaults, but every package owns its build, export, and test contract.

### Dependency direction

```text
apps/web ───────► packages/sdk ─────► packages/domain
     │                  │
     └──────────► packages/ui ──────► packages/domain

apps/desktop ───► exact trusted hosted apps/web origin + a narrow native capability bridge

apps/api ───────► application ports ─► provider adapters ─► official SDKs

packages/agent ─► Deep Agents ───────► LangChain/LangGraph public APIs

internal/fixtures ─► language-neutral schemas/transcripts only; never production package code
apps/api tests ─► Python source-adapter public ports; never adapter internals
internal/adapter-tests ─► TypeScript SDK/domain public interfaces; never implementation internals
```

Rules:

- `packages/domain` is pure, browser-safe TypeScript. It imports no app, React, SDK, provider, environment, Node-only, or generated transport module.
- `packages/ui` may use domain view types but never calls HTTP, reads credentials, imports provider SDKs, or owns source capability logic.
- `packages/sdk` owns transport clients, generated wire types, stream decoding, query/mutation services, and mapping to domain models. It has no React dependency unless a deliberately separate React entry point is later approved.
- `apps/web` composes packages and owns routes, React state, session presentation, and responsive experiences. It does not become a second application backend.
- `apps/desktop` owns Tauri commands and OS integration only. Product rules stay in shared web/domain packages, and secret-bearing native APIs are exposed through a minimal typed bridge.
- `apps/api` owns application use cases, persistence, credentials, cross-source aggregation, jobs, and provider adapters. Route handlers translate; they do not contain provider logic.
- `packages/agent` is independently deployable. It must not import application-service internals or assume a particular Deep Work tenancy implementation.
- Provider-specific types stop at an adapter boundary. Presentation components must never branch on a provider class or raw upstream payload.
- Circular dependencies are forbidden. A dependency-direction check runs in CI, and an exception requires an architecture decision.

### Package anatomy

Every owned package should have:

- a one-paragraph responsibility statement and explicit non-responsibilities;
- public entry points rather than deep imports;
- exact local setup, format, lint, type, and test commands;
- unit tests beside or structurally mirroring source modules;
- an owner/reviewer path in `CODEOWNERS` once maintainers exist;
- a changelog strategy if externally versioned; and
- the nearest `AGENTS.md` with package-specific rules, allowed dependencies, and verification commands.

Prefer a new module in an existing owner over a new package. Create a package only when it needs an independent dependency boundary, deployment/release lifecycle, public API, or reusable conformance surface.

## 4. Stable command contract

The exact implementation may fan out through Make and Turbo, but contributors should see one predictable vocabulary.

```bash
make bootstrap       # install pinned toolchains/dependencies; no hidden network after completion
make doctor          # report versions and missing optional capabilities without changing state
make dev-demo        # start fixture API + web with no credentials
make format          # write formatting changes
make format-check    # check formatting only
make lint            # static lint, no writes
make typecheck       # all type systems
make test            # credential-free unit suites
make contract        # generated-schema and adapter conformance suites
make integration     # explicit network/service tests; never implied by make test
make e2e             # browser acceptance against fixture services
make build           # production builds and Python distributions
make package-check   # install packed artifacts in clean consumers
make check-architecture # package/layer/domain/browser/provider structural rules
make check-docs      # links, indexes, IDs, living sections, and generated drift
make check           # required local pre-PR suite, excluding secret-bearing integration/evals
```

Every root command must have a package-scoped equivalent. A Python contributor can run `make -C apps/api test`; an agent contributor can run `make -C packages/agent lint`; a frontend contributor can use `pnpm --filter ./apps/web test`. CI should print the local reproduction command on failure.

Root orchestration must not hide different semantics behind the same name. In particular, `test` never makes paid API calls, and `format-check` never writes.

## 5. Python conventions

### 5.1 Runtime and dependency management

- Python 3.12 is the initial application-service and deployment target. Each independent package declares its own supported range in `requires-python`; contributors and CI follow the package declaration instead of assuming the system interpreter.
- Use `uv` for installation, resolution, running, locking, and building. Do not mix `pip`, Poetry, Conda, or manually activated ad-hoc environments into documented workflows.
- Commit one `uv.lock` per independently resolvable Python project and run with `UV_FROZEN=true` in CI. A lock change must be attributable to the package whose dependencies changed.
- Use `[tool.uv.sources]` for editable local relationships when a Python package genuinely depends on another local Python package. Do not smuggle application imports through `PYTHONPATH`.
- Put runtime requirements in `[project.dependencies]`, test/lint/type requirements in dependency groups, and optional provider support in named extras only when it changes installed capability.
- A direct dependency needs a reason, active maintenance evidence, compatible license, and an owner. Prefer LangChain/LangGraph public abstractions and standard-library features over thin local wrappers.
- Never use an alpha/private-beta package as the unguarded v1 baseline. Pin it, detect the capability at runtime, isolate it behind an adapter, and provide a supported fallback.

### 5.2 Package-local configuration

Use the upstream package closest to the code's job as the starting preset:

- `packages/agent` starts from the pinned Deep Agents package: Ruff formatting/linting, absolute imports, Google docstrings, pytest with automatic asyncio discovery, disabled sockets for unit tests, and `ty` for static checking.
- `apps/api` starts from LangChain core/v1 discipline: Ruff plus strict `mypy`, `pydantic.mypy`, deprecated-code reporting, and unreachable-code warnings. The service has heavier Pydantic and framework boundaries, so strict mypy is the clearer enforcement baseline.

Do not force the two packages to share every Ruff ignore or line length. Package-local executable config is authoritative. Consistency in public behavior and test vocabulary matters more than pretending an agent graph and a FastAPI service are the same kind of package.

### 5.3 Formatting, imports, and lint suppressions

- Ruff is the sole Python formatter and linter. Enable docstring code formatting.
- Production Python has complete parameter and return annotations. `Any` requires a narrowly scoped boundary and a comment explaining why validation cannot narrow it.
- Use absolute imports across package modules. Relative imports are disallowed outside a documented package-internal exception.
- Prefer modern built-in generics and unions supported by the package's minimum Python version.
- Use `# noqa: RULE` on the exact line with a reason for an exceptional suppression. Use per-file ignores only for categorical policies such as tests allowing `assert` and omitting public docstrings.
- Do not solve lint failures by globally weakening a rule. Rule changes require representative before/after examples in the PR.
- Remove dead/commented code. No bare `except`, dynamic `eval`/`exec`, or untrusted `pickle`.

### 5.4 Public Python APIs

- A public symbol is one intentionally exported from a package entry point and documented. Use explicit `__all__` and ship `py.typed` for importable typed packages.
- Keep internal modules private by name and avoid re-exporting third-party implementation types.
- New parameters on a public callable are keyword-only unless positional use is an intentional, documented API decision.
- Public signatures, argument names, and return shapes are compatibility commitments. A change requires a breaking-change classification even before 1.0; do not silently alter them because internal call sites still pass.
- Experimental APIs use a visible `Experimental` marker in documentation and a capability/feature flag where behavior can reach users. Beta status is not a substitute for an exit or fallback plan.
- Deprecation has an alternative, warning category, removal release, tests, and migration note. Deep Work can use shorter pre-1.0 windows than LangChain, but the window must be explicit.
- Google-style docstrings document purpose, arguments, return values, raised exceptions, and non-obvious side effects. Types remain in signatures. Use American English and single-backtick code references.

### 5.5 Choosing a Python data abstraction

| Need | Default | Do not use it for |
|---|---|---|
| HTTP request/response, versioned event, settings validation, serialized boundary | Pydantic v2 model | incidental internal values or SQL persistence models |
| LangGraph state, tool payload, callback/config mapping that must preserve dictionary semantics | `TypedDict` with explicit optionality | runtime validation of untrusted JSON |
| Pluggable source, sandbox, notification, artifact, or credential behavior | `typing.Protocol` | objects selected only by a growing `if provider == ...` chain |
| Small immutable internal value with no wire validation | frozen, slotted `dataclass` | public wire schemas or mutable ORM entities |
| Persisted relational row | SQLAlchemy 2 declarative model | HTTP response or agent graph state |
| Finite public discriminator | string `Literal`/enum plus forward-compatible unknown handling | provider classes or presentation labels |

Conversion happens once at a boundary. Do not make one class simultaneously represent a SQL row, HTTP response, upstream runtime record, and UI model.

### 5.6 Async, cancellation, and resources

- External I/O is async-first in `apps/api` and agent tools. A synchronous provider call runs in a bounded worker only at an adapter boundary.
- Use structured concurrency for sibling work. Every spawned task has an owner, deadline, cancellation path, and observed exception.
- Propagate cancellation. Do not catch and suppress `CancelledError`; shield only the smallest durability-critical write and document why.
- Apply deadlines at use-case or adapter boundaries and convert timeouts into stable application error codes. Avoid nested arbitrary timeouts.
- Use async context managers for database sessions, clients, streams, sandboxes, files, and subprocesses. Tests assert cleanup after cancellation and failure.
- Backpressure is explicit for streams and queues. Do not create unbounded in-memory queues for run events, terminal output, or notifications.

### 5.7 Errors, configuration, and logs

- Domain/application errors have stable machine codes and safe user messages. Provider exceptions are retained as causal diagnostics but translated before crossing the HTTP boundary.
- HTTP handlers map errors centrally to one versioned error envelope containing `code`, `message`, optional safe `details`, `request_id`, and retry guidance. Stack traces and provider response bodies never reach clients.
- Define exception message strings in a `msg` variable where the package Ruff configuration requires it. Never use a bare `except`.
- Load environment variables once in the composition root through typed Pydantic settings. Domain and use-case modules receive configuration explicitly; they never call `os.getenv`.
- Configuration distinguishes a credential reference from credential material. Secret values are redacted from repr, logs, metrics, fixtures, traces, and error payloads.
- Use structured logs with request, actor, tenant, source, thread, and run identifiers where available. Do not log prompts, tool arguments, files, tokens, or upstream payloads by default.

## 6. TypeScript, React, and Next.js conventions

### 6.1 Toolchain and compiler baseline

- Pin an exact pnpm 10.x release through `packageManager` and use Corepack. Commit one root `pnpm-lock.yaml`; CI installs frozen.
- Use Node.js 24 for development and CI at launch. Add another supported version only when Deep Work publishes a package that promises it; do not inherit LangChain.js's Node 20/22, browser, Deno, Bun, CommonJS, and edge-runtime compatibility matrix by default.
- Use pnpm workspaces and Turborepo for the TypeScript dependency graph, affected tasks, cacheable builds, and downstream checks.
- Target ES2022, use ESM, `module: ESNext`, bundler resolution, strict mode, `isolatedModules`, `noImplicitReturns`, `noFallthroughCasesInSwitch`, `noUncheckedIndexedAccess`, and consistent casing.
- Set `allowJs: false` for product packages. Keep `skipLibCheck: false` in the contract/type CI profile. The broader LangChain.js repository relaxes these for compatibility breadth; a new application should begin stricter.
- Use Oxfmt and Oxlint as the formatting/linting baseline. Add React, Next.js, hooks, and accessibility checks not covered by the base rules; do not introduce a second formatter.
- `tsc --noEmit`, Next production builds, and package export tests remain separate gates. A bundler succeeding is not proof the public types are sound.

### 6.2 Modules, names, and exports

- Use named exports. Default exports are allowed only where Next.js requires them for `page`, `layout`, `loading`, `error`, and related framework files.
- Framework-neutral `domain` and `sdk` modules use explicit `.js` extensions in relative ESM imports, matching LangChain.js package practice.
- Public imports come through declared package export maps. Deep imports into another package's `src/`, generated folder, or internal module are forbidden.
- Keep one obvious public `index.ts` per export surface; do not create barrel chains that hide cycles or pull server-only code into browsers.
- `domain`/`sdk` filenames may follow LangChain.js-style `snake_case.ts`; React application and UI component files may use `kebab-case.tsx` with PascalCase component symbols. Each package records one rule and enforces it; renaming for aesthetic uniformity is not a reason to blur package idioms.
- Avoid `any`, unsafe assertions, non-null assertions, and TypeScript enums at external boundaries. Narrow `unknown` with schemas or type guards.

### 6.3 Environment boundaries

- Only a small, typed environment module reads `process.env`. Test files and build configuration are the only other exceptions.
- Mark server-only modules and fail a build if they enter the client graph. Credential values, database clients, provider SDKs, file-system APIs, and privileged Tauri commands are never browser imports.
- Browser environment variables require an explicit public allow-list. No secret is made public by a naming convention alone.
- Next.js route handlers may perform web-specific session exchange or same-origin proxy work approved by the architecture. They do not own persistence, provider aggregation, jobs, or a shadow copy of FastAPI business logic.
- Edge-runtime deployment is opt-in per route after compatibility tests. Node is the default server runtime.

### 6.4 Wire validation and Zod

- Use Zod v4 at untrusted TypeScript boundaries: persisted browser data, native bridge responses, push/deep-link payloads, and any response not already decoded by the generated SDK.
- Do not support Zod v3 and v4 simultaneously. LangChain.js needs dual-version compatibility for a public ecosystem; Deep Work does not.
- Generated OpenAPI types describe the wire. Handwritten Zod/domain schemas may add client-side invariants but must not become a competing definition of the same HTTP payload.
- A decode failure is observable and recoverable: capture the schema version and safe field path, reject the payload, and show a stable refresh/reconnect state. Never cast a malformed payload into the expected type.

### 6.5 React and App Router

- Server Components are the default for static shell, public documentation, and server-owned initial reads. The live task console, composer, approvals, terminal, diff, and offline state are explicit Client Component islands.
- Fetch application data through `packages/sdk` query/mutation services. React components do not construct endpoint URLs or call raw provider SDKs.
- Keep the live stream as a separate normalized service/reducer from ordinary queries and mutations. A React streaming hook binds the service to lifecycle; it does not become the only API client.
- Treat URL state as the owner for navigable search/filter/selection state, the query cache as owner for server state, a reducer as owner for ordered stream state, and local component state as owner for ephemeral interaction. Do not mirror the same value across stores.
- Prefer composition and explicit slots over large boolean-prop components. Provider/source differences enter components as capabilities and normalized view models.
- Derive values during render where possible. Effects synchronize with external systems, not recompute local values or orchestrate business workflows.
- Every async screen defines loading, empty, partial, stale, reconnecting, offline, denied, and error behavior. Suspense is not a substitute for the full state matrix.
- Preserve semantic HTML, focus order, labels, reduced motion, contrast, keyboard operation, screen-reader announcements, and touch targets in the component contract—not as final QA polish.
- Components shared by desktop and mobile web use responsive variants and capability props. Desktop-native and future React Native views share domain/SDK packages, not DOM components.

### 6.6 Rust and Tauri conventions

- Pin a stable Rust toolchain with `rust-toolchain.toml`; record the Rust edition and minimum supported Rust version in `apps/desktop/README.md`. Nightly features require a reviewed architecture decision and must not become a transitive default.
- Use `cargo fmt --check`, Clippy with warnings denied in CI, Cargo unit/integration tests, locked builds, license review, vulnerability/advisory audit, and clean platform packaging. Print exact local reproduction commands.
- Organize Rust by host capability—bootstrap/session handoff, deep link, tray, notification, secure storage, updater, window lifecycle—not by copied product feature. Product state and provider logic remain in web/API packages.
- Generate or structurally test the TypeScript/Rust bridge. Validate both sides of each IPC boundary; Rust commands accept narrow typed values and never generic URL, shell, file, or header forwarding.
- Tauri capability files declare exact windows/webviews, commands, plugins, platforms, and remote URL patterns. A wildcard remote origin, generic shell/filesystem plugin, or provider credential requires rejection, not a lint suppression.
- Fixture qualification uses an explicit local trusted origin and prohibits external/provider traffic. Loopback fixture API/worker/object/telemetry traffic is expected and separately namespaced.
- Signing/notarization/updater secrets exist only in protected release infrastructure. Platform packaging, updater signature, downgrade/rollback, and support-window evidence are release gates.

## 7. Schema, API, and event authority

### 7.1 Single-source rules

| Contract | Authority | Generated consumers |
|---|---|---|
| Deep Work HTTP requests, responses, errors, and pagination | versioned Pydantic v2 models exposed by FastAPI OpenAPI | `packages/sdk/src/generated/` TypeScript client/types; API reference docs |
| Normalized Deep Work stream event envelope and event variants | versioned Pydantic discriminated union plus committed JSON Schema | TypeScript decoder/types, fixture validation, event reference docs |
| Database structure | Alembic migration history | SQLAlchemy models checked against migrations; never client types |
| UI/domain state | handwritten `packages/domain` types and reducers | web/UI view models; never direct HTTP serialization authority |
| Upstream LangGraph/LangSmith data | pinned official SDK/public generated contract | Python provider adapter only; raw records never become product domain objects |
| Native desktop bridge | explicit Tauri command/event schema | generated or checked TypeScript bindings and Rust tests |

The Python service is the authority for the application's HTTP and normalized event wire because it owns that boundary. TypeScript code is generated, then wrapped by handwritten SDK mappers; generated files are never hand-edited. `packages/domain` may intentionally differ from wire types to express view-safe identities and states.

### 7.2 Contract-change procedure

1. change the authoritative Pydantic/event model and compatibility tests;
2. classify additive, behavioral, experimental, or breaking impact;
3. regenerate OpenAPI, JSON Schema, TypeScript artifacts, examples, and reference docs with one command;
4. inspect the generated diff and run both Python and TypeScript contract suites;
5. add a Changeset or release classification for affected public TypeScript packages;
6. add migration/rollout behavior when old clients or persisted payloads remain possible; and
7. prove a second regeneration produces no diff.

Unknown fields in external provider data are tolerated at the adapter boundary where safe. Unknown discriminators in Deep Work's own public event stream produce an explicit `unknown_event` diagnostic rather than an application crash or silent drop. Required semantic changes use a versioned event or endpoint, not field reuse.

Raw reasoning, tool arguments, files, and untrusted Markdown are classified content, not harmless JSON. Schema validation does not replace authorization, redaction, size limits, content sanitization, or provenance.

## 8. Adapter method and conformance tests

Deep Work should adapt providers the way LangChain tests integrations: one small public protocol, provider implementations behind it, and a reusable capability-aware suite.

### Adapter requirements

- Define ports in application-owned modules with application language: source, thread, run, checkpoint, interrupt, artifact, sandbox, schedule, and credential reference.
- Keep official SDK calls inside provider adapters. Never copy SDK retry, stream replay, authentication, or pagination internals into Deep Work.
- Every adapter declares a capability manifest. Unsupported behavior returns a stable unsupported-capability result; it is not simulated as success.
- Classic LangSmith Deployment is the public baseline. A Managed Deep Agents adapter remains capability-detected and private-beta gated until a live-contract spike proves each used operation.
- Aggregate per source in the application service. Do not invent a global upstream thread-search API.
- Do not expose raw provider headers, URLs containing credentials, internal identifiers, or exception bodies to clients.

### Shared conformance method

Use one redacted, versioned, language-neutral corpus without pretending one
directory is both a Python and TypeScript project. Python source-adapter standard
tests live under `apps/api/tests/contract/sources`; each adapter supplies a factory
and evidence-bearing capability manifest. `internal/adapter-tests` is a TypeScript
project that validates generated transport, DTO mapping, domain reducers, and
client behavior against the same corpus. The harnesses own behavior assertions and
never import private adapter internals.

Minimum source-adapter contracts:

1. identity mapping is stable and source-qualified;
2. list/search pagination has deterministic continuation and no duplicate records;
3. create/invoke is idempotent under a repeated application idempotency key;
4. streaming preserves order, resumes from the documented cursor, and deduplicates reconnect replay;
5. cancellation distinguishes requested, acknowledged, unsupported, and terminal states;
6. interrupts preserve ordered `actionRequests[]`, `reviewConfigs[]`, and decisions;
7. stale checkpoint/interrupt handling fails safely;
8. auth and permission failures map to stable application codes without leaking credentials;
9. rate limits and transient failures expose retry guidance;
10. malformed/unknown upstream payloads are quarantined and observable;
11. capability-disabled tests skip with an explicit reason, while a claimed capability must pass; and
12. cleanup leaves no unowned run, sandbox, task, or client resource.

Unit conformance uses sanitized fixture transports and no sockets. Live source
conformance is a separately permissioned Python workflow against pinned packages
and test deployments. It records server/client versions, capability output,
request/response schema hashes, and sanitized evidence; it never records tokens or
user content. Captured transcripts then exercise the TypeScript harness without
live credentials.

A second adapter cannot merge with copied provider-specific test cases alone. It must make the shared suite more precise where behaviors legitimately differ.

## 9. Testing and evaluation taxonomy

### Python

| Suite | Location/pattern | Network | Required on PR |
|---|---|---:|---:|
| Unit | `tests/unit_tests/` mirroring source | disabled | yes |
| Contract/conformance | `tests/contract_tests/` plus shared harness | disabled by default | yes for affected adapters/contracts |
| Integration | `tests/integration_tests/` | explicit, credential/service gated | selected protected workflow |
| Migration | migration upgrade/downgrade and model parity tests | local Postgres only | yes for persistence changes |
| Type/public import | mypy/ty plus import/export assertions | disabled | yes |
| Benchmark | marked benchmark suite | controlled | scheduled or regression-sensitive PR |

Use pytest with automatic asyncio discovery. Tests mirror source, are deterministic, assert failure paths, and minimize mocks. Prefer fakes at owned ports and recorded/synthetic protocol fixtures at external boundaries. Unit commands pass `--disable-socket` with only explicitly justified local Unix-socket allowances.

### TypeScript and React

| Suite | Pattern | Purpose |
|---|---|---|
| Unit | `*.test.ts` / `*.test.tsx` | pure domain, reducer, mapper, component behavior; no external network |
| Integration | `*.int.test.ts` / `*.int.test.tsx` | package or local-service integration, explicitly gated |
| Type | `*.test-d.ts` or `expectTypeOf` | exported type inference and compatibility |
| Contract | `*.contract.test.ts` | generated client, decoders, fixtures, native bridge, API parity |
| Accessibility/component | stories plus interaction/a11y tests | semantics, focus, keyboard, contrast states |
| End to end | Playwright specs | complete fixture and selected live user journeys |

Do not duplicate implementation logic in tests. A reducer test consumes the same normalized event fixture as Python. A browser test asserts user outcomes and visible recovery, not internal hook calls.

### Evals are not unit tests

Agent quality evaluation belongs in a distinct `evals/` project or package with datasets, graders, model/config metadata, repeat counts, cost, and trace links. It should mirror Deep Agents' separation between deterministic package tests and evaluation harnesses.

- A small deterministic golden-transcript smoke can gate changes to prompts/tools when it uses fakes.
- Paid or stochastic evals run on demand, nightly, or before a release candidate; they are not silently part of `make test`.
- Compare distributions and regression thresholds, not a single pass/fail generation.
- Pin dataset version, model/profile, agent commit, provider settings, and grader independently.
- Human review remains required for subjective release gates and changes to the grader itself.

### Clean-package tests

CI must prove packages work outside the monorepo:

- build Python wheels/sdists, install each into a fresh temporary environment without editable sources, import only declared public modules, verify `py.typed`, and run a smoke invocation;
- `pnpm pack` public TypeScript packages, install tarballs in minimal ESM consumers, verify runtime exports, types, browser/server boundaries, and tree-shaking entry points;
- build Next.js and Tauri from declared package exports rather than source-path aliases; and
- fail if an artifact contains fixtures, secrets, local paths, unpublished workspace dependencies, or undeclared license material.

Coverage is a diagnostic and regression signal. Do not reward a high percentage that omits contract, failure, cancellation, permission, and responsive states.

## 10. Dependency and version policy

### Adding a dependency

A PR must state:

- the capability it provides and why existing dependencies/standard library are insufficient;
- its runtime surface and which package owns it;
- release activity, maintainer/adoption evidence, license, bundle/install impact, and known security posture;
- whether it runs on untrusted data or has network/file/subprocess access;
- its supported version range, lock update, and removal/fallback plan; and
- the test that proves the boundary.

Thin wrappers, overlapping utilities, provider-specific SDKs in UI code, and dependencies used for one trivial function should be rejected by default.

### Pins and updates

- Lock every deployed application exactly through its package lock. Declare compatible direct dependency ranges in publishable manifests.
- Group LangChain/LangGraph/Deep Agents updates so their compatibility is tested as one change, but keep unrelated dependency churn out of feature PRs.
- Renovate/Dependabot opens scheduled groups; security patches may bypass the schedule but not tests.
- Every upstream agent/runtime SDK bump runs adapter conformance, golden event fixtures, and a live-contract canary when the integration is enabled.
- Pin GitHub Actions by full commit SHA and record the human-readable version in a comment.
- Verify model IDs in official provider documentation when examples change. Do not turn a current model name into an application default without a separate compatibility decision.
- Vendor code only when there is no supported package path, with license/provenance headers, a documented divergence reason, security ownership, and an upstream-parity test.

### Compatibility posture

Before 1.0, Deep Work promises documented migration notes and deliberate versioning, not indefinite compatibility. Specifically, it should not adopt these upstream burdens unless product demand proves them necessary:

- CommonJS, Deno, Bun, legacy Node, or broad edge-runtime support;
- multiple Zod major versions;
- obsolete Python versions or parallel Pydantic major versions;
- historical provider aliases and undocumented import paths;
- copied LangGraph/LangSmith protocol internals; or
- fallback behavior that hides an unsupported capability.

This is the central balance: copy the maintenance discipline, not the maintenance surface.

## 11. CI, release, and change management

### Required CI graph

Run independent jobs in parallel where possible, then a single required summary gate:

1. repository policy: formatting, lint, title/scope, lock integrity, generated-file drift, dependency graph, secret scanning;
2. `apps/api`: Ruff, strict mypy, unit, contract, migrations, build, clean-wheel install;
3. `packages/agent`: Ruff, `ty`, unit, deterministic agent contracts, build, clean install;
4. TypeScript: Oxfmt, Oxlint, strict typecheck, unit/type/contract tests, package builds;
5. web/UI: Next production build, component accessibility, fixture render, Playwright smoke;
6. desktop: pinned stable Rust, rustfmt, Clippy, Cargo tests, dependency/advisory audit, generated bridge parity, Tauri capability review, and signed-build smoke where credentials are available;
7. docs/architecture: indexed links, living-plan sections, freshness, generated views, feature/acceptance/issue IDs, package/layer graph, and deliberate boundary fixtures; and
8. affected downstream checks based on the dependency map.

Frozen installs are mandatory. Unit jobs run without secrets and fail on external sockets. Secret-bearing integration jobs use protected environments, least-privilege test tenants, time limits, concurrency limits, and sanitized artifacts. Forked PRs never receive repository secrets.

### Releases

- Use Changesets for externally versioned TypeScript packages and user-visible package behavior. CI requires a Changeset or an explicit `no-release` classification.
- Use release-please-style Conventional Commit history for any Python package intentionally published to PyPI, matching Deep Agents practice. Until publication is approved, `apps/api` and the deployable agent artifact are built and tagged but not accidentally published.
- Version and release the web/desktop product independently from public libraries. Every desktop build records its web compatibility range and API schema version.
- Build once and promote the same immutable artifact. Generate an SBOM, provenance/attestation, checksums, changelog, migrations, and rollback instructions before stable release.
- Release notes describe user outcomes, capability gates, migrations, and known limitations. Generated entries are curated; internal file lists are not release notes.
- Lockfile-only churn must not accidentally fan out package releases. Release automation scopes by package paths and tests this behavior before it becomes required.

## 12. Security, documentation, and accessibility are code conventions

### Security baseline

- Treat prompts, model output, Markdown, diffs, terminal output, files, connector data, URLs, and provider error text as untrusted.
- Never execute or render active content merely because an agent produced it. Sanitize Markdown/HTML, restrict URL schemes, isolate previews, and make command execution an explicit sandbox capability.
- Keep credentials server-side or in approved OS secure storage. The browser receives credential status and capability, not secret values or server `authRef` identifiers.
- Authorize every resource by tenant/workspace/actor and source. A valid external runtime identifier is not authorization.
- Apply request, upload, artifact, stream, and log size limits. Quarantine/scanning requirements are part of attachment and artifact contracts.
- Threat-model auth, GitHub installation, sandbox/proxy, desktop bridge, updater, deep-link, and untrusted-content changes before implementation-ready status.
- Maintain `SECURITY.md`, private disclosure instructions, supported versions, incident ownership, dependency review, SAST, secret scanning, and periodic DAST. Security findings never enter public issue templates before triage.

### Documentation baseline

- A user-visible feature includes user docs, recovery behavior, capability/fallback notes, and screenshots or recordings where interaction is the contract.
- A public code surface includes API reference, one minimal executable example, one realistic example, and migration notes when changed.
- Examples run in CI or are compiled/typechecked. Copyable snippets must use supported public imports and current verified model identifiers.
- Architecture decisions describe context, decision, alternatives, consequences, and revisit triggers. They do not rewrite history when a decision changes.
- Use the canonical product glossary consistently: task/thread/run/checkpoint, agent/assistant/deployment/source, environment/snapshot/sandbox, interrupt/approval/decision, file/artifact/attachment, and org/workspace/tenant/actor.
- Document experimental and private-beta capabilities next to the control that exposes them. A feature flag without user-visible status is not documentation.
- Keep root `AGENTS.md` a concise map; detailed rules live in the nearest canonical document or nested instruction. Stable product specifications, the release roadmap, and living implementation ExecPlans are distinct artifacts.
- Generated docs state generator, source, command, and last source commit. Hand edits fail CI. Change-aware freshness flags governing docs when owned code/schema paths move after their last verified commit.
- Maintain an evidence-backed `QUALITY_SCORE.md` and owned debt tracker. Recurring gardening may repair bounded drift or open follow-ups; it cannot rewrite accepted scope or lower a gate.

### Accessibility baseline

- WCAG 2.2 AA is the product target for web/PWA experiences.
- Keyboard, screen-reader, reduced-motion, zoom/reflow, high-contrast, focus restoration, live-region, and touch behavior are acceptance criteria for every interactive component.
- Automated a11y checks run in components and critical E2E journeys, but manual keyboard and screen-reader checks remain release gates.
- Loading, streaming, reconnect, approval, terminal, diff, and notification experiences announce meaningful state without flooding assistive technology.
- Accessibility regressions are product regressions and receive the same ownership and release treatment as functional regressions.

## 13. Branches, commits, pull requests, and review

### Branches and titles

Use the Deep Agents/LangChain shape:

```text
<github-user>/<scope>/<short-kebab-description>
```

Examples:

```text
sam/api/normalize-source-errors
alex/agent/add-research-rubric
lee/web/reconnect-task-stream
```

Pull request and squash-commit titles use Conventional Commits with a mandatory scope:

```text
feat(api): add source capability endpoint
fix(sdk): preserve ordered approval decisions
test(agent): cover cancellation during tool execution
docs(contributing): add fixture adapter tutorial
```

Initial scopes: `api`, `agent`, `domain`, `sdk`, `ui`, `web`, `desktop`, `fixtures`, `docs`, `deps`, `infra`, and `repo`. Multiple scopes require an explicit allowed syntax and should remain rare.

Start descriptions after `type(scope):` with lowercase text except proper nouns or a named symbol. Put issue closing syntax in the body, not the title. Breaking changes use the repository's accepted Conventional Commit marker and a migration note.

### Pull request body

Use a short opening block:

```markdown
Closes #123

Plain-English user or contributor outcome.

---

Why this change is needed, why this boundary is appropriate, risks, and review focus.
```

The PR should:

- explain **why**, not narrate every file;
- identify public/schema/security/capability impact;
- state commands run only when coverage is non-obvious or consequential;
- include before/after interaction evidence for UI changes;
- disclose meaningful AI-agent assistance, including what the author personally verified;
- avoid stale line-number citations and enormous generated prose; and
- remain focused enough to review, revert, and release as one change.

### Review rules

- The package owner reviews implementation; a boundary owner reviews schema, security, persistence, or dependency-direction changes.
- Generated files are reviewed through their source diff and drift check, not line-by-line as handwritten code.
- Public API changes require compatibility review. Security-sensitive changes require a threat-model/security reviewer. Accessibility-sensitive components require interaction review.
- A reviewer can reproduce the package command without private credentials. If not, the PR supplies a deterministic fixture or the change is not ready for community review.
- No self-merge of a public contract, auth boundary, migration, updater, sandbox policy, or release workflow until the maintainer model explicitly allows it.

## 14. Contributor experience and good-first issues

### The 15-minute path

The public contribution guide should make this sequence real from a clean clone:

```bash
make doctor
make bootstrap
make dev-demo
```

The contributor opens the printed local URL, sees a fixture workspace with at least one task, stream, approval, artifact, and failure/reconnect state, then follows one package-specific change:

```bash
pnpm --filter ./apps/web test
# or
make -C apps/api test
# or
make -C packages/agent test
```

Requirements:

- no LangSmith, model-provider, GitHub, database-cloud, signing, or notification credential;
- one supported local database/fixture command with seeded deterministic data;
- useful `doctor` output for Node, pnpm, Python, uv, Rust/Tauri optionality, ports, and architecture;
- startup output that prints URLs, fixture identity, optional capabilities, and clean shutdown command;
- a dev container/Codespaces path that runs the same commands rather than a parallel workflow; and
- no manual copying of `.env.example` merely to enter fixture mode.

Instrument this path with an opt-in contributor survey or periodic usability run; do not collect local source paths, secrets, or repository content.

### Good-first-issue standard

Apply `good first issue` only when all of these are true:

- one package owns the outcome and no unresolved product/API decision remains;
- the issue names the user/contributor outcome, likely modules, non-goals, and exact verification command;
- fixture evidence reproduces the current problem without secrets;
- expected behavior and edge cases are explicit;
- maintainers can answer questions and review promptly;
- the change is useful, not disposable busywork; and
- a new contributor can reasonably finish it without changing a public wire contract.

Use `help wanted` for broader bounded work and `design needed` for unresolved decisions. Do not disguise a discovery spike, private-beta dependency, flaky test, or security-sensitive migration as a first issue.

### Community files before launch

Publish `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, governance/maintainer expectations, support policy, issue forms, PR template, scoped labels, roadmap link, license, and an explicit policy for AI-assisted contributions. Decide any CLA/DCO requirement before launch and explain it plainly; do not surprise a contributor after they open a PR.

## 15. What to copy, adapt, and avoid

| Copy faithfully | Adapt for Deep Work | Do not copy |
|---|---|---|
| package-local ownership and commands | mixed Python/TypeScript root façade | undocumented upstream internals |
| `uv`, locks, Makefiles, Ruff, pytest | `ty` for agent and strict mypy for API | a single type checker chosen for visual uniformity |
| no-network unit tests | fixture transports representing application events | live provider calls in ordinary PR tests |
| explicit typed public exports | shorter, stated pre-1.0 compatibility windows | LangChain's full historical compatibility burden |
| core/implementation/integration/test separation | application ports/adapters and UI/domain layers | reimplementing official SDK retry/replay/deploy behavior |
| standard adapter test suites | capability-aware source and sandbox conformance | provider-specific tests copied per adapter |
| pnpm/Turbo, strict ES2022 ESM | one Node 24 application support target | CJS/Deno/Bun/multi-Node matrix without demand |
| Oxfmt/Oxlint and named exports | Next-required default exports and React/a11y checks | Biome plus Oxfmt or multiple format authorities |
| unit/integration/type test naming | Playwright and responsive UI acceptance | unit tests that duplicate reducer/business logic |
| scoped Conventional Commits and branches | scopes that match Deep Work package ownership | vague `fix stuff` titles or issue IDs as scope |
| Changesets/release-note discipline | Changesets for TS; Python-native release tooling | forcing JS release tools onto Python distributions |
| public API compatibility review | deliberate early evolution with migrations | silent breaking changes or indefinite beta excuses |
| separate agent evaluation harness | product-specific datasets and human review | treating one stochastic eval as a deterministic unit test |

Also avoid copying official LangGraph SDK streaming internals, LangSmith deployment CLI behavior, beta Deep Agents internals, arbitrary Managed Deep Agents connector routes, or a global thread-search abstraction. Depend on supported public APIs and prove their behavior through contract tests.

## 16. Enforcement rollout

### Stage 0 — architecture and knowledge review — complete

- Accept the architecture/package map, source precedence, tool choices, public support matrix, and release ownership.
- Resolve naming/scope, Python publication, CLA/DCO, and license-policy decisions.
- Record deviations from current canonical monorepo plans, especially Biome, root Python workspace assumptions, and SDK/provider ownership.

Exit: accepted decision records and merge-map entries; no runtime enforcement yet.

### Stage 1 — repository scaffold

- Add root/package Makefiles, exact toolchain pins, package manifests/locks, shared TS profiles, Oxfmt/Oxlint/Ruff/type/Rust configs, and the named UI-harness/product-demo fixture modes.
- Add package READMEs and staged `AGENTS.md` files with exact commands.
- Add root `ARCHITECTURE.md`, the canonical documentation taxonomy, living ExecPlan template, machine-readable architecture graph, generated views, quality score, and owned debt tracker.
- Make `make doctor`, `bootstrap`, `dev-demo`, `format-check`, `lint`, `typecheck`, `test`, `check-architecture`, and `check-docs` truthful.

Exit: clean-clone fixture journey and package-scoped CI are green without secrets.

### Stage 2 — first application contracts

- Establish Pydantic/OpenAPI/event authorities and deterministic generation.
- Add the TypeScript generated client wrapper, domain mapping, error envelope, schema drift check, and clean-package tests.
- Turn off raw endpoint use from React and provider types outside Python adapters.

Exit: intentional schema break fails Python, generated-diff, SDK contract, and consumer tests.

### Stage 3 — adapter discipline

- Introduce the source port/capability manifest and shared conformance harness.
- Make classic deployment adapter pass as baseline; keep private-beta adapters gated.
- Add sanitized live-contract canaries with pinned evidence.

Exit: an adapter cannot claim a capability it fails to demonstrate.

### Stage 4 — public contribution readiness

- Publish community/governance/security files, issue forms, PR lint, CODEOWNERS, release workflows, docs checks, and good-first issues.
- Run timed contribution exercises with at least one person unfamiliar with the repository.
- Require accessibility, package install, supply-chain, and release gates.

Exit: two independent clean-clone trials complete a useful change and its package checks in the documented flow.

### Stage 5 — post-1.0 compatibility

- Freeze documented public boundaries, publish support windows, and require deprecation/migration policy.
- Expand environment matrices only from observed contributor/user demand.
- Track conformance and evaluation trends across releases.

Exit: stable releases can be reproduced, promoted, rolled back, and supported from tagged source and immutable artifacts.

## 17. Executable acceptance scenarios

These scenarios define completion of the conventions rollout. Command names are proposed contracts until Stage 1 implements them.

### AC-ENG-01 — credential-free first contribution

Given a clean checkout on a supported machine, when a new contributor runs `make doctor`, `make bootstrap`, and `make dev-demo`, then the fixture application starts without an `.env` file or private credential, prints its URL and capability state, and the contributor can change one fixture-backed UI behavior and pass `pnpm --filter ./apps/web test` within 15 minutes.

### AC-ENG-02 — independent Python packages

Given only `apps/api`, when CI runs its package Makefile with its frozen `uv.lock`, then format, Ruff, strict mypy with Pydantic plugin, no-socket unit tests, contract tests, distribution build, and clean-wheel import all pass without installing `packages/agent` source implicitly.

Given only `packages/agent`, the equivalent loop uses its own lock and `ty`, and does not import application-service internals.

### AC-ENG-03 — strict TypeScript package boundary

Given a deep import from `apps/web` into `packages/sdk/src/internal`, a browser import of a server-only module, an omitted local ESM extension in a framework-neutral package, or an explicit `any`, when `make lint` and `make typecheck` run, then at least one required check fails with a package-local reproduction command.

### AC-ENG-04 — deterministic schema generation

Given an additive Pydantic response field, when `make contract` runs, then OpenAPI, JSON Schema, TypeScript generated artifacts, reference docs, and fixture validation update together. A second generation produces no diff.

Given an intentional breaking field change without a version/migration and Changeset, the contract gate fails.

### AC-ENG-05 — event parity across languages

Given the same golden stream containing start, token/content, tool, interrupt batch, checkpoint, reconnect replay, completion, and unknown-event fixtures, Python validates/normalizes it and TypeScript decodes/reduces it to the expected ordered domain state. Reordered decisions or duplicate replay causes the test to fail.

### AC-ENG-06 — adapter capability honesty

Given an adapter manifest claiming resume, cancel, or ordered HITL support, when shared conformance runs, then the corresponding behavior tests are mandatory. An unsupported adapter passes only by declaring the capability unavailable and returning the stable fallback result.

### AC-ENG-07 — network-isolated unit suites

Given code that accidentally calls an external provider from a unit test, when the normal Python or TypeScript unit command runs, then socket isolation fails the test. Only explicitly invoked integration jobs may access their allow-listed test services.

### AC-ENG-08 — cancellation and cleanup

Given an in-flight upstream stream, database transaction, and sandbox operation, when the request is cancelled, then cancellation propagates, resources close, durability-critical writes either commit atomically or roll back, and no background exception or orphan task remains.

### AC-ENG-09 — install from built artifacts

Given Python wheels/sdists and pnpm package tarballs built by CI, when installed into empty consumer projects with no monorepo source aliases, then documented public imports, runtime exports, types, and one minimal invocation work. Undeclared workspace dependencies fail the gate.

### AC-ENG-10 — dependency update safety

Given a grouped LangChain/LangGraph/Deep Agents dependency update, when CI runs, then locks are frozen and scoped, source adapter conformance, event fixtures, agent tests, clean installs, and enabled live-contract canaries pass before merge. A private-beta behavior change cannot silently alter the public baseline.

### AC-ENG-11 — accessible responsive component

Given a new approval component, when component and Playwright checks run at desktop and mobile widths, then keyboard-only operation, focus restoration, accessible names, screen-reader status, reduced motion, touch target, stale/denied/error states, and automated WCAG checks pass.

### AC-ENG-12 — secure untrusted content

Given malicious Markdown/HTML, unsafe URL schemes, oversized tool output, provider error secrets, and a cross-tenant identifier, when contract/security tests run, then active content is neutralized, limits apply, credentials are redacted, and authorization denies cross-tenant access without confirming resource existence.

### AC-ENG-13 — contribution metadata

Given a PR titled `fixed stuff`, missing its required package scope, changing user-visible behavior without a Changeset/classification, or modifying a public API without compatibility review, then branch protection fails with actionable guidance. A focused, scoped PR with the correct owner approvals passes.

### AC-ENG-14 — documentation remains executable

Given a renamed public import, command, configuration key, or model example, when `make docs-check` runs, then compiled snippets, links, generated reference, terminology checks, and current-model verification identify stale documentation before merge.

### AC-ENG-15 — release reproducibility

Given a release tag, when the release workflow rebuilds in the documented environment, then source, lockfiles, schema versions, SBOM, provenance, checksums, changelog, and artifact contents correspond to the promoted release. Rollback uses the prior immutable artifact and compatible migration procedure rather than rebuilding a branch.

## 18. Accepted defaults and remaining public-launch decisions

Wave 0 accepts these engineering defaults; exact dependency pins are recorded by
the scaffold change and governance items remain required before public launch:

1. per-project Python locks and package Makefiles instead of one root Python workspace;
2. Python 3.12 for the application service and package-declared ranges elsewhere;
3. `ty` for the agent package and strict mypy/Pydantic plugin for the FastAPI service;
4. Oxfmt/Oxlint instead of the current staged Biome choice;
5. Node 24 as the initial application support target rather than an inherited multi-runtime library matrix;
6. FastAPI/Pydantic OpenAPI and Pydantic event unions as wire authorities;
7. `packages/domain` as a pure TypeScript package separate from the SDK and UI;
8. private shared adapter conformance harnesses and credential-free fixtures;
9. Changesets for public TypeScript packages and Python-native release tooling only when a Python package is published;
10. the initial branch/title scopes, AI-assistance disclosure, and reviewer requirements; and
11. the contributor agreement, license-policy, and maintainer/governance choices that cannot be inferred from reference code.

The active scaffold ExecPlan may implement these defaults. Rules not yet backed by
configuration remain planned enforcement and must not be reported as passing.
Contributor agreement, license policy details, and maintainer governance still
require explicit owner review before public launch.
