"""HTTP routes for process and configured-runtime status."""

from typing import Any

from fastapi import APIRouter

from deepwork_api.application import StatusService
from deepwork_api.contracts import DemoStatusResponse, HealthResponse


def build_router(
    service: StatusService,
    *,
    status_dependencies: list[Any] | None = None,
) -> APIRouter:
    """Build public health and optionally guarded runtime-status routes."""

    router = APIRouter()

    @router.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        """Return process liveness only."""

        return HealthResponse.from_domain(service.health())

    @router.get(
        "/api/v1/runtime/status",
        response_model=DemoStatusResponse,
        dependencies=status_dependencies or [],
    )
    async def runtime_status() -> DemoStatusResponse:
        """Return credential-free configured runtime capability status."""

        return DemoStatusResponse.from_domain(service.demo())

    @router.get(
        "/api/v1/demo/status",
        response_model=DemoStatusResponse,
        deprecated=True,
        dependencies=status_dependencies or [],
    )
    async def demo_status() -> DemoStatusResponse:
        """Retain the original fixture-era path as a compatible read alias."""

        return await runtime_status()

    return router
