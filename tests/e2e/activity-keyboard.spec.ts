import { expect, test } from "@playwright/test";

// The activity timeline supports mouse-free review: j/k move a highlight over
// the entries and Enter opens the focused entry's task. This covers the
// keyboard-open path end to end against the credential-free local API.
test("opens a task from the activity feed by keyboard", async ({ page }) => {
  const prompt = "Keyboard navigation acceptance for activity";

  await page.goto("/tasks/new");
  await expect(page.getByRole("heading", { name: "New task" })).toBeVisible();
  await page.getByLabel("Task", { exact: true }).fill(prompt);
  await page.getByRole("button", { name: "Dispatch" }).click();
  await expect(page).toHaveURL(/\/tasks\/task_[0-9]{8}$/);

  // The dispatched task's status lands on the timeline.
  await page.goto("/activity");
  await expect(page.getByRole("heading", { name: "Activity" })).toBeVisible();
  await expect(page.getByRole("list", { name: "Activity timeline" })).toBeVisible();

  // Move focus off the heading, then drive the timeline with the keyboard:
  // j highlights the first entry, Enter opens its task.
  await page.getByRole("heading", { name: "Activity" }).click();
  await page.keyboard.press("j");
  await expect(page.locator('li[aria-current="true"]')).toBeVisible();
  await page.keyboard.press("Enter");

  await page.waitForURL(/\/tasks\/task_[0-9]{8}$/);
});
