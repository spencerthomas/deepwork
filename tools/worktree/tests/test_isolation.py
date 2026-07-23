from __future__ import annotations

import json
import multiprocessing
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock


WORKTREE_TOOL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKTREE_TOOL))

from isolation import (  # noqa: E402
    EvidenceError,
    IsolationError,
    OwnershipError,
    ReservationConflict,
    ReservationStore,
    UnsafeNamespace,
    allocate_manifest,
    assert_distinct,
    canonical_root,
    differing_dimensions,
    public_manifest,
    validate_evidence,
    validate_namespace,
    write_evidence,
)


FIXED_TOKEN_A = "a" * 43
FIXED_TOKEN_B = "b" * 43


def _reserve_in_process(
    state_dir: str,
    manifest: dict[str, object],
    barrier: multiprocessing.synchronize.Barrier,
    results: multiprocessing.queues.Queue,
) -> None:
    barrier.wait()
    try:
        ReservationStore(state_dir).reserve(manifest)
        results.put("won")
    except ReservationConflict:
        results.put("rejected")
    except Exception as error:  # pragma: no cover - returned to the parent assertion
        results.put(type(error).__name__)


class NamespaceTests(unittest.TestCase):
    def test_valid_namespace_is_unchanged(self) -> None:
        self.assertEqual(validate_namespace("dw-fixture-a1"), "dw-fixture-a1")

    def test_invalid_namespaces_are_rejected(self) -> None:
        invalid = [
            "",
            ".",
            "..",
            "../peer",
            "DW-UPPER",
            " leading",
            "trailing ",
            "double--dash",
            "trailing-",
            "-leading",
            "under_score",
            "/absolute",
            "é",
            "a" * 49,
        ]
        for namespace in invalid:
            with self.subTest(namespace=namespace):
                with self.assertRaises(UnsafeNamespace):
                    validate_namespace(namespace)

    def test_broad_workspace_roots_are_rejected(self) -> None:
        with self.assertRaises(IsolationError):
            canonical_root("/")
        with self.assertRaises(IsolationError):
            canonical_root(Path.home())


class ManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.sandbox = Path(self.temporary.name).resolve()
        self.root_a = self.sandbox / "root-a"
        self.root_b = self.sandbox / "root-b"
        self.root_a.mkdir()
        self.root_b.mkdir()

    def manifest(
        self, root: Path, namespace: str, token: str
    ) -> dict[str, object]:
        return allocate_manifest(
            root=root,
            namespace=namespace,
            evidence_dir=self.sandbox / "evidence",
            teardown_token=token,
        )

    def test_manifest_is_complete_and_deterministic(self) -> None:
        left = self.manifest(self.root_a, "dw-test-a", FIXED_TOKEN_A)
        right = self.manifest(self.root_a, "dw-test-a", FIXED_TOKEN_A)
        self.assertEqual(left, right)
        self.assertEqual(
            {
                "workspace_path",
                "ports",
                "database",
                "schema",
                "object_prefix",
                "browser",
                "telemetry",
                "logs_path",
                "proof_path",
                "process_identities",
            }.difference(left),
            set(),
        )
        self.assertEqual(len(set(left["ports"].values())), 4)
        self.assertEqual(left["browser"]["origin"].split(":")[0], "http")
        self.assertIn("127.0.0.1", left["browser"]["origin"])
        self.assertNotIn("0.0.0.0", left["browser"]["origin"])

    def test_all_peer_dimensions_differ(self) -> None:
        left = self.manifest(self.root_a, "dw-test-a", FIXED_TOKEN_A)
        right = self.manifest(self.root_b, "dw-test-b", FIXED_TOKEN_B)
        self.assertTrue(all(differing_dimensions(left, right).values()))
        assert_distinct(left, right)

    def test_any_port_overlap_is_a_conflict(self) -> None:
        left = self.manifest(self.root_a, "dw-test-a", FIXED_TOKEN_A)
        right = self.manifest(self.root_b, "dw-test-b", FIXED_TOKEN_B)
        right["ports"]["api"] = left["ports"]["worker"]
        self.assertFalse(differing_dimensions(left, right)["ports"])
        with self.assertRaises(ReservationConflict):
            assert_distinct(left, right)

    def test_public_manifest_drops_capability_and_local_paths(self) -> None:
        manifest = self.manifest(self.root_a, "dw-test-a", FIXED_TOKEN_A)
        public = public_manifest(manifest)
        serialized = json.dumps(public)
        self.assertNotIn("teardown_token", public)
        self.assertNotIn(FIXED_TOKEN_A, serialized)
        self.assertNotIn(str(self.sandbox), serialized)
        self.assertEqual(public["workspace_id"], "synthetic-workspace-dw-test-a")


class ReservationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.sandbox = Path(self.temporary.name).resolve()
        self.root_a = self.sandbox / "root-a"
        self.root_b = self.sandbox / "root-b"
        self.root_a.mkdir()
        self.root_b.mkdir()
        self.store = ReservationStore(self.sandbox / "state")
        self.manifest_a = allocate_manifest(
            root=self.root_a,
            namespace="dw-test-a",
            evidence_dir=self.sandbox / "proof",
            teardown_token=FIXED_TOKEN_A,
        )
        self.manifest_b = allocate_manifest(
            root=self.root_b,
            namespace="dw-test-b",
            evidence_dir=self.sandbox / "proof",
            teardown_token=FIXED_TOKEN_B,
        )

    def test_atomic_duplicate_reservation_has_one_winner(self) -> None:
        barrier = threading.Barrier(8)
        outcomes: list[str] = []
        mutex = threading.Lock()

        def attempt() -> None:
            barrier.wait()
            try:
                self.store.reserve(self.manifest_a)
                result = "won"
            except ReservationConflict:
                result = "rejected"
            with mutex:
                outcomes.append(result)

        threads = [threading.Thread(target=attempt) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(outcomes.count("won"), 1)
        self.assertEqual(outcomes.count("rejected"), 7)

    def test_cross_process_duplicate_reservation_has_one_winner(self) -> None:
        context = multiprocessing.get_context("fork")
        barrier = context.Barrier(6)
        results = context.Queue()
        processes = [
            context.Process(
                target=_reserve_in_process,
                args=(
                    str(self.store.state_dir),
                    self.manifest_a,
                    barrier,
                    results,
                ),
            )
            for _ in range(6)
        ]
        for process in processes:
            process.start()
        for process in processes:
            process.join(timeout=10)
            self.assertEqual(process.exitcode, 0)
        outcomes = [results.get(timeout=2) for _ in processes]
        self.assertEqual(outcomes.count("won"), 1)
        self.assertEqual(outcomes.count("rejected"), 5)

    def test_cross_namespace_resource_collision_is_rejected(self) -> None:
        self.store.reserve(self.manifest_a)
        self.manifest_b["ports"]["api"] = self.manifest_a["ports"]["web"]
        with self.assertRaises(ReservationConflict):
            self.store.reserve(self.manifest_b)
        self.assertEqual(
            self.store.active_namespaces(),
            ("dw-test-a",),
        )

    def test_restart_requires_exact_owner_and_reuses_manifest(self) -> None:
        self.store.reserve(self.manifest_a)
        with self.assertRaises(OwnershipError):
            self.store.restart(
                namespace="dw-test-a",
                teardown_token=FIXED_TOKEN_B,
                root=self.root_a,
            )
        restarted = self.store.restart(
            namespace="dw-test-a",
            teardown_token=FIXED_TOKEN_A,
            root=self.root_a,
        )
        self.assertEqual(restarted, self.manifest_a)

    def test_teardown_is_exact_idempotent_and_preserves_peer(self) -> None:
        self.store.reserve(self.manifest_a)
        self.store.reserve(self.manifest_b)
        with self.assertRaises(OwnershipError):
            self.store.teardown(
                namespace="dw-test-b",
                teardown_token=FIXED_TOKEN_A,
                root=self.root_b,
            )
        released = self.store.teardown(
            namespace="dw-test-a",
            teardown_token=FIXED_TOKEN_A,
            root=self.root_a,
        )
        self.assertEqual(released.state, "released")
        self.assertEqual(
            self.store.active_namespaces(),
            ("dw-test-b",),
        )
        repeated = self.store.teardown(
            namespace="dw-test-a",
            teardown_token=FIXED_TOKEN_A,
            root=self.root_a,
        )
        self.assertEqual(repeated.state, "already-absent")
        tombstone = (
            self.store.state_dir / "dw-test-a.released.json"
        ).read_text(encoding="utf-8")
        self.assertNotIn(FIXED_TOKEN_A, tombstone)

    def test_pair_release_recovers_after_second_unlink_failure(self) -> None:
        self.store.reserve(self.manifest_a)
        self.store.reserve(self.manifest_b)
        release_id = "c" * 32
        calls = 0

        def fail_second(path: Path) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("injected second release failure")
            path.unlink()

        with mock.patch(
            "isolation._unlink_reservation", side_effect=fail_second
        ):
            with self.assertRaisesRegex(
                OSError, "injected second release failure"
            ):
                self.store.release_pair(
                    release_id=release_id,
                    namespace_a="dw-test-a",
                    teardown_token_a=FIXED_TOKEN_A,
                    root_a=self.root_a,
                    namespace_b="dw-test-b",
                    teardown_token_b=FIXED_TOKEN_B,
                    root_b=self.root_b,
                )

        self.assertEqual(self.store.active_namespaces(), ("dw-test-b",))
        self.assertTrue(
            self.store.release_pair_pending(release_id=release_id)
        )
        results = self.store.commit_pair_release(release_id=release_id)
        self.assertEqual(
            [result.state for result in results],
            ["already-absent", "released"],
        )
        self.assertEqual(self.store.active_namespaces(), ())
        self.assertFalse(
            self.store.release_pair_pending(release_id=release_id)
        )

    def test_corrupt_reservation_fails_closed(self) -> None:
        self.store.state_dir.mkdir(parents=True)
        (self.store.state_dir / "dw-broken.json").write_text("{", encoding="utf-8")
        with self.assertRaises(IsolationError):
            self.store.active_namespaces()

    def test_reservation_state_rejects_symlink_and_broad_permissions(self) -> None:
        target = self.sandbox / "state-target"
        target.mkdir(mode=0o700)
        link = self.sandbox / "state-link"
        link.symlink_to(target, target_is_directory=True)
        with self.assertRaises(IsolationError):
            ReservationStore(link)

        broad = self.sandbox / "state-broad"
        broad.mkdir(mode=0o700)
        broad.chmod(0o755)
        with self.assertRaises(IsolationError):
            ReservationStore(broad).active_namespaces()

    def test_reservation_state_rejects_wrong_owner(self) -> None:
        state = self.sandbox / "state-owner"
        state.mkdir(mode=0o700)
        store = ReservationStore(state)
        with mock.patch("isolation.os.geteuid", return_value=os.geteuid() + 1):
            with self.assertRaises(IsolationError):
                store.active_namespaces()

    def test_teardown_refuses_symlink_fixture_path(self) -> None:
        target = self.sandbox / "outside"
        target.mkdir()
        logs = Path(self.manifest_a["logs_path"])
        logs.parent.mkdir(parents=True)
        logs.symlink_to(target, target_is_directory=True)
        self.store.reserve(self.manifest_a)
        with self.assertRaises(OwnershipError):
            self.store.teardown(
                namespace="dw-test-a",
                teardown_token=FIXED_TOKEN_A,
                root=self.root_a,
                remove_fixture_paths=True,
            )
        self.assertTrue(target.exists())
        self.assertEqual(self.store.active_namespaces(), ("dw-test-a",))


class EvidenceTests(unittest.TestCase):
    def test_credential_like_content_is_rejected(self) -> None:
        unsafe_values = [
            {"secret": "canary"},
            {"authRef": "fixture-ref"},
            {"nested": {"customer": "value"}},
            {"environment_variables": {"SAFE": "still-not-retained"}},
            {"message": "Authorization: Bearer abcdefghijklmnop"},
            {"message": "sk-abcdefghijklmnop"},
            {"message": "ghp_abcdefghijklmnopqrstuvwxyz123456"},
            {"message": "github_pat_abcdefghijklmnopqrstuvwxyz_123456"},
            {"message": "AKIAABCDEFGHIJKLMNOP"},
            {"message": "-----BEGIN PRIVATE KEY-----"},
            {"message": "/Users/example/private/project"},
            {"raw_response": {"status": "synthetic"}},
            {"upstream_payload": {"item": "synthetic"}},
            {"provider_response": {"status": "synthetic"}},
        ]
        for value in unsafe_values:
            with self.subTest(value=value):
                with self.assertRaises(EvidenceError):
                    validate_evidence(value)

    def test_synthetic_evidence_writes_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary).resolve() / "nested" / "proof.json"
            write_evidence(path, {"status": "passed", "namespace": "dw-test-a"})
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8"))["status"], "passed"
            )
            self.assertEqual(list(path.parent.glob("*.tmp")), [])

    def test_evidence_symlink_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary).resolve()
            target = sandbox / "target"
            target.mkdir()
            link = sandbox / "link"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaises(EvidenceError):
                write_evidence(link / "proof.json", {"status": "passed"})

    def test_evidence_nested_symlink_ancestor_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary).resolve()
            target = sandbox / "target"
            existing = target / "existing"
            existing.mkdir(parents=True)
            link = sandbox / "link"
            link.symlink_to(target, target_is_directory=True)
            destination = link / "existing" / "nested" / "proof.json"
            self.assertFalse(destination.parent.exists())
            self.assertTrue((link / "existing").exists())
            self.assertFalse((link / "existing").is_symlink())
            with self.assertRaises(EvidenceError):
                write_evidence(destination, {"status": "passed"})


if __name__ == "__main__":
    unittest.main()
