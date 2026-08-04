from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
