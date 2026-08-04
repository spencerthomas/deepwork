"""Server-owned configuration for the bounded source qualification feature."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SourceProbeConfig:
    """One workspace-owned classic target; never serialize this value."""

    credential: str = field(repr=False)
    allowed_endpoints: tuple[str, ...]
    tenant_id: str = "tenant-local"
    workspace_id: str = "workspace-local"
