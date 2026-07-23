"""CLI validator for the retained research matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from langchain_contract_spikes.contracts import validate_matrix_document


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("matrix", type=Path)
    args = parser.parse_args()
    document = json.loads(args.matrix.read_text(encoding="utf-8"))
    errors = validate_matrix_document(document)
    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"validated {len(document['rows'])} pinned contract rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
