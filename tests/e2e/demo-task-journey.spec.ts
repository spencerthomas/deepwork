import { createServer } from "node:http";

import { expect, test as base } from "@playwright/test";

const redirectGuardProbeHost = "browser-redirect-guard.invalid";

const test = base.extend<{ redirectProbeUrl: string }>({
  redirectProbeUrl: async ({ browserName: _browserName }, use) => {
    const server = createServer((_request, response) => {
      response.writeHead(302, {
        "access-control-allow-origin": "*",
        location: `https://${redirectGuardProbeHost}/redirect-probe`,
      });
      response.end();
    });
    await new Promise<void>((resolve, reject) => {
      server.once("error", reject);
      server.listen(0, "127.0.0.1", () => {
        server.off("error", reject);
        resolve();
      });
    });
    const address = server.address();
    if (address === null || typeof address === "string") {
      throw new Error("The redirect probe server did not expose a loopback TCP address.");
    }
    try {
      await use(`http://127.0.0.1:${address.port}/redirect-probe`);
    } finally {
      await new Promise<void>((resolve, reject) => {
        server.close((error) => (error ? reject(error) : resolve()));
      });
    }
  },
});

test("creates, approves, and completes one API-backed task", async ({
  context,
  page,
  redirectProbeUrl,
}) => {
  const guardProbeHost = "browser-guard.invalid";
  const blockedGuardProbes = new Set<string>();
  const blockedRedirectGuardProbes = new Set<string>();
  const unexpectedEgress = new Set<string>();
  const pageErrors: string[] = [];
  let redirectProbeWasRequested = false;

  const cdp = await context.newCDPSession(page);
  await cdp.send("Fetch.enable", {
    patterns: [{ urlPattern: "http://*" }, { urlPattern: "https://*" }],
  });
  cdp.on("Fetch.requestPaused", (event) => {
    void (async () => {
      const url = new URL(event.request.url);
      if (url.href === redirectProbeUrl) {
        redirectProbeWasRequested = true;
      }
      if (url.hostname !== "127.0.0.1") {
        if (url.hostname === guardProbeHost) {
          blockedGuardProbes.add(url.protocol);
        } else if (url.hostname === redirectGuardProbeHost && redirectProbeWasRequested) {
          blockedRedirectGuardProbes.add(url.href);
        } else {
          unexpectedEgress.add(url.origin);
        }
        await cdp.send("Fetch.failRequest", {
          requestId: event.requestId,
          errorReason: "BlockedByClient",
        });
        return;
      }
      await cdp.send("Fetch.continueRequest", { requestId: event.requestId });
    })();
  });
  await page.routeWebSocket(/^wss?:\/\//, async (webSocket) => {
    const url = new URL(webSocket.url());
    if ((url.protocol === "ws:" || url.protocol === "wss:") && url.hostname !== "127.0.0.1") {
      if (url.hostname === guardProbeHost) {
        blockedGuardProbes.add(url.protocol);
      } else {
        unexpectedEgress.add(url.origin);
      }
      await webSocket.close({ code: 1008, reason: "Non-loopback browser traffic is blocked" });
      return;
    }
    webSocket.connectToServer();
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));

  await context.clearCookies();
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Connect to Deep Work" })).toBeVisible();
  await page.getByLabel("Workspace access key").fill("not-the-workspace-key");
  await page.getByRole("button", { name: "Connect workspace" }).click();
  await expect(page.getByText("That access key was not accepted.", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Connect workspace" })).toBeEnabled();
  await page.getByLabel("Workspace access key").fill("deepwork-local-browser-acceptance");
  const loginResponse = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      response.url() === "http://127.0.0.1:3000/api/v1/auth/login",
  );
  await page.getByRole("button", { name: "Connect workspace" }).click();
  expect((await loginResponse).status()).toBe(200);
  await expect(page).toHaveURL(/\/tasks$/);

  await page.goto("/tasks/new");
  await expect(page.getByRole("heading", { name: "New task" })).toBeVisible();
  await expect(page.getByRole("radio", { name: /General task/, checked: true })).toBeVisible();

  await page.evaluate(async (host) => {
    const webSocketProbe = new Promise<void>((resolve) => {
      const socket = new WebSocket(`wss://${host}/websocket-probe`);
      socket.addEventListener("close", () => resolve(), { once: true });
      socket.addEventListener("error", () => resolve(), { once: true });
    });
    await Promise.all([fetch(`https://${host}/http-probe`).catch(() => undefined), webSocketProbe]);
  }, guardProbeHost);
  await expect.poll(() => [...blockedGuardProbes].sort()).toEqual(["https:", "wss:"]);

  await page.evaluate((url) => fetch(url).catch(() => undefined), redirectProbeUrl);
  await expect
    .poll(() => [...blockedRedirectGuardProbes])
    .toEqual([`https://${redirectGuardProbeHost}/redirect-probe`]);

  const prompt = "Prepare a credential-free browser acceptance result";
  await page.getByLabel("Task", { exact: true }).fill(prompt);

  const createResponse = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      response.url() === "http://127.0.0.1:3000/api/v1/tasks",
  );
  await page.getByRole("button", { name: "Dispatch" }).click();
  expect((await createResponse).status()).toBe(202);

  await expect(page).toHaveURL(/\/tasks\/task_[0-9]{8}$/);
  const taskHeader = page.getByRole("heading", { level: 1 }).locator("..");
  await expect(taskHeader.getByText("Needs review", { exact: true })).toBeVisible();
  await expect(page.getByText("Safe local fixture plan", { exact: true }).first()).toBeVisible();

  await page.getByRole("button", { name: "Edit plan" }).click();
  await page.getByLabel("Plan step 2").fill("Execute the reviewed plan through the bounded API.");
  await page.getByRole("button", { name: "Save plan" }).click();

  const batch = page.getByRole("region", { name: "Ordered approval batch" });
  await expect(batch.getByText("approval version 2", { exact: true })).toBeVisible();
  await expect(batch.getByText("Execute the reviewed plan through the bounded API.")).toBeVisible();
  await expect(batch.getByText("execute_plan_step", { exact: true })).toHaveCount(3);
  await batch
    .getByRole("listitem")
    .nth(0)
    .getByRole("button", { name: "Approve", exact: true })
    .click();
  const secondAction = batch.getByRole("listitem").nth(1);
  await secondAction.getByRole("button", { name: "Edit", exact: true }).click();
  await secondAction
    .getByLabel("Edited step text for action 2 · execute_plan_step")
    .fill("Execute the approved plan and verify the hosted-ready result.");
  await batch
    .getByRole("listitem")
    .nth(2)
    .getByRole("button", { name: "Approve", exact: true })
    .click();
  await expect(batch.getByText(/2 approve · 1 edit/)).toBeVisible();

  const decisionResponse = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      /\/api\/v1\/tasks\/task_[0-9]{8}\/decision-batch$/.test(response.url()),
  );
  await batch.getByRole("button", { name: "Submit reviewed batch" }).click();
  expect((await decisionResponse).status()).toBe(202);

  await expect(taskHeader.getByText("Running", { exact: true })).toBeVisible();
  await expect(page.getByText(/Agent is working/)).toBeVisible();
  await expect(taskHeader.getByText("Done", { exact: true })).toBeVisible();
  await expect(page.getByText("Run completed", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: prompt, exact: true })).toBeVisible();
  await expect(page.getByText(/hosted-ready result/).first()).toBeVisible();

  // The completed result must be exportable: the user can take the deep-work
  // output out of the app. Assert the controls render and that "Copy brief"
  // actually copies the Markdown brief (prompt + result + evidence) to the OS
  // clipboard.
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await expect(page.getByRole("button", { name: "Copy", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Download" })).toBeVisible();
  const copyBrief = page.getByRole("button", { name: "Copy brief" });
  await expect(copyBrief).toBeVisible();
  await copyBrief.click();
  await expect(page.getByRole("button", { name: "Copied" })).toBeVisible();
  const clipboardBrief = await page.evaluate(() => navigator.clipboard.readText());
  expect(clipboardBrief).toContain("## Result");
  expect(clipboardBrief).toContain(prompt);

  // "Edit & re-run" opens the composer to revise the objective before a fresh
  // dispatch; it ships alongside the one-click "Run again".
  await expect(page.getByRole("button", { name: "Edit & re-run" })).toBeVisible();

  // Inspection is part of the outcome, not a decorative panel. Sources,
  // portable task files, and the exact local/external trace state all remain
  // attached to the same completed task.
  await page.getByRole("tab", { name: "Sources" }).click();
  await expect(page.getByText("local-runner", { exact: false })).toBeVisible();
  await page.getByRole("tab", { name: "Files" }).click();
  await expect(page.getByText("result.md", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: /Download evidence-/ }).first()).toBeVisible();
  await page.getByRole("tab", { name: "Details" }).click();
  await expect(page.getByText("Execution trace", { exact: true })).toBeVisible();
  await expect(page.getByText("Retained events", { exact: true })).toBeVisible();

  // Return to the inbox and reopen this exact retained task before exercising
  // re-dispatch. The result and inspection views must survive route changes.
  const completedUrl = new URL(page.url());
  await page.getByRole("link", { name: "All tasks" }).click();
  await expect(page).toHaveURL(/\/tasks$/);
  await page.locator(`a[href="${completedUrl.pathname}"]`).first().click();
  await expect(page).toHaveURL(new RegExp(`${completedUrl.pathname}$`));
  await expect(page.getByText("Run completed", { exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "Files" }).click();
  await expect(page.getByText("result.md", { exact: true })).toBeVisible();

  // Re-dispatch: "Run again" creates a fresh task from the same prompt and
  // navigates to it. Wait for the POST and for the URL to change to a
  // *different* task id (the completed task already matches the id pattern).
  const reopenedUrl = page.url();
  const rerunResponse = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      response.url() === "http://127.0.0.1:3000/api/v1/tasks",
  );
  await page.getByRole("button", { name: "Run again" }).click();
  expect((await rerunResponse).status()).toBe(202);
  await page.waitForURL(
    (url) => /\/tasks\/task_[0-9]{8}$/.test(url.pathname) && url.href !== reopenedUrl,
  );
  await expect(taskHeader.getByText("Needs review", { exact: true })).toBeVisible();

  expect([...unexpectedEgress]).toEqual([]);
  expect(pageErrors).toEqual([]);
});

