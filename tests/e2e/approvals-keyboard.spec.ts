import { expect, test } from "@playwright/test";

// The approvals queue supports mouse-free triage: j/k move a highlight, and
// a/r approve/reject the focused request. This covers the keyboard-approve path
// end to end against the credential-free local API.
test("approves a pending request from the approvals queue by keyboard", async ({ page }) => {
  const prompt = "Keyboard triage acceptance for approvals";

  await page.goto("/tasks/new");
  await expect(page.getByRole("heading", { name: "New task" })).toBeVisible();
  await page.getByLabel("Task", { exact: true }).fill(prompt);
  await page.getByRole("button", { name: "Dispatch" }).click();
  await expect(page).toHaveURL(/\/tasks\/task_[0-9]{8}$/);

  await page.goto("/approvals");
  await expect(page.getByRole("heading", { name: "Approvals" })).toBeVisible();
  // At least one request is pending (the one just dispatched) with its panel loaded.
  await expect(page.getByRole("button", { name: "Approve", exact: true }).first()).toBeVisible();

  // Move focus off any field, then triage with the keyboard: j highlights the
  // first row, a approves it.
  await page.getByRole("heading", { name: "Approvals" }).click();
  await page.keyboard.press("j");
  await page.keyboard.press("a");

  await expect(page.getByText("Approval recorded")).toBeVisible();
});
