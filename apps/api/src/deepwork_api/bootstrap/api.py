"""FastAPI composition root and local CLI."""

import argparse
import os
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
from deepwork_api.adapters.sources.local import (
    LocalAgentServerSource,
    LocalSourceGatedError,
)
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
_LOCAL_SOURCE_GATED_MESSAGE = (
    "local Agent Server task execution is gated pending accepted live-contract "
    "evidence (SPIKE-SOURCE-001); it is a local-development-only capability and "
    "stays disabled unless the caller sets allow_ungated_local_agent_source=True "
    "(CLI: --allow-ungated-local-agent-source). The default runtime makes no "
    "provider/service calls."
)


def _build_local_agent_server_source(
    *,
    endpoint: str,
    assistant_id: str,
) -> LocalAgentServerSource:
    """Build the loopback source through the official SDK; test seam."""

    return LocalAgentServerSource.from_official_sdk(
        endpoint=endpoint,
        assistant_id=assistant_id,
    )


def create_app(
    *,
    task_database_path: Path | None = None,
    local_agent_server_endpoint: str | None = None,
    local_agent_server_assistant: str | None = None,
    allow_ungated_local_agent_source: bool = False,
) -> FastAPI:
    """Create the local application; loopback source execution is gated off by default.

    The default is credential-free deterministic fixture mode and makes no
    provider/service calls. Executing tasks through a real ``langgraph dev``
    Agent Server is a development-only capability that stays disabled until its
    contract gate (``SPIKE-SOURCE-001``) is accepted: supplying a loopback
    endpoint and assistant is not enough, the caller must also deliberately set
    ``allow_ungated_local_agent_source=True``. Without that opt-in the loopback
    configuration is refused before any source object is constructed.
    """

    status_service = StatusService(provider=FixtureStatusProvider())
    task_repository: TaskRepository
    task_runner: DeterministicFixtureRunner | LocalAgentServerRunner
    sqlite_repository: SQLiteTaskRepository | None
    if task_database_path is None:
        task_repository = InMemoryTaskRepository()
        sqlite_repository = None
    else:
        sqlite_repository = SQLiteTaskRepository(task_database_path)
        task_repository = sqlite_repository
    local_source: LocalAgentServerSource | None = None
    if local_agent_server_endpoint is None:
        if local_agent_server_assistant is not None:
            raise ValueError("local Agent Server assistant requires an explicit loopback endpoint")
        if allow_ungated_local_agent_source:
            raise ValueError(
                "allow_ungated_local_agent_source requires an explicit loopback endpoint "
                "and assistant"
            )
        task_runner = DeterministicFixtureRunner(repository=task_repository)
    else:
        # Fail closed before constructing any provider-calling source: the
        # capability is gated pending SPIKE-SOURCE-001 and reachable only through
        # a deliberate, documented local-development opt-in.
        if not allow_ungated_local_agent_source:
            raise LocalSourceGatedError(_LOCAL_SOURCE_GATED_MESSAGE)
        if task_database_path is not None:
            raise ValueError("local Agent Server mode does not support persistent task recovery")
        if local_agent_server_assistant is None:
            raise ValueError("local Agent Server mode requires an explicit assistant identifier")
        local_source = _build_local_agent_server_source(
            endpoint=local_agent_server_endpoint,
            assistant_id=local_agent_server_assistant,
        )
        task_runner = LocalAgentServerRunner(
            repository=task_repository,
            source=cast("LocalSource", local_source),
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
                if local_source is not None:
                    await local_source.close()

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
    parser.add_argument(
        "--local-agent-server-endpoint",
        default=os.environ.get("DEEPWORK_LOCAL_AGENT_ENDPOINT"),
        help=(
            "Explicit HTTP loopback IP origin of a langgraph dev Agent Server "
            "(for example http://127.0.0.1:2024); local development only, requires "
            "the assistant flag and --allow-ungated-local-agent-source. Defaults "
            "to the DEEPWORK_LOCAL_AGENT_ENDPOINT environment variable."
        ),
    )
    parser.add_argument(
        "--local-agent-server-assistant",
        default=os.environ.get("DEEPWORK_LOCAL_AGENT_ASSISTANT"),
        help=(
            "Assistant identifier registered on the loopback Agent Server. "
            "Defaults to the DEEPWORK_LOCAL_AGENT_ASSISTANT environment variable."
        ),
    )
    parser.add_argument(
        "--allow-ungated-local-agent-source",
        action="store_true",
        default=os.environ.get("DEEPWORK_ENABLE_LOCAL_AGENT") == "1",
        help=(
            "Deliberately opt in to the local-development-only loopback Agent "
            "Server task execution path, which is otherwise gated off pending "
            "accepted live-contract evidence (SPIKE-SOURCE-001). Without this "
            "flag the API runs in credential-free fixture mode and makes no "
            "provider/service calls. Defaults on when DEEPWORK_ENABLE_LOCAL_AGENT=1."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the credential-free local API on a fixed loopback host."""

    args = _parser().parse_args(argv)
    uvicorn.run(
        create_app(
            task_database_path=args.task_database,
            local_agent_server_endpoint=args.local_agent_server_endpoint,
            local_agent_server_assistant=args.local_agent_server_assistant,
            allow_ungated_local_agent_source=args.allow_ungated_local_agent_source,
        ),
        host="127.0.0.1",
        port=args.port,
        access_log=False,
    )
    return 0