test("checks a classic source without saving or accepting browser credentials", async ({
  page,
}) => {
  await page.goto("/settings/runtime");
  await expect(page.getByRole("heading", { name: "Runtime" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Check a source" })).toBeVisible();

  await page.getByLabel("Assistant ID").fill("assistant-1");
  const unavailableResponse = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      response.url() === "http://127.0.0.1:3000/api/v1/sources/probes",
  );
  await page.getByRole("button", { name: "Run read-only check" }).click();
  const unavailable = await unavailableResponse;
  expect(unavailable.status()).toBe(503);
  expect(unavailable.request().postDataJSON()).toEqual({
    kind: "langsmith_deployment",
    sourceTargetId: "classic-default",
    assistantId: "assistant-1",
  });
  expect(unavailable.request().postData()?.toLowerCase()).not.toContain("credential");
  await expect(
    page.getByText("No server-held source credential is configured for connection checks."),
  ).toBeVisible();

  let qualifiedRequests = 0;
  let releaseQualifiedRequest: (() => void) | undefined;
  const qualifiedRequestHeld = new Promise<void>((resolve) => {
    releaseQualifiedRequest = resolve;
  });
  await page.route("**/api/v1/sources/probes", async (route) => {
    qualifiedRequests += 1;
    await qualifiedRequestHeld;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        kind: "langsmith_deployment",
        state: "available",
        assistantId: "assistant-1",
        graphId: "deep-work",
        reason: "assistant-qualified-read-only",
        saveAllowed: false,
        capabilities: [
          {
            name: "assistants-read",
            state: "available",
            observedAt: "2026-08-04T00:00:00.000Z",
            adapterVersion: "classic-source-probe-v1",
            contractVersion: "langgraph-assistants-get-v1",
            evidenceClass: "live-contract",
          },
          {
            name: "runs-create",
            state: "gated",
            safeReason: "adapter-disabled",
            observedAt: "2026-08-04T00:00:00.000Z",
            adapterVersion: "classic-source-probe-v1",
            contractVersion: "langgraph-assistants-get-v1",
            evidenceClass: "documented",
          },
        ],
      }),
    });
  });
  const probeForm = page
    .getByRole("button", { name: "Run read-only check" })
    .locator("xpath=ancestor::form");
  await probeForm.evaluate((form: HTMLFormElement) => {
    form.requestSubmit();
    form.requestSubmit();
  });
  await expect.poll(() => qualifiedRequests).toBe(1);
  releaseQualifiedRequest?.();

  const result = page.getByLabel("Source check result");
  await expect(result.getByText("Assistant found", { exact: true })).toBeVisible();
  await expect(result.getByText("assistant-1 · graph deep-work", { exact: false })).toBeVisible();
  await expect(result.getByText("assistants-read", { exact: true })).toBeVisible();
  await expect(result.getByText("runs-create", { exact: true })).toBeVisible();
  await expect(result.getByText("adapter-disabled", { exact: true })).toBeVisible();
  await expect(result.getByText(/Saving and selecting this source stay blocked/)).toBeVisible();
  await expect(page.getByRole("button", { name: /save/i })).toHaveCount(0);

  await page.getByLabel("Assistant ID").fill("assistant-2");
  await expect(result).toHaveCount(0);
});
