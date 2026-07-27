"""Pydantic wire contracts."""

from deepwork_api.contracts.agents import (
    AgentCreateRequest,
    AgentListResponse,
    AgentSummaryResponse,
    AgentUpdateRequest,
)
from deepwork_api.contracts.settings import SystemPromptResponse, SystemPromptUpdateRequest
from deepwork_api.contracts.status import DemoStatusResponse, HealthResponse, WorkerStatusResponse
from deepwork_api.contracts.tasks import (
    CancellationAcceptedResponse,
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

__all__ = [
    "AgentCreateRequest",
    "AgentListResponse",
    "AgentSummaryResponse",
    "AgentUpdateRequest",
    "CancellationAcceptedResponse",
    "DecisionAcceptedResponse",
    "DecisionRequest",
    "DemoStatusResponse",
    "HealthResponse",
    "PlanUpdateRequest",
    "PlanUpdateResponse",
    "ProblemResponse",
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
