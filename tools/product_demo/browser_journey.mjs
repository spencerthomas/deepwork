#!/usr/bin/env node

import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import { dirname } from "node:path";

function monitorPage(page, label, origin) {
  const failures = [];
  const navigationAborts = [];
  page.on("pageerror", (error) => failures.push(`pageerror: ${error.message}`));
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (["http:", "https:"].includes(url.protocol) && url.hostname !== "127.0.0.1") {
      failures.push(`external-network: ${request.method()} ${url.origin}${url.pathname}`);
    }
  });
  page.on("console", (message) => {
    if (message.type() === "error") failures.push(`console: ${message.text()}`);
  });
  page.on("requestfailed", (request) => {
    const reason = request.failure()?.errorText ?? "unknown";
    // Next can abort an in-flight route-handler request after its client router
    // has already completed the authenticated navigation. The destination URL
    // and rendered state are asserted by login(); retain that classification
    // separately while still failing every other network error.
    if (reason === "net::ERR_ABORTED") {
      navigationAborts.push(`${request.method()} ${request.url()}`);
    } else {
      failures.push(`requestfailed (${reason}): ${request.method()} ${request.url()}`);
    }
  });
  page.on("response", (response) => {
    if (response.url().startsWith(`${origin}/api/`) && response.status() >= 400) {
      failures.push(`api-response: ${response.status()} ${response.url()}`);
    }
  });
  return () => {
    if (failures.length > 0) throw new Error(`${label} browser failures: ${failures.join("; ")}`);
    return { browserErrors: 0, classifiedNavigationAborts: navigationAborts.length };
  };
}

async function assertCompletedOutcome(page, prompt) {
  const resultRegion = page.getByRole("region", { name: "Task result" });
  await resultRegion.getByText("Run completed", { exact: true }).waitFor({ timeout: 20_000 });
  const resultText = (await resultRegion.textContent()) ?? "";
  if (!resultText.includes(`Objective: ${prompt}`) || !resultText.includes("Next actions:")) {
    throw new Error("completed task did not render a useful prompt-specific result");
  }
  const downloadPromise = page.waitForEvent("download");
  await resultRegion.getByRole("button", { name: "Download", exact: true }).click();
  const download = await downloadPromise;
  if (!(await download.path()) || !download.suggestedFilename().endsWith(".md")) {
    throw new Error("portable result download was not produced");
  }
  return resultText;
}

function parseArgs(argv) {
  const values = {};
  for (let index = 0; index < argv.length; index += 2) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (!flag?.startsWith("--") || value === undefined) {
      throw new Error("arguments must be --name value pairs");
    }
    values[flag.slice(2)] = value;
  }
  for (const required of ["origin-a", "origin-b", "storage-a", "storage-b", "report"]) {
    if (!values[required]) throw new Error(`missing --${required}`);
  }
  return values;
}

async function login(page, origin, accessKey) {
  await page.goto(`${origin}/login`, { waitUntil: "domcontentloaded" });
  await page.getByRole("heading", { name: "Connect to Deep Work" }).waitFor();
  const input = page.getByLabel("Workspace access key");
  const submit = page.getByRole("button", { name: "Connect workspace" });
  // The first request compiles the route in development mode. Let hydration
  // replace the server-rendered form before entering the credential.
  await page.waitForTimeout(3_000);
  await input.fill(accessKey);
  await page.waitForFunction(
    () => !(document.querySelector('button[type="submit"]')?.disabled ?? true),
    undefined,
    { timeout: 15_000 },
  );
  if (!(await submit.isEnabled())) throw new Error(`login form did not hydrate: ${origin}`);
  await submit.click();
  await page.waitForURL(`${origin}/tasks`);
}

