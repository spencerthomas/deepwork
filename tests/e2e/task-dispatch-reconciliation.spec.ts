import { expect, test } from "@playwright/test";

import { approveCurrentReview } from "./support/approve-current-review";

const viewports = {
  desktop: { width: 1440, height: 1000 },
  phone: { width: 390, height: 844 },
} as const;

for (const [viewportName, viewport] of Object.entries(viewports)) {
  test(`reconciles one lost create response without a duplicate task at ${viewportName} width`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    const requests: Array<{ body: string | null; key: string | undefined }> = [];
    let acceptedTaskId = "";
    let acceptedRunId = "";
    let replayWasDuplicate = false;
    let requestCount = 0;
    let markSecondRequestSeen!: () => void;
    const secondRequestSeen = new Promise<void>((resolve) => {
      markSecondRequestSeen = resolve;
    });
    let releaseSecondRequest!: () => void;
    const secondRequestReleased = new Promise<void>((resolve) => {
      releaseSecondRequest = resolve;
    });

    await page.route("**/api/v1/tasks", async (route) => {
      const request = route.request();
      if (request.method() !== "POST") {
        await route.continue();
        return;
      }
      requestCount += 1;
      requests.push({
        body: request.postData(),
        key: request.headers()["idempotency-key"],
      });

      if (requestCount === 1) {
        const response = await route.fetch();
        expect(response.status()).toBe(202);
        const receipt = (await response.json()) as Record<string, unknown>;
        expect(receipt["duplicate"]).toBe(false);
        acceptedTaskId = String(receipt["taskId"]);
        acceptedRunId = String(receipt["runId"]);
        await route.abort("connectionfailed");
        return;
      }
      if (requestCount === 2) {
        markSecondRequestSeen();
        await secondRequestReleased;
        await route.abort("connectionfailed");
        return;
      }

      const response = await route.fetch();
      expect(response.status()).toBe(202);
      const receipt = (await response.json()) as Record<string, unknown>;
      expect(receipt["taskId"]).toBe(acceptedTaskId);
      expect(receipt["runId"]).toBe(acceptedRunId);
      replayWasDuplicate = receipt["duplicate"] === true;
      await route.fulfill({ response });
    });

    await page.goto("/tasks/new");
    await expect(page.getByRole("heading", { name: "New task" })).toBeVisible();
    const objective = `Recover a lost ${viewportName} task dispatch safely`;
    const prompt = page.getByLabel("Task", { exact: true });
    await prompt.fill(objective);
    await page.getByRole("button", { name: "Dispatch" }).click();

    await secondRequestSeen;
    await expect(page.getByRole("button", { name: "Checking…" })).toBeDisabled();
    await expect(page.getByText("Checking the original request…", { exact: true })).toBeVisible();
    await expect(
      page.getByText(
        "Task start not confirmed yet. Deep Work is checking the original request so it does not start twice.",
        { exact: true },
      ),
    ).toBeVisible();
    await expect(page).toHaveURL(/\/tasks\/new$/);
    await expect(prompt).toBeDisabled();
    await expect(page.getByRole("radio", { name: /General task/ })).toBeDisabled();

    releaseSecondRequest();
    await expect(page.getByText("Task start not confirmed.", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Check task" })).toBeEnabled();
    await expect(page.getByRole("link", { name: "View tasks" })).toBeVisible();
    await expect(page.getByText("Task was not created.", { exact: true })).toHaveCount(0);
    expect(requestCount).toBe(2);
    expect(requests[0]?.key).toBeTruthy();
    expect(requests[1]).toEqual(requests[0]);

    await page.reload();
    await expect(page.getByText("Task start not confirmed.", { exact: true })).toBeVisible();
    await expect(prompt).toHaveValue(objective);
    await expect(prompt).toBeDisabled();
    expect(requestCount).toBe(2);

    await page.getByRole("button", { name: "Check task" }).click();
    await expect(page).toHaveURL(new RegExp(`/tasks/${acceptedTaskId}$`));
    await expect(page.getByText("Needs review", { exact: true }).first()).toBeVisible();
    expect(replayWasDuplicate).toBe(true);
    expect(requests).toHaveLength(3);
    expect(requests[2]).toEqual(requests[0]);

    await approveCurrentReview(page);
    await expect(page.getByText("Done", { exact: true }).first()).toBeVisible();

    const retained = await page.evaluate(async (taskId) => {
      const [listingResponse, detailResponse, eventsResponse] = await Promise.all([
        fetch("/api/v1/tasks", { credentials: "include" }),
        fetch(`/api/v1/tasks/${encodeURIComponent(taskId)}`, {
          credentials: "include",
        }),
        fetch(`/api/v1/tasks/${encodeURIComponent(taskId)}/events`, {
          credentials: "include",
        }),
      ]);
      if (!listingResponse.ok || !detailResponse.ok || !eventsResponse.ok) {
        throw new Error("The retained task proof could not be read.");
      }
      const listing = (await listingResponse.json()) as { items: Array<{ taskId: string }> };
      return {
        matchingTasks: listing.items.filter((item) => item.taskId === taskId).length,
        detail: (await detailResponse.json()) as { lastEventId: number; taskId: string },
        events: await eventsResponse.text(),
      };
    }, acceptedTaskId);
    expect(retained.matchingTasks).toBe(1);
    expect(retained.detail.taskId).toBe(acceptedTaskId);
    expect(retained.events.match(/event: task\.created/g)).toHaveLength(1);
  });
}

test("an authoritative create rejection preserves the draft and rotates the next request identity", async ({
  page,
}) => {
  const keys: string[] = [];
  await page.route("**/api/v1/tasks", async (route) => {
    const request = route.request();
    if (request.method() !== "POST") {
      await route.continue();
      return;
    }
    keys.push(request.headers()["idempotency-key"] ?? "");
    await route.fulfill({
      status: 422,
      contentType: "application/json",
      body: JSON.stringify({
        code: "invalid_request",
        message: "The task objective was rejected by the API.",
      }),
    });
  });

  await page.goto("/tasks/new");
  const prompt = page.getByLabel("Task", { exact: true });
  const objective = "Preserve this rejected task objective";
  await prompt.fill(objective);
  await page.getByRole("button", { name: "Dispatch" }).click();
  await expect(page.getByText("Task was not created.", { exact: true })).toBeVisible();
  await expect(page.getByText("The task objective was rejected by the API.")).toBeVisible();
  await expect(prompt).toBeEnabled();
  await expect(prompt).toHaveValue(objective);

  await page.getByRole("button", { name: "Dispatch" }).click();
  await expect.poll(() => keys.length).toBe(2);
  expect(keys[0]).toBeTruthy();
  expect(keys[1]).toBeTruthy();
  expect(keys[1]).not.toBe(keys[0]);
});
