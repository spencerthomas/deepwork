"""Fail-closed synthetic header-selection and error-normalization policy."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping, Sequence
import re

from .catalog import FORBIDDEN_CALLER_HEADERS, operation_map


class ContractRejected(ValueError):
    """A request could not be made without guessing or forwarding authority."""


HEADER_NAME_PATTERN = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")


@dataclass(frozen=True)
class PreparedProbe:
    method: str
    route_template: str
    service_host_class: str
    headers: dict[str, str]


def _validate_authority_value(value: str, label: str) -> str:
    if (
        not value
        or len(value) > 256
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ContractRejected(f"invalid-{label}")
    return value


def prepare_probe(
    operation_name: str,
    *,
    server_credential: str | None,
    key_class: str,
    workspace_id: str | None = None,
    secondary_workspace_id: str | None = None,
    organization_id: str | None = None,
    caller_headers: Mapping[str, str] | Sequence[tuple[str, str]] | None = None,
    target_override: str | None = None,
) -> PreparedProbe:
    """Construct a synthetic request without accepting caller-controlled authority."""

    operation = operation_map().get(operation_name)
    if operation is None:
        raise ContractRejected("unknown-operation")
    if target_override is not None:
        raise ContractRejected("caller-target-override")
    if not server_credential:
        raise ContractRejected("missing-server-credential")
    _validate_authority_value(server_credential, "server-credential")
    if key_class not in {
        "personal",
        "service-workspace-single",
        "service-workspace-multiple",
        "service-organization",
    }:
        raise ContractRejected("unsupported-key-class")

    pairs = (
        list(caller_headers.items())
        if isinstance(caller_headers, Mapping)
        else list(caller_headers or ())
    )
    seen: set[str] = set()
    for name, value in pairs:
        if (
            not isinstance(name, str)
            or not isinstance(value, str)
            or not HEADER_NAME_PATTERN.fullmatch(name)
            or any(
                ord(character) < 32 or ord(character) == 127
                for character in value
            )
        ):
            raise ContractRejected("invalid-caller-header")
        lowered = name.lower()
        if lowered in seen:
            raise ContractRejected("duplicate-caller-header")
        seen.add(lowered)
        if (
            lowered in FORBIDDEN_CALLER_HEADERS
            or lowered.startswith("x-forwarded-")
            or lowered.startswith("x-original-")
            or lowered.startswith("x-b3-")
        ):
            raise ContractRejected("caller-authority-header")

    headers = {"X-Api-Key": server_credential}
    if workspace_id is not None:
        _validate_authority_value(workspace_id, "workspace-context")
    if secondary_workspace_id is not None:
        _validate_authority_value(
            secondary_workspace_id, "secondary-workspace-context"
        )
        if workspace_id is None or secondary_workspace_id != workspace_id:
            raise ContractRejected("conflicting-workspace-context")
    if organization_id is not None:
        _validate_authority_value(organization_id, "organization-context")
    if operation.plane == "platform":
        if operation.operation in {"current-organization", "list-workspaces"}:
            if not organization_id:
                raise ContractRejected("missing-organization-context")
            headers["X-Organization-Id"] = organization_id
        if key_class == "service-organization" and operation.operation not in {
            "current-organization",
            "list-workspaces",
        } and not workspace_id:
            raise ContractRejected("missing-required-workspace-context")
    elif workspace_id or organization_id:
        # Context may be used to resolve an allowlisted deployment before this
        # boundary, but no workspace/org header is forwarded to Agent Server or
        # the unresolved control-plane host without accepted evidence.
        if operation.plane == "control":
            headers["X-Tenant-Id"] = workspace_id or ""
    if operation.plane == "control" and not workspace_id:
        raise ContractRejected("missing-required-workspace-context")

    return PreparedProbe(
        method=operation.method,
        route_template=operation.route_template,
        service_host_class=operation.service_host_class,
        headers=headers,
    )


def sanitize_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """Retain header names while removing every value with authority."""

    sanitized: dict[str, str] = {}
    for name in sorted(headers, key=str.lower):
        if name.lower() in {
            "authorization",
            "cookie",
            "set-cookie",
            "x-api-key",
            "x-organization-id",
            "x-tenant-id",
        }:
            sanitized[name] = "<redacted>"
        else:
            sanitized[name] = "<present>"
    return sanitized


def normalize_provider_error(status: int) -> dict[str, object]:
    """Return a stable error without echoing a provider body or identifier."""

    code = {
        401: "source-unauthorized",
        403: "source-forbidden",
        404: "source-not-found",
        409: "source-context-conflict",
        429: "source-rate-limited",
    }.get(status, "source-unavailable")
    return {
        "code": code,
        "status": status if status in {401, 403, 404, 409, 429} else 502,
        "message": "The source operation is unavailable for this credential and context.",
        "provider_body_retained": False,
    }
