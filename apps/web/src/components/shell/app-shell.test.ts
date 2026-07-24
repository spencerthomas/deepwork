import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import { shellRuntimePresentation } from "@/lib/runtime-disclosure";
import { taskClient } from "@/lib/task-client";
import { TasksProvider } from "@/lib/tasks-store";

import { AppShell } from "./app-shell";

vi.mock("./command-bar", () => ({
  CommandBar: () => null,
}));

/** Render AppShell inside the tasks store it now reads for the approvals badge. */
function renderShell(active: string) {
  return renderToStaticMarkup(
    createElement(
      TasksProvider,
      null,
      createElement(AppShell, {
        active,
        children: createElement("p", null, "Task content"),
      }),
    ),
  );
}

describe("AppShell accessibility landmarks", () => {
  it("renders a keyboard-visible skip link, labeled primary navigation, and main target", () => {
    const markup = renderShell("Tasks");

    expect(markup).toContain('href="#main-content"');
    expect(markup).toContain("focus:translate-y-0");
    expect(markup).toContain(">Skip to main content</a>");
    expect(markup).toContain('<nav aria-label="Primary navigation"');
    expect(markup).toContain('<main id="main-content" tabindex="-1"');
    expect(markup).toMatch(/<a aria-label="New task"[^>]*href="\/tasks\/new"/);
    const workspace = shellRuntimePresentation(taskClient.mode);
    expect(markup).toContain(
      `aria-label="Workspace: ${workspace.workspaceLabel} — ${workspace.workspaceSubtitle}"`,
    );
  });

  it("renders a compact search icon and restores the text and shortcut at sm", () => {
    const markup = renderShell("Tasks");

    expect(markup).toContain('aria-label="Search or run a command"');
    expect(markup).toContain("lucide-search");
    const searchIcon = markup.indexOf("lucide-search");
    const searchButton = markup.slice(
      markup.lastIndexOf("<button", searchIcon),
      markup.indexOf("</button>", searchIcon),
    );
    expect(searchButton).toContain('aria-hidden="true"');
    expect(markup).toContain("size-9 shrink-0");
    expect(markup).toContain("gap-2 px-4 sm:gap-4");
    expect(markup).toContain("sm:flex-1");
    expect(markup).toMatch(/<a aria-label="Deep Work home"[^>]*href="\/tasks"/);
    expect(markup).toContain(
      'class="hidden text-[15px] font-semibold tracking-tight sm:inline">deepwork</span>',
    );
    expect(markup).toContain('aria-hidden="true" class="hidden text-border sm:inline"');
    expect(markup).toContain('class="hidden truncate sm:inline"');
    expect(markup).toContain("Search or run a command…");
    expect(markup).toContain("⌘K");
  });
});
