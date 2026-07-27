"""In-memory system-prompt store for the single-process local runtime.

The value lives only while the API process is alive. The durable variant behind
the same ``PromptStore`` port is :class:`~deepwork_api.adapters.prompt.sqlite.SQLitePromptStore`.
"""

from __future__ import annotations

from deepwork_api.domain import normalize_system_prompt


class InMemoryPromptStore:
    """Process-local storage for the workspace system prompt."""

    def __init__(self, initial: str | None = None) -> None:
        self._prompt = normalize_system_prompt(initial)

    async def get_system_prompt(self) -> str | None:
        return self._prompt

    async def set_system_prompt(self, prompt: str | None) -> None:
        self._prompt = normalize_system_prompt(prompt)

    async def close(self) -> None:
        return None
