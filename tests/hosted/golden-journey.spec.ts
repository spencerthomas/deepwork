import { expect, test } from "@playwright/test";

import { approveCurrentReview } from "../e2e/support/approve-current-review";

const accessKey = process.env.DEEPWORK_E2E_ACCESS_KEY;
const expectedBuildSha = process.env.DEEPWORK_EXPECTED_BUILD_SHA;

interface HostedAgent {
  agentId: string;
  name: string;
}

interface HostedTaskDetail {
  agentId: string | null;
  evidence: Array<{ kind: string; source: string }>;
  result: string | null;
}

interface HostedRuntimeStatus {
  runtime_kind: "fixture" | "local-agent-server" | "classic-deployment";
  evidence_class: string;
  capabilities: Array<{ name: string; state: string }>;
  build_sha: string | null;
}

function isApiUrl(value: string): boolean {
  return new URL(value).pathname.startsWith("/api/");
}

function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

test("hosted golden journey reaches a retained inspectable result", async ({ page }) => {
  if (!accessKey) throw new Error("DEEPWORK_E2E_ACCESS_KEY is required.");
  const pageErrors: string[] = [];
  const consoleErrors: string[] = [];
  const failedApiRequests: string[] = [];
  const failedApiResponses: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") {
      const location = message.location().url;
      consoleErrors.push(`${message.text()}${location ? ` @ ${location}` : ""}`);
    }
  });
  page.on("requestfailed", (request) => {
    if (isApiUrl(request.url())) {
      const path = new URL(request.url()).pathname;
      const failure = request.failure()?.errorText ?? "unknown";
      // A successful login immediately replaces /login with /tasks. Chromium can
      // report the now-unneeded rewritten POST body as aborted during that
      // navigation; the explicit /tasks assertion and authenticated status call
      // below remain the binding proof that login actually succeeded.
      if (
        request.method() === "POST" &&
        path === "/api/v1/auth/login" &&
        failure === "net::ERR_ABORTED"
      ) {
        return;
      }
      failedApiRequests.push(`${request.method()} ${path}: ${failure}`);
    }
  });
  page.on("response", (response) => {
    if (isApiUrl(response.url()) && !response.ok()) {
      failedApiResponses.push(
        `${response.request().method()} ${new URL(response.url()).pathname}: HTTP ${response.status()}`,
      );
    }
  });

  await page.goto("/login");
  expect(expectedBuildSha).toBeTruthy();
  expect(
    await page.locator('meta[name="deepwork-build-sha"]').getAttribute("content"),
  ).toBe(expectedBuildSha);
  await expect(page.getByRole("heading", { name: "Connect to Deep Work" })).toBeVisible();
  await page.getByLabel("Workspace access key").fill(accessKey);
  await page.getByRole("button", { name: "Connect workspace" }).click();
  await expect(page).toHaveURL(/\/tasks$/);

  const runtime = await page.evaluate(async () => {
    const response = await fetch("/api/v1/runtime/status", { credentials: "include" });
    return {
      status: response.status,
      body: (await response.json()) as HostedRuntimeStatus,
    };
  });
  expect(runtime.status).toBe(200);
  expect(runtime.body.runtime_kind).not.toBe("fixture");
  expect(runtime.body.build_sha).toBe(expectedBuildSha);
  expect(runtime.body.evidence_class).toBe("local-source");
  const runtimeCapabilities = Object.fromEntries(
    runtime.body.capabilities.map((capability) => [capability.name, capability.state]),
  );
  expect(runtimeCapabilities["local_task_loop"]).toBe("available");
  expect(runtimeCapabilities["sources"]).toBe("available");

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
  await expect(page).toHaveURL(/\/tasks\/task_[0-9]{8}$/);
  const taskUrl = new URL(page.url());

  const header = page.getByRole("heading", { level: 1 }).locator("..");
  await expect(header.getByText("Needs review", { exact: true })).toBeVisible();
  await expect(page.getByText(/plan/i).first()).toBeVisible();

  await approveCurrentReview(page);
  await expect(header.getByText("Running", { exact: true })).toBeVisible();
  await expect(header.getByText("Done", { exact: true })).toBeVisible();
  await expect(page.getByText("Run completed", { exact: true })).toBeVisible();

  const taskId = taskUrl.pathname.split("/").at(-1);
  expect(taskId).toBeTruthy();
  const detail = await page.evaluate(async (id) => {
    const response = await fetch(`/api/v1/tasks/${encodeURIComponent(id!)}`, {
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error(
        `Task detail for ${JSON.stringify(id)} at ${response.url} returned HTTP ${response.status}: ${await response.text()}`,
      );
    }
    return (await response.json()) as HostedTaskDetail;
  }, taskId);
  expect(detail.result?.trim().length).toBeGreaterThan(0);
  expect(detail.agentId).toBe(agent.agentId);
  expect(detail.evidence.length).toBeGreaterThan(0);

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
  const reopenedDetail = await page.evaluate(async (id) => {
    const response = await fetch(`/api/v1/tasks/${encodeURIComponent(id!)}`, {
      credentials: "include",
    });
    if (!response.ok) throw new Error(`Reopened task returned HTTP ${response.status}`);
    return (await response.json()) as HostedTaskDetail;
  }, taskId);
  expect(reopenedDetail.agentId).toBe(agent.agentId);
  await page.getByRole("tab", { name: "Files" }).click();
  await expect(page.getByText("result.md", { exact: true })).toBeVisible();

  expect(pageErrors).toEqual([]);
  expect(consoleErrors).toEqual([]);
  expect(failedApiRequests).toEqual([]);
  expect(failedApiResponses).toEqual([]);
});
