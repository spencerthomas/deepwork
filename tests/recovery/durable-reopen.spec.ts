import { randomBytes } from "node:crypto";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { spawn, type ChildProcess } from "node:child_process";

import { expect, test, type Page } from "@playwright/test";

import { approveCurrentReview } from "../e2e/support/approve-current-review";

const repositoryRoot = process.cwd();
const apiExecutable = resolve(repositoryRoot, "apps/api/.venv/bin/deepwork-api");
const apiOrigin = "http://127.0.0.1:8000";
const webOrigin = "http://127.0.0.1:3000";
const accessKey = randomBytes(32).toString("hex");
const apiOutputLimit = 8_000;
const hostileAmbientEnvironment = {
  DEEPWORK_ACCESS_KEY: "ambient-access-key-must-not-win",
  DEEPWORK_ENABLE_LOCAL_AGENT: "1",
  DEEPWORK_HOST: "0.0.0.0",
  DEEPWORK_LOCAL_AGENT_ASSISTANT: "ambient-agent",
  DEEPWORK_LOCAL_AGENT_ENDPOINT: "http://127.0.0.1:9",
  DEEPWORK_SETTINGS_DB: "/must-not-exist/settings.sqlite",
  DEEPWORK_TASK_DB: "/must-not-exist/tasks.sqlite",
  LANGSMITH_API_KEY: "ambient-provider-canary-must-not-reach-child",
  PORT: "9",
} as const;

interface RetainedEvent {
  data: unknown;
  id: number;
  name: string;
}

interface TaskSnapshot {
  detail: Record<string, unknown>;
  events: RetainedEvent[];
  listing: Record<string, unknown>;
  result: Record<string, unknown>;
  trace: Record<string, unknown>;
}

let apiProcess: ChildProcess | undefined;
let databaseDirectory: string | undefined;
let databasePath: string | undefined;
let apiOutput = "";

function safeApiOutput(): string {
  return apiOutput.replaceAll(accessKey, "[redacted]").slice(-4_000);
}

function appendApiOutput(chunk: string): void {
  apiOutput = `${apiOutput}${chunk}`.slice(-apiOutputLimit);
}

async function withHostileAmbientEnvironment(operation: () => Promise<void>): Promise<void> {
  const originalValues = new Map(
    Object.keys(hostileAmbientEnvironment).map((name) => [name, process.env[name]]),
  );
  Object.assign(process.env, hostileAmbientEnvironment);
  try {
    await operation();
  } finally {
    for (const [name, value] of originalValues) {
      if (value === undefined) delete process.env[name];
      else process.env[name] = value;
    }
  }
}

