"""Fail-closed qualification for configured classic LangSmith Deployments.

This module deliberately implements only a bounded assistant lookup. Runtime
operations stay gated until their pinned live-contract spikes are accepted.
Endpoint validation rejects obvious unsafe shapes, but is not a complete
DNS-rebinding or redirect SSRF defence; those controls belong at egress.
"""

from __future__ import annotations

import importlib
import ipaddress
import re
import socket
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal, Protocol, cast
from urllib.parse import unquote, urlsplit, urlunsplit

QualificationState = Literal[
    "available",
    "unavailable",
    "gated",
    "permission-denied",
    "unknown",
]
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_AUTH_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,511}$")
_HOST_LABEL = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")
_INVALID_PERCENT_ESCAPE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_SDK_TIMEOUT = (5.0, 20.0, 20.0, 5.0)
_MAX_CREDENTIAL_LENGTH = 8_192

LIVE_CONTRACT_CAPABILITIES = (
    "task",
    "run",
    "thread",
    "stream",
    "steer",
    "hitl",
    "cancel",
    "checkpoint",
    "config",
    "compose",
    "deploy",
)


class _AssistantsClient(Protocol):
    async def get(self, assistant_id: str) -> object: ...


class _ClassicClient(Protocol):
    @property
    def assistants(self) -> _AssistantsClient: ...

    async def aclose(self) -> None: ...


CredentialResolver = Callable[[str], Awaitable[str]]
ClientFactory = Callable[..., _ClassicClient]


class ClassicSourceConfigurationError(ValueError):
    """A source setting is invalid before any external side effect."""


@dataclass(frozen=True, slots=True)
class ClassicSourceSettings:
    """Server-owned settings; callers must use ``safe_projection`` externally."""

    source_id: str
    endpoint: str
    assistant_id: str
    auth_ref: str = field(repr=False)
    enabled: bool = False

    def __post_init__(self) -> None:
        if not _IDENTIFIER.fullmatch(self.source_id):
            raise ClassicSourceConfigurationError("classic source identifier is invalid")
        if not _IDENTIFIER.fullmatch(self.assistant_id):
            raise ClassicSourceConfigurationError("classic assistant identifier is invalid")
        if not _AUTH_REF.fullmatch(self.auth_ref):
            raise ClassicSourceConfigurationError("classic credential reference is invalid")
        object.__setattr__(self, "endpoint", validate_deployment_endpoint(self.endpoint))

    def safe_projection(self) -> ClassicSourceSettingsProjection:
        """Return the only configuration view that may cross this boundary."""

        return ClassicSourceSettingsProjection(
            source_id=self.source_id,
            assistant_id=self.assistant_id,
            enabled=self.enabled,
        )


@dataclass(frozen=True, slots=True)
class ClassicSourceSettingsProjection:
    """Credential-free, endpoint-free source configuration projection."""

    source_id: str
    assistant_id: str
    enabled: bool


@dataclass(frozen=True, slots=True)
class ClassicAssistantProjection:
    """Only source-qualified assistant identity may leave the adapter."""

    source_id: str
    assistant_id: str
    graph_id: str


@dataclass(frozen=True, slots=True)
class CapabilityObservation:
    """Sanitized capability evidence without upstream text."""

    name: str
    state: QualificationState = "gated"
    reason: str = "blocked-live-evidence"


@dataclass(frozen=True, slots=True)
class ClassicQualification:
    """One source result; never contains endpoint or authentication material."""

    source_id: str
    state: QualificationState
    assistant: ClassicAssistantProjection | None = None
    reason: str | None = None
    capabilities: tuple[CapabilityObservation, ...] = field(
        default_factory=lambda: tuple(
            CapabilityObservation(name=name) for name in LIVE_CONTRACT_CAPABILITIES
        )
    )


def validate_deployment_endpoint(value: str) -> str:
    """Accept a hostname-based HTTPS deployment URL and preserve its mount path."""

    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ClassicSourceConfigurationError("classic deployment endpoint is invalid")
    try:
        parsed = urlsplit(value)
        port = parsed.port
        host = parsed.hostname
    except ValueError:
        raise ClassicSourceConfigurationError("classic deployment endpoint is invalid") from None
    if (
        parsed.scheme != "https"
        or not host
        or port == 0
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path.startswith("//")
        or "\\" in parsed.path
    ):
        raise ClassicSourceConfigurationError(
            "classic deployment endpoint must be a safe HTTPS URL"
        )
    try:
        ipaddress.ip_address(host)
    except ValueError:
        try:
            socket.inet_aton(host)
        except OSError:
            pass
        else:
            raise ClassicSourceConfigurationError(
                "classic deployment endpoint must not use an IP literal"
            ) from None
    else:
        raise ClassicSourceConfigurationError(
            "classic deployment endpoint must not use an IP literal"
        )
    normalized_host = host.rstrip(".").lower()
    if (
        normalized_host == "localhost"
        or "." not in normalized_host
        or any(not _HOST_LABEL.fullmatch(label) for label in normalized_host.split("."))
    ):
        raise ClassicSourceConfigurationError(
            "classic deployment endpoint must use a qualified hostname"
        )
    _validate_mount_path(parsed.path)
    netloc = normalized_host if port is None else f"{normalized_host}:{port}"
    path = parsed.path.rstrip("/")
    return urlunsplit(("https", netloc, path, "", ""))


