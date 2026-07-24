/**
 * Device-local persistence for the task composer draft (coverage-matrix
 * TASK-CTRL-19, owner DW-TASK-002).
 *
 * The in-progress prompt is saved to localStorage so navigating away or
 * reloading does not lose it. A draft is bounded, carries an explicit save
 * timestamp, and expires; the composer offers an explicit Discard and clears it
 * on a successful dispatch. Storage is device-local by design — no cross-device
 * sync — matching the privacy posture of the transient Edit & re-run handoff:
 * a prompt can hold private context, so it never leaves the browser.
 *
 * The parse/serialize core is pure so it is fully unit tested without touching
 * storage or the clock; the load/save/clear wrappers add the `window` and
 * try/catch guards (private mode, quota, disabled storage) so a lost draft can
 * never break typing.
 */

export const DRAFT_STORAGE_KEY = "dw-task-draft";

/** Drafts older than this (or future-dated) are treated as expired and dropped. */
export const DRAFT_TTL_MS = 7 * 24 * 60 * 60 * 1000;

/** Hard cap on a persisted draft, independent of the live textarea limit. */
export const DRAFT_MAX_LENGTH = 20_000;

export interface ComposerDraft {
  prompt: string;
  savedAt: number;
}

/**
 * Interpret a raw stored value as a live draft, or `null` when it is absent,
 * malformed, empty, or expired relative to `now`. Pure.
 */
export function parseComposerDraft(raw: string | null, now: number): ComposerDraft | null {
  if (raw === null || raw === "") {
    return null;
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return null;
  }
  if (typeof parsed !== "object" || parsed === null) {
    return null;
  }
  const record = parsed as Record<string, unknown>;
  const { prompt, savedAt } = record;
  if (typeof prompt !== "string" || typeof savedAt !== "number" || !Number.isFinite(savedAt)) {
    return null;
  }
  const bounded = prompt.slice(0, DRAFT_MAX_LENGTH);
  if (bounded.trim() === "") {
    return null;
  }
  // A future-dated or expired stamp is not a usable draft.
  const age = now - savedAt;
  if (age < 0 || age > DRAFT_TTL_MS) {
    return null;
  }
  return { prompt: bounded, savedAt };
}

/** Serialize a bounded draft for storage. Pure. */
export function serializeComposerDraft(prompt: string, now: number): string {
  return JSON.stringify({ prompt: prompt.slice(0, DRAFT_MAX_LENGTH), savedAt: now });
}

function storage(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

/** Read the current live draft, or `null` when there is none. */
export function loadComposerDraft(now: number = Date.now()): ComposerDraft | null {
  const store = storage();
  if (store === null) {
    return null;
  }
  try {
    return parseComposerDraft(store.getItem(DRAFT_STORAGE_KEY), now);
  } catch {
    return null;
  }
}

/** Persist a non-empty draft; an empty/whitespace prompt clears any stored draft. */
export function saveComposerDraft(prompt: string, now: number = Date.now()): void {
  const store = storage();
  if (store === null) {
    return;
  }
  try {
    if (prompt.trim() === "") {
      store.removeItem(DRAFT_STORAGE_KEY);
      return;
    }
    store.setItem(DRAFT_STORAGE_KEY, serializeComposerDraft(prompt, now));
  } catch {
    // Storage can be unavailable or full; a lost draft must never break typing.
  }
}

/** Remove any stored draft (explicit discard, or a successful dispatch). */
export function clearComposerDraft(): void {
  const store = storage();
  if (store === null) {
    return;
  }
  try {
    store.removeItem(DRAFT_STORAGE_KEY);
  } catch {
    // Best effort; nothing to recover if removal fails.
  }
}
