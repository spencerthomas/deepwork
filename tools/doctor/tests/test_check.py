"""Root toolchain-version contract tests."""

from __future__ import annotations

import unittest

from tools.doctor.check import (
    NODE_MAXIMUM,
    NODE_MINIMUM,
    PNPM_REQUIRED,
    parse_version,
    validate_node_version,
    validate_pnpm_version,
)


class ToolchainVersionTests(unittest.TestCase):
    def test_node_accepts_only_the_supported_range(self) -> None:
        self.assertEqual(NODE_MINIMUM, (24, 14, 0))
        self.assertEqual(NODE_MAXIMUM, (25, 0, 0))
        self.assertIsNone(validate_node_version("v24.14.0"))
        self.assertIsNone(validate_node_version("v24.19.0"))
        self.assertIsNotNone(validate_node_version("v24.13.9"))
        self.assertIsNotNone(validate_node_version("v25.0.0"))
        self.assertIsNotNone(validate_node_version("v20.18.0"))

    def test_pnpm_requires_the_pinned_package_manager_version(self) -> None:
        self.assertEqual(PNPM_REQUIRED, (11, 9, 0))
        self.assertIsNone(validate_pnpm_version("11.9.0"))
        self.assertIsNotNone(validate_pnpm_version("9.12.1"))
        self.assertIsNotNone(validate_pnpm_version("11.10.0"))

    def test_version_parser_rejects_ambiguous_or_decorated_values(self) -> None:
        self.assertEqual(parse_version("v24.14.0"), (24, 14, 0))
        self.assertEqual(parse_version("11.9.0"), (11, 9, 0))
        for invalid in ("", "24", "24.14", "24.14.0-beta", "version 24.14.0"):
            with self.subTest(invalid=invalid):
                self.assertIsNone(parse_version(invalid))


if __name__ == "__main__":
    unittest.main()
