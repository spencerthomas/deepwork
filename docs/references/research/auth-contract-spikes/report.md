# SPIKE-AUTH-002 API-key and workspace-header contract report

Date: 2026-07-23
Author disposition: `blocked-live-evidence`
Independent acceptance: not claimed

## Result

The retained matrix covers 14 required classic operations across four key
classes and 11 positive, missing, conflicting, unsupported, revoked,
permission, inaccessible-workspace, and forwarding-abuse context cases: 616
canonical rows.

- 432 documented positive or provider-observed negative combinations remain
  `blocked-live-evidence`.
- 184 missing-authority, conflicting-context, forwarding-abuse, or
  control-plane-missing-context combinations are
  `rejected` locally before dispatch.
- No row is `accepted-live`.

No sanctioned non-production classic account was supplied. The packet therefore
does not establish that the classic API-key baseline is ready to connect.
The opt-in live runner accepts no Agent Server origin and probes only the
official regional platform and control hosts. The documented authenticated
`GET /v2/deployments/{deployment_id}` response does not define an Agent Server
URL field, so data-plane rows remain blocked until an explicit response-field
contract is documented and independently accepted.

## Evidence classifications

| Evidence class | Retained source | What it establishes | Acceptance effect |
|---|---|---|---|
| Official primary documentation and public package metadata, tier 2 | `official-source-inventory.md` | Current key classes, regional platform/control host classes, official route templates, exact documented header names, and documentation conflicts | Does not establish live authorization |
| Installed public APIs/generated schemas, tier 2 | `installed-generated-inventory.md`, frozen `uv.lock`, `versions.json` | `langsmith==0.10.9` and `langgraph-sdk==0.4.2` request-construction and SDK safety limits | Does not establish live authorization |
| Pinned research/reference code, tier 4 | `pinned-source-inventory.md` | Revision-qualified generated contracts and SDK behavior for all three packet pins | Does not establish live authorization |
| Offline synthetic fixtures, tier 5 | `fixtures/`, probe tests, `matrix.json` | Fail-closed selection, caller-header rejection, redaction, error normalization, fixture hashes, and deterministic fallbacks | Cannot promote a provider row |
| Accepted live contract, tier 1 | none | No non-production account, server revision, tier, region, or authenticated provider transcript was collected | All live-dependent rows remain blocked |

## Required-plane inventory and disposition

| Plane | Required operation slice | Official route/host class | Documented headers | Disposition |
|---|---|---|---|---|
| LangSmith platform | Authorized organization/workspace discovery | `GET /api/v1/orgs/current`, `GET /api/v1/workspaces`; regional `api.smith.langchain.com` class | `X-API-Key`; conditional `X-Tenant-Id`; organization-management guidance also mentions `X-Organization-Id` | Block pending live key-class/context proof; no dedicated credential-validation route was established |
| Classic Deployment control plane | Deployment list/read and capability discovery | `GET /v2/deployments`, `GET /v2/deployments/{deployment_id}`; regional `api.host.langchain.com` class | `X-Api-Key` plus required `X-Tenant-Id` | Block pending sanctioned live confirmation |
| Classic Agent Server data plane | Health, capability, assistant/graph, thread/state, and run operations | Opaque per-deployment Agent Server host with API origin discovery unresolved; `/ok`, `/info`, assistant search/subgraphs, thread search/read/state, stateless/thread streaming, and run read | `X-Api-Key` only | Block pending a documented authenticated origin-discovery field and live confirmation; never copy platform/control workspace headers onto Agent Server |

The public sources did not establish one dedicated, complete “validate this
credential” method/route/schema. `GET /api/v1/workspaces` is retained as
authentication-bearing, authorization-aware discovery, not relabeled as a
universal validation endpoint.

## Key and context matrix

The exact key classes are:

1. personal access token;
2. single-workspace service key;
3. multi-workspace service key; and
4. organization-scoped service key.

For each operation and key class, the matrix retains no-context and documented
workspace-context rows plus missing auth, missing required context, wrong or
conflicting context, unsupported key/plane, caller forwarding, permission
denied, revoked key, and inaccessible workspace cases.

Documented control-plane reads require `X-Tenant-Id`. Classic Agent Server
documentation establishes only `X-Api-Key`; a workspace selection may identify
which server-owned deployment record is resolved, but it is not forwarded as an
Agent Server header.

## Contradictions and open contract cells

