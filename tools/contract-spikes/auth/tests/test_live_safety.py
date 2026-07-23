from __future__ import annotations

import pytest

from auth_contract_spikes.live import (
    LiveProfileRejected,
    _pinned_https_get,
    load_profile,
)

SYNTHETIC_PROFILE = {
    "account_class": "non-production-classic",
    "read_only": True,
    "api_key": "<synthetic-key>",
    "workspace_id": "00000000-0000-4000-8000-000000000001",
    "deployment_id": "00000000-0000-4000-8000-000000000002",
    "account_tier": "unknown-non-production",
    "region": "gcp-us",
}


def test_live_profile_has_no_agent_origin_input() -> None:
    with pytest.raises(
        LiveProfileRejected, match="unsupported-live-profile-field"
    ):
        load_profile(
            {**SYNTHETIC_PROFILE, "agent_origin": "https://attacker.example.org"}
        )


def test_live_profile_rejects_noncanonical_context_ids() -> None:
    with pytest.raises(LiveProfileRejected, match="invalid-workspace-id"):
        load_profile({**SYNTHETIC_PROFILE, "workspace_id": "tenant-alias"})


def test_live_transport_rejects_nonofficial_host_before_dns(monkeypatch) -> None:
    monkeypatch.setattr(
        "auth_contract_spikes.live._public_addresses",
        lambda hostname: pytest.fail("DNS must not run for an unverified host"),
    )
    with pytest.raises(LiveProfileRejected, match="unverified-official-host"):
        _pinned_https_get(
            "attacker.example.org",
            "/ok",
            {"X-Api-Key": "<synthetic-key>"},
        )
