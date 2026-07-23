"""Fail-closed package-index preflight for the research/writing contract spike."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


PUBLIC_SIMPLE_INDEX = "https://pypi.org/simple/deepagents/"
APPROVAL_ARTIFACT = Path(
    "docs/references/program/package-index-approvals/research-writing-outcomes.json"
)


def _reviewed_approval() -> tuple[bool, str | None, str | None]:
    """Accept only a separately owned, committed coordinator approval artifact."""
    try:
        committed = subprocess.run(
            ["git", "show", f"HEAD:{APPROVAL_ARTIFACT}"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout
        approval = json.loads(committed)
        approval_commit = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--", str(APPROVAL_ARTIFACT)],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        approved = (
            len(approval_commit) == 40
            and approval.get("schema_version") == "dw.package-index-approval.v1"
            and approval.get("approved") is True
            and approval.get("scope") == "research-writing-outcomes-installed-public"
            and approval.get("packages") == ["deepagents", "pytest"]
            and isinstance(approval.get("reviewer_id"), str)
            and approval["reviewer_id"]
        )
        return approved, approval_commit or None, None if approved else "approval-artifact-invalid"
    except (OSError, json.JSONDecodeError, subprocess.SubprocessError):
        return False, None, "approval-artifact-absent-or-invalid"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        required=True,
        choices=("no-index", "approved-public-index"),
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    approval_present, approval_commit, approval_failure = (
        _reviewed_approval()
        if args.mode == "approved-public-index"
        else (False, None, None)
    )
    request_performed = False
    reachable = False
    failure = None
    if approval_present:
        request_performed = True
        try:
            request = Request(PUBLIC_SIMPLE_INDEX, method="HEAD")
            with urlopen(request, timeout=10) as response:
                reachable = response.status == 200
        except (OSError, URLError) as exc:
            failure = type(exc).__name__
    approved = approval_present and reachable
    result = {
        "schema_version": "dw.index-preflight.v1",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "network_request_performed": request_performed,
        "approved": approved,
        "state": (
            "approved-package-index-evidence"
            if approved
            else "blocked-package-index-evidence"
        ),
        "permitted_validation_path": (
            "installed-public"
            if approved
            else "offline-no-index-only"
        ),
        "reason": (
            "Reviewer approval was present and the public package index was reachable."
            if approved
            else (
                "Reviewer approval was present but the public package index was unreachable."
                if approval_present
                else "No reviewer-approved public package-index access was supplied."
            )
        ),
        "failure_class": failure,
        "approval_artifact": str(APPROVAL_ARTIFACT),
        "approval_commit": approval_commit,
        "approval_failure": approval_failure,
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0 if args.mode == "no-index" or approved else 2


if __name__ == "__main__":
    raise SystemExit(main())
