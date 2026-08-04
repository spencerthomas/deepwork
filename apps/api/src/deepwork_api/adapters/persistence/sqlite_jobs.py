"""Local SQLite proof adapter for durable application jobs."""

from __future__ import annotations

import asyncio
import secrets
import sqlite3
from pathlib import Path

from deepwork_api.domain import (
    JobAcceptance,
    JobDurability,
    JobKind,
    JobLease,
    JobLeaseConflictError,
    JobNotFoundError,
    JobRecord,
    JobStatus,
)

_APPLICATION_ID = 0x44574A31
_SCHEMA_VERSION = 2
_MAX_IDEMPOTENCY_KEY_LENGTH = 200
_MAX_SAFE_ERROR_LENGTH = 100
_MAX_ATTEMPTS = 10
_EXPIRED_FINAL_LEASE_ERROR = "worker lease expired after maximum attempts"

_SCHEMA_STATEMENTS = (
    """
CREATE TABLE jobs (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL UNIQUE,
    tenant_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    status TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    attempts INTEGER NOT NULL,
    max_attempts INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    lease_owner TEXT,
    lease_token TEXT,
    lease_expires_at INTEGER,
    safe_error TEXT,
    UNIQUE (tenant_id, workspace_id, idempotency_key)
)
""",
    "CREATE INDEX jobs_queue_order ON jobs(status, sequence)",
    "CREATE INDEX jobs_expired_leases ON jobs(status, lease_expires_at)",
)
_EXPECTED_OBJECTS = {"jobs", "jobs_queue_order", "jobs_expired_leases"}


class SQLiteJobRepositoryError(Exception):
    """Local durable-job database is unsafe or incompatible."""


