#!/usr/bin/env python3
"""Fail closed on Deep Work OSS license, attribution, and trademark drift."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

MIT_MARKERS = (
    "MIT License",
    "Permission is hereby granted, free of charge",
    'THE SOFTWARE IS PROVIDED "AS IS"',
)
README_MARKERS = {
    "attribution": "Portions Copyright (c) LangChain, Inc.",
    "non-affiliation": "not affiliated with, endorsed by, or sponsored by LangChain, Inc.",
    "runtime-license": "Elastic License 2.0",
    "runtime-boundary": "never vendors or redistributes langgraph-api",
}
REQUIRED_COMMUNITY_FILES = (
    "LICENSE",
    "README.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
)
IGNORED_PARTS = {
    ".git",
    ".next",
    ".pnpm-store",
    ".turbo",
    ".venv",
    "build",
    "dist",
    "node_modules",
    "output",
}
ASSET_EXTENSIONS = {".eot", ".gif", ".jpeg", ".jpg", ".otf", ".png", ".svg", ".ttf", ".webp", ".woff", ".woff2"}
RESTRICTED_FONT_NAMES = ("aeonik", "lausanne", "twk")
RESTRICTED_MARK_ASSET_NAMES = ("langchain", "langsmith")
ACTION_REFERENCE = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)@([^\s#]+)", re.MULTILINE)
FULL_COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    message: str


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _source_files(root: Path) -> list[Path]:
    if (root / ".git").exists():
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            check=True,
            capture_output=True,
        )
        return sorted(root / relative.decode("utf-8") for relative in result.stdout.split(b"\0") if relative)
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and not any(part in IGNORED_PARTS for part in path.relative_to(root).parts)
    )


def _finding(code: str, path: Path | str, message: str, root: Path) -> Finding:
    if isinstance(path, Path):
        try:
            rendered = path.relative_to(root).as_posix()
        except ValueError:
            rendered = path.as_posix()
    else:
        rendered = path
    return Finding(code=code, path=rendered, message=message)


def audit(root: Path) -> tuple[list[Finding], dict[str, object]]:
    root = root.resolve()
    findings: list[Finding] = []

    for relative in REQUIRED_COMMUNITY_FILES:
        path = root / relative
        if not path.is_file():
            findings.append(_finding("missing-community-file", path, "required OSS community file is missing", root))

    license_path = root / "LICENSE"
    license_text = _read(license_path)
    for marker in MIT_MARKERS:
        if marker not in license_text:
            findings.append(_finding("invalid-root-license", license_path, f"missing MIT marker: {marker}", root))

    readme_path = root / "README.md"
    readme_text = _read(readme_path)
    readme_text_folded = " ".join(readme_text.casefold().split())
    for label, marker in README_MARKERS.items():
        normalized_marker = " ".join(marker.casefold().split())
        if normalized_marker not in readme_text_folded:
            findings.append(_finding("missing-readme-boundary", readme_path, f"missing {label} statement: {marker}", root))

    manifest_paths = sorted((root / "apps").glob("*/package.json")) + sorted((root / "packages").glob("*/package.json"))
    for path in [root / "package.json", *manifest_paths]:
        if not path.is_file():
            continue
        try:
            manifest = json.loads(_read(path))
        except json.JSONDecodeError as error:
            findings.append(_finding("invalid-package-manifest", path, str(error), root))
            continue
        if manifest.get("license") != "MIT":
            findings.append(_finding("missing-package-license", path, 'package manifest must declare "license": "MIT"', root))
        name = manifest.get("name")
        if not isinstance(name, str) or name.casefold().startswith(("langchain", "langsmith", "@langchain", "@langsmith")):
            findings.append(_finding("restricted-package-name", path, "package name must use Deep Work ownership, not a provider mark", root))

    pyproject_paths = sorted((root / "apps").glob("*/pyproject.toml")) + sorted((root / "packages").glob("*/pyproject.toml"))
    for path in pyproject_paths:
        text = _read(path)
        if not re.search(r"(?m)^license\s*=\s*(?:\{\s*text\s*=\s*)?[\"']MIT[\"']", text):
            findings.append(_finding("missing-python-license", path, "Python project must declare its MIT license", root))
        name_match = re.search(r"(?m)^name\s*=\s*[\"']([^\"']+)[\"']", text)
        if not name_match or name_match.group(1).casefold().startswith(("langchain", "langsmith")):
            findings.append(_finding("restricted-python-name", path, "Python project name must use Deep Work ownership, not a provider mark", root))

    source_files = _source_files(root)
    for path in source_files:
        suffix = path.suffix.casefold()
        name = path.name.casefold()
        if suffix in {".eot", ".otf", ".ttf", ".woff", ".woff2"} and any(value in name for value in RESTRICTED_FONT_NAMES):
            findings.append(_finding("restricted-font-asset", path, "commercial font asset name is forbidden", root))
        if suffix in ASSET_EXTENSIONS and any(value in name for value in RESTRICTED_MARK_ASSET_NAMES):
            findings.append(_finding("restricted-provider-asset", path, "provider wordmark/logo asset name is forbidden", root))

    workflow_paths = sorted((root / ".github" / "workflows").glob("*.y*ml"))
    action_references = 0
    for path in workflow_paths:
        for match in ACTION_REFERENCE.finditer(_read(path)):
            action_references += 1
            action, reference = match.groups()
            if action.startswith("./"):
                continue
            if not FULL_COMMIT_SHA.fullmatch(reference):
                findings.append(_finding("unpinned-action", path, f"{action}@{reference} must use a full 40-character commit SHA", root))

    report = {
        "schemaVersion": 1,
        "status": "pass" if not findings else "fail",
        "rootLicense": "MIT" if not any(item.code == "invalid-root-license" for item in findings) else "invalid",
        "communityFilesChecked": len(REQUIRED_COMMUNITY_FILES),
        "packageManifestsChecked": len(manifest_paths) + int((root / "package.json").is_file()),
        "pythonProjectsChecked": len(pyproject_paths),
        "sourceFilesChecked": len(source_files),
        "actionReferencesChecked": action_references,
        "findings": [asdict(item) for item in findings],
    }
    return findings, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    findings, report = audit(args.root)

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if findings:
        for item in findings:
            print(f"{item.code}: {item.path}: {item.message}", file=sys.stderr)
        return 1
    print(
        "OSS audit passed: "
        f"{report['packageManifestsChecked']} package manifests, "
        f"{report['pythonProjectsChecked']} Python projects, "
        f"{report['actionReferencesChecked']} action references, "
        f"{report['sourceFilesChecked']} source files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
