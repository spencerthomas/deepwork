---
title: Deep Work reliability model
status: canonical
last_reviewed: 2026-07-23
owners: [platform, reliability]
---

# Deep Work reliability model

Deep Work treats the application service, worker, each registered source, object
store, notification channel, browser, and desktop host as independent failure
domains. Partial source failure does not erase healthy results, and an unavailable
optional capability does not prevent the public classic-deployment baseline.

## Required behaviors

- Mutations use idempotency, explicit conflict/stale responses, and durable audit.
- API transactions enqueue accepted background work through a PostgreSQL outbox;
  workers are restartable and retry only classified transient failures.
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
