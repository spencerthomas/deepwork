---
feature_id: DW-CODE-002
title: GitHub installation, auth proxy, repository, branch, PR, CI, and merge
release: v1
status: canonical-spec
decision_status: blocked-on-spikes
owners: [github-integration, coding-runtime, api, security]
surfaces: [web, pwa, desktop, api, agent, sandbox]
runtime_scopes: [classic, mda, local]
source_refs: [SRC-FE, SRC-LC, SRC-DW, SRC-DP]
dependencies: [DW-ONB-001, DW-ONB-002, DW-CODE-001, DW-HITL-001, DW-FND-003]
contract_gates: [SPIKE-GITHUB-001, SPIKE-GITHUB-PROXY-001, SPIKE-GITHUB-CI-001]
last_reviewed: 2026-07-22
---

# GitHub installation, auth proxy, repository, branch, PR, CI, and merge

## User outcome

A user can install the Deep Work GitHub App for selected repositories, choose an authorized repository and base branch, let an agent work on a task-specific branch without receiving a long-lived token, review a draft pull request and live CI state, and deliberately merge from web/desktop/phone when repository policy permits.

## Evidence and confidence

| Evidence | Classification | Planning consequence |
|---|---|---|
| The prototype shows fixture GitHub connectors, repository/branch context, draft PR, commits, checks, diff, and merge-shaped actions. | Prototype evidence at `26c698b`; simulated | Retain the end-to-end review story, but every GitHub state requires authoritative API/webhook evidence. |
| Canonical plans require a GitHub App, repo-scoped access, zero-token-in-sandbox proxy, draft PR, CI, and phone merge loop. | Internal intent at `06f0515` | Make installation and proxy first-class application-service capabilities. |
| Pinned LangSmith sandbox docs document auth-proxy rules/callbacks and egress, but the exact GitHub CLI/git callback recipe and provider payload must be proven. | Documented building block at `7b9215d`; integration contract unknown | `SPIKE-GITHUB-PROXY-001` must prove zero-secret git and API operations before private-repo coding ships. |
| GitHub API, App permission, protection, webhook, and merge behavior are external contracts outside the LangChain pin. | Known platform area; not pinned by current evidence | `SPIKE-GITHUB-001` and `SPIKE-GITHUB-CI-001` produce reviewed GitHub contract fixtures. |

## Scope and ownership

### In scope

- GitHub App install/reconfigure/uninstall detection and installation-account selection.
- Repository list/search scoped to selected installations and current actor/workspace.
- Repository binding with immutable owner/name/node identity and current default branch.
- Task branch creation from a reviewed base SHA using safe collision handling.
- Auth-proxy delivery of short-lived GitHub App installation authorization without placing the token in sandbox env, files, command arguments, logs, or shell history.
- Clone/fetch/push, commit, draft PR create/update, PR link, commit list, checks/status, branch protection diagnostics, and explicit merge.
- Webhook validation, idempotency, polling reconciliation, stale-state indicators, and installation permission changes.
- Phone-friendly PR/CI/merge flow using the same FastAPI service.

### Out of scope

- GitLab/Bitbucket, forks across accounts, stacked PRs, multi-repo/worktree tasks, or arbitrary user PATs in the sandbox.
- Automatic merge by the agent or a schedule.
- Bypassing required reviews, checks, signed-commit rules, merge queue, code owners, or branch protection.
- Treating GitHub App installation as LangSmith operator authentication.
- Deleting branches automatically before merged/closed state and retention policy are confirmed.

### Ownership

- FastAPI owns GitHub App OAuth/installation callbacks, installation/repository authorization, token minting, proxy callback, webhook verification, branch/PR/merge orchestration, CI reconciliation, and audit.
- Postgres owns installation identifiers and safe metadata, selected repository permissions, task repository/base/head bindings, PR/check projections, webhook idempotency, and merge audit. It never stores installation tokens.
- GitHub owns installations, repository permissions, refs, commits, pull requests, checks, protection, and merge truth.
- LangSmith Sandbox auth proxy owns in-flight credential injection after its callback contract is validated.
- The Python starter agent owns safe git workflow and a draft-PR tool that calls reviewed application/provider boundaries; it cannot merge.
- Next.js/Tauri/PWA own install handoff, repo picker, PR/CI review, and merge confirmation.

