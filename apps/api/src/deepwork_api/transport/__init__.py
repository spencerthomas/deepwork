"""FastAPI transport boundary."""

from deepwork_api.transport.agents import build_agents_router
from deepwork_api.transport.auth import build_auth_router, build_session_guard
from deepwork_api.transport.http import build_router
from deepwork_api.transport.settings import build_settings_router
from deepwork_api.transport.tasks import build_task_router

__all__ = [
    "build_agents_router",
    "build_auth_router",
    "build_router",
    "build_session_guard",
    "build_settings_router",
    "build_task_router",
]
