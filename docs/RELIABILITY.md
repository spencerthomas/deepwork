---
title: Deep Work reliability model
status: canonical
last_reviewed: 2026-07-23
owners: [platform, reliability]
---

# Deep Work reliability model

This document states the **target** reliability model. The "Implementation status"
section records what is shipped today; where they differ, the status section is
authoritative for the current build. (Recorded in `CODE_REVIEW-2026-07-27.md`.)

Deep Work treats the application service, worker, each registered source, object
store, notification channel, browser, and desktop host as independent failure
domains. Partial source failure does not erase healthy results, and an unavailable
optional capability does not prevent the public classic-deployment baseline.

## Implementation status (v1, as of 2026-07-27)

- **No PostgreSQL outbox or worker yet.** The worker entry point is an explicit
  stub reporting unavailable durability; there is no Postgres, outbox, or job
  runtime. Durable task state is an **optional single-file SQLite** store
  (`--task-database`), not the target Postgres/outbox design below.
- **Implemented and proven:** idempotent mutations with explicit conflict/stale
  responses; replayable SSE with an opaque recovery cursor and natural
  backpressure; honest task/approval states (no simulated completion); honest
  restart recovery in real-agent mode; deterministic credential-free fixtures.
- **Known gaps (see audit):** fixture+SQLite restart reconciliation, SSE
  keepalive, event-scan performance, and structured logging/observability are not
  yet addressed.

## Target behaviors

- Mutations use idempotency, explicit conflict/stale responses, and durable audit.
- API transactions enqueue accepted background work through a PostgreSQL outbox;
  workers are restartable and retry only classified transient failures. *(target;
  not yet implemented — see status above.)*
- The application stream carries source provenance, application ordering, and an
  opaque recovery token. Provider cursors stay server-side.
- Reconnect performs bounded replay and deduplication, then authoritative
  hydration with explicit freshness and recovery boundaries.
- Task and approval views expose offline, stale, reconnecting, partial, cancelled,
  permission, and terminal failure states without simulating completion.
- Fixtures are deterministic and credential-free. Only the API-backed product demo
  proves application integration; live provider claims require pinned contract
  evidence.

Release acceptance requires the 12 program scenarios plus enabled feature
scenarios, sanitized diagnostics, rollback compatibility, and recovery proof.
Open runtime contract questions remain in the
[decision and spike register](design-docs/decisions/index.md).
