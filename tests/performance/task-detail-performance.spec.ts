import { mkdir, writeFile } from "node:fs/promises";
import { dirname } from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { blockNonLoopbackEgress } from "../e2e/support/block-non-loopback-egress";
import profile from "./inbox-1000.profile.json";

const taskId = "perf-task-9999";
const runId = "perf-run-9999";
const title = "Long stream performance task";
const result = "The long stream completed with retained evidence and files.";
const reportPath = "output/playwright/performance-report/task-detail-1000.json";

const task = {
  taskId,
  runId,
  title,
  prompt: "Inspect a long-running task without losing its latest updates.",
  status: "running",
  createdAt: "2026-08-03T12:00:00.000Z",
};

const detail = {
  ...task,
  evidence: [
    {
      evidenceId: "evidence-long-stream",
      kind: "source",
      summary: "The synthetic event transcript retained every source update.",
      source: "performance-profile",
      verified: true,
    },
  ],
};

const streamBody = [
  ...Array.from({ length: profile.dataset.streamEventCount }, (_, index) => [
    `id: ${String(index + 1)}`,
    "event: content.delta",
    `data: ${JSON.stringify({ taskId, runId, text: `Long stream update ${String(index + 1)}` })}`,
    "",
  ]).flat(),
  `id: ${String(profile.dataset.streamEventCount + 1)}`,
  "event: run.completed",
  `data: ${JSON.stringify({ taskId, runId, status: "completed", result })}`,
  "",
  "",
].join("\n");

async function installLongStream(page: Page): Promise<void> {
  await blockNonLoopbackEgress(page);
  await page.route(`**/api/v1/tasks/${taskId}/trace`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ state: "unavailable" }),
    });
  });
  await page.route(`**/api/v1/tasks/${taskId}/events`, async (route) => {
    await route.fulfill({ status: 200, contentType: "text/event-stream", body: streamBody });
  });
  await page.route(`**/api/v1/tasks/${taskId}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(detail),
    });
  });
  await page.route("**/api/v1/tasks", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [task] }),
    });
  });
}

test("1,000-event task stays bounded and inspectable", async ({ page }, testInfo) => {
  await installLongStream(page);
  const startedAt = performance.now();
  await page.goto(`/tasks/${taskId}`);
  await expect(page.getByRole("region", { name: "Task result" })).toContainText(result);
  const readyMs = performance.now() - startedAt;
  expect(readyMs).toBeLessThan(profile.budgets.longStreamReadyMs);

  const mountedUpdates = page.getByText("Task update", { exact: true });
  expect(await mountedUpdates.count()).toBeLessThanOrEqual(
    profile.budgets.maximumMountedThreadUpdates,
  );
  await expect(page.getByText(/earlier events are available in Stream/i)).toBeVisible();

  await page.getByRole("tab", { name: "Activity" }).click();
  const streamPanel = page.getByRole("tabpanel");
  await expect(streamPanel.getByRole("listitem")).toHaveCount(
    profile.budgets.maximumMountedStreamRows,
  );
  let maximumObservedStreamRows = await streamPanel.getByRole("listitem").count();
  await expect(streamPanel.getByText(/Showing 100 of 1001 events/)).toBeVisible();
  await expect(streamPanel.getByRole("button", { name: "Earlier events" })).toBeEnabled();
  await streamPanel.getByRole("button", { name: "Earlier events" }).click();
  await expect(streamPanel.getByRole("listitem")).toHaveCount(
    profile.budgets.maximumMountedStreamRows,
  );
  maximumObservedStreamRows = Math.max(
    maximumObservedStreamRows,
    await streamPanel.getByRole("listitem").count(),
  );
  await expect(streamPanel.getByRole("button", { name: "Newer events" })).toBeEnabled();

  await page.getByRole("tab", { name: "Sources" }).click();
  await expect(
    page.getByText("The synthetic event transcript retained every source update."),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Files" }).click();
  await expect(page.getByRole("link", { name: /Download result/i })).toBeVisible();
  await page.getByRole("tab", { name: "Details" }).click();
  await expect(page.getByText("No external trace was resolved.")).toBeVisible();

  const report = {
    profileId: profile.profileId,
    project: testInfo.project.name,
    streamEventCount: profile.dataset.streamEventCount + 1,
    maximumMountedThreadUpdates: await mountedUpdates.count(),
    maximumObservedStreamRows,
    maximumMountedStreamRowsBudget: profile.budgets.maximumMountedStreamRows,
    readyMs: Math.round(readyMs * 100) / 100,
    readyBudgetMs: profile.budgets.longStreamReadyMs,
  };
  const projectReportPath = reportPath.replace(".json", `-${testInfo.project.name}.json`);
  await mkdir(dirname(projectReportPath), { recursive: true });
  await writeFile(projectReportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
});
