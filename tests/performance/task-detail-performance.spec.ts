import { mkdir, writeFile } from "node:fs/promises";
import { dirname } from "node:path";

import { expect, test, type Locator, type Page } from "@playwright/test";

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

async function visibleStreamEventIds(streamPanel: Locator): Promise<number[]> {
  const rows = await streamPanel.getByRole("listitem").allTextContents();
  return rows.map((row) => {
    const id = /^\s*#(\d+)/.exec(row)?.[1];
    if (id === undefined) throw new Error(`Stream row is missing an event id: ${row}`);
    return Number(id);
  });
}

function expectedStreamPageIds(total: number, page: number, pageSize: number): number[] {
  const end = total - (page - 1) * pageSize;
  const start = Math.max(1, end - pageSize + 1);
  return Array.from({ length: end - start + 1 }, (_, index) => start + index);
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
  const streamRows = streamPanel.getByRole("listitem");
  const earlierEvents = streamPanel.getByRole("button", { name: "Earlier events" });
  const newerEvents = streamPanel.getByRole("button", { name: "Newer events" });
  const streamEventCount = profile.dataset.streamEventCount + 1;
  const streamPageSize = profile.budgets.maximumMountedStreamRows;
  const streamPageCount = Math.ceil(streamEventCount / streamPageSize);
  const observedEventIds: number[] = [];
  let maximumObservedStreamRows = 0;

  await expect(streamPanel.getByText(/Showing 100 of 1001 events/)).toBeVisible();
  for (let streamPage = 1; streamPage <= streamPageCount; streamPage += 1) {
    const expectedIds = expectedStreamPageIds(streamEventCount, streamPage, streamPageSize);
    await expect(streamRows).toHaveCount(expectedIds.length);
    const visibleIds = await visibleStreamEventIds(streamPanel);
    expect(visibleIds).toEqual(expectedIds);
    observedEventIds.push(...visibleIds);
    maximumObservedStreamRows = Math.max(maximumObservedStreamRows, visibleIds.length);

    const firstId = expectedIds[0];
    const lastId = expectedIds.at(-1);
    if (firstId === undefined || lastId === undefined) throw new Error("Expected a populated page.");
    await expect(
      streamPanel.getByText(`${firstId.toLocaleString()}–${lastId.toLocaleString()}`, {
        exact: true,
      }),
    ).toBeVisible();
    if (firstId <= profile.dataset.streamEventCount) {
      await expect(streamRows.first()).toContainText(`Long stream update ${String(firstId)}`);
    }
    const lastContentId = Math.min(lastId, profile.dataset.streamEventCount);
    await expect(streamRows.nth(lastContentId - firstId)).toContainText(
      `Long stream update ${String(lastContentId)}`,
    );
    if (lastId === streamEventCount) {
      await expect(streamRows.last()).toContainText(`#${String(streamEventCount)}`);
      await expect(streamRows.last()).toContainText("run.completed");
    }

    if (streamPage === 1) await expect(newerEvents).toBeDisabled();
    else await expect(newerEvents).toBeEnabled();
    if (streamPage === streamPageCount) await expect(earlierEvents).toBeDisabled();
    else {
      await expect(earlierEvents).toBeEnabled();
      await earlierEvents.click();
    }
  }

  expect(new Set(observedEventIds).size).toBe(streamEventCount);
  expect([...observedEventIds].sort((left, right) => left - right)).toEqual(
    Array.from({ length: streamEventCount }, (_, index) => index + 1),
  );

  for (let streamPage = streamPageCount - 1; streamPage >= 1; streamPage -= 1) {
    await newerEvents.click();
    const expectedIds = expectedStreamPageIds(streamEventCount, streamPage, streamPageSize);
    await expect(streamRows).toHaveCount(expectedIds.length);
    expect(await visibleStreamEventIds(streamPanel)).toEqual(expectedIds);
  }
  await expect(newerEvents).toBeDisabled();
  await expect(earlierEvents).toBeEnabled();

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
    streamEventCount,
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
