---
feature_id: DW-FUT-201
title: Pure-OSS runtime tier
release: v2
status: proposed-brief
decision_status: discovery-gated
owners: [platform, api, agent]
surfaces: [self-hosted, web, desktop]
runtime_scopes: [oss]
source_refs: [SRC-DW, SRC-LC]
dependencies: [DW-FND-003, DW-FND-004, DW-AGENT-001]
last_reviewed: 2026-07-23
---

# Pure-OSS runtime tier

> This v2 brief is discovery-gated. “Protocol-compatible” is a conformance target, not a current claim. No open runtime implementation, license, deployment topology, or parity level is selected here.

## User outcome

Self-hosters can operate Deep Work without LangSmith, understand exactly which capabilities they own and which are unavailable, and complete the core task/stream/approval journey without hidden hosted dependencies.

## Evidence and confidence

- `SRC-DW` establishes open-source/self-hosting as long-term product intent. Confidence: high for direction, low for timing and operating model.
- `SRC-LC` provides open packages and protocol concepts, but does not by itself prove a complete supported Agent Server replacement or compatibility. Confidence: low until legal and conformance spikes close.
- The source-capability adapter and application service proposed in v1 make an honestly reduced tier plausible. Confidence: medium at architecture level, dependent on real adapter evidence.

## Scope, ownership, and non-goals

Platform owns deployment, upgrades, storage, queues, backups, observability, and operational guidance. API owns identity, tenancy, source adapter, reconciliation, and capability manifest. Agent owns runtime/checkpointer/store integration and behavioral conformance.

In scope:

- A vetted open runtime, PostgreSQL-compatible durable state, object storage, queue, and user-selected sandbox integration.
- Assistants/agents, threads/tasks, runs, state, streaming, HITL, and files at a tested minimum capability profile.
- Self-hosted identity integration, encryption, backup/restore, migration, health, diagnostics, and reduced-capability messaging.
- An explicit shared-responsibility model for operator versus Deep Work responsibilities.

Non-goals:

- Claiming hosted feature parity, recreating the LangSmith control plane, or shipping a bespoke orchestration engine before evaluating existing permissive options.
- Bundling a sandbox provider, identity provider, model provider, or production SRE service as an implicit dependency.
- Multi-tenant production support until isolation and operations gates pass.

## Primary journeys

1. **Evaluate:** an operator reviews topology, licenses, capability profile, resource estimate, security boundaries, and unsupported hosted features.
2. **Install:** the operator configures identity, database, object storage, queue, encryption, runtime, and sandbox adapter; preflight validates each dependency.
3. **Use:** an authorized user connects the OSS source, creates/invokes an agent, streams a task, resolves HITL, reconnects, and accesses artifacts.
4. **Operate:** health and diagnostics identify component ownership, degraded capability, stuck work, storage pressure, and required remediation.
5. **Upgrade/recover:** the operator backs up, rehearses migration, upgrades one supported path, and restores without duplicate or lost logical events.

## Complete state matrix

| State/condition | Expected experience |
| --- | --- |
| Loading | Connection/setup UI shows component-by-component probes; task UI uses the same source loading semantics as hosted tiers. |
| Empty | A new installation displays a guided preflight and no agents/tasks; empty is distinct from unreachable storage. |
| Healthy | Show verified capability manifest, version set, last health check, and operator ownership links. |
| Degraded | Name the failed component/capability and safe fallback; unaffected read/write paths remain available only when conformance proves safety. |
| Error/unavailable | Fail closed for mutations, preserve last known data read-only where safe, and provide a correlation ID plus operator diagnostic. |
| Offline | Web/PWA cache follows `DW-SURF-001`; the self-hosted server itself has no “offline success” mode. Mutations wait for authoritative connectivity. |
| Permission denied | Distinguish application role, runtime identity, and infrastructure denial without leaking other tenants or secrets. |
| Reconnecting | Resume only with a verified cursor/event contract; otherwise refetch state and label any stream gap. |
| Stale/version mismatch | Block unsafe mutation, show incompatible component versions/capabilities, and link migration guidance. |
| Backup/restoring/upgrading | Expose maintenance state, read/write restrictions, progress, failure boundary, and rollback availability. |
| Mobile | Core task/approval views remain usable; operator setup and diagnostics may be desktop-only with an explicit accessible handoff. |

## Proposed interfaces (non-binding)

The v1 `AgentSource`/capability model would gain an `oss` adapter with illustrative capabilities for assistants, threads, runs, stream resume, HITL, files, schedules, sandboxes, and control-plane operations. Proposed operator concepts include `DeploymentManifest`, `ComponentHealth`, `CompatibilityReport`, `BackupReceipt`, and `MigrationPlan`.

