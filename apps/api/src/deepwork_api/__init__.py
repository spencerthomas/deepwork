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
) -> FastAPI:
    """Load and create the local application only when explicitly called.

    The default stays in credential-free deterministic fixture mode and makes no
    provider/service calls. Executing tasks through a local ``langgraph dev``
    Agent Server is a development-only capability gated pending accepted
    live-contract evidence (``SPIKE-SOURCE-001``): the caller must supply an
    explicit loopback endpoint and assistant *and* deliberately set
    ``allow_ungated_local_agent_source=True``, otherwise the loopback
    configuration is refused before any source is constructed. Anything except
    an explicit HTTP loopback IP origin is rejected before any network use.
    """

    from deepwork_api.bootstrap.api import create_app as _create_app

    return _create_app(
        task_database_path=task_database_path,
        local_agent_server_endpoint=local_agent_server_endpoint,
        local_agent_server_assistant=local_agent_server_assistant,
        allow_ungated_local_agent_source=allow_ungated_local_agent_source,
    )
