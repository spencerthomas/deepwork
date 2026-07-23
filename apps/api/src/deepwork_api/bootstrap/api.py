"""FastAPI composition root and local CLI."""

import argparse
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from deepwork_api.adapters.fixture import FixtureStatusProvider, InMemoryTaskRepository
from deepwork_api.application import DeterministicFixtureRunner, StatusService, TaskService
from deepwork_api.transport import build_router, build_task_router

_WEB_ORIGINS = ("http://localhost:3000", "http://127.0.0.1:3000")


def create_app() -> FastAPI:
    """Create the fixture-only application without import-time side effects."""

    status_service = StatusService(provider=FixtureStatusProvider())
    task_repository = InMemoryTaskRepository()
    task_runner = DeterministicFixtureRunner(repository=task_repository)
    task_service = TaskService(repository=task_repository, runner=task_runner)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await task_runner.close()

    app = FastAPI(
        title="Deep Work API fixture scaffold",
        version="0.0.0",
        description=("Credential-free local task and fixture behavior; no live provider contract."),
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(_WEB_ORIGINS),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Last-Event-ID"],
    )

    @app.exception_handler(RequestValidationError)
    async def safe_validation_error(
        _request: Request,
        _error: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "code": "request_invalid",
                "message": "Request validation failed.",
            },
        )

    app.include_router(build_router(status_service))
    app.include_router(build_task_router(task_service))
    app.state.task_repository = task_repository
    app.state.task_runner = task_runner
    app.state.task_service = task_service
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
