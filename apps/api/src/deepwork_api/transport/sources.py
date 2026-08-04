"""Authenticated API for read-only source qualification."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from deepwork_api.application import (
    DEFAULT_SECURITY_CONTEXT,
    SecurityContext,
    SourceEndpointInvalidError,
    SourceService,
    SourceTargetUnavailableError,
)
from deepwork_api.contracts import ProblemResponse, SourceProbeRequest, SourceProbeResponse


def _default_security_context() -> SecurityContext:
    return DEFAULT_SECURITY_CONTEXT


def build_sources_router(
    service: SourceService | None,
    *,
    security_context_dependency: Callable[
        ..., SecurityContext | Awaitable[SecurityContext]
    ] = _default_security_context,
) -> APIRouter:
    """Build source qualification routes around an optional configured service."""

    router = APIRouter(prefix="/api/v1/sources", tags=["sources"])
    security_context_marker = Depends(security_context_dependency)

    @router.post(
        "/probes",
        response_model=SourceProbeResponse,
        responses={
            401: {"model": ProblemResponse},
            404: {"model": ProblemResponse},
            422: {"model": ProblemResponse},
            503: {"model": ProblemResponse},
        },
    )
    async def probe_source(
        request: SourceProbeRequest,
        security_context: SecurityContext = security_context_marker,
    ) -> SourceProbeResponse | JSONResponse:
        if service is None:
            problem = ProblemResponse(
                code="source_probe_unavailable",
                message="No server-held source credential is configured for connection checks.",
            )
            return JSONResponse(
                status_code=503,
                content=problem.model_dump(),
            )
        try:
            result = await service.probe_classic(
                security_context,
                request.source_target_id,
                request.assistant_id,
            )
        except SourceTargetUnavailableError:
            problem = ProblemResponse(
                code="source_target_unavailable",
                message="The source target is not available in this workspace.",
            )
            return JSONResponse(status_code=404, content=problem.model_dump())
        except SourceEndpointInvalidError:
            problem = ProblemResponse(
                code="source_endpoint_invalid",
                message="The deployment URL is not an allowed hosted HTTPS endpoint.",
            )
            return JSONResponse(
                status_code=422,
                content=problem.model_dump(),
            )
        return SourceProbeResponse.from_domain(result)

    return router
