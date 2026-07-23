"""Validate the immutable, review-only attestation commit."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from .common import ValidationError, require


REVIEW_PATH = "docs/references/research/research-writing-outcomes/review.json"
MATRIX_PATH = "docs/references/research/research-writing-outcomes/matrix.json"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    ).stdout.strip()


def _git_json(commit: str, path: str) -> dict:
    try:
        return json.loads(_git("show", f"{commit}:{path}"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"committed JSON invalid at {commit}:{path}") from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("review")
    parser.add_argument("--attestation-commit", required=True)
    parser.add_argument("--require-review-only-parent", action="store_true")
    parser.add_argument("--require-roles", nargs="+", required=True)
    args = parser.parse_args()
    try:
        require(args.require_review_only_parent, "review-only parent enforcement required")
        require(Path(args.review).name == "review.json", "review path drifted")
        attestation = _git("rev-parse", args.attestation_commit)
        parent = _git("rev-parse", f"{attestation}^")
        review = _git_json(attestation, REVIEW_PATH)
        matrix = _git_json(parent, MATRIX_PATH)
        require(review.get("schema_version") == "dw.review-attestation.v1", "review schema drifted")
        self_reference = review.get("attestation_commit")
        require(
            self_reference
            == {
                "derived_from_cli_argument": True,
                "self_reference_omitted": True,
            },
            "attestation derivation marker invalid",
        )
        require(review.get("candidate_commit") == parent, "candidate is not attestation parent")
        candidate_tree = _git("rev-parse", f"{parent}^{{tree}}")
        require(review.get("candidate_tree") == candidate_tree, "candidate tree mismatch")
        changed = _git("diff-tree", "--no-commit-id", "--name-only", "-r", attestation).splitlines()
        require(changed == [REVIEW_PATH], f"attestation changed non-review paths: {changed}")
        author_email = _git("show", "-s", "--format=%ae", parent)
        attestation_author_email = _git("show", "-s", "--format=%ae", attestation)
        candidate_time = int(_git("show", "-s", "--format=%ct", parent))
        attestation_time = int(_git("show", "-s", "--format=%ct", attestation))
        require(attestation_time >= candidate_time, "attestation predates candidate")
        reviewers = review.get("reviewers", [])
        roles = [item.get("role") for item in reviewers]
        identities = [item.get("reviewer_id") for item in reviewers]
        require(sorted(roles) == sorted(args.require_roles), "review roles incomplete")
        require(len(set(identities)) == len(identities) == len(roles), "reviewers must be distinct")
        require(all(item.get("verdict") == "accepted" for item in reviewers), "non-final review verdict")
        require(all(item.get("reviewer_email") != author_email for item in reviewers), "author self-review forbidden")
        require(
            attestation_author_email in {item.get("reviewer_email") for item in reviewers},
            "attestation author is not a recorded reviewer",
        )
        require(all(item.get("reviewed_commit") == parent for item in reviewers), "reviewed candidate mismatch")
        require(all(item.get("reviewed_tree") == candidate_tree for item in reviewers), "reviewed tree mismatch")
        require(all(item.get("reviewed_commands") for item in reviewers), "reviewed commands missing")
        require(review.get("all_findings_resolved") is True, "findings remain unresolved")
        finding_resolutions = review.get("finding_resolutions")
        require(isinstance(finding_resolutions, list) and finding_resolutions, "finding resolutions missing")
        finding_ids: set[str] = set()
        for finding in finding_resolutions:
            finding_id = finding.get("finding_id")
            require(isinstance(finding_id, str) and finding_id, "finding id missing")
            require(finding_id not in finding_ids, f"duplicate finding resolution: {finding_id}")
            finding_ids.add(finding_id)
            require(
                finding.get("source_review_role") in set(args.require_roles),
                f"finding review role invalid: {finding_id}",
            )
            require(finding.get("status") == "resolved", f"finding unresolved: {finding_id}")
            require(
                finding.get("resolved_in_candidate") == parent,
                f"finding candidate mismatch: {finding_id}",
            )
            require(isinstance(finding.get("resolution"), str) and finding["resolution"], f"finding resolution missing: {finding_id}")
        expected_rows = {
            row["row_id"]: row["result"] for row in matrix.get("rows", [])
        }
        require(
            review.get("row_dispositions") == expected_rows,
            "per-row dispositions incomplete or drifted",
        )
        dispositions = review.get("spike_dispositions", {})
        require(
            set(dispositions)
            == {"SPIKE-ARTIFACT-001", "SPIKE-SUBAGENT-001", "SPIKE-RUBRIC-001", "SPIKE-VERIFICATION-001"},
            "spike dispositions incomplete",
        )
        require(
            all(value in {"accepted-deterministic-normalization", "blocked-live-evidence", "blocked-package-index-evidence"} for value in dispositions.values()),
            "invalid spike disposition",
        )
    except (OSError, subprocess.SubprocessError, ValidationError) as exc:
        print(f"review validation failed: {exc}")
        return 1
    print("review attestation validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