1. `X-Organization-Id` is unresolved for platform organization/workspace
   enumeration. Organization-management prose says it should be present in that
   workflow, while the generated workspace-list contract declares `X-API-Key`.
   The matrix retains both tier-2 observations and no final header set.
2. No dedicated public credential-validation endpoint with a complete method,
   route, auth, and error contract was found.
3. Classic Agent Server extra workspace-header behavior is undocumented.
4. Most negative provider status and error shapes are not live-confirmed.
   Synthetic rejection proves only Deep Work’s proposed boundary behavior.
5. Current package versions do not identify the hosted server revision.
6. The documented control-plane deployment response does not define an Agent
   Server URL field. An origin must never come from a generic example or caller
   input; a future live probe may accept one only from an explicit field in an
   authenticated documented control-plane response and after server-side URL,
   DNS, TLS, redirect, and provenance validation.

## Recommended server-only adapter boundary

The future application service should:

- store the provider credential only behind a server-owned opaque handle;
- type the target as platform, control, or data plane before selecting a host;
- use an immutable operation registry of official methods and route templates;
- allow only official regional platform/control host classes; keep data-plane
  dispatch disabled until an explicit Agent Server origin field from an
  authenticated documented control-plane response is independently accepted,
  then validate that returned origin server-side;
- construct exact auth/context headers server-side from key class and selected
  workspace;
- reject caller authorization, workspace, organization, host, cookie,
  forwarding, tracing, alternate-auth, duplicate, and newline-bearing headers;
- disable ambient credential lookup, environment proxy inheritance, and
  redirects for probes;
- never forward `X-Tenant-Id` or `X-Organization-Id` to classic Agent Server
  without accepted evidence;
- normalize provider errors to typed fixed messages without retaining provider
  bodies, header values, origins, or exception representations; and
- keep every unresolved source operation unavailable with the matrix fallback.

This probe code is evidence tooling only. It is not production adapter code.

## Downstream acceptance contributions

| Acceptance ID | Contribution only | Still required downstream |
|---|---|---|
| `SPIKE-AUTH-002` | Complete documented/installed/pinned/synthetic matrix and deterministic fallback | Independent accepted-live rows for the required classic baseline |
| `AC-DW-ONB-001-01` | Server-side key/context selection and redaction contract | Application persistence, browser, and log proof |
| `AC-DW-ONB-002-01` | Auth/header part of a classic source probe | Assistant and invocation capability proof |
| `AC-DW-FND-003-01` | Revoked/unauthorized modeling and redaction | Two-source isolation and partial-workspace behavior |
| `AC-DW-FND-003-02` | Header selection/stripping and typed target registry | Application host, redirect, SSRF, and open-proxy rejection |
| `AC-DW-FND-003-08` | Credential-free retained corpus and scrub report | Normalized application source-view proof |
| `AC-DW-QUAL-001-03` | Named gate and row dispositions | Release-manifest omission/disablement |
| `AC-DW-QUAL-001-04` | Synthetic auth/header abuse slice | Full cross-layer security suite |

## Independent review record

- Runtime-contract review: `PASS` on 2026-07-23 after correction of the
  current-organization header selection, strict validator semantics,
  case-specific negative transcripts, and Agent Server origin wording. The
  reviewer independently verified 616 rows, 154 fixtures, 432 blocked rows,
  184 local rejections, zero `accepted-live` rows, `matrix-valid`, and 51
  passing offline tests with one live test deselected.
- Security/compliance review: `PASS` on 2026-07-23 after correction of raw
  header/context/reference/origin scrubbing, malformed-header rejection, and
  exact negative-fixture validation. The reviewer independently replayed the
  prior bypass cases, verified they now fail closed, and found zero prohibited
  retained values.
- Packet-level disposition: the documented/installed/pinned/synthetic corpus is
  accepted as a safe blocked matrix. Neither reviewer accepted a live row,
  `SPIKE-AUTH-002`, capability enablement, or product integration. Coordinator
  product/integration review and sanctioned non-production live evidence remain
  required.

## Reviewer-ready recommendation

The completed runtime-contract and security reviews accept the offline corpus as
a safe, source-precedence-aware blocked matrix. Product/integration review must
not accept `SPIKE-AUTH-002` or enable a classic source until a sanctioned
non-production session adds exact live rows for the required
key/header/account/plane combinations and resolves the platform organization
header conflict.
