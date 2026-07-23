# Pinned local source inventory

Collected: 2026-07-23
Scope: read-only evidence for `SPIKE-AUTH-002`
Evidence class: pinned documentation, generated-contract, and reference-code
evidence only; no installed-package or live-contract acceptance

This inventory records what the three packet-pinned local repositories establish
about classic LangSmith authentication, workspace selection, hosts, and routes.
It does not promote any row to `accepted-live`. No credential, credential
reference, account identifier, customer value, reusable deployment endpoint, or
environment dump was used.

## Checkout and revision verification

The repositories were inspected with `git show <full-pin>:<path>` and `git grep
<full-pin>` so every finding is revision-qualified even though each checkout's
current `HEAD` also matched its expected pin.

| Source | Read-only local checkout | Required revision | Observed `HEAD` | Status |
|---|---|---|---|---|
| `SRC-LC` | `/Users/tomspencer/dev/deepwork/langchain-docs-reference` | `7b9215d708e0b57e6fbae7b5d0762c4118b8e309` | exact match | clean |
| `SRC-LCPY` | `/Users/tomspencer/dev/deepwork/langchain-packages/langchain` | `592055e15e138f5369dce95dd049ce22430996e2` | exact match | clean |
| `SRC-LG` | `/Users/tomspencer/dev/deepwork/langchain-packages/langgraph` | `31f90df3e6b0268fa77fd2d118a917d420b84a68` | exact match | clean |

No sibling repository was modified.

## `SRC-LC`: official documentation snapshot and generated contracts

### Key classes and workspace context

At the pinned revision:

- `src/langsmith/create-account-api-key.mdx:11-33` and
  `src/langsmith/administration-overview.mdx:96-125` distinguish:
  - a personal access token (PAT), scoped to its creating user and inheriting that
    user's permissions; and
  - a service key, scoped to one workspace, multiple workspaces, or the entire
    organization and recommended for applications/services.
- `src/langsmith/administration-overview.mdx:120-125` says `X-Tenant-Id`
  selects the target workspace. A PAT without it runs against the key's default
  workspace. An organization-scoped service key accessing workspace-scoped
  resources must provide it or receives `403 Forbidden`.
- `src/langsmith/create-account-api-key.mdx:76-86` says the SDK workspace setting
  is required when an API key is scoped to more than one workspace. This is a
  broad SDK setup statement, not evidence that every HTTP plane has the same
  omission rule.
- `src/langsmith/manage-organization-by-api.mdx:19-32` says non-organization
  keys default to the workspace where the key was created when `X-Tenant-Id` is
  absent; organization-scoped service keys fail on workspace-scoped resources
  without it. That document also says `X-Organization-Id` should be present on
  all organization-management requests and `X-Tenant-Id` on workspace-scoped
  requests.

The source establishes the names `X-Api-Key`, `X-Tenant-Id`, and
`X-Organization-Id`. HTTP header names are case-insensitive; evidence should
retain these canonical spellings while validators and stripping logic compare
them case-insensitively.

### Host classes and required-plane routes

