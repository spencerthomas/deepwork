from __future__ import annotations

import hashlib
import json
import tomllib
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from langchain_contract_spikes.contracts import (
    SPIKE_IDS,
    dedupe_protocol_events,
    validate_matrix_document,
    validate_ordered_decisions,
)
from langchain_contract_spikes.live import load_live_profile

EVIDENCE = Path(__file__).parents[4] / "docs/references/research/langchain-contract-spikes"


@pytest.fixture(scope="module")
def installed_contract() -> dict[str, Any]:
    from langchain_contract_spikes.installed import capture_installed_contract

    return capture_installed_contract()


def test_probe_lock_pins_the_public_contract_distributions() -> None:
    manifest = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
    assert manifest["project"]["dependencies"] == [
        "deepagents==0.6.12",
        "langchain==1.3.14",
        "langgraph==1.2.9",
        "langgraph-sdk==0.4.2",
        "pytest==9.0.2",
    ]
    assert manifest["tool"]["deepwork"]["contract-pins"]["langgraph-sdk"] == "0.4.2"


def test_installed_hitl_contract_preserves_repeated_names_and_resume_transport(
    installed_contract: dict[str, Any],
) -> None:
    assert installed_contract["distributions"] == {
        "deepagents": "0.6.12",
        "langchain": "1.3.14",
        "langgraph": "1.2.9",
        "langgraph-sdk": "0.4.2",
        "pytest": "9.0.2",
    }
    requests = installed_contract["hitl"]["request"]["action_requests"]
    review_configs = installed_contract["hitl"]["request"]["review_configs"]
    assert [item["name"] for item in requests] == ["write_file", "write_file"]
    assert [item["action_name"] for item in review_configs] == [
        item["name"] for item in requests
    ]
    assert [item["allowed_decisions"] for item in review_configs] == [
        ["approve", "edit", "reject"],
        ["approve", "edit", "reject"],
    ]
    assert [
        item["args"]["path"]
        for item in requests
    ] == [
        "synthetic/a.txt",
        "synthetic/c.txt",
    ]
    assert [item["args"]["path"] for item in installed_contract["hitl"]["revised_tool_calls"]] == [
        "synthetic/a.txt",
        "synthetic/b.txt",
    ]
    assert installed_contract["protocol_v3_resume"] == {
        "command": "input.respond",
        "params": {
            "interrupt_id": "synthetic-interrupt-2",
            "namespace": ["synthetic", "review"],
            "response": {
                "decisions": [
                    {"type": "approve"},
                    {
                        "type": "edit",
                        "edited_action": {
                            "name": "write_file",
                            "args": {"path": "synthetic/b.txt", "content": "synthetic edited"},
                        },
                    },
                ]
            },
        },
    }


def test_retained_installed_hitl_contract_evidence_matches_fresh_capture(
    installed_contract: dict[str, Any],
) -> None:
    retained = json.loads(
        (EVIDENCE / "fixtures/installed-hitl-contract.json").read_text(encoding="utf-8")
    )
    assert retained == installed_contract


def test_installed_hitl_contract_rejects_ambiguous_resume_without_interrupt_id(
    installed_contract: dict[str, Any],
) -> None:
    assert "ambiguous" in installed_contract["ambiguous_resume_error"]


def test_installed_hitl_contract_exercises_reject_and_respond_semantics(
    installed_contract: dict[str, Any],
) -> None:
    outcomes = installed_contract["decision_outcomes"]
    assert outcomes == {
        "reject": {"status": "error", "content": "Synthetic rejection"},
        "respond": {"status": "success", "content": "Synthetic answer"},
    }


def test_installed_hitl_contract_rejects_an_incomplete_decision_vector(
    installed_contract: dict[str, Any],
) -> None:
    assert installed_contract["invalid_decision_length_error"] == (
        "Number of human decisions (1) does not match number of hanging tool calls (2)."
    )


def test_matrix_is_complete() -> None:
    document = json.loads((EVIDENCE / "matrix.json").read_text(encoding="utf-8"))
    assert validate_matrix_document(document) == []
    assert {row["spike_id"] for row in document["rows"]} == set(SPIKE_IDS)
    assert document["installed_public_distributions"] == {
        "deepagents": "0.6.12",
        "langchain": "1.3.14",
        "langgraph": "1.2.9",
        "langgraph-sdk": "0.4.2",
        "pytest": "9.0.2",
    }
    hitl = next(row for row in document["rows"] if row["spike_id"] == "SPIKE-HITL-001")
    assert hitl["evidence_level"] == "installed-public-contract"
    assert hitl["result"] == "blocked-live-evidence"


def test_matrix_rejects_installed_claim_without_distribution_inventory() -> None:
    document = json.loads((EVIDENCE / "matrix.json").read_text(encoding="utf-8"))
    invalid = deepcopy(document)
    invalid["installed_public_distributions"] = {}
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
        "live contract operations remain unavailable: a coordinator-authorized classic "
        "sandbox probe was not produced"
    )
