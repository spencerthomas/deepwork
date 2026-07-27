"""FastAPI routes for the source-backed schedule (recurring run) registry.

Read-only: no create/update/delete route exists yet. A schedule-triggered
run starts a fresh thread directly on the configured task source, which does
not currently surface in this application's task repository or event
stream, so offering mutation here would silently create schedules whose
runs never appear anywhere in the product.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from deepwork_api.application import (
    ScheduleRegistryUnavailableError,
    TaskService,
    TaskSourceContractError,
    TaskSourceUnavailableError,
)
from deepwork_api.contracts import ProblemResponse, ScheduleListResponse, ScheduleSummaryResponse


def build_schedules_router(
    service: TaskService,
    *,
    dependencies: list[Any] | None = None,
) -> APIRouter:
    """Build the schedule-registry API around an injected task service.

    ``dependencies`` are attached to every route (the session guard when
    authentication is enabled), matching the task and agents routers.
    """

    router = APIRouter(
        prefix="/api/v1/schedules",
        tags=["schedules"],
        dependencies=dependencies or [],
    )

    @router.get("", response_model=ScheduleListResponse)
    async def list_schedules() -> ScheduleListResponse | JSONResponse:
        try:
            schedules = await service.list_schedules()
        except ScheduleRegistryUnavailableError:
            return ScheduleListResponse(available=False, items=())
        except TaskSourceContractError:
            return _problem(
                502,
                "schedule_source_contract_mismatch",
                "The configured task source broke its supported contract.",
            )
        except TaskSourceUnavailableError:
            return _problem(
                503,
                "schedule_source_unavailable",
                "The configured task source is unavailable.",
            )
        return ScheduleListResponse(
            available=True,
            items=tuple(ScheduleSummaryResponse.from_source(schedule) for schedule in schedules),
        )

    return router


def _problem(status_code: int, code: str, message: str) -> JSONResponse:
    body = ProblemResponse(code=code, message=message)
    return JSONResponse(status_code=status_code, content=body.model_dump())
