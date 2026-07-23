# Official public source inventory: classic LangSmith auth and workspace headers

Accessed: 2026-07-23

## Scope and evidence boundary

This inventory covers current official LangChain documentation and current public
package-index metadata for the classic LangSmith API, LangSmith Deployment control
plane, and deployment-specific Agent Server data plane. It does not use a live
account, credentials, private documentation, Fleet contracts, Managed Deep Agents
contracts, or application/provider source code.

All claims below are evidence tier 2 under the repository precedence:
official primary documentation or public package metadata. They are
`documented`/`public-package-metadata`, not `accepted-live`. Package versions and
documentation examples do not establish a live server revision or live
authorization behavior.

Header values in this document are placeholders only. No credential, workspace
identifier, organization identifier, customer value, or reusable deployment URL
was collected.

## Exact documented key and header distinctions

| Plane | Key class | Exact documented header names | Documented workspace or organization behavior | Evidence classification |
|---|---|---|---|---|
| LangSmith API | Personal Access Token (PAT), prefix `lsv2_pt_` | `X-API-Key`; `X-Tenant-Id` when selecting a target workspace | PAT is user-scoped and inherits the user's permissions. If `X-Tenant-Id` is omitted, the request runs against the default workspace associated with the key. | Tier 2, official documentation |
| LangSmith API | Service key, prefix `lsv2_sk_`; may be scoped to one workspace, multiple workspaces, or the organization | `X-API-Key`; `X-Tenant-Id` when selecting a target workspace | An organization-scoped service key must include `X-Tenant-Id` for workspace-scoped resources; documented omission result is `403 Forbidden`. The organization-management guide also says a non-organization-scoped key defaults to the workspace where it was created when `X-Tenant-Id` is absent. | Tier 2, official documentation |
| LangSmith organization-management examples | Organization-scoped service key with Organization Admin permission | `X-API-Key`, `X-Organization-Id`, and `X-Tenant-Id` for workspace-scoped calls | The guide says `X-Organization-Id` “should be present on all requests,” but this statement is within its organization-management workflow. The generated `GET /api/v1/workspaces` reference declares only `X-API-Key` authorization. This conflict is unresolved and must not be generalized to every LangSmith API request. | Tier 2, same-tier documentation conflict |
| Classic LangSmith Deployment control plane | Valid LangSmith API key | `X-Api-Key` and `X-Tenant-Id` | The control-plane overview explicitly instructs callers to set both headers and defines `X-Tenant-Id` as the workspace ID to target. | Tier 2, official documentation |
| Classic Agent Server on a LangSmith deployment | Valid LangSmith API key for the organization where the Agent Server is deployed | `X-Api-Key` | The Agent Server overview says to pass `X-Api-Key` with each request. It does not document `X-Tenant-Id` or `X-Organization-Id` for classic Agent Server calls. Do not add either header without higher-precedence evidence. | Tier 2, official documentation |
| Fleet Agent Server, excluded from this classic baseline | PAT | `X-API-Key` and `X-Auth-Scheme: langsmith-api-key` | Fleet documentation requires the additional auth-scheme header. This is a distinct Fleet contract and is not evidence that classic Agent Server accepts or requires `X-Auth-Scheme`. | Tier 2, official documentation; out of scope |

HTTP header spelling above follows the spelling shown by the source for that plane.
The inventory intentionally does not collapse the documented forms into a guessed
universal header set.

Legacy API keys prefixed `ls__` are documented as unsupported since
2024-10-22. They are an unsupported key family for new integrations, not a
fallback.

## Required-plane host and route inventory

Only hosts and routes explicitly established by official sources are listed.
`https://api.example.com` in generated reference examples is a placeholder and is
never a verified provider host.

### LangSmith API: authentication-bearing workspace discovery

Cloud service host class:

| Region | Exact official host |
|---|---|
| GCP US | `https://api.smith.langchain.com` |
| GCP EU | `https://eu.api.smith.langchain.com` |
| GCP APAC | `https://apac.api.smith.langchain.com` |
| AWS US | `https://aws.api.smith.langchain.com` |

Self-hosted host template: `http(s)://<langsmith-url>/api`. The official CI/CD
guide separately warns that the `LANGSMITH_ENDPOINT` environment-variable form
needs `/v1`, for example `https://api.smith.langchain.com/v1` or
`http(s)://<langsmith-url>/api/v1`; this environment-variable form must not be
silently substituted for the REST route base below.

| Operation | Method and official route template | Exact documented auth/context | What it establishes |
|---|---|---|---|
| Enumerate workspaces visible to the current auth in the current organization | `GET /api/v1/workspaces` | Generated reference declares `X-API-Key` required. Organization-management guidance additionally discusses `X-Organization-Id`, creating the unresolved conflict recorded below. | Authorized workspace enumeration and workspace metadata, including workspace `id`, `organization_id`, permissions, and optional `data_plane_url`. |
| Current-organization context used by organization-management examples | `GET /api/v1/orgs/current` | Example session uses `X-API-Key` and `X-Organization-Id`; `X-Tenant-Id` is added for workspace-scoped operations. | A documented example route base, not a separately verified credential-validation contract in this inventory. |

