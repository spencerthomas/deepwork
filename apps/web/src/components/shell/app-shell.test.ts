import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import { shellRuntimePresentation } from "@/lib/runtime-disclosure";
import { taskClient } from "@/lib/task-client";

import { AppShell } from "./app-shell";

vi.mock("./command-bar", () => ({
  CommandBar: () => null,
}));

describe("AppShell accessibility landmarks", () => {
  it("renders a keyboard-visible skip link, labeled primary navigation, and main target", () => {
    const markup = renderToStaticMarkup(
      createElement(AppShell, {
        active: "Tasks",
        children: createElement("p", null, "Task content"),
      }),
    );

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
});
