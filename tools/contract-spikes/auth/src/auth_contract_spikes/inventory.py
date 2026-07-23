"""Record dependency and evidence inventory without reading environment values."""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .catalog import COLLECTED_AT


def _version(distribution: str) -> str | None:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return None


def build_inventory() -> dict[str, object]:
    modules = {}
    for module in ("langsmith", "langgraph_sdk"):
        spec = importlib.util.find_spec(module)
        modules[module] = {
            "installed": spec is not None,
            "generated_schema_available": bool(
                spec and module == "langgraph_sdk"
            ),
        }
    return {
        "schema_version": 1,
        "collection_date": COLLECTED_AT,
        "interpreter": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "major_minor": f"{sys.version_info.major}.{sys.version_info.minor}",
        },
        "packages": {
            "auth-contract-spikes": _version("auth-contract-spikes"),
            "langgraph-sdk": _version("langgraph-sdk"),
            "langsmith": _version("langsmith"),
            "pytest": _version("pytest"),
        },
        "installed_module_inventory": modules,
        "pinned_sources": {
            "SRC-LC": "7b9215d708e0b57e6fbae7b5d0762c4118b8e309",
            "SRC-LCPY": "592055e15e138f5369dce95dd049ce22430996e2",
            "SRC-LG": "31f90df3e6b0268fa77fd2d118a917d420b84a68",
        },
        "server_revision": None,
        "account_tier": None,
        "region": None,
        "live_profile": "blocked-live-evidence",
        "environment_values_read": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build_inventory(), indent=2, sort_keys=True) + "\n")
    print(f"inventory-written:{args.output}")


if __name__ == "__main__":
    main()
