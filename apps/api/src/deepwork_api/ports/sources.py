"""Application port for bounded, read-only source qualification."""

from __future__ import annotations

from typing import Protocol

from deepwork_api.domain import SourceProbeResult


class SourceProbeClient(Protocol):
    """Check a source without exposing provider credentials or raw responses."""

    async def probe(self, endpoint: str, assistant_id: str) -> SourceProbeResult: ...

    async def close(self) -> None:
        """Release any resources; idempotent."""
