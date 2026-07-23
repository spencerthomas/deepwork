from __future__ import annotations

import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from auth_contract_spikes.policy import (
    ContractRejected,
    normalize_provider_error,
    prepare_probe,
    sanitize_headers,
)
from auth_contract_spikes.synthetic_server import synthetic_server


def test_platform_headers_are_selected_server_side() -> None:
    prepared = prepare_probe(
        "current-organization",
        server_credential="<synthetic-key>",
        key_class="personal",
        workspace_id="<workspace-id>",
        organization_id="<organization-id>",
    )
    assert prepared.headers == {
        "X-Api-Key": "<synthetic-key>",
        "X-Organization-Id": "<organization-id>",
    }


@pytest.mark.parametrize(
    "header",
    [
        "Authorization",
        "Baggage",
        "Cookie",
        "Forwarded",
        "Host",
        "Proxy-Authorization",
        "Traceparent",
        "Via",
        "X-Api-Key",
        "X-Amzn-Trace-Id",
        "X-Forwarded-Host",
        "X-Original-URL",
        "X-Tenant-Id",
    ],
)
def test_caller_authority_headers_fail_closed(header: str) -> None:
    with pytest.raises(ContractRejected, match="caller-authority-header"):
        prepare_probe(
            "agent-server-health",
            server_credential="<synthetic-key>",
            key_class="personal",
            caller_headers={header: "<caller-value>"},
        )


def test_target_override_fails_closed() -> None:
    with pytest.raises(ContractRejected, match="caller-target-override"):
        prepare_probe(
            "agent-server-health",
            server_credential="<synthetic-key>",
            key_class="personal",
            target_override="https://untrusted.example.org",
        )


def test_duplicate_case_variant_header_fails_closed() -> None:
    with pytest.raises(ContractRejected, match="duplicate-caller-header"):
        prepare_probe(
            "agent-server-health",
            server_credential="<synthetic-key>",
            key_class="personal",
            caller_headers=[("Accept", "application/json"), ("accept", "text/plain")],
        )


def test_crlf_header_fails_closed() -> None:
    with pytest.raises(ContractRejected, match="invalid-caller-header"):
        prepare_probe(
            "agent-server-health",
            server_credential="<synthetic-key>",
            key_class="personal",
            caller_headers=[("X-Request-Id", "safe\r\nX-Api-Key: injected")],
        )


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("Host ", "untrusted"),
        ("\tAuthorization", "untrusted"),
        ("X-Request-Id", "safe\x00unsafe"),
    ],
)
def test_malformed_caller_header_fails_closed(name: str, value: str) -> None:
    with pytest.raises(ContractRejected, match="invalid-caller-header"):
        prepare_probe(
            "agent-server-health",
            server_credential="<synthetic-key>",
            key_class="personal",
            caller_headers=[(name, value)],
        )


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("workspace_id", "safe\r\nX-Api-Key: injected", "invalid-workspace-context"),
        (
            "organization_id",
            "safe\nX-Tenant-Id: injected",
            "invalid-organization-context",
        ),
    ],
)
def test_stored_context_control_characters_fail_closed(
    field: str, value: str, error: str
) -> None:
    kwargs = {
        "operation_name": "current-organization",
        "server_credential": "<synthetic-key>",
        "key_class": "personal",
        "workspace_id": "<workspace-id>",
        "organization_id": "<organization-id>",
    }
    kwargs[field] = value
    with pytest.raises(ContractRejected, match=error):
        prepare_probe(**kwargs)


def test_conflicting_typed_workspace_context_fails_closed() -> None:
    with pytest.raises(ContractRejected, match="conflicting-workspace-context"):
        prepare_probe(
            "search-assistants",
            server_credential="<synthetic-key>",
            key_class="personal",
            workspace_id="<workspace-id>",
            secondary_workspace_id="<wrong-workspace-id>",
        )


def test_control_plane_workspace_context_is_required() -> None:
    with pytest.raises(ContractRejected, match="missing-required-workspace-context"):
        prepare_probe(
            "list-classic-deployments",
            server_credential="<synthetic-key>",
            key_class="personal",
        )


def test_control_plane_uses_documented_workspace_header() -> None:
    prepared = prepare_probe(
        "list-classic-deployments",
        server_credential="<synthetic-key>",
        key_class="service-organization",
        workspace_id="<workspace-id>",
    )
    assert prepared.headers == {
        "X-Api-Key": "<synthetic-key>",
        "X-Tenant-Id": "<workspace-id>",
    }


def test_agent_server_does_not_receive_workspace_header() -> None:
    prepared = prepare_probe(
        "search-assistants",
        server_credential="<synthetic-key>",
            key_class="service-workspace-single",
        workspace_id="<selector-only-workspace-id>",
    )
    assert prepared.headers == {"X-Api-Key": "<synthetic-key>"}


def test_header_sanitization_retains_names_not_values() -> None:
    assert sanitize_headers(
        {
            "X-Api-Key": "<synthetic-key>",
            "Cookie": "<synthetic-cookie>",
            "Content-Type": "application/json",
        }
    ) == {
        "Content-Type": "<present>",
        "Cookie": "<redacted>",
        "X-Api-Key": "<redacted>",
    }


def test_error_normalization_never_retains_provider_body() -> None:
    assert normalize_provider_error(403) == {
        "code": "source-forbidden",
        "status": 403,
        "message": "The source operation is unavailable for this credential and context.",
        "provider_body_retained": False,
    }


def test_loopback_synthetic_server_redacts_observed_headers() -> None:
    with synthetic_server() as base_url:
        request = Request(
            f"{base_url}/assistants/search",
            headers={"X-Api-Key": "<synthetic-key>"},
            method="POST",
            data=b"{}",
        )
        with urlopen(request, timeout=2) as response:
            payload = json.loads(response.read())
    assert payload["ok"] is True
    assert payload["observed_headers"]["X-Api-Key"] == "<redacted>"


def test_loopback_synthetic_server_rejects_missing_auth() -> None:
    with synthetic_server() as base_url:
        request = Request(f"{base_url}/ok", method="GET")
        with pytest.raises(HTTPError) as error:
            urlopen(request, timeout=2)
    assert error.value.code == 401