async function completeJourney(browser, config) {
  const context = await browser.newContext({
    baseURL: config.origin,
    viewport: { width: 1440, height: 900 },
    serviceWorkers: "block",
  });
  const page = await context.newPage();
  const assertDesktopHealthy = monitorPage(page, `${config.label} desktop`, config.origin);
  await login(page, config.origin, config.accessKey);

  await page.goto(`${config.origin}/agents`);
  await page.getByRole("heading", { name: "Agents", exact: true }).waitFor();
  await page.goto(`${config.origin}/tasks/new`);
  await page.getByRole("heading", { name: "New task" }).waitFor();
  const agent = page.getByRole("radio", { name: /General task/ });
  await agent.click();
  const prompt = `Prepare isolated product-demo result for ${config.label}`;
  await page.getByLabel("Task", { exact: true }).fill(prompt);
  await page.getByRole("button", { name: "Dispatch" }).click();
  await page.waitForURL(/\/tasks\/task_[0-9]{8}$/);
  const taskUrl = page.url();

  await page.getByText("Safe local fixture plan", { exact: true }).first().waitFor();
  await page.getByRole("button", { name: "Edit plan" }).click();
  await page
    .getByLabel("Plan step 2")
    .fill("Execute the reviewed plan through the isolated API contract.");
  await page.getByRole("button", { name: "Save plan" }).click();
  const batch = page.getByRole("region", { name: "Ordered approval batch" });
  await batch.getByText("approval version 2", { exact: true }).waitFor();
  await batch
    .getByRole("listitem")
    .nth(0)
    .getByRole("button", { name: "Approve", exact: true })
    .click();
  const second = batch.getByRole("listitem").nth(1);
  await second.getByRole("button", { name: "Edit", exact: true }).click();
  await second
    .getByLabel("Edited step text for action 2 · execute_plan_step")
    .fill("Execute the approved plan and verify the isolated result.");
  await batch
    .getByRole("listitem")
    .nth(2)
    .getByRole("button", { name: "Approve", exact: true })
    .click();
  await batch.getByRole("button", { name: "Submit reviewed batch" }).click();
  await page
    .getByText("Agent is working — it pauses at the plan checkpoint for your review", {
      exact: true,
    })
    .waitFor({ timeout: 5_000 });
  const resultText = await assertCompletedOutcome(page, prompt);
  await page.getByRole("tab", { name: "Activity" }).click();
  await page.getByText("run.completed", { exact: true }).waitFor();
  await page.getByRole("tab", { name: "Sources" }).click();
  const sourceRecord = page.getByText("local-runner", { exact: false });
  await sourceRecord.waitFor();
  const sourceText = (await sourceRecord.locator("..").textContent()) ?? "";
  await page.getByRole("tab", { name: "Files" }).click();
  await page.getByText("result.md", { exact: true }).waitFor();
  await page.getByRole("tab", { name: "Details" }).click();
  await page.getByText("Execution trace", { exact: true }).waitFor();
  const retainedEventsText =
    (await page.getByText("Retained events", { exact: true }).locator("..").textContent()) ?? "";
  if (!/[1-9][0-9]*/.test(retainedEventsText)) {
    throw new Error("execution trace did not retain any events");
  }

  await page.evaluate(({ ownKey, label }) => localStorage.setItem(ownKey, `owned-by-${label}`), {
    ownKey: config.ownStorageKey,
    label: config.label,
  });
  const ownStorageObserved = await page.evaluate(
    (ownKey) => localStorage.getItem(ownKey),
    config.ownStorageKey,
  );
  const peerStorageObserved = await page.evaluate(
    (peerKey) => localStorage.getItem(peerKey),
    config.peerStorageKey,
  );
  await mkdir(config.artifactDir, { recursive: true });
  await page.screenshot({
    path: `${config.artifactDir}/desktop-completed.png`,
    fullPage: true,
  });

  await page.goto(`${config.origin}/tasks`);
  await page
    .locator(`a[href="${new URL(taskUrl).pathname}"]`)
    .first()
    .click();
  await page.getByText("Run completed", { exact: true }).waitFor();
  await assertCompletedOutcome(page, prompt);

  const phone = await browser.newContext({
    baseURL: config.origin,
    viewport: { width: 390, height: 844 },
    serviceWorkers: "block",
  });
  const phonePage = await phone.newPage();
  const assertPhoneHealthy = monitorPage(phonePage, `${config.label} phone`, config.origin);
  await login(phonePage, config.origin, config.accessKey);
  await phonePage.goto(taskUrl);
  await assertCompletedOutcome(phonePage, prompt);
  await phonePage.getByRole("tab", { name: "Files" }).click();
  await phonePage.getByText("result.md", { exact: true }).waitFor();
  await phonePage.screenshot({
    path: `${config.artifactDir}/phone-reopened.png`,
    fullPage: true,
  });
  const phoneDiagnostics = assertPhoneHealthy();
  await phone.close();
  const desktopDiagnostics = assertDesktopHealthy();
  await context.close();
  return {
    label: config.label,
    taskPath: new URL(taskUrl).pathname,
    prompt,
    resultText,
    sourceText,
    retainedEventsText,
    portableDownload: true,
    liveProgressObserved: true,
    diagnostics: { desktop: desktopDiagnostics, phone: phoneDiagnostics },
    ownStorageObserved,
    peerStorageObserved,
    states: [
      "sign-in",
      "agent-choice",
      "compose",
      "plan-review",
      "approved",
      "running",
      "result",
      "evidence-files-trace",
      "reopened",
    ],
    viewports: ["1440x900", "390x844"],
  };
}

