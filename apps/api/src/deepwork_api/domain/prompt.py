"""Pure rules for the workspace's editable agent system prompt."""

from __future__ import annotations

# An editable prompt is bounded so it cannot grow without limit through the API
# or flow an unbounded value into every run's config. Kept in step with the
# agent's own per-run override bound.
MAX_SYSTEM_PROMPT_LENGTH = 100_000


class SystemPromptTooLongError(ValueError):
    """The submitted system prompt exceeds the allowed length."""


def normalize_system_prompt(prompt: str | None) -> str | None:
    """Normalize a submitted system prompt to its stored form.

    Trailing and leading whitespace is stripped; an empty or whitespace-only
    prompt normalizes to ``None`` (clear the override). A prompt longer than
    :data:`MAX_SYSTEM_PROMPT_LENGTH` is rejected rather than silently truncated,
    so the caller learns the value was not stored as sent.
    """
    if prompt is None:
        return None
    text = prompt.strip()
    if not text:
        return None
    if len(text) > MAX_SYSTEM_PROMPT_LENGTH:
        message = "system prompt exceeds the maximum allowed length"
        raise SystemPromptTooLongError(message)
    return text
