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
 *
 * Tenant boundary: fixture drafts retain their historic device-local scope.
 * API drafts are partitioned by the authenticated actor and workspace before
 * any storage access; there is deliberately no generic API fallback.
 */

import { PROMPT_MAX_LENGTH } from "./task-types";
import { validatePrompt } from "./task-normalizers";

export const DRAFT_STORAGE_PREFIX = "dw-task-draft";
export const DISPATCH_ATTEMPT_STORAGE_PREFIX = "dw-task-dispatch";

/** Drafts older than this (or future-dated) are treated as expired and dropped. */
export const DRAFT_TTL_MS = 7 * 24 * 60 * 60 * 1000;

/** Hard cap on a persisted draft, independent of the live textarea limit. */
export const DRAFT_MAX_LENGTH = 20_000;

export interface ComposerDraft {
  prompt: string;
  savedAt: number;
}

export interface ComposerDispatchAttempt {
  schemaVersion: 1;
  idempotencyKey: string;
  attemptedAt: number;
  prompt: string;
  agentId?: string;
  journey: "general" | "coding";
}

export function createComposerDispatchAttempt(
  input: Pick<ComposerDispatchAttempt, "prompt" | "agentId" | "journey">,
  now: number,
  createKey: () => string,
): ComposerDispatchAttempt {
  const prompt = validatePrompt(input.prompt);
  const idempotencyKey = createKey().trim();
  if (idempotencyKey === "") {
    throw new Error("A task dispatch identity could not be created.");
  }
  return {
    schemaVersion: 1,
    idempotencyKey,
    attemptedAt: now,
    prompt,
    ...(input.agentId ? { agentId: input.agentId } : {}),
    journey: input.journey,
  };
}

export interface DraftIdentity {
  actorId: string;
  workspaceId: string;
}

export type DraftRuntimeScope = { mode: "fixture" } | { mode: "api"; identity: DraftIdentity };

/**
 * Return the only valid draft scope for a runtime. JSON's array encoding is
 * unambiguous even when either identity contains punctuation or delimiters.
 * The API branch requires an identity by construction, so callers cannot fall
 * back to the legacy unscoped `api` key while a session is unresolved.
 */
export function draftScopeForRuntime(runtime: DraftRuntimeScope): string {
  if (runtime.mode === "fixture") {
    return "fixture";
  }
  return `api:${JSON.stringify([runtime.identity.actorId, runtime.identity.workspaceId])}`;
}

/**
 * Storage key for a draft, qualified by a scope returned from
 * `draftScopeForRuntime`.
 */
export function draftStorageKey(scope: string): string {
  return `${DRAFT_STORAGE_PREFIX}:${scope}`;
}

export function dispatchAttemptStorageKey(scope: string): string {
  return `${DISPATCH_ATTEMPT_STORAGE_PREFIX}:${scope}`;
}

/** Human-readable age of a saved draft (pure): "just now", "5 minutes ago", … */
export function formatDraftAge(savedAt: number, now: number): string {
  const minutes = Math.floor(Math.max(0, now - savedAt) / 60_000);
  if (minutes < 1) {
    return "just now";
  }
  if (minutes < 60) {
    return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  }
  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
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

export function parseComposerDispatchAttempt(
  raw: string | null,
  now: number,
): ComposerDispatchAttempt | null {
  if (raw === null || raw === "") return null;
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return null;
  }
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) return null;
  const record = parsed as Record<string, unknown>;
  const { schemaVersion, idempotencyKey, attemptedAt, prompt, agentId, journey } = record;
  if (
    schemaVersion !== 1 ||
    typeof idempotencyKey !== "string" ||
    idempotencyKey.trim() === "" ||
    typeof attemptedAt !== "number" ||
    !Number.isFinite(attemptedAt) ||
    typeof prompt !== "string" ||
    prompt.trim() === "" ||
    prompt.length > PROMPT_MAX_LENGTH ||
    (journey !== "general" && journey !== "coding") ||
    (agentId !== undefined && (typeof agentId !== "string" || agentId.trim() === ""))
  ) {
    return null;
  }
  // Unlike an ordinary draft, an ambiguous dispatch must not silently expire:
  // only an accepted receipt or authoritative rejection may unlock it.
  if (attemptedAt < 0 || attemptedAt > now) return null;
  return {
    schemaVersion: 1,
    idempotencyKey,
    attemptedAt,
    prompt,
    ...(typeof agentId === "string" ? { agentId } : {}),
    journey,
  };
}

function storage(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

/** Read the current live draft for `scope`, or `null` when there is none. */
export function loadComposerDraft(scope: string, now: number = Date.now()): ComposerDraft | null {
  const store = storage();
  if (store === null) {
    return null;
  }
  try {
    return parseComposerDraft(store.getItem(draftStorageKey(scope)), now);
  } catch {
    return null;
  }
}

/** Persist a non-empty draft; an empty/whitespace prompt clears any stored draft. */
export function saveComposerDraft(scope: string, prompt: string, now: number = Date.now()): void {
  const store = storage();
  if (store === null) {
    return;
  }
  const key = draftStorageKey(scope);
  try {
    if (prompt.trim() === "") {
      store.removeItem(key);
      return;
    }
    store.setItem(key, serializeComposerDraft(prompt, now));
  } catch {
    // Storage can be unavailable or full; a lost draft must never break typing.
  }
}

/** Remove any stored draft for `scope` (explicit discard, or a successful dispatch). */
export function clearComposerDraft(scope: string): void {
  const store = storage();
  if (store === null) {
    return;
  }
  try {
    store.removeItem(draftStorageKey(scope));
  } catch {
    // Best effort; nothing to recover if removal fails.
  }
}

export function loadComposerDispatchAttempt(
  scope: string,
  now: number = Date.now(),
): ComposerDispatchAttempt | null {
  const store = storage();
  if (store === null) return null;
  try {
    return parseComposerDispatchAttempt(store.getItem(dispatchAttemptStorageKey(scope)), now);
  } catch {
    return null;
  }
}

export function saveComposerDispatchAttempt(
  scope: string,
  attempt: ComposerDispatchAttempt,
): boolean {
  const store = storage();
  if (store === null) return false;
  try {
    store.setItem(dispatchAttemptStorageKey(scope), JSON.stringify(attempt));
    return true;
  } catch {
    return false;
  }
}

export function clearComposerDispatchAttempt(scope: string): void {
  const store = storage();
  if (store === null) return;
  try {
    store.removeItem(dispatchAttemptStorageKey(scope));
  } catch {
    // Best effort; the in-memory composer remains locked for this session.
  }
}