async function reopenJourney(browser, config) {
  const context = await browser.newContext({
    baseURL: config.origin,
    viewport: config.viewport,
    serviceWorkers: "block",
  });
  const page = await context.newPage();
  const assertHealthy = monitorPage(
    page,
    `${config.label} ${config.viewport.width}x${config.viewport.height} restart reopen`,
    config.origin,
  );
  await login(page, config.origin, config.accessKey);
  await page.goto(`${config.origin}${config.taskPath}`);
  await assertCompletedOutcome(page, config.prompt);
  await page.getByRole("tab", { name: "Files" }).click();
  await page.getByText("result.md", { exact: true }).waitFor();
  await page.screenshot({ path: config.screenshot, fullPage: true });
  const diagnostics = assertHealthy();
  await context.close();
  return {
    label: config.label,
    taskPath: config.taskPath,
    viewport: `${config.viewport.width}x${config.viewport.height}`,
    reopenedAfterApiRestart: true,
    diagnostics,
  };
}

const args = parseArgs(process.argv.slice(2));
await mkdir(dirname(args.report), { recursive: true });
const browser = await chromium.launch({ headless: true });
try {
  if (args["reopen-a"] && args["reopen-b"]) {
    const reopened = [];
    for (const [label, origin, accessKey, taskPath] of [
      ["stack-a", args["origin-a"], "deepwork-product-demo-a", args["reopen-a"]],
      ["stack-b", args["origin-b"], "deepwork-product-demo-b", args["reopen-b"]],
    ]) {
      for (const viewport of [
        { width: 1440, height: 900, name: "desktop" },
        { width: 390, height: 844, name: "phone" },
      ]) {
        reopened.push(
          await reopenJourney(browser, {
            label,
            origin,
            accessKey,
            taskPath,
            prompt: `Prepare isolated product-demo result for ${label}`,
            viewport,
            screenshot: `${dirname(args.report)}/${label}/reopened-after-api-restart-${viewport.name}.png`,
          }),
        );
      }
    }
    await writeFile(args.report, `${JSON.stringify({ schemaVersion: 1, reopened }, null, 2)}\n`, {
      mode: 0o600,
    });
  } else {
    const a = await completeJourney(browser, {
      label: "stack-a",
      origin: args["origin-a"],
      accessKey: "deepwork-product-demo-a",
      ownStorageKey: args["storage-a"],
      peerStorageKey: args["storage-b"],
      artifactDir: `${dirname(args.report)}/stack-a`,
    });
    const b = await completeJourney(browser, {
      label: "stack-b",
      origin: args["origin-b"],
      accessKey: "deepwork-product-demo-b",
      ownStorageKey: args["storage-b"],
      peerStorageKey: args["storage-a"],
      artifactDir: `${dirname(args.report)}/stack-b`,
    });
    await writeFile(
      args.report,
      `${JSON.stringify({ schemaVersion: 1, journeys: [a, b] }, null, 2)}\n`,
      {
        mode: 0o600,
      },
    );
  }
} finally {
  await browser.close();
}
