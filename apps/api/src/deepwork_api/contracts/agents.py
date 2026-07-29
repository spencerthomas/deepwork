"""Pydantic wire contracts for the source-backed agent registry.

Deep Work does not own agent storage: these contracts describe LangGraph
Assistants already registered on the configured task source, projected
through :class:`~deepwork_api.application.local_runner.LocalAgentSummary`.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from deepwork_api.application.local_runner import LocalAgentSummary
from deepwork_api.contracts._text import reject_unsafe_controls
from deepwork_api.contracts.tasks import AgentId
from deepwork_api.domain import (
    MAX_AGENT_DESCRIPTION_LENGTH,
    MAX_AGENT_NAME_LENGTH,
    MAX_SYSTEM_PROMPT_LENGTH,
)


class _AgentWireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class AgentSummaryResponse(_AgentWireModel):
    """One registered agent sharing the deployed graph."""

    agent_id: AgentId = Field(alias="agentId")
    name: str = Field(min_length=1, max_length=MAX_AGENT_NAME_LENGTH)
    description: str | None = Field(default=None, max_length=MAX_AGENT_DESCRIPTION_LENGTH)
    system_prompt: str | None = Field(
        default=None, alias="systemPrompt", max_length=MAX_SYSTEM_PROMPT_LENGTH
    )
    is_default: bool = Field(alias="isDefault")
    created_at: str = Field(alias="createdAt", max_length=64)
    updated_at: str = Field(alias="updatedAt", max_length=64)

    @classmethod
    def from_source(cls, agent: LocalAgentSummary) -> AgentSummaryResponse:
        return cls(
            agent_id=agent.agent_id,
            name=agent.name,
            description=agent.description,
            system_prompt=agent.system_prompt,
            is_default=agent.is_default,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        )


class AgentListResponse(_AgentWireModel):
    """Agent registry listing with an honest availability flag.

    ``available`` is false whenever no real task source is configured
    (fixture mode), so an empty list is never confused with "zero agents".
    """

    available: bool
    items: tuple[AgentSummaryResponse, ...]


class _AgentEditableFields(_AgentWireModel):
    """Shared editable agent fields for create and full-replace update."""

    name: str = Field(min_length=1, max_length=MAX_AGENT_NAME_LENGTH)
    description: str | None = Field(default=None, max_length=MAX_AGENT_DESCRIPTION_LENGTH)
    system_prompt: str | None = Field(
        default=None, alias="systemPrompt", max_length=MAX_SYSTEM_PROMPT_LENGTH
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        reject_unsafe_controls(value)
        if not value.strip():
            raise ValueError("agent name must contain visible text")
        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        if value is not None:
            reject_unsafe_controls(value)
        return value


class AgentCreateRequest(_AgentEditableFields):
    """Register a new agent sharing the deployed graph."""


class AgentUpdateRequest(_AgentEditableFields):
    """Replace the editable fields of one non-default registered agent.

    Every editable field is supplied on every call (full replace), so a
    cleared ``systemPrompt`` or ``description`` is unambiguous.
    """
