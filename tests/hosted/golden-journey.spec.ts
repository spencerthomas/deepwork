import { expect, test } from "@playwright/test";

const accessKey = process.env.DEEPWORK_E2E_ACCESS_KEY;

interface HostedAgent {
  agentId: string;
  name: string;
}

interface HostedTaskDetail {
  evidence: Array<{ kind: string; source: string }>;
  result: string | null;
}

function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

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
  const registry = await page.evaluate(async () => {
    const response = await fetch("/api/v1/agents", { credentials: "include" });
    return {
      status: response.status,
      body: (await response.json()) as { available: boolean; items: HostedAgent[] },
    };
  });
  expect(registry.status).toBe(200);
  expect(registry.body.available).toBe(true);
  expect(registry.body.items.length).toBeGreaterThan(0);
  const agent = registry.body.items[0];
  const selectedAgent = page.getByRole("radio", {
    name: new RegExp(escapeRegex(agent.name), "i"),
  });
  await expect(selectedAgent).toBeEnabled();
  await selectedAgent.click();
  await expect(selectedAgent).toHaveAttribute("aria-checked", "true");

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

  const taskId = taskUrl.pathname.split("/").at(-1);
  expect(taskId).toBeTruthy();
  const detail = await page.evaluate(async (id) => {
    const response = await fetch(`/api/v1/tasks/${encodeURIComponent(id!)}`, {
      credentials: "include",
    });
    if (!response.ok) throw new Error(`Task detail returned HTTP ${response.status}.`);
    return (await response.json()) as HostedTaskDetail;
  }, taskId);
  expect(detail.result?.trim().length).toBeGreaterThan(0);

  await page.getByRole("tab", { name: "Sources" }).click();
  await expect(page.getByText("local-source", { exact: false }).first()).toBeVisible();
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
