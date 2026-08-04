#!/usr/bin/env node

import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import { dirname } from "node:path";

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
  await page.getByLabel("Workspace access key").fill(accessKey);
  await page.getByRole("button", { name: "Connect workspace" }).click();
  await page.waitForURL(`${origin}/tasks`);
}

async function completeJourney(browser, config) {
  const context = await browser.newContext({
    baseURL: config.origin,
    viewport: { width: 1440, height: 900 },
    serviceWorkers: "block",
  });
  const page = await context.newPage();
  const pageErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
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
  await page.getByText("Run completed", { exact: true }).waitFor({ timeout: 20_000 });
  await page.getByRole("tab", { name: "Sources" }).click();
  await page.getByText("local-runner", { exact: false }).waitFor();
  await page.getByRole("tab", { name: "Files" }).click();
  await page.getByText("result.md", { exact: true }).waitFor();
  await page.getByRole("tab", { name: "Details" }).click();
  await page.getByText("Execution trace", { exact: true }).waitFor();

  await page.evaluate(({ ownKey, label }) => localStorage.setItem(ownKey, `owned-by-${label}`), {
    ownKey: config.ownStorageKey,
    label: config.label,
  });
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

  const phone = await browser.newContext({
    baseURL: config.origin,
    viewport: { width: 390, height: 844 },
    serviceWorkers: "block",
  });
  const phonePage = await phone.newPage();
  await login(phonePage, config.origin, config.accessKey);
  await phonePage.goto(taskUrl);
  await phonePage.getByText("Run completed", { exact: true }).waitFor();
  await phonePage.getByRole("tab", { name: "Files" }).click();
  await phonePage.getByText("result.md", { exact: true }).waitFor();
  await phonePage.screenshot({
    path: `${config.artifactDir}/phone-reopened.png`,
    fullPage: true,
  });
  await phone.close();
  await context.close();
  if (pageErrors.length > 0)
    throw new Error(`${config.label} page errors: ${pageErrors.join("; ")}`);
  return {
    label: config.label,
    taskPath: new URL(taskUrl).pathname,
    prompt,
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
    viewport: { width: 390, height: 844 },
    serviceWorkers: "block",
  });
  const page = await context.newPage();
  await login(page, config.origin, config.accessKey);
  await page.goto(`${config.origin}${config.taskPath}`);
  await page.getByText("Run completed", { exact: true }).waitFor();
  await page.getByRole("tab", { name: "Files" }).click();
  await page.getByText("result.md", { exact: true }).waitFor();
  await page.screenshot({ path: config.screenshot, fullPage: true });
  await context.close();
  return { label: config.label, taskPath: config.taskPath, reopenedAfterApiRestart: true };
}

const args = parseArgs(process.argv.slice(2));
await mkdir(dirname(args.report), { recursive: true });
const browser = await chromium.launch({ headless: true });
try {
  if (args["reopen-a"] && args["reopen-b"]) {
    const reopened = await Promise.all([
      reopenJourney(browser, {
        label: "stack-a",
        origin: args["origin-a"],
        accessKey: "deepwork-product-demo-a",
        taskPath: args["reopen-a"],
        screenshot: `${dirname(args.report)}/stack-a/reopened-after-api-restart.png`,
      }),
      reopenJourney(browser, {
        label: "stack-b",
        origin: args["origin-b"],
        accessKey: "deepwork-product-demo-b",
        taskPath: args["reopen-b"],
        screenshot: `${dirname(args.report)}/stack-b/reopened-after-api-restart.png`,
      }),
    ]);
    await writeFile(args.report, `${JSON.stringify({ schemaVersion: 1, reopened }, null, 2)}\n`, {
      mode: 0o600,
    });
  } else {
    const [a, b] = await Promise.all([
      completeJourney(browser, {
        label: "stack-a",
        origin: args["origin-a"],
        accessKey: "deepwork-product-demo-a",
        ownStorageKey: args["storage-a"],
        peerStorageKey: args["storage-b"],
        artifactDir: `${dirname(args.report)}/stack-a`,
      }),
      completeJourney(browser, {
        label: "stack-b",
        origin: args["origin-b"],
        accessKey: "deepwork-product-demo-b",
        ownStorageKey: args["storage-b"],
        peerStorageKey: args["storage-a"],
        artifactDir: `${dirname(args.report)}/stack-b`,
      }),
    ]);
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
