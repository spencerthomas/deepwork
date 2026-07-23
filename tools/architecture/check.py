#!/usr/bin/env python3
"""Check Deep Work source imports and generated views against the architecture graph."""

from __future__ import annotations

import argparse
import ast
import io
import json
import re
import sys
import tokenize
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Iterator, Sequence

SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts"}
TS_SUFFIXES = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts"}
RUNTIME_ESM_SUFFIXES = {".js", ".mjs", ".cjs", ".json"}
IGNORED_PARTS = {
    ".git",
    ".next",
    ".turbo",
    ".venv",
    "__pycache__",
    "coverage",
    "dist",
    "evidence",
    "node_modules",
    "scripts",
    "tests",
}
TS_IMPORT = re.compile(
    r"""(?mx)
    ^\s*(?:import|export)\s+(?:type\s+)?(?:[\s\S]*?\s+from\s+)?["']([^"']+)["']
    | \bimport\s*\(\s*["']([^"']+)["']\s*\)
    | \brequire\s*\(\s*["']([^"']+)["']\s*\)
    """
)
SENSITIVE_IDENTIFIER = re.compile(
    r"\b(?:authRef|credentialRef|secretRef|api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|secretValue)\b",
    re.IGNORECASE,
)
SECRET_SHAPE = re.compile(
    r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\bAKIA[0-9A-Z]{16}\b|\bgh[pousr]_[A-Za-z0-9]{20,}\b|\bsk-[A-Za-z0-9_-]{20,}\b)"
)
GRAPH_STATUSES = {"planned-wave-1", "enforced"}


def _shield_typescript(text: str, *, mask_strings: bool) -> str:
    """Blank comments/literal text but retain executable template expressions."""

    output = list(text)
    index = 0
    state = "code"
    quote = ""
    brace_depth: int | None = None
    stack: list[tuple[str, int | None, str]] = []

    def blank(position: int) -> None:
        if output[position] != "\n":
            output[position] = " "

    while index < len(text):
        character = text[index]
        following = text[index + 1] if index + 1 < len(text) else ""
        if state == "code":
            if character == "/" and following == "/":
                end = text.find("\n", index + 2)
                end = len(text) if end < 0 else end
                for position in range(index, end):
                    blank(position)
                index = end
                continue
            if character == "/" and following == "*":
                end = text.find("*/", index + 2)
                end = len(text) - 2 if end < 0 else end
                for position in range(index, min(len(text), end + 2)):
                    blank(position)
                index = min(len(text), end + 2)
                continue
            if brace_depth is not None:
                if character == "{":
                    brace_depth += 1
                elif character == "}":
                    if brace_depth == 0:
                        if mask_strings:
                            blank(index)
                        state, brace_depth, quote = stack.pop()
                        index += 1
                        continue
                    brace_depth -= 1
            if character in {"'", '"'}:
                stack.append((state, brace_depth, quote))
                state = "quote"
                quote = character
                if mask_strings:
                    blank(index)
                index += 1
                continue
            if character == "`":
                stack.append((state, brace_depth, quote))
                state = "template"
                quote = "`"
                if mask_strings:
                    blank(index)
                index += 1
                continue
        elif state == "quote":
            if character == "\\":
                if mask_strings:
                    blank(index)
                    if index + 1 < len(output):
                        blank(index + 1)
                index += 2
                continue
            if mask_strings:
                blank(index)
            if character == quote:
                state, brace_depth, quote = stack.pop()
            index += 1
            continue
        elif state == "template":
            if character == "\\":
                if mask_strings:
                    blank(index)
                    if index + 1 < len(output):
                        blank(index + 1)
                index += 2
                continue
            if character == "`":
                if mask_strings:
                    blank(index)
                state, brace_depth, quote = stack.pop()
                index += 1
                continue
            if character == "$" and following == "{":
                if mask_strings:
                    blank(index)
                    blank(index + 1)
                stack.append((state, brace_depth, quote))
                state = "code"
                brace_depth = 0
                quote = ""
                index += 2
                continue
            if mask_strings:
                blank(index)
            index += 1
            continue
        index += 1
    return "".join(output)


