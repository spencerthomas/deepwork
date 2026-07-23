# U1 · Monorepo scaffold

*Feature deep-dive · 2026-07-22 (rev 2026-07-23) · Milestone M0 · Status: planning*
*Parent: [../2026-07-22-001-feat-deepwork-v1-delivery-plan.md](../2026-07-22-001-feat-deepwork-v1-delivery-plan.md) · Specs: [../../plan/05-oss-setup.md](../../plan/05-oss-setup.md), [../application-architecture.md](../application-architecture.md), [../code-conventions.md](../code-conventions.md)*

> **rev 2026-07-23:** reworked to match canonical LangChain conventions (adoption goal). Lint/format is now **oxlint + oxfmt** (was biome); adds the **`internal/`** shared-package pattern, **tsdown** builds, a **uv Python workspace** (`apps/api` + `packages/agent`), and the contribution furniture (AGENTS.md/CLAUDE.md, commit conventions). See [../code-conventions.md](../code-conventions.md).

---

## Goal

Bootstrap the canonical monorepo — **two toolchains, one repo** — so every subsequent unit lands in a stable, CI-green foundation that already looks and feels like a LangChain project. After U1: `pnpm install && uv sync --all-groups` from a clean checkout, `pnpm turbo build` + `pnpm turbo test` green (TS), `make test` green (Python), CI enforcing the same gates on every PR, and Vercel previews for the web app.

Pure scaffolding — no product code. The output is the workspace graph, the shared build/lint/type/test pipeline for **both** Python and TypeScript, and the contribution furniture.

---

## Decisions taken

### D1 — Lint/format: **oxlint + oxfmt** (match langchainjs)

The adoption goal ([code-conventions.md](../code-conventions.md)) makes this non-negotiable: `langchain-ai/langchainjs` uses **oxlint** (`.oxlintrc.json`) and **oxfmt** (not Prettier). Deep Work matches. This **reverses the earlier biome choice** — which was explicitly flagged as reversible for exactly this trigger. oxlint/oxfmt applies repo-wide (libs *and* apps) so the lint/format experience is uniform for every contributor.

### D2 — Adopt the `internal/` shared-package pattern

Mirror langchainjs: shared TS config and build live in workspace packages, not root files.

- `internal/tsconfig` → `@deepwork/tsconfig` (base `tsconfig` every TS package extends).
- `internal/build` → `@deepwork/build` (tsdown wrapper producing dual CJS+ESM, mirroring `@langchain/build`).

This replaces the earlier "root `tsconfig.base.json`" idea. A LangChain JS contributor will recognize `extends: "@deepwork/tsconfig/base.json"` immediately.

### D3 — Two toolchains, one Turborepo

- **TypeScript** (`apps/{web,desktop,mobile}`, `packages/{sdk,ui}`, `internal/*`): pnpm 10.14 + Turborepo, oxlint + oxfmt, tsdown (libs), vitest, TS ^6.
- **Python** (`apps/api`, `packages/agent`): a **uv workspace**, ruff + mypy + pytest, per-package `pyproject.toml` + `uv.lock`, Makefile targets.
- Turborepo orchestrates both: Python packages expose `test`/`lint`/`type` task wrappers that shell to `uv`/`ruff`/`mypy`, so `pnpm turbo test` runs vitest *and* pytest.

### D4 — Stub every package in U1

Placeholder packages so the workspace graph and task pipeline are complete and green from day one:
- TS stubs: `packages/sdk`, `packages/ui` (real tokens already), `apps/web`, `apps/desktop`, `apps/mobile`, `internal/tsconfig`, `internal/build`.
- Python stubs: `apps/api` (FastAPI hello + one test), `packages/agent` (module + one test).

Each stub ships one trivial passing test so `test` is real. Later units turn stubs into code without touching workspace plumbing.

### D5 — Strict CI + branch protection from day one

`main` requires all gates green (TS: oxfmt-check → oxlint → typecheck → vitest → build; Python: ruff-check → ruff-format-check → mypy → pytest) plus **Conventional Commits with mandatory scope** and **Actions pinned to full-length commit SHAs** (LangChain hard rules). The **"contributor first hour" test** (clone → install → all green with zero credentials) is a CI job.

---

## Output structure (after U1)