| Plane / operation class | Verified host class | Pinned route evidence | Documented header evidence | Qualification |
|---|---|---|---|---|
| LangSmith platform credential/workspace discovery | regional platform API; default GCP US class is `api.smith.langchain.com`, with EU/APAC/AWS regional variants from `src/snippets/langsmith/saas-region-urls.mdx` | generated `GET /api/v1/workspaces` in `src/langsmith/langsmith-platform-openapi.json`; described as listing workspaces visible to the current auth in the current organization | generated schemes name `X-API-Key`, `X-Tenant-Id`, `Authorization: Bearer`, and `X-Organization-Id`; organization prose adds context rules above | The generated list operation can contribute to authorized enumeration. It does not name itself a universal credential-validation endpoint, so no dedicated validation route is established here. |
| Classic Deployment control plane | regional `api.host.langchain.com` class, corresponding EU/APAC/AWS regional variants; self-hosted control plane uses its configured host under `/api-host` | `GET /v2/deployments`, `GET /v2/deployments/{deployment_id}`, and `GET /v2/deployments/{deployment_id}/revisions/{revision_id}` in `src/langsmith/api-ref-control-plane.mdx:17-47`; create/update routes are documented but are outside a read-only connection probe | `X-Api-Key` **and** `X-Tenant-Id` in `src/langsmith/api-ref-control-plane.mdx:25-35,71-76` | Exact classic control-plane host and route class are documented. This plane is separate from a deployment's Agent Server. |
| Classic Agent Server health/capability | per-deployment Agent Server root URL, not the control-plane or platform host | generated `GET /ok` and `GET /info` in `src/langsmith/agent-server-openapi.json` | `X-Api-Key` on every hosted Agent Server request in `src/langsmith/server-api-ref.mdx:20-35` | `/ok` reports health; `/info` reports server version, flags, and metadata. The generated schema itself has no top-level security scheme, so the prose supplies the auth claim and live behavior remains unproved. |
| Classic Agent Server assistant discovery/read | same per-deployment Agent Server root | generated `POST /assistants/search` and `GET /assistants/{assistant_id}` | `X-Api-Key` on every hosted request | Search also acts as list according to the generated operation description. |
| Classic Agent Server thread discovery/read/create | same per-deployment Agent Server root | generated `POST /threads/search`, `GET /threads/{thread_id}`, and `POST /threads` | `X-Api-Key` on every hosted request | These are deployment-scoped, not organization-global. Creation is not required for a read-only credential probe. |
| Classic Agent Server run read/invoke | same per-deployment Agent Server root | generated `GET /threads/{thread_id}/runs`, `POST /threads/{thread_id}/runs`, and `POST /threads/{thread_id}/runs/stream`; the stateless `POST /runs/stream` example is also documented in `src/langsmith/deployment-quickstart.mdx:202-219` | `X-Api-Key` on every hosted request | Invocation needs separate sanctioned synthetic/live evidence; route existence does not authorize a mutation during credential validation. |
| Classic Agent Server protocol-v2 events | same per-deployment Agent Server root | generated `POST /threads/{thread_id}/stream/events` | `X-Api-Key` on every hosted request | Generated contract says reconnect uses body field `since`, not browser `Last-Event-ID`; availability is version/capability gated elsewhere. |

The cloud control-plane host table is derived by passing `prefix="api.host"` to
`src/snippets/langsmith/saas-region-urls.mdx`, yielding the host class
`api.host.langchain.com` and its documented region-prefixed variants. Agent
Server examples deliberately use a deployment root placeholder or localhost, and
the documented deployment response does not define an Agent Server URL field.
The snapshot therefore justifies neither constructing a deployment URL from an
ID nor accepting a caller-provided origin. A future connector may accept an
origin only from an explicit authenticated documented control-plane response
field whose URL and provenance validation has been independently accepted.

### Generated-platform ambiguity

`src/langsmith/langsmith-platform-openapi.json` defines four security schemes:
`X-API-Key`, `X-Tenant-Id`, bearer authorization, and `X-Organization-Id`.
However, several operations express those schemes as separate OpenAPI security
alternatives. For example, `GET /api/v1/workspaces` lists API key,
organization-ID, or bearer alternatives, while
`src/langsmith/manage-organization-by-api.mdx:32` says the organization header
should be present on all organization-management requests.

This is an unresolved generated-contract/prose ambiguity, not permission to send
an organization or workspace header speculatively. Preserve both observations in
the matrix, assign an owner and deterministic fallback, and keep affected
combinations `blocked-live-evidence` until higher-precedence evidence resolves
the actual conjunction and key-class behavior.

### Additional non-baseline distinctions

- `src/langsmith/fleet/code.mdx:36-37` documents Fleet Agent Server calls with a
  PAT in `X-Api-Key` plus `X-Auth-Scheme: langsmith-api-key`. That special scheme
  must not be generalized to classic deployment calls.
- `src/langsmith/custom-auth.mdx` documents user-defined Agent Server
  authorization such as `Authorization: Bearer`. Custom deployment auth is a
  separate source configuration, not a substitute for the classic API-key
  baseline.
- `src/langsmith/server-api-ref.mdx` documents `X-Api-Key` for hosted Agent
  Server calls but does not document `X-Tenant-Id` as a universal Agent Server
  header. The workspace header therefore must not be copied from control-plane or
  platform calls onto a deployment merely because the same key is used.

### Integrity hashes for the inspected `SRC-LC` files

