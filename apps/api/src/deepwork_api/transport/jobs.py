"""Session-authenticated durable-job HTTP routes."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Path
from fastapi.responses import JSONResponse

from deepwork_api.application import JobNotFoundError, JobService, SecurityContext
from deepwork_api.contracts import JobResponse, ProblemResponse

IdempotencyKey = Annotated[
    str,
    Header(
        alias="Idempotency-Key",
        min_length=8,
        max_length=200,
        pattern=r"^[A-Za-z0-9._:-]+$",
    ),
]
JobPath = Annotated[str, Path(pattern=r"^job_[0-9a-f]{24}$")]


def build_job_router(
    service: JobService,
    *,
    security_context_dependency: Callable[..., SecurityContext | Awaitable[SecurityContext]],
) -> APIRouter:
    """Build jobs on the application's existing opaque-session guard."""

    router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])
    security_context_marker = Depends(security_context_dependency)

    @router.post(
        "/fixture",
        response_model=JobResponse,
        status_code=202,
        responses={
            401: {"model": ProblemResponse},
            422: {"model": ProblemResponse},
        },
    )
    async def accept_fixture_job(
        idempotency_key: IdempotencyKey,
        security_context: SecurityContext = security_context_marker,
    ) -> JobResponse:
        acceptance = await service.accept_fixture_job(
            security_context=security_context,
            idempotency_key=idempotency_key,
        )
        return JobResponse.from_acceptance(acceptance)

    @router.get(
        "/{job_id}",
        response_model=JobResponse,
        responses={
            401: {"model": ProblemResponse},
            404: {"model": ProblemResponse},
            422: {"model": ProblemResponse},
        },
    )
    async def get_job(
        job_id: JobPath,
        security_context: SecurityContext = security_context_marker,
    ) -> JobResponse | JSONResponse:
        try:
            job = await service.get(security_context=security_context, job_id=job_id)
        except JobNotFoundError:
            problem = ProblemResponse(code="job_not_found", message="Job was not found.")
            return JSONResponse(
                status_code=404,
                content=problem.model_dump(),
            )
        return JobResponse.from_record(job)

    return router
