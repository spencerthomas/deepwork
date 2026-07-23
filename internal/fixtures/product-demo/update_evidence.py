#!/usr/bin/env python3
"""Deterministically write or check product-demo fixture evidence."""

import argparse
import hashlib
import json
from pathlib import Path

import validate as fixture_validate


ROOT = Path(__file__).resolve().parent


def render_targets():
    analysis = fixture_validate.analyze_sources()
    return {
        "hashes.sha256": fixture_validate.render_hash_manifest(),
        "evidence/no-external-network.json": fixture_validate.render_network_report(analysis),
        "evidence/validation-report.json": fixture_validate.render_validation_report(analysis),
    }


def target_digests(targets):
    return {
        path: hashlib.sha256(content).hexdigest()
        for path, content in sorted(targets.items())
    }


def write_changed(targets):
    updated = []
    for relative_path, content in sorted(targets.items()):
        path = ROOT / relative_path
        current = path.read_bytes() if path.exists() else None
        if current == content:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.update.tmp")
        temporary.write_bytes(content)
        temporary.replace(path)
        updated.append(relative_path)
    return updated


def print_digests(targets):
    for path, digest in target_digests(targets).items():
        print(f"target_sha256 {digest}  {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()

    first = render_targets()
    if args.write:
        updated = write_changed(first)
        print_digests(first)
        print("updated_files=" + json.dumps(updated, separators=(",", ":")))
        return 0

    second = render_targets()
    render_identical = first == second
    disk_identical = all(
        (ROOT / path).exists() and (ROOT / path).read_bytes() == content
        for path, content in first.items()
    )
    print_digests(first)
    print("render_passes=2")
    print(f"render_byte_identical={str(render_identical).lower()}")
    print(f"disk_byte_identical={str(disk_identical).lower()}")
    return 0 if render_identical and disk_identical else 1


if __name__ == "__main__":
    raise SystemExit(main())
