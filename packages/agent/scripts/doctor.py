"""Verify package-local immutable tool prerequisites."""

from __future__ import annotations

import platform
import sys


def main() -> int:
    """Report the interpreter and fail unless it is supported Python 3.11+."""
    sys.stdout.write(f"python: {platform.python_version()}\n")
    sys.stdout.write(f"implementation: {platform.python_implementation()}\n")
    if not (3, 11) <= sys.version_info[:2] < (4, 0):
        sys.stdout.write("required: Python >=3.11,<4.0\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
