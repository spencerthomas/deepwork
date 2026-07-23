# Deep Work API scaffold

This independently locked Python 3.12 project is the application-service package
boundary for Deep Work. The Wave 1 scaffold provides:

- a side-effect-free `deepwork_api.create_app()` factory;
- process-only `GET /health`;
- deterministic `GET /api/v1/demo/status` that is permanently labelled fixture;
- in-memory task create/list/detail endpoints with a sanitized, prompt-specific result;
- replayable normalized SSE and real local approve/reject/respond pauses;
- inspectable fixture evidence and an editable, revision-checked pending plan;
- separate `deepwork-api` and `deepwork-worker` entry points from one artifact; and
- package-local format, lint, type, no-network test, build, and clean-wheel checks.

Task state survives list/detail/result requests only for the lifetime of one API process.
The API does **not** provide authentication, source connections, provider calls,
durable persistence, durable jobs, credentials, or production readiness. Stream
output is explicitly local fixture evidence, never a provider/model claim. The worker
supports `--check` only and reports durability unavailable.

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
process identities, and the in-memory repository is intentionally reset on restart.
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
make check
```

`make bootstrap` is the only command permitted to resolve dependencies from
reviewed public package indexes. Every other package command forces uv offline and
disables Python downloads. A cold package state fails closed with an instruction
to run the explicit bootstrap; it never falls through to an implicit download.
Normal tests deny IP sockets and require no `.env`, provider account, or external
service.