class SQLiteJobRepository:
    """Cross-process SQLite queue used only for local durability evidence."""

    def __init__(self, database_path: str | Path) -> None:
        candidate = Path(database_path).expanduser().absolute()
        for part in (candidate, *candidate.parents):
            if part.is_symlink():
                raise SQLiteJobRepositoryError("job database path cannot traverse a symlink")
        if candidate == Path(candidate.anchor):
            raise SQLiteJobRepositoryError("job database path must be an explicit file")
        self._path = candidate.resolve(strict=False)
        self._initialized = False
        self._closed = False
        self._lock = asyncio.Lock()

    @property
    def durability(self) -> JobDurability:
        return JobDurability.LOCAL_SQLITE_PROOF

    @property
    def database_path(self) -> Path:
        return self._path

    async def initialize(self) -> None:
        self._ensure_open()
        if self._initialized:
            return
        async with self._lock:
            if not self._initialized:
                await asyncio.to_thread(self._initialize_sync)
                self._initialized = True

    async def close(self) -> None:
        self._closed = True

    async def enqueue(
        self,
        *,
        tenant_id: str,
        workspace_id: str,
        actor_id: str,
        kind: JobKind,
        idempotency_key: str,
        now: int,
        max_attempts: int = 3,
    ) -> JobAcceptance:
        self._validate_enqueue(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            actor_id=actor_id,
            idempotency_key=idempotency_key,
            now=now,
            max_attempts=max_attempts,
        )
        await self.initialize()
        return await asyncio.to_thread(
            self._enqueue_sync,
            tenant_id,
            workspace_id,
            actor_id,
            kind,
            idempotency_key,
            now,
            max_attempts,
        )

    async def get(self, *, tenant_id: str, workspace_id: str, job_id: str) -> JobRecord:
        await self.initialize()
        return await asyncio.to_thread(self._get_sync, tenant_id, workspace_id, job_id)

    async def lease_next(
        self,
        *,
        worker_id: str,
        now: int,
        lease_seconds: int,
    ) -> JobLease | None:
        if not worker_id or len(worker_id) > 200 or not 1 <= lease_seconds <= 300 or now < 0:
            raise ValueError("worker lease input is invalid")
        await self.initialize()
        return await asyncio.to_thread(self._lease_next_sync, worker_id, now, lease_seconds)

    async def complete(
        self,
        *,
        job_id: str,
        lease_token: str,
        now: int,
    ) -> JobRecord:
        await self.initialize()
        return await asyncio.to_thread(
            self._finish_sync,
            job_id,
            lease_token,
            now,
            None,
            False,
        )

    async def fail(
        self,
        *,
        job_id: str,
        lease_token: str,
        now: int,
        safe_error: str,
        retryable: bool,
    ) -> JobRecord:
        if not safe_error or len(safe_error) > _MAX_SAFE_ERROR_LENGTH:
            raise ValueError("safe job error is invalid")
        await self.initialize()
        return await asyncio.to_thread(
            self._finish_sync,
            job_id,
            lease_token,
            now,
            safe_error,
            retryable,
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def _initialize_sync(self) -> None:
        self._path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self._path.exists() and (self._path.is_symlink() or not self._path.is_file()):
            raise SQLiteJobRepositoryError("job database must be a regular file")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            application_id = int(connection.execute("PRAGMA application_id").fetchone()[0])
            user_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            objects = {
                str(row["name"])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type IN ('table', 'index') "
                    "AND name NOT LIKE 'sqlite_%'"
                )
            }
            if not objects:
                for statement in _SCHEMA_STATEMENTS:
                    connection.execute(statement)
                connection.execute(f"PRAGMA application_id = {_APPLICATION_ID}")
                connection.execute(f"PRAGMA user_version = {_SCHEMA_VERSION}")
            elif application_id != _APPLICATION_ID or user_version != _SCHEMA_VERSION:
                raise SQLiteJobRepositoryError("job database schema is incompatible")
            objects = {
                str(row["name"])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type IN ('table', 'index') "
                    "AND name NOT LIKE 'sqlite_%'"
                )
            }
            if objects != _EXPECTED_OBJECTS:
                raise SQLiteJobRepositoryError("job database schema is incompatible")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _enqueue_sync(
        self,
        tenant_id: str,
        workspace_id: str,
        actor_id: str,
        kind: JobKind,
        idempotency_key: str,
        now: int,
        max_attempts: int,
    ) -> JobAcceptance:
        job_id = f"job_{secrets.token_hex(12)}"
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM jobs "
                "WHERE tenant_id = ? AND workspace_id = ? AND idempotency_key = ?",
                (tenant_id, workspace_id, idempotency_key),
            ).fetchone()
            if existing is not None:
                connection.commit()
                return JobAcceptance(job=self._record(existing), duplicate=True)
            connection.execute(
                """
                INSERT INTO jobs (
                    job_id, tenant_id, workspace_id, actor_id, kind, status,
                    idempotency_key, attempts, max_attempts, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
                """,
                (
                    job_id,
                    tenant_id,
                    workspace_id,
                    actor_id,
                    kind.value,
                    JobStatus.QUEUED.value,
                    idempotency_key,
                    max_attempts,
                    now,
                    now,
                ),
            )
            row = connection.execute(
                "SELECT * FROM jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
            connection.commit()
        if row is None:
            raise SQLiteJobRepositoryError("accepted job could not be reloaded")
        return JobAcceptance(job=self._record(row), duplicate=False)

    def _get_sync(self, tenant_id: str, workspace_id: str, job_id: str) -> JobRecord:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM jobs WHERE tenant_id = ? AND workspace_id = ? AND job_id = ?",
                (tenant_id, workspace_id, job_id),
            ).fetchone()
        if row is None:
            raise JobNotFoundError
        return self._record(row)

    def _lease_next_sync(
        self,
        worker_id: str,
        now: int,
        lease_seconds: int,
    ) -> JobLease | None:
        with self._connect() as connection:
            candidate = connection.execute(
                """
                SELECT 1 FROM jobs
                WHERE (status = ? AND attempts < max_attempts)
                   OR (status = ? AND lease_expires_at <= ?)
                LIMIT 1
                """,
                (JobStatus.QUEUED.value, JobStatus.LEASED.value, now),
            ).fetchone()
            if candidate is None:
                return None
            lease_token = secrets.token_hex(24)
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                UPDATE jobs
                SET status = ?, lease_owner = NULL, lease_token = NULL,
                    lease_expires_at = NULL, updated_at = ?
                WHERE status = ? AND lease_expires_at <= ? AND attempts < max_attempts
                """,
                (
                    JobStatus.QUEUED.value,
                    now,
                    JobStatus.LEASED.value,
                    now,
                ),
            )
            connection.execute(
                """
                UPDATE jobs
                SET status = ?, lease_owner = NULL, lease_token = NULL,
                    lease_expires_at = NULL, updated_at = ?, safe_error = ?
                WHERE status = ? AND lease_expires_at <= ? AND attempts >= max_attempts
                """,
                (
                    JobStatus.DEAD.value,
                    now,
                    _EXPIRED_FINAL_LEASE_ERROR,
                    JobStatus.LEASED.value,
                    now,
                ),
            )
            row = connection.execute(
                """
                SELECT * FROM jobs
                WHERE status = ? AND attempts < max_attempts
                ORDER BY sequence
                LIMIT 1
                """,
                (JobStatus.QUEUED.value,),
            ).fetchone()
            if row is None:
                connection.commit()
                return None
            connection.execute(
                """
                UPDATE jobs
                SET status = ?, attempts = attempts + 1, updated_at = ?,
                    lease_owner = ?, lease_token = ?, lease_expires_at = ?, safe_error = NULL
                WHERE job_id = ? AND status = ?
                """,
                (
                    JobStatus.LEASED.value,
                    now,
                    worker_id,
                    lease_token,
                    now + lease_seconds,
                    row["job_id"],
                    JobStatus.QUEUED.value,
                ),
            )
            leased = connection.execute(
                "SELECT * FROM jobs WHERE job_id = ?",
                (row["job_id"],),
            ).fetchone()
            connection.commit()
        if leased is None:
            raise SQLiteJobRepositoryError("leased job could not be reloaded")
        return JobLease(job=self._record(leased), lease_token=lease_token)

    def _finish_sync(
        self,
        job_id: str,
        lease_token: str,
        now: int,
        safe_error: str | None,
        retryable: bool,
    ) -> JobRecord:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
            if (
                row is None
                or row["status"] != JobStatus.LEASED.value
                or row["lease_token"] is None
                or not secrets.compare_digest(str(row["lease_token"]), lease_token)
                or row["lease_expires_at"] is None
                or int(row["lease_expires_at"]) <= now
            ):
                connection.rollback()
                raise JobLeaseConflictError
            if safe_error is None:
                status = JobStatus.SUCCEEDED
            elif retryable and int(row["attempts"]) < int(row["max_attempts"]):
                status = JobStatus.QUEUED
            else:
                status = JobStatus.DEAD
            connection.execute(
                """
                UPDATE jobs
                SET status = ?, updated_at = ?, lease_owner = NULL,
                    lease_token = NULL, lease_expires_at = NULL, safe_error = ?
                WHERE job_id = ?
                """,
                (status.value, now, safe_error, job_id),
            )
            finished = connection.execute(
                "SELECT * FROM jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
            connection.commit()
        if finished is None:
            raise SQLiteJobRepositoryError("finished job could not be reloaded")
        return self._record(finished)

    @staticmethod
    def _record(row: sqlite3.Row) -> JobRecord:
        return JobRecord(
            job_id=str(row["job_id"]),
            tenant_id=str(row["tenant_id"]),
            workspace_id=str(row["workspace_id"]),
            actor_id=str(row["actor_id"]),
            kind=JobKind(str(row["kind"])),
            status=JobStatus(str(row["status"])),
            attempts=int(row["attempts"]),
            max_attempts=int(row["max_attempts"]),
            created_at=int(row["created_at"]),
            updated_at=int(row["updated_at"]),
            lease_expires_at=(
                int(row["lease_expires_at"]) if row["lease_expires_at"] is not None else None
            ),
            safe_error=str(row["safe_error"]) if row["safe_error"] is not None else None,
        )

    @staticmethod
    def _validate_enqueue(
        *,
        tenant_id: str,
        workspace_id: str,
        actor_id: str,
        idempotency_key: str,
        now: int,
        max_attempts: int,
    ) -> None:
        if not all((tenant_id, workspace_id, actor_id)):
            raise ValueError("job identity context is incomplete")
        if any(len(value) > 200 for value in (tenant_id, workspace_id, actor_id)):
            raise ValueError("job identity context is invalid")
        if (
            not idempotency_key
            or len(idempotency_key) > _MAX_IDEMPOTENCY_KEY_LENGTH
            or any(character.isspace() for character in idempotency_key)
        ):
            raise ValueError("idempotency key is invalid")
        if now < 0 or not 1 <= max_attempts <= _MAX_ATTEMPTS:
            raise ValueError("job timing or retry bound is invalid")

    def _ensure_open(self) -> None:
        if self._closed:
            raise SQLiteJobRepositoryError("job repository is closed")
