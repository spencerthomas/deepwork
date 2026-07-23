# OSS project setup research

*Condensed findings (agent-researched 2026-07-21, verified against live sources). Key facts and sources only; full reports available on request.*

## KEY FACTS
- All upstream LangChain packages are MIT (Copyright (c) LangChain, Inc.): deepagents PyPI 0.6.12, npm deepagents 1.11.1, langgraph, managed-deepagents (npm latest 0.3.1 / dev 0.4.0-dev.72), and the archived open-agent-platform — no license constraint on Deep Work's own choice.
- Comparable agent apps split MIT (LibreChat, open-agent-platform) vs Apache-2.0 (Continue, Cline, OpenAI Codex CLI); Open WebUI uses a non-OSI modified BSD with a branding-preservation clause (>50 users must keep 'Open WebUI' branding) after relicensing from MIT — a cautionary precedent; Claude Code is proprietary ('subject to Anthropic's Commercial Terms of Service').
- Apache-2.0 + NOTICE file ('Portions Copyright (c) LangChain, Inc. (MIT)') + DCO is the mainstream recommendation for a venture-shaped OSS agent app.
- LANGCHAIN (USPTO serial 98033029, registered Jan 21, 2025) and LANGSMITH (serial 98141268) are registered trademarks of LangChain Inc.; there is no published third-party brand policy, so use nominative fair use only ('built on LangChain deepagents') plus an explicit non-affiliation disclaimer, and never put 'Lang*' in the product name/domain/npm scope; live precedent: Anthropic forced Clawdbot→Moltbot rename in Jan 2026.
- deepagentsjs is the reference TS monorepo: pnpm workspaces + libs/* + changesets (@changesets/config 3.1.1, changelog-github, access public, ignore examples) + oxlint/oxfmt + Node 22/24 CI matrix + amannn/action-semantic-pull-request PR-title lint with per-package scopes + all Actions pinned to SHAs.
- deepagentsjs release.yml uses changesets/action (v1.9.0, SHA-pinned) on push to main/alpha with pnpm, NPM_CONFIG_PROVENANCE=true, and permissions contents:write/pull-requests:write/id-token:write; the Python deepagents repo instead uses release-please + Conventional Commits.
- open-agent-platform (archived, superseded by hosted LangSmith Agent Builder) shows the app shape: turbo ^2.5 monorepo, workspaces apps/* (web, docs), CI only does format/lint/codespell, and Vercel preview deploys come from the Vercel Git integration, not GitHub Actions.
- Managed Deep Agents (private beta, LangSmith Cloud US-only, CLI-first) requires a strict project layout — root agent.ts/agent.py exporting named `agent` from defineDeepAgent, plus optional instructions.md, tools/, middleware/, connectors/mcp.ts, schedules/, skills/<name>/SKILL.md, sandbox/ — so packages/agent must itself be a valid `mda` project root; runtime owns backend/store/checkpointer/memory/skills/system-prompt and setting those keys is an error.
- mda CLI: `mda init|dev|deploy`; auth key order LANGGRAPH_HOST_API_KEY → LANGSMITH_API_KEY → LANGCHAIN_API_KEY; deploy forwards non-reserved .env entries as hosted secrets and compiles into .mda/build.
- Docs tooling: LangChain docs = Mintlify theme 'aspen' (langchain-ai/docs src/docs.json, primary #161F34); Continue and Cline keep docs/ in-repo with Mintlify docs.json; Open WebUI uses Docusaurus; recommendation for v1 is README + in-repo docs/ Mintlify stub.
- Community-file staging: official deepagentsjs ships only LICENSE/README/workflows/dependabot at 1.4k stars — ship minimal CONTRIBUTING, SECURITY, CoC (Contributor Covenant), 2 issue-form templates and PR template at v1; defer FUNDING, stale-bots, labelers, locales, CLA, governance until traction.
- Staging precedent: LibreChat/Open WebUI/Continue/Cline were open from first commit; OpenAI Codex CLI and Zed were built privately and opened with clean history at launch (Codex CLI initially with 'not accepting PRs' posture) — the recommended middle path for Deep Work v1.
- npm deepagents 1.11.1 peer deps to pin in packages/agent: @langchain/core ^1.2.0, @langchain/langgraph ^1.4.4, @langchain/langgraph-checkpoint ^1.1.2, @langchain/langgraph-sdk ^1.9.23, langchain ^1.5.0, langsmith ^0.7.1; Python deepagents needs Python >=3.11 and langchain-core >=1.4.8 <2.
- Recommended stack for the deepwork repo: pnpm + turborepo ^2.5 + changesets + biome (or oxlint), workspaces apps/{web,desktop,mobile} + packages/{agent,sdk,ui}, CI = format/lint/typecheck/build/test matrix + semantic PR titles, Vercel Git integration for previews, changesets/action for releases with npm provenance.

## OPEN QUESTIONS
- Whether Cline's 2024 rename from 'Claude Dev' was formally trademark-driven (widely reported as confusion/trademark-adjacent, but not verified from a primary source in this session; the verified enforcement precedent is Clawdbot→Moltbot, Jan 2026).
- Exact contents of langchain-ai/open-agent-platform apps/web internal structure (archived repo; only top level and workflows verified).
- Whether deepagentsjs keeps CONTRIBUTING/issue templates somewhere non-standard (only .github/{workflows,images,dependabot.yml} were visible in the directory listing).
- Managed Deep Agents public API surface for programmatic create/update/invoke — docs explicitly removed API examples during private beta ('contact your LangChain team'), so the SDK package design must assume CLI-first until the API is published.
- Zed's private-then-open timeline was asserted from training knowledge (Jan 2024 open-sourcing), not re-verified live.
- LibreChat's docs-site generator (Nextra) was asserted from prior knowledge; the librechat.ai repo tooling was not fetched this session.

## SOURCES
- langchain-ai/deepagents LICENSE (MIT) — https://raw.githubusercontent.com/langchain-ai/deepagents/main/LICENSE
- langchain-ai/deepagentsjs LICENSE (MIT) — https://raw.githubusercontent.com/langchain-ai/deepagentsjs/main/LICENSE
- langchain-ai/langgraph LICENSE (MIT) — https://raw.githubusercontent.com/langchain-ai/langgraph/main/LICENSE
- langchain-ai/open-agent-platform (archived; MIT; turbo/yarn monorepo) — https://github.com/langchain-ai/open-agent-platform
- Open WebUI LICENSE (modified BSD w/ branding clause) — https://raw.githubusercontent.com/open-webui/open-webui/main/LICENSE
- LibreChat LICENSE (MIT) — https://raw.githubusercontent.com/danny-avila/LibreChat/main/LICENSE
- Continue LICENSE (Apache-2.0) — https://raw.githubusercontent.com/continuedev/continue/main/LICENSE
- Cline LICENSE (Apache-2.0) — https://raw.githubusercontent.com/cline/cline/main/LICENSE
- OpenAI Codex LICENSE (Apache-2.0) — https://raw.githubusercontent.com/openai/codex/main/LICENSE
- anthropics/claude-code LICENSE.md (proprietary) — https://raw.githubusercontent.com/anthropics/claude-code/main/LICENSE.md
- Managed Deep Agents overview (private beta) — https://docs.langchain.com/langsmith/managed-deep-agents-overview
- Managed Deep Agents CLI reference (mda; project file reference) — https://docs.langchain.com/langsmith/managed-deep-agents-cli
- deepagents on PyPI (0.6.12, MIT) — https://pypi.org/pypi/deepagents/json
- deepagents on npm (1.11.1, MIT, peer deps) — https://registry.npmjs.org/deepagents/latest
- managed-deepagents on npm (0.3.1 / 0.4.0-dev.72, mda bin) — https://registry.npmjs.org/managed-deepagents
- deepagentsjs repo tree (pnpm, libs/, .changeset, oxlint) — https://github.com/langchain-ai/deepagentsjs
- deepagentsjs ci.yml — https://raw.githubusercontent.com/langchain-ai/deepagentsjs/main/.github/workflows/ci.yml
- deepagentsjs release.yml (changesets/action) — https://raw.githubusercontent.com/langchain-ai/deepagentsjs/main/.github/workflows/release.yml
- deepagentsjs .changeset/config.json — https://raw.githubusercontent.com/langchain-ai/deepagentsjs/main/.changeset/config.json
- deepagentsjs pr_lint.yml (semantic PR titles) — https://raw.githubusercontent.com/langchain-ai/deepagentsjs/main/.github/workflows/pr_lint.yml
- open-agent-platform package.json (turbo, yarn workspaces) — https://raw.githubusercontent.com/langchain-ai/open-agent-platform/main/package.json
- open-agent-platform ci.yml — https://raw.githubusercontent.com/langchain-ai/open-agent-platform/main/.github/workflows/ci.yml
- langchain-ai/docs src/docs.json (Mintlify aspen) — https://github.com/langchain-ai/docs
- continuedev/continue docs/docs.json (Mintlify) — https://github.com/continuedev/continue
- cline/cline docs/docs.json + community files — https://github.com/cline/cline
- open-webui/docs docusaurus.config.ts — https://github.com/open-webui/docs
- LibreChat .github community files — https://github.com/danny-avila/LibreChat/tree/main/.github
- LANGSMITH trademark registration (USPTO serial 98141268) — https://uspto.report/TM/98141268
- LANGCHAIN trademark (serial 98033029) — https://www.trademarkia.com/langchain-98033029
- LangChain Terms of Service (trademark clauses) — https://www.langchain.com/terms-of-service
- Clawdbot creator says Anthropic 'forced' rename (trademark enforcement precedent) — https://www.aol.com/articles/clawdbot-creator-says-anthropic-forced-162839894.html