No dedicated public “validate this LangSmith API key” endpoint with a complete
method, route, auth schema, and response/error schema was found. The Cloud rate
limit page mentions `/auth`, but that mention is not a public operation contract.
The Agent Server OpenAPI guide also says LangSmith does not provide authentication
endpoints for application user authentication. Therefore:

- `GET /api/v1/workspaces` may be modeled as an authentication-bearing,
  authorization-aware discovery operation;
- it must not be relabeled as a dedicated credential-validation endpoint; and
- exact invalid/revoked/permission response behavior remains
  `blocked-live-evidence`.

### Classic LangSmith Deployment control plane

Cloud service host class:

| Region | Exact official host |
|---|---|
| GCP US | `https://api.host.langchain.com` |
| GCP EU | `https://eu.api.host.langchain.com` |
| GCP APAC | `https://apac.api.host.langchain.com` |
| AWS US | `https://aws.api.host.langchain.com` |

Self-hosted host template: `http(s)://<langsmith-url>/api-host`.

For every operation in this subsection, the control-plane overview documents
`X-Api-Key` plus `X-Tenant-Id` containing the target workspace ID.

| Operation | Method and official route template | Route evidence |
|---|---|---|
| List deployments / discover deployment capability | `GET /v2/deployments` | Control-plane overview and generated API reference |
| Read a deployment | `GET /v2/deployments/{deployment_id}` | Control-plane overview and generated API reference |
| List revisions | `GET /v2/deployments/{deployment_id}/revisions` | Control-plane overview example and generated API reference |
| Read a revision / inspect deployment status | `GET /v2/deployments/{deployment_id}/revisions/{revision_id}` | Control-plane overview and generated API reference |

These are read routes suitable for a later sanctioned negative/live probe. Create,
patch, and delete routes are documented but are not required for safe source
connection discovery and are not authorized by this packet.

### Classic Agent Server data plane

Host class: an opaque deployment-specific Agent Server API URL. Official
quickstarts say to copy it from the deployment details UI and use the placeholder
`<DEPLOYMENT_URL>` / `your-deployment-url`, but the documented authenticated
`GET /v2/deployments/{deployment_id}` response does not define an Agent Server
URL field. This inventory therefore establishes neither API origin discovery nor
an acceptable hostname pattern. A deployment exposes its own API reference at
`/docs` only after an origin has been safely established.

The Agent Server overview says LangSmith deployments require `X-Api-Key` with each
request. The generated operation pages often omit the header from their snippets;
the overview is the explicit plane-level auth statement and must be retained as
the documented requirement. No classic source reviewed here documents
`X-Tenant-Id`, `X-Organization-Id`, `Authorization`, cookies, or
`X-Auth-Scheme` for these operations.

| Operation | Method and official route template | Purpose |
|---|---|---|
| Health | `GET /ok` | Health, optionally database connectivity via `check_db=1` |
| Capability/version discovery | `GET /info` | Server version, LangGraph Python version, feature flags, and deployment metadata |
| List/search assistants and their graph IDs | `POST /assistants/search` | Lists assistants; response includes `assistant_id` and `graph_id` |
| Inspect graph/subgraph schema metadata | `GET /assistants/{assistant_id}/subgraphs` | Returns graph-name keyed schema metadata |
| Create a thread | `POST /threads` | Creates a persisted thread |
| List/search threads | `POST /threads/search` | Lists authorized threads matching filters |
| Read a thread | `GET /threads/{thread_id}` | Reads one thread |
| Read current thread state | `GET /threads/{thread_id}/state` | Reads the latest checkpoint/state |
| Create a stateful streaming run | `POST /threads/{thread_id}/runs/stream` | Invokes an assistant/graph in an existing thread and returns SSE |
| Read a run | `GET /threads/{thread_id}/runs/{run_id}` | Reads one run |
| Create a stateless run and wait | `POST /runs/wait` | Invokes an assistant/graph without persisted thread state and waits for output |

Only synthetic/local fixtures may create threads or runs under this packet unless
an explicitly sanctioned non-production classic account later authorizes those
operations. Official route documentation alone is not live authorization.

## Official public package metadata snapshot

Package-index metadata provides current release identity and artifact integrity;
it does not prove the hosted service uses that version or that a client request is
authorized.

