"""Validate the immutable, review-only attestation commit."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from .common import ValidationError, load_json, require


REVIEW_PATH = "docs/references/research/research-writing-outcomes/review.json"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("review")
    parser.add_argument("--attestation-commit", required=True)
    parser.add_argument("--require-review-only-parent", action="store_true")
    parser.add_argument("--require-roles", nargs="+", required=True)
    args = parser.parse_args()
    try:
        review = load_json(Path(args.review))
        require(review.get("schema_version") == "dw.review-attestation.v1", "review schema drifted")
        attestation = _git("rev-parse", args.attestation_commit)
        parent = _git("rev-parse", f"{attestation}^")
        require(review.get("attestation_commit") == attestation, "attestation SHA mismatch")
        require(review.get("candidate_commit") == parent, "candidate is not attestation parent")
        candidate_tree = _git("rev-parse", f"{parent}^{{tree}}")
        require(review.get("candidate_tree") == candidate_tree, "candidate tree mismatch")
        changed = _git("diff-tree", "--no-commit-id", "--name-only", "-r", attestation).splitlines()
        require(changed == [REVIEW_PATH], f"attestation changed non-review paths: {changed}")
        author_email = _git("show", "-s", "--format=%ae", parent)
        reviewers = review.get("reviewers", [])
        roles = [item.get("role") for item in reviewers]
        identities = [item.get("reviewer_id") for item in reviewers]
        require(sorted(roles) == sorted(args.require_roles), "review roles incomplete")
        require(len(set(identities)) == len(identities) == len(roles), "reviewers must be distinct")
        require(all(item.get("verdict") == "accepted" for item in reviewers), "non-final review verdict")
        require(all(item.get("reviewer_email") != author_email for item in reviewers), "author self-review forbidden")
        require(all(item.get("reviewed_commit") == parent for item in reviewers), "reviewed candidate mismatch")
        require(all(item.get("reviewed_tree") == candidate_tree for item in reviewers), "reviewed tree mismatch")
        require(all(item.get("reviewed_commands") for item in reviewers), "reviewed commands missing")
        require(review.get("all_findings_resolved") is True, "findings remain unresolved")
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
