"""LangSmith trace lookup for task runs.

The agent's LangGraph run identifiers double as LangSmith trace identifiers
when the runtime traces to LangSmith. This adapter resolves a run id to its
human-viewable trace URL through the LangSmith API. Failures of any kind map to
``None`` (honest "trace unavailable") and the API key never leaves the server.
"""

from __future__ import annotations

import re

import httpx

_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_MAX_APP_PATH_LENGTH = 2_048


class LangSmithTraceLocator:
    """Resolve run ids to LangSmith trace URLs with a server-held API key."""

    def __init__(
        self,
        *,
        api_key: str,
        api_base_url: str = "https://api.smith.langchain.com",
        app_base_url: str = "https://smith.langchain.com",
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("a LangSmith API key is required")
        self._app_base_url = app_base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=api_base_url.rstrip("/"),
            headers={"x-api-key": api_key},
            timeout=10.0,
        )
        self._cache: dict[str, str] = {}

    async def locate(self, run_id: str) -> str | None:
        """Return the trace URL for ``run_id`` or ``None`` when unavailable."""
        if not isinstance(run_id, str) or not _RUN_ID.fullmatch(run_id):
            return None
        cached = self._cache.get(run_id)
        if cached is not None:
            return cached
        try:
            response = await self._client.get(f"/api/v1/runs/{run_id}")
            if response.status_code != 200:
                return None
            payload = response.json()
        except Exception:
            return None
        app_path = payload.get("app_path") if isinstance(payload, dict) else None
        if (
            not isinstance(app_path, str)
            or not app_path.startswith("/")
            or len(app_path) > _MAX_APP_PATH_LENGTH
        ):
            return None
        url = f"{self._app_base_url}{app_path}"
        self._cache[run_id] = url
        return url

    async def close(self) -> None:
        """Release the HTTP transport; idempotent."""
        try:
            await self._client.aclose()
        except Exception:
            pass
