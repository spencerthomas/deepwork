"""Write sanitized runtime and contract version inventory."""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path
import subprocess

from coding_github_spikes import __version__


def safe_version(command: list[str]) -> str:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    value = {
        "observed_at": "2026-07-23",
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "git": safe_version(["git", "--version"]),
        "uv": safe_version(["uv", "--version"]),
        "probe": __version__,
        "github_rest_api": "2026-03-10",
        "github_media_type": "application/vnd.github+json",
        "github_client": "stdlib deterministic fake; no credentialed SDK installed",
        "auth_class": "none-offline; GitHub App installation required for live",
        "account_tier": "not-supplied",
        "region": "not-supplied",
        "sandbox_upstream": {
            "commit": "5a518c40fb44b5d64b8eb36f618c8ecd58bad188",
            "review": "missing",
        },
        "pinned_sources": {
            "SRC-LC": "7b9215d708e0b57e6fbae7b5d0762c4118b8e309",
            "SRC-DA": "7794b61a6e76230e8c7a49bdce808b3728305914",
            "SRC-LG": "31f90df3e6b0268fa77fd2d118a917d420b84a68",
        },
        "app_permission_manifest": {
            "administration": "read",
            "actions": "read",
            "checks": "read",
            "commit_statuses": "read",
            "contents": "write",
            "metadata": "read",
            "pull_requests": "write",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