## Primary journeys

### Install and select repository

1. An authenticated workspace user chooses **Connect GitHub** and sees requested App permissions and why each is needed.
2. FastAPI creates a signed, expiring installation transaction and redirects to GitHub.
3. The callback validates state and retrieves installation metadata; webhook or reconciliation confirms repository selection and permissions.
4. The repository picker shows only repos visible through an authorized installation, with private/public and access diagnostics.
5. Selecting a repo stores its stable GitHub identity and current default branch; branch/head state is re-fetched at task preflight.

### Branch, work, and draft PR

1. Coding preflight freezes repository identity, base branch, and base SHA.
2. FastAPI assigns a sanitized task branch such as `deepwork/<task-slug>-<short-id>` and proves it does not collide; if it exists, it verifies ownership or creates a deterministic suffix.
3. The sandbox clones/fetches over HTTPS through the verified auth proxy. A short-lived installation token is minted on demand, scoped to the installation/repository, injected in transit, and never returned to sandbox code.
4. The agent edits/tests, commits with task/run provenance, pushes the task branch, and requests a draft PR through a reviewed tool/service operation.
5. The PR projection records number, URL, base/head SHA, draft state, author/app, and last reconciliation time.

### CI and merge

1. Signed webhooks update checks/commit/PR state; bounded polling reconciles missed/out-of-order events.
2. The UI groups required, pending, failed, neutral/skipped, and unknown checks and marks freshness.
3. Before merge, FastAPI re-fetches PR, head SHA, approvals/checks, mergeability, branch protection, conflicts, and allowed methods.
4. A confirmation names repo, PR, base branch, exact head SHA, merge method, and any branch deletion.
5. FastAPI submits one idempotent merge request. GitHub's response is authoritative; timeout triggers reconciliation before retry.
6. Branch deletion is a separate explicit option after confirmed merge and policy checks.

## State matrix

| State | Required behavior | Recovery / transition |
|---|---|---|
| Not installed | Explain permissions and repository selection. | Start installation or choose non-coding path. |
| Install redirect pending | Preserve task/onboarding return path without repo data in URL. | Return, cancel, or expire. |
| Callback invalid/expired | Reject without attaching installation. | Restart. |
| Installed, repo selection pending | Show account/organization and GitHub-managed selection link. | Select/reconfigure repos. |
| Installation suspended/deleted | Immediately disable token minting and writes. | Reinstall/reactivate or switch. |
| Permissions insufficient | Name missing permission category, not token. | Reconfigure App installation. |
| Repositories loading | Skeleton/search disabled until authorized page arrives. | Results, empty, rate limit, or error. |
| No selected repositories | Explain GitHub-side selection. | Reconfigure. |
| Repository access revoked | Remove from new-task picker; freeze affected task mutations. | Restore or export/review existing artifacts. |
| Base branch loading | Show default/current branch and SHA freshness. | Select valid base. |
| Base branch moved before dispatch | Require preflight refresh and re-confirm new SHA. | Reconfirm or branch from reviewed SHA. |
| Branch creating | Idempotent request with intended name/base SHA. | Created, collision, forbidden, or reconcile. |
| Branch collision, ours | Verify task binding and reuse only exact intended ref. | Continue. |
| Branch collision, unknown | Never overwrite/force-push. | Create deterministic alternative. |
| Proxy token request | Authenticate sandbox callback and mint least-privilege short token. | Inject or fail closed. |
| Proxy unavailable | No token fallback in env/file. | Block private clone/push; repair integration. |
| Clone/fetch/push denied | Surface repository/branch/permission category and preserve sandbox. | Reauthorize or retry after refresh. |
| Commit ready | Show SHA/message/status; do not imply pushed. | Push or continue. |
| Push accepted | Re-fetch head SHA. | Create/update PR. |
| PR creating | Idempotent by task/repo/head/base; no duplicate PR on timeout. | Open existing/created PR or error. |
| PR draft | Show draft badge, current base/head, checks, and review link. | Update, mark ready at GitHub if supported/authorized, or keep draft. |
| PR changed externally | Mark local projection stale and reconcile. | Refresh before action. |
| CI pending | Show each known check and latest event time. | Update via webhook/poll. |
| CI failed | Merge disabled when required; link to check/log at GitHub. | Fix/retry externally or new agent attempt. |
| CI unknown/stale | Never treat as green. | Refresh; open GitHub. |
| Mergeable | Show allowed merge methods and required confirmation. | Merge or cancel. |
| Protection/review blocked | Explain authoritative blocker; no bypass. | Resolve at GitHub/review. |
| Conflict | Merge disabled; preserve task/PR. | Agent follow-up or manual resolution. |
| Merge submitting | Lock exact head SHA and idempotency key. | Confirm, reject, or reconcile timeout. |
| Head changed during confirm | Abort stale merge and require new review. | Refresh diff/checks and reconfirm. |
| Merged | Show merge SHA/time/method and optional explicit branch cleanup. | Archive/review outcome. |
| Offline client | Cached PR/CI is visibly stale; merge disabled. | Reconnect and refresh. |

