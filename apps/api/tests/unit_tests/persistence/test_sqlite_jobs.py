"""Local SQLite durable-job recovery, retry, and isolation proof."""

import asyncio
from pathlib import Path

import pytest

from deepwork_api.adapters.persistence import SQLiteJobRepository
from deepwork_api.application import JobWorker
from deepwork_api.domain import (
    JobKind,
    JobLeaseConflictError,
    JobNotFoundError,
    JobStatus,
)


async def test_jobs_are_tenant_scoped_idempotent_and_survive_repository_restart(
    tmp_path: Path,
) -> None:
    database = (tmp_path / "jobs.sqlite3").resolve()
    first_repository = SQLiteJobRepository(database)
    first = await first_repository.enqueue(
        tenant_id="tenant-a",
        workspace_id="workspace-a",
        actor_id="actor-a",
        kind=JobKind.FIXTURE_NOOP,
        idempotency_key="request-0001",
        now=100,
    )
    duplicate = await first_repository.enqueue(
        tenant_id="tenant-a",
        workspace_id="workspace-a",
        actor_id="actor-a",
        kind=JobKind.FIXTURE_NOOP,
        idempotency_key="request-0001",
        now=101,
    )
    peer = await first_repository.enqueue(
        tenant_id="tenant-b",
        workspace_id="workspace-b",
        actor_id="actor-b",
        kind=JobKind.FIXTURE_NOOP,
        idempotency_key="request-0001",
        now=102,
    )

    assert duplicate.duplicate is True
    assert duplicate.job.job_id == first.job.job_id
    assert peer.job.job_id != first.job.job_id
    with pytest.raises(JobNotFoundError):
        await first_repository.get(
            tenant_id="tenant-b",
            workspace_id="workspace-b",
            job_id=first.job.job_id,
        )
    await first_repository.close()

    recovered_repository = SQLiteJobRepository(database)
    recovered = await recovered_repository.get(
        tenant_id="tenant-a",
        workspace_id="workspace-a",
        job_id=first.job.job_id,
    )
    assert recovered.status is JobStatus.QUEUED
    assert recovered.actor_id == "actor-a"
    await recovered_repository.close()


async def test_concurrent_first_start_initializes_one_shared_database(tmp_path: Path) -> None:
    database = (tmp_path / "jobs.sqlite3").resolve()
    repositories = [SQLiteJobRepository(database) for _ in range(8)]

    await asyncio.gather(*(repository.initialize() for repository in repositories))

    accepted = await repositories[0].enqueue(
        tenant_id="tenant-a",
        workspace_id="workspace-a",
        actor_id="actor-a",
        kind=JobKind.FIXTURE_NOOP,
        idempotency_key="request-concurrent-initialize",
        now=100,
    )
    recovered = await repositories[-1].get(
        tenant_id="tenant-a",
        workspace_id="workspace-a",
        job_id=accepted.job.job_id,
    )
    assert recovered.job_id == accepted.job.job_id
    await asyncio.gather(*(repository.close() for repository in repositories))


async def test_expired_lease_is_recovered_by_restarted_worker(tmp_path: Path) -> None:
    database = (tmp_path / "jobs.sqlite3").resolve()
    crashed_worker_repository = SQLiteJobRepository(database)
    accepted = await crashed_worker_repository.enqueue(
        tenant_id="tenant-a",
        workspace_id="workspace-a",
        actor_id="actor-a",
        kind=JobKind.FIXTURE_NOOP,
        idempotency_key="request-expired-lease",
        now=100,
    )
    stale_lease = await crashed_worker_repository.lease_next(
        worker_id="worker-before-restart",
        now=101,
        lease_seconds=5,
    )
    assert stale_lease is not None
    await crashed_worker_repository.close()

    restarted_worker_repository = SQLiteJobRepository(database)
    with pytest.raises(JobLeaseConflictError):
        await restarted_worker_repository.complete(
            job_id=accepted.job.job_id,
            lease_token=stale_lease.lease_token,
            now=107,
        )

    completed = await JobWorker(
        repository=restarted_worker_repository,
        worker_id="worker-after-restart",
        now=lambda: 107,
    ).run_once()
    assert completed is not None
    assert completed.status is JobStatus.SUCCEEDED
    assert completed.attempts == 2
    await restarted_worker_repository.close()


async def test_retry_bound_moves_repeated_failure_to_dead_letter(tmp_path: Path) -> None:
    repository = SQLiteJobRepository((tmp_path / "jobs.sqlite3").resolve())
    accepted = await repository.enqueue(
        tenant_id="tenant-a",
        workspace_id="workspace-a",
        actor_id="actor-a",
        kind=JobKind.FIXTURE_NOOP,
        idempotency_key="request-dead-letter",
        now=100,
        max_attempts=2,
    )

    first = await repository.lease_next(worker_id="worker-a", now=101, lease_seconds=10)
    assert first is not None
    queued = await repository.fail(
        job_id=accepted.job.job_id,
        lease_token=first.lease_token,
        now=102,
        safe_error="retryable-fixture-error",
        retryable=True,
    )
    assert queued.status is JobStatus.QUEUED

    second = await repository.lease_next(worker_id="worker-a", now=103, lease_seconds=10)
    assert second is not None
    dead = await repository.fail(
        job_id=accepted.job.job_id,
        lease_token=second.lease_token,
        now=104,
        safe_error="retryable-fixture-error",
        retryable=True,
    )
    assert dead.status is JobStatus.DEAD
    assert dead.attempts == 2
    assert dead.safe_error == "retryable-fixture-error"
    assert await repository.lease_next(worker_id="worker-a", now=105, lease_seconds=10) is None
    await repository.close()


async def test_expired_final_attempt_is_dead_lettered_instead_of_staying_leased(
    tmp_path: Path,
) -> None:
    repository = SQLiteJobRepository((tmp_path / "jobs.sqlite3").resolve())
    accepted = await repository.enqueue(
        tenant_id="tenant-a",
        workspace_id="workspace-a",
        actor_id="actor-a",
        kind=JobKind.FIXTURE_NOOP,
        idempotency_key="request-final-expired-lease",
        now=100,
        max_attempts=1,
    )
    lease = await repository.lease_next(worker_id="worker-a", now=101, lease_seconds=5)
    assert lease is not None

    assert await repository.lease_next(worker_id="worker-b", now=106, lease_seconds=5) is None
    dead = await repository.get(
        tenant_id="tenant-a",
        workspace_id="workspace-a",
        job_id=accepted.job.job_id,
    )
    assert dead.status is JobStatus.DEAD
    assert dead.safe_error == "worker lease expired after maximum attempts"
    await repository.close()
