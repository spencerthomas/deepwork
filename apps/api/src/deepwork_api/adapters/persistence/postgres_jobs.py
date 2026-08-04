"""PostgreSQL transactional job/outbox repository."""

from __future__ import annotations

import secrets

from sqlalchemy import select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import RowMapping, make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from deepwork_api.adapters.persistence.postgres_schema import (
    ALEMBIC_HEAD,
    job_outbox,
    jobs,
)
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

_MAX_IDEMPOTENCY_KEY_LENGTH = 200
_MAX_SAFE_ERROR_LENGTH = 100
_MAX_ATTEMPTS = 10
_EXPIRED_FINAL_LEASE_ERROR = "worker lease expired after maximum attempts"
_POOL_TIMEOUT_SECONDS = 5
_CONNECT_TIMEOUT_SECONDS = 5
_STATEMENT_TIMEOUT_MILLISECONDS = 10_000
_LOCK_TIMEOUT_MILLISECONDS = 5_000


class PostgresJobRepositoryError(Exception):
    """The configured PostgreSQL job/outbox boundary is unsafe or unavailable."""


class PostgresJobRepository:
    """Tenant-scoped jobs delivered through one transactional PostgreSQL outbox."""

    def __init__(self, database_url: str) -> None:
        try:
            parsed = make_url(database_url)
        except (TypeError, ValueError):
            raise PostgresJobRepositoryError(
                "PostgreSQL database configuration is invalid"
            ) from None
        if parsed.drivername != "postgresql+psycopg":
            raise PostgresJobRepositoryError(
                "PostgreSQL jobs require the postgresql+psycopg driver"
            )
        self._engine: AsyncEngine = create_async_engine(
            parsed,
            pool_pre_ping=True,
            pool_timeout=_POOL_TIMEOUT_SECONDS,
            connect_args={
                "connect_timeout": _CONNECT_TIMEOUT_SECONDS,
                "options": (
                    f"-c statement_timeout={_STATEMENT_TIMEOUT_MILLISECONDS} "
                    f"-c lock_timeout={_LOCK_TIMEOUT_MILLISECONDS} "
                    f"-c idle_in_transaction_session_timeout={_STATEMENT_TIMEOUT_MILLISECONDS}"
                ),
            },
            hide_parameters=True,
        )
        self._initialized = False
        self._closed = False

    @property
    def durability(self) -> JobDurability:
        return JobDurability.POSTGRES_OUTBOX

    async def initialize(self) -> None:
        self._ensure_open()
        if self._initialized:
            return
        try:
            async with self._engine.connect() as connection:
                version = await connection.scalar(text("SELECT version_num FROM alembic_version"))
                present = await connection.execute(
                    text(
                        "SELECT to_regclass('jobs') IS NOT NULL, "
                        "to_regclass('job_outbox') IS NOT NULL"
                    )
                )
                tables = present.one()
        except SQLAlchemyError:
            raise PostgresJobRepositoryError(
                "PostgreSQL job schema is unavailable; run the reviewed migrations"
            ) from None
        if version != ALEMBIC_HEAD or not all(bool(value) for value in tables):
            raise PostgresJobRepositoryError(
                "PostgreSQL job schema is incompatible; run the reviewed migrations"
            )
        self._initialized = True

    async def close(self) -> None:
        if not self._closed:
            self._closed = True
            await self._engine.dispose()

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
        job_id = f"job_{secrets.token_hex(12)}"
        outbox_id = f"out_{secrets.token_hex(12)}"
        async with self._engine.begin() as connection:
            inserted = (
                (
                    await connection.execute(
                        insert(jobs)
                        .values(
                            job_id=job_id,
                            tenant_id=tenant_id,
                            workspace_id=workspace_id,
                            actor_id=actor_id,
                            kind=kind.value,
                            status=JobStatus.QUEUED.value,
                            idempotency_key=idempotency_key,
                            attempts=0,
                            max_attempts=max_attempts,
                            created_at=now,
                            updated_at=now,
                        )
                        .on_conflict_do_nothing(
                            constraint="job_scope_idempotency",
                        )
                        .returning(*jobs.c)
                    )
                )
                .mappings()
                .first()
            )
            if inserted is None:
                existing = (
                    (
                        await connection.execute(
                            select(jobs).where(
                                jobs.c.tenant_id == tenant_id,
                                jobs.c.workspace_id == workspace_id,
                                jobs.c.idempotency_key == idempotency_key,
                            )
                        )
                    )
                    .mappings()
                    .one()
                )
                return JobAcceptance(job=self._record(existing), duplicate=True)
            await connection.execute(
                insert(job_outbox).values(
                    outbox_id=outbox_id,
                    job_id=job_id,
                    status="pending",
                    created_at=now,
                    updated_at=now,
                )
            )
            return JobAcceptance(job=self._record(inserted), duplicate=False)

    async def get(self, *, tenant_id: str, workspace_id: str, job_id: str) -> JobRecord:
        await self.initialize()
        async with self._engine.connect() as connection:
            row = (
                (
                    await connection.execute(
                        select(jobs).where(
                            jobs.c.tenant_id == tenant_id,
                            jobs.c.workspace_id == workspace_id,
                            jobs.c.job_id == job_id,
                        )
                    )
                )
                .mappings()
                .first()
            )
        if row is None:
            raise JobNotFoundError
        return self._record(row)

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
        lease_token = secrets.token_hex(24)
        async with self._engine.begin() as connection:
            await connection.execute(
                update(jobs)
                .where(
                    jobs.c.status == JobStatus.LEASED.value,
                    jobs.c.lease_expires_at <= now,
                    jobs.c.attempts >= jobs.c.max_attempts,
                )
                .values(
                    status=JobStatus.DEAD.value,
                    updated_at=now,
                    lease_owner=None,
                    lease_token=None,
                    lease_expires_at=None,
                    safe_error=_EXPIRED_FINAL_LEASE_ERROR,
                )
            )
            await connection.execute(
                update(job_outbox)
                .where(
                    job_outbox.c.status == "leased",
                    job_outbox.c.job_id.in_(
                        select(jobs.c.job_id).where(jobs.c.status == JobStatus.DEAD.value)
                    ),
                )
                .values(
                    status="dead",
                    updated_at=now,
                    lease_owner=None,
                    lease_token=None,
                    lease_expires_at=None,
                )
            )
            await connection.execute(
                update(jobs)
                .where(
                    jobs.c.status == JobStatus.LEASED.value,
                    jobs.c.lease_expires_at <= now,
                    jobs.c.attempts < jobs.c.max_attempts,
                )
                .values(
                    status=JobStatus.QUEUED.value,
                    updated_at=now,
                    lease_owner=None,
                    lease_token=None,
                    lease_expires_at=None,
                )
            )
            await connection.execute(
                update(job_outbox)
                .where(
                    job_outbox.c.status == "leased",
                    job_outbox.c.job_id.in_(
                        select(jobs.c.job_id).where(jobs.c.status == JobStatus.QUEUED.value)
                    ),
                )
                .values(
                    status="pending",
                    updated_at=now,
                    lease_owner=None,
                    lease_token=None,
                    lease_expires_at=None,
                )
            )
            candidate = (
                (
                    await connection.execute(
                        select(jobs)
                        .select_from(job_outbox.join(jobs, job_outbox.c.job_id == jobs.c.job_id))
                        .where(
                            job_outbox.c.status == "pending",
                            jobs.c.status == JobStatus.QUEUED.value,
                            jobs.c.attempts < jobs.c.max_attempts,
                        )
                        .order_by(job_outbox.c.sequence)
                        .limit(1)
                        .with_for_update(of=job_outbox, skip_locked=True)
                    )
                )
                .mappings()
                .first()
            )
            if candidate is None:
                return None
            job_id = str(candidate["job_id"])
            lease_expires_at = now + lease_seconds
            await connection.execute(
                update(jobs)
                .where(jobs.c.job_id == job_id, jobs.c.status == JobStatus.QUEUED.value)
                .values(
                    status=JobStatus.LEASED.value,
                    attempts=jobs.c.attempts + 1,
                    updated_at=now,
                    lease_owner=worker_id,
                    lease_token=lease_token,
                    lease_expires_at=lease_expires_at,
                    safe_error=None,
                )
            )
            await connection.execute(
                update(job_outbox)
                .where(job_outbox.c.job_id == job_id, job_outbox.c.status == "pending")
                .values(
                    status="leased",
                    updated_at=now,
                    lease_owner=worker_id,
                    lease_token=lease_token,
                    lease_expires_at=lease_expires_at,
                )
            )
            leased = (
                (await connection.execute(select(jobs).where(jobs.c.job_id == job_id)))
                .mappings()
                .one()
            )
        return JobLease(job=self._record(leased), lease_token=lease_token)

    async def complete(self, *, job_id: str, lease_token: str, now: int) -> JobRecord:
        return await self._finish(
            job_id=job_id,
            lease_token=lease_token,
            now=now,
            safe_error=None,
            retryable=False,
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
        return await self._finish(
            job_id=job_id,
            lease_token=lease_token,
            now=now,
            safe_error=safe_error,
            retryable=retryable,
        )

    async def _finish(
        self,
        *,
        job_id: str,
        lease_token: str,
        now: int,
        safe_error: str | None,
        retryable: bool,
    ) -> JobRecord:
        if now < 0 or not job_id or not lease_token:
            raise ValueError("job completion input is invalid")
        await self.initialize()
        async with self._engine.begin() as connection:
            row = (
                (
                    await connection.execute(
                        select(jobs)
                        .select_from(jobs.join(job_outbox, jobs.c.job_id == job_outbox.c.job_id))
                        .where(jobs.c.job_id == job_id)
                        .with_for_update()
                    )
                )
                .mappings()
                .first()
            )
            if (
                row is None
                or row["status"] != JobStatus.LEASED.value
                or row["lease_token"] is None
                or not secrets.compare_digest(str(row["lease_token"]), lease_token)
                or row["lease_expires_at"] is None
                or int(row["lease_expires_at"]) <= now
            ):
                raise JobLeaseConflictError
            if safe_error is None:
                status = JobStatus.SUCCEEDED
                outbox_status = "delivered"
            elif retryable and int(row["attempts"]) < int(row["max_attempts"]):
                status = JobStatus.QUEUED
                outbox_status = "pending"
            else:
                status = JobStatus.DEAD
                outbox_status = "dead"
            await connection.execute(
                update(jobs)
                .where(jobs.c.job_id == job_id)
                .values(
                    status=status.value,
                    updated_at=now,
                    lease_owner=None,
                    lease_token=None,
                    lease_expires_at=None,
                    safe_error=safe_error,
                )
            )
            await connection.execute(
                update(job_outbox)
                .where(job_outbox.c.job_id == job_id)
                .values(
                    status=outbox_status,
                    updated_at=now,
                    lease_owner=None,
                    lease_token=None,
                    lease_expires_at=None,
                    delivered_at=now if outbox_status == "delivered" else None,
                )
            )
            finished = (
                (await connection.execute(select(jobs).where(jobs.c.job_id == job_id)))
                .mappings()
                .one()
            )
        return self._record(finished)

    @staticmethod
    def _record(row: RowMapping) -> JobRecord:
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
            raise PostgresJobRepositoryError("PostgreSQL job repository is closed")
