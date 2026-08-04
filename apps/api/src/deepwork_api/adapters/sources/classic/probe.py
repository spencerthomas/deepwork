"""Server-credentialed classic deployment qualification adapter."""

from __future__ import annotations

from datetime import UTC, datetime

from deepwork_api.adapters.sources.classic.source import (
    ClassicSourceConfigurationError,
    ClassicSourceSettings,
    qualify_classic_sources,
    validate_deployment_endpoint,
)
from deepwork_api.domain import (
    SourceCapabilityObservation,
    SourceEndpointInvalidError,
    SourceProbeResult,
)
from deepwork_api.domain.sources import SourceCapabilitySafeReason, SourceProbeState

_AUTH_REF = "server:classic-source-probe"
_SOURCE_ID = "classic-source-candidate"
_ADAPTER_VERSION = "classic-source-probe-v1"
_CONTRACT_VERSION = "langgraph-assistants-get-v1"


def _safe_capability_state(
    state: str,
) -> tuple[SourceProbeState, SourceCapabilitySafeReason]:
    if state == "permission-denied":
        return "permission-denied", "permission-required"
    if state == "unavailable":
        return "unavailable", "source-unavailable"
    return "unknown", "contract-not-verified"


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
                validate_deployment_endpoint(endpoint) for endpoint in allowed_endpoints
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
        observed_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        assistant_state, assistant_safe_reason = _safe_capability_state(qualification.state)
        capabilities = (
            SourceCapabilityObservation(
                name="assistants-read",
                state="available" if assistant is not None else assistant_state,
                safe_reason=None if assistant is not None else assistant_safe_reason,
                observed_at=observed_at,
                adapter_version=_ADAPTER_VERSION,
                contract_version=_CONTRACT_VERSION,
                evidence_class="live-contract",
            ),
            *(
                SourceCapabilityObservation(
                    name=observation.name,
                    state="gated",
                    safe_reason="adapter-disabled",
                    observed_at=observed_at,
                    adapter_version=_ADAPTER_VERSION,
                    contract_version=_CONTRACT_VERSION,
                    evidence_class="documented",
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
