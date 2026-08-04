"""Credential-free status for a configured source-backed task runtime."""

from dataclasses import dataclass

from deepwork_api.domain import (
    Capability,
    CapabilityState,
    DemoStatus,
    EvidenceClass,
    HealthStatus,
    ProcessState,
    RuntimeKind,
    WorkerDurability,
    WorkerStatus,
)


@dataclass(frozen=True, slots=True)
class SourceStatusProvider:
    """Describe configured adapter mechanics without probing provider readiness."""

    runtime_kind: RuntimeKind
    authentication_enabled: bool

    def __post_init__(self) -> None:
        if self.runtime_kind is RuntimeKind.FIXTURE:
            raise ValueError("source status requires a source-backed runtime kind")

    def health(self) -> HealthStatus:
        """Return process liveness without upgrading it to source readiness."""

        return HealthStatus(status=ProcessState.ALIVE, evidence_class=EvidenceClass.LOCAL_SOURCE)

    def demo(self) -> DemoStatus:
        """Return the safe configured runtime projection consumed by the browser."""

        classic = self.runtime_kind is RuntimeKind.CLASSIC_DEPLOYMENT
        authentication = (
            CapabilityState.AVAILABLE
            if self.authentication_enabled
            else CapabilityState.UNAVAILABLE
        )
        capabilities = (
            Capability(name="local_task_loop", state=CapabilityState.AVAILABLE),
            Capability(name="task_stream", state=CapabilityState.AVAILABLE),
            Capability(name="authentication", state=authentication),
            Capability(name="durable_jobs", state=CapabilityState.UNAVAILABLE),
            Capability(name="sources", state=CapabilityState.AVAILABLE),
            Capability(
                name="external_providers",
                state=(CapabilityState.AVAILABLE if classic else CapabilityState.UNAVAILABLE),
            ),
        )
        label = "classic deployment" if classic else "local Agent Server"
        return DemoStatus(
            mode=EvidenceClass.LOCAL_SOURCE,
            runtime_kind=self.runtime_kind,
            evidence_class=EvidenceClass.LOCAL_SOURCE,
            capabilities=capabilities,
            safe_reason=(
                f"A {label} task source is configured through the server-held credential "
                "boundary. These are configured adapter mechanics, not a live provider "
                "readiness check."
            ),
        )

    def worker(self) -> WorkerStatus:
        """Do not claim durable worker execution from an in-process source runner."""

        return WorkerStatus(
            mode=EvidenceClass.LOCAL_SOURCE,
            durability=WorkerDurability.UNAVAILABLE,
            safe_reason="The source task follower is process-local and is not a durable worker.",
        )


__all__ = ["SourceStatusProvider"]