## Proposed interfaces and runtime fallback

```ts
interface GitHubRepositoryBinding {
  bindingId: string;
  installationId: string;
  repositoryId: string;
  owner: string;
  name: string;
  private: boolean;
  permissions: Record<string, "read" | "write" | "admin" | "none">;
  defaultBranch: string;
  checkedAt: string;
}

interface TaskGitBinding {
  taskId: string;
  repositoryBindingId: string;
  baseRef: string;
  baseSha: string;
  headRef: string;
  headSha?: string;
  pullRequest?: { number: number; url: string; state: "draft" | "open" | "closed" | "merged" };
}

interface PullRequestGate {
  headSha: string;
  freshness: "live" | "stale";
  requiredChecks: Array<{ id: string; name: string; state: "pending" | "success" | "failure" | "neutral" | "unknown" }>;
  reviewState: string;
  mergeability: "mergeable" | "conflicting" | "blocked" | "unknown";
  allowedMethods: Array<"merge" | "squash" | "rebase">;
}
```

Proposed operations use `/api/v1/github/installations`, repository pages, task Git binding/actions, PR/check reads, and an explicit merge command. Internal auth-proxy callback is not a public arbitrary proxy and accepts only provider-authenticated requests tied to a live sandbox binding and approved host/repository intent.

`SPIKE-GITHUB-001` must pin the GitHub App/API client and prove install/reconfigure/suspend/delete, minimum permissions, repository pagination/search, token scoping/expiry, refs, commits/push assumptions, draft PR idempotency, branch protection, and merge methods. The reviewed result defines the manifest; the UI never infers write access from list access.

`SPIKE-GITHUB-PROXY-001` must run a real private-repo clone, fetch, push, and permitted API call from a test LangSmith sandbox using the pinned auth-proxy callback. It must prove the real token is absent from environment, filesystem, process list/args, Git config, command output, shell history, traces, snapshot, and logs. Callback authentication, replay, host/path match, TTL, and egress are acceptance requirements.

`SPIKE-GITHUB-CI-001` must capture signed webhook and polling fixtures for PR/check run/status events, retries/out-of-order delivery, required-check discovery, stale SHA, merge queue/protection, and merge timeout reconciliation.

If the auth proxy is unavailable, private-repo clone/push and GitHub writes are disabled. A public repository may be cloned read-only only when environment egress allows it; output remains a downloadable patch/diff with **Open GitHub** handoff. No PAT/token-in-sandbox fallback is permitted. MDA is enabled only by the same conformance tests.

## Persistence and security