```
deepwork/
  package.json                 # TS workspace root: turbo scripts, oxlint/oxfmt/tsdown devDeps
  pnpm-workspace.yaml          # globs: apps/*, packages/*, internal/*
  turbo.json                   # pipeline: build/test/lint/format/typecheck (TS + Python wrappers)
  .oxlintrc.json               # lint config (plugins: typescript, unicorn, node)
  pyproject.toml               # uv workspace root (members: apps/api, packages/agent)
  uv.lock                      # root lock (per-package locks too)
  .npmrc                       # pnpm: minimum-release-age, provenance
  .nvmrc                       # Node 24 (dev); CI matrix 20/22/24
  AGENTS.md                    # contributor + AI-agent guidance (mirrors langchain)
  CLAUDE.md                    # same content, Claude entrypoint
  .pre-commit-config.yaml      # per-package format+lint+version-consistency hooks
  .changeset/                  # changesets config (OIDC provenance)
  .github/
    workflows/                 # ci-ts.yml, ci-py.yml, release.yml, preview (Vercel)
    ISSUE_TEMPLATE/            # (content in U19)
    pull_request_template.md   # (content in U19)
  internal/
    tsconfig/                  # @deepwork/tsconfig — base.json
    build/                     # @deepwork/build — tsdown wrapper
  apps/
    api/                       # STUB: FastAPI app + pyproject.toml + one test (real in U7b)
    web/                       # STUB: package.json + tsconfig (real in U2)
    desktop/                   # STUB (real in U18)
    mobile/                    # STUB (real in U18)
  packages/
    agent/                     # STUB: pyproject.toml + module + one test (real in U6)
    sdk/                       # STUB: package.json + src/index.ts (real in U7)
    ui/                        # EXISTS: tokens.css, tailwind.preset.mjs (+ package.json here)
  docs/
```

> Community files (CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, issue forms, CODEOWNERS) are fully populated in **U19**; U1 creates AGENTS.md/CLAUDE.md and the CI plumbing.

---

## TypeScript side

### Root `package.json`
- `"packageManager": "pnpm@10.14.0"` (exact, matches langchainjs).
- Scripts delegate to turbo: `build`, `test`, `lint` (`oxlint .`), `format` (`oxfmt .`), `format:check` (`oxfmt --check .`), `typecheck`, `changeset`, `release`.
- Root devDeps: `turbo`, `oxlint`, `oxfmt`, `tsdown`, `typescript@^6`, `vitest`, `@changesets/cli`, `@changesets/changelog-github`, `lint-staged`.
- `lint-staged`: `"**/*.{ts,tsx}": ["oxfmt --write"]`.

### `pnpm-workspace.yaml`
Globs `apps/*`, `packages/*`, `internal/*`. Catalog centralizes the churny `@langchain/*` versions (see pins below).

### `.oxlintrc.json`
Plugins `typescript`/`unicorn`/`node`. Key rules matching langchainjs: `no-explicit-any: error`, `import/extensions: ["error","ignorePackages"]` (require `.js`), `prefer-template`, `no-var`, `prefer-const`, `no-param-reassign`. Overrides relax `no-process-env`/`no-unused-vars`/`no-explicit-any` for `**/*.test.ts` and examples. **Apps get the same base**, with framework-native exceptions noted in [code-conventions.md](../code-conventions.md) §4.

### `internal/tsconfig` (`@deepwork/tsconfig`)
`base.json`: `target ES2022`, `module ESNext`, `moduleResolution bundler`, `strict`, `noUnusedLocals/Parameters`, `declaration/declarationMap/sourceMap`, `isolatedModules`, `composite`. Packages extend it with `rootDir`/`outDir`/`references`.

### `internal/build` (`@deepwork/build`)
tsdown wrapper: dual `["cjs","esm"]`, target es2022, declaration maps, `unbundle: true` (externals stay external). Library packages' `tsdown.config.ts` calls `getBuildConfig({ entry: ["./src/index.ts"], ... })`.

### `turbo.json`
`build:compile` (`dependsOn ^build:compile`, outputs `dist/**`), `typecheck`, `test`, `lint`, `format`. Python packages register `test`/`lint`/`type` tasks that shell to `make`.

---

## Python side (uv workspace)

`apps/api` and `packages/agent` are a **uv workspace** (root `pyproject.toml` with `[tool.uv.workspace] members`). Matching langchain:

