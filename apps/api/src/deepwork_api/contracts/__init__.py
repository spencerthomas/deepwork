"""Pydantic wire contracts."""

from deepwork_api.contracts.agents import (
    AgentCreateRequest,
    AgentListResponse,
    AgentSummaryResponse,
    AgentUpdateRequest,
)
from deepwork_api.contracts.jobs import JobResponse
from deepwork_api.contracts.schedules import ScheduleListResponse, ScheduleSummaryResponse
from deepwork_api.contracts.settings import SystemPromptResponse, SystemPromptUpdateRequest
from deepwork_api.contracts.sources import SourceProbeRequest, SourceProbeResponse
from deepwork_api.contracts.status import DemoStatusResponse, HealthResponse, WorkerStatusResponse
from deepwork_api.contracts.tasks import (
    CancellationAcceptedResponse,
    DecisionAcceptedResponse,
    DecisionBatchAcceptedResponse,
    DecisionBatchRequest,
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

__all__ = [
    "AgentCreateRequest",
    "AgentListResponse",
    "AgentSummaryResponse",
    "AgentUpdateRequest",
    "CancellationAcceptedResponse",
    "DecisionAcceptedResponse",
    "DecisionBatchAcceptedResponse",
    "DecisionBatchRequest",
    "DecisionRequest",
    "DemoStatusResponse",
    "HealthResponse",
    "JobResponse",
    "PlanUpdateRequest",
    "PlanUpdateResponse",
    "ProblemResponse",
    "ScheduleListResponse",
    "ScheduleSummaryResponse",
    "SourceProbeRequest",
    "SourceProbeResponse",
    "SystemPromptResponse",
    "SystemPromptUpdateRequest",
    "TaskAcceptedResponse",
    "TaskCreateRequest",
    "TaskDetailResponse",
    "TaskListResponse",
    "TaskResultResponse",
    "TaskSummaryResponse",
    "WorkerStatusResponse",
    "encode_event_data",
]
