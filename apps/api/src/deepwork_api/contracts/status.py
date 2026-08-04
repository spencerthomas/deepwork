"""Status wire models."""

from pydantic import BaseModel, ConfigDict

from deepwork_api.domain import (
    DemoStatus,
    EvidenceClass,
    HealthStatus,
    ProcessState,
    RuntimeKind,
    WorkerStatus,
)


class _WireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class HealthResponse(_WireModel):
    """Process liveness response, not dependency readiness."""

    status: ProcessState
    scope: str = "process"
    evidence_class: EvidenceClass
    dependencies_checked: tuple[str, ...] = ()

    @classmethod
    def from_domain(cls, status: HealthStatus) -> "HealthResponse":
        """Map a pure domain value to the wire contract."""

        return cls(status=status.status, evidence_class=status.evidence_class)


class CapabilityResponse(_WireModel):
    """One fixture capability response."""

    name: str
    state: str


class DemoStatusResponse(_WireModel):
    """Credential-free configured runtime status response."""

    mode: EvidenceClass
    runtime_kind: RuntimeKind
    evidence_class: EvidenceClass
    capabilities: tuple[CapabilityResponse, ...]
    safe_reason: str
    build_sha: str | None

    @classmethod
    def from_domain(cls, status: DemoStatus) -> "DemoStatusResponse":
        """Map a pure domain value to the wire contract."""

        capabilities = tuple(
            CapabilityResponse(name=capability.name, state=capability.state.value)
            for capability in status.capabilities
        )
        return cls(
            mode=status.mode,
            runtime_kind=status.runtime_kind,
            evidence_class=status.evidence_class,
            capabilities=capabilities,
            safe_reason=status.safe_reason,
            build_sha=status.build_sha,
        )


class WorkerStatusResponse(_WireModel):
    """Worker smoke response without a durable backend."""

    mode: EvidenceClass
    durability: str
    safe_reason: str

    @classmethod
    def from_domain(cls, status: WorkerStatus) -> "WorkerStatusResponse":
        """Map a pure domain value to a CLI-safe contract."""

        return cls(
            mode=status.mode,
            durability=status.durability.value,
            safe_reason=status.safe_reason,
        )
