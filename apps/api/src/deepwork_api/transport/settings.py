"""FastAPI routes for editable workspace settings (the agent system prompt)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from deepwork_api.application import PromptStore, SystemPromptTooLongError
from deepwork_api.contracts import SystemPromptResponse, SystemPromptUpdateRequest


def build_settings_router(
    prompt_store: PromptStore,
    *,
    dependencies: list[Any] | None = None,
) -> APIRouter:
    """Build the workspace-settings API around an injected prompt store.

    ``dependencies`` are attached to every route (the session guard when
    authentication is enabled), matching the task router.
    """

    router = APIRouter(
        prefix="/api/v1/settings",
        tags=["settings"],
        dependencies=dependencies or [],
    )

    @router.get("/prompt", response_model=SystemPromptResponse)
    async def get_prompt() -> SystemPromptResponse:
        prompt = await prompt_store.get_system_prompt()
        return SystemPromptResponse.from_value(prompt)

    @router.put("/prompt", response_model=SystemPromptResponse)
    async def put_prompt(request: SystemPromptUpdateRequest) -> SystemPromptResponse | JSONResponse:
        try:
            await prompt_store.set_system_prompt(request.systemPrompt)
        except SystemPromptTooLongError:
            return JSONResponse(
                status_code=422,
                content={
                    "code": "system_prompt_too_long",
                    "message": "The system prompt exceeds the maximum allowed length.",
                },
            )
        prompt = await prompt_store.get_system_prompt()
        return SystemPromptResponse.from_value(prompt)

    return router
