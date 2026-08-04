#!/usr/bin/env node

import { chromium } from "@playwright/test";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";

const POLICY_PROBE_PREFIX = "/__deepwork_policy_probe";

async function captureScreenshot(page, screenshots, relativePath) {
  const viewport = page.viewportSize();
  const phone = viewport !== null && viewport.width <= 390;
  if (phone) {
    await page.getByText("result.md", { exact: true }).scrollIntoViewIfNeeded();
    const layout = await page.evaluate(() => {
      const navigations = [...document.querySelectorAll('nav[aria-label="Primary navigation"]')];
      const visibleNavigation = navigations.find((element) => {
        const style = window.getComputedStyle(element);
        return style.display !== "none" && style.visibility !== "hidden";
      });
      const navigation = visibleNavigation?.getBoundingClientRect();
      const header = document.querySelector("header")?.getBoundingClientRect();
      return {
        headerBottom: header?.bottom,
        headerTop: header?.top,
        navigationBottom: navigation?.bottom,
        navigationTop: navigation?.top,
        scrollWidth: document.documentElement.scrollWidth,
        viewportHeight: window.innerHeight,
        viewportWidth: window.innerWidth,
      };
    });
    if (
      layout.scrollWidth > layout.viewportWidth ||
      layout.headerTop === undefined ||
      layout.headerTop < -1 ||
      layout.headerBottom === undefined ||
      layout.headerBottom > layout.viewportHeight ||
      layout.navigationTop === undefined ||
      layout.navigationTop < 0 ||
      layout.navigationBottom === undefined ||
      Math.abs(layout.navigationBottom - layout.viewportHeight) > 1
    ) {
      throw new Error(`phone shell overlaps or overflows its viewport: ${JSON.stringify(layout)}`);
    }
  }
  const buffer = await page.screenshot({ fullPage: !phone });
  screenshots[relativePath] = buffer.toString("base64");
}

function sanitizedRequest(request) {
  const url = new URL(request.url());
  return { method: request.method(), path: url.pathname, resourceType: request.resourceType() };
}

async function createIsolatedContext(browser, { origin, viewport }) {
  const context = await browser.newContext({
    baseURL: origin,
    viewport,
    serviceWorkers: "block",
  });
  const networkPolicyViolations = [];
  const blockedNetworkProbes = [];
  await context.route("**/*", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (["http:", "https:"].includes(url.protocol) && url.origin !== origin) {
      const record = sanitizedRequest(request);
      if (url.pathname.startsWith(POLICY_PROBE_PREFIX)) blockedNetworkProbes.push(record);
      else networkPolicyViolations.push(record);
      await route.abort("blockedbyclient");
      return;
    }
    await route.continue();
  });
  if (typeof context.routeWebSocket === "function") {
    await context.routeWebSocket("**/*", (socket) => {
      const url = new URL(socket.url());
      if (url.origin !== origin.replace(/^http/, "ws")) {
        const record = { method: "WEBSOCKET", path: url.pathname, resourceType: "websocket" };
        if (url.pathname.startsWith(POLICY_PROBE_PREFIX)) blockedNetworkProbes.push(record);
        else networkPolicyViolations.push(record);
        socket.close({ code: 1008, reason: "blocked by product-demo origin policy" });
      } else {
        socket.connectToServer();
      }
    });
  }
  return { context, networkPolicyViolations, blockedNetworkProbes };
}

