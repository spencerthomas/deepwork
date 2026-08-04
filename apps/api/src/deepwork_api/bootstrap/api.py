"""FastAPI composition root and local CLI."""

import argparse
import os
from collections.abc import AsyncIterator, Mapping, Sequence
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
from deepwork_api.adapters.persistence import (
    PostgresJobRepository,
    SQLiteJobRepository,
    SQLiteTaskRepository,
)
from deepwork_api.adapters.prompt import InMemoryPromptStore, SQLitePromptStore
from deepwork_api.adapters.sources.classic.probe import ClassicSourceProbeClient
from deepwork_api.adapters.sources.classic.runtime import ClassicDeploymentSource
from deepwork_api.adapters.sources.local import (
    LocalAgentServerSource,
    LocalSourceGatedError,
)
from deepwork_api.adapters.sources.status import SourceStatusProvider
from deepwork_api.adapters.trace import LangSmithTraceLocator
from deepwork_api.application import (
    AuthService,
    DeterministicFixtureRunner,
    JobService,
    LocalAgentServerRunner,
    SourceService,
    StatusService,
    TaskService,
)
from deepwork_api.application.local_runner import LocalSource
from deepwork_api.bootstrap.source_probe_config import SourceProbeConfig
from deepwork_api.domain import (
    DEFAULT_SECURITY_CONTEXT,
    RuntimeKind,
    TaskEventName,
    TaskStatus,
)
from deepwork_api.domain import SecurityContext as SecurityContext
from deepwork_api.ports import (
    Clock,
    JobRepository,
    PromptStore,
    StatusProvider,
    TaskRepository,
    system_clock,
)
from deepwork_api.ports import SourceProbeClient as SourceProbeClient
from deepwork_api.transport import (
    build_agents_router,
    build_auth_router,
    build_job_router,
    build_router,
    build_schedules_router,
    build_session_guard,
    build_settings_router,
    build_sources_router,
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


def _open_security_context() -> SecurityContext:
    return DEFAULT_SECURITY_CONTEXT


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
    job_database_path: Path | None = None,
    job_database_url: str | None = None,
    local_agent_server_endpoint: str | None = None,
    local_agent_server_assistant: str | None = None,
    allow_ungated_local_agent_source: bool = False,
    classic_deployment_endpoint: str | None = None,
    classic_deployment_assistant: str | None = None,
    classic_deployment_credential: str | None = None,
    source_probe_config: SourceProbeConfig | None = None,
    source_probe_client: SourceProbeClient | None = None,
    access_key: str | None = None,
    access_key_contexts: Mapping[str, SecurityContext] | None = None,
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

    status_provider: StatusProvider = FixtureStatusProvider(
        authentication_enabled=access_key is not None or access_key_contexts is not None
    )
    if source_probe_client is not None and source_probe_config is None:
        raise ValueError("a source probe client requires server-owned source probe settings")
    if source_probe_config is not None and len(source_probe_config.allowed_endpoints) != 1:
        raise ValueError("classic source qualification requires exactly one configured target")
    configured_probe_client = source_probe_client
    if configured_probe_client is None and source_probe_config is not None:
        configured_probe_client = ClassicSourceProbeClient(
            source_probe_config.credential,
            allowed_endpoints=source_probe_config.allowed_endpoints,
        )
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
        status_provider = SourceStatusProvider(
            runtime_kind=RuntimeKind.CLASSIC_DEPLOYMENT,
            authentication_enabled=access_key is not None or access_key_contexts is not None,
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
        status_provider = SourceStatusProvider(
            runtime_kind=RuntimeKind.LOCAL_AGENT_SERVER,
            authentication_enabled=access_key is not None or access_key_contexts is not None,
        )
    task_service = TaskService(repository=task_repository, runner=task_runner)
    trace_locator = _build_trace_locator(api_key=trace_api_key) if trace_api_key else None
    if job_database_path is not None and job_database_url is not None:
        raise ValueError("configure either SQLite job proof or PostgreSQL jobs, not both")
    if (
        (job_database_path is not None or job_database_url is not None)
        and access_key is None
        and access_key_contexts is None
    ):
        raise ValueError("durable jobs require configured session authentication")
    job_repository: JobRepository | None
    if job_database_url is not None:
        job_repository = PostgresJobRepository(job_database_url)
    elif job_database_path is not None:
        job_repository = SQLiteJobRepository(job_database_path)
    else:
        job_repository = None
    status_service = StatusService(
        provider=status_provider,
        job_durability=(job_repository.durability if job_repository is not None else None),
    )

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
            if job_repository is not None:
                await job_repository.initialize()
            yield
        finally:
            try:
                await task_runner.close()
            finally:
                await prompt_store.close()
                if sqlite_repository is not None:
                    await sqlite_repository.close()
                if job_repository is not None:
                    await job_repository.close()
                if local_source is not None:
                    await local_source.close()
                if trace_locator is not None:
                    await trace_locator.close()
                if source_service is not None:
                    await source_service.close()

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
    if access_key is not None and access_key_contexts is not None:
        raise ValueError("configure either one access key or an access key context mapping")
    auth_service = (
        AuthService(
            store=InMemorySessionStore(),
            access_key=access_key,
            access_key_contexts=access_key_contexts,
        )
        if access_key is not None or access_key_contexts is not None
        else None
    )
    auth_guard = build_session_guard(auth_service) if auth_service else None
    task_dependencies = [Depends(auth_guard)] if auth_guard else None
    job_service = JobService(repository=job_repository) if job_repository is not None else None
    if configured_probe_client is not None and auth_guard is None:
        raise ValueError("source qualification requires configured session authentication")
    source_service = (
        SourceService(
            configured_probe_client,
            endpoint=source_probe_config.allowed_endpoints[0],
            tenant_id=source_probe_config.tenant_id,
            workspace_id=source_probe_config.workspace_id,
        )
        if configured_probe_client is not None and source_probe_config is not None
        else None
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(web_origins or _WEB_ORIGINS),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Idempotency-Key", "Last-Event-ID", "Authorization"],
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

    app.include_router(build_router(status_service, status_dependencies=task_dependencies))
    app.include_router(
        build_task_router(
            task_service,
            security_context_dependency=(auth_guard if auth_guard else _open_security_context),
            trace_locator=trace_locator,
            require_idempotency_key=auth_guard is not None,
        )
    )
    app.include_router(
        build_settings_router(
            prompt_store,
            security_context_dependency=(auth_guard if auth_guard else _open_security_context),
        )
    )
    app.include_router(
        build_sources_router(
            source_service,
            security_context_dependency=(auth_guard if auth_guard else _open_security_context),
        )
    )
    app.include_router(build_agents_router(task_service, dependencies=task_dependencies))
    app.include_router(build_schedules_router(task_service, dependencies=task_dependencies))
    if job_service is not None:
        if auth_guard is None:
            raise RuntimeError("durable jobs require the session guard")
        app.include_router(build_job_router(job_service, security_context_dependency=auth_guard))
    if auth_service is not None:
        app.include_router(build_auth_router(auth_service))
        generated_openapi = app.openapi

        def authenticated_openapi() -> dict[str, object]:
            """Publish the stricter authenticated create contract."""

            document = generated_openapi()
            paths = cast(dict[str, object], document["paths"])
            task_path = cast(dict[str, object], paths["/api/v1/tasks"])
            operation = cast(dict[str, object], task_path["post"])
            parameters = cast(list[dict[str, object]], operation["parameters"])
            for parameter in parameters:
                if parameter.get("in") == "header" and parameter.get("name") == "Idempotency-Key":
                    parameter["required"] = True
                    break
            return document

        app.openapi = authenticated_openapi  # type: ignore[method-assign]
    app.state.task_repository = task_repository
    app.state.task_runner = task_runner
    app.state.task_service = task_service
    app.state.auth_service = auth_service
    app.state.job_repository = job_repository
    app.state.job_service = job_service
    app.state.source_service = source_service
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
        "--job-database",
        type=Path,
        default=(
            Path(os.environ["DEEPWORK_JOB_DB"]) if os.environ.get("DEEPWORK_JOB_DB") else None
        ),
        help=(
            "Absolute SQLite path for the authenticated local-sqlite-proof job queue. "
            "Requires DEEPWORK_ACCESS_KEY. Defaults to DEEPWORK_JOB_DB."
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
    raw_probe_endpoints = os.environ.get("DEEPWORK_SOURCE_PROBE_ENDPOINTS")
    source_probe_allowed_endpoints = tuple(
        endpoint.strip() for endpoint in (raw_probe_endpoints or "").split(",") if endpoint.strip()
    )
    if args.classic_deployment_endpoint is not None:
        source_probe_allowed_endpoints = (
            *source_probe_allowed_endpoints,
            args.classic_deployment_endpoint,
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
            job_database_path=args.job_database,
            job_database_url=os.environ.get("DEEPWORK_DATABASE_URL"),
            local_agent_server_endpoint=args.local_agent_server_endpoint,
            local_agent_server_assistant=args.local_agent_server_assistant,
            allow_ungated_local_agent_source=args.allow_ungated_local_agent_source,
            classic_deployment_endpoint=args.classic_deployment_endpoint,
            classic_deployment_assistant=args.classic_deployment_assistant,
            classic_deployment_credential=(
                classic_credential if args.classic_deployment_endpoint is not None else None
            ),
            source_probe_config=(
                SourceProbeConfig(
                    credential=classic_credential,
                    allowed_endpoints=source_probe_allowed_endpoints,
                )
                if source_probe_allowed_endpoints and classic_credential is not None
                else None
            ),
            access_key=access_key,
            web_origins=web_origins,
            trace_api_key=trace_api_key,
        ),
        host=host,
        port=port,
        access_log=False,
    )
    return 0
