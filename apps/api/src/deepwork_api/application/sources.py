"""Use case for checking a source candidate before any connection is saved."""

from __future__ import annotations

from deepwork_api.domain import SecurityContext, SourceProbeResult, SourceTargetUnavailableError
from deepwork_api.ports import SourceProbeClient


class SourceService:
    """Validate candidates locally, then delegate the credentialed read check."""

    def __init__(
        self,
        client: SourceProbeClient,
        *,
        endpoint: str,
        tenant_id: str,
        workspace_id: str,
    ) -> None:
        self._client = client
        self._endpoint = endpoint
        configured_context = SecurityContext(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            actor_id="source-probe-config",
        )
        self._tenant_id = configured_context.tenant_id
        self._workspace_id = configured_context.workspace_id

    async def probe_classic(
        self,
        security_context: SecurityContext,
        source_target_id: str,
        assistant_id: str,
    ) -> SourceProbeResult:
        if (
            security_context.tenant_id != self._tenant_id
            or security_context.workspace_id != self._workspace_id
            or source_target_id != "classic-default"
        ):
            raise SourceTargetUnavailableError
        return await self._client.probe(self._endpoint, assistant_id)

    async def close(self) -> None:
        await self._client.close()
