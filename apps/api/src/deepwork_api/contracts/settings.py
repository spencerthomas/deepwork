"""Pydantic wire contracts for editable workspace settings."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from deepwork_api.domain import MAX_SYSTEM_PROMPT_LENGTH


class SystemPromptResponse(BaseModel):
    """The workspace's current system prompt and whether it overrides the default."""

    model_config = ConfigDict(extra="forbid")

    systemPrompt: str | None = Field(
        default=None,
        description="The stored workspace system prompt, or null when using the default.",
    )
    isDefault: bool = Field(
        description="True when no workspace override is set and the deployment default is used.",
    )

    @classmethod
    def from_value(cls, prompt: str | None) -> SystemPromptResponse:
        return cls(systemPrompt=prompt, isDefault=prompt is None)


class SystemPromptUpdateRequest(BaseModel):
    """Set or clear the workspace system prompt.

    A null or blank prompt clears the override and reverts to the deployment
    default; a non-empty prompt is stored and governs subsequent runs.
    """

    model_config = ConfigDict(extra="forbid")

    systemPrompt: str | None = Field(
        default=None,
        max_length=MAX_SYSTEM_PROMPT_LENGTH,
        description="New system prompt, or null/blank to clear the override.",
    )
