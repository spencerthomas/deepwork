"""Application-owned ports."""

from deepwork_api.ports.status import StatusProvider
from deepwork_api.ports.tasks import TaskRepository

__all__ = ["StatusProvider", "TaskRepository"]