def _shield_python(text: str) -> str:
    """Blank Python comments and strings while retaining executable positions."""

    output = list(text)
    line_offsets = [0]
    for match in re.finditer("\n", text):
        line_offsets.append(match.end())

    def offset(position: tuple[int, int]) -> int:
        line, column = position
        return line_offsets[min(line - 1, len(line_offsets) - 1)] + column

    try:
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
        for token in tokens:
            if token.type not in {tokenize.COMMENT, tokenize.STRING}:
                continue
            start = offset(token.start)
            end = offset(token.end)
            for position in range(start, min(end, len(output))):
                if output[position] != "\n":
                    output[position] = " "
    except (IndentationError, tokenize.TokenError):
        return text
    return "".join(output)


@dataclass(frozen=True)
class Rule:
    identifier: str
    legal_direction: str
    anchor: str


@dataclass(frozen=True, order=True)
class Diagnostic:
    file: str
    rule: str
    detail: str
    legal_direction: str
    anchor: str
    reproduce: str

    def render(self) -> str:
        return (
            f"{self.file}: rule={self.rule}; {self.detail}; "
            f"legal={self.legal_direction}; anchor={self.anchor}; "
            f"reproduce={self.reproduce}"
        )


@dataclass(frozen=True)
class ImportReference:
    specifier: str
    line: int


