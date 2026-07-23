---
feature_id: DW-FUT-206
title: Team governance and application RBAC
release: v2
status: canonical-deferred-brief
decision_status: discovery-gated
owners: [api, security, enterprise]
surfaces: [web, api, audit]
runtime_scopes: [any]
source_refs: [SRC-DW, SRC-LC]
dependencies: [DW-FND-003, DW-FND-005]
last_reviewed: 2026-07-23
---

# Team governance and application RBAC

> This v2 brief is discovery-gated. It proposes application-level authorization without asserting current LangSmith organization/workspace role claims, SSO payloads, control-plane permissions, or Fleet administration contracts.

## User outcome

Teams can delegate Deep Work actions with least privilege, see why an action is allowed or denied across application and upstream boundaries, and audit consequential decisions without Deep Work becoming a contradictory shadow identity directory.

## Evidence and confidence

- `SRC-DW` requires team compatibility and future RBAC/governance while v1 remains deliberately narrow. Confidence: high for need, medium for application-role categories.
- `SRC-LC` includes organization/workspace concepts, but exact roles, claims, permission APIs, propagation, and source differences require verification. Confidence: unknown externally.
- Application-owned actions such as source administration, draft deployment, schedule management, memory review, and notification registration require explicit ownership. Confidence: high at domain level.

## Scope, ownership, and non-goals

API owns policy evaluation, effective permission, caching/invalidation, mutation enforcement, audit, and source-derived access. Security owns threat model, role design review, separation of duties, retention, and test program. Enterprise owns customer requirements, SSO/RBAC mapping policy, export, and administration experience.

In scope:

- Application roles/capabilities for task use, approval, source administration, agent draft/deploy, schedule management, memory/evaluation review, audit, and read-only operation.
- Effective permission composed from tenant/workspace membership, application grant, upstream/runtime access, connector ownership, resource scope, and source capability.
- Delegated/high-risk approval separation, policy explanation, access loss, and audit export.

Non-goals:

- Reimplementing upstream org/workspace governance, identity lifecycle, SCIM, directory, or SSO unless Deep Work is later explicitly chosen as authoritative.
- Allowing a Deep Work grant to widen upstream/runtime access, exposing hidden policy/resource existence, or relying on UI hiding as enforcement.
- One coarse role that collapses task, deployment, credential, schedule, memory, and audit risk.

## Primary journeys

1. **Assign role:** an authorized administrator selects tenant/workspace/resource scope, reviews resulting capabilities/conflicts, and grants a versioned application role.
2. **Understand access:** a user views effective permissions with contribution from application, upstream, connector/resource, and capability constraints.
3. **Perform/deny action:** API evaluates current policy at mutation time; UI previews denial, but server remains authoritative and logs the reason code safely.
4. **Separate duty:** a high-risk production deploy requires a distinct eligible reviewer; self-approval and stale approval are blocked.
5. **Lose access/export audit:** upstream membership or local grant revocation invalidates sessions/caches promptly; authorized auditors export complete non-secret evidence.

## Complete state matrix

| State/condition | Expected experience |
| --- | --- |
| Loading | Do not render privileged content/action while effective policy is unresolved; show a neutral authorization check. |
| Empty | A tenant with no custom grants uses the documented baseline; admin sees guidance, not an accidental open policy. |
| Effective/allowed | Show scoped capability, resource boundary, origin, expiry, and any separation requirement. |
| Denied | Explain a safe reason and remediation without revealing hidden tenant/resource/actor existence. |
| Conflicted | Fail closed when application/upstream/connector policies disagree; show which owner can resolve it without exposing sensitive details. |
| Pending approval | Freeze exact action/resource/version and list eligible reviewer criteria, not hidden user directory data. |
| Error/upstream unavailable | Fail closed for consequential mutation; permit only explicitly safe cached reads with freshness and provenance. |
| Offline | Cached authorized content follows offline policy; no role, approval, deploy, source, or credential mutation is queued offline. |
| Reconnecting | Refresh identity, memberships, grants, resource ownership, and policy version before privileged controls return. |
| Stale/revoked | Invalidate effective-permission cache/session, stop subscriptions/push where required, and remove inaccessible cached content. |
| Permission administration mobile | Allow read/audit and urgent revoke where safely designed; complex policy editing may require accessible desktop handoff. |
| Audit export | Show scope, retention/redaction, generation progress, immutable receipt/hash, expiration, and download authorization. |

## Proposed interfaces (non-binding)

Illustrative application concepts are `ApplicationRole`, `CapabilityGrant`, `ResourceScope`, `DerivedAccess`, `EffectivePermission`, `PolicyDecision`, `ApprovalRequirement`, and `AuditExport`. A decision records actor, tenant/workspace, action, resource type/ID, policy version, contributing grants/derived checks, outcome/reason code, time, and correlation ID—without secret values.

