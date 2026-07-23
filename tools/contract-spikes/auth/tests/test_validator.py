from __future__ import annotations

import hashlib
import json

import pytest

from auth_contract_spikes.generate_matrix import write_outputs
from auth_contract_spikes.validate_matrix import MatrixError, validate


@pytest.fixture
def corpus(tmp_path):
    write_outputs(tmp_path)
    return tmp_path


def _validate(path) -> None:
    validate(
        path,
        require_complete_cross_product=True,
        reject_unresolved_precedence_conflicts=True,
    )


def test_generated_corpus_passes_strict_validator(corpus) -> None:
    _validate(corpus / "matrix.json")


def test_pending_self_declared_live_evidence_cannot_open_row(corpus) -> None:
    path = corpus / "matrix.json"
    matrix = json.loads(path.read_text())
    row = matrix["rows"][0]
    row["final_conclusion"] = "accepted-live"
    row["observations"].append(
        {
            "evidence_id": "test-live-evidence",
            "tier": 1,
            "evidence_class": "accepted-live-contract-and-executable-fixture",
            "source_id": "test-live-source",
            "source": row["observations"][-1]["fixture_path"],
            "revision_or_version": "test-live-revision",
            "date": "2026-07-23",
            "claim": "Synthetic validator test only.",
            "reviewer_decision": "accepted",
            "fixture_path": row["observations"][-1]["fixture_path"],
            "fixture_sha256": row["observations"][-1]["fixture_sha256"],
            "contradicts": [],
        }
    )
    path.write_text(json.dumps(matrix))
    with pytest.raises(MatrixError, match="independent review"):
        _validate(path)


def test_offline_fixture_and_bogus_headers_cannot_open_row(corpus) -> None:
    path = corpus / "matrix.json"
    matrix = json.loads(path.read_text())
    row = next(
        candidate
        for candidate in matrix["rows"]
        if candidate["final_conclusion"] == "blocked-live-evidence"
    )
    offline = row["observations"][-1]
    row.update(
        {
            "final_conclusion": "accepted-live",
            "reviewer_status": "accepted-independent-review",
            "reviewed_by": ["independent-runtime-reviewer"],
            "reviewed_at": "2026-07-23",
            "final_selected_header_names": ["Bogus-Header"],
        }
    )
    row["evidence_context"].update(
        {
            "server_revision": "synthetic-revision",
            "account_tier": "developer",
            "region": "gcp-us",
            "auth_context": "non-production-classic",
        }
    )
    row["observations"].append(
        {
            "evidence_id": "test-live-evidence",
            "tier": 1,
            "evidence_class": "accepted-live-contract-and-executable-fixture",
            "source_id": "test-live-source",
            "source": offline["fixture_path"],
            "revision_or_version": "test-live-revision",
            "date": "2026-07-23",
            "claim": "Synthetic validator test only.",
            "reviewer_decision": "accepted",
            "fixture_path": offline["fixture_path"],
            "fixture_sha256": offline["fixture_sha256"],
            "contradicts": [],
        }
    )
    path.write_text(json.dumps(matrix))
    with pytest.raises(MatrixError, match="invalid live fixture"):
        _validate(path)


def test_workspace_schema_must_match_context(corpus) -> None:
    path = corpus / "matrix.json"
    matrix = json.loads(path.read_text())
    row = next(
        candidate
        for candidate in matrix["rows"]
        if candidate["context_case"] == "valid-no-workspace-context"
    )
    row["redacted_request_schema"]["workspace"] = "<workspace-id>"
    path.write_text(json.dumps(matrix))
    with pytest.raises(MatrixError, match="workspace schema mismatch"):
        _validate(path)


def test_fixture_identity_is_validated_after_hash(corpus) -> None:
    path = corpus / "matrix.json"
    matrix = json.loads(path.read_text())
    row = matrix["rows"][0]
    observation = next(
        item
        for item in row["observations"]
        if item.get("evidence_class") == "offline-synthetic-fixture"
    )
    fixture_path = corpus / observation["fixture_path"]
    fixture = json.loads(fixture_path.read_text())
    fixture["context_case"] = "wrong-workspace-context"
    encoded = (json.dumps(fixture, indent=2, sort_keys=True) + "\n").encode()
    fixture_path.write_bytes(encoded)
    observation["fixture_sha256"] = hashlib.sha256(encoded).hexdigest()
    path.write_text(json.dumps(matrix))
    with pytest.raises(MatrixError, match="fixture transcript mismatch"):
        _validate(path)


def test_duplicate_json_keys_are_rejected(tmp_path) -> None:
    path = tmp_path / "matrix.json"
    path.write_text('{"rows":[],"rows":[]}')
    with pytest.raises(MatrixError, match="duplicate JSON key"):
        validate(
            path,
            require_complete_cross_product=False,
            reject_unresolved_precedence_conflicts=True,
        )


def test_undocumented_selected_header_is_rejected(corpus) -> None:
    path = corpus / "matrix.json"
    matrix = json.loads(path.read_text())
    row = next(
        candidate
        for candidate in matrix["rows"]
        if candidate["operation"] == "current-organization"
        and candidate["context_case"] == "valid-documented-workspace-context"
    )
    row["synthetic_selected_header_names"].append("X-Tenant-Id")
    path.write_text(json.dumps(matrix))
    with pytest.raises(MatrixError, match="selected header mismatch"):
        _validate(path)


def test_security_inconsistent_fixture_is_rejected_after_rehash(corpus) -> None:
    path = corpus / "matrix.json"
    matrix = json.loads(path.read_text())
    rows = [
        row
        for row in matrix["rows"]
        if row["operation"] == "search-assistants"
        and row["context_case"] == "caller-supplied-forwarding-headers"
    ]
    observation = next(
        item
        for item in rows[0]["observations"]
        if item["evidence_class"] == "offline-synthetic-fixture"
    )
    fixture_path = corpus / observation["fixture_path"]
    fixture = json.loads(fixture_path.read_text())
    fixture["request"]["headers"]["Host"] = "<stripped>"
    fixture["result"]["network_dispatched"] = True
    fixture["result"]["provider_body_retained"] = True
    encoded = (json.dumps(fixture, indent=2, sort_keys=True) + "\n").encode()
    fixture_path.write_bytes(encoded)
    replacement_hash = hashlib.sha256(encoded).hexdigest()
    for row in rows:
        row["synthetic_selected_header_names"].append("Host")
        fixture_observation = next(
            item
            for item in row["observations"]
            if item["evidence_class"] == "offline-synthetic-fixture"
        )
        fixture_observation["fixture_sha256"] = replacement_hash
    path.write_text(json.dumps(matrix))
    with pytest.raises(MatrixError, match="selected header mismatch"):
        _validate(path)


def test_unknown_conclusion_and_missing_observation_provenance_are_rejected(
    corpus,
) -> None:
    path = corpus / "matrix.json"
    matrix = json.loads(path.read_text())
    row = next(
        candidate
        for candidate in matrix["rows"]
        if candidate["final_conclusion"] == "blocked-live-evidence"
    )
    row["final_conclusion"] = "unknown"
    row["observations"][0].pop("source_id")
    path.write_text(json.dumps(matrix))
    with pytest.raises(MatrixError, match="observation schema"):
        _validate(path)
