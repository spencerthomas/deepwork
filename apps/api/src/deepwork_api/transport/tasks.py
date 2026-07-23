"""FastAPI task routes and normalized replayable SSE transport."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Header, Path
from fastapi.responses import JSONResponse, StreamingResponse

from deepwork_api.application import (
    DecisionConflictError,
    InterruptMismatchError,
    InvalidEventCursorError,
    PlanRevisionConflictError,
    PlanUnavailableError,
    StaleInterruptError,
    TaskEvent,
    TaskNotFoundError,
    TaskService,
    TaskSourceContractError,
    TaskSourceUnavailableError,
    TaskStatus,
)
from deepwork_api.contracts import (
    DecisionAcceptedResponse,
    DecisionRequest,
    PlanUpdateRequest,
    PlanUpdateResponse,
    ProblemResponse,
    TaskAcceptedResponse,
    TaskCreateRequest,
    TaskDetailResponse,
    TaskListResponse,
    TaskResultResponse,
    TaskSummaryResponse,
    encode_event_data,
)

TaskPath = Annotated[str, Path(pattern=r"^task_[0-9]{8}$")]
_MAX_EVENT_CURSOR = 2_147_483_647


def build_task_router(service: TaskService) -> APIRouter:
    """Build the shared internal task API around an injected service."""

    router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

    @router.post("", response_model=TaskAcceptedResponse, status_code=202)
    async def create_task(request: TaskCreateRequest) -> TaskAcceptedResponse | JSONResponse:
        try:
            task = await service.create_task(request.prompt)
        except TaskSourceContractError:
            return _problem(
                502,
                "local_source_contract_mismatch",
                "The configured local task source broke its supported contract.",
            )
        except TaskSourceUnavailableError:
            return _problem(
                503,
                "local_source_unavailable",
                "The configured local task source is unavailable.",
            )
        return TaskAcceptedResponse.from_domain(task)

    @router.get("", response_model=TaskListResponse)
    async def list_tasks() -> TaskListResponse:
        tasks = await service.list_tasks()
        return TaskListResponse(
            items=tuple(TaskSummaryResponse.from_domain(task) for task in tasks)
        )

    @router.get("/{task_id}", response_model=TaskDetailResponse)
    async def get_task(task_id: TaskPath) -> TaskDetailResponse | JSONResponse:
        try:
            task = await service.get_task(task_id)
        except TaskNotFoundError:
            return _problem(404, "task_not_found", "Task was not found.")
        return TaskDetailResponse.from_domain(task)

    @router.get("/{task_id}/result", response_model=TaskResultResponse)
    async def get_task_result(task_id: TaskPath) -> TaskResultResponse | JSONResponse:
        try:
            task = await service.get_task(task_id)
        except TaskNotFoundError:
            return _problem(404, "task_not_found", "Task was not found.")
        if task.status is not TaskStatus.COMPLETED or task.result is None:
            return _problem(
                409,
                "task_result_unavailable",
                "Task does not have a completed result.",
            )
        return TaskResultResponse.from_domain(task)

    @router.get("/{task_id}/events", response_model=None)
    async def task_events(
        task_id: TaskPath,
        last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
    ) -> StreamingResponse | JSONResponse:
        try:
            cursor = _parse_event_cursor(last_event_id)
            await service.validate_event_cursor(task_id, cursor)
        except TaskNotFoundError:
            return _problem(404, "task_not_found", "Task was not found.")
        except InvalidEventCursorError:
            return _problem(409, "event_cursor_invalid", "Event replay cursor is invalid.")

        return StreamingResponse(
            _event_stream(service, task_id, cursor),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-store",
                "X-Accel-Buffering": "no",
            },
        )

    @router.post(
        "/{task_id}/decisions",
        response_model=DecisionAcceptedResponse,
        status_code=202,
    )
    async def record_decision(
        task_id: TaskPath,
        request: DecisionRequest,
    ) -> DecisionAcceptedResponse | JSONResponse:
        try:
            decision = await service.record_decision(
                task_id,
                interrupt_id=request.interrupt_id,
                decision=request.decision,
                comment=request.comment,
            )
        except TaskNotFoundError:
            return _problem(404, "task_not_found", "Task was not found.")
        except TaskSourceContractError:
            return _problem(
                502,
                "local_source_contract_mismatch",
                "The configured local task source broke its supported contract.",
            )
        except TaskSourceUnavailableError:
            return _problem(
                503,
                "local_source_unavailable",
                "The configured local task source is unavailable.",
            )
        except InterruptMismatchError:
            return _problem(
                409,
                "interrupt_mismatch",
                "Interrupt does not match the pending task decision.",
            )
        except StaleInterruptError:
            return _problem(409, "interrupt_stale", "Interrupt is no longer actionable.")
        except DecisionConflictError:
            return _problem(
                409,
                "decision_conflict",
                "A different decision was already recorded.",
            )
        return DecisionAcceptedResponse.from_domain(decision)

    @router.patch(
        "/{task_id}/plan",
        response_model=PlanUpdateResponse,
    )
    async def update_plan(
        task_id: TaskPath,
        request: PlanUpdateRequest,
    ) -> PlanUpdateResponse | JSONResponse:
        try:
            update = await service.update_plan(
                task_id,
                interrupt_id=request.interrupt_id,
                expected_revision=request.expected_revision,
                steps=request.steps,
            )
        except TaskNotFoundError:
            return _problem(404, "task_not_found", "Task was not found.")
        except TaskSourceContractError:
            return _problem(
                502,
                "local_source_contract_mismatch",
                "The configured local task source broke its supported contract.",
            )
        except TaskSourceUnavailableError:
            return _problem(
                503,
                "local_source_unavailable",
                "The configured local task source is unavailable.",
            )
        except InterruptMismatchError:
            return _problem(
                409,
                "interrupt_mismatch",
                "Interrupt does not match the pending task decision.",
            )
        except StaleInterruptError:
            return _problem(409, "interrupt_stale", "Interrupt is no longer actionable.")
        except PlanUnavailableError:
            return _problem(409, "plan_unavailable", "Task has no editable proposed plan.")
        except PlanRevisionConflictError:
            return _problem(
                409,
                "plan_revision_conflict",
                "Plan revision is stale or conflicting.",
            )
        return PlanUpdateResponse.from_domain(update)

    return router


def _parse_event_cursor(value: str | None) -> int:
    if value is None or value == "":
        return 0
    if not value.isascii() or not value.isdecimal():
        raise InvalidEventCursorError
    # Reject clearly out-of-range cursors before int(): Python caps int(str)
    # at 4300 digits and would otherwise raise ValueError (an unhandled 500)
    # for an over-long client-supplied Last-Event-ID.
    if len(value) > len(str(_MAX_EVENT_CURSOR)):
        raise InvalidEventCursorError
    cursor = int(value)
    if cursor > _MAX_EVENT_CURSOR:
        raise InvalidEventCursorError
    return cursor


async def _event_stream(
    service: TaskService,
    task_id: str,
    event_id: int,
) -> AsyncIterator[str]:
    async for event in service.stream_events(task_id, event_id):
        yield _format_event(event)


def _format_event(event: TaskEvent) -> str:
    data = encode_event_data(event)
    return f"id: {event.event_id}\nevent: {event.name.value}\ndata: {data}\n\n"


def _problem(status_code: int, code: str, message: str) -> JSONResponse:
    body = ProblemResponse(code=code, message=message)
    return JSONResponse(status_code=status_code, content=body.model_dump())
