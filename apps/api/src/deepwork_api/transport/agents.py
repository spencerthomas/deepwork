"""FastAPI routes for the source-backed agent registry (list/select/manage)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Path
from fastapi.responses import JSONResponse, Response

from deepwork_api.application import (
    AgentRegistryUnavailableError,
    DefaultAgentImmutableError,
    TaskService,
    TaskSourceContractError,
    TaskSourceUnavailableError,
)
from deepwork_api.contracts import (
    AgentCreateRequest,
    AgentListResponse,
    AgentSummaryResponse,
    AgentUpdateRequest,
    ProblemResponse,
)

AgentPath = Annotated[str, Path(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")]


def build_agents_router(
    service: TaskService,
    *,
    dependencies: list[Any] | None = None,
) -> APIRouter:
    """Build the agent-registry API around an injected task service.

    ``dependencies`` are attached to every route (the session guard when
    authentication is enabled), matching the task and settings routers.
    """

    router = APIRouter(
        prefix="/api/v1/agents",
        tags=["agents"],
        dependencies=dependencies or [],
    )

    @router.get("", response_model=AgentListResponse)
    async def list_agents() -> AgentListResponse | JSONResponse:
        try:
            agents = await service.list_agents()
        except AgentRegistryUnavailableError:
            return AgentListResponse(available=False, items=())
        except TaskSourceContractError:
            return _source_contract_problem()
        except TaskSourceUnavailableError:
            return _source_unavailable_problem()
        return AgentListResponse(
            available=True,
            items=tuple(AgentSummaryResponse.from_source(agent) for agent in agents),
        )

    @router.post("", response_model=AgentSummaryResponse, status_code=201)
    async def create_agent(request: AgentCreateRequest) -> AgentSummaryResponse | JSONResponse:
        try:
            agent = await service.create_agent(
                name=request.name,
                description=request.description,
                system_prompt=request.system_prompt,
            )
        except AgentRegistryUnavailableError:
            return _registry_unavailable_problem()
        except TaskSourceContractError:
            return _source_contract_problem()
        except TaskSourceUnavailableError:
            return _source_unavailable_problem()
        return AgentSummaryResponse.from_source(agent)

    @router.put("/{agent_id}", response_model=AgentSummaryResponse)
    async def update_agent(
        agent_id: AgentPath,
        request: AgentUpdateRequest,
    ) -> AgentSummaryResponse | JSONResponse:
        try:
            agent = await service.update_agent(
                agent_id,
                name=request.name,
                description=request.description,
                system_prompt=request.system_prompt,
            )
        except DefaultAgentImmutableError:
            return _default_agent_immutable_problem()
        except AgentRegistryUnavailableError:
            return _registry_unavailable_problem()
        except TaskSourceContractError:
            return _source_contract_problem()
        except TaskSourceUnavailableError:
            return _source_unavailable_problem()
        return AgentSummaryResponse.from_source(agent)

    @router.delete("/{agent_id}", status_code=204, response_model=None)
    async def delete_agent(agent_id: AgentPath) -> Response | JSONResponse:
        try:
            await service.delete_agent(agent_id)
        except DefaultAgentImmutableError:
            return _default_agent_immutable_problem()
        except AgentRegistryUnavailableError:
            return _registry_unavailable_problem()
        except TaskSourceContractError:
            return _source_contract_problem()
        except TaskSourceUnavailableError:
            return _source_unavailable_problem()
        return Response(status_code=204)

    return router


def _source_contract_problem() -> JSONResponse:
    return _problem(
        502,
        "agent_source_contract_mismatch",
        "The configured task source broke its supported contract.",
    )


def _source_unavailable_problem() -> JSONResponse:
    return _problem(503, "agent_source_unavailable", "The configured task source is unavailable.")


def _registry_unavailable_problem() -> JSONResponse:
    return _problem(
        409,
        "agent_registry_unavailable",
        "No real task source is configured, so there is no agent registry.",
    )


def _default_agent_immutable_problem() -> JSONResponse:
    return _problem(
        409,
        "default_agent_immutable",
        "The default agent bound to the deployed graph cannot be edited or deleted.",
    )


def _problem(status_code: int, code: str, message: str) -> JSONResponse:
    body = ProblemResponse(code=code, message=message)
    return JSONResponse(status_code=status_code, content=body.model_dump())
