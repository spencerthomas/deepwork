"""In-memory system-prompt store for the single-process local runtime.

The value lives only while the API process is alive. The durable variant behind
the same ``PromptStore`` port is :class:`~deepwork_api.adapters.prompt.sqlite.SQLitePromptStore`.
"""

from __future__ import annotations

from deepwork_api.domain import (
    DEFAULT_TENANT_ID,
    DEFAULT_WORKSPACE_ID,
    SecurityContext,
    normalize_system_prompt,
)


class InMemoryPromptStore:
    """Process-local storage for the workspace system prompt."""

    def __init__(self, initial: str | None = None) -> None:
        self._prompts: dict[tuple[str, str], str] = {}
        normalized = normalize_system_prompt(initial)
        if normalized is not None:
            self._prompts[(DEFAULT_TENANT_ID, DEFAULT_WORKSPACE_ID)] = normalized

    @staticmethod
    def _scope(tenant_id: str, workspace_id: str) -> tuple[str, str]:
        context = SecurityContext(tenant_id=tenant_id, workspace_id=workspace_id)
        return context.tenant_id, context.workspace_id

    async def get_system_prompt(
        self,
        *,
        tenant_id: str = DEFAULT_TENANT_ID,
        workspace_id: str = DEFAULT_WORKSPACE_ID,
    ) -> str | None:
        return self._prompts.get(self._scope(tenant_id, workspace_id))

    async def set_system_prompt(
        self,
        prompt: str | None,
        *,
        tenant_id: str = DEFAULT_TENANT_ID,
        workspace_id: str = DEFAULT_WORKSPACE_ID,
    ) -> None:
        scope = self._scope(tenant_id, workspace_id)
        normalized = normalize_system_prompt(prompt)
        if normalized is None:
            self._prompts.pop(scope, None)
        else:
            self._prompts[scope] = normalized

    async def close(self) -> None:
        return None