| Package | Registry URL | Version on 2026-07-23 | Relevant artifact integrity | Evidence classification |
|---|---|---:|---|---|
| `langsmith` | `https://pypi.org/pypi/langsmith/json` | `0.10.9` | wheel SHA-256 `5e0e8ab0f8df05710809919184495e33c2a7c9a9a5e8861d63dd12c1226d9c79` | Tier 2, official PyPI metadata |
| `langgraph-sdk` | `https://pypi.org/pypi/langgraph-sdk/json` | `0.4.2` | wheel SHA-256 `75fa5096c1177ce39c847096a8fe3745ffd480ddb412995f836e9f5f884c43dd` | Tier 2, official PyPI metadata |
| `langgraph-api` | `https://pypi.org/pypi/langgraph-api/json` | `0.11.1` | wheel SHA-256 `35c25186f11c625756e35530c6909082c47e81815ef14b5130ca1d33ba9b7328` | Tier 2, official PyPI metadata |
| `@langchain/langgraph-sdk` | `https://registry.npmjs.org/%40langchain%2Flanggraph-sdk/latest` | `1.9.28` | registry integrity `sha512-4j3XuM0PvtmAbL8mPfBS99ez3+ytRfgbOpAR/nOeaejTRF3Q9dNw2QnaGLGng8wLPtGLoSj+SYgUOVxy9Bv9vg==` | Tier 2, official npm metadata |

## Contradictions and unknowns that must remain open

1. **`X-Organization-Id` scope is unresolved.** The organization-management
   guide says it should be present on all requests in that workflow. The generated
   `GET /api/v1/workspaces` reference declares only `X-API-Key`, while the general
   administration overview describes workspace selection through
   `X-Tenant-Id`. Do not inject `X-Organization-Id` across all LangSmith API,
   control-plane, or Agent Server requests without installed/generated or live
   contract evidence.
2. **No complete public credential-validation operation was established.** `/auth`
   appears in a Cloud rate-limit table, but no public method/schema/error contract
   was found. Treat the exact validation route as `unknown`, not guessed.
3. **Classic Agent Server workspace-header behavior is undocumented.** The
   official classic Agent Server overview requires `X-Api-Key` and does not
   mention `X-Tenant-Id`. Whether an extra tenant header is ignored, honored, or
   rejected is `blocked-live-evidence`.
4. **System-page snippets omit auth.** Individual `/ok` and `/info` reference
   examples show no header, while the plane overview says `X-Api-Key` is required
   with each LangSmith-deployment request. Model the overview requirement; do not
   infer that Cloud system routes are public.
5. **Generic API-reference hosts are placeholders and Agent Server API origin
   discovery is unresolved.** `api.example.com` is not an allowed provider
   target. The documented authenticated deployment response does not define an
   Agent Server URL field. A future origin may be accepted only from an explicit
   field in an authenticated documented control-plane response and then
   constrained by an accepted server-side URL, DNS, TLS, redirect, and provenance
   policy.
6. **Workspace selection wording differs by source.** The setup guide says
   `LANGSMITH_WORKSPACE_ID` is required when an API key is scoped to more than one
   workspace; the administration overview specifically requires
   `X-Tenant-Id` for organization-scoped service keys on workspace-scoped
   resources. Retain key class and scope as separate matrix dimensions.
7. **Error behavior is mostly unproven.** Only the missing-tenant
   organization-scoped service-key case documents `403 Forbidden`. Missing auth,
   wrong tenant, conflicting tenant, revoked key, inaccessible workspace,
   wrong-plane key, and sanitized provider bodies need sanctioned live evidence.
8. **Hosted versions are unknown.** Current package-index versions cannot be used
   as the server revision. A later live probe must record `/info`, deployment
   region/tier, and per-deployment `/docs` schema without storing a reusable
   endpoint.

## Safe disposition for downstream matrix generation

- Keep every live-dependent combination `blocked-live-evidence`.
- Allow-list the exact plane and accepted regional host class; never accept a
  caller-supplied host, redirect target, cookie, `Authorization`, forwarding,
  tracing, or alternate auth header.
- Construct headers server-side from typed key class, key scope, plane, and
  selected workspace. Do not forward caller headers.
- For LangSmith API workspace discovery, start from the documented
  `X-API-Key` scheme and retain the `X-Organization-Id` conflict as an explicit
  row blocker.
- For control-plane reads, require exactly `X-Api-Key` plus `X-Tenant-Id` as
  documented.
- For classic Agent Server calls, send only documented `X-Api-Key` unless
  higher-precedence evidence accepts another header.
- Reject Fleet-only `X-Auth-Scheme`, guessed workspace headers, unsupported
  legacy `ls__` keys, and any route/host not present in the accepted inventory.

## Official sources

Every source below was accessed on 2026-07-23.

