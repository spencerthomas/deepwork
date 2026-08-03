"""Pydantic wire contracts for the source-backed schedule (recurring run) registry.

Deep Work does not own schedule storage: these contracts describe LangGraph
Crons already registered on the configured task source. Read only: no
create/update/delete contract exists yet because a schedule-
triggered run does not currently surface in this application's task
repository or event stream.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from deepwork_api.contracts.tasks import AgentId


class _ScheduleSummary(Protocol):
    """Structural source projection accepted at the wire boundary."""

    @property
    def schedule_id(self) -> str: ...

    @property
    def agent_id(self) -> str: ...

    @property
    def cron_expression(self) -> str: ...

    @property
    def timezone(self) -> str | None: ...

    @property
    def end_time(self) -> str | None: ...

    @property
    def created_at(self) -> str: ...

    @property
    def updated_at(self) -> str: ...


class _ScheduleWireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ScheduleSummaryResponse(_ScheduleWireModel):
    """One recurring run registered on the configured task source."""

    schedule_id: AgentId = Field(alias="scheduleId")
    agent_id: AgentId = Field(alias="agentId")
    cron_expression: str = Field(alias="cronExpression", min_length=1, max_length=128)
    timezone: str | None = Field(default=None, max_length=64)
    end_time: str | None = Field(default=None, alias="endTime", max_length=64)
    created_at: str = Field(alias="createdAt", max_length=64)
    updated_at: str = Field(alias="updatedAt", max_length=64)

    @classmethod
    def from_source(cls, schedule: _ScheduleSummary) -> ScheduleSummaryResponse:
        return cls(
            schedule_id=schedule.schedule_id,
            agent_id=schedule.agent_id,
            cron_expression=schedule.cron_expression,
            timezone=schedule.timezone,
            end_time=schedule.end_time,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at,
        )


class ScheduleListResponse(_ScheduleWireModel):
    """Schedule registry listing with an honest availability flag.

    ``available`` is false whenever no real task source is configured
    (fixture mode), so an empty list is never confused with "zero schedules".
    """

    available: bool
    items: tuple[ScheduleSummaryResponse, ...]
