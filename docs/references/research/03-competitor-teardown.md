# Competitor feature teardown (Codex, Claude Code/Cowork, Jules, Copilot, Cursor)

*Condensed findings (agent-researched 2026-07-21, verified against live sources). Key facts and sources only; full reports available on request.*

## KEY FACTS
- OpenAI merged Codex into a unified ChatGPT desktop app on 2026-07-09 with Chat/Work/Codex modes on every plan; ChatGPT Work (GPT-5.6) produces finished sheets/slides/docs/sites and has Scheduled Tasks — non-coding agent work is now core to both OpenAI and Anthropic products.
- Anthropic's own data (1.2M Cowork sessions, late May 2026): 33.4% business-process automation, 16.4% content creation, only 8.7% software development — >90% of Cowork usage is non-coding, so Deep Work v1 should not be code-only.
- Codex cloud environments: openai/codex-universal base image, auto-detected dependency install plus custom setup and maintenance scripts, secrets available only during setup phase, internet OFF by default in agent phase, 12-hour container caching that cut follow-up latency ~90%.
- Claude Code on the web: fresh VM per session (~4 vCPU/16GB/30GB), Network access levels None/Trusted/Full/Custom, bash setup scripts with ~7-day filesystem snapshot caching, GitHub credential proxy keeping tokens out of the sandbox, push restricted to the working branch.
- Claude Routines = prompt + repos + environment + connectors + model, with combinable triggers: cron (min 1h) / one-off / per-routine bearer-token POST /fire endpoint (beta header experimental-cc-routine-2026-04-01) / GitHub pull_request and release events with field-operator filters; autonomous runs are restricted to claude/-prefixed branches by default.
- Fired/webhook payloads reach Claude wrapped in an untrusted-data block (<routine-fire-payload>) and only the pre-stored routine prompt is treated as the task — a prompt-injection defense pattern worth copying verbatim.
- The dominant diff-review UX in both Codex and Claude: inline comments on diff lines are batch-submitted as the next steering message to the agent; Claude adds a CI status bar with Auto-fix and Auto-merge (squash) toggles after PR creation.
- Cross-surface handoff exists in both: Claude claude --cloud / --teleport / Desktop 'Continue in' (branch + context summary), Codex Remote GA 2026-06-25 with QR pairing of phone to local CLI; ChatGPT iOS 1.2026.181 supports create/search/open/fork Codex tasks.
- Auto-fix PR watching (Claude) subscribes to GitHub webhooks per-PR: pushes clear fixes, asks before ambiguous/architectural changes, replies on threads as the user but labeled as Claude Code; it cannot see merge conflicts because GitHub emits no webhook for them.
- Usage models: Codex uses 5-hour rolling windows shared across local+cloud plus token-based credits since April 2026 (typical task 5-45 credits); Claude cloud sessions share the subscription rate limit with no separate VM compute charge; routines add a daily per-account run cap with metered overage via usage credits.
- Environment setup friction is the top documented pain point (generic 'Failed to create task' errors, 'create an environment for this repo' dead ends, mis-tuned envs timing out), followed by context loss (no cross-session memory; user-level config not carried to cloud).
- Review trust is collapsing industry-wide: 29% of developers trust AI output accuracy (down from 40% in 2024), 66% cite 'almost right' output as top frustration — v1 must optimize for cheap verification (plans, traces, diffs, self-review), not assumed trust.
- Jules exposes the cleanest API model to emulate: Sessions containing typed Activities (plan, progress, message), requirePlanApproval and AUTO_CREATE_PR flags, scheduled tasks with edit/pause/resume, and repoless ephemeral serverless sessions.
- Competitor table stakes convergence: task inbox + live trace, named multi-repo environments, parallel sandboxed tasks, plan-first flow, PR creation, Slack/Linear entry points (Cursor posts a plan before starting; Copilot has an Agents panel with per-task model picker and custom agents in .github/agents/).
- Claude Desktop's parallel-session model uses one git worktree per session (.claude/worktrees/), auto-archive on PR merge/close, side chats (/btw) that read session context without appending to it, and OS notifications when an unfocused session finishes.

