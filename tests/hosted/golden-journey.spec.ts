import { expect, test } from "@playwright/test";

const accessKey = process.env.DEEPWORK_E2E_ACCESS_KEY;

test("hosted golden journey reaches a retained inspectable result", async ({ page }) => {
  if (!accessKey) throw new Error("DEEPWORK_E2E_ACCESS_KEY is required.");
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));

  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Connect to Deep Work" })).toBeVisible();
  await page.getByLabel("Workspace access key").fill(accessKey);
  await page.getByRole("button", { name: "Connect workspace" }).click();
  await expect(page).toHaveURL(/\/tasks$/);

  await page.goto("/tasks/new");
  await expect(page.getByRole("heading", { name: "New task" })).toBeVisible();
  const selectedAgent = page.getByRole("radio", { checked: true });
  await expect(selectedAgent).toBeVisible();

  const objective = `Hosted release acceptance ${new Date().toISOString()}`;
  await page.getByLabel("Task", { exact: true }).fill(objective);
  await page.getByRole("button", { name: "Dispatch" }).click();
  await expect(page).toHaveURL(/\/tasks\/[^/?]+$/);
  const taskUrl = new URL(page.url());

  const header = page.getByRole("heading", { level: 1 }).locator("..");
  await expect(header.getByText("Needs review", { exact: true })).toBeVisible();
  await expect(page.getByText(/plan/i).first()).toBeVisible();

  await page.getByRole("button", { name: "Approve", exact: true }).click();
  await expect(header.getByText("Running", { exact: true })).toBeVisible();
  await expect(header.getByText("Done", { exact: true })).toBeVisible();
  await expect(page.getByText("Run completed", { exact: true })).toBeVisible();
  await expect(page.getByText(/Next actions:/)).toBeVisible();

  await page.getByRole("tab", { name: "Sources" }).click();
  await expect(page.getByText(/Verified|Not independently verified/).first()).toBeVisible();
  await page.getByRole("tab", { name: "Files" }).click();
  await expect(page.getByText("result.md", { exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "Details" }).click();
  await expect(page.getByText("Execution trace", { exact: true })).toBeVisible();
  await expect(page.getByText("Retained events", { exact: true })).toBeVisible();

  await page.getByRole("link", { name: "All tasks" }).click();
  await expect(page).toHaveURL(/\/tasks$/);
  await page.locator(`a[href="${taskUrl.pathname}"]`).first().click();
  await expect(page).toHaveURL(new RegExp(`${taskUrl.pathname}$`));
  await expect(page.getByText("Run completed", { exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "Files" }).click();
  await expect(page.getByText("result.md", { exact: true })).toBeVisible();

  expect(pageErrors).toEqual([]);
});