Exact upstream claims/API mappings remain undecided. The proposed evaluator applies a fail-closed intersection: local grants cannot exceed verified upstream/resource access, and source capability can only reduce executable actions. Policy caches must be short-lived and invalidatable; high-risk mutations always re-evaluate.

## Runtime capability and fallback

- Each source adapter reports whether workspace membership/role, resource ownership, and permission change signals can be verified.
- If current upstream access cannot be established, sensitive reads/mutations fail closed; application role never substitutes.
- Where no safe delegated model exists, retain v1 owner-only administration while ordinary runtime access follows upstream identity.
- No Fleet administration capability is inferred from runtime tier; it requires separate verified contract and policy mapping.

## Persistence and security

Persist role definitions/versions, scoped grants, approval requirements, derived-access references, decisions, revocations, cache invalidations, and audit exports. Minimize copied identity attributes and set retention. Credentials/SSO assertions are stored only in session/credential infrastructure, never audit payloads.

Test horizontal/vertical escalation, IDOR, confused deputy, stale membership, self-approval, scope wildcard, tenant switch, connector ownership, audit tampering, export leakage, and cache race. Policy changes are versioned, transactional, idempotent, and recoverable. Break-glass, if approved, is time-bound, monitored, and separately audited.

## Responsive and accessible behavior

Permission tables provide text summaries, filters, keyboard navigation, and accessible row detail; narrow screens use actor/role/resource cards. Policy source and denial are not color-only. Confirmation names exact actor, scope, capabilities, duration, and risk. Focus returns to changed grant and live regions announce access status. Exports have accessible progress/error states.

## Metrics and guardrails

- Authorization decision latency/availability, cache invalidation and upstream-revocation propagation time.
- Denial by reason, admin correction, overbroad-grant detection, dormant/expired grant, and reviewer-separation compliance.
- Unauthorized success, cross-tenant disclosure, stale-access success, self-approval bypass, and secret-in-audit/export; targets zero.
- Support burden and user comprehension of effective access.
- Guardrail: a local role never grants more access than verified upstream/resource authority.

## Dependencies

- `DW-FND-003` supplies sessions, application service, durable policy, credentials, and security baseline.
- `DW-FND-005` supplies org/workspace/tenant/actor/resource identity and audit model.
- Feature plans define their specific actions/resources; RBAC cannot invent or change feature semantics.
- External identity/RBAC verification spike is required before mapping any source claims.

## Rollout and rollback

1. Build a read-only action/resource inventory and policy simulation from fixtures.
2. Shadow-evaluate v1 owner model, compare decisions, and resolve false allow/deny without enforcement.
3. Feature-flag read-only effective-permission explanations for internal tenants.
4. Enforce one low-risk role boundary, then consequential actions with separation after security tests.
5. Pilot enterprise mapping/export only with verified source contracts.

Rollback returns administration to the narrower v1 owner-only model, revokes custom grants from enforcement, preserves versioned policies/audit, and never broadens access. Emergency disable defaults consequential mutations to denied.

## Executable acceptance scenarios

1. Given an operator may dispatch tasks but not deploy agents, when they call UI and API paths, then dispatch succeeds and deploy fails with the same safe policy reason.
2. Given upstream workspace access is removed, when cached access exists, then invalidation/re-evaluation removes Deep Work access before another privileged mutation succeeds.
3. Given a production deploy requires separation, when its proposer attempts review, then self-approval is blocked and an eligible distinct reviewer can decide the exact version.
4. Given a local admin tries to grant a resource absent upstream access, then the effective permission remains denied and no resource existence/content leaks.
5. Given two tenants and guessed IDs, when every query/mutation/export path is exercised, then no cross-tenant content or existence signal appears.
6. Given an authorized audit export, when generated, then actor/action/source/policy evidence is complete, immutable/verifiable, time-bound, and secret-free.
7. Given upstream permission service is unavailable, when a consequential mutation occurs, then it fails closed with a retryable operational state.

## Explicit discovery gates

- **External mapping:** verify current LangSmith/org/workspace/SSO and each runtime/source’s identity, role, ownership, membership-change, and permission contracts.
- **Policy model:** approve action/resource taxonomy, role bundles, scope inheritance, precedence/intersection, expiry, delegation, separation, and break-glass.
- **Threat model:** complete escalation, IDOR, tenant, cache, confused-deputy, audit/export, and recovery testing.
- **Lifecycle:** define join/leave/revoke, tenant switch, connector ownership transfer, source disconnect, and retention behavior.
- **Enterprise:** validate SSO/SCIM boundary, audit format, retention/legal hold, delegated approval, and support expectations without promising unowned directory features.
- **UX/accessibility:** prove administrators and users understand effective access and denial on desktop/mobile/assistive tech.

This brief stays non-ready until upstream mappings and policy semantics are accepted; uncertainty always resolves to the narrower v1 boundary.
