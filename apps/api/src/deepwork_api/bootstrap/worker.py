"""Separate worker composition root for the local SQLite durability proof."""

import argparse
import asyncio
import json
from collections.abc import Sequence
from pathlib import Path

from deepwork_api.adapters.fixture import FixtureStatusProvider
from deepwork_api.adapters.persistence import SQLiteJobRepository
from deepwork_api.application import JobWorker, StatusService
from deepwork_api.contracts import WorkerStatusResponse
from deepwork_api.domain import EvidenceClass, WorkerDurability, WorkerStatus


def worker_status(*, durable: bool = False) -> WorkerStatusResponse:
    """Return the configured worker durability without production claims."""

    if not durable:
        service = StatusService(provider=FixtureStatusProvider())
        return WorkerStatusResponse.from_domain(service.worker())
    return WorkerStatusResponse.from_domain(
        WorkerStatus(
            mode=EvidenceClass.FIXTURE,
            durability=WorkerDurability.LOCAL_SQLITE_PROOF,
            safe_reason="local SQLite durability proof; not production PostgreSQL",
        )
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run or inspect the Deep Work worker.")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--job-database", type=Path)
    parser.add_argument("--worker-id", default="worker-local")
    parser.add_argument("--once", action="store_true")
    return parser


async def _run_once(database: Path, worker_id: str) -> int:
    repository = SQLiteJobRepository(database)
    await repository.initialize()
    try:
        result = await JobWorker(repository=repository, worker_id=worker_id).run_once()
    finally:
        await repository.close()
    if result is None:
        payload = {"status": "idle", "durability": "local-sqlite-proof"}
    else:
        payload = {
            "status": result.status.value,
            "durability": "local-sqlite-proof",
            "jobId": result.job_id,
        }
    print(json.dumps(payload, separators=(",", ":")))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Inspect durability or execute one bounded job from the configured queue."""

    args = _parser().parse_args(argv)
    if args.check:
        print(worker_status(durable=args.job_database is not None).model_dump_json())
        return 0
    if args.once and args.job_database is not None:
        return asyncio.run(_run_once(args.job_database, args.worker_id))
    raise ValueError("worker requires --check or --job-database with --once")
