"""Worker composition root with an explicit unavailable durability result."""

import argparse
from collections.abc import Sequence

from deepwork_api.adapters.fixture import FixtureStatusProvider
from deepwork_api.application import StatusService
from deepwork_api.contracts import WorkerStatusResponse


def worker_status() -> WorkerStatusResponse:
    """Return fixture worker status without accepting durable work."""

    service = StatusService(provider=FixtureStatusProvider())
    return WorkerStatusResponse.from_domain(service.worker())


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect the non-durable scaffold worker.")
    parser.add_argument("--check", action="store_true", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Print the worker's explicit unavailable durability state."""

    _parser().parse_args(argv)
    print(worker_status().model_dump_json())
    return 0
