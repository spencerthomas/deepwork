"""Durable application-job repository port."""

from __future__ import annotations

from typing import Protocol

from deepwork_api.domain import JobAcceptance, JobKind, JobLease, JobRecord


class JobRepository(Protocol):
    """Persist tenant-scoped jobs and worker leases."""

    async def initialize(self) -> None: ...

    async def close(self) -> None: ...

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
    ) -> JobAcceptance: ...

    async def get(
        self,
        *,
        tenant_id: str,
        workspace_id: str,
        job_id: str,
    ) -> JobRecord: ...

    async def lease_next(
        self,
        *,
        worker_id: str,
        now: int,
        lease_seconds: int,
    ) -> JobLease | None: ...

    async def complete(
        self,
        *,
        job_id: str,
        lease_token: str,
        now: int,
    ) -> JobRecord: ...

    async def fail(
        self,
        *,
        job_id: str,
        lease_token: str,
        now: int,
        safe_error: str,
        retryable: bool,
    ) -> JobRecord: ...
