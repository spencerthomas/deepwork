---
title: Deep Work reliability model
status: canonical
last_reviewed: 2026-08-04
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

## Local SQLite recovery boundary

The local adapter has a stopped-application backup/restore utility for recovery
testing and developer-owned data. Stop the API first so the task and settings
databases represent one application point in time, then use absolute paths:

```bash
make -C apps/api test-local-backup
uv --directory apps/api run python scripts/sqlite_backup.py backup \
  --tasks /absolute/path/tasks.sqlite \
  --settings /absolute/path/settings.sqlite3 \
  --output /absolute/path/new-backup-directory
uv --directory apps/api run python scripts/sqlite_backup.py restore \
  --bundle /absolute/path/new-backup-directory \
  --output /absolute/path/new-restored-directory
```

The bundle records file and logical-content hashes, row counts, schema objects and
SQLite application/user versions. Restore checks the manifest, both databases and
SQLite integrity before atomically exposing a new output directory; it refuses
existing destinations and symbolic-link inputs. The retained manifest detects
accidental or one-sided data changes, but is not signed and therefore does not
authenticate a bundle from an untrusted party.

This utility does not supply cross-database online snapshots, encryption,
retention, remote storage, PostgreSQL/outbox recovery, object restoration,
migration rollback, disaster recovery objectives or production acceptance. Those
remain release gates under `E2E-V1-09-SECURITY-RECOVERY` and
`E2E-V1-12-OPERATIONAL-RELEASE`.

## PostgreSQL job/outbox boundary

The application now has an Alembic-managed PostgreSQL job/outbox implementation.
An authenticated API transaction inserts exactly one tenant/workspace-scoped job
and one unique outbox row. Separate worker processes claim pending effects with
`FOR UPDATE SKIP LOCKED`; job and outbox lease, completion, retry, lease-expiry
recovery, and dead-letter state move in the same transaction. The repository
fails startup when the schema is absent or not at the packaged head revision.

`make test-postgres` is an explicit opt-in acceptance gate requiring
`DEEPWORK_TEST_DATABASE_URL` to identify a disposable local database. It applies
the migration, rejects metadata drift, proves idempotency and scope, runs
concurrent workers, exercises lease recovery/dead-lettering, and stops/restarts
separate API and worker processes before read-back. This is real local PostgreSQL
mechanism proof. It does not yet prove a replica failover, production backup and
restore, object recovery, real job handlers, hosted operation, or once-only
external side effects.
