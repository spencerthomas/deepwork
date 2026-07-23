---
feature_id: DW-CODE-001
title: Sandbox lifecycle, environments, snapshots, setup, and egress
release: v1
status: canonical-spec
decision_status: blocked-on-spikes
owners: [coding-runtime, api, agent-runtime, security]
surfaces: [web, pwa, desktop, api, agent]
runtime_scopes: [classic, mda, local]
source_refs: [SRC-FE, SRC-LC, SRC-DW, SRC-DP]
dependencies: [DW-FND-003, DW-FND-005, DW-ONB-002, DW-TASK-002]
contract_gates: [SPIKE-SANDBOX-001, SPIKE-SANDBOX-002, SPIKE-EGRESS-001]
last_reviewed: 2026-07-22
---

# Sandbox lifecycle, environments, snapshots, setup, and egress

## User outcome

A user can choose a reviewed coding environment, see a sandbox created for the task, understand setup and network access, recover when an idle sandbox expires, and know exactly what persists. Code execution is isolated from the Deep Work application service, starts from a versioned snapshot/configuration, and contains no long-lived provider or GitHub credentials.

## Evidence and confidence

| Evidence | Classification | Planning consequence |
|---|---|---|
| Prototype settings and task detail show fixture sandbox, environment, terminal, network, and snapshot concepts. | Prototype evidence at `26c698b`; simulated | Retain the mental model while defining resource ownership and all lifecycle states. |
| Pinned LangSmith docs describe managed sandboxes, snapshots built/captured from images or Dockerfiles, SDK file/execute operations, permissions, service URLs, and auth-proxy egress controls. | Documented at `7b9215d` | Classic LangSmith Sandbox is the first managed provider target, behind a pinned Python adapter. |
| Deep Agents documents sandbox backends and thread/assistant-scoped lifecycle patterns. | Documented, with application integration choices | Use a thread/task-scoped sandbox for v1; verify factory/state mapping in the starter Python agent. |
| MDA-managed sandbox integration and arbitrary connector routes are not a stable public baseline. | Gated/unknown | MDA is capability-detected; no assumed `/connectors/...` route is required for baseline file/runtime access. |

## Definitions

- **Environment**: a Deep Work-owned, reusable configuration naming snapshot/base, setup script version, resource profile, egress policy, and tool policy. It is not a running machine.
- **Snapshot**: a provider-owned immutable filesystem image/bundle referenced by ID and recorded version/provenance.
- **Sandbox**: an ephemeral provider runtime instance created for one task/thread from an environment.
- **Setup run**: a bounded, logged initialization command executed after sandbox creation and before agent work.

## Scope and ownership

### In scope

- Environment list/detail/select and versioned definition.
- Classic LangSmith Sandbox adapter for create, inspect, execute, file transfer, reconnect where supported, stop/delete, and snapshot reference.
- Thread/task-scoped sandbox mapping, idle TTL, explicit lifecycle, recreation after expiry, and cleanup.
- Snapshot selection plus controlled build/capture workflows where the accepted SDK contract permits.
- Versioned `setup.sh`, setup logs/status, timeout, retry from clean sandbox, and immutable task binding.
- Explicit egress allow-list policy and raw-port disclosure.
- Resource/quota/permission diagnostics and safe no-sandbox behavior.
- Local development adapter only if it remains isolated and passes the same capability contract.

### Out of scope

- Running agent shell commands on the FastAPI host, Next.js server, or Tauri host as fallback.
- Shared assistant-scoped mutable sandboxes across unrelated users/tasks.
- Secret values in environment definitions, setup scripts, process environments, files, logs, snapshots, or command history.
- Arbitrary Docker build contexts from untrusted users without a separate hardened build pipeline.
- Native browser/computer-use environment; that remains a capability flag in `DW-CODE-003`.

### Ownership

- FastAPI owns environment CRUD/versioning, provider adapters, sandbox orchestration, authorization, quotas, lifecycle reconciliation, setup initiation, egress/auth-proxy policy, and audit.
- Postgres owns environment definitions/versions, snapshot references/provenance, task-sandbox mapping, lifecycle history, setup result metadata, and cleanup jobs.
- LangSmith or the selected provider owns sandbox instances, snapshots, execution, filesystem bytes, TTL enforcement, and provider permissions.
- The Python starter agent resolves a sandbox backend from a validated task/thread mapping; it does not create an untracked sandbox ad hoc.
- Next.js/Tauri own environment selection and lifecycle/recovery views using the same FastAPI API.

## Primary journey

