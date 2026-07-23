"""Source-grounded operation and cross-product dimensions.

This module is evidence data for a probe kit, not an application provider adapter.
Unknown control-plane details are deliberately retained as unknown rather than
filled with an inferred host or workspace header.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

COLLECTED_AT = "2026-07-23"

KEY_CLASSES = (
    "personal",
    "service-workspace-single",
    "service-workspace-multiple",
    "service-organization",
)

CONTEXT_CASES = (
    "valid-no-workspace-context",
    "valid-documented-workspace-context",
    "missing-authorization",
    "missing-required-workspace-context",
    "wrong-workspace-context",
    "conflicting-workspace-context",
    "unsupported-key-plane-combination",
    "caller-supplied-forwarding-headers",
    "permission-denied",
    "revoked-key",
    "inaccessible-workspace",
)

REJECTED_CASES = frozenset(
    {
        "missing-authorization",
        "conflicting-workspace-context",
        "caller-supplied-forwarding-headers",
    }
)

FORBIDDEN_CALLER_HEADERS = (
    "authorization",
    "b3",
    "baggage",
    "connection",
    "cookie",
    "forwarded",
    "host",
    "keep-alive",
    "proxy-authorization",
    "proxy-connection",
    "set-cookie",
    "te",
    "trailer",
    "traceparent",
    "tracestate",
    "transfer-encoding",
    "upgrade",
    "via",
    "x-amzn-trace-id",
    "x-api-key",
    "x-b3-flags",
    "x-b3-sampled",
    "x-b3-spanid",
    "x-b3-traceid",
    "x-forwarded-for",
    "x-forwarded-host",
    "x-forwarded-proto",
    "x-original-host",
    "x-original-url",
    "x-organization-id",
    "x-tenant-id",
)


@dataclass(frozen=True)
class Operation:
    operation: str
    method: str
    route_template: str
    service_host_class: str
    plane: str
    documented_headers: tuple[str, ...]
    workspace_context: str
    request_schema: str
    response_schema: str
    source_url: str
    source_claim: str
    contract_limit: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


OPERATIONS = (
    Operation(
        operation="current-organization",
        method="GET",
        route_template="/api/v1/orgs/current",
        service_host_class="langsmith-platform-api",
        plane="platform",
        documented_headers=("X-Api-Key", "X-Organization-Id"),
        workspace_context="Organization context only; no target-workspace header is documented for this operation.",
        request_schema="no-body",
        response_schema="sanitized organization identity object",
        source_url="https://docs.langchain.com/langsmith/manage-organization-by-api",
        source_claim="Organization-management guidance documents /api/v1/orgs/current and says X-Organization-Id should be present.",
        contract_limit="Generated platform security schemes and organization-management prose do not establish whether X-Organization-Id is a conjunction or alternative for this request.",
    ),
    Operation(
        operation="list-workspaces",
        method="GET",
        route_template="/api/v1/workspaces",
        service_host_class="langsmith-platform-api",
        plane="platform",
        documented_headers=("X-Api-Key", "X-Organization-Id"),
        workspace_context="Organization-scoped enumeration; no target workspace is selected.",
        request_schema="query-only",
        response_schema="sanitized workspace summary array",
        source_url="https://docs.langchain.com/langsmith/manage-organization-by-api",
        source_claim="Organization-management guidance documents /api/v1/workspaces and X-Organization-Id.",
        contract_limit="Generated GET /api/v1/workspaces declares X-API-Key while organization-management prose says X-Organization-Id should be present; the conjunction is unresolved.",
    ),
    Operation(
        operation="list-classic-deployments",
        method="GET",
        route_template="/v2/deployments",
        service_host_class="regional-langsmith-control-plane-api",
        plane="control",
        documented_headers=("X-Api-Key", "X-Tenant-Id"),
        workspace_context="X-Tenant-Id is required and contains the target workspace ID.",
        request_schema="pagination query",
        response_schema="sanitized deployment summary page",
        source_url="https://docs.langchain.com/langsmith/api-ref-control-plane",
        source_claim="Official control-plane reference documents regional api.host classes, GET /v2/deployments, X-Api-Key, and X-Tenant-Id.",
    ),
    Operation(
        operation="read-classic-deployment",
        method="GET",
        route_template="/v2/deployments/{deployment_id}",
        service_host_class="regional-langsmith-control-plane-api",
        plane="control",
        documented_headers=("X-Api-Key", "X-Tenant-Id"),
        workspace_context="X-Tenant-Id is required and contains the target workspace ID.",
        request_schema="deployment_id path parameter",
        response_schema="sanitized deployment capability object",
        source_url="https://docs.langchain.com/api-reference/deployments-v2/get-deployment",
        source_claim="Official control-plane reference documents GET /v2/deployments/{deployment_id} with plane-level X-Api-Key and X-Tenant-Id.",
    ),
    Operation(
        operation="agent-server-health",
        method="GET",
        route_template="/ok",
        service_host_class="classic-agent-server",
        plane="data",
        documented_headers=("X-Api-Key",),
        workspace_context="Deployment URL selects the resource; no Agent Server workspace header is documented.",
        request_schema="no-body",
        response_schema="sanitized health status",
        source_url="https://docs.langchain.com/langsmith/server-api-ref",
        source_claim="Official Agent Server reference documents system health/info and X-Api-Key for each request.",
    ),
    Operation(
        operation="agent-server-capabilities",
        method="GET",
        route_template="/info",
        service_host_class="classic-agent-server",
        plane="data",
        documented_headers=("X-Api-Key",),
        workspace_context="Deployment URL selects the resource; no Agent Server workspace header is documented.",
        request_schema="no-body",
        response_schema="sanitized server capability object",
        source_url="https://docs.langchain.com/langsmith/server-api-ref",
        source_claim="Official Agent Server reference identifies server-info operations and X-Api-Key authentication.",
    ),
    Operation(
        operation="search-assistants",
        method="POST",
        route_template="/assistants/search",
        service_host_class="classic-agent-server",
        plane="data",
        documented_headers=("X-Api-Key",),
        workspace_context="Deployment URL selects the resource; no Agent Server workspace header is documented.",
        request_schema="{metadata?: object, limit: integer, offset: integer}",
        response_schema="sanitized assistant summary array",
        source_url="https://docs.langchain.com/langsmith/server-api-ref",
        source_claim="Official Agent Server reference gives POST /assistants/search with X-Api-Key.",
    ),
    Operation(
        operation="read-assistant-subgraphs",
        method="GET",
        route_template="/assistants/{assistant_id}/subgraphs",
        service_host_class="classic-agent-server",
        plane="data",
        documented_headers=("X-Api-Key",),
        workspace_context="Deployment URL selects the resource; no Agent Server workspace header is documented.",
        request_schema="assistant_id path parameter",
        response_schema="sanitized graph/subgraph schema map",
        source_url="https://docs.langchain.com/langsmith/agent-server-api/assistants/get-assistant-subgraphs",
        source_claim="Official Agent Server reference documents GET /assistants/{assistant_id}/subgraphs.",
    ),
    Operation(
        operation="search-threads",
        method="POST",
        route_template="/threads/search",
        service_host_class="classic-agent-server",
        plane="data",
        documented_headers=("X-Api-Key",),
        workspace_context="Deployment URL selects the resource; no Agent Server workspace header is documented.",
        request_schema="{limit: integer, offset: integer, metadata?: object}",
        response_schema="sanitized thread summary array",
        source_url="https://docs.langchain.com/langsmith/server-api-ref",
        source_claim="Official Agent Server reference documents the Threads endpoint group and deployment authentication.",
    ),
    Operation(
        operation="read-thread",
        method="GET",
        route_template="/threads/{thread_id}",
        service_host_class="classic-agent-server",
        plane="data",
        documented_headers=("X-Api-Key",),
        workspace_context="Deployment URL selects the resource; no Agent Server workspace header is documented.",
        request_schema="thread_id path parameter",
        response_schema="sanitized thread object",
        source_url="https://docs.langchain.com/langsmith/agent-server-api/threads/get-thread",
        source_claim="Official Agent Server reference documents GET /threads/{thread_id}.",
    ),
    Operation(
        operation="read-thread-state",
        method="GET",
        route_template="/threads/{thread_id}/state",
        service_host_class="classic-agent-server",
        plane="data",
        documented_headers=("X-Api-Key",),
        workspace_context="Deployment URL selects the resource; no Agent Server workspace header is documented.",
        request_schema="thread_id path parameter",
        response_schema="sanitized current checkpoint/state object",
        source_url="https://docs.langchain.com/langsmith/agent-server-api/threads/get-thread-state",
        source_claim="Official Agent Server reference documents GET /threads/{thread_id}/state.",
    ),
    Operation(
        operation="stream-stateless-run",
        method="POST",
        route_template="/runs/stream",
        service_host_class="classic-agent-server",
        plane="data",
        documented_headers=("X-Api-Key",),
        workspace_context="Deployment URL selects the resource; no Agent Server workspace header is documented.",
        request_schema="{assistant_id: string, input: object, stream_mode: string|array}",
        response_schema="sanitized server-sent event sequence",
        source_url="https://docs.langchain.com/langsmith/deployment-quickstart",
        source_claim="Official deployment quickstart gives POST /runs/stream with X-Api-Key.",
    ),
    Operation(
        operation="stream-thread-run",
        method="POST",
        route_template="/threads/{thread_id}/runs/stream",
        service_host_class="classic-agent-server",
        plane="data",
        documented_headers=("X-Api-Key",),
        workspace_context="Deployment URL selects the resource; no Agent Server workspace header is documented.",
        request_schema="{assistant_id: string, input: object, stream_mode: string|array}",
        response_schema="sanitized server-sent event sequence",
        source_url="https://docs.langchain.com/langsmith/server-api-ref",
        source_claim="Official Agent Server reference documents Thread Runs and deployment authentication.",
    ),
    Operation(
        operation="read-thread-run",
        method="GET",
        route_template="/threads/{thread_id}/runs/{run_id}",
        service_host_class="classic-agent-server",
        plane="data",
        documented_headers=("X-Api-Key",),
        workspace_context="Deployment URL selects the resource; no Agent Server workspace header is documented.",
        request_schema="thread_id and run_id path parameters",
        response_schema="sanitized run object",
        source_url="https://docs.langchain.com/langsmith/agent-server-api/thread-runs/get-run",
        source_claim="Official Agent Server reference documents GET /threads/{thread_id}/runs/{run_id}.",
    ),
)


def operation_map() -> dict[str, Operation]:
    return {operation.operation: operation for operation in OPERATIONS}
