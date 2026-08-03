import { expect, test, type Locator, type Page } from "@playwright/test";

import { blockNonLoopbackEgress } from "./support/block-non-loopback-egress";

async function tabTo(page: Page, target: Locator, limit = 50): Promise<void> {
  await expect(target).toBeVisible();
  for (let index = 0; index < limit; index += 1) {
    if (await target.evaluate((element) => element === document.activeElement)) return;
    await page.keyboard.press("Tab");
  }
  throw new Error(`Keyboard focus did not reach ${await target.getAttribute("aria-label")}.`);
}

async function expectNoHorizontalOverflow(page: Page): Promise<void> {
  await expect
    .poll(() =>
      page.evaluate(
        () =>
          Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) <=
          window.innerWidth,
      ),
    )
    .toBe(true);
}

async function expectMinimumTarget(target: Locator): Promise<void> {
  const box = await target.boundingBox();
  expect(box).not.toBeNull();
  expect(box?.width).toBeGreaterThanOrEqual(24);
  expect(box?.height).toBeGreaterThanOrEqual(24);
}

test.describe("assistive interaction acceptance", () => {
  test.use({ viewport: { width: 800, height: 900 } });

  test("completes the review journey by keyboard and preserves modal and system preferences", async ({
    page,
  }) => {
    await blockNonLoopbackEgress(page);
    await page.goto("/tasks/new");
    await expect(page.getByRole("heading", { name: "New task" })).toBeVisible();
    await expect(page.getByRole("radio", { checked: true })).toBeVisible();

    // Traverse from the document itself; no pointer click is needed to compose
    // or dispatch the API-backed fixture task.
    const prompt = page.getByLabel("Task", { exact: true });
    await tabTo(page, prompt);
    await page.keyboard.insertText("Prove the assistive task journey");
    await page.keyboard.press("Control+Enter");
    await expect(page).toHaveURL(/\/tasks\/task_[0-9]{8}$/);

    const lifecycle = page.getByTestId("task-lifecycle-status");
    await expect(lifecycle).toHaveAttribute("role", "status");
    await expect(lifecycle).toHaveAttribute("aria-live", "polite");
    await expect(lifecycle).toHaveAttribute("aria-atomic", "true");
    await expect(lifecycle).toHaveText("Needs review");

    await page.emulateMedia({ reducedMotion: "reduce" });
    const approve = page.getByRole("button", { name: "Approve", exact: true });
    await tabTo(page, approve);
    await page.keyboard.press("Enter");
    await expect(lifecycle).toHaveText("Running");
    await expect
      .poll(() =>
        page
          .locator(".animate-ping")
          .evaluate((element) => getComputedStyle(element).animationName),
      )
      .toBe("none");
    await expect(lifecycle).toHaveText("Done");

    // Completion focus only occurs after this mounted page observed an active
    // lifecycle state; the inspectable result is now the predictable target.
    const result = page.getByRole("region", { name: "Task result" });
    await expect(result).toBeFocused();
    await expect(result.getByText("Run completed", { exact: true })).toBeVisible();

    // The Run panel implements the horizontal tabs pattern: arrow keys change
    // both DOM focus and aria-selected, without a click.
    const panelToggle = page.getByRole("button", { name: "Toggle run panel" });
    if ((await panelToggle.getAttribute("aria-pressed")) === "false") {
      await tabTo(page, panelToggle);
      await page.keyboard.press("Enter");
    }
    const overviewTab = page.getByRole("tab", { name: "Overview" });
    await tabTo(page, overviewTab);
    await page.keyboard.press("ArrowRight");
    const activityTab = page.getByRole("tab", { name: "Activity" });
    await expect(activityTab).toBeFocused();
    await expect(activityTab).toHaveAttribute("aria-selected", "true");
    await expect(overviewTab).toHaveAttribute("aria-selected", "false");

    const more = page.getByRole("button", { name: "More destinations" });
    await tabTo(page, more);
    await page.keyboard.press("Enter");
    const dialog = page.getByRole("dialog", { name: "More" });
    await expect(dialog).toBeVisible();
    const dialogControls = dialog.locator("a[href], button:not([disabled])");
    const firstControl = dialogControls.first();
    const lastControl = dialogControls.last();
    await expect(firstControl).toBeFocused();
    await page.keyboard.press("Shift+Tab");
    await expect(lastControl).toBeFocused();
    await page.keyboard.press("Tab");
    await expect(firstControl).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();
    await expect(more).toBeFocused();

    // Replacing More with another modal must leave focus in the replacement,
    // not restore it to the More trigger behind that modal.
    await page.keyboard.press("Enter");
    await expect(dialog).toBeVisible();
    await page.keyboard.press("Control+k");
    const commandDialog = page.getByRole("dialog", { name: "Command palette" });
    await expect(commandDialog).toBeVisible();
    await expect(page.getByRole("combobox", { name: "Search commands" })).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(commandDialog).toBeHidden();
    await tabTo(page, more);

    const reducedMotionStyles = await more.evaluate((element) => {
      const styles = getComputedStyle(element);
      return {
        transitionDelay: styles.transitionDelay,
        transitionDuration: styles.transitionDuration,
        scrollBehavior: getComputedStyle(document.documentElement).scrollBehavior,
      };
    });
    expect(reducedMotionStyles).toEqual({
      transitionDelay: "0s",
      transitionDuration: "0s",
      scrollBehavior: "auto",
    });

    await page.emulateMedia({ forcedColors: "active", reducedMotion: "reduce" });
    const forcedColorStyles = await page.evaluate(() => {
      const focused = document.activeElement;
      const current = document.querySelector<HTMLElement>('[aria-current="page"]');
      if (!(focused instanceof HTMLElement) || !current) return null;
      const focusStyles = getComputedStyle(focused);
      const currentStyles = getComputedStyle(current);
      return {
        forcedColorsActive: matchMedia("(forced-colors: active)").matches,
        focusOutlineColor: focusStyles.outlineColor,
        focusOutlineStyle: focusStyles.outlineStyle,
        focusOutlineWidth: focusStyles.outlineWidth,
        currentForcedColorAdjust: currentStyles.forcedColorAdjust,
        currentOutlineStyle: currentStyles.outlineStyle,
        currentOutlineWidth: currentStyles.outlineWidth,
      };
    });
    expect(forcedColorStyles).not.toBeNull();
    expect(forcedColorStyles?.forcedColorsActive).toBe(true);
    expect(forcedColorStyles?.focusOutlineStyle).toBe("solid");
    expect(forcedColorStyles?.focusOutlineWidth).toBe("2px");
    expect(forcedColorStyles?.focusOutlineColor).not.toBe("rgba(0, 0, 0, 0)");
    expect(forcedColorStyles?.currentForcedColorAdjust).toBe("auto");
    expect(forcedColorStyles?.currentOutlineStyle).toBe("solid");
    expect(forcedColorStyles?.currentOutlineWidth).toBe("1px");

    // A retained completed task opened afresh is inspectable but must not steal
    // initial page focus: only the observed active-to-complete transition above
    // is allowed to move focus to the result.
    const completedPath = new URL(page.url()).pathname;
    await page.goto("/tasks");
    await page.goto(completedPath);
    await expect(page.getByRole("region", { name: "Task result" })).toBeVisible();
    await expect(page.getByRole("region", { name: "Task result" })).not.toBeFocused();
  });
});

