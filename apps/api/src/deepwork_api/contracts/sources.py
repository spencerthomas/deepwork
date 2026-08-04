"""Pydantic wire contracts for bounded source qualification."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from deepwork_api.domain import SourceCapabilityObservation, SourceProbeResult, SourceProbeState


class _SourceWireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SourceProbeRequest(_SourceWireModel):
    """A server-owned classic target; credentials and provider URLs are absent."""

    kind: Literal["langsmith_deployment"]
    source_target_id: Literal["classic-default"] = Field(alias="sourceTargetId")
    assistant_id: str = Field(
        alias="assistantId",
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$",
    )


class _SourceCapabilityBase(_SourceWireModel):
    """Evidence metadata shared by every source capability observation."""

    name: str = Field(min_length=1, max_length=64)
    observed_at: str = Field(alias="observedAt", min_length=1, max_length=64)
    adapter_version: str = Field(alias="adapterVersion", min_length=1, max_length=64)
    contract_version: str = Field(alias="contractVersion", min_length=1, max_length=64)
    evidence_class: Literal["documented", "live-contract", "fixture"] = Field(alias="evidenceClass")


class SourceAvailableCapabilityResponse(_SourceCapabilityBase):
    state: Literal["available"]


class SourceUnavailableCapabilityResponse(_SourceCapabilityBase):
    state: Literal["unavailable", "gated", "permission-denied", "unknown"]
    safe_reason: Literal[
        "contract-not-verified",
        "not-supported",
        "permission-required",
        "source-unavailable",
        "adapter-disabled",
    ] = Field(alias="safeReason")


SourceCapabilityResponse = Annotated[
    SourceAvailableCapabilityResponse | SourceUnavailableCapabilityResponse,
    Field(discriminator="state"),
]


def _capability_from_domain(
    value: SourceCapabilityObservation,
) -> SourceAvailableCapabilityResponse | SourceUnavailableCapabilityResponse:
    if value.state == "available":
        return SourceAvailableCapabilityResponse(
            name=value.name,
            state="available",
            observed_at=value.observed_at,
            adapter_version=value.adapter_version,
            contract_version=value.contract_version,
            evidence_class=value.evidence_class,
        )
    assert value.safe_reason is not None
    return SourceUnavailableCapabilityResponse(
        name=value.name,
        state=value.state,
        safe_reason=value.safe_reason,
        observed_at=value.observed_at,
        adapter_version=value.adapter_version,
        contract_version=value.contract_version,
        evidence_class=value.evidence_class,
    )


class SourceProbeResponse(_SourceWireModel):
    """Credential-free result; read qualification never authorizes saving."""

    kind: Literal["langsmith_deployment"]
    state: SourceProbeState
    assistant_id: str | None = Field(alias="assistantId", max_length=256)
    graph_id: str | None = Field(alias="graphId", max_length=256)
    reason: str = Field(min_length=1, max_length=128)
    save_allowed: Literal[False] = Field(alias="saveAllowed")
    capabilities: tuple[SourceCapabilityResponse, ...]

    @classmethod
    def from_domain(cls, value: SourceProbeResult) -> SourceProbeResponse:
        return cls(
            kind="langsmith_deployment",
            state=value.state,
            assistant_id=value.assistant_id,
            graph_id=value.graph_id,
            reason=value.reason,
            save_allowed=False,
            capabilities=tuple(_capability_from_domain(item) for item in value.capabilities),
        )
