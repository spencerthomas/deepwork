"""Fail-closed package-index preflight for the research/writing contract spike."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


APPROVAL_ENV = "DW_APPROVED_PUBLIC_INDEX_PREFLIGHT"
PUBLIC_SIMPLE_INDEX = "https://pypi.org/simple/deepagents/"


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
    approval_present = (
        args.mode == "approved-public-index"
        and os.environ.get(APPROVAL_ENV) == "reviewer-approved"
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
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0 if args.mode == "no-index" or approved else 2


if __name__ == "__main__":
    raise SystemExit(main())
