import { expect, test } from "@playwright/test";

test("waits for the API agent registry before enabling a coding review", async ({ page }) => {
  let releaseRegistry!: () => void;
  let markRegistryRequested!: () => void;
  const registryRequested = new Promise<void>((resolve) => {
    markRegistryRequested = resolve;
  });
  const registryRelease = new Promise<void>((resolve) => {
    releaseRegistry = resolve;
  });
  let codingCreateRequests = 0;

  await page.route("**/api/v1/agents", async (route) => {
    markRegistryRequested();
    await registryRelease;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ available: false, items: [] }),
    });
  });
  page.on("request", (request) => {
    if (
      request.method() === "POST" &&
      request.url() === "http://127.0.0.1:3000/api/v1/tasks" &&
      request.postDataJSON()?.journey === "coding"
    ) {
      codingCreateRequests += 1;
    }
  });

  await page.goto("/tasks/new");
  await registryRequested;

  const codingReview = page.getByRole("radio", { name: /Coding review/ });
  const dispatch = page.getByRole("button", { name: "Dispatch" });
  await page.getByLabel("Task", { exact: true }).fill("Fix the bounded registry race");
  await expect(codingReview).toBeDisabled();
  await expect(codingReview).not.toBeChecked();
  await expect(dispatch).toBeDisabled();
  await codingReview.evaluate((element) => (element as HTMLButtonElement).click());
  await expect(codingReview).not.toBeChecked();
  expect(codingCreateRequests).toBe(0);

  releaseRegistry();
  await expect(codingReview).toBeEnabled();
  await codingReview.click();
  await expect(codingReview).toBeChecked();

  const createResponse = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      response.url() === "http://127.0.0.1:3000/api/v1/tasks",
  );
  await dispatch.click();
  const response = await createResponse;
  expect(response.request().postDataJSON()).toMatchObject({ journey: "coding" });
  expect(response.status()).toBe(202);
  await expect(page).toHaveURL(/\/tasks\/task_[0-9]{8}$/);
});

test("completes the truthful coding-to-draft-PR review journey on a phone", async ({
  context,
  page,
}) => {
  await context.clearCookies();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/login");
  await page.getByLabel("Workspace access key").fill("deepwork-local-browser-acceptance");
  await page.getByRole("button", { name: "Connect workspace" }).click();
  await expect(page).toHaveURL(/\/tasks$/);

  await page.goto("/tasks/new");
  await page.getByRole("radio", { name: /Coding review/ }).click();
  await expect(page.getByText("deepwork-fixtures/sample-app", { exact: true })).toBeVisible();
  await expect(page.getByText(/no GitHub token or external request/i)).toBeVisible();

  const prompt = "Fix the bounded session refresh regression";
  await page.getByLabel("Task", { exact: true }).fill(prompt);
  const createResponse = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      response.url() === "http://127.0.0.1:3000/api/v1/tasks",
  );
  await page.getByRole("button", { name: "Dispatch" }).click();
  const response = await createResponse;
  expect(response.request().postDataJSON()).toMatchObject({ journey: "coding" });
  expect(response.status()).toBe(202);
  await expect(page).toHaveURL(/\/tasks\/task_[0-9]{8}$/);

  const batch = page.getByRole("region", { name: "Ordered approval batch" });
  await expect(batch).toBeVisible();
  for (const action of await batch.getByRole("listitem").all()) {
    await action.getByRole("button", { name: "Approve", exact: true }).click();
  }
  await batch.getByRole("button", { name: "Submit reviewed batch" }).click();
  await expect(page.getByText("Done", { exact: true }).first()).toBeVisible();

  await page.getByRole("tab", { name: "Changes" }).click();
  const review = page.getByTestId("coding-review");
  await expect(review.getByText("deepwork-fixtures/sample-app", { exact: true })).toBeVisible();
  await expect(review.getByText("5d8f2de17703cb32fc4c6f6d7af0258ddf5f0f17")).toBeVisible();
  await expect(review.getByText("bb525814d85c6e2e35233d703e0a4069dd625d75")).toBeVisible();
  await expect(review.getByText("src/session.ts", { exact: true })).toBeVisible();
  await expect(review.getByText("tests/session.test.ts", { exact: true })).toBeVisible();
  await expect(review.getByText("Draft PR #17", { exact: true })).toBeVisible();
  await expect(review.getByText(/Reconciled after a simulated timeout/)).toBeVisible();
  await expect(
    review.getByText(/deterministic fixture evidence, not authoritative GitHub CI/),
  ).toBeVisible();
  await expect(review.getByRole("button", { name: "Merge unavailable" })).toBeDisabled();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
    ),
  ).toBe(true);

  const completedPath = new URL(page.url()).pathname;
  // The Next.js dev-tools launcher overlaps the left edge of this phone target.
  // Tap the unobscured side of the full-width navigation link.
  await page.getByRole("link", { name: "Tasks", exact: true }).click({
    position: { x: 70, y: 24 },
  });
  await page.locator(`a[href="${completedPath}"]`).first().click();
  await page.getByRole("tab", { name: "Changes" }).click();
  await expect(page.getByTestId("coding-review").getByText("Draft PR #17")).toBeVisible();
});