def _validate_mount_path(path: str) -> None:
    candidate = path
    for _ in range(8):
        _validate_decoded_mount_path(candidate)
        decoded = unquote(candidate)
        if decoded == candidate:
            return
        if decoded.count("/") != candidate.count("/") or "\\" in decoded:
            raise ClassicSourceConfigurationError("classic deployment mount path is unsafe")
        candidate = decoded
    _validate_decoded_mount_path(candidate)
    if unquote(candidate) == candidate:
        return
    raise ClassicSourceConfigurationError("classic deployment mount path is ambiguous")


def _validate_decoded_mount_path(path: str) -> None:
    if _INVALID_PERCENT_ESCAPE.search(path):
        raise ClassicSourceConfigurationError("classic deployment mount path is invalid")
    if (
        path.startswith("//")
        or "\\" in path
        or any(ord(character) < 32 or ord(character) == 127 for character in path)
        or any(segment in {".", ".."} for segment in path.split("/"))
    ):
        raise ClassicSourceConfigurationError("classic deployment mount path is unsafe")


def _official_client_factory() -> ClientFactory:
    try:
        module = importlib.import_module("langgraph_sdk")
        factory_value = getattr(module, "get_client", None)
        if not callable(factory_value):
            raise AttributeError
    except Exception:
        raise RuntimeError("official LangGraph SDK is unavailable") from None
    return cast("ClientFactory", factory_value)


def _safe_identifier(record: Mapping[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ValueError("malformed assistant response")
    return value


def _project_assistant(
    source: ClassicSourceSettings,
    response: object,
) -> ClassicAssistantProjection:
    if not isinstance(response, Mapping):
        raise ValueError("malformed assistant response")
    record = cast("Mapping[str, object]", response)
    assistant_id = _safe_identifier(record, "assistant_id")
    graph_id = _safe_identifier(record, "graph_id")
    if assistant_id != source.assistant_id:
        raise ValueError("malformed assistant response")
    return ClassicAssistantProjection(
        source_id=source.source_id,
        assistant_id=assistant_id,
        graph_id=graph_id,
    )


async def qualify_classic_sources(
    sources: Sequence[ClassicSourceSettings],
    *,
    credential_resolver: CredentialResolver,
    enabled: bool = False,
    client_factory: ClientFactory | None = None,
) -> tuple[ClassicQualification, ...]:
    """Qualify sources in input order while isolating per-source failures."""

    source_ids = [source.source_id for source in sources]
    if len(source_ids) != len(set(source_ids)):
        raise ClassicSourceConfigurationError("duplicate classic source identifier")

    if not enabled:
        return tuple(
            ClassicQualification(
                source_id=source.source_id,
                state="gated",
                reason="classic-source-disabled",
            )
            for source in sources
        )

    factory = client_factory
    results: list[ClassicQualification] = []
    for source in sources:
        if not source.enabled:
            results.append(
                ClassicQualification(
                    source_id=source.source_id,
                    state="gated",
                    reason="classic-source-disabled",
                )
            )
            continue

        try:
            credential = await credential_resolver(source.auth_ref)
        except Exception:
            results.append(
                ClassicQualification(
                    source_id=source.source_id,
                    state="permission-denied",
                    reason="credential-unavailable",
                )
            )
            continue
        if (
            not isinstance(credential, str)
            or not credential.strip()
            or len(credential) > _MAX_CREDENTIAL_LENGTH
        ):
            results.append(
                ClassicQualification(
                    source_id=source.source_id,
                    state="permission-denied",
                    reason="credential-unavailable",
                )
            )
            continue

        try:
            if factory is None:
                factory = _official_client_factory()
            client = factory(
                url=source.endpoint,
                api_key=credential,
                headers={},
                timeout=_SDK_TIMEOUT,
            )
        except Exception:
            results.append(
                ClassicQualification(
                    source_id=source.source_id,
                    state="unknown",
                    reason="client-unavailable",
                )
            )
            continue

        try:
            try:
                response = await client.assistants.get(source.assistant_id)
            except Exception:
                results.append(
                    ClassicQualification(
                        source_id=source.source_id,
                        state="unknown",
                        reason="qualification-failed",
                    )
                )
            else:
                try:
                    assistant = _project_assistant(source, response)
                except ValueError:
                    results.append(
                        ClassicQualification(
                            source_id=source.source_id,
                            state="unavailable",
                            reason="assistant-contract-mismatch",
                        )
                    )
                else:
                    results.append(
                        ClassicQualification(
                            source_id=source.source_id,
                            state="available",
                            assistant=assistant,
                            reason="assistant-qualified-read-only",
                        )
                    )
        finally:
            try:
                await client.aclose()
            except Exception:
                if results and results[-1].source_id == source.source_id:
                    results[-1] = ClassicQualification(
                        source_id=source.source_id,
                        state="unknown",
                        reason="client-close-failed",
                    )
    return tuple(results)
