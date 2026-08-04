"""Status provider port."""

from typing import Protocol

from deepwork_api.domain import DemoStatus, HealthStatus, WorkerStatus


class StatusProvider(Protocol):
    """Provide credential-free runtime status without external I/O."""

    def health(self) -> HealthStatus:
        """Return process-only liveness."""

    def demo(self) -> DemoStatus:
        """Return configured runtime capability state."""

    def worker(self) -> WorkerStatus:
        """Return worker durability state."""