class ArchitectureChecker:
    """Apply graph-declared rules to a repository or isolated fixture root."""

    def __init__(
        self,
        root: Path,
        graph: dict[str, object],
        graph_path: Path,
        *,
        check_generated_views: bool = True,
    ) -> None:
        self.root = root.resolve()
        self.graph = graph
        self.graph_path = graph_path.resolve()
        self.zones = graph["zones"]
        self.rules = {
            identifier: Rule(
                identifier=identifier,
                legal_direction=str(config["legal_direction"]),
                anchor=str(config["anchor"]),
            )
            for identifier, config in graph["rules"].items()
        }
        self.prefixes = {
            str(prefix): str(zone)
            for prefix, zone in graph.get("import_prefixes", {}).items()
        }
        self.provider_modules = tuple(str(value) for value in graph.get("provider_modules", []))
        self.provider_locations = tuple(
            str(value).strip("/") for value in graph.get("provider_locations", [])
        )
        self.browser_forbidden = tuple(
            str(value) for value in graph.get("browser_forbidden_modules", [])
        )
        self.domain_forbidden = tuple(
            str(value) for value in graph.get("domain_forbidden_modules", [])
        )
        self.esm_zones = set(str(value) for value in graph.get("esm_extension_zones", []))
        self.forbidden_edges = {
            (str(edge[0]), str(edge[1])) for edge in graph.get("forbidden", [])
        }
        self.composition_roots = tuple(
            str(value).strip("/") for value in graph.get("composition_roots", [])
        )
        self.environment_read_locations = tuple(
            str(value).strip("/") for value in graph.get("environment_read_locations", [])
        )
        self.python_layers = {
            str(layer): set(str(target) for target in targets)
            for layer, targets in graph.get("python_layers", {}).items()
        }
        self.check_generated_views = check_generated_views
        self.diagnostics: list[Diagnostic] = []
        self.module_edges: dict[Path, set[Path]] = defaultdict(set)

    def run(self) -> list[Diagnostic]:
        self._check_declared_graph_cycles()
        for zone, config in self.zones.items():
            source_root = self._source_root(str(zone))
            if source_root is None:
                continue
            for path in self._source_files(source_root):
                self._check_file(path, str(zone), dict(config))
        self._check_cycles()
        if self.check_generated_views:
            self._check_generated_views()
        return sorted(set(self.diagnostics))

    def coverage_summary(self) -> dict[str, object]:
        coverage = self.graph.get("coverage", {})
        markers = coverage.get("source_markers", {})
        gates = coverage.get("dependency_gates", {})
        present = sorted(
            zone
            for zone in markers
            if (source_root := self._source_root(str(zone))) is not None
            and self._marker_has_source(source_root)
        )
        missing = sorted(zone for zone in self.zones if zone not in present)
        gated = [
            {"zone": zone, "dependency": str(gates[zone])}
            for zone in missing
            if zone in gates
        ]
        ungated = sorted(zone for zone in missing if zone not in gates)
        status = "complete" if not missing else "dependency-gated" if not ungated else "incomplete"
        return {
            "status": status,
            "checked_zones": present,
            "missing_zones": missing,
            "dependency_gates": gated,
            "ungated_missing_zones": ungated,
        }

    def _marker_has_source(self, marker: Path) -> bool:
        return any(self._source_files(marker))

    def _source_root(self, zone: str) -> Path | None:
        marker = self.graph["coverage"]["source_markers"][zone]
        source_root = self.root / str(marker)
        if not source_root.exists() and not source_root.is_symlink():
            return None
        if not source_root.is_dir():
            raise ValueError(f"source marker for {zone} is not a directory: {marker}")
        resolved_zone = (self.root / zone).resolve()
        resolved_source = source_root.resolve()
        try:
            resolved_source.relative_to(resolved_zone)
        except ValueError:
            raise ValueError(
                f"source marker for {zone} resolves outside its declared zone: {marker}"
            ) from None
        return source_root

    def _source_files(self, zone_root: Path) -> Iterator[Path]:
        for path in sorted(zone_root.rglob("*")):
            if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
                continue
            relative_parts = path.relative_to(zone_root).parts
            if any(part in IGNORED_PARTS for part in relative_parts):
                continue
            yield path

    def _check_file(self, path: Path, zone: str, config: dict[str, object]) -> None:
        text = path.read_text(encoding="utf-8")
        imports = self._imports(path, text)
        for reference in imports:
            self._check_import(path, zone, config, reference)
            target = self._resolve_module(path, reference.specifier)
            if target is not None:
                self.module_edges[path].add(target)
        executable_text = self._executable_text(path, text)
        self._check_raw_network(path, zone, executable_text)
        self._check_domain_globals(path, zone, executable_text)
        self._check_credentials(path, zone, executable_text, text)
        self._check_environment(path, executable_text, text)

    def _imports(self, path: Path, text: str) -> list[ImportReference]:
        if path.suffix == ".py":
            try:
                tree = ast.parse(text, filename=str(path))
            except SyntaxError as exc:
                self._add(
                    path,
                    "parse-error",
                    f"Python syntax error at line {exc.lineno}: {exc.msg}",
                )
                return []
            references: list[ImportReference] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    references.extend(
                        ImportReference(alias.name, node.lineno) for alias in node.names
                    )
                elif isinstance(node, ast.ImportFrom):
                    dots = "." * node.level
                    module = node.module or ""
                    if module:
                        references.append(
                            ImportReference(f"{dots}{module}", node.lineno)
                        )
                    if not module:
                        references.extend(
                            ImportReference(f"{dots}{alias.name}", node.lineno)
                            for alias in node.names
                            if alias.name != "*"
                        )
                    elif module == "deepwork_api":
                        for alias in node.names:
                            if alias.name in self.python_layers:
                                references.append(
                                    ImportReference(
                                        f"{dots}{module}.{alias.name}",
                                        node.lineno,
                                    )
                                )
            return references
        comment_free = _shield_typescript(text, mask_strings=False)
        executable = _shield_typescript(text, mask_strings=True)
        return [
            ImportReference(next(value for value in match.groups() if value is not None), line)
            for match in TS_IMPORT.finditer(comment_free)
            if re.search(
                r"\b(?:import|export|require)\b",
                executable[match.start() : match.end()],
            )
            for line in [comment_free.count("\n", 0, match.start()) + 1]
        ]

    def _executable_text(self, path: Path, text: str) -> str:
        if path.suffix in TS_SUFFIXES:
            return _shield_typescript(text, mask_strings=True)
        if path.suffix == ".py":
            return _shield_python(text)
        return text

    def _check_import(
        self,
        path: Path,
        zone: str,
        config: dict[str, object],
        reference: ImportReference,
    ) -> None:
        specifier = reference.specifier
        target_zone = self._target_zone(specifier)
        if specifier.startswith("@deepwork/") and target_zone is None:
            self._add(
                path,
                "unknown-deepwork-import",
                f"line {reference.line} imports undeclared Deep Work package {specifier!r}",
            )
        allowed = set(str(value) for value in config.get("allows", []))
        if (
            target_zone is not None
            and target_zone != zone
            and (
                target_zone not in allowed
                or (zone, target_zone) in self.forbidden_edges
            )
        ):
            self._add(
                path,
                "illegal-zone-edge",
                f"line {reference.line} imports {specifier!r} ({zone} -> {target_zone})",
            )

        if zone == "packages/domain" and self._matches_module(
            specifier, self.domain_forbidden + self.browser_forbidden
        ):
            self._add(
                path,
                "domain-purity",
                f"line {reference.line} imports non-pure module {specifier!r}",
            )

        runtime = str(config.get("runtime", ""))
        target_runtime = (
            str(self.zones[target_zone].get("runtime", "")) if target_zone is not None else ""
        )
        if runtime in {"browser", "browser-safe"} and (
            self._matches_module(specifier, self.browser_forbidden)
            or target_runtime.startswith("server")
        ):
            self._add(
                path,
                "browser-server-boundary",
                f"line {reference.line} imports server-only module {specifier!r}",
            )

        if self._matches_module(specifier, self.provider_modules) and not self._provider_allowed(
            path, zone
        ):
            self._add(
                path,
                "provider-location",
                f"line {reference.line} imports provider module {specifier!r}",
            )

        if self._is_private_import(specifier, zone):
            self._add(
                path,
                "private-import",
                f"line {reference.line} uses deep/private import {specifier!r}",
            )

        if (
            zone in self.esm_zones
            and path.suffix in TS_SUFFIXES
            and specifier.startswith(".")
            and Path(specifier).suffix not in RUNTIME_ESM_SUFFIXES
        ):
            self._add(
                path,
                "esm-extension",
                f"line {reference.line} omits a runtime ESM extension in {specifier!r}",
            )

        if zone == "apps/api":
            layer = self._api_layer(path)
            target_path = self._resolve_module(path, specifier)
            target_layer = (
                self._api_layer(target_path)
                if target_path is not None and self._path_in_zone(target_path, "apps/api")
                else None
            )
            if (
                target_layer is not None
                and target_layer != layer
                and target_layer not in self.python_layers.get(layer, set())
            ):
                self._add(
                    path,
                    "python-layer-edge",
                    f"line {reference.line} imports Python API layer "
                    f"{target_layer!r} from {layer!r}",
                )
            if (
                target_layer == "adapters"
                and layer != "adapters"
                and not self._is_composition_root(path)
            ):
                self._add(
                    path,
                    "concrete-adapter-import",
                    f"line {reference.line} imports a concrete adapter outside composition root",
                )
            if self._matches_module(specifier, ("fastapi",)) and layer not in {
                "bootstrap",
                "package-root",
                "transport",
            }:
                self._add(
                    path,
                    "fastapi-layer",
                    f"line {reference.line} imports FastAPI from API layer {layer!r}",
                )
            if self._matches_module(specifier, ("sqlalchemy",)) and layer not in {
                "adapters",
                "bootstrap",
            }:
                self._add(
                    path,
                    "sqlalchemy-layer",
                    f"line {reference.line} imports SQLAlchemy from API layer {layer!r}",
                )

    def _check_raw_network(self, path: Path, zone: str, text: str) -> None:
        raw_fetch = re.search(r"\bfetch\s*\(", text)
        raw_client = re.search(r"\b(?:axios|XMLHttpRequest|WebSocket)\b", text)
        web_component = zone == "apps/web" and (
            path.suffix in {".jsx", ".tsx"} or "components" in path.parts
        )
        if (zone == "packages/ui" or web_component) and (raw_fetch or raw_client):
            self._add(path, "raw-network", "UI/React source constructs a raw network client")

    def _check_domain_globals(self, path: Path, zone: str, text: str) -> None:
        if zone != "packages/domain":
            return
        browser_or_runtime_global = re.search(
            r"\b(?:document|fetch|localStorage|navigator|process|sessionStorage|window)\b",
            text,
        )
        if browser_or_runtime_global:
            self._add(
                path,
                "domain-purity",
                "domain source references a browser, network, or process runtime global",
            )

    def _check_credentials(
        self,
        path: Path,
        zone: str,
        executable_text: str,
        original_text: str,
    ) -> None:
        browser_zones = {"apps/desktop", "apps/web", "packages/domain", "packages/sdk", "packages/ui"}
        relative = self._relative(path)
        wire_model = (
            zone == "apps/api"
            and any(part in {"contracts", "transport"} for part in Path(relative).parts)
        )
        sensitive_identifier = SENSITIVE_IDENTIFIER.search(executable_text)
        if path.suffix == ".py":
            sensitive_identifier = sensitive_identifier or self._python_sensitive_identifier(
                original_text
            )
        if (zone in browser_zones or wire_model) and sensitive_identifier:
            self._add(
                path,
                "credential-leakage",
                "browser-safe or wire source contains a reusable credential/reference identifier",
            )
        if SECRET_SHAPE.search(original_text):
            self._add(path, "credential-leakage", "source contains secret-shaped material")

    def _check_environment(
        self,
        path: Path,
        executable_text: str,
        original_text: str,
    ) -> None:
        if self._is_configuration_path(path):
            return
        patterns = (
            r"\bos\.environ\b",
            r"\bos\.getenv\s*\(",
            r"\bgetenv\s*\(",
            r"\bprocess\.env\b",
            r"\bimport\.meta\.env\b",
            r"\bDeno\.env\b",
        )
        environment_read = any(
            re.search(pattern, executable_text) for pattern in patterns
        )
        if path.suffix == ".py":
            environment_read = environment_read or self._python_environment_read(
                original_text
            )
        if environment_read:
            self._add(path, "environment-read", "source reads the process environment directly")

    def _python_sensitive_identifier(self, text: str) -> bool:
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return False
        identifiers = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                identifiers.append(node.id)
            elif isinstance(node, ast.Attribute):
                identifiers.append(node.attr)
            elif isinstance(node, ast.arg):
                identifiers.append(node.arg)
            elif isinstance(node, ast.keyword) and node.arg is not None:
                identifiers.append(node.arg)
        return any(SENSITIVE_IDENTIFIER.search(identifier) for identifier in identifiers)

    def _python_environment_read(self, text: str) -> bool:
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return False
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module == "os"
                and any(alias.name in {"environ", "getenv"} for alias in node.names)
            ):
                return True
            if isinstance(node, ast.Attribute):
                if (
                    isinstance(node.value, ast.Name)
                    and node.value.id == "os"
                    and node.attr in {"environ", "getenv"}
                ):
                    return True
            elif isinstance(node, ast.Name) and node.id == "getenv":
                return True
        return False

    def _check_cycles(self) -> None:
        state: dict[Path, int] = {}
        stack: list[Path] = []
        reported: set[frozenset[Path]] = set()

        def visit(node: Path) -> None:
            state[node] = 1
            stack.append(node)
            for target in sorted(self.module_edges.get(node, set())):
                if state.get(target, 0) == 0:
                    visit(target)
                elif state.get(target) == 1:
                    start = stack.index(target)
                    cycle = stack[start:] + [target]
                    key = frozenset(cycle)
                    if key not in reported:
                        reported.add(key)
                        route = " -> ".join(self._relative(item) for item in cycle)
                        self._add(node, "import-cycle", f"module cycle detected: {route}")
            stack.pop()
            state[node] = 2

        for node in sorted(self.module_edges):
            if state.get(node, 0) == 0:
                visit(node)

    def _check_declared_graph_cycles(self) -> None:
        state: dict[str, int] = {}
        stack: list[str] = []

        def visit(zone: str) -> None:
            state[zone] = 1
            stack.append(zone)
            for target in self.zones[zone].get("allows", []):
                if target not in self.zones:
                    self._add(
                        self.graph_path,
                        "illegal-zone-edge",
                        f"zone {zone!r} allows undeclared target {target!r}",
                    )
                    continue
                if state.get(target, 0) == 0:
                    visit(target)
                elif state.get(target) == 1:
                    start = stack.index(target)
                    route = " -> ".join(stack[start:] + [target])
                    self._add(
                        self.graph_path,
                        "import-cycle",
                        f"declared package cycle detected: {route}",
                    )
            stack.pop()
            state[zone] = 2

        for zone in self.zones:
            if state.get(zone, 0) == 0:
                visit(zone)

    def _check_generated_views(self) -> None:
        configured = self.graph.get("generated_views", {})
        for relative, view in configured.items():
            path = self.root / str(relative)
            if not path.exists():
                self._add(
                    path,
                    "generated-drift",
                    f"configured {view} is missing; "
                    "repair=python3 tools/docs/generate.py --write",
                )
                continue
            expected = self._render_generated(str(view))
            if path.read_text(encoding="utf-8") != expected:
                self._add(
                    path,
                    "generated-drift",
                    f"{view} does not match graph authority; "
                    "repair=python3 tools/docs/generate.py --write",
                )

    def _render_generated(self, view: str) -> str:
        header = (
            "<!-- GENERATED: do not edit by hand. -->\n"
            "<!-- Source: tools/architecture/graph.json; "
            "command: python3 tools/docs/generate.py --write -->\n\n"
        )
        if view == "package-graph":
            rows = []
            for zone, config in self.zones.items():
                allowed = ", ".join(config["allows"]) or "none"
                rows.append(f"| `{zone}` | {config['runtime']} | {allowed} |")
            return (
                header
                + "# Package graph\n\n"
                + "| Zone | Runtime | May depend on |\n"
                + "|---|---|---|\n"
                + "\n".join(rows)
                + "\n"
            )
        if view == "architecture-graph":
            edges = [
                f'  "{zone}" --> "{target}"'
                for zone, config in self.zones.items()
                for target in config["allows"]
            ]
            body = "\n".join(edges) if edges else "  planned[No planned edges]"
            return header + "# Architecture graph\n\n```mermaid\nflowchart LR\n" + body + "\n```\n"
        raise ValueError(f"unknown generated architecture view: {view}")

    def _target_zone(self, specifier: str) -> str | None:
        for prefix, zone in sorted(self.prefixes.items(), key=lambda item: -len(item[0])):
            if specifier == prefix or specifier.startswith(prefix + "/") or specifier.startswith(
                prefix + "."
            ):
                return zone
        return None

    def _provider_allowed(self, path: Path, zone: str) -> bool:
        relative = self._relative(path).replace("\\", "/")
        canonical = relative.replace("apps/api/src/deepwork_api/", "apps/api/", 1)
        return any(
            candidate == location or candidate.startswith(location + "/")
            for location in self.provider_locations
            for candidate in (relative, canonical)
        )

    def _is_private_import(self, specifier: str, zone: str) -> bool:
        target = self._target_zone(specifier)
        if specifier.startswith(".") or target == zone:
            return False
        normalized = specifier.replace(".", "/") if not specifier.startswith("@") else specifier
        segments = [part for part in normalized.split("/") if part not in {"", ".", ".."}]
        if any(
            part.startswith("_") or part in {"internal", "private", "src", "dist"}
            for part in segments[1:]
        ):
            return True
        if target is not None and target != zone:
            public_prefix = next(
                prefix
                for prefix, mapped_zone in self.prefixes.items()
                if mapped_zone == target and (specifier == prefix or specifier.startswith(prefix))
            )
            return specifier != public_prefix
        return False

    def _resolve_module(self, path: Path, specifier: str) -> Path | None:
        if path.suffix == ".py":
            return self._resolve_python_module(path, specifier)
        if not specifier.startswith("."):
            return None
        base = path.parent / specifier
        candidates = [base]
        if base.suffix in RUNTIME_ESM_SUFFIXES:
            candidates.extend(
                base.with_suffix(suffix)
                for suffix in (".ts", ".tsx", ".mts", ".cts")
                if base.suffix in {".js", ".mjs", ".cjs"}
            )
        else:
            candidates.extend(base.with_suffix(suffix) for suffix in SOURCE_SUFFIXES)
            candidates.extend(base / f"index{suffix}" for suffix in SOURCE_SUFFIXES)
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved.is_file() and self.root in resolved.parents:
                return resolved
        return None

    def _resolve_python_module(self, path: Path, specifier: str) -> Path | None:
        api_source = self.root / "apps/api/src"
        agent_source = self.root / "packages/agent/src"
        if specifier.startswith("."):
            leading = len(specifier) - len(specifier.lstrip("."))
            base = path.parent
            for _ in range(max(0, leading - 1)):
                base = base.parent
            remainder = specifier[leading:]
            module_base = base / Path(*remainder.split(".")) if remainder else base
        elif specifier == "deepwork_api" or specifier.startswith("deepwork_api."):
            module_base = api_source / Path(*specifier.split("."))
        elif specifier == "deepwork_agent" or specifier.startswith("deepwork_agent."):
            module_base = agent_source / Path(*specifier.split("."))
        else:
            return None
        candidates = [module_base.with_suffix(".py"), module_base / "__init__.py"]
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved.is_file() and self.root in resolved.parents:
                return resolved
        return None

    def _api_layer(self, path: Path) -> str:
        parts = path.relative_to(self.root / "apps/api").parts
        if "deepwork_api" in parts:
            index = parts.index("deepwork_api")
            if len(parts) > index + 1:
                candidate = parts[index + 1]
                if "." not in candidate:
                    return candidate
        return "package-root"

    def _canonical_arch_path(self, path: Path) -> str:
        relative = self._relative(path).replace("\\", "/")
        return relative.replace("apps/api/src/deepwork_api/", "apps/api/", 1).replace(
            "packages/agent/src/deepwork_agent/", "packages/agent/", 1
        )

    def _path_in_zone(self, path: Path, zone: str) -> bool:
        try:
            path.resolve().relative_to((self.root / zone).resolve())
        except ValueError:
            return False
        return True

    def _is_composition_root(self, path: Path) -> bool:
        canonical = self._canonical_arch_path(path)
        return any(
            canonical == root or canonical.startswith(root + "/")
            for root in self.composition_roots
        )

    def _is_configuration_path(self, path: Path) -> bool:
        canonical = self._canonical_arch_path(path)
        if any(
            canonical == zone or canonical.startswith(zone + "/")
            for zone in ("packages/domain", "packages/sdk", "packages/ui")
        ):
            return False
        return any(
            canonical == location or canonical.startswith(location.rstrip("/") + "/")
            for location in self.environment_read_locations
        )

    def _matches_module(self, specifier: str, modules: Iterable[str]) -> bool:
        return any(
            specifier == module
            or specifier.startswith(module + "/")
            or specifier.startswith(module + ".")
            or module.endswith(":")
            and specifier.startswith(module)
            for module in modules
        )

    def _relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def _add(self, path: Path, rule_id: str, detail: str) -> None:
        rule = self.rules[rule_id]
        self.diagnostics.append(
            Diagnostic(
                file=self._relative(path),
                rule=rule.identifier,
                detail=detail,
                legal_direction=rule.legal_direction,
                anchor=rule.anchor,
                reproduce=self._reproduction(),
            )
        )

    def _reproduction(self) -> str:
        try:
            root = self.root.relative_to(Path.cwd().resolve()).as_posix() or "."
        except ValueError:
            root = self.root.as_posix()
        try:
            graph = self.graph_path.relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            graph = self.graph_path.as_posix()
        return f"python3 tools/architecture/check.py --root {root} --graph {graph}"


