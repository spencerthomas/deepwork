"""Opt-in read-only probes for official regional platform/control hosts.

The profile is mounted outside the repository. This runner deliberately does not
accept or construct an Agent Server origin: the documented authenticated
``GET /v2/deployments/{deployment_id}`` response does not define an Agent Server
URL field. A future origin may be accepted only from an authenticated,
documented control-plane response field with its own reviewed contract. Until
then, all data-plane live rows remain blocked.
"""

from __future__ import annotations

import http.client
import ipaddress
import json
import socket
import ssl
import uuid
from dataclasses import dataclass
from pathlib import Path

from .catalog import COLLECTED_AT

REGION_HOSTS = {
    "gcp-us": {
        "platform": "api.smith.langchain.com",
        "control": "api.host.langchain.com",
    },
    "gcp-eu": {
        "platform": "eu.api.smith.langchain.com",
        "control": "eu.api.host.langchain.com",
    },
    "gcp-apac": {
        "platform": "apac.api.smith.langchain.com",
        "control": "apac.api.host.langchain.com",
    },
    "aws-us": {
        "platform": "aws.api.smith.langchain.com",
        "control": "aws.api.host.langchain.com",
    },
}


class LiveProfileRejected(ValueError):
    pass


@dataclass(frozen=True)
class LiveProfile:
    api_key: str
    workspace_id: str
    deployment_id: str
    account_tier: str
    region: str


def _authority_value(value: object, label: str, *, maximum: int = 512) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise LiveProfileRejected(f"invalid-{label}")
    return value


def _uuid_value(value: object, label: str) -> str:
    text = _authority_value(value, label, maximum=36)
    try:
        parsed = uuid.UUID(text)
    except ValueError as error:
        raise LiveProfileRejected(f"invalid-{label}") from error
    if str(parsed) != text.lower():
        raise LiveProfileRejected(f"noncanonical-{label}")
    return text


def load_profile(data: dict[str, object]) -> LiveProfile:
    allowed_fields = {
        "account_class",
        "read_only",
        "api_key",
        "workspace_id",
        "deployment_id",
        "account_tier",
        "region",
    }
    if set(data) - allowed_fields:
        raise LiveProfileRejected("unsupported-live-profile-field")
    if data.get("account_class") != "non-production-classic":
        raise LiveProfileRejected("not-non-production-classic")
    if data.get("read_only") is not True:
        raise LiveProfileRejected("not-read-only")
    region = _authority_value(data.get("region"), "region", maximum=16)
    if region not in REGION_HOSTS:
        raise LiveProfileRejected("unsupported-region")
    tier = _authority_value(data.get("account_tier"), "account-tier", maximum=32)
    if tier not in {
        "developer",
        "plus",
        "enterprise",
        "unknown-non-production",
    }:
        raise LiveProfileRejected("unsupported-account-tier")
    return LiveProfile(
        api_key=_authority_value(data.get("api_key"), "api-key"),
        workspace_id=_uuid_value(data.get("workspace_id"), "workspace-id"),
        deployment_id=_uuid_value(data.get("deployment_id"), "deployment-id"),
        account_tier=tier,
        region=region,
    )


def _public_addresses(hostname: str) -> list[str]:
    try:
        addresses = sorted(
            {
                item[4][0]
                for item in socket.getaddrinfo(
                    hostname, 443, type=socket.SOCK_STREAM
                )
            }
        )
    except OSError:
        return []
    if any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise LiveProfileRejected("non-public-official-host-resolution")
    return addresses


def _pinned_https_get(
    hostname: str, route: str, headers: dict[str, str]
) -> int:
    if (
        not route.startswith("/")
        or "://" in route
        or "\\" in route
        or ".." in route
        or any(ord(character) < 32 for character in route)
    ):
        raise LiveProfileRejected("unsafe-route")
    official_hosts = {
        hosts[plane]
        for hosts in REGION_HOSTS.values()
        for plane in ("platform", "control")
    }
    if hostname not in official_hosts:
        raise LiveProfileRejected("unverified-official-host")
    context = ssl.create_default_context()
    for address in _public_addresses(hostname):
        connection: http.client.HTTPSConnection | None = None
        try:
            raw_socket = socket.create_connection((address, 443), timeout=5)
            tls_socket = context.wrap_socket(raw_socket, server_hostname=hostname)
            connection = http.client.HTTPSConnection(
                hostname, 443, timeout=5, context=context
            )
            # Pin TLS to the address already checked above. No proxy, redirect
            # handler, netrc lookup, or second DNS resolution is involved.
            connection.sock = tls_socket
            connection.request(
                "GET",
                route,
                headers={
                    **headers,
                    "Host": hostname,
                    "User-Agent": "auth-contract-spikes/0.1",
                },
            )
            response = connection.getresponse()
            if 300 <= response.status < 400:
                raise LiveProfileRejected("unexpected-redirect")
            if len(response.read(4097)) > 4096:
                raise LiveProfileRejected("oversized-provider-response")
            return int(response.status)
        except LiveProfileRejected:
            raise
        except (OSError, ssl.SSLError, http.client.HTTPException):
            continue
        finally:
            if connection is not None:
                connection.close()
    return 0


def run_read_only_profile(
    profile_data: dict[str, object], evidence_dir: Path
) -> dict[str, object]:
    profile = load_profile(profile_data)
    hosts = REGION_HOSTS[profile.region]
    observations = [
        {
            "operation": "list-workspaces",
            "host_class": "langsmith-platform-api",
            "status": _pinned_https_get(
                hosts["platform"],
                "/api/v1/workspaces",
                {"X-Api-Key": profile.api_key},
            ),
        },
        {
            "operation": "read-classic-deployment",
            "host_class": "regional-langsmith-control-plane-api",
            "status": _pinned_https_get(
                hosts["control"],
                f"/v2/deployments/{profile.deployment_id}",
                {
                    "X-Api-Key": profile.api_key,
                    "X-Tenant-Id": profile.workspace_id,
                },
            ),
        },
    ]
    evidence = {
        "schema_version": 1,
        "date": COLLECTED_AT,
        "evidence_class": "unreviewed-live-contract",
        "account_tier": profile.account_tier,
        "region": profile.region,
        "server_revision": None,
        "read_only": True,
        "request_count": 2,
        "origins_persisted": False,
        "provider_bodies_persisted": False,
        "agent_server_rows": "blocked-live-evidence",
        "observations": observations,
        "reviewer_status": "pending-independent-review",
    }
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "live-summary.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    )
    return evidence
