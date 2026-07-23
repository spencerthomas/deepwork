"""Status use cases."""

from dataclasses import dataclass

from deepwork_api.domain import DemoStatus, HealthStatus, WorkerStatus
from deepwork_api.ports import StatusProvider


@dataclass(frozen=True, slots=True)
class StatusService:
    """Read status through an application-owned port."""

    provider: StatusProvider

    def health(self) -> HealthStatus:
        """Read process-only liveness."""

        return self.provider.health()

    def demo(self) -> DemoStatus:
        """Read fixture-only demo status."""

        return self.provider.demo()

    def worker(self) -> WorkerStatus:
        """Read worker durability status."""

        return self.provider.worker()
