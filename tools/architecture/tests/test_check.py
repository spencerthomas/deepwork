"""Tests for the graph-driven architecture checker."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tools.architecture.check import (
    ArchitectureChecker,
    acceptance_status,
    check_root,
    load_graph,
    main,
    verify_fixtures,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
GRAPH_PATH = REPOSITORY_ROOT / "tools/architecture/graph.json"
FIXTURES = REPOSITORY_ROOT / "internal/fixtures/architecture"


class ArchitectureCheckerTests(unittest.TestCase):
    def test_repository_and_positive_fixture_are_clean(self) -> None:
        self.assertEqual(check_root(REPOSITORY_ROOT, GRAPH_PATH), [])
        self.assertEqual(
            check_root(
                FIXTURES / "positive/clean",
                GRAPH_PATH,
                check_generated_views=False,
            ),
            [],
        )

    def test_every_negative_fixture_emits_its_declared_rule(self) -> None:
        for fixture in sorted((FIXTURES / "negative").iterdir()):
            with self.subTest(fixture=fixture.name):
                manifest = json.loads((fixture / "fixture.json").read_text(encoding="utf-8"))
                expected = set(manifest["expected_rules"])
                diagnostics = check_root(
                    fixture,
                    GRAPH_PATH,
                    check_generated_views=bool(
                        manifest.get("check_generated_views", False)
                    ),
                )
                actual = {diagnostic.rule for diagnostic in diagnostics}
                self.assertTrue(diagnostics)
                self.assertEqual(expected, actual)

    def test_diagnostic_contains_every_actionable_field(self) -> None:
        diagnostics = check_root(
            FIXTURES / "negative/ui-to-sdk",
            GRAPH_PATH,
            check_generated_views=False,
        )
        self.assertEqual(len(diagnostics), 1)
        diagnostic = diagnostics[0]
        rendered = diagnostic.render()
        self.assertIn("packages/ui/src/bad.ts", rendered)
        self.assertIn("rule=illegal-zone-edge", rendered)
        self.assertIn("legal=", rendered)
        self.assertIn("anchor=ARCHITECTURE.md#package-graph", rendered)
        self.assertIn("reproduce=python3 tools/architecture/check.py", rendered)

    def test_graph_is_machine_readable_and_declares_all_fixture_rules(self) -> None:
        graph = load_graph(GRAPH_PATH)
        declared = set(graph["rules"])
        expected: set[str] = set()
        for manifest_path in (FIXTURES / "negative").glob("*/fixture.json"):
            expected.update(json.loads(manifest_path.read_text(encoding="utf-8"))["expected_rules"])
        self.assertLessEqual(expected, declared)
        self.assertEqual(graph["exceptions"], [])

    def test_negative_fixture_that_becomes_clean_fails_verification(self) -> None:
        with tempfile.TemporaryDirectory(prefix="architecture-fixture-") as directory:
            fixtures = Path(directory)
            positive = fixtures / "positive/clean"
            negative = fixtures / "negative/missing-violation"
            (positive / "packages/domain/src").mkdir(parents=True)
            (negative / "packages/domain/src").mkdir(parents=True)
            (positive / "packages/domain/src/value.ts").write_text(
                "export const value = true;\n",
                encoding="utf-8",
            )
            (negative / "packages/domain/src/value.ts").write_text(
                "export const value = true;\n",
                encoding="utf-8",
            )
            (negative / "fixture.json").write_text(
                '{"expected_rules":["domain-purity"]}\n',
                encoding="utf-8",
            )
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertFalse(verify_fixtures(fixtures, GRAPH_PATH))
            self.assertIn("UNEXPECTED NEGATIVE RESULT", stderr.getvalue())

    def test_positive_fixture_that_becomes_illegal_fails_verification(self) -> None:
        with tempfile.TemporaryDirectory(prefix="architecture-fixture-") as directory:
            fixtures = Path(directory)
            positive = fixtures / "positive/broken"
            negative = fixtures / "negative/known-bad"
            (positive / "packages/ui/src").mkdir(parents=True)
            (negative / "packages/ui/src").mkdir(parents=True)
            (positive / "packages/ui/src/bad.ts").write_text(
                'import "@deepwork/sdk";\n',
                encoding="utf-8",
            )
            (negative / "packages/ui/src/bad.ts").write_text(
                'import "@deepwork/sdk";\n',
                encoding="utf-8",
            )
            (negative / "fixture.json").write_text(
                '{"expected_rules":["illegal-zone-edge"]}\n',
                encoding="utf-8",
            )
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertFalse(verify_fixtures(fixtures, GRAPH_PATH))
            self.assertIn("UNEXPECTED CLEAN FAILURE", stderr.getvalue())

    def test_generated_view_projection_matches_repository(self) -> None:
        graph = load_graph(GRAPH_PATH)
        checker = ArchitectureChecker(REPOSITORY_ROOT, graph, GRAPH_PATH)
        for relative, view in graph["generated_views"].items():
            actual = (REPOSITORY_ROOT / relative).read_text(encoding="utf-8")
            self.assertEqual(checker._render_generated(view), actual)

    def test_repository_coverage_is_explicitly_dependency_gated(self) -> None:
        graph = load_graph(GRAPH_PATH)
        coverage = ArchitectureChecker(
            REPOSITORY_ROOT,
            graph,
            GRAPH_PATH,
        ).coverage_summary()
        self.assertEqual(coverage["status"], "dependency-gated")
        self.assertEqual(
            coverage["checked_zones"],
            [
                "apps/api",
                "packages/agent",
                "packages/domain",
                "packages/sdk",
                "packages/ui",
            ],
        )
        self.assertEqual(coverage["missing_zones"], ["apps/desktop", "apps/web"])
        self.assertEqual(coverage["ungated_missing_zones"], [])
        self.assertEqual(
            coverage["dependency_gates"],
            [
                {
                    "zone": "apps/desktop",
                    "dependency": "local:DW-M1-TS-SCAFFOLD",
                },
                {
                    "zone": "apps/web",
                    "dependency": "local:DW-M1-TS-SCAFFOLD",
                },
            ],
        )

    def test_empty_coverage_marker_is_not_counted_as_checked(self) -> None:
        graph = load_graph(GRAPH_PATH)
        with tempfile.TemporaryDirectory(prefix="architecture-coverage-") as directory:
            root = Path(directory)
            marker = root / "apps/api/src/deepwork_api"
            marker.mkdir(parents=True)
            checker = ArchitectureChecker(
                root,
                graph,
                GRAPH_PATH,
                check_generated_views=False,
            )
            self.assertNotIn("apps/api", checker.coverage_summary()["checked_zones"])
            (marker / "status.py").write_text("VALUE = True\n", encoding="utf-8")
            self.assertIn("apps/api", checker.coverage_summary()["checked_zones"])

    def test_cli_reports_machine_readable_non_acceptance(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = main(
                [
                    "--root",
                    str(REPOSITORY_ROOT),
                    "--graph",
                    str(GRAPH_PATH),
                ]
            )
        self.assertEqual(status, 0, stderr.getvalue())
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], "passed")
        self.assertEqual(payload["acceptance"], "implemented-not-accepted")
        self.assertEqual(payload["coverage"]["status"], "dependency-gated")

    def test_missing_configured_generated_views_fail(self) -> None:
        with tempfile.TemporaryDirectory(prefix="architecture-generated-") as directory:
            diagnostics = check_root(Path(directory), GRAPH_PATH)
        generated = [
            diagnostic for diagnostic in diagnostics if diagnostic.rule == "generated-drift"
        ]
        self.assertEqual(len(generated), 2)
        self.assertTrue(all("is missing" in diagnostic.detail for diagnostic in generated))

    def test_forbidden_edge_overrides_accidental_allow(self) -> None:
        with tempfile.TemporaryDirectory(prefix="architecture-graph-") as directory:
            graph = load_graph(GRAPH_PATH)
            graph["zones"]["packages/ui"]["allows"].append("packages/sdk")
            graph_path = Path(directory) / "graph.json"
            graph_path.write_text(json.dumps(graph), encoding="utf-8")
            diagnostics = check_root(
                FIXTURES / "negative/ui-to-sdk",
                graph_path,
                check_generated_views=False,
            )
        self.assertEqual({item.rule for item in diagnostics}, {"illegal-zone-edge"})

    def test_fixture_verification_rejects_undeclared_extra_rule(self) -> None:
        with tempfile.TemporaryDirectory(prefix="architecture-fixture-") as directory:
            fixtures = Path(directory)
            positive = fixtures / "positive/clean/packages/domain/src"
            negative = fixtures / "negative/extra/packages/domain/src"
            positive.mkdir(parents=True)
            negative.mkdir(parents=True)
            (positive / "value.ts").write_text(
                "export const value = true;\n",
                encoding="utf-8",
            )
            (negative / "bad.ts").write_text(
                "export const value = process.env.VALUE;\n",
                encoding="utf-8",
            )
            (fixtures / "negative/extra/fixture.json").write_text(
                '{"expected_rules":["environment-read"]}\n',
                encoding="utf-8",
            )
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertFalse(verify_fixtures(fixtures, GRAPH_PATH))
        self.assertIn("unexpected_rules=['domain-purity']", stderr.getvalue())

    def test_typescript_comments_and_strings_are_lexically_shielded(self) -> None:
        diagnostics = check_root(
            FIXTURES / "positive/clean",
            GRAPH_PATH,
            check_generated_views=False,
        )
        self.assertEqual(diagnostics, [])

    def test_nested_template_expressions_remain_executable(self) -> None:
        diagnostics = check_root(
            FIXTURES / "negative/template-expression",
            GRAPH_PATH,
            check_generated_views=False,
        )
        self.assertEqual(
            {diagnostic.rule for diagnostic in diagnostics},
            {"credential-leakage", "environment-read", "raw-network"},
        )

    def test_secret_shapes_are_scanned_in_ts_and_python_comments(self) -> None:
        for fixture_name in ("secret-ts-comment", "secret-python-docstring"):
            with self.subTest(fixture=fixture_name):
                diagnostics = check_root(
                    FIXTURES / "negative" / fixture_name,
                    GRAPH_PATH,
                    check_generated_views=False,
                )
                self.assertEqual(
                    {diagnostic.rule for diagnostic in diagnostics},
                    {"credential-leakage"},
                )

    def test_python_comments_and_docstrings_do_not_trigger_identifiers_or_env(self) -> None:
        diagnostics = check_root(
            FIXTURES / "positive/clean",
            GRAPH_PATH,
            check_generated_views=False,
        )
        self.assertEqual(diagnostics, [])

    def test_graph_status_controls_acceptance_even_with_complete_coverage(self) -> None:
        graph = load_graph(GRAPH_PATH)
        complete = {"status": "complete"}
        self.assertEqual(
            acceptance_status(graph, complete),
            "implemented-not-accepted",
        )
        graph["status"] = "enforced"
        self.assertEqual(
            acceptance_status(graph, complete),
            "boundaries-verified",
        )
        self.assertEqual(
            acceptance_status(graph, {"status": "dependency-gated"}),
            "implemented-not-accepted",
        )

    def test_unknown_graph_status_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="architecture-graph-") as directory:
            graph = load_graph(GRAPH_PATH)
            graph["status"] = "claimed-without-enforcement"
            graph_path = Path(directory) / "graph.json"
            graph_path.write_text(json.dumps(graph), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid architecture graph status"):
                load_graph(graph_path)

    def test_graph_rejects_environment_exemption_in_pure_zone(self) -> None:
        with tempfile.TemporaryDirectory(prefix="architecture-graph-") as directory:
            graph = load_graph(GRAPH_PATH)
            graph["environment_read_locations"].append("packages/domain/config")
            graph_path = Path(directory) / "graph.json"
            graph_path.write_text(json.dumps(graph), encoding="utf-8")
            with self.assertRaisesRegex(
                ValueError,
                "environment exemptions cannot enter domain/UI/SDK",
            ):
                load_graph(graph_path)

    def test_graph_requires_one_source_marker_per_zone(self) -> None:
        with tempfile.TemporaryDirectory(prefix="architecture-graph-") as directory:
            graph = load_graph(GRAPH_PATH)
            del graph["coverage"]["source_markers"]["packages/ui"]
            graph_path = Path(directory) / "graph.json"
            graph_path.write_text(json.dumps(graph), encoding="utf-8")
            with self.assertRaisesRegex(
                ValueError,
                "source marker zones must exactly match declared zones",
            ):
                load_graph(graph_path)

    def test_graph_rejects_source_marker_outside_its_zone(self) -> None:
        with tempfile.TemporaryDirectory(prefix="architecture-graph-") as directory:
            graph = load_graph(GRAPH_PATH)
            graph["coverage"]["source_markers"]["packages/ui"] = "packages/sdk/src"
            graph_path = Path(directory) / "graph.json"
            graph_path.write_text(json.dumps(graph), encoding="utf-8")
            with self.assertRaisesRegex(
                ValueError,
                "source marker for packages/ui is outside its declared zone",
            ):
                load_graph(graph_path)

    def test_graph_rejects_noncanonical_source_markers(self) -> None:
        invalid_markers = (
            "/packages/domain/src",
            "packages/domain/../sdk/src",
            "packages/domain/src/../../sdk/src",
            r"packages/domain/..\sdk/src",
        )
        for marker in invalid_markers:
            with self.subTest(marker=marker), tempfile.TemporaryDirectory(
                prefix="architecture-graph-"
            ) as directory:
                graph = load_graph(GRAPH_PATH)
                graph["coverage"]["source_markers"]["packages/domain"] = marker
                graph_path = Path(directory) / "graph.json"
                graph_path.write_text(json.dumps(graph), encoding="utf-8")
                with self.assertRaisesRegex(
                    ValueError,
                    "source marker for packages/domain must be a canonical POSIX path",
                ):
                    load_graph(graph_path)

    def test_checker_rejects_existing_file_as_source_marker(self) -> None:
        with tempfile.TemporaryDirectory(prefix="architecture-marker-") as directory:
            root = Path(directory)
            marker = root / "packages/domain/src/index.ts"
            marker.parent.mkdir(parents=True)
            marker.write_text('import "node:fs";\n', encoding="utf-8")
            graph = load_graph(GRAPH_PATH)
            graph["coverage"]["source_markers"]["packages/domain"] = (
                "packages/domain/src/index.ts"
            )
            graph_path = root / "graph.json"
            graph_path.write_text(json.dumps(graph), encoding="utf-8")
            checker = ArchitectureChecker(
                root,
                load_graph(graph_path),
                graph_path,
                check_generated_views=False,
            )
            with self.assertRaisesRegex(
                ValueError,
                "source marker for packages/domain is not a directory",
            ):
                checker.run()
            with self.assertRaisesRegex(
                ValueError,
                "source marker for packages/domain is not a directory",
            ):
                checker.coverage_summary()

    def test_checker_rejects_source_marker_symlinked_into_another_zone(self) -> None:
        with tempfile.TemporaryDirectory(prefix="architecture-marker-") as directory:
            root = Path(directory)
            source = root / "packages/sdk/src"
            source.mkdir(parents=True)
            (source / "index.ts").write_text("export const value = true;\n", encoding="utf-8")
            domain = root / "packages/domain"
            domain.mkdir(parents=True)
            (domain / "src").symlink_to("../sdk/src", target_is_directory=True)
            checker = ArchitectureChecker(
                root,
                load_graph(GRAPH_PATH),
                GRAPH_PATH,
                check_generated_views=False,
            )
            with self.assertRaisesRegex(
                ValueError,
                "source marker for packages/domain resolves outside its declared zone",
            ):
                checker.run()
            with self.assertRaisesRegex(
                ValueError,
                "source marker for packages/domain resolves outside its declared zone",
            ):
                checker.coverage_summary()


if __name__ == "__main__":
    unittest.main()
