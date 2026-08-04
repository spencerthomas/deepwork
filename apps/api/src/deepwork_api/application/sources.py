"""Use case for checking a source candidate before any connection is saved."""

from __future__ import annotations

from deepwork_api.domain import SourceProbeResult
from deepwork_api.ports import SourceProbeClient


class SourceService:
    """Validate candidates locally, then delegate the credentialed read check."""

    def __init__(self, client: SourceProbeClient) -> None:
        self._client = client

    async def probe_classic(self, endpoint: str, assistant_id: str) -> SourceProbeResult:
        return await self._client.probe(endpoint, assistant_id)

    async def close(self) -> None:
        await self._client.close()
