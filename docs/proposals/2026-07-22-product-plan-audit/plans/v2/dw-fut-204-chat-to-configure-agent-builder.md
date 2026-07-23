---
feature_id: DW-FUT-204
title: Chat-to-configure agent builder
release: v2
status: proposed-brief
decision_status: discovery-gated
owners: [agent, web, api]
surfaces: [agent-builder]
runtime_scopes: [classic, mda]
source_refs: [SRC-FE, SRC-DW]
dependencies: [DW-AGENT-003, DW-AGENT-004, DW-AGENT-005]
last_reviewed: 2026-07-23
---

# Chat-to-configure agent builder

> This v2 brief is discovery-gated. Conversational generation is an alternative editor over the same versioned draft/deploy boundary, never a privileged configuration path. No runtime-specific project schema or generated patch contract is assumed.

## User outcome

Users can describe an agent change in plain language, understand every proposed file/setting/permission impact, accept or reject changes granularly, and deploy only through the normal validated versioned workflow.

## Evidence and confidence

- `SRC-FE` demonstrates interest in conversational agent configuration, but the prototype is interaction evidence only. Confidence: medium for discoverability, low for correctness/safety.
- `SRC-DW` requires project-based, versioned configuration and explicit deploy semantics. Confidence: high for the product boundary.
- A complete typed edit model, safe imported-context boundary, and high-precision generation have not been proven. Confidence: low until corpus evaluation and threat modeling.

## Scope, ownership, and non-goals

Agent owns the typed editable schema, generation prompt/tool boundary, validators, and evaluation corpus. Web owns conversation, questions, diff/risk/permission review, partial acceptance, and undo. API owns versioned draft persistence, authorization, secret references, conflict detection, and deploy handoff.

In scope:

- Bounded clarification, structured patch proposal, impacted file/setting inventory, permission/credential requirements, validation, individual hunk/item acceptance, undo, and handoff to versioned draft.
- Creating a new draft from a template or editing an existing draft.
- Capability-aware suggestions that distinguish verified, gated, unavailable, and unknown runtime features.

Non-goals:

- Direct live mutation/deploy, credential creation or secret viewing, unsupported tool invention, permission auto-grant, arbitrary filesystem editing, or free-form shell execution.
- Replacing forms/files for expert users, silently rewriting imported instructions, or claiming a chat answer proves runtime compatibility.

## Primary journeys

1. **Create:** user states intended job and constraints; builder asks bounded questions, proposes a template-backed draft, and explains every capability/permission.
2. **Modify:** user requests a change; builder targets the current draft version and returns a structured reversible patch with validation results.
3. **Review partially:** user compares before/after, rejects one permission/tool change, accepts other compatible edits, and receives revalidated output.
4. **Resolve conflict:** if another editor changes the draft, the generated patch becomes stale and must be regenerated/rebased—never silently applied.
5. **Deploy normally:** accepted patch becomes a saved draft revision; the separate Deploy action presents final diff, target, and capability checks.

## Complete state matrix

| State/condition | Expected experience |
| --- | --- |
| Loading | Show draft/version and capability context loading separately; chat input can draft locally but generation waits for authoritative context. |
| Empty | Explain examples and supported editable areas; offer template/form path without forcing chat. |
| Clarifying | Show which required fields remain unknown and allow explicit “leave unchanged/not applicable.” |
| Generating | Indicate bounded proposal generation, allow cancellation, and make clear no draft/live config has changed. |
| Proposed | Show structured diff, affected files/settings, permissions, credentials, warnings, validation, and accept/reject per item. |
| Partially accepted | Recompute dependent changes and validation; never leave hidden orphan edits. |
| Applied to draft | Display new draft revision and undo lineage; Deploy remains separate and disabled until validation passes. |
| Error | Separate model generation, schema, validation, save, and capability errors; retain user request and unchanged draft for retry. |
| Offline | Permit local request drafting and viewing cached draft with timestamp; no generation, apply, or deploy mutation initially. |
| Permission denied | Hide restricted config/secrets and prevent patch generation that would reveal them; explain required role. |
| Reconnecting | Refresh draft version and capabilities, then mark any generated proposal stale before apply. |
| Stale/conflicted | Show exact base/current version mismatch, block apply, and offer regenerate or manual rebase. |
| Mobile | Support simple clarification and summary review; complex multi-file diff uses accessible drill-down or desktop handoff before apply. |

## Proposed interfaces (non-binding)

Illustrative entities are `BuilderSession`, `ConfigurationIntent`, `Clarification`, `ProjectPatch`, `PatchOperation`, `PermissionDelta`, `ValidationFinding`, and `DraftRevision`. Patch operations may target only a typed allowlist of project fields/files and include stable identity, base version/hash, before/after representation, rationale, reversibility, and dependencies.

