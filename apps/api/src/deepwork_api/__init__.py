"""Public entry points for the Deep Work application-service scaffold."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from fastapi import FastAPI

__all__ = ["create_app"]


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
    clock: Callable[[], datetime] | None = None,
) -> FastAPI:
    """Load and create the local application only when explicitly called.

    The default stays in credential-free deterministic fixture mode and makes no
    provider/service calls. Two real-agent paths exist, both gated behind
    ``allow_ungated_local_agent_source=True``: a local ``langgraph dev`` Agent
    Server, and a hosted classic LangSmith/LangGraph Deployment via a qualified
    HTTPS ``classic_deployment_endpoint``, an assistant, and a server-held
    ``classic_deployment_credential`` that is never returned to a client.

    Setting ``access_key`` enables session authentication on the task routes;
    ``web_origins`` overrides the allowed CORS origins for a hosted frontend.
    """

    from deepwork_api.bootstrap.api import create_app as _create_app

    kwargs: dict[str, object] = {
        "task_database_path": task_database_path,
        "settings_database_path": settings_database_path,
        "local_agent_server_endpoint": local_agent_server_endpoint,
        "local_agent_server_assistant": local_agent_server_assistant,
        "allow_ungated_local_agent_source": allow_ungated_local_agent_source,
        "classic_deployment_endpoint": classic_deployment_endpoint,
        "classic_deployment_assistant": classic_deployment_assistant,
        "classic_deployment_credential": classic_deployment_credential,
        "access_key": access_key,
        "web_origins": web_origins,
        "trace_api_key": trace_api_key,
    }
    # Forward an explicit clock only when supplied; otherwise the bootstrap
    # default (system_clock) applies, so this facade never imports it directly.
    if clock is not None:
        kwargs["clock"] = clock
    return _create_app(**kwargs)
