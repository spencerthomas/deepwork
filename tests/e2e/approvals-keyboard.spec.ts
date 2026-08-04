import { expect, test } from "@playwright/test";

// Ordered batches must never inherit the legacy one-key bulk-decision behavior.
test("keyboard shortcut opens an ordered review and still requires every action", async ({
  page,
}) => {
  const prompt = "Keyboard triage acceptance for approvals";

  await page.goto("/tasks/new");
  await expect(page.getByRole("heading", { name: "New task" })).toBeVisible();
  await page.getByLabel("Task", { exact: true }).fill(prompt);
  await page.getByRole("button", { name: "Dispatch" }).click();
  await expect(page).toHaveURL(/\/tasks\/task_[0-9]{8}$/);

  await page.goto("/approvals");
  await expect(page.getByRole("heading", { name: "Approvals" })).toBeVisible();
  // At least one request is pending (the one just dispatched) with its panel loaded.
  const row = page.getByRole("list", { name: "Pending approvals" }).getByRole("listitem").first();
  const submit = row.getByRole("button", { name: "Submit reviewed batch" });
  await expect(row.getByRole("button", { name: "Approve", exact: true })).toHaveCount(3);
  await expect(submit).toBeDisabled();

  // The legacy approve shortcut focuses the first positional choice; it does
  // not silently approve the full vector.
  await page.getByRole("heading", { name: "Approvals" }).click();
  await page.keyboard.press("j");
  await page.keyboard.press("a");
  const approveButtons = row.getByRole("button", { name: "Approve", exact: true });
  await expect(approveButtons.nth(0)).toBeFocused();
  await expect(submit).toBeDisabled();
  await page.keyboard.press("Space");
  await approveButtons.nth(1).click();
  await approveButtons.nth(2).click();
  await expect(submit).toBeEnabled();
  await submit.click();

  await expect(page.getByText("Approval recorded")).toBeVisible();
});
