"""Explicit unavailable boundary for the future agent graph."""

from dataclasses import dataclass
from typing import Never

from deepwork_agent.config import AgentPackageConfig

CONFIG_CONTRACT_GATE = "SPIKE-CONFIG-001"
_UNAVAILABLE_REASON = (
    "agent runtime unavailable until the reviewed public configuration and graph contract passes"
)


@dataclass(frozen=True, slots=True)
class RuntimeAvailability:
    """Report why the package cannot construct a runtime graph yet."""

    available: bool
    contract_gate: str
    reason: str


class RuntimeCapabilityUnavailable(RuntimeError):  # noqa: N818 - canonical capability state name
    """Raised when code attempts to construct the gated runtime graph."""

    def __init__(self, availability: RuntimeAvailability) -> None:
        """Create a safe error without provider or credential detail."""
        self.availability = availability
        super().__init__(f"{availability.contract_gate}: {availability.reason}")


def runtime_availability() -> RuntimeAvailability:
    """Return the deterministic unavailable state for the runtime boundary."""
    return RuntimeAvailability(
        available=False,
        contract_gate=CONFIG_CONTRACT_GATE,
        reason=_UNAVAILABLE_REASON,
    )


def create_graph(*, config: AgentPackageConfig | None = None) -> Never:
    """Refuse graph construction until the public runtime contract is reviewed.

    Args:
        config: Optional package-scaffold configuration. It cannot enable runtime
            behavior.

    Raises:
        RuntimeCapabilityUnavailable: Always, while `SPIKE-CONFIG-001` is open.

    """
    _ = config or AgentPackageConfig()
    raise RuntimeCapabilityUnavailable(runtime_availability())