async function waitForApi(expectedReady: boolean, timeoutMs = 15_000): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  let lastProblem = "no health response";
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${apiOrigin}/health`, {
        signal: AbortSignal.timeout(500),
      });
      if (response.ok === expectedReady) return;
      lastProblem = `health returned HTTP ${response.status}`;
    } catch (error) {
      if (!expectedReady) return;
      lastProblem = error instanceof Error ? error.message : "health request failed";
    }
    await new Promise((resolveDelay) => setTimeout(resolveDelay, 100));
  }
  throw new Error(
    `API did not become ${expectedReady ? "ready" : "stopped"} within ${timeoutMs}ms: ${lastProblem}\n${safeApiOutput()}`,
  );
}

async function startApi(): Promise<void> {
  if (!databasePath) throw new Error("The recovery database was not initialized.");
  if (apiProcess && apiProcess.exitCode === null && apiProcess.signalCode === null)
    throw new Error("The recovery API is already running.");
  // Refuse to characterize an unrelated process that already owns the test
  // port. Both initial start and restart must begin from an observed outage.
  await waitForApi(false, 2_000);

  apiOutput = "";
  apiProcess = spawn(apiExecutable, ["--task-database", databasePath, "--port", "8000"], {
    cwd: resolve(repositoryRoot, "apps/api"),
    env: {
      DEEPWORK_ACCESS_KEY: accessKey,
      DEEPWORK_HOST: "127.0.0.1",
      PORT: "8000",
    },
    stdio: ["ignore", "pipe", "pipe"],
  });
  apiProcess.stdout?.on("data", (chunk: Buffer) => {
    appendApiOutput(chunk.toString("utf8"));
  });
  apiProcess.stderr?.on("data", (chunk: Buffer) => {
    appendApiOutput(chunk.toString("utf8"));
  });
  apiProcess.on("error", (error) => {
    appendApiOutput(`${error.name}: ${error.message}\n`);
  });

  try {
    await waitForApi(true);
  } catch (error) {
    await stopApi();
    throw error;
  }
}

async function stopApi(): Promise<void> {
  const child = apiProcess;
  if (!child || child.exitCode !== null || child.signalCode !== null) {
    apiProcess = undefined;
    await waitForApi(false, 2_000);
    return;
  }

  const exited = new Promise<void>((resolveExit) => child.once("exit", () => resolveExit()));
  child.kill("SIGTERM");
  let timeout: ReturnType<typeof setTimeout> | undefined;
  const stoppedGracefully = await Promise.race([
    exited.then(() => true),
    new Promise<false>((resolveTimeout) => {
      timeout = setTimeout(() => resolveTimeout(false), 5_000);
    }),
  ]).finally(() => clearTimeout(timeout));
  if (!stoppedGracefully) {
    child.kill("SIGKILL");
    await exited;
  }
  apiProcess = undefined;
  await waitForApi(false, 2_000);
}

function parseEventStream(body: string): RetainedEvent[] {
  return body
    .trim()
    .split(/\r?\n\r?\n/)
    .filter(Boolean)
    .map((record) => {
      const fields = new Map(
        record.split(/\r?\n/).map((line) => {
          const separator = line.indexOf(":");
          return [line.slice(0, separator), line.slice(separator + 1).trimStart()] as const;
        }),
      );
      const id = Number(fields.get("id"));
      const name = fields.get("event");
      const data = fields.get("data");
      if (!Number.isSafeInteger(id) || id < 1 || !name || !data) {
        throw new Error("The retained event stream was malformed.");
      }
      return { id, name, data: JSON.parse(data) as unknown };
    });
}

async function readSnapshot(page: Page, taskId: string): Promise<TaskSnapshot> {
  const raw = await page.evaluate(async (id) => {
    async function json(path: string): Promise<Record<string, unknown>> {
      const response = await fetch(path, { credentials: "include" });
      if (!response.ok) throw new Error(`${path} returned HTTP ${response.status}.`);
      return (await response.json()) as Record<string, unknown>;
    }

    const [detail, result, trace, listing, eventsResponse] = await Promise.all([
      json(`/api/v1/tasks/${encodeURIComponent(id)}`),
      json(`/api/v1/tasks/${encodeURIComponent(id)}/result`),
      json(`/api/v1/tasks/${encodeURIComponent(id)}/trace`),
      json("/api/v1/tasks"),
      fetch(`/api/v1/tasks/${encodeURIComponent(id)}/events`, {
        credentials: "include",
      }),
    ]);
    if (!eventsResponse.ok) {
      throw new Error(`events returned HTTP ${eventsResponse.status}.`);
    }
    return { detail, result, trace, listing, events: await eventsResponse.text() };
  }, taskId);

  return { ...raw, events: parseEventStream(raw.events) };
}

async function installLoopbackOnlyGuard(page: Page): Promise<Set<string>> {
  const unexpectedOrigins = new Set<string>();
  const cdp = await page.context().newCDPSession(page);
  await cdp.send("Fetch.enable", {
    patterns: [{ urlPattern: "http://*" }, { urlPattern: "https://*" }],
  });
  cdp.on("Fetch.requestPaused", (event) => {
    void (async () => {
      const url = new URL(event.request.url);
      if (url.hostname !== "127.0.0.1") {
        unexpectedOrigins.add(url.origin);
        await cdp.send("Fetch.failRequest", {
          requestId: event.requestId,
          errorReason: "BlockedByClient",
        });
        return;
      }
      await cdp.send("Fetch.continueRequest", { requestId: event.requestId });
    })();
  });
  await page.routeWebSocket(/^wss?:\/\//, async (socket) => {
    const url = new URL(socket.url());
    if (url.hostname !== "127.0.0.1") {
      unexpectedOrigins.add(url.origin);
      await socket.close({ code: 1008, reason: "Non-loopback browser traffic is blocked" });
      return;
    }
    socket.connectToServer();
  });
  return unexpectedOrigins;
}

async function signIn(page: Page): Promise<void> {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Connect to Deep Work" })).toBeVisible();
  await page.getByLabel("Workspace access key").fill(accessKey);
  await page.getByRole("button", { name: "Connect workspace" }).click();
  await expect(page).toHaveURL(/\/tasks$/);
}

async function inspectTaskUi(
  page: Page,
  taskId: string,
  snapshot: TaskSnapshot,
): Promise<Array<{ download: string | null; href: string | null }>> {
  await expect(page).toHaveURL(new RegExp(`/tasks/${taskId}$`));
  await expect(page.getByText(taskId, { exact: true }).first()).toBeVisible();
  await expect(page.getByText("Run completed", { exact: true })).toBeVisible();
  await expect(
    page.getByText(String(snapshot.result["result"]), { exact: true }).first(),
  ).toBeVisible();

  const evidence = snapshot.detail["evidence"];
  expect(Array.isArray(evidence)).toBe(true);
  expect(evidence.length).toBeGreaterThan(0);
  await page.getByRole("tab", { name: "Sources" }).click();
  for (const item of evidence) {
    if (!item || typeof item !== "object") throw new Error("Task evidence was malformed.");
    const evidenceId = Reflect.get(item, "evidenceId");
    if (typeof evidenceId !== "string") throw new Error("Task evidence had no identifier.");
    await expect(page.getByText(evidenceId, { exact: false }).first()).toBeVisible();
  }

  await page.getByRole("tab", { name: "Files" }).click();
  await expect(page.getByText("result.md", { exact: true })).toBeVisible();
  const artifacts = await page.locator("a[download]").evaluateAll((links) =>
    links.map((link) => ({
      download: link.getAttribute("download"),
      href: link.getAttribute("href"),
    })),
  );
  expect(artifacts.length).toBeGreaterThan(1);

  await page.getByRole("tab", { name: "Details" }).click();
  await expect(page.getByText("Execution trace", { exact: true })).toBeVisible();
  const eventCountRow = page.getByText("Retained events", { exact: true }).locator("..");
  await expect(
    eventCountRow.getByText(String(snapshot.events.length), { exact: true }),
  ).toBeVisible();
  const expectedTraceLabel =
    snapshot.trace["state"] === "available" ? "Available" : "Not available";
  await expect(page.getByText(expectedTraceLabel, { exact: true })).toBeVisible();
  return artifacts;
}

test.describe.configure({ mode: "serial" });

test.beforeAll(async () => {
  databaseDirectory = await mkdtemp(join(tmpdir(), "deepwork-browser-recovery-"));
  databasePath = resolve(databaseDirectory, "tasks.sqlite");
  await withHostileAmbientEnvironment(startApi);
});

test.afterAll(async () => {
  await stopApi();
  if (databaseDirectory) {
    await rm(databaseDirectory, { recursive: true, force: true });
  }
});

test("completed fixture task survives an API restart and reopens without duplicate events", async ({
  browser,
}) => {
  const firstContext = await browser.newContext({ baseURL: webOrigin, serviceWorkers: "block" });
  const firstPage = await firstContext.newPage();
  const firstUnexpectedOrigins = await installLoopbackOnlyGuard(firstPage);

  await signIn(firstPage);
  await firstPage.goto("/tasks/new");
  const objective = "Prepare a durable local restart acceptance result";
  await firstPage.getByLabel("Task", { exact: true }).fill(objective);
  await firstPage.getByRole("button", { name: "Dispatch" }).click();
  await expect(firstPage).toHaveURL(/\/tasks\/task_[0-9]{8}$/);
  const taskId = new URL(firstPage.url()).pathname.split("/").at(-1);
  if (!taskId) throw new Error("The created task URL did not contain a task identifier.");

  const header = firstPage.getByRole("heading", { level: 1 }).locator("..");
  await expect(header.getByText("Needs review", { exact: true })).toBeVisible();
  await approveCurrentReview(firstPage);
  await expect(header.getByText("Done", { exact: true })).toBeVisible();

  const beforeRestart = await readSnapshot(firstPage, taskId);
  expect(beforeRestart.detail["taskId"]).toBe(taskId);
  expect(beforeRestart.detail["status"]).toBe("completed");
  expect(beforeRestart.result["taskId"]).toBe(taskId);
  expect(beforeRestart.trace).toEqual({
    taskId,
    traceUrl: null,
    state: "unavailable",
  });
  expect(beforeRestart.events.map((event) => event.id)).toEqual(
    Array.from({ length: beforeRestart.events.length }, (_, index) => index + 1),
  );
  const beforeArtifacts = await inspectTaskUi(firstPage, taskId, beforeRestart);

  await stopApi();
  await firstPage.getByRole("button", { name: "Run again" }).click();
  await expect(
    firstPage.getByText("The re-run could not be started.", { exact: false }).first(),
  ).toBeVisible();
  await expect(firstPage).toHaveURL(new RegExp(`/tasks/${taskId}$`));
  await expect(firstPage.getByText("Run completed", { exact: true })).toBeVisible();
  expect(firstUnexpectedOrigins).toEqual(new Set());
  await firstContext.close();

  await withHostileAmbientEnvironment(startApi);

  const recoveredContext = await browser.newContext({
    baseURL: webOrigin,
    serviceWorkers: "block",
  });
  const recoveredPage = await recoveredContext.newPage();
  const recoveredUnexpectedOrigins = await installLoopbackOnlyGuard(recoveredPage);
  await signIn(recoveredPage);

  const taskLinks = recoveredPage.locator(`a[href="/tasks/${taskId}"]`);
  await expect(taskLinks.first()).toBeVisible();
  await taskLinks.first().click();
  await expect(recoveredPage).toHaveURL(new RegExp(`/tasks/${taskId}$`));

  const afterRestart = await readSnapshot(recoveredPage, taskId);
  expect(afterRestart).toEqual(beforeRestart);
  const afterArtifacts = await inspectTaskUi(recoveredPage, taskId, afterRestart);
  expect(afterArtifacts).toEqual(beforeArtifacts);
  expect((afterRestart.listing["items"] as unknown[]).length).toBe(1);
  expect(recoveredUnexpectedOrigins).toEqual(new Set());
  await recoveredContext.close();
});

test("a lost create response replays the original task identity after an API restart", async ({
  browser,
}) => {
  const context = await browser.newContext({ baseURL: webOrigin, serviceWorkers: "block" });
  const page = await context.newPage();
  const unexpectedOrigins = await installLoopbackOnlyGuard(page);
  const requests: Array<{ body: string | null; key: string | undefined }> = [];
  let taskId = "";
  let runId = "";
  let replayWasDuplicate = false;
  let requestCount = 0;

  await signIn(page);
  const baselineTaskIds = await page.evaluate(async () => {
    const response = await fetch("/api/v1/tasks", { credentials: "include" });
    if (!response.ok) throw new Error("The baseline task list could not be read.");
    const listing = (await response.json()) as { items: Array<{ taskId: string }> };
    return listing.items.map((item) => item.taskId);
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
      taskId = String(receipt["taskId"]);
      runId = String(receipt["runId"]);
      await route.abort("connectionfailed");
      return;
    }
    if (requestCount === 2) {
      await route.abort("connectionfailed");
      return;
    }
    const response = await route.fetch();
    expect(response.status()).toBe(202);
    const receipt = (await response.json()) as Record<string, unknown>;
    expect(receipt["taskId"]).toBe(taskId);
    expect(receipt["runId"]).toBe(runId);
    replayWasDuplicate = receipt["duplicate"] === true;
    await route.fulfill({ response });
  });

  await page.goto("/tasks/new");
  const objective = "Recover the original dispatch after a durable API restart";
  await page.getByLabel("Task", { exact: true }).fill(objective);
  await page.getByRole("button", { name: "Dispatch" }).click();
  await expect(page.getByText("Task start not confirmed.", { exact: true })).toBeVisible();
  expect(requestCount).toBe(2);
  expect(requests[0]?.key).toBeTruthy();
  expect(requests[1]).toEqual(requests[0]);

  await expect
    .poll(() =>
      page.evaluate(async (id) => {
        const response = await fetch(`/api/v1/tasks/${encodeURIComponent(id)}`, {
          credentials: "include",
        });
        if (!response.ok) return `http-${response.status}`;
        const detail = (await response.json()) as { status: string };
        return detail.status;
      }, taskId),
    )
    .toBe("waiting-approval");

  await stopApi();
  await withHostileAmbientEnvironment(startApi);
  // The local API intentionally rotates its in-memory session signer on
  // restart. Reconnect the same browser context, preserving origin-scoped
  // dispatch storage, before reopening the composer.
  await context.clearCookies();
  await signIn(page);
  await page.goto("/tasks/new");
  await expect(page.getByText("Task start not confirmed.", { exact: true })).toBeVisible();
  await expect(page.getByLabel("Task", { exact: true })).toHaveValue(objective);
  expect(requestCount).toBe(2);

  await page.getByRole("button", { name: "Check task" }).click();
  await expect(page).toHaveURL(new RegExp(`/tasks/${taskId}$`));
  // Startup reconciliation marks the interrupted run terminal rather than
  // pretending it can resume. The dispatch receipt must still resolve to that
  // one durable task instead of launching another run.
  await expect(page.getByText("Failed", { exact: true }).first()).toBeVisible();
  expect(replayWasDuplicate).toBe(true);
  expect(requests).toHaveLength(3);
  expect(requests[2]).toEqual(requests[0]);

  const retained = await page.evaluate(async (id) => {
    const [detailResponse, listingResponse, eventsResponse] = await Promise.all([
      fetch(`/api/v1/tasks/${encodeURIComponent(id)}`, { credentials: "include" }),
      fetch("/api/v1/tasks", { credentials: "include" }),
      fetch(`/api/v1/tasks/${encodeURIComponent(id)}/events`, { credentials: "include" }),
    ]);
    if (!detailResponse.ok || !listingResponse.ok || !eventsResponse.ok) {
      throw new Error("The restarted task proof could not be read.");
    }
    return {
      detail: (await detailResponse.json()) as Record<string, unknown>,
      listing: (await listingResponse.json()) as Record<string, unknown>,
      events: await eventsResponse.text(),
    };
  }, taskId);
  const retainedEvents = parseEventStream(retained.events);
  expect(retained.detail).toMatchObject({ taskId, runId, status: "failed" });
  expect(retainedEvents.filter((event) => event.name === "task.created")).toHaveLength(1);
  expect(
    (retained.listing["items"] as Array<{ taskId: string }>)
      .map((item) => item.taskId)
      .filter((candidate) => !baselineTaskIds.includes(candidate)),
  ).toEqual([taskId]);
  expect(unexpectedOrigins).toEqual(new Set());
  await context.close();
});

test("reconnect episodes recover once, ignore a late initial read, and suppress duplicate events", async ({
  browser,
}) => {
  const taskId = "task_recovery_browser";
  const runId = "run_recovery_browser";
  const objective = "Recover a dropped live task without losing its result";
  const completedResult = "The durable task state was recovered after the stream disconnected.";
  let detailReads = 0;
  let eventRequests = 0;
  let releaseInitialDetail!: () => void;
  const initialDetailReleased = new Promise<void>((resolveRelease) => {
    releaseInitialDetail = resolveRelease;
  });
  let releaseProgressStream!: () => void;
  const progressStreamReleased = new Promise<void>((resolveRelease) => {
    releaseProgressStream = resolveRelease;
  });
  let releaseTerminalStream!: () => void;
  const terminalStreamReleased = new Promise<void>((resolveRelease) => {
    releaseTerminalStream = resolveRelease;
  });
  const context = await browser.newContext({ baseURL: webOrigin, serviceWorkers: "block" });
  const page = await context.newPage();
  const unexpectedOrigins = await installLoopbackOnlyGuard(page);

  await signIn(page);
  await page.route(`**/api/v1/tasks/${taskId}/events`, async (route) => {
    eventRequests += 1;
    if (eventRequests === 2) {
      await route.abort("connectionfailed");
      return;
    }
    if (eventRequests === 3) await progressStreamReleased;
    if (eventRequests === 4) await terminalStreamReleased;
    if (eventRequests > 4) {
      await route.abort("connectionfailed");
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      headers: { "cache-control": "no-cache" },
      body:
        eventRequests === 4
          ? [
              'id: 3\nevent: content.delta\ndata: {"delta":"Recovered durable progress."}',
              `id: 4\nevent: run.completed\ndata: ${JSON.stringify({ status: "completed", result: completedResult })}`,
              "",
            ].join("\n\n")
          : eventRequests === 3
            ? [
                'id: 2\nevent: run.started\ndata: {"status":"running"}',
                'id: 3\nevent: content.delta\ndata: {"delta":"Recovered durable progress."}',
                "",
              ].join("\n\n")
            : [
                'id: 1\nevent: task.created\ndata: {"status":"queued"}',
                'id: 2\nevent: run.started\ndata: {"status":"running"}',
                "",
              ].join("\n\n"),
    });
  });
  await page.route(`**/api/v1/tasks/${taskId}`, async (route) => {
    detailReads += 1;
    const read = detailReads;
    if (read === 1) await initialDetailReleased;
    const completed = read >= 2;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        taskId,
        runId,
        title: objective,
        objective,
        status: completed ? "completed" : read === 1 ? "queued" : "running",
        lastEventId: completed ? 4 : 1,
        evidence: [],
        ...(completed ? { result: completedResult } : {}),
      }),
    });
  });
  await page.route("**/api/v1/tasks", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [{ taskId, runId, title: objective, objective, status: "running", lastEventId: 2 }],
      }),
    });
  });

  await page.goto(`/tasks/${taskId}`);
  await expect(page.getByRole("heading", { name: objective })).toBeVisible();
  await expect(
    page.getByText("Recovered current task state from the API while the live stream reconnects."),
  ).toBeVisible({ timeout: 20_000 });
  await expect.poll(() => eventRequests).toBeGreaterThanOrEqual(3);
  expect(detailReads).toBe(2);

  releaseInitialDetail();
  await expect(page.getByText("Run started", { exact: true })).toHaveCount(1);
  await expect(
    page.getByText("Recovered current task state from the API while the live stream reconnects."),
  ).toBeVisible();

  releaseProgressStream();
  await expect.poll(() => detailReads, { timeout: 15_000 }).toBe(3);
  await expect.poll(() => eventRequests, { timeout: 15_000 }).toBeGreaterThanOrEqual(4);
  releaseTerminalStream();
  await expect(page.getByText(completedResult, { exact: true }).first()).toBeVisible();
  await expect.poll(() => detailReads).toBe(4);
  await expect(page.getByText("Run started", { exact: true })).toHaveCount(1);

  const eventCountRow = page.getByText("Events", { exact: true }).locator("..");
  await expect(eventCountRow.getByText("4", { exact: true })).toBeVisible();
  expect(unexpectedOrigins).toEqual(new Set());
  await context.close();
});

test("a timed-out recovery retains the last known state while EventSource keeps retrying", async ({
  browser,
}) => {
  const taskId = "task_recovery_timeout";
  const runId = "run_recovery_timeout";
  const objective = "Keep useful state visible through a stalled recovery read";
  const completedResult = "The live stream eventually supplied the terminal result.";
  let detailReads = 0;
  let eventRequests = 0;
  let releaseRecoveryRead!: () => void;
  const recoveryReadReleased = new Promise<void>((resolveRelease) => {
    releaseRecoveryRead = resolveRelease;
  });
  let releaseRetryStream!: () => void;
  const retryStreamReleased = new Promise<void>((resolveRelease) => {
    releaseRetryStream = resolveRelease;
  });
  const context = await browser.newContext({ baseURL: webOrigin, serviceWorkers: "block" });
  const page = await context.newPage();
  const unexpectedOrigins = await installLoopbackOnlyGuard(page);

  await signIn(page);
  await page.route(`**/api/v1/tasks/${taskId}/events`, async (route) => {
    eventRequests += 1;
    if (eventRequests === 2) await retryStreamReleased;
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      headers: { "cache-control": "no-cache" },
      body:
        eventRequests === 1
          ? [
              'id: 1\nevent: task.created\ndata: {"status":"queued"}',
              'id: 2\nevent: run.started\ndata: {"status":"running"}',
              "",
            ].join("\n\n")
          : [
              'id: 2\nevent: run.started\ndata: {"status":"running"}',
              'id: 3\nevent: content.delta\ndata: {"delta":"Progress after retry."}',
              `id: 4\nevent: run.completed\ndata: ${JSON.stringify({ status: "completed", result: completedResult })}`,
              "",
            ].join("\n\n"),
    });
  });
  await page.route(`**/api/v1/tasks/${taskId}`, async (route) => {
    detailReads += 1;
    const read = detailReads;
    if (read === 2) {
      await recoveryReadReleased;
    }
    await route
      .fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          taskId,
          runId,
          title: objective,
          objective,
          status: read >= 3 ? "completed" : "running",
          lastEventId: read >= 3 ? 4 : 2,
          evidence: [],
          ...(read >= 3 ? { result: completedResult } : {}),
        }),
      })
      .catch(() => undefined);
  });
  await page.route("**/api/v1/tasks", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [{ taskId, runId, title: objective, objective, status: "running", lastEventId: 2 }],
      }),
    });
  });

  await page.goto(`/tasks/${taskId}`);
  await expect(page.getByRole("heading", { name: objective })).toBeVisible();
  await expect(
    page.getByText(
      /Could not recover current task state from the API\. The last known state is still shown/,
    ),
  ).toBeVisible({ timeout: 20_000 });
  expect(detailReads).toBe(2);
  await expect.poll(() => eventRequests).toBeGreaterThanOrEqual(2);
  await expect(page.getByText("Run started", { exact: true })).toHaveCount(1);

  releaseRecoveryRead();
  releaseRetryStream();
  await expect(page.getByText(completedResult, { exact: true }).first()).toBeVisible();
  await expect(
    page.getByText(
      /Could not recover current task state from the API\. The last known state is still shown/,
    ),
  ).not.toBeVisible();
  await expect(page.getByText("Run started", { exact: true })).toHaveCount(1);
  const eventCountRow = page.getByText("Events", { exact: true }).locator("..");
  await expect(eventCountRow.getByText("4", { exact: true })).toBeVisible();
  expect(unexpectedOrigins).toEqual(new Set());
  await context.close();
});

test("a stale recovery snapshot stays unconfirmed until a newer live event arrives", async ({
  browser,
}) => {
  const taskId = "task_recovery_unconfirmed";
  const runId = "run_recovery_unconfirmed";
  const objective = "Keep a newer live projection when durable recovery trails it";
  const completedResult = "A newer live event restored confirmed progress.";
  let detailReads = 0;
  let eventRequests = 0;
  let releaseFreshStream!: () => void;
  const freshStreamReleased = new Promise<void>((resolveRelease) => {
    releaseFreshStream = resolveRelease;
  });
  const context = await browser.newContext({ baseURL: webOrigin, serviceWorkers: "block" });
  const page = await context.newPage();
  const unexpectedOrigins = await installLoopbackOnlyGuard(page);

  await signIn(page);
  await page.route(`**/api/v1/tasks/${taskId}/events`, async (route) => {
    eventRequests += 1;
    if (eventRequests === 2) await freshStreamReleased;
    if (eventRequests > 2) {
      await route.abort("connectionfailed");
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      headers: { "cache-control": "no-cache" },
      body:
        eventRequests === 1
          ? [
              'id: 1\nevent: task.created\ndata: {"status":"queued"}',
              'id: 2\nevent: run.started\ndata: {"status":"running"}',
              "",
            ].join("\n\n")
          : [
              `id: 6\nevent: run.completed\ndata: ${JSON.stringify({ status: "completed", result: completedResult })}`,
              "",
            ].join("\n\n"),
    });
  });
  await page.route(`**/api/v1/tasks/${taskId}`, async (route) => {
    detailReads += 1;
    const completed = detailReads >= 3;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        taskId,
        runId,
        title: objective,
        objective,
        status: completed ? "completed" : "running",
        lastEventId: completed ? 6 : detailReads === 1 ? 5 : 2,
        evidence: [],
        ...(completed ? { result: completedResult } : {}),
      }),
    });
  });
  await page.route("**/api/v1/tasks", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [{ taskId, runId, title: objective, objective, status: "running", lastEventId: 5 }],
      }),
    });
  });

  await page.goto(`/tasks/${taskId}`);
  await expect(page.getByRole("heading", { name: objective })).toBeVisible();
  await expect(
    page.getByText(
      "The live stream is newer than the API snapshot. The last known state is shown, but durable recovery is not yet confirmed.",
    ),
  ).toBeVisible({ timeout: 20_000 });
  expect(detailReads).toBe(2);
  await expect.poll(() => eventRequests).toBeGreaterThanOrEqual(2);

  releaseFreshStream();
  await expect(page.getByText(completedResult, { exact: true }).first()).toBeVisible();
  await expect(
    page.getByText(
      "The live stream is newer than the API snapshot. The last known state is shown, but durable recovery is not yet confirmed.",
    ),
  ).not.toBeVisible();
  const eventCountRow = page.getByText("Events", { exact: true }).locator("..");
  await expect(eventCountRow.getByText("3", { exact: true })).toBeVisible();
  expect(unexpectedOrigins).toEqual(new Set());
  await context.close();
});