No server implementation, endpoint path, open protocol version, or component is selected. A conformance suite—not naming similarity—decides whether an adapter may advertise a capability. The external user-facing application API remains the versioned FastAPI boundary proposed by the architecture decision.

## Runtime capability and fallback

- Unsupported capabilities are absent from the manifest and produce specific UI guidance, never simulated success.
- If resumable streams fail conformance, clients recover by state refetch and disclose possible event-detail loss.
- If schedules, agent versioning, or managed sandboxes are absent, those controls remain disabled or route to separately configured providers.
- Until this tier passes release gates, Classic LangSmith Deployment remains the only supported production baseline; OSS may remain local/evaluation-only.

## Persistence and security

Operators own database/object-store/queue durability, encryption keys, backups, retention, and infrastructure access. Deep Work owns schemas, migration tooling, least-privilege guidance, application audit, secret references, and safe defaults. Credentials live in configured secret stores, not manifests, logs, or task records.

Tenant isolation, row/object authorization, sandbox boundary, egress control, SSRF protection, credential brokerage, image provenance, supply-chain integrity, and deletion must be independently tested. Backup artifacts are encrypted and restore tests prove tenant and audit consistency.

## Responsive and accessible behavior

User task experiences follow shared web/PWA/desktop accessibility requirements. Operator dashboards support keyboard navigation, text health summaries, accessible logs, non-color status, copyable diagnostics, reduced motion, and zoom/reflow. Dense topology tables collapse into ordered component cards on narrow screens.

## Metrics and guardrails

- Clean-install success and median time to first completed HITL task.
- Conformance pass rate by capability and supported version set.
- Recovery point/time achieved in tested backup/restore; migration success/rollback rate.
- Duplicate/missing logical event, stuck-run, unauthorized-cross-tenant, and secret-exposure rates; security targets zero.
- Operator support burden, patch latency, and infrastructure cost profile.
- Guardrail: no production-support claim until security, restore, upgrade, and conformance release gates pass.

## Dependencies

- `DW-FND-003` for application service, persistence, identity, security, and operations.
- `DW-FND-004` for SDK/stream/fixture contract and conformance harness.
- `DW-AGENT-001` for source adapters and honest capability manifests.
- All v1 task/HITL/coding features contribute tier-specific conformance scenarios; unsupported ones remain absent.

## Rollout and rollback

1. Legal/architecture evaluation with no distributable runtime claim.
2. Local single-user reference topology and automated conformance in CI.
3. Opt-in developer preview explicitly unsupported for production.
4. Single-tenant production pilot after security, backup, and upgrade drills.
5. Broader self-host support only after an operational service-level policy is approved.

Rollback preserves the database/object store, exports source metadata, stops new dispatch, and lets operators return clients to Classic Deployment. Every migration has a tested down/restore path or is explicitly irreversible before execution.

## Executable acceptance scenarios

1. Given clean documented prerequisites, when an operator installs the reference topology, then preflight passes and a user completes dispatch, stream, reconnect, and HITL without hosted calls.
2. Given a runtime lacks schedules, when source capabilities load, then schedule controls are absent/disabled with accurate guidance and no failing call is attempted.
3. Given a service restart mid-run, when components recover, then durable state reconciles with no duplicate logical event or approval.
4. Given a supported upgrade, when migration fails at a rehearsed checkpoint, then the operator restores the prior working version and data/audit invariants pass.
5. Given users in two tenants, when isolation tests attempt cross-tenant task, file, secret, and health access, then no content or existence signal leaks.
6. Given an operator on mobile opens a deep diagnostic, then a useful summary and accessible desktop handoff are shown rather than a broken table.

## Explicit discovery gates

- **Legal:** inventory and approve licenses, trademarks, redistribution, hosted-service restrictions, and dependency obligations.
- **Runtime selection:** evaluate existing permissive implementations before build; record why the selected path satisfies maintenance and governance needs.
- **Conformance:** pin protocol/packages and pass assistants, state, stream, HITL, files, cancellation, recovery, and idempotency suites.
- **Security:** complete sandbox/network/credential, tenancy, supply-chain, and data-deletion assessment with remediation.
- **Operations:** prove backup/restore, rolling or maintenance upgrade, rollback, diagnostics, capacity, and support ownership.
- **Product:** validate that self-hosters understand capability gaps and shared responsibility.

This brief cannot become implementation-ready, and the tier cannot be described as production-supported, until every gate has accepted evidence.