1. An authorized user chooses a coding environment whose latest approved version shows runtime, snapshot, setup version, resource limits, egress destinations, and approval policy.
2. Preflight binds that exact version to the task. Later environment edits do not mutate a running task.
3. FastAPI requests a sandbox from the validated provider adapter, records external identity, and waits for Ready with bounded polling.
4. The service applies explicit auth-proxy/egress configuration and runs the immutable setup script without secrets.
5. Setup status and sanitized logs are visible. Only a successful setup releases the agent run.
6. The task reuses the mapped sandbox for follow-ups while healthy. Idle/expiry state is visible.
7. If expired, recreation starts from the same environment version; working-tree recovery is attempted only from an explicit persisted Git branch/artifact/snapshot, never implied.
8. Completion follows retention policy: preserve for a short review window, stop, then delete. A user can end early after confirmation.

## State matrix

| State | Required behavior | Recovery / transition |
|---|---|---|
| No environment | Coding dispatch blocked; explain create/select prerequisite. | Select/create or use non-coding task. |
| Environment draft | Editable, not selectable for production tasks. | Validate and publish version. |
| Environment validating | Check provider capability, snapshot, setup, egress syntax, permissions. | Publish or show field-level errors. |
| Snapshot resolving | Show provider and reference; no task execution yet. | Ready, missing, forbidden, or error. |
| Snapshot building/capturing | Show immutable source/provenance and bounded progress. | Ready, failed, cancel if supported. |
| Sandbox requested | Record idempotent create request; no duplicate instance on timeout retry. | Provisioning or reconcile. |
| Provisioning | Show provider state and elapsed time. | Ready, quota, timeout, failure. |
| Quota/capacity blocked | Preserve task draft and name provider/quota category. | Retry later, choose environment, or contact admin. |
| Permission denied | Do not retry automatically. | Reauthorize workspace/source. |
| Ready, setup pending | Agent remains blocked. | Start setup. |
| Setup running | Stream bounded sanitized output and timeout. | Ready, failed, or cancelled. |
| Setup failed | Agent does not start; preserve logs and exact environment version. | Retry in a clean sandbox or edit/publish new environment. |
| Setup timed out | Stop command/sandbox per policy; label timeout. | Retry with reviewed changes. |
| Active | Show instance ID suffix, created time, TTL, environment version, egress summary. | Execute, idle, stop, expire. |
| Idle/warm | Follow-up may reuse while health check passes. | Reuse or expire. |
| Expiring soon | Warn without claiming working state is durable. | Persist/commit work or extend only if allowed. |
| Expired/deleted | Mark instance unavailable and assess recovery sources. | Recreate from environment; restore explicit work source. |
| Provider state stale | Stop new commands and show last successful check. | Reconcile; never assume active/deleted. |
| Stop requested | Show stopping; reject duplicate stop. | Stopped or reconcile race. |
| Cleanup failed | Hide no data; record operational alert and retry bounded cleanup. | Reconcile/delete. |
| Egress denied | Surface host/port policy and safe request for environment change. | Continue without access or publish revised policy. |
| Auth injection unavailable | GitHub/third-party operations disabled; no token fallback in sandbox. | Fix proxy capability/config. |
| Offline client | Server task may continue; cached UI is stale and mutations unavailable. | Reconnect and reconcile. |
| Source without sandbox | Coding capability false; no local-host execution fallback. | Choose compatible source. |

## Proposed interfaces and runtime fallback

```ts
interface EnvironmentVersion {
  environmentId: string;
  version: number;
  name: string;
  provider: "langsmith" | "local_verified";
  snapshotRef?: { providerId: string; digest?: string; provenance: string };
  setupScriptRef: { contentHash: string; version: number };
  resources: { vcpus?: number; memoryBytes?: number; diskBytes?: number };
  egress: { mode: "allow_list"; destinations: string[] };
  idleTtlSeconds: number;
  status: "draft" | "published" | "retired";
}

interface SandboxBinding {
  bindingId: string;
  taskId: string;
  threadId: string;
  environmentId: string;
  environmentVersion: number;
  providerSandboxId: string;
  state: "requested" | "provisioning" | "setup" | "ready" | "idle" | "stopping" | "stopped" | "expired" | "error";
  createdAt: string;
  expiresAt?: string;
}
```

Proposed operations include environment/version endpoints, `POST /api/v1/tasks/{id}/sandbox`, sandbox status/log reads, and explicit stop/recreate commands. OpenAPI generates TS clients; React stream hooks do not own lifecycle mutations.

`SPIKE-SANDBOX-001` must pin the Python LangSmith SDK and capture create/get/list/delete, command run/reconnect, upload/download, snapshot reference/build/capture, TTL, permission, quota, timeout, and idempotency/error behavior. It must distinguish the sandbox control plane from Agent Server APIs.

