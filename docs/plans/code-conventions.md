# Deep Work — Code Conventions (LangChain-community fit)

*Conventions doc · 2026-07-23 · Status: proposed*
*Derived from the canonical LangChain repos: `langchain-ai/langchain` (Python) and `langchain-ai/langchainjs` (TS), plus their `AGENTS.md`/`CLAUDE.md`. Companion: [application-architecture.md](application-architecture.md).*

---

## Why this document exists

The launch goal is to **invite the active OSS LangChain community to contribute**. Adoption is a function of familiarity: a LangChain contributor who clones Deep Work should feel like they never left their own repo — same package manager, same linter, same test layout, same commit conventions, same docstring style. Every gratuitous difference is a small tax on contribution.

So the governing rule for all server-side and library code is:

> **Would a LangChain maintainer feel at home in this file?** If not, change the file, not the convention.

The **frontend app** is the one deliberate exception (explained in §4) — React/Next contributors are a *different* community, and forcing library-Python idioms onto a Next app would alienate them instead.

This document is the authoritative style contract. It updates several delivery-plan units (§7).

---

## 1. The two toolchains

Deep Work has a Python server side and a TypeScript client side. Each matches its LangChain counterpart exactly.

| | Python (`apps/api`, `packages/agent`) | TypeScript libs (`packages/sdk`, `packages/ui`, `internal/*`) | Frontend apps (`apps/web`, `desktop`, `mobile`) |
|---|---|---|---|
| Matches | `langchain-ai/langchain` | `langchain-ai/langchainjs` | React/Next community |
| Pkg mgr | **uv** | **pnpm 10.14** + Turborepo | pnpm (shared) |
| Lint | **ruff** (`select=["ALL"]`) | **oxlint** | oxlint (shared) |
| Format | **ruff format** | **oxfmt** | oxfmt (shared) |
| Types | **mypy** (strict) | tsc / **TS ^6** | tsc |
| Build | hatchling | **tsdown** (dual CJS+ESM) | Next / Tauri / Expo |
| Test | **pytest** | **vitest** | vitest |

**This reverses the earlier delivery-plan choice of biome** — the canonical LangChain JS toolchain is **oxlint + oxfmt**, so Deep Work uses oxlint + oxfmt. (This is exactly the "revisit if LangChain adoption is the goal" trigger written into the original U1 decision.)

---

## 2. Python conventions (`apps/api` + `packages/agent`)

Match `langchain-ai/langchain` precisely.

### Environment & packaging
- **uv** for everything — never `pip`/`poetry`/`conda`. `uv sync --all-groups`; `uv run --group <g> ...`.
- Each Python package has its own `pyproject.toml` + `uv.lock`; internal deps via `[tool.uv.sources]` editable paths.
- **Dependency groups** (not extras): `test`, `lint`, `typing`, `test_integration`.
- `requires-python = ">=3.11"` — Deep Work's floor is 3.11 (the deepagents floor), a compatible narrowing of langchain's `>=3.10`. State it once; don't pin a global interpreter.
- Build backend: `hatchling`.
- Version in **two places**, kept in sync by a pre-commit check: `pyproject.toml` `version` and `<pkg>/_version.py` `__version__`.
- `py.typed` marker in every package source root.

### Lint / format (ruff)
```toml
[tool.ruff.lint]
select = ["ALL"]           # opt-out model, like langchain
ignore = [ "COM812", "FIX", "TD002", "TD003", "ANN401", ... ]  # curate from langchain's list
[tool.ruff.lint.flake8-tidy-imports]
ban-relative-imports = "all"
[tool.ruff.lint.pydocstyle]
convention = "google"
[tool.ruff.lint.per-file-ignores]
"tests/**" = ["D1", "PLR2004", "S", "SLF"]
```
- `select = ["ALL"]` + a curated ignore list — copy langchain's ignore set as the starting point, adjust per package.
- **No relative imports.**
- Format is two-pass like langchain: `ruff format` then `ruff check --fix`.

### Types (mypy)
```toml
[tool.mypy]
plugins = ["pydantic.mypy"]
strict = true
warn_unreachable = true
```
- All functions have type hints **and** return types.
- `from __future__ import annotations` at the top of every module.
- `X | None` (never `Optional[X]`); `collections.abc` types over `typing` equivalents; `Self`/`NotRequired` from `typing_extensions`.
- New public params are **keyword-only**: `def f(a, *, new: str = "..."):`.

### Docstrings (Google style)
- Google-style with `Args:` / `Returns:` / `Raises:`; **types go in the signature, not the docstring**; don't repeat defaults; single backticks (not Sphinx double-backtick); American English; explain *why* not *what*.

