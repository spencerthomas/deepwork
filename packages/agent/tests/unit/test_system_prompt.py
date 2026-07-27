"""The bundled default system prompt must describe *this* runtime.

Regression guard for code-review H1: the previous default was a foreign
Codex-CLI harness prompt referencing tools that do not exist here and omitting
the untrusted-content clause. These tests pin that the shipped default matches
the Deep Agents runtime and keeps the injection-resistance instruction.
"""

from __future__ import annotations

from deepwork_agent.graph import DEEP_WORK_SYSTEM_PROMPT

FOREIGN_TOOL_MARKERS = [
    "apply_patch",
    "update_plan",
    "powershell",
    "list_mcp_resources",
    "require_escalated",
    "<tool_call>",
]


def test_prompt_does_not_reference_nonexistent_tools() -> None:
    """The default prompt must not instruct the model to use tools we don't provide."""
    lowered = DEEP_WORK_SYSTEM_PROMPT.lower()
    for marker in FOREIGN_TOOL_MARKERS:
        assert marker.lower() not in lowered, f"prompt references nonexistent tool: {marker}"


def test_prompt_keeps_the_untrusted_content_clause() -> None:
    """Injection resistance: retrieved content is data, not instructions."""
    lowered = DEEP_WORK_SYSTEM_PROMPT.lower()
    assert "untrusted" in lowered
    assert "instructions" in lowered


def test_prompt_describes_the_plan_approval_flow() -> None:
    """The prompt reflects the single plan-approval interrupt this graph implements."""
    lowered = DEEP_WORK_SYSTEM_PROMPT.lower()
    assert "plan" in lowered
    assert "approv" in lowered
