"""Application-owned ports."""

from deepwork_api.ports.auth import SessionStore
from deepwork_api.ports.clock import Clock, system_clock
from deepwork_api.ports.jobs import JobRepository
from deepwork_api.ports.prompt import PromptStore
from deepwork_api.ports.sources import SourceProbeClient
from deepwork_api.ports.status import StatusProvider
from deepwork_api.ports.tasks import TaskRepository
from deepwork_api.ports.trace import TraceLocator

__all__ = [
    "Clock",
    "JobRepository",
    "PromptStore",
    "SessionStore",
    "SourceProbeClient",
    "StatusProvider",
    "TaskRepository",
    "TraceLocator",
    "system_clock",
]