Exact schema, patch format, model/tool orchestration, endpoint paths, and runtime project representations remain undecided. Generation receives redacted schemas/capabilities, not credential values. Apply uses expected draft version and idempotency key, then invokes the same validators as forms/files.

## Runtime capability and fallback

- Suggestions are constrained by the selected source’s verified capability manifest and template schema.
- Unknown/beta features are labelled discovery-gated and cannot generate deployable config until verification.
- Classic and capability-detected MDA may use different project adapters while exposing the same review semantics.
- On generation uncertainty or unsupported edit, route to the exact form/file/documentation context and preserve the user’s request as notes.

## Persistence and security

Persist builder intent, clarifications, redacted generation inputs, structured proposal, decisions, draft revision lineage, validators, and audit under retention policy. Do not persist secrets, raw credentials, hidden reasoning, or unrestricted imported content in model logs. Treat existing agent instructions, tool descriptions, ZIP imports, and retrieved docs as untrusted data.

Authorization applies to read, propose, apply, permission change, secret-reference selection, save, and deploy separately. A builder cannot grant itself tools or access. Validate paths, schema, prompt-injection boundary, archive traversal, content size, and generated references before draft apply.

## Responsive and accessible behavior

Desktop supports conversation plus synchronized diff/validation panels; narrow screens present a sequenced Request → Clarify → Review → Draft flow. Accessibility requirements include semantic diffs, announced non-color permission changes, keyboard-selectable operations, focus at validation errors, screen-reader-clear undo/Deploy state, and reduced motion.

## Metrics and guardrails

- Intent-to-valid-draft completion, clarification turns, proposal accept/edit/reject, undo, and manual-fallback rates.
- Schema-valid, semantically valid, deploy-valid, and post-deploy rollback rates by edit category.
- Unauthorized/unsupported proposal, hidden permission delta, secret exposure, and prompt-injection escape rates; targets zero.
- Time saved versus forms/files without lowering successful deploy or comprehension.
- Guardrails: no live mutation, no secret generation/view, no hidden change, and no deploy without existing explicit gate.

## Dependencies

- `DW-AGENT-003` supplies versioned drafts, import/export, validation, and explicit deploy.
- `DW-AGENT-004` owns model/profile/runtime/advanced settings and their dispositions.
- `DW-AGENT-005` owns tools, connectors, permissions, skills, memory, and subagent schemas.
- `DW-AGENT-001` transitively supplies source capability detection.

## Rollout and rollback

1. Define schema and replayable corpus; run offline generation/evaluation with no product mutation.
2. Read-only “explain this config” internal prototype.
3. Suggestion-only patches downloadable as diff, not applicable.
4. Feature-flagged apply to non-deployed test drafts for low-risk edit classes.
5. Expand edit classes only after precision/security thresholds; Deploy remains unchanged.

Rollback disables generation/apply, retains ordinary form/file editing, and preserves applied draft revisions for manual review/undo. It never rolls back a deployed agent automatically; the normal version rollback process remains authoritative.

## Executable acceptance scenarios

1. Given a request to add a tool, when a proposal is generated, then every file/setting, permission, credential reference, capability requirement, and validation result is visible before apply.
2. Given a user rejects the new connector permission but accepts instruction edits, when applying, then dependent connector changes are removed and the remaining patch revalidates.
3. Given imported instructions attempt prompt injection, when generation runs, then they remain quoted data and cannot alter builder policy, tools, target, or permissions.
4. Given the draft changed after generation, when Apply is selected, then expected-version validation blocks mutation and offers regenerate/rebase.
5. Given an unsupported runtime capability, when requested, then the builder labels it unavailable/unknown and routes to discovery rather than inventing config.
6. Given a valid applied patch, when the user leaves the builder, then the normal draft shows the exact revision and Deploy still requires independent confirmation.
7. Given keyboard and screen reader use on mobile, when reviewing a permission delta, then before/after, risk, accept/reject, and outcome are fully operable and announced.

## Explicit discovery gates

- **Schema:** define complete typed, versioned editable project model, stable identities, reversible patch semantics, dependency handling, and round-trip fidelity.
- **Runtime adapters:** verify classic/MDA project representations and capability boundaries without inventing external routes.
- **Quality:** build representative creation/change corpus and accept thresholds for correctness, completeness, clarification burden, and deploy validation.
- **Security:** threat-model imported prompt/tool content, permission escalation, secret leakage, path/archive attacks, model logs, and indirect injection.
- **UX:** validate change comprehension, partial acceptance, conflict recovery, undo, and mobile/assistive review.
- **Operations:** define model/provider policy, cost/latency limits, reproducibility, incident disable switch, and audit retention.

The builder remains non-ready while any editable schema or external runtime contract is unverified, regardless of demo quality.
