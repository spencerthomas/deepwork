from __future__ import annotations

import hashlib
import json
import tomllib
from copy import deepcopy
from pathlib import Path

import pytest

from langchain_contract_spikes.contracts import (
    SPIKE_IDS,
    dedupe_protocol_events,
    validate_matrix_document,
    validate_ordered_decisions,
)
from langchain_contract_spikes.live import load_live_profile

EVIDENCE = Path(__file__).parents[4] / "docs/references/research/langchain-contract-spikes"


def test_candidate_source_contract_is_not_promoted_to_installed() -> None:
    manifest = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
    assert manifest["project"]["dependencies"] == []
    assert manifest["tool"]["deepwork"]["contract-pins"]["langgraph-sdk"] == "0.4.2"


def test_matrix_is_complete() -> None:
    document = json.loads((EVIDENCE / "matrix.json").read_text(encoding="utf-8"))
    assert validate_matrix_document(document) == []
    assert {row["spike_id"] for row in document["rows"]} == set(SPIKE_IDS)


def test_matrix_rejects_installed_claim_without_distribution_inventory() -> None:
    document = json.loads((EVIDENCE / "matrix.json").read_text(encoding="utf-8"))
    invalid = deepcopy(document)
    invalid["rows"][0]["evidence_level"] = "installed-public-contract"
    assert any("cannot claim installed evidence" in error for error in validate_matrix_document(invalid))


def test_protocol_v3_replay_dedupes_by_event_id() -> None:
    transcript = json.loads((EVIDENCE / "fixtures/protocol-v3-events.json").read_text(encoding="utf-8"))
    projected = dedupe_protocol_events(transcript["events"], since=1)
    assert [event["event_id"] for event in projected] == ["evt-synthetic-2", "evt-synthetic-3"]


def test_hitl_preserves_order_and_allowed_decisions() -> None:
    fixture = json.loads((EVIDENCE / "fixtures/hitl-ordered-batch.json").read_text(encoding="utf-8"))
    validate_ordered_decisions(fixture["action_requests"], fixture["review_configs"], fixture["decisions"])


def test_hitl_rejects_positional_decision_not_allowed_for_repeated_name() -> None:
    fixture = json.loads((EVIDENCE / "fixtures/hitl-ordered-batch.json").read_text(encoding="utf-8"))
    with pytest.raises(ValueError, match="not allowed"):
        validate_ordered_decisions(
            fixture["action_requests"],
            fixture["review_configs"],
            list(reversed(fixture["decisions"])),
        )


def test_fixture_manifest_hashes_match() -> None:
    manifest = json.loads((EVIDENCE / "fixtures/manifest.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        content = (EVIDENCE / "fixtures" / item["path"]).read_bytes()
        assert hashlib.sha256(content).hexdigest() == item["sha256"]


def test_assistant_search_fixture_uses_generated_bare_array() -> None:
    transcript = json.loads(
        (EVIDENCE / "fixtures/package-source-contract-transcript.json").read_text(encoding="utf-8")
    )
    operation = next(item for item in transcript["operations"] if item["operation"] == "assistant.search")
    assert isinstance(operation["response"], list)
    assert operation["response"][0]["assistant_id"] == "00000000-0000-4000-8000-000000000001"


def test_live_profile_fails_closed_when_absent() -> None:
    with pytest.raises(RuntimeError, match="live profile unavailable"):
        load_live_profile({})


@pytest.mark.live_contract
def test_live_contract_requires_explicit_profile(request) -> None:
    load_live_profile(
        {
            "profile": request.config.getoption("--live-profile"),
            "base_url": request.config.getoption("--live-base-url"),
            "account_tier": request.config.getoption("--live-account-tier"),
            "region": request.config.getoption("--live-region"),
            "server_revision": request.config.getoption("--live-server-revision"),
        }
    )
    pytest.fail(
        "live contract operations remain unavailable: installed public SDK evidence and "
        "coordinator-authorized sandbox probes were not produced"
    )
