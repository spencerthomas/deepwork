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
  // j highlights the first entry and moves real DOM focus to its row.
  await page.getByRole("heading", { name: "Activity" }).click();
  await page.keyboard.press("j");
  const focusedRow = page.locator('li[aria-current="true"]');
  await expect(focusedRow).toBeFocused();

  // Enter opens exactly the task the highlighted row points at — read the row's
  // own link so the assertion holds under a shared server where another spec's
  // task may be the newest entry.
  const focusedTaskPath = await focusedRow.getByRole("link").getAttribute("href");
  expect(focusedTaskPath).toMatch(/^\/tasks\/task_[0-9]{8}$/);
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(new RegExp(`${focusedTaskPath}$`));
});
