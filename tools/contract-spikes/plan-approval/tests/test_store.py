from __future__ import annotations

import pytest

from plan_approval_contract_spikes.errors import ContractViolation
from plan_approval_contract_spikes.store import AppendOnlyCheckpointStore


def test_append_only_hash_chain_detects_tampering(tmp_path):
    path = tmp_path / "events.jsonl"
    store = AppendOnlyCheckpointStore(path)
    store.append("synthetic_event", {"value": "original"})
    original = path.read_text(encoding="utf-8")
    path.write_text(original.replace("original", "modified"), encoding="utf-8")
    with pytest.raises(ContractViolation, match="content was modified"):
        store.load()
