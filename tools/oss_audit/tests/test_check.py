"""Intentional-drift tests for the OSS license and trademark audit."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.oss_audit.check import audit


class OssAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "apps" / "api").mkdir(parents=True)
        (self.root / "packages" / "ui").mkdir(parents=True)
        (self.root / ".github" / "workflows").mkdir(parents=True)
        for filename in ("CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md"):
            (self.root / filename).write_text(f"# {filename}\n", encoding="utf-8")
        (self.root / "LICENSE").write_text(
            'MIT License\nPermission is hereby granted, free of charge\nTHE SOFTWARE IS PROVIDED "AS IS"\n',
            encoding="utf-8",
        )
        (self.root / "README.md").write_text(
            "Portions Copyright (c) LangChain, Inc.\n"
            "Not affiliated with, endorsed by, or sponsored by LangChain, Inc.\n"
            "The Elastic License 2.0 runtime boundary means this project never vendors or redistributes langgraph-api.\n",
            encoding="utf-8",
        )
        (self.root / "package.json").write_text(json.dumps({"name": "deepwork", "license": "MIT"}), encoding="utf-8")
        (self.root / "packages" / "ui" / "package.json").write_text(
            json.dumps({"name": "@deepwork/ui", "license": "MIT"}), encoding="utf-8"
        )
        (self.root / "apps" / "api" / "pyproject.toml").write_text(
            '[project]\nname = "deepwork-api"\nlicense = { text = "MIT" }\n', encoding="utf-8"
        )
        (self.root / ".github" / "workflows" / "checks.yml").write_text(
            "steps:\n  - uses: actions/checkout@0123456789abcdef0123456789abcdef01234567\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_minimal_repository_passes(self) -> None:
        findings, report = audit(self.root)
        self.assertEqual(findings, [])
        self.assertEqual(report["status"], "pass")

    def test_missing_legal_boundary_has_specific_diagnostic(self) -> None:
        (self.root / "README.md").write_text("Portions Copyright (c) LangChain, Inc.\n", encoding="utf-8")
        findings, _ = audit(self.root)
        messages = {item.message for item in findings if item.code == "missing-readme-boundary"}
        self.assertTrue(any("runtime-license" in message for message in messages))
        self.assertTrue(any("non-affiliation" in message for message in messages))

    def test_manifest_and_action_drift_fail_closed(self) -> None:
        (self.root / "packages" / "ui" / "package.json").write_text(
            json.dumps({"name": "@deepwork/ui"}), encoding="utf-8"
        )
        (self.root / ".github" / "workflows" / "checks.yml").write_text(
            "steps:\n  - uses: actions/checkout@v5\n", encoding="utf-8"
        )
        findings, _ = audit(self.root)
        self.assertIn("missing-package-license", {item.code for item in findings})
        self.assertIn("unpinned-action", {item.code for item in findings})

    def test_restricted_assets_are_rejected(self) -> None:
        asset = self.root / "packages" / "ui" / "LangChain-logo.svg"
        font = self.root / "packages" / "ui" / "TWK-Lausanne.woff2"
        asset.write_text("<svg/>", encoding="utf-8")
        font.write_bytes(b"font")
        findings, _ = audit(self.root)
        codes = {item.code for item in findings}
        self.assertIn("restricted-provider-asset", codes)
        self.assertIn("restricted-font-asset", codes)


if __name__ == "__main__":
    unittest.main()
