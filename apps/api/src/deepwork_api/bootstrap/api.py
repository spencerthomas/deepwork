"""FastAPI composition root and local CLI."""

import argparse
from collections.abc import Sequence

import uvicorn
from fastapi import FastAPI

from deepwork_api.adapters.fixture import FixtureStatusProvider
from deepwork_api.application import StatusService
from deepwork_api.transport import build_router


def create_app() -> FastAPI:
    """Create the fixture-only application without import-time side effects."""

    service = StatusService(provider=FixtureStatusProvider())
    app = FastAPI(
        title="Deep Work API fixture scaffold",
        version="0.0.0",
        description="Credential-free fixture behavior; no live provider contract.",
        docs_url=None,
        redoc_url=None,
    )
    app.include_router(build_router(service))
    return app


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the fixture-only Deep Work API on loopback.")
    parser.add_argument("--port", type=int, default=8000)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the fixture-only API on a fixed loopback host."""

    args = _parser().parse_args(argv)
    uvicorn.run(create_app(), host="127.0.0.1", port=args.port, access_log=False)
    return 0