def load_graph(path: Path) -> dict[str, object]:
    graph = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "composition_roots",
        "coverage",
        "forbidden",
        "python_layers",
        "rules",
        "schema_version",
        "status",
        "zones",
    }
    missing = sorted(required - graph.keys())
    if graph.get("schema_version") != 1 or missing:
        raise ValueError(f"invalid architecture graph; missing={missing}, schema_version must be 1")
    if graph.get("status") not in GRAPH_STATUSES:
        raise ValueError(
            f"invalid architecture graph status: {graph.get('status')!r}; "
            f"expected one of {sorted(GRAPH_STATUSES)}"
        )
    for zone, config in graph["zones"].items():
        if not isinstance(config, dict) or "runtime" not in config or "allows" not in config:
            raise ValueError(f"invalid zone declaration: {zone}")
    coverage = graph["coverage"]
    if not isinstance(coverage, dict) or not isinstance(
        coverage.get("source_markers"), dict
    ):
        raise ValueError("architecture coverage must declare source_markers")
    source_markers = coverage["source_markers"]
    marker_zones = set(source_markers)
    declared_zones = set(graph["zones"])
    if marker_zones != declared_zones:
        raise ValueError(
            "source marker zones must exactly match declared zones; "
            f"missing={sorted(declared_zones - marker_zones)}, "
            f"unknown={sorted(marker_zones - declared_zones)}"
        )
    for zone, marker in source_markers.items():
        if not isinstance(marker, str) or not marker or "\\" in marker:
            raise ValueError(
                f"source marker for {zone} must be a canonical POSIX path: {marker!r}"
            )
        marker_path = PurePosixPath(marker)
        if (
            marker_path.is_absolute()
            or ".." in marker_path.parts
            or marker_path.as_posix() != marker
        ):
            raise ValueError(
                f"source marker for {zone} must be a canonical POSIX path: {marker!r}"
            )
        try:
            marker_path.relative_to(PurePosixPath(zone))
        except ValueError:
            raise ValueError(
                f"source marker for {zone} is outside its declared zone: {marker}"
            ) from None
    for edge in graph.get("forbidden", []):
        if (
            not isinstance(edge, list)
            or len(edge) != 2
            or any(zone not in graph["zones"] for zone in edge)
        ):
            raise ValueError(f"invalid forbidden edge declaration: {edge!r}")
    for root in graph.get("composition_roots", []):
        if not any(
            str(root) == zone or str(root).startswith(zone + "/")
            for zone in graph["zones"]
        ):
            raise ValueError(f"composition root is outside declared zones: {root}")
    unknown_prefix_zones = sorted(
        set(graph.get("import_prefixes", {}).values()).difference(graph["zones"])
    )
    if unknown_prefix_zones:
        raise ValueError(f"import prefixes reference unknown zones: {unknown_prefix_zones}")
    python_layers = graph["python_layers"]
    for layer, targets in python_layers.items():
        unknown = sorted(set(targets).difference(python_layers))
        if unknown:
            raise ValueError(f"Python layer {layer} references unknown layers: {unknown}")
    forbidden_environment_zones = ("packages/domain", "packages/sdk", "packages/ui")
    unsafe_environment_locations = sorted(
        location
        for location in graph.get("environment_read_locations", [])
        if any(
            str(location) == zone or str(location).startswith(zone + "/")
            for zone in forbidden_environment_zones
        )
    )
    if unsafe_environment_locations:
        raise ValueError(
            "environment exemptions cannot enter domain/UI/SDK zones: "
            f"{unsafe_environment_locations}"
        )
    return graph


