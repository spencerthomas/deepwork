"""Build the immutable retained-evidence hash closure."""

from __future__ import annotations

import argparse
from pathlib import Path

from .common import dump_json, sha256_file


EXCLUDED = {"hashes.json", "review.json"}


def collect(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name not in EXCLUDED
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.root)
    files = collect(root)
    dump_json(
        Path(args.output),
        {
            "schema_version": "dw.evidence-hashes.v1",
            "algorithm": "sha256",
            "excluded": sorted(EXCLUDED),
            "files": files,
        },
    )
    print(f"hashed {len(files)} retained evidence files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
