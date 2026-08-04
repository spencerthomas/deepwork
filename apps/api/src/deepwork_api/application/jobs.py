"""Session-scoped durable application-job use cases."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field

from deepwork_api.domain import JobAcceptance, JobKind, JobRecord, SecurityContext
from deepwork_api.ports import JobRepository


def _epoch_seconds() -> int:
    return int(time.time())


@dataclass(slots=True)
class JobService:
    """Accept and inspect jobs under the current server-derived session context."""

    repository: JobRepository
    now: Callable[[], int] = field(default=_epoch_seconds)

    async def accept_fixture_job(
        self,
        *,
        security_context: SecurityContext,
        idempotency_key: str,
    ) -> JobAcceptance:
        return await self.repository.enqueue(
            tenant_id=security_context.tenant_id,
            workspace_id=security_context.workspace_id,
            actor_id=security_context.actor_id,
            kind=JobKind.FIXTURE_NOOP,
            idempotency_key=idempotency_key,
            now=self.now(),
        )

    async def get(
        self,
        *,
        security_context: SecurityContext,
        job_id: str,
    ) -> JobRecord:
        return await self.repository.get(
            tenant_id=security_context.tenant_id,
            workspace_id=security_context.workspace_id,
            job_id=job_id,
        )


@dataclass(slots=True)
class JobWorker:
    """Lease and execute one bounded local-proof job at a time."""

    repository: JobRepository
    worker_id: str
    lease_seconds: int = 30
    now: Callable[[], int] = field(default=_epoch_seconds)

    async def run_once(self) -> JobRecord | None:
        lease = await self.repository.lease_next(
            worker_id=self.worker_id,
            now=self.now(),
            lease_seconds=self.lease_seconds,
        )
        if lease is None:
            return None
        return await self.repository.complete(
            job_id=lease.job.job_id,
            lease_token=lease.lease_token,
            now=self.now(),
        )
