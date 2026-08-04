import { expect, test, type Page } from "@playwright/test";

import { approveCurrentReview } from "../e2e/support/approve-current-review";

const viewports = {
  desktop: { width: 1440, height: 1000 },
  phone: { width: 390, height: 844 },
} as const;

async function capture(page: Page, name: string, viewport: keyof typeof viewports) {
  await page.setViewportSize(viewports[viewport]);
  await page.addStyleTag({
    content: `
      nextjs-portal { display: none !important; }
      *, *::before, *::after {
        animation-duration: 0s !important;
        animation-delay: 0s !important;
        transition-duration: 0s !important;
      }
  `,
  });
  if (viewport === "phone") {
    if (name === "task-files") {
      await page.getByText("result.md", { exact: true }).scrollIntoViewIfNeeded();
    } else if (name === "coding-review") {
      await page.getByTestId("coding-review").scrollIntoViewIfNeeded();
    } else if (name === "new-task-start-unknown") {
      await page.getByText("Task start not confirmed.", { exact: true }).scrollIntoViewIfNeeded();
    } else {
      await page.evaluate(() => window.scrollTo({ top: 0, left: 0, behavior: "instant" }));
    }
  }
  if (viewport === "phone" && name !== "login") {
    const shell = await page.evaluate(() => {
      const navigation = [...document.querySelectorAll('nav[aria-label="Primary navigation"]')]
        .find((element) => window.getComputedStyle(element).display !== "none")
        ?.getBoundingClientRect();
      const header = document.querySelector("header")?.getBoundingClientRect();
      return {
        headerBottom: header?.bottom,
        headerTop: header?.top,
        navigationBottom: navigation?.bottom,
        navigationTop: navigation?.top,
        scrollWidth: document.documentElement.scrollWidth,
        viewportHeight: window.innerHeight,
        viewportWidth: window.innerWidth,
      };
    });
    expect(shell.scrollWidth).toBeLessThanOrEqual(shell.viewportWidth);
    if (!["settings", "config", "observability", "new-task-start-unknown"].includes(name)) {
      expect(shell.headerTop).toBeGreaterThanOrEqual(-1);
      expect(shell.headerBottom).toBeLessThanOrEqual(shell.viewportHeight);
      expect(shell.navigationTop).toBeGreaterThanOrEqual(0);
      expect(shell.navigationBottom).toBeCloseTo(shell.viewportHeight, 0);
    }
  }
  await page.mouse.move(2, 2);
  await expect(page).toHaveScreenshot(`${viewport}/${name}.png`, {
    fullPage: viewport !== "phone",
    animations: "disabled",
    caret: "hide",
    maxDiffPixelRatio: 0.005,
  });
}

async function open(page: Page, path: string) {
  await page.goto(path);
  await page.waitForLoadState("networkidle");
  await expect(page.getByRole("heading").first()).toBeVisible();
}

async function signIn(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Workspace access key").fill("deepwork-local-browser-acceptance");
  await page.getByRole("button", { name: "Connect workspace" }).click();
  await expect(page).toHaveURL(/\/tasks$/);
}

test("designed routes and supervised journey match their accepted screenshots", async ({
  context,
  page,
}) => {
  await page.route("**/api/v1/agents", async (route) => {
    const agents = [
      {
        agentId: "agent-swe",
        name: "SWE agent",
        description: "Ships code: reproduces bugs in a sandbox, edits, tests, and opens PRs.",
        isDefault: true,
      },
      {
        agentId: "agent-research",
        name: "Research agent",
        description: "Gathers and synthesizes: web search, doc reading, and structured writeups.",
        isDefault: false,
      },
      {
        agentId: "agent-content",
        name: "Content agent",
        description:
          "Turns merged work into customer-facing writing — changelogs and release notes.",
        isDefault: false,
      },
      {
        agentId: "agent-exec",
        name: "Exec assistant",
        description: "Manages inbox and calendar: drafts replies, schedules, and prepares briefs.",
        isDefault: false,
      },
    ].map((agent, index) => ({
      ...agent,
      systemPrompt: null,
      createdAt: `2026-08-04T00:0${index}:00.000Z`,
      updatedAt: `2026-08-04T00:0${index}:00.000Z`,
    }));
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ available: true, items: agents }),
    });
  });
  await context.clearCookies();
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Connect to Deep Work" })).toBeVisible();
  await capture(page, "login", "desktop");
  await capture(page, "login", "phone");

  await page.getByLabel("Workspace access key").fill("deepwork-local-browser-acceptance");
  await page.getByRole("button", { name: "Connect workspace" }).click();
  await expect(page).toHaveURL(/\/tasks$/);

  const stableRoutes = [
    ["tasks", "/tasks"],
    ["approvals", "/approvals"],
    ["agents", "/agents"],
    ["schedules", "/schedules"],
    ["activity", "/activity"],
    ["settings", "/settings"],
  ] as const;
  for (const [name, path] of stableRoutes) {
    await open(page, path);
    await capture(page, name, "desktop");
    await capture(page, name, "phone");
  }
  const compatibilityRoutes = [
    ["agent-detail", "/agents/local"],
    ["config", "/config"],
    ["observability", "/observability"],
  ] as const;
  for (const [name, path] of compatibilityRoutes) {
    await open(page, path);
    await capture(page, name, "desktop");
    await capture(page, name, "phone");
  }
  await page.unroute("**/api/v1/agents");

  await open(page, "/tasks/new");
  await page
    .getByLabel("Task", { exact: true })
    .fill("Prepare the release acceptance brief with explicit evidence");
  await capture(page, "new-task-composed", "desktop");
  await capture(page, "new-task-composed", "phone");
  await page.getByRole("button", { name: "Dispatch" }).click();
  await expect(page).toHaveURL(/\/tasks\/task_[0-9]{8}$/);
  const taskPath = new URL(page.url()).pathname;

  await expect(page.getByText("Safe local fixture plan", { exact: true }).first()).toBeVisible();
  await capture(page, "task-plan-review", "desktop");
  await capture(page, "task-plan-review", "phone");

  await approveCurrentReview(page);
  await expect(page.getByText("Running", { exact: true }).first()).toBeVisible();
  await capture(page, "task-running", "desktop");
  await expect(page.getByText("Run completed", { exact: true })).toBeVisible();
  await capture(page, "task-completed", "desktop");
  await capture(page, "task-completed", "phone");

  await page.getByRole("tab", { name: "Sources" }).click();
  await capture(page, "task-sources", "desktop");
  await page.getByRole("tab", { name: "Files" }).click();
  await expect(page.getByText("result.md", { exact: true })).toBeVisible();
  await capture(page, "task-files", "desktop");
  await capture(page, "task-files", "phone");
  await page.getByRole("tab", { name: "Details" }).click();
  await expect(page.getByText("Execution trace", { exact: true })).toBeVisible();
  await capture(page, "task-details", "desktop");

  await page.getByRole("link", { name: "All tasks" }).click();
  await expect(page).toHaveURL(/\/tasks$/);
  await capture(page, "tasks-with-result", "desktop");
  await page.locator(`a[href="${taskPath}"]`).first().click();
  await expect(page).toHaveURL(new RegExp(`${taskPath}$`));
  await expect(page.getByText("Run completed", { exact: true })).toBeVisible();
  await capture(page, "task-reopened", "desktop");
});

