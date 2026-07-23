from __future__ import annotations

import json

import pytest

from plan_approval_contract_spikes.catalog import SCENARIOS, TEMPLATES
from plan_approval_contract_spikes.errors import ContractViolation
from plan_approval_contract_spikes.generate_evidence import build_evidence
from plan_approval_contract_spikes.scrub import scan
from plan_approval_contract_spikes.validate_matrix import validate


def test_generated_matrix_and_fixture_hashes_validate(tmp_path):
    matrix = build_evidence(tmp_path)
    assert len(matrix["rows"]) == len(TEMPLATES) * len(SCENARIOS)
    validate(
        matrix,
        require_complete_cross_product=True,
        reject_blocked_dependency_promotion=True,
        reject_unresolved_precedence_conflicts=True,
        evidence_root=tmp_path,
    )


def test_validator_rejects_target_acceptance(tmp_path):
    matrix = build_evidence(tmp_path)
    matrix["target_spikes"][0]["status"] = "accepted"
    with pytest.raises(ContractViolation, match="must remain unaccepted"):
        validate(
            matrix,
            require_complete_cross_product=True,
            reject_blocked_dependency_promotion=True,
            reject_unresolved_precedence_conflicts=True,
            evidence_root=tmp_path,
        )


def test_validator_rejects_permission_widening_claim(tmp_path):
    matrix = build_evidence(tmp_path)
    row = next(
        item for item in matrix["rows"] if item["scenario"] == "permission_widening"
    )
    row["observed_result"] = "approved"
    with pytest.raises(ContractViolation, match="did not fail closed"):
        validate(
            matrix,
            require_complete_cross_product=True,
            reject_blocked_dependency_promotion=True,
            reject_unresolved_precedence_conflicts=True,
            evidence_root=tmp_path,
        )


def test_scrubber_rejects_sensitive_patterns(tmp_path):
    (tmp_path / "bad.json").write_text(
        json.dumps({"authorization": "Bearer synthetic-but-reusable-token"}),
        encoding="utf-8",
    )
    report = scan(tmp_path)
    assert report["status"] == "rejected"
    assert report["finding_count"] == 1
