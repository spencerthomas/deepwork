import { mkdir, writeFile } from "node:fs/promises";
import { dirname } from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { blockNonLoopbackEgress } from "../e2e/support/block-non-loopback-egress";
import profile from "./inbox-1000.profile.json";

const reportPath = "output/playwright/performance-report/inbox-1000.json";

function taskItems() {
  const epoch = Date.parse("2026-08-03T12:00:00.000Z");
  return Array.from({ length: profile.dataset.taskCount }, (_, index) => {
    const sequence = index + 1;
    return {
      taskId: `perf-task-${sequence.toString().padStart(4, "0")}`,
      runId: `perf-run-${sequence.toString().padStart(4, "0")}`,
      title: `Performance task ${sequence.toString().padStart(4, "0")}`,
      status: profile.dataset.statuses[index % profile.dataset.statuses.length],
      createdAt: new Date(epoch - index * 60_000).toISOString(),
    };
  });
}

const taskListBody = JSON.stringify({ items: taskItems() });

function percentile(values: readonly number[], percentileValue: number): number {
  const sorted = [...values].sort((left, right) => left - right);
  const index = Math.ceil((percentileValue / 100) * sorted.length) - 1;
  return sorted[Math.max(0, index)] ?? Number.POSITIVE_INFINITY;
}

async function installDataset(page: Page): Promise<void> {
  await blockNonLoopbackEgress(page);
  await page.route("**/api/v1/tasks", async (route) => {
    if (route.request().method() !== "GET") {
      await route.continue();
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, profile.network.taskListDelayMs));
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: taskListBody,
    });
  });
}

test("1,000-task inbox stays bounded, responsive, and keyboard usable", async ({
  page,
}, testInfo) => {
  await installDataset(page);
  await page.goto("/tasks");

  await expect(page.getByRole("status")).toContainText("1000 loaded tasks");
  const taskRows = page.locator('a[href^="/tasks/perf-task-"]');
  await expect(taskRows).toHaveCount(profile.budgets.maximumMountedTaskRows);
  let maximumObservedTaskRows = await taskRows.count();
  await expect(page.getByRole("button", { name: "Next page" })).toBeEnabled();
  await expect(page.getByText("1–50 of 1,000 tasks", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Next page" }).click();
  await expect(page).toHaveURL(/\?page=2$/);
  await expect(page.getByText("51–100 of 1,000 tasks", { exact: true })).toBeVisible();
  await expect(taskRows).toHaveCount(profile.budgets.maximumMountedTaskRows);
  maximumObservedTaskRows = Math.max(maximumObservedTaskRows, await taskRows.count());
  await page.getByRole("button", { name: "Previous page" }).click();
  await expect(page).toHaveURL(/\/tasks$/);

  const search = page.getByRole("searchbox", { name: "Search loaded tasks" });
  const interactionSamples: number[] = [];
  for (const sequence of [997, 41, 812, 76, 643, 215, 904, 388]) {
    const startedAt = performance.now();
    await search.fill(`Performance task ${sequence.toString().padStart(4, "0")}`);
    await expect(page.getByRole("status")).toContainText("Showing 1 of 1000 loaded tasks");
    interactionSamples.push(performance.now() - startedAt);
  }
  const interactionP75Ms = percentile(interactionSamples, 75);
  expect(interactionP75Ms).toBeLessThan(profile.budgets.interactionP75Ms);

  await search.fill("");
  await expect(taskRows).toHaveCount(profile.budgets.maximumMountedTaskRows);
  maximumObservedTaskRows = Math.max(maximumObservedTaskRows, await taskRows.count());
  await search.press("Escape");
  await page.keyboard.press("j");
  await expect(taskRows.first()).toHaveAttribute("data-focused", "true");
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/tasks\/perf-task-/);

  const report = {
    profileId: profile.profileId,
    datasetId: profile.dataset.id,
    project: testInfo.project.name,
    taskCount: profile.dataset.taskCount,
    maximumObservedTaskRows,
    maximumMountedTaskRowsBudget: profile.budgets.maximumMountedTaskRows,
    interactionSamplesMs: interactionSamples.map((value) => Math.round(value * 100) / 100),
    interactionP75Ms: Math.round(interactionP75Ms * 100) / 100,
    interactionBudgetMs: profile.budgets.interactionP75Ms,
  };
  const projectReportPath = reportPath.replace(".json", `-${testInfo.project.name}.json`);
  await mkdir(dirname(projectReportPath), { recursive: true });
  await writeFile(projectReportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
});
