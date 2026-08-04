"""Server-credentialed classic deployment qualification adapter."""

from __future__ import annotations

from deepwork_api.adapters.sources.classic.source import (
    ClassicSourceConfigurationError,
    ClassicSourceSettings,
    qualify_classic_sources,
)
from deepwork_api.domain import (
    SourceCapabilityObservation,
    SourceEndpointInvalidError,
    SourceProbeResult,
)

_AUTH_REF = "server:classic-source-probe"
_SOURCE_ID = "classic-source-candidate"


class ClassicSourceProbeClient:
    """Check only operator-allowlisted origins with a server-held credential."""

    def __init__(self, credential: str, *, allowed_endpoints: tuple[str, ...]) -> None:
        if not isinstance(credential, str) or not credential.strip():
            raise ValueError("classic source probe credential must be non-empty")
        if not allowed_endpoints:
            raise ValueError("classic source probe requires at least one allowed endpoint")
        self._credential = credential
        try:
            self._allowed_endpoints = frozenset(
                ClassicSourceSettings(
                    source_id=_SOURCE_ID,
                    endpoint=endpoint,
                    assistant_id="source-probe-placeholder",
                    auth_ref=_AUTH_REF,
                ).endpoint
                for endpoint in allowed_endpoints
            )
        except ClassicSourceConfigurationError:
            raise ValueError("classic source probe allowed endpoint is invalid") from None

    async def probe(self, endpoint: str, assistant_id: str) -> SourceProbeResult:
        try:
            source = ClassicSourceSettings(
                source_id=_SOURCE_ID,
                endpoint=endpoint,
                assistant_id=assistant_id,
                auth_ref=_AUTH_REF,
                enabled=True,
            )
        except ClassicSourceConfigurationError:
            raise SourceEndpointInvalidError from None
        if source.endpoint not in self._allowed_endpoints:
            # Browser input can select an operator-approved source but can never
            # turn this API into an arbitrary server-side request primitive.
            raise SourceEndpointInvalidError

        async def resolve_credential(reference: str) -> str:
            if reference != _AUTH_REF:
                raise ValueError("unknown credential reference")
            return self._credential

        (qualification,) = await qualify_classic_sources(
            (source,),
            credential_resolver=resolve_credential,
            enabled=True,
        )
        assistant = qualification.assistant
        capabilities = (
            SourceCapabilityObservation(
                name="assistants-read",
                state="available" if assistant is not None else qualification.state,
                reason=(
                    "assistant-qualified"
                    if assistant is not None
                    else qualification.reason or "qualification-failed"
                ),
            ),
            *(
                SourceCapabilityObservation(
                    name=observation.name,
                    state=observation.state,
                    reason=observation.reason,
                )
                for observation in qualification.capabilities
            ),
        )
        return SourceProbeResult(
            state=qualification.state,
            assistant_id=assistant.assistant_id if assistant is not None else None,
            graph_id=assistant.graph_id if assistant is not None else None,
            reason=qualification.reason or "qualification-failed",
            capabilities=capabilities,
        )

    async def close(self) -> None:
        # Each qualification owns and closes its SDK client.
        return None