- Never store installation access tokens. Mint short-lived repository-scoped tokens on demand; keep App private key in a dedicated secret store with rotation and access audit.
- Validate installation callback state and webhook signatures/timestamps; deduplicate delivery IDs and reconcile out-of-order events by authoritative ref/SHA.
- Bind installation/repository records to Deep Work tenant/workspace and current actor authorization. GitHub account identity does not replace Deep Work identity.
- Auth-proxy callback validates sandbox binding, task, host/path, repository, method/use, expiry, nonce, and egress policy before minting.
- Redact Authorization, clone credential helpers, remotes containing credentials, environment dumps, error bodies, Git URLs, logs, analytics, and traces.
- Never force-push or overwrite an unrecognized branch. Merge requires current head SHA and a newly fetched gate.
- Render PR titles, commit messages, check names/log links, branch names, and webhook payload fields as untrusted text/URLs.
- Merge and branch cleanup are high-impact audited mutations with CSRF protection, idempotency, confirmation, and no agent authority.

## Responsive and accessible behavior

- Installation/repository chooser uses labelled search/list controls and identifies account, repository, visibility, and permissions in text.
- Git state uses semantic headings for Repository, Branch, Pull request, Checks, and Merge; status is not color-only.
- Mobile summarizes files/checks/blockers first, with the exact repo/PR/head visible before merge confirmation.
- Check lists and commit history are keyboard navigable; external GitHub links identify new-site navigation.
- Confirmation focus starts on the summary, not the destructive button, and returns to the PR panel on cancel/failure.
- Live webhook changes are announced at meaningful state boundaries. Reduced motion removes pending pulses.

## Metrics and guardrails

- Installation completion/reconfigure/suspension rate and repository-access failures.
- Branch create/collision, clone/fetch/push, draft PR creation, webhook delay, polling reconciliation, and CI freshness rates.
- Coding funnel from repo selected to branch pushed, draft PR, checks green, and merged.
- Merge rejection category, stale-head abort, timeout reconciliation, and branch cleanup rate.
- Guardrails: zero long-lived GitHub token in sandbox leak corpus; zero duplicate PR for one task/head; zero merge when reviewed head differs; zero protection bypass attempt.

## Dependencies and rollout

- Depends on auth/workspace, sandbox/egress, HITL, task lifecycle, persistence, and security threat model.
- Phase 0: accept GitHub App, proxy, webhook/CI fixtures and secret-leak test suite.
- Phase 1: internal selected-repo install plus read-only metadata and public clone.
- Phase 2: private clone/push and draft PR via verified proxy on classic sandbox.
- Phase 3: CI/webhook reconciliation and explicit merge on web/desktop.
- Phase 4: phone review/merge after responsive diff and reauthentication tests.
- Disable token minting immediately on callback/permission regression; preserve PR links and review artifacts while mutations fall back to GitHub handoff.

## Executable acceptance scenarios

```gherkin
Scenario: Private repository workflow leaks no installation token
  Given an installed test repository and a verified sandbox binding
  When the sandbox clones, commits, pushes, and opens a draft PR
  Then each operation succeeds through the auth proxy
  And the leak scanner finds no real token in env, files, args, git config, logs, traces, snapshot, or outputs

Scenario: PR create timeout reconciles to one pull request
  Given GitHub creates a draft PR but the application request times out
  When FastAPI retries with the same task, repo, head, base, and idempotency key
  Then it finds and returns the existing PR
  And no duplicate PR is created

Scenario: Head change blocks a stale phone merge
  Given the phone reviewed head SHA A
  And a new commit changes the PR head to SHA B
  When the user confirms merge
  Then FastAPI aborts with head_changed
  And refreshes diff and checks for SHA B
  And sends no stale merge request

Scenario: Proxy unavailable has no token fallback
  Given the auth-proxy callback health check fails
  When a private-repository coding task reaches clone
  Then the task is blocked with proxy_unavailable
  And no credential is written into the sandbox
  And the user can open setup diagnostics or choose an artifact-only/public path
```
