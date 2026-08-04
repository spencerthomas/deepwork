# Deep Work

Deep Work is an open-source control surface for delegating, supervising,
approving, and verifying long-running agent work across desktop and phone.

> **Status:** One credential-free golden journey is locally browser-proven:
> branded sign-in, agent choice, compose, plan review, approval, progress, useful
> result, evidence/files/trace inspection and reopen. This is not a v1 release
> claim; the four independent evidence states for all twelve release stories live
> in the [release scorecard](docs/RELEASE_SCORECARD.md).

## Hosted validation deployment

The documented web and API endpoints were publicly reachable on 2026-08-03. That
reachability is not authenticated acceptance. The protected `make test-hosted`
gate must still complete the signed-in golden journey without fixture fallback
before any scenario is marked hosted-proven in the release scorecard.

| Component | URL | Notes |
| --------- | --- | ----- |
| Web app (test here) | <https://web-brown-xi-10.vercel.app> | Next.js on Vercel; sign in at `/login` |
| Application API | `https://deepwork-api-production.up.railway.app` | FastAPI on Railway; session-authed |
| Agent runtime | `https://deepwork-agent-production.up.railway.app` | LangGraph server on Railway; called only by the API |

```text
Web UI (Vercel) → login (session cookie) → Application API (Railway)
   → LangGraph agent (Railway) → OpenRouter → model → plan → approval → result
```

### How to test

1. Open the web app and sign in at `/login` with the access key. The key is the
   `DEEPWORK_ACCESS_KEY` value set on the Railway API service (obtain it from the
   project owner or Railway → Variables; it is not committed to this repository).
2. Create a task (for example, "List two concrete benefits of writing unit
   tests"). The agent proposes a plan and pauses for approval.
3. Approve the plan. The agent executes and returns a result.

API-only smoke test (replace the placeholder with the real access key):

```bash
API=https://deepwork-api-production.up.railway.app
COOKIE_JAR=$(mktemp)
trap 'rm -f "$COOKIE_JAR"' EXIT
curl -s -c "$COOKIE_JAR" -X POST "$API/api/v1/auth/login" \
  -H 'content-type: application/json' -d '{"accessKey":"<DEEPWORK_ACCESS_KEY>"}'
curl -s -b "$COOKIE_JAR" "$API/api/v1/tasks"
```

### Model and configuration

The agent's model is selected with `DEEPWORK_AGENT_MODEL` on the agent service,
using OpenRouter (`openrouter:<model>`, one key serves the leading model
families). The current validation model is `openrouter:openai/gpt-5.6-luna`;
alternatives include `openrouter:z-ai/glm-5.2` (cheaper) and
`openrouter:moonshotai/kimi-k2.7-code`. Provider/model credentials
(`OPENROUTER_API_KEY`, `LANGSMITH_API_KEY`) live only in the hosting
environment and are never committed.

> This is an ephemeral **validation** environment: task state is in-memory (a
> restart clears tasks), the access and model keys rotate, and the agent runtime
> is not yet hardened for public exposure. It is for verifying the end-to-end
> product, not production traffic.

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

## Run against a hosted deployment (classic LangSmith/LangGraph)

Instead of running an agent locally, Deep Work can drive a hosted classic
LangSmith/LangGraph Deployment (the same protocol a Managed Deep Agents
deployment speaks). Deploy the `packages/agent` graph to the platform using the
`langgraph.json` in this repo, then point the launcher at it:

```bash
DEEPWORK_CLASSIC_ENDPOINT=https://<your-deployment>.smith.langchain.com \
DEEPWORK_CLASSIC_ASSISTANT=deep-work-local-agent \
LANGSMITH_API_KEY=... \
./dev
```

The deployment credential is read only on the server and is never returned to a
client, written to task content, or included in the event stream. The model key
lives in the deployment's own configuration, not in Deep Work. This path is
gated off by default; the launcher enables it when `DEEPWORK_CLASSIC_ENDPOINT`
is set with a credential and assistant.

## Start here

| Need                             | Canonical source                                                                     |
| -------------------------------- | ------------------------------------------------------------------------------------ |
| Agent instructions               | [AGENTS.md](AGENTS.md)                                                               |
| System and dependency boundaries | [ARCHITECTURE.md](ARCHITECTURE.md)                                                   |
| Product outcome and judgment     | [docs/PRODUCT_SENSE.md](docs/PRODUCT_SENSE.md)                                       |
| Program roadmap and acceptance   | [docs/PLANS.md](docs/PLANS.md) and [release scorecard](docs/RELEASE_SCORECARD.md)    |
| Stable feature specifications    | [docs/product-specs/index.md](docs/product-specs/index.md)                           |
| Active implementation handoff    | [Golden journey recovery ExecPlan](docs/exec-plans/active/DW-EXEC-PRODUCT-RECOVERY-GOLDEN-JOURNEY.md) |
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

Deep Work is released under the [MIT license](LICENSE). Portions Copyright (c)
LangChain, Inc. (MIT); that attribution covers upstream MIT-licensed ideas and
dependencies and does not imply ownership of this project.

Deep Work is an independent open-source project built for compatibility with
LangChain technologies. Deep Work is not affiliated with, endorsed by, or
sponsored by LangChain, Inc.
“LangChain” and “LangSmith” are trademarks of their respective owner and are used
only to describe compatibility.

`langgraph-api` is a separately operated Agent Server runtime under the Elastic
License 2.0. Deep Work communicates with that runtime over HTTP and never vendors
or redistributes langgraph-api. The Deep Work source and packages in this
repository remain MIT-licensed; using a separately deployed runtime remains
subject to that runtime's own terms.
