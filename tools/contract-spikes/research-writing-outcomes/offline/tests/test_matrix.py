from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from research_writing_outcome_spikes.common import ValidationError, load_json
from research_writing_outcome_spikes.validate_matrix import validate_matrix

from support import OfflineTestCase


REPO = Path(__file__).resolve().parents[5]
MATRIX = REPO / "docs/references/research/research-writing-outcomes/matrix.json"


class MatrixTests(OfflineTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.matrix = load_json(MATRIX)

    def test_complete_retained_matrix(self) -> None:
        validate_matrix(self.matrix, installed_public_blocked=True)

    def test_each_identity_dimension_substitution_is_rejected(self) -> None:
        substitutions = {
            row["substitution_dimension"]
            for row in self.matrix["rows"]
            if row["case"] == "substitution"
        }
        for dimension in self.matrix["identity_fields"]:
            self.assertIn(dimension, substitutions)

    def test_blocked_upstream_cannot_be_promoted(self) -> None:
        mutated = deepcopy(self.matrix)
        mutated["upstream_dependencies"]["SPIKE-COMPOSE-001"]["state"] = "accepted"
        with self.assertRaisesRegex(ValidationError, "must remain blocked"):
            validate_matrix(mutated, installed_public_blocked=True)

    def test_evidence_owner_substitution_fails(self) -> None:
        mutated = deepcopy(self.matrix)
        row = next(item for item in mutated["rows"] if item["evidence_refs"])
        evidence = next(
            item for item in mutated["evidence"]
            if item["evidence_id"] == row["evidence_refs"][0]
        )
        evidence["identity"]["tenant_id"] = "wrong"
        with self.assertRaisesRegex(ValidationError, "cross-owner"):
            validate_matrix(mutated, installed_public_blocked=True)

    def test_required_failure_cannot_automatically_pass(self) -> None:
        mutated = deepcopy(self.matrix)
        row = next(
            item for item in mutated["rows"]
            if item.get("required_evidence_state") in {"fail", "missing"}
        )
        row["automatic_pass"] = True
        with self.assertRaisesRegex(ValidationError, "auto-passed"):
            validate_matrix(mutated, installed_public_blocked=True)