def check_root(
    root: Path,
    graph_path: Path,
    *,
    check_generated_views: bool = True,
) -> list[Diagnostic]:
    graph = load_graph(graph_path)
    return ArchitectureChecker(
        root,
        graph,
        graph_path,
        check_generated_views=check_generated_views,
    ).run()


def _fixture_graph(fixture: Path, fallback: Path) -> Path:
    candidate = fixture / "tools/architecture/graph.json"
    return candidate if candidate.is_file() else fallback


def verify_fixtures(fixtures: Path, graph_path: Path) -> bool:
    ok = True
    positive_root = fixtures / "positive"
    negative_root = fixtures / "negative"
    positive = sorted(path for path in positive_root.iterdir() if path.is_dir())
    negative = sorted(path for path in negative_root.iterdir() if path.is_dir())
    if not positive or not negative:
        print("fixture verification requires at least one positive and negative fixture", file=sys.stderr)
        return False

    for fixture in positive:
        diagnostics = check_root(
            fixture,
            _fixture_graph(fixture, graph_path),
            check_generated_views=False,
        )
        if diagnostics:
            ok = False
            print(f"UNEXPECTED CLEAN FAILURE: {fixture.as_posix()}", file=sys.stderr)
            for diagnostic in diagnostics:
                print(diagnostic.render(), file=sys.stderr)
        else:
            print(f"verified positive fixture: {fixture.name}")

    for fixture in negative:
        manifest_path = fixture / "fixture.json"
        if not manifest_path.is_file():
            ok = False
            print(f"negative fixture lacks fixture.json: {fixture.as_posix()}", file=sys.stderr)
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = set(str(value) for value in manifest.get("expected_rules", []))
        allowed_additional = set(
            str(value) for value in manifest.get("allowed_additional_rules", [])
        )
        diagnostics = check_root(
            fixture,
            _fixture_graph(fixture, graph_path),
            check_generated_views=bool(manifest.get("check_generated_views", False)),
        )
        actual = {diagnostic.rule for diagnostic in diagnostics}
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected - allowed_additional)
        if not diagnostics or missing or unexpected:
            ok = False
            print(
                f"UNEXPECTED NEGATIVE RESULT: {fixture.name}; "
                f"missing_rules={missing}; unexpected_rules={unexpected}",
                file=sys.stderr,
            )
        else:
            print(
                f"verified negative fixture: {fixture.name}; "
                f"rules={','.join(sorted(actual))}"
            )
    return ok


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path)
    parser.add_argument("--verify-negative", action="store_true")
    return parser


