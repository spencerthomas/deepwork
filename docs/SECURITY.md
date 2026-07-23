---
title: Deep Work security architecture
status: canonical
last_reviewed: 2026-07-23
owners: [security, platform]
---

# Deep Work security architecture

Deep Work is multi-tenant from the first durable schema. Every application read,
mutation, stream, object, background job, and audit event is authorized with tenant
and actor context. Provider credentials remain server-side in a secret manager or
KMS; browser, native webview, fixtures, logs, traces, plans, errors, and screenshots
receive only sanitized health and capability views.

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
