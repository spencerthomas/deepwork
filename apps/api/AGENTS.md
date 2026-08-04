# API package instructions

`apps/api` owns the Python application-service, migration, and worker
distribution. It exposes the task/source/session contracts, an optional local
SQLite proof path, and an Alembic-managed PostgreSQL job/outbox boundary. Do not
promote the SQLite path to production durability or the fixture job handler to a
complete application runtime.

- Keep dependencies inward: `transport/bootstrap -> application -> domain/ports`;
  adapters implement ports.
- Domain code imports no FastAPI, Pydantic, provider, persistence, environment, or
  network modules.
- Do not import `packages/agent`, TypeScript packages, sibling repositories, or
  private upstream internals.
- No credential, `authRef`, arbitrary endpoint/header, provider cursor, or copied
  production content may enter schemas, logs, fixtures, tests, or evidence.
- SQLAlchemy stays in persistence adapters or bootstrap; Alembic revisions remain
  packaged, reversible, schema-drift checked, and free of credentials.
- External dependency resolution is limited to explicit bootstrap. Every other uv
  command is offline and disables Python downloads; an unbootstrapped state fails
  closed. Unit and contract tests make no provider/service calls, deny IP sockets,
  and allow only asyncio's local Unix socket pair. `make test-postgres` is a
  separate opt-in gate against an explicitly disposable local database.
- Run `make check`, `make package-check`, and (for persistence changes)
  `make test-postgres` from this directory before handoff.
