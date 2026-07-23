---
feature_id: DW-FUT-203
title: Slack, Linear, Teams, and external task channels
release: v2
status: canonical-deferred-brief
decision_status: discovery-gated
owners: [api, integrations, agent]
surfaces: [slack, linear, teams, web]
runtime_scopes: [classic, mda]
source_refs: [SRC-DW, SRC-LC]
dependencies: [DW-FND-003, DW-TASK-002, DW-OPS-001]
last_reviewed: 2026-07-23
---

# Slack, Linear, Teams, and external task channels

> This v2 brief is discovery-gated and provider-by-provider. It does not assume OAuth scopes, event shapes, interactive decisions, rate limits, enterprise approval, retention, or app-directory terms for Slack, Linear, Teams, or any other channel.

## User outcome

Authorized users can deliberately create and follow Deep Work tasks from existing work channels while retaining identity, tenant routing, provenance, untrusted-input isolation, duplicate protection, and a secure path into Deep Work for consequential review.

## Evidence and confidence

- `SRC-DW` identifies channels as a future acquisition/work surface. Confidence: medium for demand, low for provider priority and safe interaction depth.
- Existing composer, source, tenant/actor, notification, and untrusted-content proposals provide product primitives. Confidence: medium, dependent on v1 delivery.
- Every provider contract and enterprise installation model is external/version-sensitive. Confidence: unknown until official docs and live app verification per provider.

## Scope, ownership, and non-goals

Integrations owns provider adapters, installation lifecycle, event verification, rate limits, retries, and channel UX. API owns identity mapping, tenant routing, idempotency, task provenance, policy, and secure link issuance. Agent owns bounded translation of explicitly authorized untrusted content into a composer draft.

In scope:

- Install/connect, map external identity and location, configure allowed triggers and destinations, preview a task, dispatch with confirmed source/agent, post bounded status, and disconnect.
- Reconcile event replay, edits, deletes, retries, duplicate delivery, revoked identities, and provider outage.
- Verified interactive decisions only where the exact provider/identity/security contract meets Deep Work requirements.

Non-goals:

- Monitoring every message, autonomous task creation from ambient chat, copying private channel history, or treating a channel identity as trusted without mapping.
- Full Deep Work UI inside providers or a lowest-common-denominator abstraction that hides provider differences.
- Posting sensitive reasoning, secrets, full artifacts, or approval arguments into a channel by default.

## Primary journeys

1. **Install and map:** an administrator authorizes minimum scopes, selects tenant/workspace and allowed locations, maps identities, and reviews data/retention policy.
2. **Create deliberately:** an authorized mention/command/issue transition produces a preview with source content, attachments, target agent/source, and untrusted-input warning; user confirms dispatch.
3. **Follow:** the source thread/issue receives rate-limited status summaries and a secure link; Deep Work remains authoritative.
4. **Review safely:** a notification opens the current Deep Work approval; a channel-native decision is enabled only after a provider-specific gate.
5. **Reconcile/disconnect:** edits/deletes/replays update provenance or mark source unavailable without silently rewriting completed task history; uninstall revokes future access.

## Complete state matrix

| State/condition | Expected experience |
| --- | --- |
| Loading | Installation/configuration shows provider verification and mapping checks independently; event processing acknowledges within provider constraints without claiming task creation. |
| Empty | Explain required install, mapping, and allowed trigger; show no monitored locations when none are configured. |
| Connected | Show scopes, tenant/workspace mapping, allowed locations/triggers, last delivery, and revocation action. |
| Preview | Present exact imported content/attachments, actor mapping, destination, redactions, and dispatch confirmation. |
| Processing | Deduplicate by provider installation/event identity; source message shows bounded pending state where supported. |
| Error | Separate signature, mapping, permission, provider, task dispatch, and callback errors; retries are idempotent and auditable. |
| Provider offline/rate-limited | Queue only policy-approved status callbacks, respect retry hints where verified, and preserve a Deep Work activity event. |
| Permission denied | Reject before task creation/posting and avoid disclosing tenant, task, or channel existence across mappings. |
| Reconnecting/reinstalled | Reverify installation identity, scopes, mappings, and cursors before processing; never inherit mappings by display name. |
| Stale/edited/deleted source | Preserve immutable original provenance/hash, display current availability, and apply explicit policy for draft versus dispatched tasks. |
| Uninstalled/revoked | Stop ingest and callbacks, invalidate credentials/subscriptions, retain allowed historical provenance, and expose cleanup status. |
| Mobile | Provider interaction leads to a secure responsive Deep Work landing flow; preview/status messages remain concise and accessible. |

## Proposed interfaces (non-binding)

