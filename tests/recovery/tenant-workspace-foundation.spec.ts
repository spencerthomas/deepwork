import { type ChildProcess, spawn } from "node:child_process";
import { randomBytes } from "node:crypto";
import { mkdtemp, readFile, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

import { expect, test, type BrowserContext, type Page, type TestInfo } from "@playwright/test";

import { approveCurrentReview } from "../e2e/support/approve-current-review";

const repositoryRoot = process.cwd();
const apiPython = resolve(repositoryRoot, "apps/api/.venv/bin/python");
const apiLauncher = resolve(repositoryRoot, "tests/recovery/support/tenant_api.py");
const apiOrigin = "http://127.0.0.1:8000";
const webOrigin = "http://127.0.0.1:3000";
const generated = (label: string): string => `${label}-${randomBytes(18).toString("hex")}`;
const accessKeyA = generated("key-a");
const accessKeyB = generated("key-b");
const tenantA = generated("tenant-a");
const tenantB = generated("tenant-b");
const actorA = generated("actor-a");
const actorB = generated("actor-b");
const sharedWorkspace = generated("workspace-shared");
const forbiddenRetainedValues = [accessKeyA, accessKeyB, tenantA, tenantB] as const;
const apiOutputLimit = 8_000;

interface RetainedSnapshot {
  detail: Record<string, unknown>;
  events: string;
  listing: Record<string, unknown>;
  result: Record<string, unknown>;
  trace: Record<string, unknown>;
}

interface ReviewCheckpoint {
  interruptId: string;
  planRevision: number;
  steps: string[];
  version: string;
}

interface ForeignResponse {
  body: string;
  label: string;
  status: number;
}

let apiProcess: ChildProcess | undefined;
let databaseDirectory: string | undefined;
let taskDatabasePath: string | undefined;
let settingsDatabasePath: string | undefined;
let apiOutput = "";

function redact(value: string): string {
  return [...forbiddenRetainedValues, actorA, actorB, sharedWorkspace].reduce(
    (safe, secret) => safe.replaceAll(secret, "[redacted]"),
    value,
  );
}

function appendApiOutput(chunk: string): void {
  apiOutput = `${apiOutput}${chunk}`.slice(-apiOutputLimit);
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
    `API did not become ${expectedReady ? "ready" : "stopped"}: ${lastProblem}\n${redact(apiOutput).slice(-4_000)}`,
  );
}

async function startApi(): Promise<void> {
  if (!taskDatabasePath || !settingsDatabasePath) {
    throw new Error("The recovery databases were not initialized.");
  }
  if (apiProcess && apiProcess.exitCode === null && apiProcess.signalCode === null) {
    throw new Error("The tenant recovery API is already running.");
  }
  await waitForApi(false, 2_000);
  apiOutput = "";
  apiProcess = spawn(
    apiPython,
    [
      apiLauncher,
      "--task-database",
      taskDatabasePath,
      "--settings-database",
      settingsDatabasePath,
      "--port",
      "8000",
    ],
    {
      cwd: resolve(repositoryRoot, "apps/api"),
      env: {
        DEEPWORK_TEST_ACCESS_KEY_A: accessKeyA,
        DEEPWORK_TEST_ACCESS_KEY_B: accessKeyB,
        DEEPWORK_TEST_ACTOR_A: actorA,
        DEEPWORK_TEST_ACTOR_B: actorB,
        DEEPWORK_TEST_TENANT_A: tenantA,
        DEEPWORK_TEST_TENANT_B: tenantB,
        DEEPWORK_TEST_WORKSPACE: sharedWorkspace,
        PYTHONUNBUFFERED: "1",
      },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  apiProcess.stdout?.on("data", (chunk: Buffer) => appendApiOutput(chunk.toString("utf8")));
  apiProcess.stderr?.on("data", (chunk: Buffer) => appendApiOutput(chunk.toString("utf8")));
  apiProcess.on("error", (error) => appendApiOutput(`${error.name}: ${error.message}\n`));
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
  const graceful = await Promise.race([
    exited.then(() => true),
    new Promise<false>((resolveTimeout) => {
      timeout = setTimeout(() => resolveTimeout(false), 5_000);
    }),
  ]).finally(() => clearTimeout(timeout));
  if (!graceful) {
    child.kill("SIGKILL");
    await exited;
  }
  apiProcess = undefined;
  await waitForApi(false, 2_000);
}

async function signIn(page: Page, accessKey: string): Promise<void> {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Connect to Deep Work" })).toBeVisible();
  await page.getByLabel("Workspace access key").fill(accessKey);
  await page.getByRole("button", { name: "Connect workspace" }).click();
  await expect(page).toHaveURL(/\/tasks$/);
}

async function signOut(page: Page): Promise<void> {
  await page.getByLabel("Account menu").click();
  await page.getByRole("menuitem", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/login$/);
}

async function readJson(page: Page, path: string): Promise<Record<string, unknown>> {
  return page.evaluate(async (url) => {
    const response = await fetch(url, { credentials: "include" });
    if (!response.ok) throw new Error(`${url} returned HTTP ${response.status}.`);
    return (await response.json()) as Record<string, unknown>;
  }, path);
}

async function readSnapshot(page: Page, taskId: string): Promise<RetainedSnapshot> {
  return page.evaluate(async (id) => {
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
      fetch(`/api/v1/tasks/${encodeURIComponent(id)}/events`, { credentials: "include" }),
    ]);
    if (!eventsResponse.ok) throw new Error(`events returned HTTP ${eventsResponse.status}.`);
    return { detail, result, trace, listing, events: await eventsResponse.text() };
  }, taskId);
}

