"""Adapters implementing the editable system-prompt store port."""

from deepwork_api.adapters.prompt.memory import InMemoryPromptStore
from deepwork_api.adapters.prompt.sqlite import SQLitePromptStore

__all__ = ["InMemoryPromptStore", "SQLitePromptStore"]
