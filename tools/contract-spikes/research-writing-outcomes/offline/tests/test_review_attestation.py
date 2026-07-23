from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from support import OfflineTestCase


REVIEW_PATH = Path("docs/references/research/research-writing-outcomes/review.json")
MATRIX_PATH = Path("docs/references/research/research-writing-outcomes/matrix.json")


def git(root: Path, *args: str, author: str = "candidate@example.invalid") -> str:
    return subprocess.run(
        [
            "git",
            "-c",
            "user.name=Contract Test",
            "-c",
            f"user.email={author}",
            *args,
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


class ReviewAttestationTests(OfflineTestCase):
    def test_validator_reads_committed_blob_and_binds_reviewer_author(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            git(root, "init")
            (root / MATRIX_PATH.parent).mkdir(parents=True)
            matrix = {
                "rows": [
                    {
                        "row_id": "verification-001",
                        "result": "accepted-deterministic-normalization",
                    }
                ]
            }
            (root / MATRIX_PATH).write_text(json.dumps(matrix))
            git(root, "add", str(MATRIX_PATH))
            git(root, "commit", "-m", "candidate")
            candidate = git(root, "rev-parse", "HEAD")
            tree = git(root, "rev-parse", "HEAD^{tree}")
            reviewers = [
                {
                    "role": role,
                    "reviewer_id": f"/root/{role}",
                    "reviewer_email": f"{role}@review.invalid",
                    "verdict": "accepted",
                    "reviewed_commit": candidate,
                    "reviewed_tree": tree,
                    "reviewed_commands": ["offline tests: exit 0"],
                }
                for role in ("runtime-contracts", "security", "product")
            ]
            review = {
                "schema_version": "dw.review-attestation.v1",
                "attestation_commit": {
                    "derived_from_cli_argument": True,
                    "self_reference_omitted": True,
                },
                "candidate_commit": candidate,
                "candidate_tree": tree,
                "reviewers": reviewers,
                "all_findings_resolved": True,
                "finding_resolutions": [
                    {
                        "finding_id": "test-finding",
                        "source_review_role": "security",
                        "status": "resolved",
                        "resolved_in_candidate": candidate,
                        "resolution": "Synthetic resolution.",
                    }
                ],
                "row_dispositions": {
                    "verification-001": "accepted-deterministic-normalization"
                },
                "spike_dispositions": {
                    "SPIKE-ARTIFACT-001": "blocked-live-evidence",
                    "SPIKE-SUBAGENT-001": "blocked-package-index-evidence",
                    "SPIKE-RUBRIC-001": "blocked-package-index-evidence",
                    "SPIKE-VERIFICATION-001": "accepted-deterministic-normalization",
                },
            }
            (root / REVIEW_PATH).write_text(json.dumps(review))
            git(root, "add", str(REVIEW_PATH))
            git(
                root,
                "commit",
                "-m",
                "review",
                author="security@review.invalid",
            )
            attestation = git(root, "rev-parse", "HEAD")
            # Dirty working-tree data must not influence committed validation.
            (root / REVIEW_PATH).write_text('{"schema_version":"forged"}')
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "research_writing_outcome_spikes.validate_review",
                    str(REVIEW_PATH),
                    "--attestation-commit",
                    attestation,
                    "--require-review-only-parent",
                    "--require-roles",
                    "runtime-contracts",
                    "security",
                    "product",
                ],
                cwd=root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