`SPIKE-SANDBOX-002` must prove the Python Deep Agents backend factory maps one task/thread to the intended provider sandbox across initial run, follow-up, reconnect, failure, and expiry without configuring a backend forbidden by the selected runtime tier.

`SPIKE-EGRESS-001` must validate auth-proxy and access-control payloads, default provider posture, explicit allow-list semantics, redirects/DNS, raw ports, callbacks needed by GitHub, and safe update behavior. Deep Work's product default is explicit allow-list even if provider default allows broad HTTP/S.

If managed sandbox capability is absent, `sandbox: false` disables coding execution. Research/writing may use the agent's verified non-sandbox state/filesystem backend but cannot expose Execute/Terminal. MDA follows a separately verified adapter; no beta behavior is inferred.

## Persistence and security

- Environment versions and setup scripts are immutable/content-addressed after publication. Task binding records the exact version.
- Secrets are referenced only through the approved external secret/auth-proxy mechanism. Scan setup, snapshot build context, files, logs, environment dumps, and artifacts for accidental credentials.
- Enforce explicit egress allow-list and disclose every host/port class. Changes require a new environment version and audit event.
- Provider sandbox IDs are tenant/source scoped; all operations re-authorize creator/workspace permissions and do not trust IDs supplied by the browser.
- Apply size/time/output limits to commands, setup, file transfer, logs, snapshots, and build contexts.
- Sandbox content and command output are untrusted. Never render as HTML or execute on application/client hosts.
- Cleanup is fail-safe and observable. Database deletion of a binding cannot precede confirmed provider cleanup/tombstone policy.
- Snapshot capture is opt-in and warns that working files may become reusable image content; captured snapshots undergo secret/content checks before publication.

## Responsive and accessible behavior

- Environment choice shows name, version, provider, setup, egress, and readiness in text; mobile uses a full-screen details step before selection.
- Lifecycle states have persistent text and timestamps; progress is announced at phase boundaries only.
- Setup logs are keyboard-scrollable, use semantic preformatted text, and offer Download safe log; errors link to remediation.
- Egress destinations are a semantic list with host/port descriptions, not compact chips alone.
- Confirmation for Stop/Delete sandbox names what work may be lost and returns focus correctly.
- Reduced motion removes provisioning pulses; 200% zoom retains action access without horizontal page scroll.

## Metrics and guardrails

- Sandbox provision p50/p95, setup p50/p95, warm reuse rate, expiry/recreation rate, and cleanup latency/failure.
- Failure by quota, permission, snapshot, setup, egress, provider, and timeout category.
- Snapshot cold-start improvement and build/capture success.
- Egress-denied attempts by destination class without logging sensitive request bodies.
- Guardrails: zero application-host code execution; zero long-lived credential found inside sandbox/snapshot/log fixture; zero agent start before successful setup; 100% task bindings identify immutable environment version.

## Dependencies and rollout

- Depends on application service/security, source capability manifest, task composer, and GitHub proxy for authenticated repo operations.
- Phase 0: accept sandbox, Deep Agents factory, and egress spikes plus threat model.
- Phase 1: internal classic source with one reviewed snapshot/environment and setup script.
- Phase 2: environment versioning, TTL/recreation, and bounded file/terminal access.
- Phase 3: snapshot build/capture for authorized maintainers and allow-listed beta adapters.
- If provider behavior drifts, block new coding tasks, preserve existing task metadata, stop unsafe new commands, and offer provider/source diagnostics.

## Executable acceptance scenarios

```gherkin
Scenario: Setup failure prevents agent execution
  Given a published environment whose setup fixture exits nonzero
  When a coding task provisions a sandbox
  Then sandbox state becomes setup_failed
  And no agent run or coding command starts
  And sanitized setup logs and clean-retry action are available

Scenario: Expired sandbox never implies uncommitted work survived
  Given a task sandbox expires with uncommitted files
  When the user returns
  Then the UI marks the sandbox expired
  And lists only confirmed recovery sources such as Git branch, artifact, or snapshot
  And does not claim the uncommitted files will be restored

Scenario: Default egress is explicit allow-list
  Given a coding environment allows github.com and the package registry fixture
  When sandbox code requests an unlisted host and a raw database port
  Then both requests are denied
  And no credential is injected
  And the task shows an egress-policy event without the request body

Scenario: Source without sandbox cannot execute on the application host
  Given a connected source has sandbox false
  When the user chooses a coding template
  Then coding dispatch is blocked with a compatible-source action
  And FastAPI, Next.js, and Tauri execute no shell command as fallback
```
