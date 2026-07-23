"""Export the deterministic OpenAPI contract for the fixture application.

The committed ``apps/api/openapi.json`` is a reviewed source artifact generated
from ``create_app().openapi()``. Regenerate it with::

    make -C apps/api bootstrap  # once
    uv run --frozen python scripts/export_openapi.py --write

Run without ``--write`` (or with ``--check``) to fail on drift. The contract
test ``tests/contract_tests/test_openapi.py`` enforces the same equality.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from deepwork_api import create_app

OPENAPI_PATH = Path(__file__).resolve().parents[1] / "openapi.json"


def render_openapi() -> str:
    """Return the canonical, byte-stable OpenAPI document for the fixture app."""

    document = create_app().openapi()
    return json.dumps(document, indent=2, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="write the generated document to apps/api/openapi.json",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the committed document differs from the generated one",
    )
    args = parser.parse_args(argv)

    rendered = render_openapi()

    if args.write:
        OPENAPI_PATH.write_text(rendered, encoding="utf-8")
        return 0

    if not OPENAPI_PATH.exists():
        print(
            f"{OPENAPI_PATH} is missing; run 'python scripts/export_openapi.py --write'",
            file=sys.stderr,
        )
        return 1

    committed = OPENAPI_PATH.read_text(encoding="utf-8")
    if committed != rendered:
        print(
            f"{OPENAPI_PATH} is out of date; run 'python scripts/export_openapi.py --write'",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
