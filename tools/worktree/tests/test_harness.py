from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


WORKTREE_TOOL = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKTREE_TOOL))

import harness  # noqa: E402
from isolation import ReservationStore, allocate_manifest, public_manifest  # noqa: E402

class HarnessCommandTests(unittest.TestCase):
    def run_main(self, arguments: list[str]) -> tuple[int, dict[str, object]]:
        output = io.StringIO()
        with redirect_stdout(output):
            status = harness.main(arguments)
        return status, json.loads(output.getvalue())

    def test_doctor_reports_harness_ready_but_spike_not_accepted(self) -> None:
        status, output = self.run_main(["doctor", "--root", str(REPOSITORY_ROOT)])
        self.assertEqual(status, 0)
        self.assertEqual(output["harness"], "ready")
        self.assertFalse(output["product_demo"]["available"])
        self.assertEqual(
            output["spike_worktree_001"], "implemented-not-accepted"
        )

    def test_driver_path_is_never_executed_without_static_reviewed_contract(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "AGENTS.md").write_text("fixture\n", encoding="utf-8")
            (root / ".git").mkdir()
            driver = root / harness.PRODUCT_DEMO_DRIVER
            driver.parent.mkdir(parents=True)
            marker = root / "executed"
            driver.write_text(
                (
                    "from pathlib import Path\n"
                    f"Path({str(marker)!r}).write_text('executed')\n"
                ),
                encoding="utf-8",
            )
            status = harness._driver_status(root)
            self.assertFalse(status["available"])
            self.assertFalse(marker.exists())

    def test_static_contract_pins_driver_content_and_reviewed_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "AGENTS.md").write_text("fixture\n", encoding="utf-8")
            (root / ".git").mkdir()
            driver = root / harness.PRODUCT_DEMO_DRIVER
            driver.parent.mkdir(parents=True)
            driver.write_text("raise SystemExit('must not execute')\n", encoding="utf-8")
            contract = {
                "contract_version": harness.PRODUCT_DEMO_CONTRACT_VERSION,
                "protocol": harness.PRODUCT_DEMO_PROTOCOL,
                "driver_path": harness.PRODUCT_DEMO_DRIVER.as_posix(),
                "driver_sha256": harness._sha256_file(driver),
                "reviewed_repository_commit": "a" * 40,
                "components": sorted(harness.REQUIRED_PRODUCT_DEMO_COMPONENTS),
                "credential_free": True,
                "loopback_only": True,
            }
            contract_path = root / harness.PRODUCT_DEMO_CONTRACT
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            reviewed_driver = driver.read_bytes()
            reviewed_contract = contract_path.read_bytes()

            def reviewed_blob(
                _root: Path, _commit: str, relative: Path
            ) -> bytes:
                if relative == harness.PRODUCT_DEMO_DRIVER:
                    return reviewed_driver
                return reviewed_contract

            with mock.patch(
                "harness._reviewed_commit_is_ancestor", return_value=True
            ), mock.patch("harness._git_blob", side_effect=reviewed_blob):
                self.assertTrue(harness._driver_status(root)["available"])
                driver.write_text("raise SystemExit('tampered')\n", encoding="utf-8")
                status = harness._driver_status(root)
            self.assertFalse(status["available"])
            self.assertIn("SHA-256", status["reason"])

            driver.write_bytes(reviewed_driver)
            contract["components"] = list(reversed(contract["components"]))
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            with mock.patch(
                "harness._reviewed_commit_is_ancestor", return_value=True
            ), mock.patch("harness._git_blob", side_effect=reviewed_blob):
                status = harness._driver_status(root)
            self.assertFalse(status["available"])
            self.assertIn("contract semantics", status["reason"])

    def test_self_test_retains_sanitized_fixture_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence_dir = Path(temporary) / "evidence"
            status, output = self.run_main(
                [
                    "self-test",
                    "--root",
                    str(REPOSITORY_ROOT),
                    "--fixtures",
                    str(REPOSITORY_ROOT / "internal/fixtures/worktree"),
                    "--evidence-dir",
                    str(evidence_dir),
                ]
            )
            self.assertEqual(status, 0)
            self.assertEqual(output["acceptance"], "implemented-not-accepted")
            self.assertEqual(output["evidence"], "self-test.json")
            evidence_text = (evidence_dir / "self-test.json").read_text(
                encoding="utf-8"
            )
            evidence = json.loads(evidence_text)
            self.assertEqual(evidence["evidence_class"], "synthetic-fixture")
            self.assertNotIn("teardown_token", evidence_text)
            self.assertNotIn(str(Path.home()), evidence_text)
            self.assertNotIn("authRef", evidence_text)
            self.assertTrue(all(evidence["checks"].values()))

    def test_display_path_is_relative_inside_current_workspace(self) -> None:
        path = Path.cwd() / "synthetic-evidence" / "self-test.json"
        self.assertEqual(
            harness._display_path(path),
            "synthetic-evidence/self-test.json",
        )

    def test_exercise_missing_peer_blocks_before_startup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence_dir = Path(temporary) / "evidence"
            status, output = self.run_main(
                [
                    "exercise",
                    "--root",
                    str(REPOSITORY_ROOT),
                    "--peer-root",
                    str(Path(temporary) / "missing-peer"),
                    "--namespace-a",
                    "dw-iso-a",
                    "--namespace-b",
                    "dw-iso-b",
                    "--evidence-dir",
                    str(evidence_dir),
                ]
            )
            self.assertEqual(status, harness.EXIT_BLOCKED)
            self.assertEqual(output["status"], "blocked")
            evidence = json.loads(
                (evidence_dir / "exercise.json").read_text(encoding="utf-8")
            )
            self.assertEqual(evidence["processes_started"], 0)
            self.assertEqual(evidence["resources_reserved"], 0)
            self.assertEqual(evidence["acceptance"], "implemented-not-accepted")

    def test_exercise_missing_product_driver_blocks_with_two_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary)
            peer = sandbox / "peer"
            peer.mkdir()
            evidence_dir = sandbox / "evidence"
            status, output = self.run_main(
                [
                    "exercise",
                    "--root",
                    str(REPOSITORY_ROOT),
                    "--peer-root",
                    str(peer),
                    "--namespace-a",
                    "dw-iso-a",
                    "--namespace-b",
                    "dw-iso-b",
                    "--evidence-dir",
                    str(evidence_dir),
                ]
            )
            self.assertEqual(status, harness.EXIT_BLOCKED)
            self.assertEqual(len(output["reasons"]), 2)
            self.assertTrue(
                all(
                    (
                        "static reviewed product-demo contract" in reason
                        or "repository identity markers" in reason
                    )
                    for reason in output["reasons"]
                )
            )

    def test_verify_rejects_fixture_or_blocker_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence_dir = Path(temporary)
            fixture = json.loads(
                (
                    REPOSITORY_ROOT
                    / "internal/fixtures/worktree/blocked-exercise.json"
                ).read_text(encoding="utf-8")
            )
            (evidence_dir / "exercise.json").write_text(
                json.dumps(fixture), encoding="utf-8"
            )
            status, output = self.run_main(
                [
                    "verify",
                    "--evidence-dir",
                    str(evidence_dir),
                    "--require-no-cross-observation",
                    "--require-clean-teardown",
                ]
            )
            self.assertEqual(status, harness.EXIT_VERIFY_FAILED)
            self.assertEqual(output["status"], "failed")
            self.assertTrue(
                any("product evidence" in failure for failure in output["failures"])
            )

    def _valid_evidence(self, sandbox: Path) -> dict[str, object]:
        root_a = sandbox / "a"
        root_b = sandbox / "b"
        root_a.mkdir()
        root_b.mkdir()
        manifests = [
            public_manifest(
                allocate_manifest(
                    root=root,
                    namespace=namespace,
                    evidence_dir=sandbox / "proof",
                    teardown_token=character * 43,
                )
            )
            for root, namespace, character in (
                (root_a, "dw-iso-a", "a"),
                (root_b, "dw-iso-b", "b"),
            )
        ]
        namespaces = ["dw-iso-a", "dw-iso-b"]
        run_nonce = "1" * 32
        driver_revision = "2" * 40
        driver_sha256 = "3" * 64
        contract_semantic_sha256 = "4" * 64

        def bound(kind: str, payload: object) -> str:
            return harness._bound_digest(
                kind=kind,
                payload=payload,
                run_nonce=run_nonce,
                driver_revision=driver_revision,
                driver_sha256=driver_sha256,
            )

        allocation_digests = {
            manifest["namespace"]: bound("allocation", manifest)
            for manifest in manifests
        }
        observations = []
        for source, target in (
            ("dw-iso-a", "dw-iso-b"),
            ("dw-iso-b", "dw-iso-a"),
        ):
            for dimension in sorted(harness.PROBE_DIMENSIONS):
                record = {
                    "source_namespace": source,
                    "target_namespace": target,
                    "dimension": dimension,
                    "result": "not-observed",
                    "probe_id": (
                        f"probe-{source[-1]}-{target[-1]}-"
                        f"{dimension.replace('_', '-')}"
                    ),
                }
                record["result_digest"] = bound("cross-observation", record)
                observations.append(record)
        restarts = []
        for namespace in namespaces:
            record = {
                "namespace": namespace,
                "rule": "reuse-reserved-resources-with-exact-teardown-token",
                "allocation_fingerprint_before": allocation_digests[namespace],
                "allocation_fingerprint_after": allocation_digests[namespace],
                "process_identity_before": f"{namespace}-process-1",
                "process_identity_after": f"{namespace}-process-2",
            }
            record["restart_digest"] = bound("restart", record)
            restarts.append(record)
        teardown = []
        for index, namespace in enumerate(namespaces, start=1):
            record = {
                "namespace": namespace,
                "order": index,
                "peer_survived_after": index == 1,
                "resources_absent": sorted(harness.TEARDOWN_RESOURCES),
                "reservation_absent": True,
            }
            record["cleanup_digest"] = bound("cleanup", record)
            teardown.append(record)
        return {
            "schema_version": 1,
            "evidence_class": "product-demo",
            "status": "passed",
            "acceptance": "accepted",
            "exercise_id": "dw-product-demo-001",
            "run_nonce": run_nonce,
            "driver_revision": driver_revision,
            "driver_sha256": driver_sha256,
            "contract_semantic_sha256": contract_semantic_sha256,
            "namespaces": namespaces,
            "manifests": manifests,
            "allocation_digests": allocation_digests,
            "concurrency": {
                "a_started_at": "2026-07-23T01:00:00Z",
                "b_started_at": "2026-07-23T01:00:01Z",
                "a_ready_at": "2026-07-23T01:00:02Z",
                "b_ready_at": "2026-07-23T01:00:03Z",
                "a_stopped_at": "2026-07-23T01:00:10Z",
                "b_stopped_at": "2026-07-23T01:00:11Z",
            },
            "cross_observations": observations,
            "restarts": restarts,
            "teardown": teardown,
        }

    def test_verify_accepts_complete_structured_product_demo_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary).resolve()
            evidence = self._valid_evidence(sandbox)
            evidence_dir = sandbox / "evidence"
            evidence_dir.mkdir()
            (evidence_dir / "exercise.json").write_text(
                json.dumps(evidence), encoding="utf-8"
            )
            store = ReservationStore(sandbox / "state")
            receipt_record = store.create_receipt_record(
                run_nonce=evidence["run_nonce"],
                driver_revision=evidence["driver_revision"],
                driver_sha256=evidence["driver_sha256"],
                contract_semantic_sha256=evidence[
                    "contract_semantic_sha256"
                ],
                namespaces=evidence["namespaces"],
            )
            receipt = harness._build_receipt(
                evidence=evidence,
                evidence_path=evidence_dir / "exercise.json",
                receipt_record=receipt_record,
                reservation_release=[
                    {"namespace": "dw-iso-a", "state": "released"},
                    {"namespace": "dw-iso-b", "state": "released"},
                ],
            )
            (evidence_dir / "receipt.json").write_text(
                json.dumps(receipt), encoding="utf-8"
            )
            driver_status = {
                "available": True,
                "reviewed_repository_commit": evidence["driver_revision"],
                "driver_sha256": evidence["driver_sha256"],
                "contract_semantic_sha256": evidence[
                    "contract_semantic_sha256"
                ],
            }
            with mock.patch(
                "harness._driver_status", return_value=driver_status
            ), mock.patch("harness.ReservationStore", return_value=store):
                status, output = self.run_main(
                    [
                        "verify",
                        "--evidence-dir",
                        str(evidence_dir),
                        "--require-no-cross-observation",
                        "--require-clean-teardown",
                    ]
                )
            self.assertEqual(status, 0, output)
            self.assertEqual(output["status"], "passed")

    def test_verify_rejects_digest_bound_evidence_tampering(self) -> None:
        mutations = {
            "probe": lambda evidence: evidence["cross_observations"][0].__setitem__(
                "result", "observed"
            ),
            "allocation": lambda evidence: evidence["manifests"][0].__setitem__(
                "database", "tampered_database"
            ),
            "restart": lambda evidence: evidence["restarts"][0].__setitem__(
                "process_identity_after", "tampered-process"
            ),
            "cleanup": lambda evidence: evidence["teardown"][0].__setitem__(
                "cleanup_digest", "0" * 64
            ),
            "nonce": lambda evidence: evidence.__setitem__("run_nonce", "4" * 32),
            "driver": lambda evidence: evidence.__setitem__(
                "driver_revision", "5" * 40
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                evidence = self._valid_evidence(Path(temporary).resolve())
                mutate(evidence)
                failures = harness._product_demo_failures(
                    evidence,
                    require_no_cross_observation=True,
                    require_clean_teardown=True,
                )
                self.assertTrue(failures, name)

    def test_strict_evidence_schemas_reject_unknown_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary).resolve()
            evidence = self._valid_evidence(sandbox)
            evidence["account"] = "synthetic"
            failures = harness._product_demo_failures(
                evidence,
                require_no_cross_observation=True,
                require_clean_teardown=True,
            )
            self.assertTrue(any("unknown fields: account" in item for item in failures))

            nested = sandbox / "nested"
            nested.mkdir()
            evidence = self._valid_evidence(nested)
            evidence["manifests"][0]["provider_response"] = {}
            failures = harness._product_demo_failures(
                evidence,
                require_no_cross_observation=True,
                require_clean_teardown=True,
            )
            self.assertTrue(
                any("unknown fields: provider_response" in item for item in failures)
            )

            self.assertTrue(
                harness._exact_keys(
                    {**{key: None for key in harness.BLOCKER_KEYS}, "customer": "x"},
                    harness.BLOCKER_KEYS,
                    "blocker evidence",
                )
            )
            self.assertTrue(
                harness._exact_keys(
                    {**{key: None for key in harness.SELF_TEST_KEYS}, "source": "x"},
                    harness.SELF_TEST_KEYS,
                    "self-test evidence",
                )
            )
            self.assertTrue(
                harness._exact_keys(
                    {**{key: None for key in harness.RECEIPT_KEYS}, "account": "x"},
                    harness.RECEIPT_KEYS,
                    "receipt",
                )
            )
            manifest = evidence["manifests"][0]
            manifest["telemetry"]["resource_attributes"]["source"] = "x"
            self.assertTrue(
                any(
                    "unknown fields: source" in failure
                    for failure in harness._shape_failures(
                        manifest,
                        harness.PUBLIC_MANIFEST_SCHEMA,
                        "self-test manifest[0]",
                    )
                )
            )

    def test_receipt_requires_exact_released_namespaces(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary).resolve()
            evidence = self._valid_evidence(sandbox)
            evidence_dir = sandbox / "evidence"
            evidence_dir.mkdir()
            evidence_path = evidence_dir / "exercise.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            store = ReservationStore(sandbox / "state")
            receipt_record = store.create_receipt_record(
                run_nonce=evidence["run_nonce"],
                driver_revision=evidence["driver_revision"],
                driver_sha256=evidence["driver_sha256"],
                contract_semantic_sha256=evidence[
                    "contract_semantic_sha256"
                ],
                namespaces=evidence["namespaces"],
            )
            receipt = harness._build_receipt(
                evidence=evidence,
                evidence_path=evidence_path,
                receipt_record=receipt_record,
                reservation_release=[
                    {"namespace": "dw-iso-a", "state": "released"},
                    {"namespace": "dw-other", "state": "released"},
                ],
            )
            (evidence_dir / "receipt.json").write_text(
                json.dumps(receipt), encoding="utf-8"
            )
            with mock.patch(
                "harness._driver_status",
                return_value={
                    "available": True,
                    "reviewed_repository_commit": evidence["driver_revision"],
                    "driver_sha256": evidence["driver_sha256"],
                    "contract_semantic_sha256": evidence[
                        "contract_semantic_sha256"
                    ],
                },
            ):
                failures = harness._receipt_failures(
                    evidence_dir=evidence_dir, evidence=evidence, store=store
                )
            self.assertIn(
                "harness receipt releases do not match evidence namespaces",
                failures,
            )
            receipt["receipt_hmac"] = "0" * 64
            (evidence_dir / "receipt.json").write_text(
                json.dumps(receipt), encoding="utf-8"
            )
            failures = harness._receipt_failures(
                evidence_dir=evidence_dir, evidence=evidence, store=store
            )
            self.assertIn(
                "harness receipt HMAC does not prove reviewed execution",
                failures,
            )
            missing_authority = ReservationStore(sandbox / "other-state")
            failures = harness._receipt_failures(
                evidence_dir=evidence_dir,
                evidence=evidence,
                store=missing_authority,
            )
            self.assertIn(
                "private harness receipt authority is unavailable",
                failures,
            )

    def test_reviewed_cleanup_failure_retains_then_retry_releases(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary).resolve()
            root_a = sandbox / "root-a"
            root_b = sandbox / "root-b"
            root_a.mkdir()
            root_b.mkdir()
            evidence_dir = sandbox / "evidence"
            evidence_dir.mkdir()
            store = ReservationStore(sandbox / "state")
            manifest_a = allocate_manifest(
                root=root_a,
                namespace="dw-recover-a",
                evidence_dir=evidence_dir,
                teardown_token="a" * 43,
            )
            manifest_b = allocate_manifest(
                root=root_b,
                namespace="dw-recover-b",
                evidence_dir=evidence_dir,
                teardown_token="b" * 43,
            )
            store.reserve(manifest_a)
            store.reserve(manifest_b)
            path_a = store.owned_manifest_path(
                namespace="dw-recover-a",
                teardown_token=manifest_a["teardown_token"],
                root=root_a,
            )
            path_b = store.owned_manifest_path(
                namespace="dw-recover-b",
                teardown_token=manifest_b["teardown_token"],
                root=root_b,
            )
            context = {
                "run_nonce": "1" * 32,
                "driver_revision": "2" * 40,
                "driver_sha256": "3" * 64,
                "contract_semantic_sha256": "4" * 64,
            }

            def cleanup_evidence(*, unknown: bool) -> dict[str, object]:
                records = []
                for namespace in ("dw-recover-a", "dw-recover-b"):
                    record = {
                        "namespace": namespace,
                        "process_identity_verified": True,
                        "resources_absent": sorted(harness.TEARDOWN_RESOURCES),
                    }
                    record["cleanup_digest"] = harness._bound_digest(
                        kind="recovery-cleanup",
                        payload=record,
                        run_nonce=context["run_nonce"],
                        driver_revision=context["driver_revision"],
                        driver_sha256=context["driver_sha256"],
                    )
                    records.append(record)
                value = {
                    "schema_version": 1,
                    "evidence_class": "product-demo-cleanup",
                    "status": "clean",
                    "namespaces": ["dw-recover-a", "dw-recover-b"],
                    "records": records,
                    **context,
                }
                if unknown:
                    value["provider_response"] = {}
                return value

            def run_with_cleanup(unknown: bool) -> subprocess.CompletedProcess:
                (evidence_dir / "recovery-cleanup.json").write_text(
                    json.dumps(cleanup_evidence(unknown=unknown)),
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess([], 0)

            arguments = {
                "root": root_a,
                "peer_root": root_b,
                "namespace_a": "dw-recover-a",
                "namespace_b": "dw-recover-b",
                "evidence_dir": evidence_dir,
                "store": store,
                "manifest_path_a": path_a,
                "manifest_path_b": path_b,
                "manifest_a": manifest_a,
                "manifest_b": manifest_b,
                **context,
            }
            with mock.patch(
                "harness.subprocess.run",
                side_effect=lambda *args, **kwargs: run_with_cleanup(True),
            ):
                self.assertFalse(harness._attempt_reviewed_cleanup(**arguments))
            self.assertEqual(
                store.active_namespaces(), ("dw-recover-a", "dw-recover-b")
            )

            with mock.patch(
                "harness.subprocess.run",
                side_effect=lambda *args, **kwargs: run_with_cleanup(False),
            ):
                self.assertTrue(harness._attempt_reviewed_cleanup(**arguments))
            self.assertEqual(store.active_namespaces(), ())

    def test_verify_detects_missing_probe_and_nonconcurrent_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence = self._valid_evidence(Path(temporary).resolve())
            evidence["concurrency"] = {
                "a_started_at": "2026-07-23T01:00:00Z",
                "a_ready_at": "2026-07-23T01:00:01Z",
                "a_stopped_at": "2026-07-23T01:00:02Z",
                "b_started_at": "2026-07-23T01:00:03Z",
                "b_ready_at": "2026-07-23T01:00:04Z",
                "b_stopped_at": "2026-07-23T01:00:05Z",
            }
            evidence["cross_observations"] = []
            failures = harness._product_demo_failures(
                evidence,
                require_no_cross_observation=True,
                require_clean_teardown=True,
            )
        self.assertIn("product-demo stacks were not concurrently ready", failures)
        self.assertIn("bidirectional cross-observation matrix is incomplete", failures)


if __name__ == "__main__":
    unittest.main()
