"""Write a sanitized inventory for the isolated offline probe."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path

from coding_review_surface_spikes.contracts import canonical_hash

SOURCE_PINS = {
    "SRC-LC": "7b9215d708e0b57e6fbae7b5d0762c4118b8e309",
    "SRC-DA": "7794b61a6e76230e8c7a49bdce808b3728305914",
    "SRC-LG": "31f90df3e6b0268fa77fd2d118a917d420b84a68",
}


def _version(*command: str) -> str:
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    document: dict[str, object] = {
        "schema_version": "1.0",
        "observed_at": "2026-07-23",
        "interpreter": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "executable_class": "isolated-uv-environment",
        },
        "tools": {
            "uv": _version("uv", "--version"),
            "git": _version("git", "--version"),
            "pytest_runner": _version("pytest", "--version"),
        },
        "installed_public_distributions": {},
        "probe_package": "deepwork-coding-review-surface-spikes==0.1.0",
        "source_pins": SOURCE_PINS,
        "upstream_packets": {
            "sandbox": {
                "observed_commit": "5a518c40fb44b5d64b8eb36f618c8ecd58bad188",
                "reviewed_output": "missing",
            },
            "github": {
                "observed_commit": "cb8c6eebcb01f4974709c3851119499c27818335",
                "reviewed_output": "missing",
            },
        },
        "provider": {
            "account_tier": None,
            "region": None,
            "auth_class": "none",
            "sandbox_version": None,
            "github_api_version": None,
        },
        "network_policy": "offline tests deny network; no live profile was run",
        "python_hexversion": sys.hexversion,
    }
    document["inventory_hash"] = canonical_hash(document)
    args.output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote sanitized inventory {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
