import { AxeBuilder } from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

// WCAG 2.2 Level A and AA is the repository acceptance bar (AGENTS.md) for
// E2E-V1-08-RESPONSIVE-ACCESS; the older-version tags stay listed so every
// applicable success criterion, including 2.2-only rules, is executed.
const WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22a", "wcag22aa"];

// Every primary destination plus the utility settings route. The task detail and
// its approval card are exercised separately because they only exist after a run.
const SURFACES = [
  "/tasks",
  "/tasks/new",
  "/approvals",
  "/agents",
  "/schedules",
  "/activity",
  "/settings",
];

/**
 * Keep the audited page loopback-only. axe runs entirely in the browser from the
 * bundled axe-core source, so blocking egress cannot break the scan; it only
 * guarantees the rendered DOM is the application's own, never a third party's.
 */
async function blockNonLoopbackEgress(page: Page): Promise<void> {
  await page.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    const external =
      (url.protocol === "http:" || url.protocol === "https:") && url.hostname !== "127.0.0.1";
    if (external) {
      await route.abort();
      return;
    }
    await route.continue();
  });
}

async function expectNoViolations(page: Page, label: string): Promise<void> {
  // Park the cursor on inert chrome so a leftover :hover state from a prior
  // click cannot make the audit depend on pointer position.
  await page.mouse.move(2, 2);
  const results = await new AxeBuilder({ page })
    .withTags(WCAG_TAGS)
    // The Next.js dev server injects its own tooling overlay; it is not part of
    // the shipped application surface, so it is out of scope for this audit.
    .exclude("nextjs-portal")
    .analyze();
  const summary = results.violations
    .map(
      (violation) =>
        `  • ${violation.id} [${violation.impact ?? "n/a"}] ${violation.help}\n` +
        violation.nodes.map((node) => `      ${node.target.join(" ")}`).join("\n"),
    )
    .join("\n");
  expect(results.violations, `Accessibility violations on ${label}:\n${summary}`).toEqual([]);
}

async function auditSurfaces(page: Page): Promise<void> {
  for (const path of SURFACES) {
    await page.goto(path);
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("heading").first()).toBeVisible();
    await expectNoViolations(page, path);
  }
}

/**
 * Drive one bounded run to its highest-risk interactive states — the pending
 * approval card and the completed result — and audit each. Uses only role/text
 * signals so it holds for both the loopback API runner and the fixture runner.
 */
async function auditTaskJourney(page: Page): Promise<void> {
  await page.goto("/tasks/new");
  await expect(page.getByRole("heading", { name: "New task" })).toBeVisible();

  await page.getByLabel("Task", { exact: true }).fill("Audit an accessible task journey");
  await page.getByRole("button", { name: "Dispatch" }).click();
  await expect(page).toHaveURL(/\/tasks\/[^/]+$/);

  const header = page.getByRole("heading", { level: 1 }).locator("..");
  await expect(header.getByText("Needs review", { exact: true })).toBeVisible();
  await expectNoViolations(page, "task detail (needs review + approval card)");

  await page.getByRole("button", { name: "Approve", exact: true }).click();
  await expect(header.getByText("Done", { exact: true })).toBeVisible();
  await expectNoViolations(page, "task detail (completed)");
}

test.describe("accessibility — WCAG 2.1 A/AA", () => {
  test("light theme is clean across every surface and the task journey", async ({ page }) => {
    await blockNonLoopbackEgress(page);
    await auditSurfaces(page);
    await auditTaskJourney(page);
  });

  test("dark theme is clean across every surface and the task journey", async ({ page }) => {
    await blockNonLoopbackEgress(page);
    await page.addInitScript(() => window.localStorage.setItem("dw-theme", "dark"));
    await page.goto("/tasks");
    await expect
      .poll(() => page.evaluate(() => document.documentElement.classList.contains("dark")))
      .toBe(true);
    await auditSurfaces(page);
    await auditTaskJourney(page);
  });
});
