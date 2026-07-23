"""HTTP routes for the fixture-only scaffold."""

from fastapi import APIRouter

from deepwork_api.application import StatusService
from deepwork_api.contracts import DemoStatusResponse, HealthResponse


def build_router(service: StatusService) -> APIRouter:
    """Build routes around an explicitly supplied application service."""

    router = APIRouter()

    @router.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        """Return process liveness only."""

        return HealthResponse.from_domain(service.health())

    @router.get("/api/v1/demo/status", response_model=DemoStatusResponse)
    async def demo_status() -> DemoStatusResponse:
        """Return deterministic fixture-only capability status."""

        return DemoStatusResponse.from_domain(service.demo())

    return router
