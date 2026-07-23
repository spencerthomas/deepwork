from __future__ import annotations

from pathlib import Path

from research_writing_outcome_spikes.common import load_json
from research_writing_outcome_spikes.scrub import PATTERNS

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

    def test_scrubber_detects_each_claimed_sensitive_category(self) -> None:
        samples = {
            "credential_assignment": "api_key = abcdefghijklmnop",
            "unlabelled_secret": "sk-proj-abcdefghijklmnop",
            "authorization_header": "Authorization: Bearer value",
            "raw_header": "Cookie: session=value",
            "private_key": "-----BEGIN PRIVATE KEY-----",
            "hidden_reasoning": "hidden_reasoning: do not retain",
            "unsafe_html": "<script>alert(1)</script>",
            "absolute_user_path": "/home/person/private/file",
            "reusable_endpoint": "https://service.test/signed/object?token=value",
            "customer_data": "customer_email: person@test.invalid",
        }
        self.assertEqual(set(PATTERNS), set(samples))
        for category, sample in samples.items():
            self.assertIsNotNone(PATTERNS[category].search(sample), category)