### Tests
- `tests/unit_tests/` (**no network** — `--disable-socket --allow-unix-socket`, tracing env unset via `env -u`) and `tests/integration_tests/` (network OK).
- Test layout **mirrors** source layout. `pytest`, deterministic, happy + edge + error covered.
- `addopts = "--strict-markers --strict-config --durations=5"`; `blockbuster` autouse fixture to catch sync I/O in async; session-scoped fixture disabling LangSmith tracing in unit tests.
- Standard shared test suite (like langchain's `standard-tests`) for anything with multiple implementations (e.g. `AgentSource` backends).

### Security (from langchain's bar)
- No dynamic code evaluation (`eval`/`exec`) and no unsafe deserialization of user-controlled input; no bare `except:`; assign error text to a `msg` variable; ensure resource cleanup; remove commented-out/dead code before commit.

### Makefile (per package)
Standard targets so contributors get muscle memory: `make test`, `make lint`, `make format`, `make type` — each shelling to the uv/ruff/mypy invocations above, with `env -u` unsetting tracing vars for unit tests.

---

## 3. TypeScript library conventions (`packages/sdk`, `packages/ui`, `internal/*`)

Match `langchain-ai/langchainjs` precisely. These are the upstreamable, library-shaped packages.

### Packaging & build
- **pnpm 10.14** + **Turborepo**; `packageManager` pinned exactly.
- **tsdown** builds dual **CJS + ESM** with declaration maps, via a shared `@deepwork/build` wrapper (mirrors `@langchain/build`).
- Shared TS config in `internal/tsconfig` (`@deepwork/tsconfig`, base extends): `target ES2022`, `module ESNext`, `moduleResolution bundler`, `strict`, `declaration/declarationMap/sourceMap`, `isolatedModules`, `composite`.
- `package.json`: `"type": "module"`, dual `exports` map (`import`/`require` with `types`), `engines.node >= 20`, internal deps `workspace:^` (peer) / `workspace:*` (dev). Third-party deps use caret ranges, MIT/permissive only.

### Lint / format
- **oxlint** (`.oxlintrc.json`, plugins `typescript`/`unicorn`/`node`). Key rules: `no-explicit-any: error`, `import/extensions: error` (require `.js`), `prefer-template`, `no-var`, `prefer-const`, `no-param-reassign`. Test/example files relax `no-process-env`, `no-unused-vars`, `no-explicit-any`.
- **oxfmt** for formatting (not Prettier). `lint-staged` runs `oxfmt --write` on staged `.ts`.

### Code style
- **snake_case module filenames** (`agent_source.ts`, `control_plane.ts`, `stream_adapters.ts`); `index.ts` barrels; `types.ts` for types.
- **`.js` extension on all local imports** (ESM), even from `.ts` files. External imports carry no extension.
- **Named exports only** — no default exports. Barrels use `export * from "./x.js"`.
- Env vars via a `getEnvironmentVariable()` util, **never** `process.env` (outside tests).
- Typed errors: attach a `dw_error_code` (mirroring langchain's `lc_error_code`) plus a troubleshooting-URL suffix on the message; enumerate codes in one place (e.g. `MODEL_AUTHENTICATION`, `STREAM_DISCONNECT`, `HITL_STALE`).
- Support Zod v3 and v4 (`zod/v3`, `zod/v4`) where schemas are exposed.

### Tests
- **vitest**, file suffixes: `*.test.ts` (unit), `*.int.test.ts` (integration), `*.test-d.ts` (type tests). Tests live in a `tests/` folder beside the module. Type assertions via `expectTypeOf`.
- The **stream-contract golden tests** (U5) live here and gate SDK changes.

### Releases
- **changesets** with GitHub changelog + **OIDC trusted publishing** + `NPM_CONFIG_PROVENANCE: true`. Changeset markdown files describe user-visible changes in Conventional-Commit voice.

---

## 4. Frontend app conventions (`apps/web`, `apps/desktop`, `apps/mobile`) — the deliberate exception

The frontend is a Next.js/React/Expo application, and its contributors come from the React ecosystem, not langchain-core. Forcing snake_case component files or `.js`-suffixed imports onto a Next app fights the framework and **raises** the barrier for exactly the contributors this surface needs. So:

- **Shared tooling, native conventions.** Apps use the same **oxlint + oxfmt**, the same base tsconfig, and **vitest** — so the lint/format/test experience is uniform across the repo. But file/component conventions are **React/Next-native**: kebab-case files (`task-inbox.tsx`), PascalCase components, colocated hooks, `app/` router idioms.
- **No `.js`-extension imports; default-export pages where Next requires them** — follow the framework, not the library rule.
- **This is the only place the "would a LangChain maintainer feel at home" rule is relaxed**, and it's relaxed on purpose. Documented in CONTRIBUTING so it's a stated decision, not drift.

The boundary is clean: anything in `packages/*` or `internal/*` or `apps/api` follows LangChain conventions; anything in `apps/{web,desktop,mobile}` follows framework-native conventions.

---

## 5. Shared conventions (both toolchains)

### Commits & branches (exact LangChain rules)
- **Conventional Commits with a mandatory scope** — even for the main package. Lowercase after `type(scope):` unless a proper noun or named entity; wrap named entities in backticks.
  - ``feat(sdk): add `AgentSource` registry``
  - `fix(api): resolve token refresh race`
  - `chore(agent): bump deepagents to 0.6.12`
- Allowed scopes: `api`, `agent`, `sdk`, `ui`, `web`, `desktop`, `mobile`, `internal`, `docs`, `ci`, `infra`.
- **Branch naming**: `<github-username>/<scope>/<short-kebab-description>`.

### PR descriptions (exact LangChain rules)
- The description *is* the summary — no `# Summary` header. `Closes #NNN` on its own line at the top when applicable.
- Explain the *why* (user story), write for readers unfamiliar with the area, wrap entities in backticks, **don't cite line numbers**.
- Net-new/behavior-changing PRs include a `## Release note` section in release-ready language.
- Add a brief **AI-agent-involvement disclaimer** (LangChain convention).

### CI / infra
- **GitHub Actions pinned to full-length commit SHAs** (LangChain hard rule).
- Semantic-PR-title lint; per-package labelers; changesets/uv release workflows.
- **Renovate weekly**, `@langchain/*` grouped (they release weekly).

### Stable public interfaces
- Preserve exported signatures; warn on any signature change; keyword-only new params; mark experimental APIs with an admonition/warning in the docstring.

---

## 6. Repo furniture that signals "this is a LangChain-style project"

These lower the contribution barrier as much as the code style does:

- **`AGENTS.md` + `CLAUDE.md`** at the root (and the Python package), mirroring langchain's — so AI-assisted contributors get the same guidance shape.
- **`CONTRIBUTING.md`** encoding the commit/branch/PR conventions above + the dev-setup commands (`uv sync` / `pnpm install`) + the frontend-exception note.
- **`SECURITY.md`, `CODE_OF_CONDUCT.md`** (Contributor Covenant), issue forms (bug/feature), PR template, **CODEOWNERS**.
- **Per-package `README.md` + `LICENSE`** (MIT throughout).
- **Standard-tests-style** shared suites for multi-implementation seams.
- **Pre-commit hooks** per package (format + lint + version-consistency check), like langchain.

### The "contributor first hour" acceptance test
A LangChain contributor should get to green in minutes with **zero credentials**:
```
git clone … && cd deepwork
pnpm install && uv sync --all-groups
pnpm turbo test               # TS: vitest, all green (fixtures, no creds)
make -C packages/agent test   # Python: pytest, all green (no network)
make -C apps/api test
```
If any step needs a LangSmith key to pass, the barrier is too high — fixtures/mocks must carry it. (This is the same "runnable with zero credentials" invariant the delivery plan already guards via `packages/ui/fixtures`.)

---

## 7. Impact on the delivery plan (deltas to apply)

These revisions follow from adopting LangChain conventions. I'll propagate them into the affected feature docs and the master plan on your go-ahead.

| Unit / doc | Change |
|---|---|
| **U1 (scaffold)** | biome → **oxlint + oxfmt**; add **`internal/tsconfig` + `internal/build`** (tsdown) packages; TS **^6** for libs; add **uv workspace** for Python (`apps/api` + `packages/agent`); commit/branch/PR conventions + Actions-pinned-to-SHA; AGENTS.md/CLAUDE.md furniture. |
| **U2 (web import)** | Confirm the **frontend exception** (§4): apps/web keeps React/Next-native file conventions but adopts oxlint/oxfmt + base tsconfig + vitest. |
| **New: `apps/api`** | Add a **Python backend** unit (FastAPI, stateless) — the control-plane/auth/push/webhook glue moved out of Next route handlers. Slots into M1 (auth/control-plane) and M2/M3 (push, connector proxy). Follows §2. |
| **U6 (agent)** | Add the full **Python conventions** (§2): ruff `ALL`+ignore, mypy strict, Google docstrings, `from __future__ import annotations`, `tests/unit_tests`+`integration_tests` split, `py.typed`, `_version.py`, Makefile targets. |
| **U7 (sdk)** | Apply **langchainjs library conventions** (§3): snake_case modules, `.js` imports, named exports, tsdown build, `dw_error_code`, golden contract tests. Add the **backend-client** half (talks to `apps/api`) alongside the useStream adapters. |
| **U8 (auth)** | Auth logic moves into **`apps/api`** (Python); `apps/web` keeps only a thin same-origin session/callback route. |
| **U15/U16 (fleet/schedules/push)** | Control-plane + push operations are **`apps/api`** endpoints using the Python `langsmith`/`langgraph-sdk`, not Next route handlers. |

---

## 8. Divergences from LangChain we keep on purpose (and why)

Being explicit so contributors understand the intentional differences:

- **`apps/` + `packages/` layout** (not langchain's `libs/`). Deep Work is an *application* monorepo (deepagentsjs/open-swe shape), not a library monorepo. We adopt the `internal/*` shared-package pattern from langchainjs to bridge.
- **`requires-python >= 3.11`** (langchain is `>=3.10`). Driven by the deepagents floor; a compatible narrowing.
- **Frontend framework-native conventions** (§4) — a deliberate, documented exception for the React/Next surface.
- **A Python backend of our own** (`apps/api`) — langchain packages are libraries, not apps; our backend still follows their *code* conventions even though it's an application service.
