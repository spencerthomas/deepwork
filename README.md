# Deep Work

Deep Work is an open-source control surface for delegating, supervising,
approving, and verifying long-running agent work across desktop and phone.

> **Status:** A credential-free local product is runnable today. It creates a
> text task, proposes an editable plan, pauses for approval, streams honest
> progress and evidence, lets you stop a running task at any time, returns a
> prompt-specific result, and reopens completed work during the same API process.

## Run the local product

Bootstrap the API and web dependencies once, then start the API, embedded
deterministic executor, and responsive web application together:

```bash
make -C apps/api bootstrap
pnpm install
./dev
```

Open <http://127.0.0.1:3000>. The launcher requires Python 3.12, a supported
Node.js version (`>=24.14.0 <25`), and the reviewed package dependencies. Set
`DEEPWORK_NODE` to an explicit Node.js executable when it is not on `PATH`.

This experience uses the API's deterministic in-memory fixture runner. It does
not call the separately packaged LangChain/LangGraph agent runtime, choose a model,
read provider credentials, or contact an external provider. Authentication, durable
jobs, and production readiness remain unavailable. Tasks, events, evidence,
decisions, and results survive navigation and reconnects only while the same API
process remains alive; restarting it clears the local task list.

## Run with a real agent (local development)

The launcher can run a real local LangGraph Agent Server instead of the fixture
runner, so a task is planned, approved, and executed by the actual
`packages/agent` graph. This is a local-development opt-in and stays off by default.

```bash
# 1. Install the agent package and the LangGraph dev server into its venv.
uv venv --python 3.12 packages/agent/.venv
uv pip install --python packages/agent/.venv -e packages/agent 'langgraph-cli[inmem]'

# 2a. Keyless: prove the full loop with the deterministic stand-in (no provider key).
DEEPWORK_REAL_AGENT=1 DEEPWORK_AGENT_FAKE=1 ./dev

# 2b. Real model: point the agent at a provider (credential stays server-side).
DEEPWORK_REAL_AGENT=1 DEEPWORK_AGENT_MODEL=anthropic:claude-sonnet-5 \
  ANTHROPIC_API_KEY=... ./dev
```

Verify the engine independently of the web tier at any time:

```bash
DEEPWORK_AGENT_FAKE=1 python tools/smoke/agent_roundtrip.py
```

The smoke gate drives the real graph through plan → interrupt → decision →
terminal state and passes only when the engine actually turns. Real-agent mode is
in-memory (no durable task recovery yet) and requires the same supported Node.js
and Python versions as the fixture launcher.

## Start here

| Need                             | Canonical source                                                                     |
| -------------------------------- | ------------------------------------------------------------------------------------ |
| Agent instructions               | [AGENTS.md](AGENTS.md)                                                               |
| System and dependency boundaries | [ARCHITECTURE.md](ARCHITECTURE.md)                                                   |
| Product outcome and judgment     | [docs/PRODUCT_SENSE.md](docs/PRODUCT_SENSE.md)                                       |
| Program roadmap and acceptance   | [docs/PLANS.md](docs/PLANS.md)                                                       |
| Stable feature specifications    | [docs/product-specs/index.md](docs/product-specs/index.md)                           |
| Active implementation handoff    | [Wave 1 scaffold ExecPlan](docs/exec-plans/active/DW-EXEC-M1-REPOSITORY-SCAFFOLD.md) |
| Security and reliability         | [docs/SECURITY.md](docs/SECURITY.md), [docs/RELIABILITY.md](docs/RELIABILITY.md)     |
| Evidence and source pins         | [docs/references/source-ledger.md](docs/references/source-ledger.md)                 |

## Accepted stack direction

- Python 3.12 FastAPI API and worker with PostgreSQL/outbox, object storage, and
  server-only source adapters.
- A separately installable Python Deep Agents package.
- Next.js/React/TypeScript responsive web, with pure domain, browser-safe SDK, and
  presentation-only UI packages.
- PWA enhancements only on qualified browser cells; Tauri as a gated thin desktop
  host; Expo/native mobile later.
- Classic LangSmith Deployment as the public baseline. MDA and Fleet remain
  capability-gated; unsupported routes or CRUD are not assumed.

The sibling `deep-work-frontend` repository at the accepted `26c698b` baseline is
visual and interaction evidence only. Migration is one-way into the future
`apps/web`; do not make it a dependency.

## Validate the repository

The root `Makefile` is the stable command contract; each target delegates to the
reviewed per-workspace command:

```bash
make check         # pnpm check + apps/api check + packages/agent check
make check-docs    # tools/docs generate --check + check.py
make test-unit     # TypeScript and Python unit suites
make test-contract # API contract suite
make test-e2e-demo # API-backed browser task journey
```

The underlying commands still run directly if preferred:

```bash
pnpm check
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
```

Continuous integration runs `make bootstrap`, `make check-docs`,
`make check-architecture`, `make check`, and `make test-e2e-demo` on every pull
request to `main` (`.github/workflows/checks.yml`), so the same contract gates
merges.

There is intentionally no executable `WORKFLOW.md`. Manual one-agent-per-worktree
dispatch is current until `SPIKE-SYMPHONY-001` passes.

## License and affiliation

MIT. Deep Work is an independent open-source project built for compatibility with
LangChain technologies. It is not affiliated with, endorsed by, or sponsored by
LangChain, Inc. “LangChain” and “LangSmith” are trademarks of their respective
owner and are used only to describe compatibility.