| Source ID | Official primary source URL | Evidence used |
|---|---|---|
| `OFF-AUTH-001` | https://docs.langchain.com/langsmith/administration-overview | PAT/service-key definitions and prefixes; service-key scopes; `X-Tenant-Id`; documented missing-header `403` |
| `OFF-AUTH-002` | https://docs.langchain.com/langsmith/create-account-api-key | Supported key classes; service-key scope choices; default/regional endpoints; `LANGSMITH_WORKSPACE_ID` condition |
| `OFF-AUTH-003` | https://docs.langchain.com/langsmith/manage-organization-by-api | Organization-management header guidance; `/api/v1/workspaces` and `/api/v1/orgs/current` example paths |
| `OFF-AUTH-004` | https://docs.langchain.com/langsmith/smith-api/workspaces/list-workspaces | `GET /api/v1/workspaces`, required `X-API-Key`, response fields |
| `OFF-AUTH-005` | https://docs.langchain.com/langsmith/api-ref-control-plane | Control-plane host classes, `X-Api-Key`, `X-Tenant-Id`, and v2 deployment/revision routes |
| `OFF-AUTH-006` | https://docs.langchain.com/langsmith/cicd-pipeline-example | Exact four-region LangSmith API and Deployment API hosts; self-hosted base paths |
| `OFF-AUTH-007` | https://docs.langchain.com/api-reference/deployments-v2/list-deployments | `GET /v2/deployments` generated route contract |
| `OFF-AUTH-008` | https://docs.langchain.com/api-reference/deployments-v2/get-deployment | `GET /v2/deployments/{deployment_id}` generated route contract |
| `OFF-AUTH-009` | https://docs.langchain.com/api-reference/deployments-v2/list-revisions | List-revisions generated route contract |
| `OFF-AUTH-010` | https://docs.langchain.com/api-reference/deployments-v2/get-revision | Get-revision generated route contract |
| `OFF-AUTH-011` | https://docs.langchain.com/langsmith/server-api-ref | Classic Agent Server plane, per-deployment `/docs`, and required `X-Api-Key` |
| `OFF-AUTH-012` | https://docs.langchain.com/langsmith/deployment-quickstart | Opaque deployment URL and classic `X-Api-Key` invocation example |
| `OFF-AUTH-013` | https://docs.langchain.com/langsmith/agent-server-api/system/health-check | `GET /ok` |
| `OFF-AUTH-014` | https://docs.langchain.com/langsmith/agent-server-api/system/server-information | `GET /info` response capabilities |
| `OFF-AUTH-015` | https://docs.langchain.com/langsmith/agent-server-api/assistants/search-assistants | `POST /assistants/search` |
| `OFF-AUTH-016` | https://docs.langchain.com/langsmith/agent-server-api/assistants/get-assistant-subgraphs | `GET /assistants/{assistant_id}/subgraphs` |
| `OFF-AUTH-017` | https://docs.langchain.com/langsmith/agent-server-api/threads/create-thread | `POST /threads` |
| `OFF-AUTH-018` | https://docs.langchain.com/langsmith/agent-server-api/threads/search-threads | `POST /threads/search` |
| `OFF-AUTH-019` | https://docs.langchain.com/langsmith/agent-server-api/threads/get-thread | `GET /threads/{thread_id}` |
| `OFF-AUTH-020` | https://docs.langchain.com/langsmith/agent-server-api/threads/get-thread-state | `GET /threads/{thread_id}/state` |
| `OFF-AUTH-021` | https://docs.langchain.com/langsmith/agent-server-api/thread-runs/create-run-stream-output | `POST /threads/{thread_id}/runs/stream` |
| `OFF-AUTH-022` | https://docs.langchain.com/langsmith/agent-server-api/thread-runs/get-run | `GET /threads/{thread_id}/runs/{run_id}` |
| `OFF-AUTH-023` | https://docs.langchain.com/langsmith/agent-server-api/stateless-runs/create-run-wait-for-output | `POST /runs/wait` |
| `OFF-AUTH-024` | https://docs.langchain.com/langsmith/openapi-security | Default LangSmith Agent Server `x-api-key` schema and absence of application-user auth endpoints |
| `OFF-AUTH-025` | https://docs.langchain.com/langsmith/fleet/code | Fleet-only `X-Auth-Scheme` distinction; excluded from classic baseline |
| `OFF-AUTH-026` | https://docs.langchain.com/langsmith/cloud | `/auth` appears only as a rate-limit category, insufficient as an operation contract |
| `OFF-PKG-001` | https://pypi.org/pypi/langsmith/json | Current public Python SDK metadata |
| `OFF-PKG-002` | https://pypi.org/pypi/langgraph-sdk/json | Current public Python Agent Server SDK metadata |
| `OFF-PKG-003` | https://pypi.org/pypi/langgraph-api/json | Current public Agent Server package metadata |
| `OFF-PKG-004` | https://registry.npmjs.org/%40langchain%2Flanggraph-sdk/latest | Current public JavaScript/TypeScript SDK metadata |
