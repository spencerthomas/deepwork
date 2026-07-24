/**
 * Device-local persistence for the task-detail run panel's open/closed choice
 * (coverage-matrix TASK-CTRL-24, owner DW-TASK-003).
 *
 * Mirrors `theme-preference`: the interpretation is a pure, unit-tested function
 * and the read/write wrappers add the `window` and try/catch guards (private
 * mode, quota, disabled storage). Device-local by design — a UI preference, no
 * cross-device sync — and it never hides the current approval or status, which
 * live in the main thread, not the panel.
 */

export const RUN_PANEL_STORAGE_KEY = "dw-run-panel-open";

/**
 * Interpret a raw stored value. The panel defaults to open, so only the explicit
 * closed marker ("0") closes it; anything else (absent, empty, unexpected) keeps
 * the open default. Pure.
 */
export function readRunPanelOpen(storedValue: string | null): boolean {
  return storedValue !== "0";
}

function storage(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

/** Read the persisted open/closed choice, defaulting to open. */
export function loadRunPanelOpen(): boolean {
  const store = storage();
  if (store === null) {
    return true;
  }
  try {
    return readRunPanelOpen(store.getItem(RUN_PANEL_STORAGE_KEY));
  } catch {
    return true;
  }
}

/** Persist the open/closed choice; a lost write must never break the toggle. */
export function saveRunPanelOpen(open: boolean): void {
  const store = storage();
  if (store === null) {
    return;
  }
  try {
    store.setItem(RUN_PANEL_STORAGE_KEY, open ? "1" : "0");
  } catch {
    // Best effort; the panel still works, the choice just is not remembered.
  }
}
