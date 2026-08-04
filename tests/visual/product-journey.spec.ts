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
  await page.mouse.move(2, 2);
  await expect(page).toHaveScreenshot(`${viewport}/${name}.png`, {
    fullPage: true,
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