test("the golden journey shell reflows at 320 CSS pixels", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 });
  await signIn(page);

  for (const path of ["/tasks", "/tasks/new", "/approvals", "/agents", "/settings"]) {
    await open(page, path);
    await expect(page).toHaveURL(new RegExp(`${path}$`));
    await expect
      .poll(() => page.evaluate(() => document.documentElement.scrollWidth))
      .toBeLessThanOrEqual(320);
  }
});

test("an uncertain dispatch has a blocking desktop and phone visual contract", async ({ page }) => {
  let createRequests = 0;
  await page.route("**/api/v1/tasks", async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    createRequests += 1;
    await route.abort("connectionfailed");
  });

  await signIn(page);
  await open(page, "/tasks/new");
  await page
    .getByLabel("Task", { exact: true })
    .fill("Recover this request without starting the same task twice");
  await page.getByRole("button", { name: "Dispatch" }).click();
  await expect(page.getByText("Task start not confirmed.", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Check task" })).toBeEnabled();
  await expect(page.getByLabel("Task", { exact: true })).toBeDisabled();
  expect(createRequests).toBe(2);

  await capture(page, "new-task-start-unknown", "desktop");
  await capture(page, "new-task-start-unknown", "phone");
});

test("coding review proof remains legible at desktop and phone widths", async ({ page }) => {
  await signIn(page);
  await open(page, "/tasks/new");
  await page.getByRole("radio", { name: /Coding review/ }).click();
  await page.getByLabel("Task", { exact: true }).fill("Fix the bounded session refresh regression");
  await page.getByRole("button", { name: "Dispatch" }).click();
  await expect(page).toHaveURL(/\/tasks\/task_[0-9]{8}$/);
  const batch = page.getByRole("region", { name: "Ordered approval batch" });
  await expect(batch).toBeVisible();
  for (const action of await batch.getByRole("listitem").all()) {
    await action.getByRole("button", { name: "Approve", exact: true }).click();
  }
  await batch.getByRole("button", { name: "Submit reviewed batch" }).click();
  await expect(page.getByText("Done", { exact: true }).first()).toBeVisible();
  await page.getByRole("tab", { name: "Changes" }).click();
  await expect(page.getByTestId("coding-review").getByText("Draft PR #17")).toBeVisible();
  await capture(page, "coding-review", "desktop");
  await capture(page, "coding-review", "phone");
});

test("phone More opens, closes, and reaches secondary destinations", async ({ page }) => {
  await page.setViewportSize(viewports.phone);
  await signIn(page);

  const moreButton = page.getByRole("button", { name: "More destinations" });
  await moreButton.click();
  const dialog = page.getByRole("dialog", { name: "More" });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("link", { name: "Schedules" })).toBeVisible();
  await expect(dialog.getByRole("link", { name: "Activity" })).toBeVisible();
  await expect(dialog.getByRole("link", { name: "Settings" })).toBeVisible();

  await page.getByRole("button", { name: "Close More menu" }).click();
  await expect(dialog).toBeHidden();

  await moreButton.click();
  await dialog.getByRole("link", { name: "Settings" }).click();
  await expect(page).toHaveURL(/\/settings$/);
  await expect(dialog).toBeHidden();
});