## OPEN QUESTIONS
- Exact current Codex cloud task concurrency caps and best-of-N maximum in the July 2026 unified app (older figure: Plus 10-60 cloud tasks per 5h window; best-of-N confirmed as a feature but current N limit unverified).
- Cowork 'Race Mode' details (parallel competing attempts) come from a third-party review only; not confirmed against Anthropic docs.
- Whether ChatGPT Work's Scheduled Tasks support API/webhook triggers like Claude Routines do, or only time-based schedules.
- Precise GPT-5.6 model naming (Sol/Terra/Luna tiers) and their credit rates are from the fetched pricing page but could not be cross-verified against a second source.
- Copilot coding agent's copilot-setup-steps.yml environment mechanism and Actions-minutes billing are from training-data-era docs; 2026 sources confirmed the agent panel/custom agents/MCP but I did not re-verify the env config file name.
- Could not load the HN thread (429) for first-hand Claude Code on the web complaints; pain points synthesized from docs' own caveats, GitHub issues, third-party reviews, and industry surveys instead.
- Devin 3.0 'MultiDevin'/knowledge features carried from earlier docs; 2026 sources confirmed sessions/pricing/integrations but not every legacy feature's survival.

## SOURCES
- Codex cloud (ChatGPT Learn docs) — https://learn.chatgpt.com/docs/cloud
- Codex cloud environment configuration — https://learn.chatgpt.com/docs/environments/cloud-environment
- Codex changelog — https://learn.chatgpt.com/docs/changelog
- Codex code review — https://learn.chatgpt.com/docs/code-review
- Codex / ChatGPT pricing and usage limits — https://learn.chatgpt.com/docs/pricing
- Claude Code on the web (official docs) — https://code.claude.com/docs/en/claude-code-on-the-web
- Claude Code Routines (official docs) — https://code.claude.com/docs/en/routines
- Claude Code Desktop application (official docs) — https://code.claude.com/docs/en/desktop
- Claude Code on mobile (official docs) — https://code.claude.com/docs/en/mobile
- The Claude Cowork product guide — https://claude.com/blog/the-claude-cowork-product-guide
- TechCrunch: Claude Cowork expands to mobile and web (2026-07-07) — https://techcrunch.com/2026/07/07/the-coding-agent-wars-are-spilling-into-the-rest-of-the-office-claude-cowork/
- Neowin: OpenAI launches ChatGPT Work, unified desktop app with Codex — https://www.neowin.net/news/openai-launches-chatgpt-work-and-unveils-unified-desktop-app-with-codex-built-in/
- OpenAI: ChatGPT is now a partner for your most ambitious work — https://openai.com/index/chatgpt-for-your-most-ambitious-work/
- Morphllm: Codex pricing and usage limits July 2026 — https://www.morphllm.com/codex-pricing
- Cursor changelog (background agents, Slack, computer use) — https://cursor.com/changelog
- Cursor Slack integration docs — https://cursor.com/docs/integrations/slack
- Devin release notes 2026 — https://docs.devin.ai/release-notes/2026
- Devin pricing — https://devin.ai/pricing
- GitHub Blog: What's new with Copilot coding agent — https://github.blog/ai-and-ml/github-copilot/whats-new-with-github-copilot-coding-agent/
- GitHub Blog: Agents panel — https://github.blog/news-insights/product-news/agents-panel-launch-copilot-coding-agent-tasks-anywhere-on-github/
- Jules API reference (sessions/activities) — https://jules.google/docs/api/reference/
- Google blog: Jules proactive coding features — https://blog.google/innovation-and-ai/technology/developers-tools/jules-proactive-updates/
- Jules changelog — https://jules.google/docs/changelog/
- openai/codex issue #20093: environment resolution failures from GitHub comments — https://github.com/openai/codex/issues/20093
- openai/codex issue #21179: Failed to create task on Codex Web — https://github.com/openai/codex/issues/21179
- eesel: Claude Cowork review — features, pricing, limitations — https://www.eesel.ai/blog/claude-cowork-review
- Elephas: Claude Cowork first impressions (Race Mode, memory limits) — https://elephas.app/blog/claude-cowork-review-alternatives
- Uvik: AI coding assistant statistics 2026 (trust decline) — https://uvik.net/blog/ai-coding-assistant-statistics/
- ChatGPT iOS Codex Mobile task management (1.2026.181) — https://linkloot.io/blog/chatgpt-ios-12026181-codex-mobile-task-management
- MacRumors: Anthropic rebuilds Claude Code desktop app around parallel sessions — https://www.macrumors.com/2026/04/15/anthropic-rebuilds-claude-code-desktop-app/
