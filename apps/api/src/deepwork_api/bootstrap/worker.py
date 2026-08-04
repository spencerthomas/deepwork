"""Separate worker composition root for durable application jobs."""

import argparse
import asyncio
import json
import os
from collections.abc import Sequence
from pathlib import Path

from deepwork_api.adapters.fixture import FixtureStatusProvider
from deepwork_api.adapters.persistence import PostgresJobRepository, SQLiteJobRepository
from deepwork_api.application import JobWorker, StatusService
from deepwork_api.contracts import WorkerStatusResponse
from deepwork_api.domain import EvidenceClass, WorkerDurability, WorkerStatus


def worker_status(
    *,
    durability: WorkerDurability = WorkerDurability.UNAVAILABLE,
) -> WorkerStatusResponse:
    """Return the configured worker durability without production claims."""

    if durability is WorkerDurability.UNAVAILABLE:
        service = StatusService(provider=FixtureStatusProvider())
        return WorkerStatusResponse.from_domain(service.worker())
    safe_reason = (
        "local SQLite durability proof; not production PostgreSQL"
        if durability is WorkerDurability.LOCAL_SQLITE_PROOF
        else "PostgreSQL transactional job/outbox worker"
    )
    return WorkerStatusResponse.from_domain(
        WorkerStatus(
            mode=EvidenceClass.FIXTURE,
            durability=durability,
            safe_reason=safe_reason,
        )
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run or inspect the Deep Work worker.")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--job-database", type=Path)
    parser.add_argument("--worker-id", default="worker-local")
    parser.add_argument("--once", action="store_true")
    return parser


async def _run_once(
    repository: SQLiteJobRepository | PostgresJobRepository,
    worker_id: str,
) -> int:
    await repository.initialize()
    try:
        result = await JobWorker(repository=repository, worker_id=worker_id).run_once()
    finally:
        await repository.close()
    durability = repository.durability.value
    if result is None:
        payload = {"status": "idle", "durability": durability}
    else:
        payload = {
            "status": result.status.value,
            "durability": durability,
            "jobId": result.job_id,
        }
    print(json.dumps(payload, separators=(",", ":")))
    return 0


async def _check_postgres(database_url: str) -> None:
    repository = PostgresJobRepository(database_url)
    try:
        await repository.initialize()
    finally:
        await repository.close()


def main(argv: Sequence[str] | None = None) -> int:
    """Inspect durability or execute one bounded job from the configured queue."""

    args = _parser().parse_args(argv)
    database_url = os.environ.get("DEEPWORK_DATABASE_URL")
    if args.job_database is not None and database_url is not None:
        raise ValueError("configure either SQLite job proof or PostgreSQL jobs, not both")
    durability = (
        WorkerDurability.POSTGRES_OUTBOX
        if database_url is not None
        else (
            WorkerDurability.LOCAL_SQLITE_PROOF
            if args.job_database is not None
            else WorkerDurability.UNAVAILABLE
        )
    )
    if args.check:
        if database_url is not None:
            asyncio.run(_check_postgres(database_url))
        print(worker_status(durability=durability).model_dump_json())
        return 0
    if args.once and database_url is not None:
        return asyncio.run(_run_once(PostgresJobRepository(database_url), args.worker_id))
    if args.once and args.job_database is not None:
        return asyncio.run(_run_once(SQLiteJobRepository(args.job_database), args.worker_id))
    raise ValueError("worker requires --check or a configured database with --once")
