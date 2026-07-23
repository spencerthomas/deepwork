# Staged AGENTS.md placement map

Status: proposal only. None of the files in this directory is active repository guidance. Copy a draft to its destination only after the review gates in `../integration/merge-map.md` pass.

The reviewed installation also creates root `ARCHITECTURE.md`, root `WORKFLOW.md`
only after `SPIKE-SYMPHONY-001`, and the canonical document taxonomy described in
`../FINAL-PLAN.md`. Those are not `AGENTS.md` destinations, but the staged agent
maps are incomplete without them.

## Draft inventory

| Staged draft | Eventual destination | Scope after installation |
|---|---|---|
| `proposed-AGENTS.root.md` | `deepwork/AGENTS.md` | Entire canonical monorepo unless a more specific file overrides it |
| `proposed-AGENTS.docs.md` | `deepwork/docs/AGENTS.md` | Product plans, research, design documentation, and future proposals |
| `proposed-AGENTS.apps-web.md` | `deepwork/apps/web/AGENTS.md` | Next.js web application and minimal same-origin request mediation |
| `proposed-AGENTS.apps-api.md` | `deepwork/apps/api/AGENTS.md` | Python 3.12 FastAPI application service and Postgres durable state |
| `proposed-AGENTS.apps-desktop.md` | `deepwork/apps/desktop/AGENTS.md` | Tauri host and desktop-only integrations |
| `proposed-AGENTS.packages-domain.md` | `deepwork/packages/domain/AGENTS.md` | Pure TypeScript identities, capabilities, normalized events, reducers, and safe errors |
| `proposed-AGENTS.packages-sdk.md` | `deepwork/packages/sdk/AGENTS.md` | Browser-safe Deep Work API/application-stream client, DTO mapping, and client contracts |
| `proposed-AGENTS.packages-agent.md` | `deepwork/packages/agent/AGENTS.md` | Python deepagents project, tools, middleware, schedules, and runtime tests |
| `proposed-AGENTS.packages-ui.md` | `deepwork/packages/ui/AGENTS.md` | Design tokens, reusable presentational components, and stories |
| `proposed-AGENTS.frontend-sandbox.md` | `deep-work-frontend/AGENTS.md` | Separate visual prototype repository and the one-way porting boundary |

The first nine destinations belong to the canonical `deepwork` repository. The frontend sandbox destination belongs to the sibling `deep-work-frontend` repository and does not inherit the canonical repository's root instructions.

## Instruction inheritance

Within `deepwork`, instructions narrow by directory:

1. `deepwork/AGENTS.md` establishes evidence precedence, repository roles, dependency direction, security, and minimum quality bars.
2. `deepwork/docs/AGENTS.md` adds plan and evidence requirements for everything under `docs/`.
3. An app or package `AGENTS.md` adds rules for that implementation boundary.
4. If guidance conflicts, the closest applicable `AGENTS.md` controls only within its directory. It must not weaken root security, credential, contract-verification, or accessibility requirements.

The frontend sandbox has a separate root and one standalone instruction file. Its output is design evidence, never an upstream dependency or product contract.

## Intended dependency direction

```text
apps/web ---------> packages/sdk ---------> packages/domain
    |                                          ^
    +-------------> packages/ui ---------------+
    |
    +-------------> apps/api HTTP and application-stream contracts

apps/desktop -----> exact trusted hosted apps/web origin and explicit host adapter contracts

apps/api ---------> Postgres, object storage, worker/outbox, and external platform adapters

packages/agent ---> pinned Python runtime and harness dependencies
```

- `packages/domain` must not import SDK/UI/app/framework/network/provider/environment/generated-wire or credential code.
- `packages/ui` may import `packages/domain` but must not import `packages/sdk`, app code, runtime SDKs, generated DTOs, or server-only modules.
- `packages/sdk` may import `packages/domain` but must not import React components (except an explicit leaf binding), app code, desktop code, provider SDKs, credential references, or Python package internals.
- `apps/web` composes SDK services and UI components. It owns route behavior but not product persistence or a parallel business API.
- `apps/api` owns product sessions, durable state, capability probing, per-source aggregation, upstream streams/cursors, secret-bearing integration mediation, worker/outbox, and the application API consumed by both web and desktop. It must not import the deployable agent package as application internals.
- `apps/desktop` hosts the exact trusted web origin and implements only desktop capabilities. It stores only a scoped Deep Work bootstrap/device key and must not fork product state, business logic, or provider credentials.
- `packages/agent` is independently deployable Python code. Communication with TypeScript packages occurs through verified wire contracts, not source imports.
- `internal/fixtures` owns deterministic synthetic language-neutral records/transcripts. Python provider/source conformance lives under `apps/api`; `internal/adapter-tests` owns TypeScript client/DTO/reducer conformance. `apps/web` composes an injected UI harness or product-demo client; SDK, UI, and domain do not reverse dependencies to obtain fixtures.

## Installation rules

- Review and install all canonical-monorepo drafts in one change so there is no period with contradictory package ownership.
- Create an app or package destination only when that app or package exists. Until then, keep its draft here.
- Install the frontend-sandbox draft in a separate pull request in `deep-work-frontend`.
- Copy draft contents verbatim first. Any review edits must be applied to the staged draft and destination together so the proposal remains an audit trail.
- Do not replace a destination that acquired independent guidance after this proposal was created. Reconcile it line by line and record the result in the decision register.
- After installation, validate discovery from the repository root and from each scoped directory, then link the governing `AGENTS.md` files from contributor documentation.
