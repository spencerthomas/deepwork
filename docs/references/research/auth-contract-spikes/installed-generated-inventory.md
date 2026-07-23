# Installed public API and generated-contract inventory

Collected: 2026-07-23
Evidence class: tier 2 installed public API/generated schema
Live acceptance: none

## Frozen environment

The isolated project lock selects:

| Distribution | Version | Role |
|---|---:|---|
| `langsmith` | `0.10.9` | LangSmith platform client and generated platform client |
| `langgraph-sdk` | `0.4.2` | Classic Agent Server client and public schemas |

The environment was created only under `tools/contract-spikes/auth/.venv` from
the packet-owned `pyproject.toml` and `uv.lock`. Inspection did not read an
ambient profile, API key, endpoint, workspace, organization, cookie, proxy
credential, or environment dump.

## `langsmith==0.10.9`

Installed `langsmith/client.py` constructs `x-api-key` from the configured API
key and adds `X-Tenant-Id` when `workspace_id` is configured. The client can
otherwise resolve both settings from process configuration or a profile, so the
probe must pass explicit values and never rely on ambient configuration.

The installed generated client contains `X-Tenant-Id` authentication helpers
and security-alternative resolution. This confirms the public client can emit the
workspace header. It does not establish which key class requires it for each
route, whether `X-Organization-Id` is conjunctive for workspace enumeration, or
the live response for a missing, wrong, revoked, or inaccessible context.

Relevant installed artifact hashes:

| Installed file | SHA-256 |
|---|---|
| `langsmith/client.py` | `f10813f0581bf04fc41fb082c8d00659d4e5e94460c26bf14a1e0644366a154f` |
| `langsmith/_openapi_client/_client.py` | `20c09654359eec39bc72eb5e274ddbb570b3923e01e855c45e1525302007d959` |

## `langgraph-sdk==0.4.2`

The installed Agent Server SDK:

- resolves an explicit `api_key`, otherwise tries supported ambient API-key
  variables, and emits the selected value as lowercase `x-api-key`;
- treats explicit `api_key=None` as a request not to load ambient key material;
- exposes the assistant, thread, and run routes retained by the operation
  inventory; and
- validates reconnect `Location` values as same-origin with the already selected
  base URL.

The SDK is intentionally general-purpose: it accepts an arbitrary base URL and
custom headers. Its reserved-header check contains only exact lowercase
`x-api-key`, so differently cased authority, workspace, organization, host,
cookie, forwarding, tracing, and alternate-auth headers are not a safe
application boundary. The offline probe therefore performs case-insensitive
rejection before SDK use and never accepts a caller-selected target.

Relevant installed artifact hashes:

| Installed file | SHA-256 |
|---|---|
| `langgraph_sdk/_shared/utilities.py` | `d9c79bea534e19d69faee50959407506ea88f2c0734c29e88c08b55b549cfca5` |
| `langgraph_sdk/_async/client.py` | `1b55564227f926341cf2f819f1e64e1dae6b2e578436c707c207407b7c9df8e0` |
| `langgraph_sdk/_async/http.py` | `12d9fbea56acf32273743ec55567ad96eb1df473ba805eb89b97786d5515b177` |

## Control-plane limitation

Neither selected installed package supplies Deep Work with a typed, safe
platform/control/data-plane target selector. The control-plane header/host
contract therefore remains sourced from the separate official and pinned
observations: regional `api.host.langchain.com` classes with `X-Api-Key` plus
`X-Tenant-Id`. Installing a client is not accepted authorization behavior.

## Disposition

These observations contribute exact installed request-construction behavior.
They do not promote any matrix row to `accepted-live`. The safe boundary passes
credentials explicitly, disables ambient lookup, rejects arbitrary headers and
targets, follows no unverified redirect, and retains no provider body.
