"""Application-owned ports."""

from deepwork_api.ports.clock import Clock, system_clock
from deepwork_api.ports.status import StatusProvider
from deepwork_api.ports.tasks import TaskRepository

__all__ = ["Clock", "StatusProvider", "TaskRepository", "system_clock"]
