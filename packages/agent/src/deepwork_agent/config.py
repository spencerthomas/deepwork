"""Package-local configuration for the credential-free scaffold."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class AgentPackageConfig:
    """Describe the only supported configuration state in the Wave 1 scaffold.

    This is not the portable agent-project schema governed by `SPIKE-CONFIG-001`.
    It exists only to make the unavailable runtime boundary explicit and typed.
    """

    schema_version: Literal[1] = 1
    runtime_enabled: Literal[False] = False

    def __post_init__(self) -> None:
        """Reject attempts to enable an unverified runtime at execution time."""
        if self.schema_version != 1:
            msg = "unsupported agent package scaffold schema version"
            raise ValueError(msg)
        if self.runtime_enabled is not False:
            msg = "agent runtime cannot be enabled before SPIKE-CONFIG-001 passes"
            raise ValueError(msg)
