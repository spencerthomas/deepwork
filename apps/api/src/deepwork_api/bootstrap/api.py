"""FastAPI composition root and local CLI."""

import argparse
import os
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import cast

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from deepwork_api.adapters.auth import InMemorySessionStore
from deepwork_api.adapters.fixture import FixtureStatusProvider, InMemoryTaskRepository
from deepwork_api.adapters.persistence import SQLiteTaskRepository
from deepwork_api.adapters.prompt import InMemoryPromptStore, SQLitePromptStore
from deepwork_api.adapters.sources.classic.runtime import ClassicDeploymentSource
from deepwork_api.adapters.sources.local import (
    LocalAgentServerSource,
    LocalSourceGatedError,
)
from deepwork_api.adapters.trace import LangSmithTraceLocator
from deepwork_api.application import (
    AuthService,
    DeterministicFixtureRunner,
    LocalAgentServerRunner,
    StatusService,
    TaskService,
)
from deepwork_api.application.local_runner import LocalSource
from deepwork_api.domain import TaskEventName, TaskStatus
from deepwork_api.ports import Clock, PromptStore, TaskRepository, system_clock
from deepwork_api.transport import (
    build_agents_router,
    build_auth_router,
    build_router,
    build_schedules_router,
    build_session_guard,
    build_settings_router,
    build_task_router,
)

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


def _build_classic_deployment_source(
    *,
    endpoint: str,
    assistant_id: str,
    credential: str,
) -> ClassicDeploymentSource:
    """Build the hosted classic deployment source through the SDK; test seam."""

    return ClassicDeploymentSource.from_classic_deployment(
        endpoint=endpoint,
        assistant_id=assistant_id,
        credential=credential,
    )


def _build_trace_locator(*, api_key: str) -> LangSmithTraceLocator:
    """Build the LangSmith trace locator; test seam."""

    return LangSmithTraceLocator(api_key=api_key)


