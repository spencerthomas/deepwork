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
const incrementalReportPath =
  "output/playwright/performance-report/task-detail-incremental-1000.json";

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

async function installTaskApi(page: Page): Promise<void> {
  await blockNonLoopbackEgress(page);
  await page.route(`**/api/v1/tasks/${taskId}/trace`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ state: "unavailable" }),
    });
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

async function installLongStream(page: Page): Promise<void> {
  await installTaskApi(page);
  await page.route(`**/api/v1/tasks/${taskId}/events`, async (route) => {
    await route.fulfill({ status: 200, contentType: "text/event-stream", body: streamBody });
  });
}

async function installIncrementalStream(page: Page): Promise<void> {
  await page.addInitScript(
    ({ eventCount, finalResult, incrementalRunId, incrementalTaskId }) => {
      const metrics = {
        closedSubscriptionCount: 0,
        dispatchedEventCount: 0,
        maxLongTaskMs: 0,
        maxMainThreadTimerLagMs: 0,
        readyMs: 0,
        startedAt: performance.now(),
        subscriptionContractValid: true,
        subscriptionCount: 0,
      };
      Object.defineProperty(window, "__deepworkIncrementalMetrics", { value: metrics });

      let expectedTimerAt = performance.now() + 16;
      const responsivenessTimer = window.setInterval(() => {
        const now = performance.now();
        metrics.maxMainThreadTimerLagMs = Math.max(
          metrics.maxMainThreadTimerLagMs,
          now - expectedTimerAt,
        );
        expectedTimerAt = now + 16;
      }, 16);
      const longTaskObserver =
        typeof PerformanceObserver === "undefined"
          ? undefined
          : new PerformanceObserver((entries) => {
              for (const entry of entries.getEntries()) {
                metrics.maxLongTaskMs = Math.max(metrics.maxLongTaskMs, entry.duration);
              }
            });
      try {
        longTaskObserver?.observe({ entryTypes: ["longtask"] });
      } catch {
        longTaskObserver?.disconnect();
      }
      Object.defineProperty(window, "__deepworkFinishIncrementalMetrics", {
        value: async () => {
          await new Promise<void>((resolve) => {
            window.requestAnimationFrame(() => window.setTimeout(resolve, 0));
          });
          for (const entry of longTaskObserver?.takeRecords() ?? []) {
            metrics.maxLongTaskMs = Math.max(metrics.maxLongTaskMs, entry.duration);
          }
          metrics.readyMs = performance.now() - metrics.startedAt;
          window.clearInterval(responsivenessTimer);
          longTaskObserver?.disconnect();
          return metrics;
        },
      });

      class IncrementalEventSource {
        static readonly CLOSED = 2;
        static readonly CONNECTING = 0;
        static readonly OPEN = 1;
        readonly url: string;
        readonly withCredentials: boolean;
        readyState = IncrementalEventSource.CONNECTING;
        onopen: ((event: Event) => void) | null = null;
        onerror: ((event: Event) => void) | null = null;
        onmessage: ((event: MessageEvent) => void) | null = null;
        private closed = false;
        private readonly listeners = new Map<string, Set<EventListenerOrEventListenerObject>>();

        constructor(url: string | URL, init?: EventSourceInit) {
          this.url = String(url);
          this.withCredentials = init?.withCredentials ?? false;
          metrics.subscriptionCount += 1;
          metrics.subscriptionContractValid &&=
            this.url.endsWith(`/api/v1/tasks/${incrementalTaskId}/events`) &&
            this.withCredentials;
          window.setTimeout(() => {
            if (this.closed) return;
            this.readyState = IncrementalEventSource.OPEN;
            this.onopen?.(new Event("open"));
            let nextId = 1;
            const delivery = new MessageChannel();
            delivery.port1.onmessage = () => {
              if (this.closed) return;
              if (nextId <= eventCount) {
                this.emit("content.delta", nextId, {
                  taskId: incrementalTaskId,
                  runId: incrementalRunId,
                  text: `Long stream update ${String(nextId)}`,
                });
                nextId += 1;
                delivery.port2.postMessage(undefined);
                return;
              }
              this.emit("run.completed", eventCount + 1, {
                taskId: incrementalTaskId,
                runId: incrementalRunId,
                status: "completed",
                result: finalResult,
              });
              delivery.port1.close();
              delivery.port2.close();
            };
            delivery.port2.postMessage(undefined);
          }, 0);
        }

        addEventListener(type: string, listener: EventListenerOrEventListenerObject): void {
          const listeners = this.listeners.get(type) ?? new Set<EventListenerOrEventListenerObject>();
          listeners.add(listener);
          this.listeners.set(type, listeners);
        }

        removeEventListener(type: string, listener: EventListenerOrEventListenerObject): void {
          this.listeners.get(type)?.delete(listener);
        }

        close(): void {
          if (this.closed) return;
          this.closed = true;
          this.readyState = IncrementalEventSource.CLOSED;
          metrics.closedSubscriptionCount += 1;
        }

        dispatchEvent(): boolean {
          return true;
        }

        private emit(type: string, id: number, data: Record<string, unknown>): void {
          metrics.dispatchedEventCount += 1;
          const event = new MessageEvent(type, {
            data: JSON.stringify(data),
            lastEventId: String(id),
          });
          for (const listener of this.listeners.get(type) ?? []) {
            if (typeof listener === "function") listener(event);
            else listener.handleEvent(event);
          }
        }
      }

      Object.defineProperty(window, "EventSource", { value: IncrementalEventSource });
    },
    {
      eventCount: profile.dataset.streamEventCount,
      finalResult: result,
      incrementalRunId: runId,
      incrementalTaskId: taskId,
    },
  );
  await installTaskApi(page);
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

test("1,000 events delivered incrementally remain responsive and bounded", async ({
  page,
}, testInfo) => {
  await installIncrementalStream(page);
  await page.goto(`/tasks/${taskId}`);
  await expect(page.getByRole("region", { name: "Task result" })).toContainText(result);

  const metrics = await page.evaluate(
    async () =>
      await (
        window as Window & {
          __deepworkFinishIncrementalMetrics: () => Promise<{
            closedSubscriptionCount: number;
            dispatchedEventCount: number;
            maxLongTaskMs: number;
            maxMainThreadTimerLagMs: number;
            readyMs: number;
            startedAt: number;
            subscriptionContractValid: boolean;
            subscriptionCount: number;
          }>;
        }
      ).__deepworkFinishIncrementalMetrics(),
  );
  expect(metrics.dispatchedEventCount).toBe(profile.dataset.streamEventCount + 1);
  expect(metrics.subscriptionContractValid).toBe(true);
  expect(metrics.subscriptionCount).toBe(1);
  expect(metrics.closedSubscriptionCount).toBe(1);
  expect(metrics.readyMs).toBeLessThan(profile.budgets.incrementalStreamReadyMs);
  expect(metrics.maxMainThreadTimerLagMs).toBeLessThan(
    profile.budgets.maximumMainThreadTimerLagMs,
  );
  expect(metrics.maxLongTaskMs).toBeLessThan(profile.budgets.maximumLongTaskMs);
  expect(await page.getByText("Task update", { exact: true }).count()).toBeLessThanOrEqual(
    profile.budgets.maximumMountedThreadUpdates,
  );
  await page.getByRole("tab", { name: "Activity" }).click();
  await expect(page.getByRole("tabpanel").getByText(/Showing 100 of 1001 events/)).toBeVisible();
  await page.getByRole("link", { name: "Tasks", exact: true }).click();
  await page.getByRole("link", { name: title }).click();
  await expect(page.getByRole("region", { name: "Task result" })).toContainText(result);
  await expect
    .poll(async () =>
      await page.evaluate(() => {
        const current = (
          window as Window & {
            __deepworkIncrementalMetrics: {
              closedSubscriptionCount: number;
              subscriptionCount: number;
            };
          }
        ).__deepworkIncrementalMetrics;
        return {
          closedSubscriptionCount: current.closedSubscriptionCount,
          subscriptionCount: current.subscriptionCount,
        };
      }),
    )
    .toEqual({ closedSubscriptionCount: 2, subscriptionCount: 2 });

  const report = {
    profileId: profile.profileId,
    project: testInfo.project.name,
    streamEventCount: profile.dataset.streamEventCount + 1,
    closedSubscriptionCount: metrics.closedSubscriptionCount,
    dispatchedEventCount: metrics.dispatchedEventCount,
    maxLongTaskMs: metrics.maxLongTaskMs,
    maxMainThreadTimerLagMs: metrics.maxMainThreadTimerLagMs,
    readyMs: metrics.readyMs,
    subscriptionContractValid: metrics.subscriptionContractValid,
    budgets: {
      readyMs: profile.budgets.incrementalStreamReadyMs,
      mainThreadTimerLagMs: profile.budgets.maximumMainThreadTimerLagMs,
      longTaskMs: profile.budgets.maximumLongTaskMs,
    },
  };
  const projectReportPath = incrementalReportPath.replace(
    ".json",
    `-${testInfo.project.name}.json`,
  );
  await mkdir(dirname(projectReportPath), { recursive: true });
  await writeFile(projectReportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
});
