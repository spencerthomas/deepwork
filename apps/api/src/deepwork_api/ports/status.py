"""Status provider port."""

from typing import Protocol

from deepwork_api.domain import DemoStatus, HealthStatus, WorkerStatus


class StatusProvider(Protocol):
    """Provide deterministic local status without external I/O."""

    def health(self) -> HealthStatus:
        """Return process-only liveness."""

    def demo(self) -> DemoStatus:
        """Return fixture-only demo capability state."""

    def worker(self) -> WorkerStatus:
        """Return worker durability state."""
