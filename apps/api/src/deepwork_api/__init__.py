"""Public entry points for the Deep Work application-service scaffold."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

__all__ = ["create_app"]


def create_app(
    *,
    task_database_path: Path | None = None,
    local_agent_server_endpoint: str | None = None,
    local_agent_server_assistant: str | None = None,
    allow_ungated_local_agent_source: bool = False,
    classic_deployment_endpoint: str | None = None,
    classic_deployment_assistant: str | None = None,
    classic_deployment_credential: str | None = None,
) -> FastAPI:
    """Load and create the local application only when explicitly called.

    The default stays in credential-free deterministic fixture mode and makes no
    provider/service calls. Two real-agent paths exist, both gated behind
    ``allow_ungated_local_agent_source=True``:

    * a local ``langgraph dev`` Agent Server via an explicit loopback endpoint
      and assistant (development-only, ``SPIKE-SOURCE-001``); and
    * a hosted classic LangSmith/LangGraph Deployment via a qualified HTTPS
      ``classic_deployment_endpoint``, an assistant, and a server-held
      ``classic_deployment_credential`` that is never returned to a client.

    Without the opt-in, either configuration is refused before any source is
    constructed.
    """

    from deepwork_api.bootstrap.api import create_app as _create_app

    return _create_app(
        task_database_path=task_database_path,
        local_agent_server_endpoint=local_agent_server_endpoint,
        local_agent_server_assistant=local_agent_server_assistant,
        allow_ungated_local_agent_source=allow_ungated_local_agent_source,
        classic_deployment_endpoint=classic_deployment_endpoint,
        classic_deployment_assistant=classic_deployment_assistant,
        classic_deployment_credential=classic_deployment_credential,
    )
