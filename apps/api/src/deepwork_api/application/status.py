"""Status use cases."""

from dataclasses import dataclass

from deepwork_api.domain import (
    Capability,
    CapabilityState,
    DemoStatus,
    HealthStatus,
    JobDurability,
    WorkerStatus,
)
from deepwork_api.ports import StatusProvider


@dataclass(frozen=True, slots=True)
class StatusService:
    """Read status through an application-owned port."""

    provider: StatusProvider
    job_durability: JobDurability | None = None

    def health(self) -> HealthStatus:
        """Read process-only liveness."""

        return self.provider.health()

    def demo(self) -> DemoStatus:
        """Read credential-free configured runtime status."""

        status = self.provider.demo()
        if self.job_durability is not JobDurability.POSTGRES_OUTBOX:
            return status
        capabilities = tuple(
            Capability(name=item.name, state=CapabilityState.AVAILABLE)
            if item.name == "durable_jobs"
            else item
            for item in status.capabilities
        )
        return DemoStatus(
            mode=status.mode,
            runtime_kind=status.runtime_kind,
            evidence_class=status.evidence_class,
            capabilities=capabilities,
            safe_reason=(
                f"{status.safe_reason} PostgreSQL transactional job/outbox durability "
                "is configured."
            ),
        )

    def worker(self) -> WorkerStatus:
        """Read worker durability status."""

        return self.provider.worker()
