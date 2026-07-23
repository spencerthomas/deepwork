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

_SAFE_REASON = "Credential-free fixture scaffold; live providers and durability are unavailable."


class FixtureStatusProvider:
    """Provide fixed local evidence and no external behavior."""

    def health(self) -> HealthStatus:
        """Return process-only liveness."""

        return HealthStatus(status=ProcessState.ALIVE, evidence_class=EvidenceClass.FIXTURE)

    def demo(self) -> DemoStatus:
        """Return deterministic unavailable live capabilities."""

        capabilities = tuple(
            Capability(name=name, state=CapabilityState.UNAVAILABLE)
            for name in ("authentication", "durable_jobs", "sources", "task_stream")
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
