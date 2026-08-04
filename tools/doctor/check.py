"""Fail-closed Node.js and pnpm version check for the root command contract."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Sequence

NODE_MINIMUM = (24, 14, 0)
NODE_MAXIMUM = (25, 0, 0)
PNPM_REQUIRED = (11, 9, 0)

_VERSION = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def parse_version(value: str) -> tuple[int, int, int] | None:
    """Parse one exact three-part tool version, with Node's optional ``v``."""

    match = _VERSION.fullmatch(value.strip())
    if match is None:
        return None
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)


def validate_node_version(value: str) -> str | None:
    """Return a safe diagnostic when ``value`` is outside the supported range."""

    parsed = parse_version(value)
    if parsed is not None and NODE_MINIMUM <= parsed < NODE_MAXIMUM:
        return None
    return f"Node.js >=24.14.0 <25 is required; found {value.strip() or 'unknown'}"


def validate_pnpm_version(value: str) -> str | None:
    """Return a safe diagnostic unless ``value`` matches packageManager exactly."""

    if parse_version(value) == PNPM_REQUIRED:
        return None
    return f"pnpm 11.9.0 is required; found {value.strip() or 'unknown'}"


def _version_output(command: str) -> tuple[str, str | None]:
    try:
        completed = subprocess.run(
            [command, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown", f"{command} is unavailable"
    value = completed.stdout.strip()
    if completed.returncode != 0 or not value:
        return value or "unknown", f"{command} --version failed"
    return value, None


def main(_argv: Sequence[str] | None = None) -> int:
    """Report both root JavaScript prerequisites and fail on any mismatch."""

    node, node_command_error = _version_output("node")
    pnpm, pnpm_command_error = _version_output("pnpm")
    errors = tuple(
        error
        for error in (
            node_command_error or validate_node_version(node),
            pnpm_command_error or validate_pnpm_version(pnpm),
        )
        if error is not None
    )
    print("== Node.js ==")
    print(node)
    print("== pnpm ==")
    print(pnpm)
    for error in errors:
        print(f"ERROR: {error}")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
