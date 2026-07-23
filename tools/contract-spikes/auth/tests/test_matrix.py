from __future__ import annotations

import json

from auth_contract_spikes.catalog import CONTEXT_CASES, KEY_CLASSES, OPERATIONS
from auth_contract_spikes.generate_matrix import build_matrix


def test_matrix_is_complete_cross_product() -> None:
    matrix = build_matrix()
    assert matrix["row_count"] == len(OPERATIONS) * len(KEY_CLASSES) * len(
        CONTEXT_CASES
    )
    assert len({row["row_id"] for row in matrix["rows"]}) == matrix["row_count"]


def test_no_row_is_self_accepted_or_claims_live_evidence() -> None:
    matrix = build_matrix()
    assert matrix["overall_conclusion"] == "blocked-live-evidence"
    assert all(row["author_acceptance"] is False for row in matrix["rows"])
    assert not any(
        row["final_conclusion"] == "accepted-live" for row in matrix["rows"]
    )


def test_matrix_serializes_without_secret_values() -> None:
    encoded = json.dumps(build_matrix())
    assert "lsv2_pt_" not in encoded
    assert "lsv2_sk_" not in encoded
    assert "Bearer " not in encoded