| Pinned path | SHA-256 |
|---|---|
| `src/langsmith/api-ref-control-plane.mdx` | `207b8e8069118099ba82e4921f4783586ecabc5c4da6d41ca4cd0a6df2a6bb71` |
| `src/langsmith/server-api-ref.mdx` | `46c5bff977360d1d3031b301c1b11f2c7a94eadf623f95f636f51e315196d228` |
| `src/langsmith/administration-overview.mdx` | `d4bccb5b1b94ee9c37a529a7e41704bdfeb1ef0698f7e0807911acddcd26ac0e` |
| `src/langsmith/manage-organization-by-api.mdx` | `247b347a0df87b9339efe25f2891156675ca8ccb73f719a9fece99eedd65a303` |
| `src/langsmith/create-account-api-key.mdx` | `03e39833bb807440ff37c1fd8db439ab64ccc6ad1f72f61e0c45665e0dacfa62` |
| `src/langsmith/agent-server-openapi.json` | `0b4d3d1e2da065a50a53838e7f63f5d90763a1dc759b165dd7a4409b5959888c` |
| `src/langsmith/langsmith-platform-openapi.json` | `84c1e69d6a2123304eabf7a9819356db17bd784c35805548fbd4bd463aaec563` |
| `src/snippets/langsmith/saas-region-urls.mdx` | `4b65548aa7cd43a72c5743e797aeb46088271857bd1ea5af3906fe27331ae168` |

## `SRC-LCPY`: LangChain Python reference source

The pinned LangChain repository does **not** vendor the LangSmith Python client's
request builder and therefore does not establish API-key, workspace-header,
host, or route behavior for this spike:

- `libs/core/pyproject.toml:27` accepts `langsmith>=0.3.45,<1.0.0`.
- The pinned `libs/core/uv.lock` resolves that dependency to `langsmith==0.8.18`.
- `libs/core/langchain_core/tracers/langchain.py:11-13,75-81` imports and
  delegates to `langsmith.Client`; it does not construct the relevant auth
  headers.

Repository-wide pinned searches found no relevant `X-Tenant-Id`,
`X-Organization-Id`, `X-Auth-Scheme`, or `LANGSMITH_WORKSPACE_ID` implementation
in this source. Unrelated third-party test fixtures containing `x-api-key` are
not LangSmith contract evidence.

Consequently `SRC-LCPY` contributes a dependency/version lead only. The separately
installed or locked `langsmith==0.8.18` package must be inventoried and probed by
the packet before any client behavior is classified as installed/generated
evidence.

| Pinned path | SHA-256 |
|---|---|
| `libs/core/pyproject.toml` | `43fd9adfde6ceb623a2c662be4faeab4e1641281582b47753c446fcf7e0e4307` |
| `libs/core/uv.lock` | `db815e9b2395ccbb652965d8fe924e6c0ebf6d057415b842f82c39164d9c46ca` |
| `libs/core/langchain_core/tracers/langchain.py` | `a8eeaae47643599d28aa3bdf428590af0f44f74d87b1294127048a08698d7b84` |

## `SRC-LG`: LangGraph Python SDK reference source

The pinned package identifies itself as `langgraph-sdk==0.4.2` in
`libs/sdk-py/langgraph_sdk/__init__.py`.

### What the SDK establishes

- `libs/sdk-py/langgraph_sdk/_shared/utilities.py:26-69` resolves an explicit API
  key first, otherwise environment variables in `LANGGRAPH_API_KEY`,
  `LANGSMITH_API_KEY`, then `LANGCHAIN_API_KEY` order, and emits the key as
  lowercase `x-api-key`.
- Passing `api_key=None` disables environment loading
  (`libs/sdk-py/langgraph_sdk/_async/client.py:96-106`). An isolated probe should
  pass key material explicitly or use `None` for no-auth cases so an ambient
  environment cannot silently change a matrix cell.
- The client accepts an arbitrary base URL and additional client headers, and
  operation methods also accept per-call headers. It does not select
  `X-Tenant-Id`, `X-Organization-Id`, or `X-Auth-Scheme` from a typed key/workspace
  model.
- The SDK routes agree with the generated Agent Server contract for assistant,
  thread, and run operations, including `/assistants/search`,
  `/assistants/{assistant_id}`, `/threads`, `/threads/search`,
  `/threads/{thread_id}`, `/threads/{thread_id}/runs`, and
  `/threads/{thread_id}/runs/stream`.
