from __future__ import annotations

import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from research_writing_outcome_spikes.common import ValidationError, load_json
from research_writing_outcome_spikes.scrub import PATTERNS
from research_writing_outcome_spikes.validate_evidence import validate_fixture_semantics

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
            "raw_header": "X-Forwarded-For: 192.0.2.1",
            "private_key": "-----BEGIN PRIVATE KEY-----",
            "hidden_reasoning": "hidden_reasoning: do not retain",
            "unsafe_html": "<script>alert(1)</script>",
            "absolute_user_path": "/home/person/private/file",
            "reusable_endpoint": "https://service.test/signed/object?token=value",
            "customer_data": '{"customer_name":"Real Customer"}',
        }
        self.assertEqual(set(PATTERNS), set(samples))
        for category, sample in samples.items():
            self.assertIsNotNone(PATTERNS[category].search(sample), category)

    def test_fixture_semantics_reject_contradictory_case_inputs(self) -> None:
        mutations = (
            ("research-transcript.json", "citation_cases", "missing", {"state": "valid"}),
            (
                "writing-transcript.json",
                "cases",
                "empty",
                {
                    "candidate_hash": "a" * 64,
                    "size_bytes": 1,
                    "artifact_state": "promoted",
                },
            ),
            (
                "coding-negative-transcript.json",
                "cases",
                "missing-tests",
                {"state": "valid", "exit_status": 0},
            ),
        )
        for filename, collection, case_name, updates in mutations:
            with self.subTest(case=case_name), TemporaryDirectory() as directory:
                root = Path(directory)
                shutil.copytree(ROOT / "fixtures", root / "fixtures")
                path = root / "fixtures" / filename
                value = json.loads(path.read_text())
                case = next(item for item in value[collection] if item["case"] == case_name)
                case.update(updates)
                path.write_text(json.dumps(value))
                with self.assertRaises(ValidationError):
                    validate_fixture_semantics(root)

    def test_subagent_declared_outcomes_must_match_raw_events(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "fixtures", root / "fixtures")
            path = root / "fixtures/subagent-events.json"
            value = json.loads(path.read_text())
            value["events"] = value["events"][:1]
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValidationError, "not derived"):
                validate_fixture_semantics(root)
