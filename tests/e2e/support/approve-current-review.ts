import { expect, type Page } from "@playwright/test";

/** Explicitly review every ordered action, with the bounded legacy fallback. */
export async function approveCurrentReview(page: Page): Promise<void> {
  const batch = page.getByRole("region", { name: "Ordered approval batch" });
  if ((await batch.count()) > 0) {
    const approveButtons = batch.getByRole("button", { name: "Approve", exact: true });
    const count = await approveButtons.count();
    expect(count).toBeGreaterThan(0);
    for (let index = 0; index < count; index += 1) {
      await approveButtons.nth(index).click();
    }
    const submit = batch.getByRole("button", { name: "Submit reviewed batch" });
    await expect(submit).toBeEnabled();
    await submit.click();
    return;
  }
  await page.getByRole("button", { name: "Approve", exact: true }).last().click();
}