- Each package: own `pyproject.toml` + `uv.lock`, `requires-python = ">=3.11"`, build-backend `hatchling`, `py.typed`, `_version.py`.
- Dependency groups: `test`, `lint`, `typing`, `test_integration`.
- Per-package `Makefile`: `test` (uv + pytest, `--disable-socket --allow-unix-socket`, `env -u` tracing), `lint` (ruff check + ruff format --diff + mypy), `format` (ruff format + ruff check --fix), `type` (mypy).
- `[tool.ruff.lint] select = ["ALL"]` + curated ignore list; `ban-relative-imports = "all"`; `pydocstyle convention = "google"`.
- `[tool.mypy] strict = true`, `plugins = ["pydantic.mypy"]`.
- `[tool.pytest.ini_options] addopts = "--strict-markers --strict-config --durations=5"`; `tests/unit_tests/` + `tests/integration_tests/`.

Turborepo wrappers let `pnpm turbo test`/`lint` include the Python packages uniformly.

---

## CI pipeline (D5)

### `ci-ts.yml` (Node 20/22/24 matrix)
`oxfmt --check` → `oxlint` → `turbo typecheck` → `turbo test` (vitest) → `turbo build`. Plus a **zero-creds fixtures-smoke** job (boot `apps/web` with no `.env`, assert render).

### `ci-py.yml`
`uv sync --all-groups` → `ruff check` → `ruff format --check` → `mypy` → `pytest` (unit, socket-disabled). The `langgraph dev` golden-transcript tests (U5) attach here when they exist.

### Shared
Conventional-Commit title lint (mandatory scope; scopes `api`,`agent`,`sdk`,`ui`,`web`,`desktop`,`mobile`,`internal`,`docs`,`ci`,`infra`). **All Actions pinned to full-length commit SHAs.** `release.yml`: changesets (npm, OIDC provenance) for TS; uv-based release for Python packages.

---

## Version pins at scaffold (from spec + langchain reference, 2026-07)

| Package | Version | Note |
|---|---|---|
| pnpm | 10.14.0 | exact (langchainjs) |
| typescript | ^6.0.3 | libs (langchainjs) |
| tsdown | ^0.21.7 | via @deepwork/build |
| oxlint | ^1.68 | |
| oxfmt | ^0.53 | |
| vitest | ^4.1 | |
| turbo | ^2.10 | |
| `deepagents` (py) | 0.6.12 | watch 0.7.0 |
| `@langchain/react` | ^1.0.28 | catalog; weekly churn |
| `@langchain/langgraph-sdk` | ^1.9.23 | catalog |
| Python | ≥3.11 | deepagents floor |

---

## Test scenarios

- **Happy path:** clean clone → `pnpm install && uv sync --all-groups` resolves both workspaces.
- **Happy path:** `pnpm turbo build` + `pnpm turbo test` green (TS); `make -C packages/agent test` + `make -C apps/api test` green (Python).
- **Happy path:** PR triggers `ci-ts.yml` (3 Node versions) and `ci-py.yml`; all gates run.
- **Contributor first hour:** the zero-creds job boots `apps/web` and runs all tests with no `.env` — green.
- **Edge case:** a non-semantic or scope-less PR title fails the title check.
- **Edge case:** an unformatted TS file fails `oxfmt --check`; a ruff violation fails `ci-py.yml`.
- **Edge case:** an Action referenced by tag (not SHA) fails the pin check.
- **Supply-chain:** a dep inside the `minimum-release-age` window is rejected.

---

## Verification

- `pnpm turbo build` and `pnpm turbo test` exit 0; `make test` exits 0 in both Python packages.
- CI green on the scaffold PR across the Node matrix + Python job.
- A test PR generates a Vercel preview URL.
- `oxlint .` and `oxfmt --check .` pass; `ruff check` + `mypy` pass.
- AGENTS.md + CLAUDE.md exist and describe both toolchains.

---

## Open questions / deferred

- **Curated ruff ignore list** — start from langchain's, trim per package during U6/U7b.
- **Remote turbo caching** — deferred (solo v1).
- **CODEOWNERS / npm scope name** — U19 / first publish (non-`lang*` for trademark).
- **uv workspace vs per-package locks** — start with a root workspace; split if it complicates partner-style independent releases.

---

## Dependencies

- **Upstream:** none (first unit).
- **Downstream:** everything. U2 (web), U6 (agent), U7 (sdk), **U7b (apps/api backend)** turn stubs into real packages on this foundation.
