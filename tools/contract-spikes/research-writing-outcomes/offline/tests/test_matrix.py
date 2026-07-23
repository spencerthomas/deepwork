from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from research_writing_outcome_spikes.common import ValidationError, load_json
from research_writing_outcome_spikes.validate_evidence import validate_commands
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
        validate_matrix(
            self.matrix,
            installed_public_blocked=True,
            evidence_root=MATRIX.parent,
        )

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

    def test_blocked_matrix_cannot_pass_installed_public_conformance(self) -> None:
        with self.assertRaisesRegex(ValidationError, "conformance result missing"):
            validate_matrix(
                self.matrix,
                installed_public_blocked=False,
                evidence_root=MATRIX.parent,
            )

    def test_fabricated_installed_public_conformance_fails_closed(self) -> None:
        mutated = deepcopy(self.matrix)
        mutated["installed_public"] = {
            "state": "accepted-installed-public-conformance",
            "lock_created": True,
            "commands_run": True,
            "lock_sha256": "z" * 64,
            "distribution_pins": [
                {"name": "unrelated", "version": "0", "sha256": "z" * 64}
            ],
            "export_observations": [],
        }
        with self.assertRaisesRegex(ValidationError, "required installed-public pins"):
            validate_matrix(
                mutated,
                installed_public_blocked=False,
                evidence_root=MATRIX.parent,
            )

        mutated["installed_public"] = {
            "state": "accepted-installed-public-conformance",
            "lock_created": True,
            "commands_run": True,
            "lock_sha256": "a" * 64,
            "distribution_pins": [
                {"name": "deepagents", "version": "1.2.3", "sha256": "b" * 64},
                {"name": "pytest", "version": "9.0.1", "sha256": "c" * 64},
            ],
            "export_observations": [
                {
                    "export": export,
                    "state": "passed",
                    "fake_model": "deterministic",
                    "provider_network": False,
                }
                for export in (
                    "create_deep_agent",
                    "RubricMiddleware",
                    "SubAgent",
                    "SubAgentMiddleware",
                )
            ],
        }
        with self.assertRaisesRegex(ValidationError, "lock path invalid"):
            validate_matrix(
                mutated,
                installed_public_blocked=False,
                evidence_root=MATRIX.parent,
            )

    def test_substitution_requires_changed_presented_value(self) -> None:
        mutated = deepcopy(self.matrix)
        row = next(item for item in mutated["rows"] if item["case"] == "substitution")
        row["presented_value"] = row["expected_value"]
        with self.assertRaisesRegex(ValidationError, "did not change"):
            validate_matrix(
                mutated,
                installed_public_blocked=True,
                evidence_root=MATRIX.parent,
            )
        del row["presented_value"]
        with self.assertRaisesRegex(ValidationError, "presented binding missing"):
            validate_matrix(
                mutated,
                installed_public_blocked=True,
                evidence_root=MATRIX.parent,
            )

    def test_stream_specific_substitution_target_is_fixture_bound(self) -> None:
        mutated = deepcopy(self.matrix)
        row = next(
            item for item in mutated["rows"]
            if item.get("substitution_dimension") == "artifact_id"
        )
        row["expected_value"] = "invented-artifact"
        with self.assertRaisesRegex(ValidationError, "stream-specific"):
            validate_matrix(
                mutated,
                installed_public_blocked=True,
                evidence_root=MATRIX.parent,
            )

    def test_evidence_path_hash_and_stream_are_bound(self) -> None:
        for field, value, message in (
            ("path", "../../../../etc/passwd", "unsafe evidence path"),
            ("content_sha256", "0" * 64, "evidence hash mismatch"),
            ("owner_stream", "artifact", "cross-stream evidence substitution"),
        ):
            mutated = deepcopy(self.matrix)
            evidence = next(
                item for item in mutated["evidence"]
                if item["owner_stream"] == "verification"
            )
            evidence[field] = value
            with self.assertRaisesRegex(ValidationError, message):
                validate_matrix(
                    mutated,
                    installed_public_blocked=True,
                    evidence_root=MATRIX.parent,
                )

    def test_incomplete_command_record_fails_closed(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "commands.txt").write_text("0\ttrue\n")
            with self.assertRaisesRegex(ValidationError, "count drifted"):
                validate_commands(root)