- `libs/sdk-py/langgraph_sdk/_shared/utilities.py:167-194` rejects reconnect
  `Location` values whose scheme, host, or effective port differs from the
  configured base URL. Both synchronous and asynchronous HTTP clients call this
  validator before reconnecting.

### Safety limitations that Deep Work must not inherit

- `RESERVED_HEADERS` contains only the exact lowercase string `x-api-key`.
  `custom_headers` is an ordinary mapping and the check at lines 57-59 is
  case-sensitive. The reference code does not provide Deep Work's required
  case-insensitive forwarding-header denylist.
- Client-level and per-operation header mappings can otherwise include caller
  values such as authorization, cookies, host-like, workspace, organization,
  tracing, or alternate API-key spellings. This flexibility is appropriate for a
  general SDK but cannot be exposed through the Deep Work server boundary.
- The same-origin reconnect check protects a reconnect flow after a base URL is
  selected. It does not validate that the original base URL belongs to an
  allowlisted platform/control-plane/deployment host class.
- HTTP errors may include a provider body in exception notes or error logs
  (`libs/sdk-py/langgraph_sdk/_async/http.py:159-166`). The probe and future
  adapter must normalize/scrub errors before retaining or returning them.

The synthetic probe must therefore own a case-insensitive header allowlist,
reject user-supplied auth/workspace/organization/host/cookie/tracing headers,
select the typed plane and host before constructing the SDK client, pass only its
own exact auth/context headers, and sanitize all provider errors. SDK construction
alone is not proof of authorization or workspace isolation.

| Pinned path | SHA-256 |
|---|---|
| `libs/sdk-py/langgraph_sdk/__init__.py` | `b3e6c08531fc1f0ec27179a08bd759079a58b9f2aac5020ac4a6ea5dcd4d9e7a` |
| `libs/sdk-py/langgraph_sdk/_shared/utilities.py` | `d9c79bea534e19d69faee50959407506ea88f2c0734c29e88c08b55b549cfca5` |
| `libs/sdk-py/langgraph_sdk/_async/client.py` | `1b55564227f926341cf2f819f1e64e1dae6b2e578436c707c207407b7c9df8e0` |
| `libs/sdk-py/langgraph_sdk/_async/http.py` | `12d9fbea56acf32273743ec55567ad96eb1df473ba805eb89b97786d5515b177` |
| `libs/sdk-py/langgraph_sdk/_async/assistants.py` | `33d57934c401d4c517a9185f7f9cca6d0a979d6de41c279190bda03263b9e16e` |
| `libs/sdk-py/langgraph_sdk/_async/threads.py` | `93745296ac13ea55f625e9adaf0182047691c2280bce24cb77227249339583f4` |
| `libs/sdk-py/langgraph_sdk/_async/runs.py` | `cdc35b5f69139729264be73370195d88c410a0fd206538acfc492b2cd99e301d` |

## Matrix implications and unresolved evidence

1. Keep platform, control-plane, and per-deployment Agent Server rows separate;
   they have different host classes and context rules.
2. Treat PAT, single-workspace service key, multi-workspace service key, and
   organization-scoped service key as distinct key/context cases.
3. For the control plane, the pinned prose requires both `X-Api-Key` and
   `X-Tenant-Id`.
4. For a classic hosted Agent Server, the pinned prose establishes `X-Api-Key`
   but not a universal workspace/organization header. Do not forward platform
   context headers without higher-precedence evidence.
5. For platform workspace enumeration, retain the generated
   `GET /api/v1/workspaces` observation and the prose context requirements
   separately. The apparent security-scheme conjunction ambiguity remains
   unresolved.
6. No pinned source establishes one universal credential-validation endpoint or
   one header builder that is safe across all required planes.
7. None of these sources prove negative status/error bodies, revoked-key behavior,
   cross-workspace rejection, permissions, entitlements, account tier, region
   availability, or live header acceptance. Every such row remains
   `blocked-live-evidence` in the absence of sanctioned non-production classic
   access.

The deterministic fallback is to reject unsupported or ambiguous
key/plane/context combinations, send no guessed workspace or organization header,
retain credentials only server-side, and leave the affected operation unavailable
with a typed explanation.
