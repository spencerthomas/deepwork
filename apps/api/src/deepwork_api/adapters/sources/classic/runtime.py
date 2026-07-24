"""Task-execution runtime for a hosted classic LangSmith/LangGraph Deployment.

The classic ``source.py`` module qualifies a deployment (read-only assistant
lookup). This module adds the runtime that actually drives it: start, stream,
approve/reject/respond, edit-plan, and read state.

It deliberately reuses the proven loopback runtime in
:class:`~deepwork_api.adapters.sources.local.source.LocalAgentServerSource`
verbatim: a hosted LangGraph Platform (or Managed Deep Agents) deployment speaks
the same official ``langgraph_sdk`` protocol as a local ``langgraph dev`` server.
Only two things differ and are overridden here:

1. endpoint policy -- a hosted deployment is a qualified HTTPS hostname, not a
   loopback IP (validated by :func:`validate_deployment_endpoint`);
2. authentication -- the official client is built with the server-held
   deployment credential (for example a LangSmith API key). The credential is
   read on the server, never returned to a client, and never logged.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, cast

from deepwork_api.adapters.sources.classic.source import validate_deployment_endpoint
from deepwork_api.adapters.sources.local.source import (
    Decision,
    LocalAgentServerSource,
    LocalSourceConfigurationError,
    LocalSourceUnavailableError,
    _AgentServerClient,
    _ASSISTANT_IDENTIFIER,
)

DEFAULT_CLASSIC_ASSISTANT = "deep-work-local-agent"
_CLASSIC_SDK_TIMEOUT = (5.0, 300.0, 30.0, 5.0)
_MAX_CREDENTIAL_LENGTH = 8_192


@dataclass(frozen=True, slots=True)
class ClassicDeploymentCapabilities:
    """Static mechanics of the hosted classic runtime; not a model/provider claim."""

    source_kind: Literal["classic-deployment"] = "classic-deployment"
    transport: Literal["langgraph-sdk"] = "langgraph-sdk"
    loopback_only: Literal[False] = False
    creates_thread_runs: Literal[True] = True
    resumable_run_stream: Literal["last-event-id"] = "last-event-id"
    plan_state_update: Literal["update-state-as-plan"] = "update-state-as-plan"
    accepts_credentials: Literal[True] = True


def create_classic_client(endpoint: str, *, credential: str) -> _AgentServerClient:
    """Construct the public ``langgraph_sdk`` client for a hosted deployment.

    ``endpoint`` must be a qualified HTTPS deployment origin; ``credential`` is the
    server-held deployment API key (for example a LangSmith key). Neither the
    credential nor upstream error detail is allowed to escape this boundary.
    """

    normalized = validate_deployment_endpoint(endpoint)
    if not isinstance(credential, str) or not credential.strip():
        raise LocalSourceConfigurationError("classic deployment credential is required")
    if len(credential) > _MAX_CREDENTIAL_LENGTH:
        raise LocalSourceConfigurationError("classic deployment credential is too long")
    try:
        module = importlib.import_module("langgraph_sdk")
        factory_value = getattr(module, "get_client", None)
        if not callable(factory_value):
            raise AttributeError
        factory = cast("Callable[..., object]", factory_value)
        return cast(
            "_AgentServerClient",
            factory(
                url=normalized,
                api_key=credential,
                headers={},
                timeout=_CLASSIC_SDK_TIMEOUT,
            ),
        )
    except LocalSourceConfigurationError:
        raise
    except Exception:
        raise LocalSourceUnavailableError("official LangGraph SDK is unavailable") from None


@dataclass(frozen=True, slots=True)
class ClassicDeploymentSource(LocalAgentServerSource):
    """Drive a hosted classic LangSmith/LangGraph Deployment over the official SDK.

    Reuses every runtime method of :class:`LocalAgentServerSource` unchanged and
    overrides only the endpoint policy (qualified HTTPS) and construction (with the
    server-held deployment credential).
    """

    def __post_init__(self) -> None:
        # Qualified HTTPS endpoint instead of the loopback policy of the base class.
        object.__setattr__(self, "endpoint", validate_deployment_endpoint(self.endpoint))
        if not _ASSISTANT_IDENTIFIER.fullmatch(self.assistant_id):
            raise LocalSourceConfigurationError("classic deployment assistant identifier is invalid")

    @classmethod
    def from_classic_deployment(
        cls,
        *,
        endpoint: str,
        assistant_id: str,
        credential: str,
    ) -> ClassicDeploymentSource:
        """Build the adapter with the official credentialed client."""

        return cls(
            client=create_classic_client(endpoint, credential=credential),
            endpoint=endpoint,
            assistant_id=assistant_id,
        )

    def capabilities(self) -> ClassicDeploymentCapabilities:  # type: ignore[override]
        """Report hosted mechanics without claiming model/provider availability."""

        return ClassicDeploymentCapabilities()


__all__ = [
    "DEFAULT_CLASSIC_ASSISTANT",
    "ClassicDeploymentCapabilities",
    "ClassicDeploymentSource",
    "Decision",
    "create_classic_client",
]
