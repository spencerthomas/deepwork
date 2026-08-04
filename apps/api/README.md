# Deep Work application API

This independently locked Python 3.12 project is the application-service package
boundary for Deep Work. It provides:

- a side-effect-free `deepwork_api.create_app()` factory;
- optional, explicit local SQLite fixture persistence;
- process-only `GET /health`;
- credential-free `GET /api/v1/runtime/status` that identifies the configured
  fixture, local Agent Server, or classic deployment adapter without exposing
  provider endpoints or credentials (the original `/api/v1/demo/status` remains
  as a deprecated read alias);
- in-memory task create/list/detail endpoints with a sanitized, prompt-specific result;
- replayable normalized SSE and real local approve/reject/respond pauses;
- inspectable fixture evidence and an editable, revision-checked pending plan;
- separate `deepwork-api`, `deepwork-worker`, and `deepwork-migrate` entry points
  from one artifact;
- authenticated, tenant/workspace-scoped durable job intake with either explicitly
  labelled local SQLite proof or an Alembic-managed PostgreSQL transactional
  outbox; and
- package-local format, lint, type, no-network test, build, and clean-wheel checks.

By default, task state survives list/detail/result requests only for the lifetime of
one API process. Two default application instances do not share task state. For
local fixture recovery across restarts, opt in with an explicit absolute path:

```bash
deepwork-api --task-database /absolute/path/tasks.sqlite --port 8000
```

The SQLite file preserves completed task, plan, result, evidence, decision, and event
history for this deterministic local fixture. Startup creates or validates the
schema and fails closed for an invalid path, schema, or database; it never falls
back to memory. There is no environment lookup or default database path.

The default mode does **not** provide authentication, source connections, provider
calls, durable jobs, credentials, or production readiness. Authentication, a local
Agent Server, or a classic deployment are explicit server-owned configuration; the
browser never supplies their provider endpoint or credential. The opt-in SQLite
adapter is not PostgreSQL, migrations, an outbox, or production durability, and
active execution is not reconstructed or resumed after restart. Fixture stream
output is explicitly local fixture evidence, never a provider/model claim. The
worker reports durability unavailable unless one explicit job backend is
configured.

## PostgreSQL job/outbox boundary

The production durability boundary uses SQLAlchemy 2 async, Psycopg 3, PostgreSQL,
and packaged Alembic migrations. Configuration is server-owned and requires
session authentication. A local operator can exercise it with a disposable
database as follows (replace every placeholder locally; do not commit values):

```bash
export DEEPWORK_DATABASE_URL='postgresql+psycopg://<role>@127.0.0.1:<port>/<database>'
export DEEPWORK_ACCESS_KEY='<test-owned-access-key>'
deepwork-migrate upgrade
deepwork-api --port 8000
deepwork-worker --once
```

Job acceptance inserts the scoped job and its unique outbox effect in one
transaction. Workers claim with `FOR UPDATE SKIP LOCKED`; lease expiry, retry,
dead-letter, completion, and outbox delivery are updated atomically. Public reads
use the existing opaque session, return safe not-found across tenant/workspace
boundaries, and never return identity, lease material, database configuration, or
internal exceptions. The currently enabled `fixture.noop` handler proves the
durability mechanism; real notification, object, webhook, and reconciliation
handlers remain separate release work.

## Local task loop

Start the loopback-only API, then create a task:

```bash
deepwork-api --port 8000
curl -sS -X POST http://127.0.0.1:8000/api/v1/tasks \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Prepare a launch checklist"}'
curl -N http://127.0.0.1:8000/api/v1/tasks/task_00000001/events
curl -sS -X PATCH http://127.0.0.1:8000/api/v1/tasks/task_00000001/plan \
  -H 'Content-Type: application/json' \
  -d '{"interruptId":"interrupt_00000001","expectedRevision":1,"steps":["Review the requested outcome","Produce a bounded local result","Validate it"]}'
curl -sS -X POST http://127.0.0.1:8000/api/v1/tasks/task_00000001/decisions \
  -H 'Content-Type: application/json' \
  -d '{"interruptId":"interrupt_00000001","decision":"approve"}'
```

`GET /api/v1/tasks/{taskId}` includes the current `proposedPlan`, its evidence
references, source-qualified `evidence`, and the exact pending interrupt. A
`respond` decision requires a bounded non-blank `comment`; the comment resumes the
current interrupt but is never echoed, stored raw, or emitted in events. It produces
a fresh interrupt around the safely revised local plan.

Reconnect with `Last-Event-ID: 6` to replay only later events. Task IDs are local
repository identities. The default in-memory repository is intentionally reset on
restart; only the explicit local SQLite option recovers completed fixture history.
`run.completed` is the terminal stream event, after which the server closes the SSE
response. `GET /api/v1/tasks/{taskId}/result` returns the completed useful result.

Prompts are bounded at 8,000 characters across the API and local runner. Inputs over
that limit are rejected with `422`; accepted objectives are never silently
truncated. Common secret shapes are redacted before any objective is persisted or
streamed. A separate prompt-specific display title is bounded at 80 characters;
the authoritative sanitized objective remains intact. The internal Python state
`waiting_approval` is deliberately serialized as the web contract's
`waiting-approval`.

## Commands

```bash
make doctor
make bootstrap
make format-check
make lint
make typecheck
make test
make contract
make build
make package-check
DEEPWORK_TEST_DATABASE_URL='postgresql+psycopg://<role>@127.0.0.1:<port>/<database>' make test-postgres
make check
```

`make bootstrap` is the only command permitted to resolve dependencies from
reviewed public package indexes. Every other package command forces uv offline and
disables Python downloads. A cold package state fails closed with an instruction
to run the explicit bootstrap; it never falls through to an implicit download.
Normal tests deny IP sockets and require no `.env`, provider account, or external
service.
