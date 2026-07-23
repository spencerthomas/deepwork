---
tracker:
  kind: __SPIKE_SYMPHONY_TRACKER_ADAPTER_REQUIRED__
  provider:
    scope: __SPIKE_SYMPHONY_TRACKER_SCOPE_REQUIRED__
    credential: $__SPIKE_SYMPHONY_HOST_SECRET_REFERENCE_REQUIRED__
  required_labels:
    - agent-ready
  active_states:
    - Agent Ready
    - In Progress
    - Agent Review
    - Rework
  terminal_states:
    - Done
    - Canceled
    - Duplicate
polling:
  interval_ms: 30000
workspace:
  root: $__SPIKE_SYMPHONY_SAFE_WORKSPACE_ROOT_REQUIRED__
hooks:
  after_create: |
    echo "This staged WORKFLOW.md is not executable until SPIKE-SYMPHONY-001 is accepted."
    exit 86
  before_run: |
    echo "This staged WORKFLOW.md is not executable until SPIKE-SYMPHONY-001 is accepted."
    exit 86
  after_run: |
    true
  before_remove: |
    true
  timeout_ms: 60000
agent:
  max_concurrent_agents: 2
  max_turns: 20
  max_retry_backoff_ms: 300000
  max_concurrent_agents_by_state:
    Agent Ready: 2
    In Progress: 2
    Agent Review: 1
    Rework: 1
codex:
  command: "__SPIKE_PINNED_CODEX_APP_SERVER_COMMAND_REQUIRED__"
  approval_policy: __SPIKE_CODEX_APPROVAL_POLICY_REQUIRED__
  thread_sandbox: __SPIKE_CODEX_THREAD_SANDBOX_REQUIRED__
  turn_sandbox_policy: __SPIKE_CODEX_TURN_SANDBOX_POLICY_REQUIRED__
  turn_timeout_ms: 3600000
  read_timeout_ms: 5000
  stall_timeout_ms: 300000
---

# Deep Work Symphony workflow

> Staged, deliberately fail-closed draft. Do not copy to repository root or run it
> until `SPIKE-SYMPHONY-001` replaces every `__SPIKE_*` value, proves the selected
> adapter/config against pinned schemas, and replaces the failing hooks with
> reviewed safe commands.

## Required launcher and adapter policy

The accepted installation must pin `openai/symphony` to an exact reviewed revision
(initial evidence pin `1f3219bb1ea5f69a1305dc594e79b0db57c113c5`). The host
launcher—not an invented Symphony key—must start disabled by default, expose an
operator-owned emergency stop that terminates polling and active child sessions,
and document recovery. An invalid dynamic workflow reload is not a kill switch,
because the pinned implementation may retain its last valid configuration.

The launcher constructs a minimal child environment from an explicit allow-list
and strips inherited tracker, provider, production, signing, publishing, and
customer secrets. The tracker credential remains in the host adapter; agents use
separately approved issue/PR tools. Tests must inspect child environment, logs,
workspace files, telemetry, and proof artifacts for leakage.

Before Symphony creates a workspace or child process, the selected tracker adapter
must derive `Issue.dispatchable=false` unless all mandatory issue fields are
non-empty, the product spec is accepted, the ExecPlan is reviewed/active, every
decision/contract gate is accepted or explicitly non-blocking for that cell,
permissions and reviewers are approved, the issue has `agent-ready`, and every
blocker is terminal-success. The adapter validates the reachable blocker graph as
acyclic and fail-closes missing, self-referential, unknown, canceled, or duplicate
dependencies. Prompt checks below are defense in depth, not the scheduling gate.

