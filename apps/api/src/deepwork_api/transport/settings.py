"""FastAPI routes for editable workspace settings (the agent system prompt)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from deepwork_api.application import (
    DEFAULT_SECURITY_CONTEXT,
    PromptStore,
    SecurityContext,
    SystemPromptTooLongError,
)
from deepwork_api.contracts import SystemPromptResponse, SystemPromptUpdateRequest


def _default_security_context() -> SecurityContext:
    return DEFAULT_SECURITY_CONTEXT


def build_settings_router(
    prompt_store: PromptStore,
    *,
    security_context_dependency: Callable[
        ..., SecurityContext | Awaitable[SecurityContext]
    ] = _default_security_context,
) -> APIRouter:
    """Build the workspace-settings API around an injected prompt store.

    ``security_context_dependency`` returns the authenticated caller context,
    or the legacy default context for the open local-development router.
    """

    router = APIRouter(
        prefix="/api/v1/settings",
        tags=["settings"],
    )
    security_context_marker = Depends(security_context_dependency)

    @router.get("/prompt", response_model=SystemPromptResponse)
    async def get_prompt(
        security_context: SecurityContext = security_context_marker,
    ) -> SystemPromptResponse:
        prompt = await prompt_store.get_system_prompt(
            tenant_id=security_context.tenant_id,
            workspace_id=security_context.workspace_id,
        )
        return SystemPromptResponse.from_value(prompt)

    @router.put("/prompt", response_model=SystemPromptResponse)
    async def put_prompt(
        request: SystemPromptUpdateRequest,
        security_context: SecurityContext = security_context_marker,
    ) -> SystemPromptResponse | JSONResponse:
        try:
            await prompt_store.set_system_prompt(
                request.systemPrompt,
                tenant_id=security_context.tenant_id,
                workspace_id=security_context.workspace_id,
            )
        except SystemPromptTooLongError:
            return JSONResponse(
                status_code=422,
                content={
                    "code": "system_prompt_too_long",
                    "message": "The system prompt exceeds the maximum allowed length.",
                },
            )
        prompt = await prompt_store.get_system_prompt(
            tenant_id=security_context.tenant_id,
            workspace_id=security_context.workspace_id,
        )
        return SystemPromptResponse.from_value(prompt)

    return router