Illustrative application concepts are `ChannelInstallation`, `ExternalActorBinding`, `ChannelLocationPolicy`, `InboundEventEnvelope`, `TaskCreationDraft`, and `OutboundStatusIntent`. Provider adapters normalize only stable application needs while retaining raw provider event ID/version and provenance.

No provider route, scope, signature algorithm, webhook retry contract, or interactive payload is specified. Each adapter must verify current official contracts. Event processing uses installation plus provider event ID for idempotency, and task dispatch uses a separate application idempotency key.

## Runtime capability and fallback

- Channel creation depends on selected source/agent dispatch capability; channel support never implies runtime support.
- Status callbacks degrade to secure links when provider formatting, permissions, or rate limits cannot safely represent state.
- Consequential approvals remain in Deep Work unless the provider-specific identity, freshness, ordered-decision, editable-argument, and audit contract is verified.
- Minimum fallback is a signed/short-lived link opening a prefilled composer; no persistent channel ingest is required.

## Persistence and security

Persist installation/tenant mapping, encrypted credential reference, minimum verified scopes, allowed location/trigger policy, external actor binding, event idempotency, task provenance, callback intent/receipt, and audit. Retain raw event content only as allowed and minimize it after dispatch.

Verify webhook signatures and replay windows per current provider contract, validate tenant/location on every event, sanitize untrusted text/files/links, block SSRF and mention injection, and prevent external content from changing system instructions or tool permissions. Uninstall/revocation and source deletion propagate under a tested policy.

## Responsive and accessible behavior

Provider messages use plain-language status and meaningful links, not color/emoji alone. Deep Work landing pages meet responsive/accessibility requirements and restore task context. Admin mapping tables reflow to cards, are keyboard operable, and clearly associate provider location with Deep Work tenant/workspace. Interactive provider UI must meet that provider’s current accessibility affordances before use.

## Metrics and guardrails

- Authorized preview-to-dispatch conversion, task completion, and secure-link continuation by provider.
- Duplicate/orphan/wrong-tenant task rate, spoof/replay rejection, callback failure, uninstall revocation time, and sensitive-output escape; critical targets zero.
- Noise guardrail: callbacks per task/channel and user mute/uninstall rate.
- No ambient monitoring, no task creation without an allowed trigger, and no channel approval until provider-specific security acceptance.

## Dependencies

- `DW-FND-003` for credential, tenant, policy, idempotency, and audit service.
- `DW-TASK-002` for composer preview, attachments, and dispatch semantics.
- `DW-OPS-001` for activity/schedule/notification ownership and untrusted content.
- `DW-HITL-001` transitively governs any future channel decision behavior.

## Rollout and rollback

1. Prioritize providers from user research; complete one provider’s contract/threat-model gates at a time.
2. Signed prefilled-composer links with no ingest.
3. Internal installation plus explicit commands and read-only status links.
4. Feature-flagged callback summaries with enterprise pilot controls.
5. Consider verified native interactions separately per provider.

Rollback disables inbound trigger and outbound callbacks independently, revokes subscriptions/credentials where verifiable, preserves task/provenance audit, and directs users to Deep Work links. It does not delete completed tasks because a source event or installation disappears.

## Executable acceptance scenarios

1. Given a valid mapped actor and allowed trigger, when a provider event arrives twice, then one preview/task is created and both deliveries reconcile to the same provenance.
2. Given malicious prompt text, link, and attachment, when previewed, then they remain untrusted data and cannot alter target agent, permissions, tools, or tenant.
3. Given an unmapped or cross-tenant actor, when an event arrives, then no task or revealing callback is created.
4. Given a source message is edited after dispatch, then original provenance remains immutable and current source state is visibly reconciled under policy.
5. Given provider rate limiting, when status changes repeatedly, then bounded callbacks resume without burst, duplicate, or lost authoritative Deep Work history.
6. Given an installation is removed, when future events arrive, then they are rejected and credential/subscription cleanup is auditable.
7. Given native approvals are unsupported, when a task needs review, then the provider receives only a safe summary and current secure Deep Work link.

## Explicit discovery gates

- **Provider contract per channel:** verify OAuth/admin install, scopes, identity, event signatures, replay, edits/deletes, interactive payloads, rate limits, retention, enterprise approval, and uninstall APIs.
- **Identity/routing:** prove actor/tenant/location mapping, guest/shared-channel behavior, renames, migration, and fail-closed rules.
- **Threat model:** test prompt injection, spoofing, replay, malicious files/URLs, callback exfiltration, and cross-tenant routing.
- **Product policy:** select triggers, preview requirement, callback content, retention, notification volume, and approval boundary per provider.
- **Operations:** define event acknowledgement, retries, dead-letter handling, reconciliation, rate limiting, support, and revocation verification.
- **Accessibility/research:** validate provider messages and secure mobile continuation with representative users.

No provider adapter is implementation-ready merely because another provider’s gates passed.
