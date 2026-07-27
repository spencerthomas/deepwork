"""Port for locating an upstream trace for a task's run."""

from __future__ import annotations

from typing import Protocol


class TraceLocator(Protocol):
    """Resolve a run identifier to a human-viewable trace URL, if one exists."""

    async def locate(self, run_id: str) -> str | None:
        """Return the trace URL for ``run_id`` or ``None`` when unavailable."""
        ...

    async def close(self) -> None:
        """Release any transport resources; idempotent."""
        ...
