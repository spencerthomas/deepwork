"""Deterministic fixture status adapter."""

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

_SAFE_REASON = (
    "Credential-free local task and SSE fixtures are available; "
    "external providers are unavailable; authentication and durable job "
    "availability are reported separately."
)


@dataclass(frozen=True, slots=True)
class FixtureStatusProvider:
    """Provide fixed local evidence and no external behavior."""

    authentication_enabled: bool = False

    def health(self) -> HealthStatus:
        """Return process-only liveness."""

        return HealthStatus(status=ProcessState.ALIVE, evidence_class=EvidenceClass.FIXTURE)

    def demo(self) -> DemoStatus:
        """Separate available local fixtures from unavailable external behavior."""

        capabilities = (
            Capability(name="local_task_loop", state=CapabilityState.AVAILABLE),
            Capability(name="task_stream", state=CapabilityState.AVAILABLE),
            Capability(
                name="authentication",
                state=(
                    CapabilityState.AVAILABLE
                    if self.authentication_enabled
                    else CapabilityState.UNAVAILABLE
                ),
            ),
            Capability(name="durable_jobs", state=CapabilityState.UNAVAILABLE),
            Capability(name="sources", state=CapabilityState.UNAVAILABLE),
            Capability(name="external_providers", state=CapabilityState.UNAVAILABLE),
        )
        return DemoStatus(
            mode=EvidenceClass.FIXTURE,
            runtime_kind=RuntimeKind.FIXTURE,
            evidence_class=EvidenceClass.FIXTURE,
            capabilities=capabilities,
            safe_reason=_SAFE_REASON,
        )

    def worker(self) -> WorkerStatus:
        """Return an honest non-durable worker result."""

        return WorkerStatus(
            mode=EvidenceClass.FIXTURE,
            durability=WorkerDurability.UNAVAILABLE,
            safe_reason=_SAFE_REASON,
        )