def acceptance_status(
    graph: dict[str, object],
    coverage: dict[str, object],
) -> str:
    if graph.get("status") == "enforced" and coverage.get("status") == "complete":
        return "boundaries-verified"
    return "implemented-not-accepted"


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        graph = load_graph(args.graph)
        checker = ArchitectureChecker(args.root, graph, args.graph)
        diagnostics = checker.run()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"architecture check configuration error: {exc}", file=sys.stderr)
        return 2
    if diagnostics:
        for diagnostic in diagnostics:
            print(diagnostic.render(), file=sys.stderr)
        return 1
    coverage = checker.coverage_summary()
    print(
        json.dumps(
            {
                "command": "architecture-check",
                "status": "passed",
                "coverage": coverage,
                "graph_status": graph["status"],
                "acceptance": acceptance_status(graph, coverage),
                "root": args.root.as_posix(),
            },
            sort_keys=True,
        )
    )

    if args.verify_negative:
        if args.fixtures is None:
            print("--verify-negative requires --fixtures", file=sys.stderr)
            return 2
        try:
            return 0 if verify_fixtures(args.fixtures, args.graph.resolve()) else 1
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"architecture fixture verification error: {exc}", file=sys.stderr)
            return 2
    if args.fixtures is not None:
        print("--fixtures requires --verify-negative", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
