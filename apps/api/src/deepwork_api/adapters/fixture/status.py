"""Deterministic fixture status adapter."""

from deepwork_api.domain import (
    Capability,
    CapabilityState,
    DemoStatus,
    EvidenceClass,
    HealthStatus,
    ProcessState,
    WorkerDurability,
    WorkerStatus,
)

_SAFE_REASON = (
    "Credential-free local task and SSE fixtures are available; "
    "external providers, authentication, and durability are unavailable."
)


class FixtureStatusProvider:
    """Provide fixed local evidence and no external behavior."""

    def health(self) -> HealthStatus:
        """Return process-only liveness."""

        return HealthStatus(status=ProcessState.ALIVE, evidence_class=EvidenceClass.FIXTURE)

    def demo(self) -> DemoStatus:
        """Separate available local fixtures from unavailable external behavior."""

        capabilities = (
            Capability(name="local_task_loop", state=CapabilityState.AVAILABLE),
            Capability(name="task_stream", state=CapabilityState.AVAILABLE),
            Capability(name="authentication", state=CapabilityState.UNAVAILABLE),
            Capability(name="durable_jobs", state=CapabilityState.UNAVAILABLE),
            Capability(name="sources", state=CapabilityState.UNAVAILABLE),
            Capability(name="external_providers", state=CapabilityState.UNAVAILABLE),
        )
        return DemoStatus(
            mode=EvidenceClass.FIXTURE,
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
