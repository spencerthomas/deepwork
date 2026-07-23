#!/usr/bin/env python3
"""Generate deterministic Wave 0 documentation from canonical sources."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC_ROOT = ROOT / "docs" / "product-specs"
GENERATED = ROOT / "docs" / "generated"


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError(f"unterminated front matter: {path.relative_to(ROOT)}")
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line or line[0].isspace() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def inline_list(value: str) -> list[str]:
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        return []
    return [item.strip().strip("'\"") for item in value[1:-1].split(",") if item.strip()]


def specs() -> list[tuple[Path, dict[str, str]]]:
    found: list[tuple[Path, dict[str, str]]] = []
    for path in sorted(SPEC_ROOT.rglob("*.md")):
        data = frontmatter(path)
        if "feature_id" in data:
            found.append((path, data))
    return found


def scenario_registry() -> dict[str, list[str]]:
    text = (SPEC_ROOT / "acceptance-scenarios.md").read_text(encoding="utf-8")
    result: dict[str, list[str]] = {}
    for line in text.splitlines():
        if not line.startswith("| DW-") or "AC-DW-" not in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        feature_id = cells[0]
        result[feature_id] = list(dict.fromkeys(re.findall(r"AC-[A-Z0-9-]+", line)))
    return result


def generated_header(source: str) -> str:
    return (
        "<!-- GENERATED: do not edit by hand. -->\n"
        f"<!-- Source: {source}; command: python3 tools/docs/generate.py --write -->\n\n"
    )


def feature_coverage() -> str:
    registry = scenario_registry()
    rows = []
    for path, data in specs():
        feature_id = data["feature_id"]
        rel = path.relative_to(ROOT / "docs").as_posix()
        rows.append(
            f"| {feature_id} | {data.get('release', '')} | {data.get('status', '')} | "
            f"{len(registry.get(feature_id, []))} | [spec](../{rel}) |"
        )
    return generated_header("docs/product-specs metadata and acceptance-scenarios.md") + """# Feature coverage

This view indexes stable ownership and scenario counts. Readiness remains governed
by each spec's contract gates and the decision register.

| Feature ID | Release | Status | Scenarios | Owner spec |
|---|---|---|---:|---|
""" + "\n".join(rows) + "\n"


def issue_map() -> str:
    known = {data["feature_id"] for _, data in specs()}
    rows: list[str] = []
    for _, data in specs():
        feature_id = data["feature_id"]
        dependencies = inline_list(data.get("dependencies", "[]"))
        if not dependencies:
            rows.append(f"| {feature_id} | none | product context only |")
        else:
            for dependency in dependencies:
                state = "known" if dependency in known else "external or unresolved"
                rows.append(f"| {feature_id} | {dependency} | {state} |")
    return generated_header("product-spec dependencies") + """# Feature dependency context

These are product integration dependencies, not automatically dispatchable work
items. The active ExecPlan decomposes implementation into an acyclic work graph.

| Feature | Dependency | Classification |
|---|---|---|
""" + "\n".join(rows) + "\n"


def route_inventory() -> str:
    text = (SPEC_ROOT / "coverage-matrix.md").read_text(encoding="utf-8")
    route_rows = [line for line in text.splitlines() if re.match(r"^\| ROUTE-\d+ ", line)]
    counts = {}
    for prefix in ("ROUTE", "NAV", "RUN", "SETTINGS"):
        counts[prefix] = len(re.findall(rf"^\| {prefix}-[A-Z0-9-]+ ", text, re.MULTILINE))
    return generated_header("docs/product-specs/coverage-matrix.md") + f"""# Prototype route inventory

Accepted frontend evidence: `deep-work-frontend@26c698b30ff08d5122cfaeedbd4a95296a7884f4`.
This is interaction evidence only. Full controls and settings ownership remains in
the canonical coverage matrix.

- Routes: {counts['ROUTE']}
- Desktop navigation destinations: {counts['NAV']}
- Run-panel entries: {counts['RUN']}
- Settings entries detected by `SETTINGS-*`: {counts['SETTINGS']}

| ID | Route and evidence | Observed state | Owner | Disposition | Planned resolution |
|---|---|---|---|---|---|
""" + "\n".join(route_rows) + "\n"


def graph_views() -> tuple[str, str]:
    graph = json.loads((ROOT / "tools" / "architecture" / "graph.json").read_text(encoding="utf-8"))
    package_rows = []
    for zone, config in graph["zones"].items():
        allowed = ", ".join(config["allows"]) or "none"
        package_rows.append(f"| `{zone}` | {config['runtime']} | {allowed} |")
    package = generated_header("tools/architecture/graph.json") + """# Package graph

| Zone | Runtime | May depend on |
|---|---|---|
""" + "\n".join(package_rows) + "\n"

    edges = []
    for zone, config in graph["zones"].items():
        for target in config["allows"]:
            edges.append(f'  "{zone}" --> "{target}"')
    architecture = generated_header("tools/architecture/graph.json") + """# Architecture graph

```mermaid
flowchart LR
""" + ("\n".join(edges) if edges else "  planned[No planned edges]") + "\n```\n"
    return package, architecture


def db_schema() -> str:
    return generated_header("Wave 0 repository state") + """# Database schema

No application database schema exists in Wave 0. PostgreSQL ownership and planned
entities are architectural decisions, not generated runtime evidence. Replace this
placeholder only from accepted migrations in Wave 1 or later.
"""


def outputs() -> dict[Path, str]:
    package, architecture = graph_views()
    return {
        GENERATED / "feature-coverage.md": feature_coverage(),
        GENERATED / "issue-map.md": issue_map(),
        GENERATED / "route-inventory.md": route_inventory(),
        GENERATED / "package-graph.md": package,
        GENERATED / "architecture-graph.md": architecture,
        GENERATED / "db-schema.md": db_schema(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale: list[str] = []
    for path, expected in outputs().items():
        if args.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
        elif not path.exists() or path.read_text(encoding="utf-8") != expected:
            stale.append(path.relative_to(ROOT).as_posix())
    if stale:
        print("generated document drift:")
        for path in stale:
            print(f"  {path}")
        print("repair: python3 tools/docs/generate.py --write")
        return 1
    action = "wrote" if args.write else "verified"
    print(f"{action} {len(outputs())} generated documents")
    return 0


if __name__ == "__main__":
    sys.exit(main())
