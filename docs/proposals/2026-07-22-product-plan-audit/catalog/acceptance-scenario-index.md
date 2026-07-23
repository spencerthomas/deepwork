# Acceptance scenario index

Status: staged proposal; IDs are stable review identifiers, not passing test claims
Last reviewed: 2026-07-23

## Stable ID policy

Every v1 feature acceptance scenario has the identifier `AC-<feature-id>-NN`.
`NN` is the scenario's one-based order in the linked plan's **Executable acceptance
scenarios** section at this proposal snapshot. This table freezes both order and
title. After review, scenario IDs move into product-spec metadata and a generated
`docs/generated/feature-coverage.md`; existing IDs are never renumbered, and new
scenarios append or receive an explicitly reviewed ID.

The 28 v1 plans contain 179 feature scenarios. A feature scenario proves one
bounded contract. The twelve `E2E-V1-*` scenarios below compose them into release
stories and are the exact owners of the twelve program acceptance criteria in
[FINAL-PLAN.md](../FINAL-PLAN.md#11-v1-program-acceptance).

## V1 program end-to-end scenarios

| ID | Executable release story | Required supporting scenarios | Retained proof |
|---|---|---|---|
| `E2E-V1-01-FIRST-VALUE` | From a clean account with no stored source, sign in through the API-key baseline, choose an authorized workspace, register a pinned classic deployment, dispatch a non-coding task, follow it to a useful result, and record elapsed time at or below 15 minutes. | `AC-DW-ONB-001-01`, `AC-DW-ONB-002-01`, `AC-DW-ONB-002-04`, `AC-DW-TASK-002-01`, `AC-DW-TASK-003-01` | Timed browser trace, sanitized API/source correlation, task/result artifact, and no-secret scan. |
| `E2E-V1-02-TRUTHFUL-RUNTIME` | Run the same source selection against classic, an unentitled MDA account, an unaccepted Fleet cell, and an unsupported capability; classic remains usable and every other cell is absent or explanatory without a guessed request. | `AC-DW-AGENT-001-01`, `AC-DW-AGENT-001-02`, `AC-DW-AGENT-001-06`, `AC-DW-AGENT-001-07`, `AC-DW-FND-004-06` | Capability manifests, adapter-call ledger, negative network assertions, and screenshots of fallbacks. |
| `E2E-V1-03-DURABLE-CORE` | Accept an application job, saved draft, notification intent, and idempotent mutation; terminate API and worker processes at named boundaries; restart and prove each record converges once without losing accepted work or changing upstream authority. | `AC-DW-FND-003-03`, `AC-DW-FND-003-07`, `AC-DW-AGENT-003-07`, `AC-DW-OPS-001-05`, `AC-DW-OPS-002-04` | Migration/database snapshots, job/outbox history, restart logs/traces, and duplicate-effect assertions. |
| `E2E-V1-04-CREDENTIAL-BOUNDARY` | Connect a private source and GitHub repository, complete one authorized operation, then inspect browser bundles/storage, service-worker cache, desktop bridge where enabled, sandbox, logs, traces, screenshots, errors, and public API shapes; no reusable provider credential or `authRef` appears. | `AC-DW-ONB-001-01`, `AC-DW-FND-003-08`, `AC-DW-CODE-002-01`, `AC-DW-SURF-002-01` | Automated secret/schema scan, storage/cache dump, redacted telemetry query, and cross-tenant negative results. |
| `E2E-V1-05-RECONNECT` | During an active classic task, disconnect the client, terminate an API replica, expire replay, and restart the worker; the upstream run continues, the application stream resumes or hydrates authoritatively, and every durable event appears once. | `AC-DW-TASK-003-01`, `AC-DW-FND-004-01`, `AC-DW-FND-004-02`, `AC-DW-FND-005-03`, `AC-DW-SURF-001-02` | Ordered event transcript, cursor/hydration classification, process-failure timeline, and zero-duplicate assertion. |
| `E2E-V1-06-ORDERED-APPROVAL` | Present a repeated-name multi-action HITL batch on desktop and phone, edit only an allowed action, race a decision from another device, and submit; array alignment, allowed decisions, stale rejection, idempotency, audit, focus, and announcements remain correct. | `AC-DW-HITL-001-01`, `AC-DW-HITL-001-03`, `AC-DW-HITL-001-04`, `AC-DW-FND-004-03`, `AC-DW-FND-005-06` | Golden request/decision transcript, two-device browser proof, accessibility output, and decision audit record. |
| `E2E-V1-07-CODING-DRAFT-PR` | From an authorized repository, create/bind a sandbox, run setup, make a bounded change, inspect exact-SHA files/diff, create one draft PR after a simulated timeout, observe authoritative CI, and complete phone review without implicit merge or leaked token. | `AC-DW-CODE-001-01`, `AC-DW-CODE-001-03`, `AC-DW-CODE-002-01`, `AC-DW-CODE-002-02`, `AC-DW-CODE-002-03`, `AC-DW-CODE-003-04`, `AC-DW-QUAL-001-01` | Sandbox/revision provenance, PR/CI IDs, phone trace, GitHub audit, token scan, and cleanup proof. |
| `E2E-V1-08-RESPONSIVE-ACCESS` | Complete sign-in, task dispatch/follow, steer, ordered approval, artifact/diff review, current-authority phone merge, and recovery at 320 CSS pixels, 200% zoom, keyboard/switch input, screen reader, touch, high contrast, and reduced motion. Installation/push is tested only on qualified cells. | `AC-DW-FND-002-03`, `AC-DW-FND-002-05`, `AC-DW-AGENT-002-07`, `AC-DW-CODE-002-03`, `AC-DW-CODE-003-04`, `AC-DW-SURF-001-01`, `AC-DW-QUAL-001-05` | Browser/device/AT matrix, focus and announcement capture, viewport screenshots, current repository/CI/protection proof, and qualified-cell manifest. |
| `E2E-V1-09-SECURITY-RECOVERY` | Execute the accepted abuse/recovery pack across tenant IDs, source URLs, redirects, webhooks, objects, untrusted content, sandbox paths/egress, stale mutations, backups/restores, and any enabled updater; every boundary fails closed and authorized state restores. | `AC-DW-AGENT-001-03`, `AC-DW-FND-003-02`, `AC-DW-TASK-002-03`, `AC-DW-CODE-003-01`, `AC-DW-OPS-001-06`, `AC-DW-QUAL-001-04`, `AC-DW-QUAL-001-06`, `AC-DW-SURF-002-05` | Security-suite report, restore comparison, audit/telemetry evidence, and zero unauthorized-effect assertion. |
| `E2E-V1-10-PERFORMANCE` | On the accepted reference device and load profile, exercise a 1,000-task multi-source inbox, long active stream, large activity/subagent/file/diff views, and reconnect. p75 local interaction stays below 200 ms, proposed p95 API/stream targets pass once accepted, frames/memory remain bounded, and assistive navigation remains usable. | `AC-DW-AGENT-002-08`, `AC-DW-TASK-001-01`, `AC-DW-TASK-003-01`, `AC-DW-OPS-001-07`, `AC-DW-QUAL-001-02` | Versioned dataset/profile, browser and API traces, memory/frame/latency report, and AT/keyboard results. |
| `E2E-V1-11-CONTRIBUTOR` | Two independent contributors start from clean supported machines with no provider credentials, follow only repository maps and stable commands, run both fixture levels, make one bounded cross-contract change, trigger/fix intentional architecture and generated drift, audit license/trademark posture from a clean fork, and produce reviewable proof. | `AC-DW-FND-001-01`, `AC-DW-FND-001-02`, `AC-DW-FND-001-03`, `AC-DW-FND-001-06`, `AC-DW-FND-001-07`, `AC-DW-FND-001-09`, `AC-DW-QUAL-001-07`, `AC-DW-QUAL-001-08`, `AC-DW-QUAL-001-09` | Two timed clean-clone logs, command outputs, intentional-failure diagnostics, license/trademark report, PR/proof packets, and contributor feedback. |
| `E2E-V1-12-OPERATIONAL-RELEASE` | Promote a compatible API/worker/web release through staged rings, round-trip an agent project, resolve a trace link or explicit unavailable state, migrate/restore, inject source/object/worker/notification failure, verify health/alerts/runbooks, and roll back application artifacts without losing authoritative source work; desktop/PWA beta cells can be disabled independently. | `AC-DW-AGENT-003-05`, `AC-DW-FND-003-01`, `AC-DW-FND-003-07`, `AC-DW-OPS-002-01`, `AC-DW-OPS-002-02`, `AC-DW-OPS-002-03`, `AC-DW-OPS-002-08`, `AC-DW-QUAL-001-06`, `AC-DW-SURF-001-06`, `AC-DW-SURF-002-06` | Build provenance, project checksums, trace classification, migration/backup/restore report, alerts and runbook timestamps, rollout metrics, rollback record, and post-rollback journey. |

## Capability-gated source scenario

| ID | Executable flagged story | Required supporting scenarios | Retained proof |
|---|---|---|---|
| `OPT-V1-01-FLEET` | Only after `SPIKE-FLEET-001` passes for the current account, connect Fleet, list one source-qualified agent, drive a task through inbox and one ordered approval, and disable the adapter again without affecting classic. No create/update/delete or inferred route is permitted. | `AC-DW-AGENT-001-09`, `AC-DW-TASK-001-01`, `AC-DW-HITL-001-01`, `AC-DW-FND-003-01` | Pinned request/response fixtures, account/tier/version manifest, negative CRUD network assertion, task/decision audit, and adapter rollback. |

## Feature scenario registry

| Feature | Owning plan | Stable scenario IDs and titles |
|---|---|---|
| DW-AGENT-001 | [plan](../plans/v1/dw-agent-001-runtime-sources-and-capabilities.md#executable-acceptance-scenarios) | AC-DW-AGENT-001-01: Classic happy path<br>AC-DW-AGENT-001-02: Capability fallback<br>AC-DW-AGENT-001-03: SSRF rejection<br>AC-DW-AGENT-001-04: Permission classification<br>AC-DW-AGENT-001-05: Credential revocation<br>AC-DW-AGENT-001-06: No-beta fallback<br>AC-DW-AGENT-001-07: Fleet gate<br>AC-DW-AGENT-001-08: Offline recovery<br>AC-DW-AGENT-001-09: Fleet read/invoke path |
| DW-AGENT-002 | [plan](../plans/v1/dw-agent-002-agent-index-detail-and-health.md#executable-acceptance-scenarios) | AC-DW-AGENT-002-01: Mixed catalog<br>AC-DW-AGENT-002-02: Identity-safe dispatch<br>AC-DW-AGENT-002-03: Permission-limited detail<br>AC-DW-AGENT-002-04: Stale/offline<br>AC-DW-AGENT-002-05: Upstream deletion<br>AC-DW-AGENT-002-06: Fleet gate<br>AC-DW-AGENT-002-07: Accessible responsive use<br>AC-DW-AGENT-002-08: Large list |
| DW-AGENT-003 | [plan](../plans/v1/dw-agent-003-create-draft-import-export-and-deploy.md#executable-acceptance-scenarios) | AC-DW-AGENT-003-01: Template to classic<br>AC-DW-AGENT-003-02: No implicit mutation<br>AC-DW-AGENT-003-03: Concurrent conflict<br>AC-DW-AGENT-003-04: Unsafe archives<br>AC-DW-AGENT-003-05: Deterministic round trip<br>AC-DW-AGENT-003-06: Failure isolation<br>AC-DW-AGENT-003-07: Reconnect/idempotency<br>AC-DW-AGENT-003-08: MDA boundary<br>AC-DW-AGENT-003-09: Fleet boundary<br>AC-DW-AGENT-003-10: Responsive review |
| DW-AGENT-004 | [plan](../plans/v1/dw-agent-004-model-profile-runtime-and-advanced-settings.md#executable-acceptance-scenarios) | AC-DW-AGENT-004-01: All-section disposition<br>AC-DW-AGENT-004-02: Supported model<br>AC-DW-AGENT-004-03: Missing credential<br>AC-DW-AGENT-004-04: Runtime-owned MDA<br>AC-DW-AGENT-004-05: Unknown imported field<br>AC-DW-AGENT-004-06: Deferred controls<br>AC-DW-AGENT-004-07: Offline conflict<br>AC-DW-AGENT-004-08: Accessible mobile |
| DW-AGENT-005 | [plan](../plans/v1/dw-agent-005-tools-connectors-permissions-skills-memory-and-subagents.md#executable-acceptance-scenarios) | AC-DW-AGENT-005-01: Connector to approval<br>AC-DW-AGENT-005-02: Revocation propagation<br>AC-DW-AGENT-005-03: Schema drift<br>AC-DW-AGENT-005-04: Boundary truth<br>AC-DW-AGENT-005-05: Organization memory<br>AC-DW-AGENT-005-06: Subagent safety<br>AC-DW-AGENT-005-07: MDA/Fleet boundaries<br>AC-DW-AGENT-005-08: Offline/mobile<br>AC-DW-AGENT-005-09: Malicious content |
| DW-CODE-001 | [plan](../plans/v1/DW-CODE-001-sandbox-environments-snapshots-setup-egress.md#executable-acceptance-scenarios) | AC-DW-CODE-001-01: Setup failure prevents agent execution<br>AC-DW-CODE-001-02: Expired sandbox never implies uncommitted work survived<br>AC-DW-CODE-001-03: Default egress is explicit allow-list<br>AC-DW-CODE-001-04: Source without sandbox cannot execute on the application host |
| DW-CODE-002 | [plan](../plans/v1/DW-CODE-002-github-auth-repository-pr-ci-merge.md#executable-acceptance-scenarios) | AC-DW-CODE-002-01: Private repository workflow leaks no installation token<br>AC-DW-CODE-002-02: PR create timeout reconciles to one pull request<br>AC-DW-CODE-002-03: Head change blocks a stale phone merge<br>AC-DW-CODE-002-04: Proxy unavailable has no token fallback |
| DW-CODE-003 | [plan](../plans/v1/DW-CODE-003-files-diff-terminal-browser-phone.md#executable-acceptance-scenarios) | AC-DW-CODE-003-01: Path traversal never leaves the task workspace<br>AC-DW-CODE-003-02: Diff comments bind to the reviewed head<br>AC-DW-CODE-003-03: Terminal fallback is honest<br>AC-DW-CODE-003-04: Phone completes the safe coding review loop<br>AC-DW-CODE-003-05: Unsupported browser never becomes simulated evidence |
| DW-FND-001 | [plan](../plans/v1/dw-fnd-001-repository-oss-and-delivery-foundation.md#executable-acceptance-scenarios) | AC-DW-FND-001-01: A clean contributor reaches a representative fixture experience<br>AC-DW-FND-001-02: UI harness and product demo have explicit proof levels<br>AC-DW-FND-001-03: Package direction is enforced<br>AC-DW-FND-001-04: A blocked Symphony issue cannot dispatch<br>AC-DW-FND-001-05: Two agent worktrees are isolated<br>AC-DW-FND-001-06: FastAPI and TypeScript contracts cannot drift silently<br>AC-DW-FND-001-07: Private beta is not a default prerequisite<br>AC-DW-FND-001-08: A publish failure is recoverable and attributable<br>AC-DW-FND-001-09: OSS license and trademark posture is forkable and explicit |
| DW-FND-002 | [plan](../plans/v1/dw-fnd-002-design-system-shell-and-demo-mode.md#executable-acceptance-scenarios) | AC-DW-FND-002-01: Demo is visible and isolated<br>AC-DW-FND-002-02: The UI harness cannot masquerade as product-demo proof<br>AC-DW-FND-002-03: A phone user can reach every destination and action<br>AC-DW-FND-002-04: A failed live source never becomes demo data<br>AC-DW-FND-002-05: Responsive focus and state survive a layout change<br>AC-DW-FND-002-06: Unknown capabilities remain honest |
| DW-FND-003 | [plan](../plans/v1/dw-fnd-003-application-service-state-and-security.md#executable-acceptance-scenarios) | AC-DW-FND-003-01: One revoked source does not take down the workspace<br>AC-DW-FND-003-02: The application service is not an open proxy<br>AC-DW-FND-003-03: A webhook side effect executes once<br>AC-DW-FND-003-04: Stale mutation cannot overwrite current state<br>AC-DW-FND-003-05: MDA and Fleet remain gated without accepted contracts<br>AC-DW-FND-003-06: Account deletion respects external ownership<br>AC-DW-FND-003-07: Accepted background work survives an API restart<br>AC-DW-FND-003-08: A public source view reveals no credential reference |
| DW-FND-004 | [plan](../plans/v1/dw-fnd-004-sdk-stream-and-fixture-contracts.md#executable-acceptance-scenarios) | AC-DW-FND-004-01: Protocol v2 reconnect renders every event once<br>AC-DW-FND-004-02: Expired cursor recovers through authoritative hydration<br>AC-DW-FND-004-03: Ordered HITL batch survives the full contract<br>AC-DW-FND-004-04: Aggregate remains usable during partial failure<br>AC-DW-FND-004-05: Fixture mode is contract-equivalent and network isolated<br>AC-DW-FND-004-06: Unknown MDA support produces no guessed request |
| DW-FND-005 | [plan](../plans/v1/dw-fnd-005-domain-identity-status-and-audit-model.md#executable-acceptance-scenarios) | AC-DW-FND-005-01: Identical provider IDs remain separate across sources<br>AC-DW-FND-005-02: Pending interrupt owns attention without erasing run state<br>AC-DW-FND-005-03: Cancel and reconnect converge on authoritative state<br>AC-DW-FND-005-04: Retry preserves every attempt<br>AC-DW-FND-005-05: Source outage preserves a historical outcome<br>AC-DW-FND-005-06: A stale approval is never recorded as accepted |
| DW-HITL-001 | [plan](../plans/v1/DW-HITL-001-ordered-approvals-plan-stale-mobile.md#executable-acceptance-scenarios) | AC-DW-HITL-001-01: Repeated tool names remain aligned by array order<br>AC-DW-HITL-001-02: Respond cannot be used to reject a side effect<br>AC-DW-HITL-001-03: Stale mobile approval is never submitted<br>AC-DW-HITL-001-04: Malformed batch fails safely |
| DW-HITL-002 | [plan](../plans/v1/DW-HITL-002-rubrics-goals-verification.md#executable-acceptance-scenarios) | AC-DW-HITL-002-01: Required failed criterion prevents automatic pass<br>AC-DW-HITL-002-02: Repair history remains visible<br>AC-DW-HITL-002-03: Unsupported runtime uses manual checklist honestly<br>AC-DW-HITL-002-04: Iteration cap stops the loop |
| DW-ONB-001 | [plan](../plans/v1/DW-ONB-001-auth-session-workspace-demo.md#executable-acceptance-scenarios) | AC-DW-ONB-001-01: API-key user selects a workspace without exposing the key<br>AC-DW-ONB-001-02: OAuth is unavailable and degrades deterministically<br>AC-DW-ONB-001-03: Workspace access is revoked during a session<br>AC-DW-ONB-001-04: Demo cannot cause external side effects |
| DW-ONB-002 | [plan](../plans/v1/DW-ONB-002-source-connection-deployment-first-task.md#executable-acceptance-scenarios) | AC-DW-ONB-002-01: Existing classic deployment becomes a verified source<br>AC-DW-ONB-002-02: MDA is unavailable and classic remains usable<br>AC-DW-ONB-002-03: Unsupported deployment automation hands off safely<br>AC-DW-ONB-002-04: A first non-coding task completes inside the onboarding target |
| DW-OPS-001 | [plan](../plans/v1/dw-ops-001-schedules-activity-and-untrusted-content.md#executable-acceptance-scenarios) | AC-DW-OPS-001-01: Classic lifecycle<br>AC-DW-OPS-001-02: MDA boundary<br>AC-DW-OPS-001-03: Fleet boundary<br>AC-DW-OPS-001-04: DST correctness<br>AC-DW-OPS-001-05: Replay protection<br>AC-DW-OPS-001-06: Malicious content<br>AC-DW-OPS-001-07: Partial source failure<br>AC-DW-OPS-001-08: Offline/reconnect<br>AC-DW-OPS-001-09: Responsive accessibility |
| DW-OPS-002 | [plan](../plans/v1/dw-ops-002-observability-traces-notifications-and-insights.md#executable-acceptance-scenarios) | AC-DW-OPS-002-01: Trace provenance<br>AC-DW-OPS-002-02: No trace<br>AC-DW-OPS-002-03: Event fan-out<br>AC-DW-OPS-002-04: Replay<br>AC-DW-OPS-002-05: Stale approval tap<br>AC-DW-OPS-002-06: Quiet hours<br>AC-DW-OPS-002-07: Revocation<br>AC-DW-OPS-002-08: Partial coverage<br>AC-DW-OPS-002-09: Offline/reconnect<br>AC-DW-OPS-002-10: Sensitive payload |
| DW-OPS-003 | [plan](../plans/v1/dw-ops-003-organizational-intelligence-layers-zero-one.md#executable-acceptance-scenarios) | AC-DW-OPS-003-01: Seed review<br>AC-DW-OPS-003-02: No direct writes<br>AC-DW-OPS-003-03: Qualified digest<br>AC-DW-OPS-003-04: No evidence<br>AC-DW-OPS-003-05: Selective review<br>AC-DW-OPS-003-06: Concurrent reviewers<br>AC-DW-OPS-003-07: Evidence revocation<br>AC-DW-OPS-003-08: Deployment isolation<br>AC-DW-OPS-003-09: Context Hub gate<br>AC-DW-OPS-003-10: Mobile review |
| DW-QUAL-001 | [plan](../plans/v1/dw-qual-001-accessibility-performance-security-testing-and-release.md#executable-acceptance-scenarios) | AC-DW-QUAL-001-01: A clean account completes the classic first-PR promise<br>AC-DW-QUAL-001-02: Every required async state has owned evidence<br>AC-DW-QUAL-001-03: Unverified runtime contracts cannot enter release scope<br>AC-DW-QUAL-001-04: Security boundaries withstand cross-layer abuse<br>AC-DW-QUAL-001-05: Primary journeys are accessible on supported surfaces<br>AC-DW-QUAL-001-06: A release can roll back without losing authoritative work<br>AC-DW-QUAL-001-07: A clean contributor checkout proves package boundaries<br>AC-DW-QUAL-001-08: Wire and public-package drift cannot merge silently<br>AC-DW-QUAL-001-09: Repository knowledge and architecture cannot drift silently<br>AC-DW-QUAL-001-10: Symphony development orchestration fails closed |
| DW-SURF-001 | [plan](../plans/v1/dw-surf-001-responsive-web-pwa-offline-and-push.md#executable-acceptance-scenarios) | AC-DW-SURF-001-01: The complete phone loop uses the shared product contract<br>AC-DW-SURF-001-02: Backgrounding does not cancel a run<br>AC-DW-SURF-001-03: Offline mode cannot replay sensitive intent<br>AC-DW-SURF-001-04: A stale push reveals no protected state<br>AC-DW-SURF-001-05: A service-worker update preserves work<br>AC-DW-SURF-001-06: Push unsupported has a complete fallback |
| DW-SURF-002 | [plan](../plans/v1/dw-surf-002-tauri-desktop-hosting-deep-links-and-updates.md#executable-acceptance-scenarios) | AC-DW-SURF-002-01: Clean desktop sign-in stores no provider credential<br>AC-DW-SURF-002-02: Hostile navigation remains outside privileged context<br>AC-DW-SURF-002-03: Signed-out deep link is bounded and authorized<br>AC-DW-SURF-002-04: Tray converges without becoming authoritative<br>AC-DW-SURF-002-05: A tampered update cannot install<br>AC-DW-SURF-002-06: Failed desktop qualification does not block v1 web |
| DW-TASK-001 | [plan](../plans/v1/DW-TASK-001-inbox-search-filter-status-pagination.md#executable-acceptance-scenarios) | AC-DW-TASK-001-01: Results from two sources merge without a global API<br>AC-DW-TASK-001-02: One source fails without hiding the failure<br>AC-DW-TASK-001-03: Canonical status favors a pending interrupt<br>AC-DW-TASK-001-04: Revoked permission removes cached content |
| DW-TASK-002 | [plan](../plans/v1/DW-TASK-002-composer-templates-attachments-rubric-plan.md#executable-acceptance-scenarios) | AC-DW-TASK-002-01: Dispatch creates exactly one task after a timeout<br>AC-DW-TASK-002-02: Requested plan approval never downgrades silently<br>AC-DW-TASK-002-03: Unsafe attachment is blocked before agent visibility<br>AC-DW-TASK-002-04: Coding task preflight shows all execution boundaries |
| DW-TASK-003 | [plan](../plans/v1/DW-TASK-003-detail-streaming-tools-reasoning-todos-reconnect.md#executable-acceptance-scenarios) | AC-DW-TASK-003-01: Protocol cursor expiry does not duplicate content<br>AC-DW-TASK-003-02: Unknown tool payload cannot crash the task<br>AC-DW-TASK-003-03: Hidden reasoning remains hidden<br>AC-DW-TASK-003-04: One source without resumable streaming uses the honest fallback |
| DW-TASK-004 | [plan](../plans/v1/DW-TASK-004-steering-queue-lifecycle-checkpoints-branching.md#executable-acceptance-scenarios) | AC-DW-TASK-004-01: Timed-out enqueue does not submit twice<br>AC-DW-TASK-004-02: Cancel loses a race to successful completion<br>AC-DW-TASK-004-03: Stale checkpoint never falls forward silently<br>AC-DW-TASK-004-04: Archive is local and reversible |
| DW-TASK-005 | [plan](../plans/v1/DW-TASK-005-journeys-artifacts-subagents.md#executable-acceptance-scenarios) | AC-DW-TASK-005-01: Research completion includes provenance without claiming truth<br>AC-DW-TASK-005-02: Working file is not automatically a final artifact<br>AC-DW-TASK-005-03: Unsupported subagent source stays honest<br>AC-DW-TASK-005-04: Coding outcome has distinct terminal substates |

## Program criterion mapping

| FINAL-PLAN criterion | Owning release scenario |
|---|---|
| 1. First value | `E2E-V1-01-FIRST-VALUE` |
| 2. Truthful runtime | `E2E-V1-02-TRUTHFUL-RUNTIME` |
| 3. Durability | `E2E-V1-03-DURABLE-CORE` |
| 4. Secure credentials | `E2E-V1-04-CREDENTIAL-BOUNDARY` |
| 5. Reconnect | `E2E-V1-05-RECONNECT` |
| 6. Approvals | `E2E-V1-06-ORDERED-APPROVAL` |
| 7. Coding evidence | `E2E-V1-07-CODING-DRAFT-PR` |
| 8. Responsive access | `E2E-V1-08-RESPONSIVE-ACCESS` |
| 9. Security/resilience | `E2E-V1-09-SECURITY-RECOVERY` |
| 10. Performance | `E2E-V1-10-PERFORMANCE` |
| 11. Contributor readiness | `E2E-V1-11-CONTRIBUTOR` |
| 12. Operational release | `E2E-V1-12-OPERATIONAL-RELEASE` |

## Pinned canonical success-criterion reconciliation

The criteria below are preserved from `deepwork@06f0515`. They are evidence, not a
second release checklist. Each has one executable owner after its audited
disposition; the twelve revised program criteria above remain canonical after
review.

| Source criterion | Disposition | One executable owner |
|---|---|---|
| `VISION-SC-01` sign-in to draft PR in under 15 minutes | Amend: the 15-minute target applies to first useful task; exact-revision draft PR is a separately measured coding journey. | `E2E-V1-01-FIRST-VALUE` |
| `VISION-SC-02` full phone loop | Retain on responsive web; install/push only where qualified; fresh GitHub authority still gates merge. | `E2E-V1-08-RESPONSIVE-ACCESS` |
| `VISION-SC-03` Fleet inbox/approval | Flagged and non-blocking; run only after the account-specific Fleet spike passes. | `OPT-V1-01-FLEET` |
| `VISION-SC-04A` trace link on every run | Amend to a verified link for trace-enabled runs and explicit unavailable classification elsewhere. | `E2E-V1-12-OPERATIONAL-RELEASE` |
| `VISION-SC-04B` portable Fleet-compatible project | Amend to deterministic portable Deep Agents project round-trip; no reverse Fleet CRUD promise. | `E2E-V1-12-OPERATIONAL-RELEASE` |
| `VISION-SC-05` LangChain-community forkability | Retain with clean-clone, community, license, attribution, trademark, and non-affiliation proof. | `E2E-V1-11-CONTRIBUTOR` |
| `ROADMAP-RC-01` fresh sign-in to draft PR under 15 minutes | Same amended split as `VISION-SC-01`. | `E2E-V1-01-FIRST-VALUE` |
| `ROADMAP-RC-02` installed-phone full loop | Retain the full phone loop on responsive web; installation is conditional. | `E2E-V1-08-RESPONSIVE-ACCESS` |
| `ROADMAP-RC-03` Fleet inbox/approval | Flagged and non-blocking. | `OPT-V1-01-FLEET` |
| `ROADMAP-RC-04A` trace link on 100% of runs | Amend to trace-enabled denominator plus explicit unavailable classification. | `E2E-V1-12-OPERATIONAL-RELEASE` |
| `ROADMAP-RC-04B` agent project round-trip | Retain as deterministic safe archive/schema round-trip. | `E2E-V1-12-OPERATIONAL-RELEASE` |
| `ROADMAP-RC-05A` zero secrets in sandboxes | Retain and extend across every client, cache, telemetry, and proof boundary. | `E2E-V1-04-CREDENTIAL-BOUNDARY` |
| `ROADMAP-RC-05B` untrusted webhook/schedule boundaries | Retain inside the cross-layer abuse/recovery pack. | `E2E-V1-09-SECURITY-RECOVERY` |
| `ROADMAP-RC-06A` checks and docs complete | Retain through two clean-clone contributor trials and drift failures. | `E2E-V1-11-CONTRIBUTOR` |
| `ROADMAP-RC-06B` MIT/trademark hygiene | Retain as a named fork/build-artifact legal and branding audit. | `E2E-V1-11-CONTRIBUTOR` |

## Evidence and readiness rules

- An ID is a traceability key, not proof. No scenario is passing until its reviewed
  ExecPlan supplies exact scaffold commands, environment/version, expected results,
  sanitized artifact location, and retained execution evidence.
- One implementation issue names one primary feature and only the scenario IDs it
  actually advances. Integration/release issues may compose several feature
  scenarios but do not become duplicate feature owners.
- A contract-gated step executes in fixtures with its deterministic fallback until
  the named spike is accepted. Fixture success never promotes a live capability.
- The generated post-integration trace is criterion -> E2E scenario -> feature
  scenario -> work item -> PR/build/environment -> proof. Missing or duplicate IDs,
  changed titles/order, broken links, or a release criterion without one E2E owner
  fail the documentation check.
- PWA install/push, Tauri, MDA, Fleet, schedules, Insights, MCP/Context, PTY, and
  browser cells appear in release proof only when their exact capability/platform
  gates pass. Their failure cannot make the responsive classic web baseline appear
  incomplete or falsely successful.