function reviewCheckpoint(detail: Record<string, unknown>): ReviewCheckpoint {
  const pending = detail["pendingInterrupt"];
  const plan = detail["proposedPlan"];
  if (!pending || typeof pending !== "object" || !plan || typeof plan !== "object") {
    throw new Error("The waiting task had no review checkpoint.");
  }
  const interruptId = Reflect.get(pending, "interruptId");
  const version = Reflect.get(pending, "version");
  const planRevision = Reflect.get(plan, "revision");
  const steps = Reflect.get(plan, "steps");
  if (
    typeof interruptId !== "string" ||
    typeof version !== "string" ||
    typeof planRevision !== "number" ||
    !Array.isArray(steps) ||
    !steps.every((step) => typeof step === "string")
  ) {
    throw new Error("The waiting task review checkpoint was malformed.");
  }
  return { interruptId, version, planRevision, steps };
}

async function saveSystemPrompt(page: Page, value: string): Promise<void> {
  await page.goto("/settings/prompt");
  const prompt = page.locator("textarea");
  await expect(prompt).toBeEnabled();
  await prompt.fill(value);
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await expect(page.getByRole("button", { name: "Saved", exact: true })).toBeVisible();
}

async function expectSystemPrompt(page: Page, value: string): Promise<void> {
  await page.goto("/settings/prompt");
  const prompt = page.locator("textarea");
  await expect(prompt).toBeEnabled();
  await expect(prompt).toHaveValue(value);
}

async function inspectTask(page: Page, taskId: string, result: string): Promise<void> {
  await expect(page).toHaveURL(new RegExp(`/tasks/${taskId}$`));
  await expect(page.getByText(result, { exact: true }).first()).toBeVisible();
  await page.getByRole("tab", { name: "Sources" }).click();
  await expect(page.getByText(/evidence_[0-9]{8}/).first()).toBeVisible();
  await page.getByRole("tab", { name: "Files" }).click();
  await expect(page.getByText("result.md", { exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "Details" }).click();
  await expect(page.getByText("Execution trace", { exact: true })).toBeVisible();
}

async function attackForeignTask(
  page: Page,
  taskId: string,
  checkpoint: ReviewCheckpoint,
): Promise<ForeignResponse[]> {
  return page.evaluate(
    async ({ id, review }) => {
      const problem = { code: "task_not_found", message: "Task was not found." };
      const requests: Array<[string, string, RequestInit | undefined]> = [
        ["detail", `/api/v1/tasks/${id}`, undefined],
        ["result", `/api/v1/tasks/${id}/result`, undefined],
        ["trace", `/api/v1/tasks/${id}/trace`, undefined],
        ["events", `/api/v1/tasks/${id}/events`, undefined],
        ["cancel", `/api/v1/tasks/${id}/cancel`, { method: "POST" }],
        [
          "decision",
          `/api/v1/tasks/${id}/decisions`,
          {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ interruptId: review.interruptId, decision: "approve" }),
          },
        ],
        [
          "batch",
          `/api/v1/tasks/${id}/decision-batch`,
          {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({
              interruptId: review.interruptId,
              expectedVersion: review.version,
              idempotencyKey: "foreign-browser-batch",
              decisions: review.steps.map(() => ({ type: "approve" })),
            }),
          },
        ],
        [
          "plan",
          `/api/v1/tasks/${id}/plan`,
          {
            method: "PATCH",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({
              interruptId: review.interruptId,
              expectedRevision: review.planRevision,
              steps: ["A foreign tenant must not edit this plan."],
            }),
          },
        ],
      ];
      const responses = [];
      for (const [label, url, init] of requests) {
        const response = await fetch(url, { ...init, credentials: "include" });
        const body = await response.text();
        if (response.status !== 404 || body !== JSON.stringify(problem)) {
          throw new Error(`${label} did not return the safe not-found contract.`);
        }
        responses.push({ label, status: response.status, body });
      }
      return responses;
    },
    { id: taskId, review: checkpoint },
  );
}

