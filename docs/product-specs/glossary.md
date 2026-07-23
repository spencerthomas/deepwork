# Canonical glossary

These definitions remove overloaded terms from the current plans. Feature plans use them consistently.

## Work lifecycle

| Term | Definition |
|---|---|
| **Task** | Deep Work's product-level unit of work. It owns a title, source, agent, task type, user-facing status, and one primary thread. |
| **Thread** | Agent Server's durable conversation and state container. A task references one thread at one agent source. |
| **Run** | One execution attempt within a thread. A thread may contain sequential, queued, interrupted, cancelled, retried, or branched runs. |
| **Checkpoint** | A persisted state snapshot within a thread, used for inspection and alternate execution paths. |
| **Branch** | A user-facing alternate path created from a checkpoint. It remains associated with the originating thread unless a verified API requires another representation. |
| **Queued submission** | Input accepted while a run is active and scheduled using the runtime's supported multitask strategy. |
| **Task status** | Deep Work's normalized reducer output: queued, running, needs-review, done, failed, or cancelled. It is not copied from one upstream field. |

## Agents and runtimes

| Term | Definition |
|---|---|
| **Agent** | User-facing configured worker, including instructions, model, tools, permissions, skills, memory policy, and templates. |
| **Assistant** | Agent Server resource/configuration identifier used to start runs. It is one runtime representation of an agent. |
| **Graph** | Executable LangGraph definition behind an assistant or deployment. |
| **Deployment** | Hosted Agent Server environment exposing assistants, threads, runs, state, and streaming. |
| **Agent source** | Deep Work server registration that names an API endpoint, assistant identity, server-only authentication reference, workspace context, runtime kind, and tested capabilities. Clients receive a safe view with credential state, never the authentication reference. |
| **Classic LangSmith Deployment** | Public v1 baseline deployment path with documented control-plane and Agent Server contracts. |
| **Managed Deep Agent (MDA)** | Private-beta, CLI-managed deployment adapter. It is not assumed to expose every classic control-plane capability. |
| **Fleet agent** | Existing Fleet-owned agent connected for capability-tested invoke/read behavior. Deep Work does not promise public Fleet CRUD in v1. |
| **Local source** | Explicit development-only connection to `langgraph dev`; direct browser credentials and broad proxying remain disabled. |

## Execution

| Term | Definition |
|---|---|
| **Environment** | User-managed reusable execution configuration: base snapshot/image, setup script, egress policy, runtime limits, and repository defaults. |
| **Snapshot** | Immutable captured sandbox filesystem/runtime baseline used to create a sandbox efficiently. |
| **Sandbox** | Isolated execution instance scoped to a task/thread. It may expire and be reconstructed from its environment. |
| **Artifact** | Deliberate task output intended for review or download, such as a report, document, image, archive, or dataset. |
| **File** | A filesystem object exposed by state or sandbox capability. A file is not automatically an artifact. |
| **Attachment** | User-provided task input uploaded or referenced during composition. |

## Human control

| Term | Definition |
|---|---|
| **Interrupt** | Durable paused runtime state requesting user input or a decision. |
| **Approval request** | Deep Work projection of an interrupt's action requests and aligned review configuration. |
| **Decision** | Ordered approve, edit, reject, or respond value sent to resume an interrupted run. |
| **Plan approval** | A specialized interrupt asking the user to approve or edit the proposed execution plan. |
| **Cancel task** | Explicit durable run cancellation, separate from dismissing stale UI. |
| **Stale approval** | An inbox item whose server interrupt no longer exists. It is removed after refresh and never force-resumed locally. |

## Identity and organization

| Term | Definition |
|---|---|
| **Organization** | LangSmith billing and administrative boundary. Deep Work respects it but does not implement org governance. |
| **Workspace** | LangSmith resource boundary selected by the operator and included in control-plane context. |
| **Tenant** | Application/customer isolation axis passed to a deployment identity contract where required. It is not interchangeable with workspace. |
| **Actor** | End user identity used to scope threads, memory, and credentials in an agent deployment. |
| **Operator session** | Deep Work application session connecting an authenticated human to stored source and credential references. |

## Application layers

| Term | Definition |
|---|---|
| **Application service** | Deep Work's Python/FastAPI service. It owns application state and integrates with external control/data planes. |
| **Application worker** | Separate process from the same initial Python distribution that leases durable Postgres jobs/outbox work for webhooks, notifications, reconciliation, and object processing. It is not the agent runtime. |
| **Application stream** | Versioned browser-safe FastAPI event stream for an authorized task. The server owns provider SDKs, credentials, cursors, recovery, and normalization; the client receives an opaque application cursor. |
| **Application object** | Deep Work-owned attachment, quarantined import, or generated export stored through the application object-store boundary with Postgres metadata and lifecycle policy. It is distinct from a runtime artifact/file. |
| **Control plane** | LangSmith APIs for deployment and platform lifecycle. It does not own per-deployment task threads. |
| **Data plane** | Per-deployment Agent Server APIs for assistants, threads, runs, state, streaming, and supported crons. |
| **Domain package** | Pure TypeScript package containing client-safe identities, capabilities, statuses, safe errors, normalized events, reducers, and selectors with no framework or I/O dependency. |
| **Client SDK** | Browser-safe TypeScript client for the Deep Work HTTP/application-stream API. It maps generated DTOs to the domain package and contains no provider SDK, credential reference, or cross-source provider fan-out. |
| **Agent package** | Runtime-agnostic Python `deepagents` project deployed to Agent Server infrastructure. |
