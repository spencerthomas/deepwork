---
title: Deep Work security architecture
status: canonical
last_reviewed: 2026-07-23
owners: [security, platform]
---

# Deep Work security architecture

This document states the **target** security architecture and, in the
"Implementation status" section, what is **actually implemented today**. Where the
two differ, the status section is authoritative for the current build; the target
is the direction, not a description of shipped controls. (Recorded in the audit at
`CODE_REVIEW-2026-07-27.md`.)

The target: Deep Work is multi-tenant from the first durable schema — every
application read, mutation, stream, object, background job, and audit event is
authorized with tenant and actor context. Provider credentials remain server-side
in a secret manager or KMS; browser, native webview, fixtures, logs, traces, plans,
errors, and screenshots receive only sanitized health and capability views.

## Implementation status (v1, as of 2026-07-27)

- **Tenancy/authorization: single-operator, not yet multi-tenant.** The durable
  schema (`apps/api` SQLite tables) has **no tenant or actor columns**, and a single
  shared `DEEPWORK_ACCESS_KEY` mints one `operator` actor. Task routes authorize
  that a live session exists but do **not** enforce per-actor/per-tenant ownership,
  so any authenticated session can read or act on any task. Tenant/actor scoping is
  target work, not a shipped control.
- **Provider credentials: server-side.** Model/deployment credentials are read only
  in server composition seams and are not returned to clients, written to task
  content, or included in the event stream (verified in the audit). This matches the
  target.
- **Sandbox GitHub credential: interim, in-agent-reach.** The sandbox push
  credential is currently a static `DEEPWORK_GITHUB_TOKEN` written into the sandbox
  filesystem, so it is within the executing agent's reach for the sandbox lifetime.
  The command is injection-safe (`shlex.quote`), but the durable control — a
  per-task, single-repo, short-lived GitHub App token minted and revoked outside the
  sandbox — is not yet implemented (roadmap A2.3).
- **Login hardening: partial.** Constant-time key comparison and secure session
  cookies are implemented; rate limiting, lockout, and a minimum key-entropy check
  are not.
- **Sanitization: implemented.** Secret redaction on objectives, reviewer-comment
  digesting, and SSRF-conscious endpoint validation are in place.

## Trust boundaries

- The browser calls only the Deep Work `/api/v1` contract and normalized stream.
- Provider endpoints and redirects are allow-listed and protected against SSRF,
  DNS rebinding, credential forwarding, oversized responses, and unsafe content.
- Model, tool, repository, web, file, diff, terminal, connector, and imported ZIP
  content is untrusted. Rendering never executes embedded HTML, instructions,
  links, paths, or code.
- Ordered HITL decisions preserve actor, request/config alignment, consequence,
  idempotency, staleness checks, and audit. There is no force-resolve path.
- Object access is tenant-scoped, short-lived, content-typed, scanned where
  required, and governed by explicit retention/deletion policy.
- Desktop deep links, remote origins, native capabilities, local storage, and
  updater signatures fail closed under their own qualification gate.

Security-sensitive capability claims remain unavailable while their named spike is
open. Architecture exceptions cannot waive secret, tenant, browser credential, or
authorization boundaries. Detailed abuse and release scenarios live in
`DW-QUAL-001` and each owning product spec.
