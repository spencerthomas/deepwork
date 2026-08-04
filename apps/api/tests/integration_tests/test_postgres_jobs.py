"""Disposable-local-PostgreSQL job/outbox acceptance tests."""

from __future__ import annotations

import asyncio
import os
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient, ConnectError
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import create_async_engine

from deepwork_api.adapters.persistence import PostgresJobRepository
from deepwork_api.adapters.persistence.postgres_schema import job_outbox, jobs
from deepwork_api.bootstrap.api import create_app
from deepwork_api.bootstrap.test_database_guard import validate_disposable_database_url
from deepwork_api.domain import (
    JobKind,
    JobLeaseConflictError,
    JobNotFoundError,
    JobStatus,
    SecurityContext,
)

_RAW_DATABASE_URL = os.environ.get("DEEPWORK_TEST_DATABASE_URL")
DATABASE_URL = (
    validate_disposable_database_url(_RAW_DATABASE_URL) if _RAW_DATABASE_URL is not None else None
)
pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        DATABASE_URL is None, reason="disposable local PostgreSQL is not configured"
    ),
]


@pytest.fixture(autouse=True)
async def clean_database() -> AsyncIterator[None]:
    assert DATABASE_URL is not None
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.begin() as connection:
            await connection.execute(text("TRUNCATE job_outbox, jobs RESTART IDENTITY CASCADE"))
    finally:
        await engine.dispose()
    yield


async def _wait_for_api(base_url: str, process: asyncio.subprocess.Process) -> None:
    async with AsyncClient(base_url=base_url) as client:
        for _ in range(100):
            if process.returncode is not None:
                raise AssertionError(f"API exited before readiness with code {process.returncode}")
            try:
                response = await client.get("/health")
            except (ConnectError, OSError):
                await asyncio.sleep(0.05)
                continue
            if response.status_code == 200:
                return
            await asyncio.sleep(0.05)
    raise AssertionError("API did not become ready")


async def _stop_process(process: asyncio.subprocess.Process) -> None:
    if process.returncode is not None:
        return
    process.terminate()
    try:
        await asyncio.wait_for(process.wait(), timeout=5)
    except TimeoutError:
        process.kill()
        await asyncio.wait_for(process.wait(), timeout=5)


async def test_atomic_idempotent_outbox_and_scope_survive_repository_restart() -> None:
    assert DATABASE_URL is not None
    repository = PostgresJobRepository(DATABASE_URL)
    first = await repository.enqueue(
        tenant_id="tenant-a",
        workspace_id="workspace-a",
        actor_id="actor-a",
        kind=JobKind.FIXTURE_NOOP,
        idempotency_key="request-postgres-0001",
        now=100,
    )
    duplicate = await repository.enqueue(
        tenant_id="tenant-a",
        workspace_id="workspace-a",
        actor_id="actor-a",
        kind=JobKind.FIXTURE_NOOP,
        idempotency_key="request-postgres-0001",
        now=101,
    )
    workspace_peer = await repository.enqueue(
        tenant_id="tenant-a",
        workspace_id="workspace-b",
        actor_id="actor-b",
        kind=JobKind.FIXTURE_NOOP,
        idempotency_key="request-postgres-0001",
        now=102,
    )

    assert duplicate.duplicate is True
    assert duplicate.job.job_id == first.job.job_id
    assert workspace_peer.job.job_id != first.job.job_id
    with pytest.raises(JobNotFoundError):
        await repository.get(
            tenant_id="tenant-a",
            workspace_id="workspace-b",
            job_id=first.job.job_id,
        )
    await repository.close()

    restarted = PostgresJobRepository(DATABASE_URL)
    recovered = await restarted.get(
        tenant_id="tenant-a",
        workspace_id="workspace-a",
        job_id=first.job.job_id,
    )
    assert recovered.status is JobStatus.QUEUED
    await restarted.close()

    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.connect() as connection:
            job_count = await connection.scalar(select(func.count()).select_from(jobs))
            outbox_count = await connection.scalar(select(func.count()).select_from(job_outbox))
    finally:
        await engine.dispose()
    assert job_count == 2
    assert outbox_count == 2