test("a fresh 320px touch context completes the primary journey without overflow", async ({
  browser,
}) => {
  const context = await browser.newContext({
    baseURL: "http://127.0.0.1:3000",
    viewport: { width: 320, height: 800 },
    hasTouch: true,
    serviceWorkers: "block",
    storageState: "output/playwright/auth.json",
  });
  const page = await context.newPage();
  try {
    await blockNonLoopbackEgress(page);
    await page.goto("/tasks/new");
    await expectNoHorizontalOverflow(page);

    const prompt = page.getByLabel("Task", { exact: true });
    await prompt.tap();
    await prompt.fill("Prove the 320px touch journey");
    const dispatch = page.getByRole("button", { name: "Dispatch" });
    await expectMinimumTarget(dispatch);
    await dispatch.tap();
    await expect(page).toHaveURL(/\/tasks\/task_[0-9]{8}$/);
    const taskPath = new URL(page.url()).pathname;
    await expectNoHorizontalOverflow(page);

    const approve = page.getByRole("button", { name: "Approve", exact: true });
    await expectMinimumTarget(approve);
    await approve.tap();
    await expect(page.getByTestId("task-lifecycle-status")).toHaveText("Done");
    await expectNoHorizontalOverflow(page);

    const files = page.getByRole("tab", { name: "Files" });
    await expectMinimumTarget(files);
    await files.tap();
    await expect(page.getByText("result.md", { exact: true })).toBeVisible();
    await expectNoHorizontalOverflow(page);

    const home = page.getByRole("link", { name: "Deep Work home" });
    await expectMinimumTarget(home);
    await home.tap();
    const retainedTask = page.locator(`a[href="${taskPath}"]`).first();
    await expect(retainedTask).toBeVisible();
    await retainedTask.tap();
    await expect(page).toHaveURL(new RegExp(`${taskPath}$`));
    await expect(page.getByRole("region", { name: "Task result" })).toBeVisible();
    await expectNoHorizontalOverflow(page);

    const more = page.getByRole("button", { name: "More destinations" });
    await expectMinimumTarget(more);
    await more.tap();
    const dialog = page.getByRole("dialog", { name: "More" });
    await expect(dialog).toBeVisible();
    await expectNoHorizontalOverflow(page);
    for (const destination of await dialog.getByRole("link").all()) {
      await expectMinimumTarget(destination);
    }
  } finally {
    await context.close();
  }
});
