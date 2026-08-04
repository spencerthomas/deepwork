"""Pydantic wire contracts for bounded source qualification."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from deepwork_api.domain import SourceCapabilityObservation, SourceProbeResult


class _SourceWireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SourceProbeRequest(_SourceWireModel):
    """A hosted classic candidate; credentials are intentionally absent."""

    kind: Literal["langsmith_deployment"]
    deployment_url: str = Field(alias="deploymentUrl", min_length=1, max_length=2_048)
    assistant_id: str = Field(
        alias="assistantId",
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$",
    )


class SourceCapabilityResponse(_SourceWireModel):
    """One sanitized, independently observed capability state."""

    name: str = Field(min_length=1, max_length=64)
    state: Literal["available", "unavailable", "gated", "permission-denied", "unknown"]
    reason: str = Field(min_length=1, max_length=128)

    @classmethod
    def from_domain(cls, value: SourceCapabilityObservation) -> SourceCapabilityResponse:
        return cls(name=value.name, state=value.state, reason=value.reason)


class SourceProbeResponse(_SourceWireModel):
    """Credential-free result; read qualification never authorizes saving."""

    kind: Literal["langsmith_deployment"] = "langsmith_deployment"
    state: Literal["available", "unavailable", "gated", "permission-denied", "unknown"]
    assistant_id: str | None = Field(default=None, alias="assistantId", max_length=256)
    graph_id: str | None = Field(default=None, alias="graphId", max_length=256)
    reason: str = Field(min_length=1, max_length=128)
    save_allowed: Literal[False] = Field(default=False, alias="saveAllowed")
    capabilities: tuple[SourceCapabilityResponse, ...]

    @classmethod
    def from_domain(cls, value: SourceProbeResult) -> SourceProbeResponse:
        return cls(
            state=value.state,
            assistant_id=value.assistant_id,
            graph_id=value.graph_id,
            reason=value.reason,
            capabilities=tuple(
                SourceCapabilityResponse.from_domain(item) for item in value.capabilities
            ),
        )
