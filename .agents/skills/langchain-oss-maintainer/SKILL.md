---
name: langchain-oss-maintainer
description: Review or change Deep Work code so it follows the repository's LangChain-shaped package, agent, testing, dependency, and OSS contributor conventions. Use for remote-main audits, pull-request reviews, cross-package changes, agent runtime changes, and recurring convention enforcement.
---

# LangChain OSS Maintainer

Keep Deep Work recognizable to LangChain contributors without copying upstream
internals or erasing this repository's application architecture.

## Start with current authority

1. Read the root and nearest scoped `AGENTS.md`, `ARCHITECTURE.md`, and the
   reviewed ExecPlan governing the changed paths.
2. Fetch the remote and compare against `origin/main`. Never assess a stale
   snapshot as current.
3. Read the complete diff and identify newly landed contracts before adding a
   type, adapter, helper, or vocabulary.
4. Use installed public APIs and pinned primary-source evidence. Never depend on
   LangChain, LangGraph, or Deep Agents private modules.
5. For any multi-package or external-contract change, create or update the
   reviewed ExecPlan before implementation.

## Apply the rules

Read [references/enforcement-checklist.md](references/enforcement-checklist.md)
completely and classify every applicable rule as pass, violation, or not
applicable. A violation needs a concrete file and the smallest safe correction.

## Change policy

- Preserve application layering: app -> SDK/UI -> domain; UI never imports SDK.
- Reuse the canonical domain and SDK contracts. Do not create a convenience copy
  of task identities, statuses, events, decisions, or recovery semantics.
- Keep `packages/agent` independently installable and based on supported public
  Deep Agents, LangChain, and LangGraph APIs.
- Treat plan review and tool authorization as separate gates. Caller tools fail
  closed and require explicit authorization by default.
- Stream long-running graph work through public streaming APIs; do not buffer a
  nested agent invocation when progress or interrupts must remain observable.
- Keep default tests deterministic, credential-free, and socket-denied. Separate
  unit, integration, evaluation, and benchmark suites by purpose.
- Prefer compatible runtime dependency ranges plus a committed lockfile. Test
  every interpreter/runtime version claimed in package metadata.
- A root success command must exercise TypeScript, every Python project,
  architecture boundaries, contracts, docs, package consumers, and builds.
- Pin third-party CI actions to immutable commit SHAs with least privilege.
- Preserve contributor-facing issue, PR, security, dependency-update, change,
  and release mechanics.

## Enforce safely

Run from the repository root:

```bash
make doctor
make check
make contract
make package-check
make docs
make ci
```

For a remote audit, do not push to or rewrite `main`. If a correction is needed,
work on a fresh `agent/langchain-oss-*` branch or isolated worktree based on the
latest `origin/main`, validate it, and open a reviewable pull request. If
credentials, review authority, or a decision gate are unavailable, report the
exact blocker and leave the protected branch unchanged.

## Report

Lead with violations, ordered by impact. Include exact paths, the rule each
violates, validation performed, and whether the result is local, pushed, or
merged. If no violations exist, report the inspected commit and the full gates
that passed. Never describe fixture or local green state as production proof.