async function retainedBrowserState(context: BrowserContext, page: Page): Promise<string> {
  const storage = await page.evaluate(() => ({
    local: Object.fromEntries(
      Array.from({ length: localStorage.length }, (_, index) => localStorage.key(index))
        .filter((key): key is string => key !== null)
        .map((key) => [key, localStorage.getItem(key)]),
    ),
    session: Object.fromEntries(
      Array.from({ length: sessionStorage.length }, (_, index) => sessionStorage.key(index))
        .filter((key): key is string => key !== null)
        .map((key) => [key, sessionStorage.getItem(key)]),
    ),
  }));
  return JSON.stringify({ storage, state: await context.storageState() });
}

async function artifactContents(directory: string): Promise<string[]> {
  try {
    const entries = await readdir(directory, { withFileTypes: true });
    const nested = await Promise.all(
      entries.map(async (entry) => {
        const path = join(directory, entry.name);
        return entry.isDirectory()
          ? artifactContents(path)
          : [Buffer.from(await readFile(path)).toString("utf8")];
      }),
    );
    return nested.flat();
  } catch (error) {
    if (error && typeof error === "object" && Reflect.get(error, "code") === "ENOENT") return [];
    throw error;
  }
}

test.describe.configure({ mode: "serial" });

test.beforeAll(async () => {
  databaseDirectory = await mkdtemp(join(tmpdir(), "deepwork-tenant-browser-recovery-"));
  taskDatabasePath = resolve(databaseDirectory, "tasks.sqlite");
  settingsDatabasePath = resolve(databaseDirectory, "settings.sqlite");
  await startApi();
});

test.afterAll(async () => {
  await stopApi();
  if (databaseDirectory) await rm(databaseDirectory, { recursive: true, force: true });
});

