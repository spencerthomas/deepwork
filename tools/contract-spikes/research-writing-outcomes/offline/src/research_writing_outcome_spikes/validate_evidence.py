"""Validate retained versions, command statuses, hashes, and scrub freshness."""

from __future__ import annotations

import argparse
from pathlib import Path

from .common import BLOCKED_UPSTREAM, ValidationError, load_json, require, sha256_file
from .hash_evidence import EXCLUDED, collect


REQUIRED_FILES = {
    "matrix.json",
    "report.md",
    "versions.json",
    "commands.txt",
    "scrub-report.json",
    "index-status.json",
    "hashes.json",
    "schemas/artifact.schema.json",
    "schemas/subagent.schema.json",
    "schemas/rubric.schema.json",
    "schemas/verdict.schema.json",
    "schemas/cross-reference.schema.json",
    "fixtures/research-transcript.json",
    "fixtures/writing-transcript.json",
    "fixtures/coding-negative-transcript.json",
    "fixtures/artifact-manifest.json",
    "fixtures/subagent-events.json",
    "fixtures/rubric-history.json",
    "fixtures/verdict-history.json",
    "fixtures/expected-outcomes.json",
}


def validate_versions(root: Path) -> None:
    value = load_json(root / "versions.json")
    require(value.get("schema_version") == "dw.research-writing-versions.v1", "versions schema drifted")
    offline = value.get("offline_project", {})
    require(offline.get("dependencies") == [], "offline project gained dependencies")
    require(offline.get("test_runner") == "stdlib-unittest", "offline runner drifted")
    require(offline.get("network_policy") == "globally-denied-in-tests", "network policy drifted")
    public = value.get("installed_public", {})
    require(public.get("state") == "blocked-package-index-evidence", "public evidence state drifted")
    require(public.get("versions") is None and public.get("file_hashes") is None, "unapproved package pins present")
    require(value.get("e2e_ids_credited") == [], "E2E credit forbidden")
    require(value.get("excluded_acceptance_ids") == ["AC-DW-TASK-005-04"], "exclusion drifted")
    for spike in BLOCKED_UPSTREAM:
        require(
            value.get("upstream_artifacts", {}).get(spike, {}).get("state")
            == "blocked-live-evidence",
            f"upstream state drifted: {spike}",
        )


def validate_commands(root: Path) -> None:
    lines = [
        line for line in (root / "commands.txt").read_text().splitlines()
        if line and not line.startswith("#")
    ]
    require(lines, "commands.txt is empty")
    for line in lines:
        status, separator, command = line.partition("\t")
        require(separator == "\t" and command, f"invalid command record: {line}")
        require(status == "0", f"nonzero or missing command status: {line}")
        forbidden = ("env ", "printenv", "set ", "approved-public-index", "installed-public --frozen pytest", "--live-profile")
        require(not any(value in command for value in forbidden), f"forbidden command recorded: {command}")


def validate_hashes(root: Path) -> None:
    manifest = load_json(root / "hashes.json")
    require(manifest.get("schema_version") == "dw.evidence-hashes.v1", "hash schema drifted")
    require(set(manifest.get("excluded", [])) == EXCLUDED, "hash exclusions drifted")
    actual = collect(root)
    require(manifest.get("files") == actual, "retained evidence hash closure drifted")
    require(REQUIRED_FILES - {"hashes.json"} <= set(actual), "required retained files missing from closure")
    fixture_paths = {
        path.relative_to(root).as_posix()
        for path in (root / "fixtures").rglob("*")
        if path.is_file()
    }
    require(fixture_paths <= set(actual), "fixture missing from hash closure")


def validate_scrub(root: Path) -> None:
    report_path = root / "scrub-report.json"
    report = load_json(report_path)
    require(report.get("schema_version") == "dw.scrub-report.v1", "scrub schema drifted")
    require(report.get("finding_count") == 0 and report.get("findings") == [], "scrub findings remain")
    covered = [
        path for path in root.rglob("*")
        if path.is_file() and path.name not in {"scrub-report.json", "hashes.json", "review.json"}
    ]
    current_max = max(path.stat().st_mtime_ns for path in covered)
    require(report.get("covered_max_mtime_ns") == current_max, "scrub report does not cover latest evidence")
    require(report_path.stat().st_mtime_ns >= current_max, "scrub report is stale")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    parser.add_argument("--require-command-statuses", action="store_true")
    parser.add_argument("--require-fixture-hash-closure", action="store_true")
    parser.add_argument("--require-fresh-scrub", action="store_true")
    args = parser.parse_args()
    root = Path(args.root)
    try:
        missing = [path for path in REQUIRED_FILES if not (root / path).is_file()]
        require(not missing, f"required evidence missing: {sorted(missing)}")
        validate_versions(root)
        validate_commands(root)
        validate_scrub(root)
        validate_hashes(root)
        index = load_json(root / "index-status.json")
        require(index.get("state") == "blocked-package-index-evidence", "index status must fail closed")
        require(index.get("network_request_performed") is False, "no-index preflight made a request")
        require(index.get("permitted_validation_path") == "offline-no-index-only", "validation path drifted")
        for schema_path in sorted((root / "schemas").glob("*.json")):
            schema = load_json(schema_path)
            require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", f"schema draft drifted: {schema_path.name}")
            require(schema.get("additionalProperties") is False, f"schema not closed: {schema_path.name}")
    except (OSError, ValidationError) as exc:
        print(f"evidence validation failed: {exc}")
        return 1
    print("evidence validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
