import { expect, test } from "@playwright/test";

test("a stale second-device decision is refreshed and blocked before submission", async ({
  browser,
  page,
}) => {
  const objective = "Prove a stale approval cannot overwrite a decision from another device";

  await page.goto("/tasks/new");
  await page.getByLabel("Task", { exact: true }).fill(objective);
  await page.getByRole("button", { name: "Dispatch" }).click();
  await expect(page).toHaveURL(/\/tasks\/task_[0-9]{8}$/);
  const taskUrl = page.url();
  const taskId = new URL(taskUrl).pathname.split("/").at(-1);
  if (!taskId) throw new Error("The dispatched task URL did not contain a task identifier.");
  await expect(page.getByRole("button", { name: "Approve", exact: true })).toBeVisible();

  const secondContext = await browser.newContext({
    baseURL: "http://127.0.0.1:3000",
    serviceWorkers: "block",
    storageState: "output/playwright/auth.json",
    viewport: { width: 390, height: 844 },
  });
  const secondPage = await secondContext.newPage();
  let releaseStaleStream!: () => void;
  const staleStreamReleased = new Promise<void>((resolve) => {
    releaseStaleStream = resolve;
  });
  await secondPage.route(`**/api/v1/tasks/${taskId}/events`, async (route) => {
    await staleStreamReleased;
    await route.abort("connectionfailed");
  });
  let secondDeviceDecisionPosts = 0;
  secondPage.on("request", (request) => {
    if (
      request.method() === "POST" &&
      request.url().endsWith(`/api/v1/tasks/${taskId}/decisions`)
    ) {
      secondDeviceDecisionPosts += 1;
    }
  });

  await secondPage.goto(taskUrl);
  await expect(secondPage.getByRole("heading", { name: objective, exact: true })).toBeVisible();
  await expect(secondPage.getByRole("button", { name: "Reject", exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Approve", exact: true }).click();
  await expect(page.getByText("Run completed", { exact: true })).toBeVisible();
  const eventTranscript = await page.request.get(`/api/v1/tasks/${taskId}/events`);
  expect(eventTranscript.status()).toBe(200);
  const eventText = await eventTranscript.text();
  expect(eventText.match(/event: decision\.recorded/g)).toHaveLength(1);
  expect(eventText).toContain('"decision":"approve"');

  await secondPage.getByRole("button", { name: "Reject", exact: true }).click();
  const staleNotice = secondPage.getByRole("alert").filter({
    hasText: "This approval is no longer current. No decision was sent. The latest task state is shown.",
  });
  await expect(staleNotice).toBeVisible();
  await expect(staleNotice).toBeFocused();
  expect(secondDeviceDecisionPosts).toBe(0);
  const secondTaskHeader = secondPage.getByRole("heading", { level: 1 }).locator("..");
  await expect(secondTaskHeader.getByText("Done", { exact: true })).toBeVisible();

  releaseStaleStream();
  await secondContext.close();
});

test("the approvals inbox retains and focuses a stale-decision explanation after removing the row", async ({
  browser,
  page,
}) => {
  const objective = "Keep stale approval feedback visible after the queue refreshes";

  await page.goto("/tasks/new");
  await page.getByLabel("Task", { exact: true }).fill(objective);
  await page.getByRole("button", { name: "Dispatch" }).click();
  await expect(page).toHaveURL(/\/tasks\/task_[0-9]{8}$/);
  const taskId = new URL(page.url()).pathname.split("/").at(-1);
  if (!taskId) throw new Error("The dispatched task URL did not contain a task identifier.");

  const secondContext = await browser.newContext({
    baseURL: "http://127.0.0.1:3000",
    serviceWorkers: "block",
    storageState: "output/playwright/auth.json",
    viewport: { width: 390, height: 844 },
  });
  const secondPage = await secondContext.newPage();
  let secondDeviceDecisionPosts = 0;
  secondPage.on("request", (request) => {
    if (
      request.method() === "POST" &&
      request.url().endsWith(`/api/v1/tasks/${taskId}/decisions`)
    ) {
      secondDeviceDecisionPosts += 1;
    }
  });

  await secondPage.goto("/approvals");
  const staleRow = secondPage.locator(`#approval-row-${taskId}`);
  await expect(staleRow.getByRole("button", { name: "Reject", exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Approve", exact: true }).click();
  await expect(page.getByText("Run completed", { exact: true })).toBeVisible();
  await staleRow.getByRole("button", { name: "Reject", exact: true }).click();

  const staleNotice = secondPage.getByRole("alert").filter({
    hasText:
      "This approval is no longer current. No decision was sent. The latest task state is shown.",
  });
  await expect(staleNotice).toBeVisible();
  await expect(staleNotice).toBeFocused();
  await expect(staleRow).toHaveCount(0);
  expect(secondDeviceDecisionPosts).toBe(0);

  await secondContext.close();
});

test("a decision won after preflight is reconciled from the server without a second audit event", async ({
  browser,
  page,
}) => {
  const objective = "Reconcile the narrow approval race between preflight and submission";

  await page.goto("/tasks/new");
  await page.getByLabel("Task", { exact: true }).fill(objective);
  await page.getByRole("button", { name: "Dispatch" }).click();
  await expect(page).toHaveURL(/\/tasks\/task_[0-9]{8}$/);
  const taskUrl = page.url();
  const taskId = new URL(taskUrl).pathname.split("/").at(-1);
  if (!taskId) throw new Error("The dispatched task URL did not contain a task identifier.");

  const secondContext = await browser.newContext({
    baseURL: "http://127.0.0.1:3000",
    serviceWorkers: "block",
    storageState: "output/playwright/auth.json",
    viewport: { width: 390, height: 844 },
  });
  const secondPage = await secondContext.newPage();
  let releaseStaleStream!: () => void;
  const staleStreamReleased = new Promise<void>((resolve) => {
    releaseStaleStream = resolve;
  });
  await secondPage.route(`**/api/v1/tasks/${taskId}/events`, async (route) => {
    await staleStreamReleased;
    await route.abort("connectionfailed");
  });

  let detailReads = 0;
  let releasePreflight!: () => void;
  const preflightReleased = new Promise<void>((resolve) => {
    releasePreflight = resolve;
  });
  let markPreflightCaptured!: () => void;
  const preflightCaptured = new Promise<void>((resolve) => {
    markPreflightCaptured = resolve;
  });
  await secondPage.route(`**/api/v1/tasks/${taskId}`, async (route) => {
    detailReads += 1;
    const response = await route.fetch();
    if (detailReads === 2) {
      markPreflightCaptured();
      await preflightReleased;
    }
    await route.fulfill({ response });
  });
  let secondDeviceDecisionPosts = 0;
  secondPage.on("request", (request) => {
    if (
      request.method() === "POST" &&
      request.url().endsWith(`/api/v1/tasks/${taskId}/decisions`)
    ) {
      secondDeviceDecisionPosts += 1;
    }
  });

  await secondPage.goto(taskUrl);
  await expect(secondPage.getByRole("button", { name: "Reject", exact: true })).toBeVisible();
  await secondPage.getByRole("button", { name: "Reject", exact: true }).click();
  await preflightCaptured;

  await page.getByRole("button", { name: "Approve", exact: true }).click();
  await expect(page.getByText("Run completed", { exact: true })).toBeVisible();
  releasePreflight();

  const conflictNotice = secondPage.getByRole("alert").filter({
    hasText:
      "A different decision was already recorded. The current task and interruption were reloaded.",
  });
  await expect(conflictNotice).toBeVisible();
  await expect(conflictNotice).toBeFocused();
  expect(secondDeviceDecisionPosts).toBe(1);
  const eventTranscript = await page.request.get(`/api/v1/tasks/${taskId}/events`);
  expect((await eventTranscript.text()).match(/event: decision\.recorded/g)).toHaveLength(1);

  releaseStaleStream();
  await secondContext.close();
});
