"""Pure status values for the credential-free scaffold."""

from dataclasses import dataclass
from enum import StrEnum


class EvidenceClass(StrEnum):
    """Origin of an observed capability or status."""

    FIXTURE = "fixture"
    LOCAL_SOURCE = "local-source"


class ProcessState(StrEnum):
    """Process-only liveness state."""

    ALIVE = "alive"


class CapabilityState(StrEnum):
    """Safe state for a product capability."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class WorkerDurability(StrEnum):
    """Durability available to the scaffold worker."""

    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class HealthStatus:
    """Process liveness without dependency-readiness claims."""

    status: ProcessState
    evidence_class: EvidenceClass


@dataclass(frozen=True, slots=True)
class Capability:
    """One evidence-bearing fixture capability."""

    name: str
    state: CapabilityState


@dataclass(frozen=True, slots=True)
class DemoStatus:
    """Fixture-only product-demo status."""

    mode: EvidenceClass
    evidence_class: EvidenceClass
    capabilities: tuple[Capability, ...]
    safe_reason: str


@dataclass(frozen=True, slots=True)
class WorkerStatus:
    """Honest worker bootstrap result without a durable backend."""

    mode: EvidenceClass
    durability: WorkerDurability
    safe_reason: str
