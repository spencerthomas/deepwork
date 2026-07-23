"""FastAPI composition root and local CLI."""

import argparse
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import cast

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from deepwork_api.adapters.fixture import FixtureStatusProvider, InMemoryTaskRepository
from deepwork_api.adapters.persistence import SQLiteTaskRepository
from deepwork_api.adapters.sources.local import LocalAgentServerSource
from deepwork_api.application import (
    DeterministicFixtureRunner,
    LocalAgentServerRunner,
    StatusService,
    TaskService,
)
from deepwork_api.application.local_runner import LocalSource
from deepwork_api.ports import TaskRepository
from deepwork_api.transport import build_router, build_task_router

_WEB_ORIGINS = ("http://localhost:3000", "http://127.0.0.1:3000")


def create_app(
    *,
    task_database_path: Path | None = None,
    local_agent_server_endpoint: str | None = None,
    local_agent_server_assistant: str | None = None,
) -> FastAPI:
    """Create the local fixture application with optional explicit SQLite persistence."""

    status_service = StatusService(provider=FixtureStatusProvider())
    task_repository: TaskRepository
    sqlite_repository: SQLiteTaskRepository | None
    if task_database_path is None:
        task_repository = InMemoryTaskRepository()
        sqlite_repository = None
    else:
        sqlite_repository = SQLiteTaskRepository(task_database_path)
        task_repository = sqlite_repository
    if local_agent_server_endpoint is None:
        if local_agent_server_assistant is not None:
            raise ValueError("local Agent Server assistant requires an explicit loopback endpoint")
        task_runner = DeterministicFixtureRunner(repository=task_repository)
    else:
        if task_database_path is not None:
            raise ValueError("local Agent Server mode does not support persistent task recovery")
        if local_agent_server_assistant is None:
            raise ValueError("local Agent Server mode requires an explicit assistant identifier")
        source = LocalAgentServerSource.from_official_sdk(
            endpoint=local_agent_server_endpoint,
            assistant_id=local_agent_server_assistant,
        )
        task_runner = LocalAgentServerRunner(
            repository=task_repository,
            source=cast(LocalSource, source),
        )
    task_service = TaskService(repository=task_repository, runner=task_runner)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            if sqlite_repository is not None:
                await sqlite_repository.initialize()
            yield
        finally:
            try:
                await task_runner.close()
            finally:
                if sqlite_repository is not None:
                    await sqlite_repository.close()
                if local_agent_server_endpoint is not None:
                    await source.close()

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
    parser.add_argument(
        "--task-database",
        type=Path,
        help="Absolute path to a SQLite database for local fixture persistence.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the fixture-only API on a fixed loopback host."""

    args = _parser().parse_args(argv)
    uvicorn.run(
        create_app(task_database_path=args.task_database),
        host="127.0.0.1",
        port=args.port,
        access_log=False,
    )
    return 0
