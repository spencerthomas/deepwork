from __future__ import annotations

from pathlib import Path

from research_writing_outcome_spikes.common import load_json

from support import OfflineTestCase


REPO = Path(__file__).resolve().parents[5]
ROOT = REPO / "docs/references/research/research-writing-outcomes"


class RetainedEvidenceTests(OfflineTestCase):
    def test_no_index_status_is_fail_closed(self) -> None:
        status = load_json(ROOT / "index-status.json")
        self.assertEqual("blocked-package-index-evidence", status["state"])
        self.assertFalse(status["network_request_performed"])
        self.assertEqual("offline-no-index-only", status["permitted_validation_path"])

    def test_expected_outcomes_reject_generic_pass(self) -> None:
        expected = load_json(ROOT / "fixtures/expected-outcomes.json")
        self.assertTrue(expected["generic_model_pass_overridden"])
        self.assertEqual("failed", expected["coding_failed_or_missing_tests"])
        self.assertIsNone(expected["automatic_numeric_score"])

    def test_zero_e2e_credit_and_explicit_coding_exclusion(self) -> None:
        matrix = load_json(ROOT / "matrix.json")
        self.assertEqual([], matrix["e2e_ids_credited"])
        self.assertEqual(["AC-DW-TASK-005-04"], matrix["excluded_acceptance_ids"])