`agent_review_required` is a mandatory boolean and must equal `true`; a present,
non-empty, or truthy-looking string is not sufficient. The accepted pilot must
also extend the launcher/adapter, or use a separately configured review queue, so
an implementation-to-`Agent Review` or review-to-`Rework` transition terminates
and releases the current Codex session before the next role is dispatchable. The
next role runs in a fresh thread over the preserved issue workspace. The adapter
records author session IDs, reviewer session ID, transition, attempt, and time,
and rejects review when the proposed reviewer session authored the attempt. The
pinned base Symphony lifecycle does not guarantee this separation; prompt text
and `max_turns` are not controls. `SPIKE-SYMPHONY-001` must prove the chosen
launcher extension or separate-queue design before these active states are used.

You are implementing one reviewed Deep Work tracker issue in its isolated
workspace. The issue tracker is the work control plane; the product specification
defines durable outcome; the active ExecPlan defines the self-contained
implementation approach. An implementation run hands off to Agent Review; a
separate review-only run hands off to Human Review or Rework.

## Start

1. Read root and nearest scoped `AGENTS.md`.
2. Read root `ARCHITECTURE.md`, `docs/PRODUCT_SENSE.md`, `docs/PLANS.md`, the
   issue's owning product specification, and its active ExecPlan.
3. Verify the issue identifier, current state, `agent-ready` label, dispatchable
   value, blocker relationships, risk, allowed paths, contract/decision gates,
   acceptance scenarios, branch, HEAD, and workspace before editing.
4. If required authority, input, secret, contract evidence, or external access is
   absent, record the concrete blocker through the approved tracker tool and stop.
   Do not guess, widen scope, or bypass a gate.

## State-specific role

- In `Agent Ready`, `In Progress`, or `Rework`, perform only the authorized
  implementation work below. A completed attempt moves to `Agent Review`.
- In `Agent Review`, start a distinct review-only session that did not author the
  attempt. Do not edit implementation. Inspect the complete diff, ExecPlan living
  sections, architecture/contract impact, tests, browser/telemetry proof, security,
  accessibility, rollback, and every review comment. Post prioritized findings.
  Actionable findings move the issue to `Rework`; a clean review moves it to
  `Human Review`. Stop after that transition.

## Work

1. Maintain the same ExecPlan's `Progress`, `Surprises & Discoveries`, `Decision
   Log`, and `Outcomes & Retrospective` as work proceeds.
2. Reproduce the problem or establish observable baseline proof before changing
   behavior.
3. Keep the change inside allowed paths and the legal architecture graph. Preserve
   unrelated user work.
4. Use public pinned dependencies and accepted contracts. Do not import private
   LangChain internals, invent provider endpoints, expose credentials, or turn a
   fixture into live-contract proof.
5. For application work, start the issue-qualified product demo/telemetry stack;
   keep ports, database/schema, object prefix, browser origin/storage, telemetry,
   and proof artifacts isolated from every other workspace.
6. Run the smallest checks while iterating. Before handoff, run required package,
   generated-contract, architecture, documentation, unit/contract, security,
   accessibility, and product-demo checks.
7. Review console/network errors and query relevant logs, metrics, and traces.
   Store only sanitized proof in the prescribed artifact path.
8. Review every human and agent pull-request comment. Address actionable feedback
   or record a reasoned response within issue authority.
9. Create separate non-agent-ready follow-up issues for out-of-scope discoveries;
   do not silently expand this change or apply `agent-ready` yourself.

## Handoff

Attach a concise proof packet containing outcome, changed interfaces, scenario IDs,
commands/results, browser and telemetry evidence, migration/rollback/capability
fallback, residual risks, and follow-ups. Ensure the issue and pull request link to
the updated ExecPlan. An implementation session moves to `Agent Review`; only the
distinct review-only session may move a clean item to `Human Review`. The launcher
must end the current role session at either transition; continuing the authoring
thread as reviewer or the reviewer thread as rework implementer is a dispatch
failure, not a recoverable prompt choice.

Do not self-approve a product/architecture/contract decision, destructive migration,
credential expansion, release, security exception, or merge. Stop safely if the
issue becomes ineligible. A retry or orchestrator restart must reuse preserved
workspace/tracker/PR evidence and must not duplicate an external effect.
