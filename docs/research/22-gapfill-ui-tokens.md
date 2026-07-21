# Gap-fill: UI design tokens & components

*Condensed findings (agent-researched 2026-07-21, verified against live sources). Key facts and sources only; full reports available on request.*

## KEY FACTS
- agent-chat-ui (main, fetched 2026-07-21): Next ^15.5.18, React ^19.2.5, Tailwind v4 (^4.2.4) via `@import "tailwindcss"` in src/app/globals.css, shadcn style=new-york baseColor=neutral, Inter (next/font/google), framer-motion ^12.38, sonner, nuqs, @langchain/langgraph-sdk ^1.8.10.
- agent-chat-ui tokens are pure-neutral oklch: light --background oklch(1 0 0), --foreground oklch(0.145 0 0), --primary oklch(0.205 0 0), --muted/--secondary/--accent oklch(0.97 0 0), --border/--input oklch(0.922 0 0), --radius 0.625rem; dark flips to 0.145 bg / 0.985 fg / 0.269 surfaces; destructive oklch(0.577 0.245 27.325); full sidebar-* and chart-1..5 sets included (src/app/globals.css).
- The only brand color in both first-party UIs is #2F6868 teal — agent-chat-ui button variant `brand` (src/components/ui/button.tsx) and deep-agents-ui New Thread button + file-count badges (src/app/page.tsx, ChatInterface.tsx).
- agent-chat-ui layout: 300px framer-motion thread-history sidebar (spring 300/30, Sheet on <1024px), chat column max-w-3xl, artifact side panel toggles grid-cols-[1fr_0fr] → grid-cols-[3fr_2fr] (min-w-[30vw]) — artifact implemented as headless React-portal slot system in src/components/thread/artifact.tsx (ArtifactProvider/useArtifact/useArtifactOpen, passed as meta.artifact to LoadExternalComponent).
- agent-chat-ui HITL (src/components/thread/agent-inbox/): schema {action_requests:[{name,args,description?}], review_configs:[{action_name, allowed_decisions:[approve|edit|reject]}]}, resume via stream.submit({},{command:{resume:{decisions:[...]}}}); UI = gray-50 rounded-2xl p-8 container, per-arg Textarea edit cards (border-gray-300 rounded-lg p-6), multi-action progress dots colored emerald/red/amber by decision, brand submit button.
- deep-agents-ui (ARCHIVED Jun 28 2026, read-only, 1.7k stars): Next ^16.2.5, React 19.1.0, Tailwind v3.4 with tailwind.config.mjs importing @radix-ui/colors {blackA,green,mauve,slate,violet} and LangSmith-style semantic var utilities (Fira Code mono, fontSize xs=13px, display-* and caps-label-* utilities), shadcn baseColor=slate, react-resizable-panels, swr, diff ^8.
- deep-agents-ui tokens (src/app/globals.css): light --primary hsl(180 35% 17%)=#1c3c3c, dark --primary hsl(174 72% 56%)≈#2dd4bf; app vars --color-user-message-bg #e8f4f8 (dark #2d2d2d), success #10b981, warning #f59e0b, error #ef4444, bg #f9f9f9/dark #202020; layout vars --sidebar-width 320px, --header-height 64px, --panel-width 40vw, --chat-max-width 900px; --radius 0.5rem.
- deep-agents-ui workspace: h-16 header; ResizablePanelGroup with thread list panel defaultSize 25% min-w-[380px]; chat column max-w-[1024px]; todos+files render as a collapsible tray inside the composer card (max-h-72, border-b, bg-sidebar) with 'Task N of M' summary row — not a permanent sidebar in the final revision.
- deep-agents-ui todo styling: completed=CheckCircle text-success/80, in_progress=Clock text-warning/80, pending=Circle text-tertiary/70; group headers text-[10px] font-semibold uppercase tracking-wider; ThreadList status dots idle=bg-green-500, busy=bg-blue-500, interrupted=bg-orange-500, error=bg-red-600 with groups Requiring Attention/Today/Yesterday/This Week/Older.
- deep-agents-ui subagent cards: tool calls named `task` with args.subagent_type become SubAgent cards — header text-[15px] font-bold tracking-[-0.6px] text-[#3F3F46] w-fit max-w-[70vw], expanded body bg-surface border-border-light rounded-md p-4 with uppercase INPUT/OUTPUT markdown sections; FileViewDialog is 60vw×80vh with Prism oneDark, showLineNumbers, md files rendered as Markdown.
- ui-patterns.langchain.com hash routes per framework (/react/#/…): tool-calling, custom-stream-channel, human-in-the-loop, hitl-interrupt-forms, generative-ui, reasoning-tokens, structured-output-latex, time-travel, join-rejoin, async-iterator-tools, graph-execution-cards, message-queues, deep-agent-subagent-cards, deep-agent-todo-list, markdown-messages, branching-chat; plus /shadcn/, /ai-elements/, /assistant-ui/, /openui/ integration demos and hidden deep-agent-ide + deep-agent-code-review agents.
- ui-patterns playground uses `useStream` from @langchain/react with first-class `stream.subagents` handles (status pending|running|complete|error, per-subagent messages/toolCalls/namespace); SubagentCard = rounded-lg border bg-surface-secondary card, ▶ caret header px-3 py-2, namespace line, 12rem max-h auto-scrolling streamed body with pulsing ▌ cursor, status glyphs ○ ◉(warning, pulse) ✓(success) ✕(error); group view has n/m progress bar (h-1 bg-primary) and 1/2/3-col responsive grid.
- ui-patterns deep-agent-ide layout: file tree w-40 (160px) with amber modified dots and depth*14+8px indent, code/diff panel flex-1 rendered by @pierre/diffs (github-light/github-dark themes, unified diff, bars indicators, dark bg #25292e), chat panel w-64 (256px); todo pattern uses SplitView sidebarWidth=300 and stream.values.todos from deepagents write_todos.
- Canonical shared conventions across all three references: Inter/system font + dedicated mono, lucide icons, sonner, nuqs URL state, use-stick-to-bottom scrolling, uppercase micro-labels for sections, chevron-collapsible tool-call cards, orange/amber for in-progress+interrupted, green for success/approve, red for error/reject.
- GitHub MCP in this session is restricted to spencerthomas/deepwork and api.github.com is proxy-blocked, but raw.githubusercontent.com works via curl with /root/.ccr/ca-bundle.crt — all repo files were fetched that way; ui-patterns pattern sources were recovered verbatim from template-string embeds in /react/assets/index-CdX9f15N.js.

## OPEN QUESTIONS
- Could not list full directory trees (api.github.com blocked; GitHub MCP scoped to spencerthomas/deepwork) — component inventory is complete for every probed path, but sibling files not guessed (e.g. agent-chat-ui src/components/thread/ContentBlocksPreview.tsx, MultimodalPreview.tsx, providers/, and deep-agents-ui src/components/ui/* shadcn primitives were confirmed to exist by imports but not all fetched).
- deep-agents-ui last-commit date could not be confirmed as exactly 2026-05-14 (GitHub page showed only '173 commits'; archive date Jun 28 2026 confirmed).
- tailwind.config.ts referenced by deep-agents-ui components.json does not exist at repo root — actual file is tailwind.config.mjs; whether shadcn CLI generation is broken there is unverified (moot, repo archived).
- ui-patterns.langchain.com source repo could not be located on GitHub (likely private); analysis is from the deployed bundle. The shared playground components (ChatContainer/SubagentCard/StatusBadge) were read from compiled JSX, so exact source file paths for those are unknown.
- The /shadcn/ 'code review crew' and /ai-elements/, /assistant-ui/, /openui/ integration demo pages were not individually scraped (separate SPA bundles); only the root-page descriptions and the react bundle were analyzed.
- Did not verify whether agent-chat-ui has dark-mode UI actually wired (next-themes is a dependency and .dark tokens exist, but no ThemeProvider was seen in the fetched layout.tsx — several components hardcode bg-white/gray-*, suggesting light-only in practice).

## SOURCES
- agent-chat-ui src/app/globals.css (raw, main) — https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/src/app/globals.css
- agent-chat-ui components.json — https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/components.json
- agent-chat-ui package.json — https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/package.json
- agent-chat-ui src/app/layout.tsx (Inter font setup) — https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/src/app/layout.tsx
- agent-chat-ui src/components/thread/index.tsx (shell, artifact grid split, composer) — https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/src/components/thread/index.tsx
- agent-chat-ui src/components/thread/artifact.tsx (portal slot system) — https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/src/components/thread/artifact.tsx
- agent-chat-ui src/components/thread/messages/ai.tsx — https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/src/components/thread/messages/ai.tsx
- agent-chat-ui src/components/thread/messages/human.tsx — https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/src/components/thread/messages/human.tsx
- agent-chat-ui src/components/thread/messages/tool-calls.tsx — https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/src/components/thread/messages/tool-calls.tsx
- agent-chat-ui src/components/thread/messages/generic-interrupt.tsx — https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/src/components/thread/messages/generic-interrupt.tsx
- agent-chat-ui src/components/thread/messages/shared.tsx (BranchSwitcher, CommandBar) — https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/src/components/thread/messages/shared.tsx
- agent-chat-ui src/components/thread/markdown-text.tsx — https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/src/components/thread/markdown-text.tsx
- agent-chat-ui src/components/thread/syntax-highlighter.tsx (coldarkDark Prism) — https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/src/components/thread/syntax-highlighter.tsx
- agent-chat-ui src/components/thread/markdown-styles.css — https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/src/components/thread/markdown-styles.css
- agent-chat-ui src/components/thread/history/index.tsx — https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/src/components/thread/history/index.tsx
- agent-chat-ui src/components/thread/agent-inbox/index.tsx (ThreadView) — https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/src/components/thread/agent-inbox/index.tsx
- agent-chat-ui agent-inbox/components/thread-actions-view.tsx — https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/src/components/thread/agent-inbox/components/thread-actions-view.tsx
- agent-chat-ui agent-inbox/components/inbox-item-input.tsx (approve/edit/reject cards) — https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/src/components/thread/agent-inbox/components/inbox-item-input.tsx
- agent-chat-ui agent-inbox/types.ts (HITLRequest schema) — https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/src/components/thread/agent-inbox/types.ts
- agent-chat-ui src/components/ui/button.tsx (brand #2F6868 variant) — https://raw.githubusercontent.com/langchain-ai/agent-chat-ui/main/src/components/ui/button.tsx
- deep-agents-ui package.json — https://raw.githubusercontent.com/langchain-ai/deep-agents-ui/main/package.json
- deep-agents-ui components.json (baseColor slate) — https://raw.githubusercontent.com/langchain-ai/deep-agents-ui/main/components.json
- deep-agents-ui tailwind.config.mjs (radix colors, LangSmith semantic tokens) — https://raw.githubusercontent.com/langchain-ai/deep-agents-ui/main/tailwind.config.mjs
- deep-agents-ui src/app/globals.css (all hex/HSL tokens light+dark) — https://raw.githubusercontent.com/langchain-ai/deep-agents-ui/main/src/app/globals.css
- deep-agents-ui src/app/page.tsx (workspace layout, resizable panels) — https://raw.githubusercontent.com/langchain-ai/deep-agents-ui/main/src/app/page.tsx
- deep-agents-ui src/app/components/ChatInterface.tsx (tasks/files tray, todo icons) — https://raw.githubusercontent.com/langchain-ai/deep-agents-ui/main/src/app/components/ChatInterface.tsx
- deep-agents-ui src/app/components/TasksFilesSidebar.tsx (FilesPopover grid) — https://raw.githubusercontent.com/langchain-ai/deep-agents-ui/main/src/app/components/TasksFilesSidebar.tsx
- deep-agents-ui src/app/components/FileViewDialog.tsx (Prism oneDark viewer) — https://raw.githubusercontent.com/langchain-ai/deep-agents-ui/main/src/app/components/FileViewDialog.tsx
- deep-agents-ui src/app/components/SubAgentIndicator.tsx — https://raw.githubusercontent.com/langchain-ai/deep-agents-ui/main/src/app/components/SubAgentIndicator.tsx
- deep-agents-ui src/app/components/ChatMessage.tsx (bubbles + subagent extraction) — https://raw.githubusercontent.com/langchain-ai/deep-agents-ui/main/src/app/components/ChatMessage.tsx
- deep-agents-ui src/app/components/ToolCallBox.tsx — https://raw.githubusercontent.com/langchain-ai/deep-agents-ui/main/src/app/components/ToolCallBox.tsx
- deep-agents-ui src/app/components/ToolApprovalInterrupt.tsx — https://raw.githubusercontent.com/langchain-ai/deep-agents-ui/main/src/app/components/ToolApprovalInterrupt.tsx
- deep-agents-ui src/app/components/ThreadList.tsx (status colors, grouping) — https://raw.githubusercontent.com/langchain-ai/deep-agents-ui/main/src/app/components/ThreadList.tsx
- deep-agents-ui src/app/types/types.ts — https://raw.githubusercontent.com/langchain-ai/deep-agents-ui/main/src/app/types/types.ts
- ui-patterns.langchain.com root (pattern list + routes) — https://ui-patterns.langchain.com/
- ui-patterns react bundle (compiled components + embedded pattern sources) — https://ui-patterns.langchain.com/react/assets/index-CdX9f15N.js
- ui-patterns react CSS (playground design tokens) — https://ui-patterns.langchain.com/react/assets/index-BFp4_0tO.css
- deep-agents-ui GitHub page (archive confirmation) — https://github.com/langchain-ai/deep-agents-ui