test("tenant and actor boundaries survive sign-out, evidence inspection, and API restart", async ({
  browser,
}, testInfo: TestInfo) => {
  expect(testInfo.project.use.trace).toBe("off");
  expect(testInfo.project.use.video).toBe("off");
  const retained: string[] = [];
  const context = await browser.newContext({ baseURL: webOrigin, serviceWorkers: "block" });
  const page = await context.newPage();
  const draftA = "A private unsent draft for the durable tenant recovery journey";
  const draftB = "B private unsent draft that must remain separate from A";
  const promptA = "Return a concise, evidence-led result for tenant A only.";

  await signIn(page, accessKeyA);
  retained.push(JSON.stringify(await readJson(page, "/api/v1/auth/session")));
  await page.goto("/tasks/new");
  await page.getByLabel("Task", { exact: true }).fill(draftA);
  await saveSystemPrompt(page, promptA);
  await page.goto("/tasks");
  await signOut(page);

  await signIn(page, accessKeyB);
  retained.push(JSON.stringify(await readJson(page, "/api/v1/auth/session")));
  await expect(page.getByText("No tasks yet", { exact: true })).toBeVisible();
  await page.goto("/tasks/new");
  await expect(page.getByLabel("Task", { exact: true })).toHaveValue("");
  await expectSystemPrompt(page, "");
  retained.push(JSON.stringify(await readJson(page, "/api/v1/settings/prompt")));
  await page.goto("/tasks/new");
  await page.getByLabel("Task", { exact: true }).fill(draftB);
  await signOut(page);

  await signIn(page, accessKeyA);
  await page.goto("/tasks/new");
  const composer = page.getByLabel("Task", { exact: true });
  await expect(composer).toHaveValue(draftA);
  await expect(composer).not.toHaveValue(draftB);
  await page.getByRole("button", { name: "Dispatch" }).click();
  await expect(page).toHaveURL(/\/tasks\/task_[0-9]{8}$/);
  const taskId = new URL(page.url()).pathname.split("/").at(-1);
  if (!taskId) throw new Error("The dispatched task URL had no task identifier.");
  const header = page.getByRole("heading", { level: 1 }).locator("..");
  await expect(header.getByText("Needs review", { exact: true })).toBeVisible();
  const waiting = await readJson(page, `/api/v1/tasks/${taskId}`);
  const checkpoint = reviewCheckpoint(waiting);
  await approveCurrentReview(page);
  await expect(header.getByText("Done", { exact: true })).toBeVisible();
  const beforeRestart = await readSnapshot(page, taskId);
  const usefulResult = String(beforeRestart.result["result"]);
  expect(usefulResult.length).toBeGreaterThan(40);
  await inspectTask(page, taskId, usefulResult);
  await page.getByRole("link", { name: "All tasks" }).click();
  await expect(page).toHaveURL(/\/tasks$/);
  await page.locator(`a[href="/tasks/${taskId}"]`).first().click();
  await inspectTask(page, taskId, usefulResult);
  await signOut(page);

  await signIn(page, accessKeyB);
  await expect(page.getByText("No tasks yet", { exact: true })).toBeVisible();
  await page.goto("/tasks/new");
  await expect(page.getByLabel("Task", { exact: true })).toHaveValue(draftB);
  await expect(page.getByLabel("Task", { exact: true })).not.toHaveValue(draftA);
  const foreignResponses = await attackForeignTask(page, taskId, checkpoint);
  expect(foreignResponses).toHaveLength(8);
  retained.push(JSON.stringify(foreignResponses));
  retained.push(await retainedBrowserState(context, page));
  await context.close();

  await stopApi();
  await startApi();

  const recoveredA = await browser.newContext({ baseURL: webOrigin, serviceWorkers: "block" });
  const recoveredAPage = await recoveredA.newPage();
  await signIn(recoveredAPage, accessKeyA);
  await expectSystemPrompt(recoveredAPage, promptA);
  retained.push(JSON.stringify(await readJson(recoveredAPage, "/api/v1/settings/prompt")));
  await recoveredAPage.goto("/tasks");
  await recoveredAPage.locator(`a[href="/tasks/${taskId}"]`).first().click();
  const afterRestart = await readSnapshot(recoveredAPage, taskId);
  expect(afterRestart).toEqual(beforeRestart);
  await inspectTask(recoveredAPage, taskId, usefulResult);
  retained.push(JSON.stringify(afterRestart));
  await recoveredA.close();

  const recoveredB = await browser.newContext({ baseURL: webOrigin, serviceWorkers: "block" });
  const recoveredBPage = await recoveredB.newPage();
  await signIn(recoveredBPage, accessKeyB);
  await expect(recoveredBPage.getByText("No tasks yet", { exact: true })).toBeVisible();
  await expectSystemPrompt(recoveredBPage, "");
  const foreignAfterRestart = await recoveredBPage.evaluate(async (id) => {
    const [listing, detail] = await Promise.all([
      fetch("/api/v1/tasks", { credentials: "include" }),
      fetch(`/api/v1/tasks/${id}`, { credentials: "include" }),
    ]);
    return {
      listing: await listing.text(),
      listingStatus: listing.status,
      detail: await detail.text(),
      detailStatus: detail.status,
    };
  }, taskId);
  expect(foreignAfterRestart).toEqual({
    listing: '{"items":[]}',
    listingStatus: 200,
    detail: '{"code":"task_not_found","message":"Task was not found."}',
    detailStatus: 404,
  });
  retained.push(JSON.stringify(foreignAfterRestart));
  retained.push(await retainedBrowserState(recoveredB, recoveredBPage));
  await recoveredB.close();

  const retainedText = retained.join("\n");
  const files = await artifactContents(testInfo.outputDir);
  for (const forbidden of forbiddenRetainedValues) {
    expect(retainedText).not.toContain(forbidden);
    for (const file of files) expect(file).not.toContain(forbidden);
  }
});
