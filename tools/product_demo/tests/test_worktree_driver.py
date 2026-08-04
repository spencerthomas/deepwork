from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

PRODUCT_DEMO = Path(__file__).resolve().parents[1]
WORKTREE = PRODUCT_DEMO.parent / "worktree"
sys.path.insert(0, str(PRODUCT_DEMO))
sys.path.insert(0, str(WORKTREE))

import harness  # noqa: E402
import worktree_driver as driver  # noqa: E402
from isolation import allocate_manifest  # noqa: E402


class DriverContractTests(unittest.TestCase):
    def test_bound_digest_matches_harness_authority(self) -> None:
        payload = {"namespace": "dw-test-a", "ports": [21000, 21001]}
        identity = {
            "run_nonce": "1" * 32,
            "driver_revision": "2" * 40,
            "driver_sha256": "3" * 64,
        }
        self.assertEqual(
            driver._bound_digest("allocation", payload, **identity),
            harness._bound_digest(kind="allocation", payload=payload, **identity),
        )

    def test_manifest_must_belong_to_exact_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary).resolve()
            root = sandbox / "root"
            peer = sandbox / "peer"
            root.mkdir()
            peer.mkdir()
            manifest = allocate_manifest(
                root=root,
                namespace="dw-test-a",
                evidence_dir=sandbox / "proof",
            )
            manifest_path = sandbox / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(driver._load_manifest(manifest_path, root), manifest)
            with self.assertRaises(driver.DriverError):
                driver._load_manifest(manifest_path, peer)

    def test_object_service_rejects_peer_prefix_and_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            # Exercise the path policy without binding a socket; network behavior
            # belongs to the real dual-stack acceptance gate.
            server = object.__new__(driver._FixtureServer)
            server.data_root = Path(temporary)
            server.object_prefix = "worktrees/dw-test-a/owned/"
            self.assertIsNotNone(
                server.object_path("worktrees/dw-test-a/owned/result.json")
            )
            self.assertIsNone(
                server.object_path("worktrees/dw-test-b/owned/result.json")
            )
            self.assertIsNone(
                server.object_path("worktrees/dw-test-a/owned/../../escape")
            )

    def test_persisted_next_env_snapshot_restores_missing_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "root"
            workspace = root / ".deepwork/worktrees/dw-test-a"
            web = root / "apps/web"
            web.mkdir(parents=True)
            workspace.mkdir(parents=True)
            destination = web / "next-env.d.ts"
            destination.write_text("original\n", encoding="utf-8")
            snapshot = driver._capture_next_env(root, workspace)
            destination.unlink()
            driver._restore_next_env(root, workspace, snapshot)
            self.assertEqual(destination.read_text(encoding="utf-8"), "original\n")

    def test_external_recovery_restores_next_env_before_workspace_removal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = (Path(temporary) / "root").resolve()
            (root / "apps/web").mkdir(parents=True)
            destination = root / "apps/web/next-env.d.ts"
            destination.write_text("tracked\n", encoding="utf-8")
            manifest = allocate_manifest(
                root=root,
                namespace="dw-test-a",
                evidence_dir=root / "proof",
            )
            workspace = Path(manifest["workspace_path"])
            workspace.mkdir(parents=True)
            snapshot = driver._capture_next_env(root, workspace)
            driver._write_private_json(
                workspace / driver.STATE_FILE,
                {
                    "namespace": manifest["namespace"],
                    "processes": [],
                    "postgres_data": str(workspace / "postgres-data"),
                    "next_env": snapshot,
                },
            )
            destination.write_text("generated\n", encoding="utf-8")
            self.assertTrue(driver._recover_stack(root, manifest, Path("pg_ctl")))
            self.assertEqual(destination.read_text(encoding="utf-8"), "tracked\n")
            self.assertFalse(workspace.exists())

    def test_postgres_stop_failure_is_not_treated_as_clean(self) -> None:
        failed = SimpleNamespace(returncode=1)
        with (
            tempfile.TemporaryDirectory() as temporary,
            mock.patch.object(driver, "_postgres_is_running", return_value=True),
            mock.patch.object(driver.subprocess, "run", return_value=failed),
        ):
            with self.assertRaises(driver.DriverError):
                driver._stop_postgres(
                    Path("pg_ctl"),
                    Path(temporary),
                    Path("socket"),
                    {"LC_ALL": "C"},
                )

    def test_prepare_validates_web_dependency_before_creating_runtime_state(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            manifest = allocate_manifest(
                root=root,
                namespace="dw-test-prepare",
                evidence_dir=root / "proof",
            )
            stack = driver.Stack(
                root=root,
                manifest=manifest,
                access_key="fixture-key",
                node=Path("node"),
                api_bin=root / "apps/api/.venv/bin",
                postgres_bins={"pg_ctl": Path("pg_ctl")},
            )
            with mock.patch.object(driver, "_port_closed", return_value=True):
                with self.assertRaisesRegex(
                    driver.DriverError, "web dependencies are absent"
                ):
                    stack.prepare()
            self.assertFalse(stack.workspace.exists())
            self.assertFalse(stack.socket_dir.exists())

    def test_stop_cleans_pre_snapshot_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            manifest = allocate_manifest(
                root=root,
                namespace="dw-test-pre-snapshot",
                evidence_dir=root / "proof",
            )
            stack = driver.Stack(
                root=root,
                manifest=manifest,
                access_key="fixture-key",
                node=Path("node"),
                api_bin=root / "apps/api/.venv/bin",
                postgres_bins={"pg_ctl": Path("pg_ctl")},
            )
            stack.workspace.mkdir(parents=True)
            stack.socket_dir.mkdir(mode=0o700)
            try:
                with (
                    mock.patch.object(driver, "_stop_postgres"),
                    mock.patch.object(driver, "_port_closed", return_value=True),
                ):
                    stack.stop()
            finally:
                if stack.socket_dir.is_dir():
                    stack.socket_dir.rmdir()
            self.assertFalse(stack.workspace.exists())
            self.assertFalse(stack.socket_dir.exists())

    def test_diagnostic_failure_does_not_prevent_any_stack_stop(self) -> None:
        first = mock.Mock(namespace="dw-test-a")
        second = mock.Mock(namespace="dw-test-b")
        with mock.patch.object(
            driver, "_copy_failure_logs", side_effect=OSError("copy failed")
        ):
            driver._cleanup_remaining(
                (first, second), set(), Path("unused"), passed=False
            )
        first.stop.assert_called_once_with()
        second.stop.assert_called_once_with()

    def test_failure_log_copy_does_not_follow_destination_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary)
            logs = sandbox / "logs"
            logs.mkdir()
            (logs / "api.log").write_text("bounded diagnostics\n", encoding="utf-8")
            evidence = sandbox / "evidence"
            diagnostic = evidence / "failure-logs/dw-test-a"
            diagnostic.mkdir(parents=True)
            victim = sandbox / "victim"
            victim.write_text("unchanged\n", encoding="utf-8")
            (diagnostic / "api.log").symlink_to(victim)
            stack = SimpleNamespace(logs=logs, namespace="dw-test-a")
            with self.assertRaises(FileExistsError):
                driver._copy_failure_logs(stack, evidence)
            self.assertEqual(victim.read_text(encoding="utf-8"), "unchanged\n")

    def test_browser_report_requires_exact_observed_schema(self) -> None:
        diagnostics = {
            "blockedNetworkProbes": [],
            "browserErrors": 0,
            "classifiedNavigationAborts": [],
        }

        def journey(label: str) -> dict[str, object]:
            prompt = f"Prepare isolated product-demo result for {label}"
            return {
                "diagnostics": {"desktop": diagnostics, "phone": diagnostics},
                "exportedBriefSha256": "a" * 64,
                "label": label,
                "liveProgressObserved": True,
                "ownStorageObserved": f"owned-by-{label}",
                "peerStorageObserved": None,
                "portableDownload": True,
                "prompt": prompt,
                "resultText": f"Objective: {prompt}\nNext actions:",
                "retainedEvidenceSha256": "b" * 64,
                "retainedEventsText": "Retained events11",
                "retainedResultSha256": "c" * 64,
                "selectedAgentId": "deepwork-fixture-planner",
                "sourceText": "local-runner evidence",
                "states": [
                    "sign-in",
                    "agent-choice",
                    "compose",
                    "plan-review",
                    "approved",
                    "running",
                    "result",
                    "evidence-files-trace",
                    "reopened",
                ],
                "taskPath": "/tasks/task_00000001",
                "viewports": ["1440x900", "390x844"],
            }

        report = {
            "schemaVersion": 1,
            "journeys": [journey("stack-a"), journey("stack-b")],
            "storageIsolation": [
                {
                    "sourceLabel": label,
                    "ownStorageObserved": f"shared-context-owned-by-{label}",
                    "peerStorageObserved": None,
                }
                for label in ("stack-a", "stack-b")
            ],
        }
        self.assertTrue(driver._journey_report_is_complete(report))
        report["journeys"][0]["liveProgressObserved"] = False
        self.assertFalse(driver._journey_report_is_complete(report))

    def test_browser_image_validation_requires_true_phone_viewport(self) -> None:
        def png_header(width: int, height: int) -> bytes:
            return (
                b"\x89PNG\r\n\x1a\n"
                + b"\x00\x00\x00\rIHDR"
                + width.to_bytes(4, "big")
                + height.to_bytes(4, "big")
            )

        with tempfile.TemporaryDirectory() as temporary:
            browser_root = Path(temporary)
            for label in ("stack-a", "stack-b"):
                cell = browser_root / label
                cell.mkdir()
                for name in ("desktop-completed", "reopened-after-api-restart-desktop"):
                    (cell / f"{name}.png").write_bytes(png_header(1440, 900))
                for name in ("phone-reopened", "reopened-after-api-restart-phone"):
                    (cell / f"{name}.png").write_bytes(png_header(390, 844))
            driver._validate_browser_images(browser_root)
            (browser_root / "stack-a/phone-reopened.png").write_bytes(
                png_header(390, 1389)
            )
            with self.assertRaisesRegex(
                driver.DriverError, "invalid viewport dimensions"
            ):
                driver._validate_browser_images(browser_root)


if __name__ == "__main__":
    unittest.main()