async def test_concurrent_workers_claim_each_outbox_effect_once() -> None:
    assert DATABASE_URL is not None
    producer = PostgresJobRepository(DATABASE_URL)
    accepted = [
        await producer.enqueue(
            tenant_id="tenant-a",
            workspace_id="workspace-a",
            actor_id="actor-a",
            kind=JobKind.FIXTURE_NOOP,
            idempotency_key=f"request-concurrent-{index:04d}",
            now=100 + index,
        )
        for index in range(8)
    ]
    workers = [PostgresJobRepository(DATABASE_URL) for _ in accepted]
    leases = await asyncio.gather(
        *(
            worker.lease_next(worker_id=f"worker-{index}", now=200, lease_seconds=30)
            for index, worker in enumerate(workers)
        )
    )
    assert all(lease is not None for lease in leases)
    leased_ids = {lease.job.job_id for lease in leases if lease is not None}
    assert leased_ids == {item.job.job_id for item in accepted}

    completed = await asyncio.gather(
        *(
            worker.complete(job_id=lease.job.job_id, lease_token=lease.lease_token, now=201)
            for worker, lease in zip(workers, leases, strict=True)
            if lease is not None
        )
    )
    assert all(item.status is JobStatus.SUCCEEDED for item in completed)
    assert await producer.lease_next(worker_id="worker-extra", now=202, lease_seconds=30) is None
    await producer.close()
    await asyncio.gather(*(worker.close() for worker in workers))

    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.connect() as connection:
            delivered = await connection.scalar(
                select(func.count())
                .select_from(job_outbox)
                .where(job_outbox.c.status == "delivered")
            )
            unique_jobs = await connection.scalar(
                select(func.count(func.distinct(job_outbox.c.job_id)))
            )
    finally:
        await engine.dispose()
    assert delivered == 8
    assert unique_jobs == 8


async def test_expired_lease_recovers_and_retry_bound_dead_letters() -> None:
    assert DATABASE_URL is not None
    repository = PostgresJobRepository(DATABASE_URL)
    accepted = await repository.enqueue(
        tenant_id="tenant-a",
        workspace_id="workspace-a",
        actor_id="actor-a",
        kind=JobKind.FIXTURE_NOOP,
        idempotency_key="request-expired-postgres",
        now=100,
        max_attempts=2,
    )
    first = await repository.lease_next(worker_id="worker-before", now=101, lease_seconds=5)
    assert first is not None
    with pytest.raises(JobLeaseConflictError):
        await repository.complete(
            job_id=accepted.job.job_id,
            lease_token=first.lease_token,
            now=107,
        )

    second = await repository.lease_next(worker_id="worker-after", now=107, lease_seconds=5)
    assert second is not None
    assert second.job.attempts == 2
    dead = await repository.fail(
        job_id=accepted.job.job_id,
        lease_token=second.lease_token,
        now=108,
        safe_error="retryable-fixture-error",
        retryable=True,
    )
    assert dead.status is JobStatus.DEAD
    assert await repository.lease_next(worker_id="worker-extra", now=109, lease_seconds=5) is None
    await repository.close()


async def test_http_session_scope_and_public_durability_use_postgres() -> None:
    assert DATABASE_URL is not None
    contexts = {
        "access-key-a": SecurityContext(
            tenant_id="tenant-a",
            workspace_id="workspace-a",
            actor_id="actor-a",
        ),
        "access-key-b": SecurityContext(
            tenant_id="tenant-a",
            workspace_id="workspace-b",
            actor_id="actor-b",
        ),
    }
    app = create_app(job_database_url=DATABASE_URL, access_key_contexts=contexts)
    openapi = app.openapi()
    assert "/api/v1/jobs/fixture" not in openapi["paths"]
    assert "/api/v1/durable-jobs/fixture" in openapi["paths"]
    durability_schema = openapi["components"]["schemas"]["DurableJobResponse"]["properties"][
        "durability"
    ]
    assert durability_schema["const"] == "postgres-outbox"
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            login_a = await client.post("/api/v1/auth/login", json={"accessKey": "access-key-a"})
            assert login_a.status_code == 200
            accepted = await client.post(
                "/api/v1/durable-jobs/fixture",
                headers={"Idempotency-Key": "request-http-postgres"},
            )
            assert accepted.status_code == 202
            assert accepted.json()["durability"] == "postgres-outbox"
            job_id = accepted.json()["jobId"]

            await client.post("/api/v1/auth/logout")
            login_b = await client.post("/api/v1/auth/login", json={"accessKey": "access-key-b"})
            assert login_b.status_code == 200
            hidden = await client.get(f"/api/v1/durable-jobs/{job_id}")
            assert hidden.status_code == 404
            assert hidden.json() == {"code": "job_not_found", "message": "Job was not found."}


