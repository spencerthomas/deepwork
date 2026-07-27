"""Port for the workspace's editable agent system prompt."""

from __future__ import annotations

from typing import Protocol


class PromptStore(Protocol):
    """Read and write the workspace-level system prompt that governs execution.

    ``None`` means no workspace override is set, so the agent runs with the
    default persona baked into the deployment. A stored value flows into each
    new run as its system prompt without redeploying the agent.
    """

    async def get_system_prompt(self) -> str | None:
        """Return the current workspace system prompt, or ``None`` if unset."""
        ...

    async def set_system_prompt(self, prompt: str | None) -> None:
        """Persist ``prompt`` as the workspace system prompt; ``None`` clears it."""
        ...

    async def close(self) -> None:
        """Release any transport resources; idempotent."""
        ...