def create_app(
    *,
    task_database_path: Path | None = None,
    settings_database_path: Path | None = None,
    local_agent_server_endpoint: str | None = None,
    local_agent_server_assistant: str | None = None,
    allow_ungated_local_agent_source: bool = False,
    classic_deployment_endpoint: str | None = None,
    classic_deployment_assistant: str | None = None,
    classic_deployment_credential: str | None = None,
    access_key: str | None = None,
    web_origins: tuple[str, ...] | None = None,
    trace_api_key: str | None = None,
    clock: Clock = system_clock,
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
        task_repository = InMemoryTaskRepository(clock=clock)
        sqlite_repository = None
    else:
        sqlite_repository = SQLiteTaskRepository(task_database_path, clock=clock)
        task_repository = sqlite_repository
    # The editable workspace system prompt is durable when a settings database is
    # configured, otherwise process-local. It lives in its own small store rather
    # than the versioned task schema.
    prompt_store: PromptStore = (
        SQLitePromptStore(settings_database_path)
        if settings_database_path is not None
        else InMemoryPromptStore()
    )
    local_source: LocalAgentServerSource | None = None
    if classic_deployment_endpoint is not None:
        # Hosted classic LangSmith/LangGraph Deployment runtime. Mutually
        # exclusive with the loopback source; the deployment credential stays
        # server-held and never enters a response.
        if local_agent_server_endpoint is not None:
            raise ValueError(
                "configure either the local Agent Server or a classic deployment, not both"
            )
        if not allow_ungated_local_agent_source:
            raise LocalSourceGatedError(_LOCAL_SOURCE_GATED_MESSAGE)
        if classic_deployment_assistant is None:
            raise ValueError("classic deployment mode requires an explicit assistant identifier")
        if not classic_deployment_credential:
            raise ValueError("classic deployment mode requires a server-held deployment credential")
        local_source = _build_classic_deployment_source(
            endpoint=classic_deployment_endpoint,
            assistant_id=classic_deployment_assistant,
            credential=classic_deployment_credential,
        )
        task_runner = LocalAgentServerRunner(
            repository=task_repository,
            source=cast("LocalSource", local_source),
            prompt_store=prompt_store,
        )
    elif local_agent_server_endpoint is None:
        if local_agent_server_assistant is not None:
            raise ValueError("local Agent Server assistant requires an explicit loopback endpoint")
        if classic_deployment_assistant is not None or classic_deployment_credential is not None:
            raise ValueError("classic deployment settings require an explicit deployment endpoint")
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
        if local_agent_server_assistant is None:
            raise ValueError("local Agent Server mode requires an explicit assistant identifier")
        local_source = _build_local_agent_server_source(
            endpoint=local_agent_server_endpoint,
            assistant_id=local_agent_server_assistant,
        )
        task_runner = LocalAgentServerRunner(
            repository=task_repository,
            source=cast("LocalSource", local_source),
            prompt_store=prompt_store,
        )
    task_service = TaskService(repository=task_repository, runner=task_runner)
    trace_locator = _build_trace_locator(api_key=trace_api_key) if trace_api_key else None

    async def _reconcile_orphaned_tasks() -> None:
        """Fail-closed recovery for any persisted task after a process restart.

        Persisted history and results survive as-is. A task that was still in
        flight when the process died has lost its in-memory follower and thread
        binding, so it is marked failed with an honest reason instead of being
        shown as running forever. The deterministic fixture runner also owns
        process-local waiters, so it follows the same honest recovery rule.
        """
        for task in await task_repository.list_tasks():
            if task.status.is_terminal:
                continue
            await task_repository.append_event(
                task.task_id,
                name=TaskEventName.RUN_COMPLETED,
                data=(
                    ("runId", task.run_id),
                    ("status", "failed"),
                    ("safeReason", "The service restarted while this task was in progress."),
                    ("resultAvailable", False),
                ),
                status=TaskStatus.FAILED,
                clear_pending_interrupt=True,
            )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            if sqlite_repository is not None:
                await sqlite_repository.initialize()
                await _reconcile_orphaned_tasks()
            yield
        finally:
            try:
                await task_runner.close()
            finally:
                await prompt_store.close()
                if sqlite_repository is not None:
                    await sqlite_repository.close()
                if local_source is not None:
                    await local_source.close()
                if trace_locator is not None:
                    await trace_locator.close()

    app = FastAPI(
        title="Deep Work API fixture scaffold",
        version="0.0.0",
        description=("Credential-free local task and fixture behavior; no live provider contract."),
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )
    # Authentication is enabled only when an access key is configured. The key is
    # read on the server and never returned; task routes are then guarded and the
    # /api/v1/auth routes are exposed. Without a key the API stays open (fixture
    # and local-development default).
    auth_service = (
        AuthService(store=InMemorySessionStore(), access_key=access_key) if access_key else None
    )
    task_dependencies = [Depends(build_session_guard(auth_service))] if auth_service else None

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(web_origins or _WEB_ORIGINS),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Last-Event-ID", "Authorization"],
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

    @app.exception_handler(HTTPException)
    async def problem_http_exception(request: Request, error: HTTPException) -> JSONResponse:
        # Render structured problem bodies (for example the auth guard's 401)
        # while preserving FastAPI's default rendering for plain-string details.
        detail: object = error.detail
        if isinstance(detail, dict):
            return JSONResponse(status_code=error.status_code, content=detail)
        return cast("JSONResponse", await http_exception_handler(request, error))

    app.include_router(build_router(status_service))
    app.include_router(
        build_task_router(
            task_service,
            dependencies=task_dependencies,
            trace_locator=trace_locator,
        )
    )
    app.include_router(build_settings_router(prompt_store, dependencies=task_dependencies))
    app.include_router(build_agents_router(task_service, dependencies=task_dependencies))
    app.include_router(build_schedules_router(task_service, dependencies=task_dependencies))
    if auth_service is not None:
        app.include_router(build_auth_router(auth_service))
    app.state.task_repository = task_repository
    app.state.task_runner = task_runner
    app.state.task_service = task_service
    app.state.auth_service = auth_service
    return app


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the fixture-only Deep Work API on loopback.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--task-database",
        type=Path,
        default=(
            Path(os.environ["DEEPWORK_TASK_DB"]) if os.environ.get("DEEPWORK_TASK_DB") else None
        ),
        help=(
            "Absolute path to a SQLite database for durable task persistence "
            "(fixture and real-agent modes). Defaults to the DEEPWORK_TASK_DB "
            "environment variable."
        ),
    )
    parser.add_argument(
        "--settings-database",
        type=Path,
        default=(
            Path(os.environ["DEEPWORK_SETTINGS_DB"])
            if os.environ.get("DEEPWORK_SETTINGS_DB")
            else None
        ),
        help=(
            "Absolute path to a small SQLite database for durable workspace "
            "settings (the editable system prompt). Defaults to the "
            "DEEPWORK_SETTINGS_DB environment variable, or a sibling of "
            "--task-database when that is set."
        ),
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
    parser.add_argument(
        "--classic-deployment-endpoint",
        default=os.environ.get("DEEPWORK_CLASSIC_ENDPOINT"),
        help=(
            "Qualified HTTPS origin of a hosted classic LangSmith/LangGraph "
            "Deployment (for example https://my-deployment.smith.langchain.com). "
            "Requires the classic assistant flag, a credential, and "
            "--allow-ungated-local-agent-source. Defaults to the "
            "DEEPWORK_CLASSIC_ENDPOINT environment variable."
        ),
    )
    parser.add_argument(
        "--classic-deployment-assistant",
        default=os.environ.get("DEEPWORK_CLASSIC_ASSISTANT"),
        help=(
            "Assistant/graph identifier on the classic deployment. Defaults to the "
            "DEEPWORK_CLASSIC_ASSISTANT environment variable."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the credential-free local API on a fixed loopback host."""

    args = _parser().parse_args(argv)
    # Credentials and the access key are only ever read from the server environment.
    classic_credential = os.environ.get("DEEPWORK_CLASSIC_CREDENTIAL") or os.environ.get(
        "LANGSMITH_API_KEY"
    )
    access_key = os.environ.get("DEEPWORK_ACCESS_KEY")
    trace_api_key = os.environ.get("LANGSMITH_API_KEY")
    raw_origins = os.environ.get("DEEPWORK_WEB_ORIGINS")
    web_origins = (
        tuple(origin.strip() for origin in raw_origins.split(",") if origin.strip())
        if raw_origins
        else None
    )
    # Hosting platforms (Railway, etc.) inject $PORT and require binding 0.0.0.0.
    # Local default stays loopback so nothing is exposed unless deliberately hosted.
    host = os.environ.get("DEEPWORK_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", str(args.port)))
    # Keep the durable setting alongside the task database unless overridden, so a
    # single persistent volume covers both.
    settings_database_path = args.settings_database
    if settings_database_path is None and args.task_database is not None:
        settings_database_path = args.task_database.with_name("settings.sqlite3")
    uvicorn.run(
        create_app(
            task_database_path=args.task_database,
            settings_database_path=settings_database_path,
            local_agent_server_endpoint=args.local_agent_server_endpoint,
            local_agent_server_assistant=args.local_agent_server_assistant,
            allow_ungated_local_agent_source=args.allow_ungated_local_agent_source,
            classic_deployment_endpoint=args.classic_deployment_endpoint,
            classic_deployment_assistant=args.classic_deployment_assistant,
            classic_deployment_credential=classic_credential,
            access_key=access_key,
            web_origins=web_origins,
            trace_api_key=trace_api_key,
        ),
        host=host,
        port=port,
        access_log=False,
    )
    return 0