function monitorPage(page, label, origin, networkPolicy) {
  const failures = [];
  const navigationAborts = [];
  const policyProbeConsoleErrors = [];
  page.on("pageerror", (error) => failures.push(`pageerror: ${error.message}`));
  page.on("console", (message) => {
    if (message.type() !== "error") return;
    const text = message.text();
    if (text === "Failed to load resource: net::ERR_BLOCKED_BY_CLIENT.Inspector") {
      policyProbeConsoleErrors.push(text);
    } else {
      failures.push(`console: ${text}`);
    }
  });
  page.on("requestfailed", (request) => {
    const reason = request.failure()?.errorText ?? "unknown";
    // Next can abort an in-flight route-handler request after its client router
    // has already completed the authenticated navigation. The destination URL
    // and rendered state are asserted by login(); retain that classification
    // separately while still failing every other network error.
    const record = sanitizedRequest(request);
    if (record.path.startsWith(POLICY_PROBE_PREFIX)) return;
    if (
      reason === "net::ERR_ABORTED" &&
      ((record.method === "POST" && record.path === "/api/v1/auth/login") ||
        (record.method === "GET" && /^\/api\/v1\/tasks\/task_[0-9]{8}\/events$/.test(record.path)))
    ) {
      navigationAborts.push(record);
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
    const expectedPolicyConsoleErrors = networkPolicy.blockedNetworkProbes.filter(
      (record) => record.resourceType !== "websocket",
    ).length;
    if (policyProbeConsoleErrors.length !== expectedPolicyConsoleErrors) {
      failures.push(
        `policy-probe-console: expected ${expectedPolicyConsoleErrors}, observed ${policyProbeConsoleErrors.length}`,
      );
    }
    if (networkPolicy.networkPolicyViolations.length > 0) {
      failures.push(`network-policy: ${JSON.stringify(networkPolicy.networkPolicyViolations)}`);
    }
    if (failures.length > 0) throw new Error(`${label} browser failures: ${failures.join("; ")}`);
    return {
      blockedNetworkProbes: networkPolicy.blockedNetworkProbes,
      browserErrors: 0,
      classifiedNavigationAborts: navigationAborts,
    };
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
  const downloadPath = await download.path();
  if (!downloadPath || !download.suggestedFilename().endsWith(".md")) {
    throw new Error("portable result download was not produced");
  }
  const exportedBrief = await readFile(downloadPath, "utf8");
  if (
    !exportedBrief.includes(prompt) ||
    !exportedBrief.includes("## Result") ||
    !exportedBrief.includes(`Objective: ${prompt}`) ||
    !exportedBrief.includes("local-runner")
  ) {
    throw new Error("portable result download is not bound to prompt, result, and evidence");
  }
  return {
    resultText,
    exportedBriefSha256: createHash("sha256").update(exportedBrief).digest("hex"),
  };
}

async function downloadText(page, locator) {
  const downloadPromise = page.waitForEvent("download");
  await locator.click();
  const download = await downloadPromise;
  const path = await download.path();
  if (!path) throw new Error("retained file download was not produced");
  return readFile(path, "utf8");
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

async function proveNetworkPolicy(page, peerOrigin, networkPolicy) {
  await page.evaluate(
    async ({ peer }) => {
      for (const url of [
        "https://example.invalid/__deepwork_policy_probe_public__",
        "http://deepwork.invalid/__deepwork_policy_probe_dns__",
        `${peer}/__deepwork_policy_probe_peer__`,
      ]) {
        await fetch(url).catch(() => undefined);
      }
      navigator.sendBeacon(
        `${peer}/__deepwork_policy_probe_beacon__`,
        new Blob(["probe"], { type: "text/plain" }),
      );
      const websocket = peer.replace(/^http/, "ws") + "/__deepwork_policy_probe_ws__";
      await new Promise((resolve) => {
        const socket = new WebSocket(websocket);
        socket.addEventListener("error", resolve, { once: true });
        socket.addEventListener("close", resolve, { once: true });
        window.setTimeout(resolve, 1_000);
      });
    },
    { peer: peerOrigin },
  );
  await page.waitForTimeout(250);
  const observed = networkPolicy.blockedNetworkProbes;
  if (observed.filter((item) => item.path.startsWith(POLICY_PROBE_PREFIX)).length !== 5) {
    throw new Error(`network policy probes were incomplete: ${JSON.stringify(observed)}`);
  }
}

async function completeJourney(browser, config) {
  const networkPolicy = await createIsolatedContext(browser, {
    origin: config.origin,
    viewport: { width: 1440, height: 900 },
  });
  const { context } = networkPolicy;
  const page = await context.newPage();
  const assertDesktopHealthy = monitorPage(
    page,
    `${config.label} desktop`,
    config.origin,
    networkPolicy,
  );
  await login(page, config.origin, config.accessKey);
  await proveNetworkPolicy(page, config.peerOrigin, networkPolicy);

  await page.goto(`${config.origin}/agents`);
  await page.getByRole("heading", { name: "Agents", exact: true }).waitFor();
  await page.goto(`${config.origin}/tasks/new`);
  await page.getByRole("heading", { name: "New task" }).waitFor();
  const agentGroup = page.getByRole("radiogroup", { name: "Choose agent" });
  const agent = agentGroup.getByRole("radio", { name: /Deep Work Planner/ });
  await agent.click();
  if ((await agent.getAttribute("aria-checked")) !== "true") {
    throw new Error("registry agent selection was not retained");
  }
  const outcome = page.getByRole("radiogroup", { name: "Choose outcome" });
  await outcome.getByRole("radio", { name: /General task/ }).click();
  const prompt = `Prepare isolated product-demo result for ${config.label}`;
  await page.getByLabel("Task", { exact: true }).fill(prompt);
  await page.getByRole("button", { name: "Dispatch" }).click();
  await page.waitForURL(/\/tasks\/task_[0-9]{8}$/);
  const taskUrl = page.url();
  await page.getByText("deepwork-fixture-planner", { exact: true }).first().waitFor();

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
  const { resultText, exportedBriefSha256 } = await assertCompletedOutcome(page, prompt);
  await page.getByRole("tab", { name: "Activity" }).click();
  await page.getByText("run.completed", { exact: true }).waitFor();
  await page.getByRole("tab", { name: "Sources" }).click();
  const sourceRecord = page.getByText("local-runner", { exact: false });
  await sourceRecord.waitFor();
  const sourceText = (await sourceRecord.locator("..").textContent()) ?? "";
  if (!sourceText.includes("deterministic local runner classified")) {
    throw new Error("source record lost its evidence summary");
  }
  await page.getByRole("tab", { name: "Files" }).click();
  await page.getByText("result.md", { exact: true }).waitFor();
  const retainedResult = await downloadText(
    page,
    page.getByRole("link", { name: "Download result.md" }),
  );
  if (
    !retainedResult.includes(prompt) ||
    !retainedResult.includes(`Objective: ${prompt}`) ||
    !retainedResult.includes("Next actions:")
  ) {
    throw new Error("retained result.md is not bound to the prompt-specific result");
  }
  const retainedEvidence = await downloadText(
    page,
    page.getByRole("link", { name: /Download evidence-evidence_/ }).first(),
  );
  const retainedEvidenceRecord = JSON.parse(retainedEvidence);
  if (
    retainedEvidenceRecord.taskId !== new URL(taskUrl).pathname.split("/").at(-1) ||
    !/^run_[0-9]{8}$/.test(String(retainedEvidenceRecord.runId ?? "")) ||
    retainedEvidenceRecord.objective !== prompt ||
    retainedEvidenceRecord.evidence?.source !== "deterministic-local-runner" ||
    !String(retainedEvidenceRecord.evidence?.summary ?? "").includes(
      "deterministic local runner classified",
    )
  ) {
    throw new Error("retained evidence JSON is not bound to this task, run, and source record");
  }
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
  await captureScreenshot(page, config.screenshots, `${config.label}/desktop-completed.png`);

  await page.goto(`${config.origin}/tasks`);
  await page
    .locator(`a[href="${new URL(taskUrl).pathname}"]`)
    .first()
    .click();
  await page.getByText("Run completed", { exact: true }).waitFor();
  await assertCompletedOutcome(page, prompt);

  const phoneNetworkPolicy = await createIsolatedContext(browser, {
    origin: config.origin,
    viewport: { width: 390, height: 844 },
  });
  const phone = phoneNetworkPolicy.context;
  const phonePage = await phone.newPage();
  const assertPhoneHealthy = monitorPage(
    phonePage,
    `${config.label} phone`,
    config.origin,
    phoneNetworkPolicy,
  );
  await login(phonePage, config.origin, config.accessKey);
  await phonePage.goto(taskUrl);
  await assertCompletedOutcome(phonePage, prompt);
  await phonePage.getByRole("tab", { name: "Files" }).click();
  await phonePage.getByText("result.md", { exact: true }).waitFor();
  await captureScreenshot(phonePage, config.screenshots, `${config.label}/phone-reopened.png`);
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
    exportedBriefSha256,
    retainedResultSha256: createHash("sha256").update(retainedResult).digest("hex"),
    retainedEvidenceSha256: createHash("sha256").update(retainedEvidence).digest("hex"),
    selectedAgentId: "deepwork-fixture-planner",
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

async function proveSharedContextStorage(browser, config) {
  const context = await browser.newContext({
    viewport: { width: 800, height: 600 },
    serviceWorkers: "block",
  });
  const allowedOrigins = new Set([config.originA, config.originB]);
  await context.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (["http:", "https:"].includes(url.protocol) && !allowedOrigins.has(url.origin)) {
      await route.abort("blockedbyclient");
      return;
    }
    await route.continue();
  });
  const page = await context.newPage();
  const cells = [
    {
      label: "stack-a",
      origin: config.originA,
      ownKey: config.storageA,
      peerKey: config.storageB,
    },
    {
      label: "stack-b",
      origin: config.originB,
      ownKey: config.storageB,
      peerKey: config.storageA,
    },
  ];
  for (const cell of cells) {
    await page.goto(`${cell.origin}/login`, { waitUntil: "domcontentloaded" });
    await page.evaluate(
      ({ key, label }) => localStorage.setItem(key, `shared-context-owned-by-${label}`),
      { key: cell.ownKey, label: cell.label },
    );
  }
  const observations = [];
  for (const cell of cells) {
    await page.goto(`${cell.origin}/login`, { waitUntil: "domcontentloaded" });
    observations.push({
      sourceLabel: cell.label,
      ownStorageObserved: await page.evaluate((key) => localStorage.getItem(key), cell.ownKey),
      peerStorageObserved: await page.evaluate((key) => localStorage.getItem(key), cell.peerKey),
    });
  }
  await context.close();
  return observations;
}

async function reopenJourney(browser, config) {
  const networkPolicy = await createIsolatedContext(browser, {
    origin: config.origin,
    viewport: config.viewport,
  });
  const context = networkPolicy.context;
  const page = await context.newPage();
  const assertHealthy = monitorPage(
    page,
    `${config.label} ${config.viewport.width}x${config.viewport.height} restart reopen`,
    config.origin,
    networkPolicy,
  );
  await login(page, config.origin, config.accessKey);
  await page.goto(`${config.origin}${config.taskPath}`);
  await assertCompletedOutcome(page, config.prompt);
  await page.getByRole("tab", { name: "Files" }).click();
  await page.getByText("result.md", { exact: true }).waitFor();
  await captureScreenshot(page, config.screenshots, config.screenshot);
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
const browser = await chromium.launch({ headless: true });
try {
  const screenshots = {};
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
            screenshots,
            screenshot: `${label}/reopened-after-api-restart-${viewport.name}.png`,
          }),
        );
      }
    }
    process.stdout.write(
      `${JSON.stringify({ report: { schemaVersion: 1, reopened }, screenshots })}\n`,
    );
  } else {
    const a = await completeJourney(browser, {
      label: "stack-a",
      origin: args["origin-a"],
      peerOrigin: args["origin-b"],
      accessKey: "deepwork-product-demo-a",
      ownStorageKey: args["storage-a"],
      peerStorageKey: args["storage-b"],
      screenshots,
    });
    const b = await completeJourney(browser, {
      label: "stack-b",
      origin: args["origin-b"],
      peerOrigin: args["origin-a"],
      accessKey: "deepwork-product-demo-b",
      ownStorageKey: args["storage-b"],
      peerStorageKey: args["storage-a"],
      screenshots,
    });
    const storageIsolation = await proveSharedContextStorage(browser, {
      originA: args["origin-a"],
      originB: args["origin-b"],
      storageA: args["storage-a"],
      storageB: args["storage-b"],
    });
    process.stdout.write(
      `${JSON.stringify({ report: { schemaVersion: 1, journeys: [a, b], storageIsolation }, screenshots })}\n`,
    );
  }
} finally {
  await browser.close();
}
