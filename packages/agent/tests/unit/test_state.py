"""Tests for deterministic graph input construction."""

import pytest

from deepwork_agent import initial_state


def test_initial_state_normalizes_task_without_runtime_side_effects() -> None:
    """Input construction is deterministic and contains no provider data."""
    state = initial_state("  Research and write a short note.  ")

    assert state == {"task": "Research and write a short note."}


def test_initial_state_rejects_empty_task() -> None:
    """An empty task cannot enter the graph."""
    with pytest.raises(ValueError, match="non-whitespace"):
        initial_state(" \n ")
