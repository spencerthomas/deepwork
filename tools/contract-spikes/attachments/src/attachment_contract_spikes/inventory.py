"""Write a sanitized, source-pinned dependency and fixture inventory."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
from pathlib import Path

from attachment_contract_spikes.scope import SCOPE_RELATIVE_PATH, load_json, scope_sha256


def _version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def _uv_version() -> str:
    result = subprocess.run(
        ["uv", "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout.strip()


def fixture_hashes(fixtures_dir: Path) -> dict[str, str]:
    """Hash retained harmless fixture documents by repository-relative filename."""
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(fixtures_dir.iterdir())
        if path.is_file()
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    scope = load_json(SCOPE_RELATIVE_PATH)
    fixtures_dir = args.output.parent / "fixtures"
    payload = {
        "schema_version": "1.0",
        "collection_date": "2026-07-23",
        "python": platform.python_version(),
        "platform": platform.system().lower(),
        "uv": _uv_version(),
        "project": {
            "attachment-contract-spikes": _version("attachment-contract-spikes"),
            "pytest": _version("pytest"),
            "hatchling": _version("hatchling"),
        },
        "evidence_pins": scope["evidence_pins"],
        "scope_sha256": scope_sha256(SCOPE_RELATIVE_PATH),
        "live_dependencies": {
            "object_store": "not-supplied",
            "scanner": "not-supplied",
            "classic_runtime_server": "not-supplied",
            "account_tier": "unknown",
            "region": "unknown",
            "authentication_context": "not-supplied",
        },
        "fixture_sha256": fixture_hashes(fixtures_dir),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"wrote {args.output.as_posix()}")


if __name__ == "__main__":
    main()