async def test_separate_api_and_worker_processes_survive_api_restart(tmp_path: Path) -> None:
    assert DATABASE_URL is not None
    port = int(os.environ.get("DEEPWORK_TEST_API_PORT", "55441"))
    base_url = f"http://127.0.0.1:{port}"
    access_key = "integration-access-key"
    environment = {
        **os.environ,
        "DEEPWORK_ACCESS_KEY": access_key,
        "DEEPWORK_DATABASE_URL": DATABASE_URL,
        "DEEPWORK_HOST": "127.0.0.1",
        "PORT": str(port),
    }
    executable_dir = Path(sys.executable).parent
    api_log_path = tmp_path / "api.log"
    with api_log_path.open("w+", encoding="utf-8") as api_log:
        first_api = await asyncio.create_subprocess_exec(
            str(executable_dir / "deepwork-api"),
            env=environment,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=api_log,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            await _wait_for_api(base_url, first_api)
            async with AsyncClient(base_url=base_url) as client:
                login = await client.post("/api/v1/auth/login", json={"accessKey": access_key})
                assert login.status_code == 200
                runtime = await client.get("/api/v1/runtime/status")
                assert runtime.status_code == 200
                capabilities = {
                    item["name"]: item["state"] for item in runtime.json()["capabilities"]
                }
                assert capabilities["authentication"] == "available"
                assert capabilities["durable_jobs"] == "available"
                accepted = await client.post(
                    "/api/v1/durable-jobs/fixture",
                    headers={"Idempotency-Key": "request-process-restart"},
                )
                assert accepted.status_code == 202
                assert accepted.json()["durability"] == "postgres-outbox"
                job_id = accepted.json()["jobId"]
        finally:
            await _stop_process(first_api)

        worker = await asyncio.create_subprocess_exec(
            str(executable_dir / "deepwork-worker"),
            "--once",
            env=environment,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        worker_stdout, worker_stderr = await asyncio.wait_for(worker.communicate(), timeout=10)
        worker_output = worker_stdout.decode()
        worker_error = worker_stderr.decode()
        assert worker.returncode == 0
        assert '"status":"succeeded"' in worker_output
        assert access_key not in worker_output + worker_error
        assert DATABASE_URL not in worker_output + worker_error

        worker_check = await asyncio.create_subprocess_exec(
            str(executable_dir / "deepwork-worker"),
            "--check",
            env=environment,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        check_stdout, check_stderr = await asyncio.wait_for(worker_check.communicate(), timeout=10)
        check_output = check_stdout.decode()
        check_error = check_stderr.decode()
        assert worker_check.returncode == 0
        assert '"durability":"postgres-outbox"' in check_output
        assert access_key not in check_output + check_error
        assert DATABASE_URL not in check_output + check_error

        second_api = await asyncio.create_subprocess_exec(
            str(executable_dir / "deepwork-api"),
            env=environment,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=api_log,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            await _wait_for_api(base_url, second_api)
            async with AsyncClient(base_url=base_url) as client:
                login = await client.post("/api/v1/auth/login", json={"accessKey": access_key})
                assert login.status_code == 200
                recovered = await client.get(f"/api/v1/durable-jobs/{job_id}")
                assert recovered.status_code == 200
                assert recovered.json()["status"] == "succeeded"
                assert recovered.json()["durability"] == "postgres-outbox"
        finally:
            await _stop_process(second_api)
        api_log.seek(0)
        safe_log = api_log.read()
    assert access_key not in safe_log
    assert DATABASE_URL not in safe_log
