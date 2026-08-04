import { afterEach, describe, expect, it, vi } from "vitest";

import {
  clearComposerDispatchAttempt,
  createComposerDispatchAttempt,
  dispatchAttemptStorageKey,
  DRAFT_MAX_LENGTH,
  DRAFT_TTL_MS,
  draftScopeForRuntime,
  draftStorageKey,
  formatDraftAge,
  loadComposerDraft,
  loadComposerDispatchAttempt,
  parseComposerDispatchAttempt,
  parseComposerDraft,
  saveComposerDispatchAttempt,
  serializeComposerDraft,
} from "./composer-draft";

const NOW = 1_700_000_000_000;
const MINUTE = 60_000;

afterEach(() => vi.unstubAllGlobals());

describe("parseComposerDraft", () => {
  it("returns null for absent, empty, or malformed values", () => {
    expect(parseComposerDraft(null, NOW)).toBeNull();
    expect(parseComposerDraft("", NOW)).toBeNull();
    expect(parseComposerDraft("not json", NOW)).toBeNull();
    expect(parseComposerDraft("[]", NOW)).toBeNull();
    expect(parseComposerDraft("123", NOW)).toBeNull();
  });

  it("returns null when the stored shape is wrong", () => {
    expect(parseComposerDraft(JSON.stringify({ prompt: 5, savedAt: NOW }), NOW)).toBeNull();
    expect(parseComposerDraft(JSON.stringify({ prompt: "hi" }), NOW)).toBeNull();
    expect(parseComposerDraft(JSON.stringify({ prompt: "hi", savedAt: "x" }), NOW)).toBeNull();
    expect(
      parseComposerDraft(JSON.stringify({ prompt: "hi", savedAt: Number.NaN }), NOW),
    ).toBeNull();
  });

  it("returns null for an empty or whitespace-only prompt", () => {
    expect(parseComposerDraft(JSON.stringify({ prompt: "   ", savedAt: NOW }), NOW)).toBeNull();
  });

  it("drops expired and future-dated drafts", () => {
    const stale = serializeComposerDraft("keep me", NOW - DRAFT_TTL_MS - 1);
    expect(parseComposerDraft(stale, NOW)).toBeNull();
    const future = serializeComposerDraft("keep me", NOW + 1000);
    expect(parseComposerDraft(future, NOW)).toBeNull();
  });

  it("round-trips a live draft within the TTL", () => {
    const raw = serializeComposerDraft("write the launch brief", NOW - 1000);
    expect(parseComposerDraft(raw, NOW)).toEqual({
      prompt: "write the launch brief",
      savedAt: NOW - 1000,
    });
    // Exactly at the TTL boundary is still valid.
    const boundary = serializeComposerDraft("edge", NOW - DRAFT_TTL_MS);
    expect(parseComposerDraft(boundary, NOW)?.prompt).toBe("edge");
  });

  it("bounds an oversized stored prompt", () => {
    const huge = "x".repeat(DRAFT_MAX_LENGTH + 5_000);
    const raw = JSON.stringify({ prompt: huge, savedAt: NOW });
    expect(parseComposerDraft(raw, NOW)?.prompt.length).toBe(DRAFT_MAX_LENGTH);
  });
});

describe("serializeComposerDraft", () => {
  it("bounds the prompt it stores", () => {
    const raw = serializeComposerDraft("y".repeat(DRAFT_MAX_LENGTH + 100), NOW);
    const parsed = JSON.parse(raw) as { prompt: string; savedAt: number };
    expect(parsed.prompt.length).toBe(DRAFT_MAX_LENGTH);
    expect(parsed.savedAt).toBe(NOW);
  });
});

describe("draftStorageKey", () => {
  it("keeps fixture drafts on their existing scope", () => {
    const fixtureScope = draftScopeForRuntime({ mode: "fixture" });

    expect(fixtureScope).toBe("fixture");
    expect(draftStorageKey(fixtureScope)).toBe("dw-task-draft:fixture");
  });

  it("partitions API drafts by both workspace and actor", () => {
    const baseline = draftScopeForRuntime({
      mode: "api",
      identity: { actorId: "actor-a", workspaceId: "workspace-a" },
    });
    const otherWorkspace = draftScopeForRuntime({
      mode: "api",
      identity: { actorId: "actor-a", workspaceId: "workspace-b" },
    });
    const otherActor = draftScopeForRuntime({
      mode: "api",
      identity: { actorId: "actor-b", workspaceId: "workspace-a" },
    });

    expect(baseline).not.toBe(otherWorkspace);
    expect(baseline).not.toBe(otherActor);
  });

  it("uses collision-safe identity encoding even when identifiers contain delimiters", () => {
    const first = draftScopeForRuntime({
      mode: "api",
      identity: { actorId: "a:b", workspaceId: "c" },
    });
    const second = draftScopeForRuntime({
      mode: "api",
      identity: { actorId: "a", workspaceId: "b:c" },
    });

    expect(first).not.toBe(second);
  });

  it("never reads the legacy unscoped API key through an identity-qualified path", () => {
    const identityScope = draftScopeForRuntime({
      mode: "api",
      identity: { actorId: "operator", workspaceId: "workspace-a" },
    });

    const getItem = vi.fn((key: string) =>
      key === "dw-task-draft:api" ? serializeComposerDraft("legacy draft", NOW) : null,
    );
    vi.stubGlobal("window", { localStorage: { getItem } });

    expect(loadComposerDraft(identityScope, NOW)).toBeNull();
    expect(getItem).toHaveBeenCalledWith(draftStorageKey(identityScope));
    expect(getItem).not.toHaveBeenCalledWith("dw-task-draft:api");
  });
});

describe("formatDraftAge", () => {
  it("describes the age at each unit boundary", () => {
    expect(formatDraftAge(NOW, NOW)).toBe("just now");
    expect(formatDraftAge(NOW - 30_000, NOW)).toBe("just now");
    expect(formatDraftAge(NOW - MINUTE, NOW)).toBe("1 minute ago");
    expect(formatDraftAge(NOW - 5 * MINUTE, NOW)).toBe("5 minutes ago");
    expect(formatDraftAge(NOW - 60 * MINUTE, NOW)).toBe("1 hour ago");
    expect(formatDraftAge(NOW - 5 * 60 * MINUTE, NOW)).toBe("5 hours ago");
    expect(formatDraftAge(NOW - 24 * 60 * MINUTE, NOW)).toBe("1 day ago");
    expect(formatDraftAge(NOW - 3 * 24 * 60 * MINUTE, NOW)).toBe("3 days ago");
  });

  it("never reports negative ages for a future stamp", () => {
    expect(formatDraftAge(NOW + 5 * MINUTE, NOW)).toBe("just now");
  });
});

describe("ComposerDispatchAttempt", () => {
  const attempt = {
    schemaVersion: 1 as const,
    idempotencyKey: "dispatch-key-1",
    attemptedAt: NOW,
    prompt: "Write the exact launch brief",
    agentId: "agent-a",
    journey: "coding" as const,
  };

  it("round-trips the exact locked request independently from the ordinary draft", () => {
    expect(parseComposerDispatchAttempt(JSON.stringify(attempt), NOW)).toEqual(attempt);
    expect(dispatchAttemptStorageKey("fixture")).toBe("dw-task-dispatch:fixture");
    expect(dispatchAttemptStorageKey("fixture")).not.toBe(draftStorageKey("fixture"));
  });

  it("does not generate a request identity until the prompt is valid", () => {
    const createKey = vi.fn(() => "dispatch-key-new");

    expect(() =>
      createComposerDispatchAttempt(
        { prompt: " ", agentId: "agent-a", journey: "general" },
        NOW,
        createKey,
      ),
    ).toThrow("cannot be empty");
    expect(createKey).not.toHaveBeenCalled();

    expect(
      createComposerDispatchAttempt(
        { prompt: "  Write the brief  ", agentId: "agent-a", journey: "general" },
        NOW,
        createKey,
      ),
    ).toEqual({
      schemaVersion: 1,
      idempotencyKey: "dispatch-key-new",
      attemptedAt: NOW,
      prompt: "Write the brief",
      agentId: "agent-a",
      journey: "general",
    });
    expect(createKey).toHaveBeenCalledTimes(1);
  });

  it("rejects malformed, future-dated, or incomplete attempts", () => {
    expect(parseComposerDispatchAttempt(null, NOW)).toBeNull();
    expect(parseComposerDispatchAttempt("not-json", NOW)).toBeNull();
    expect(
      parseComposerDispatchAttempt(JSON.stringify({ ...attempt, idempotencyKey: "" }), NOW),
    ).toBeNull();
    expect(
      parseComposerDispatchAttempt(JSON.stringify({ ...attempt, prompt: " " }), NOW),
    ).toBeNull();
    expect(
      parseComposerDispatchAttempt(
        JSON.stringify({ ...attempt, attemptedAt: NOW - DRAFT_TTL_MS - 1 }),
        NOW,
      ),
    ).toEqual({ ...attempt, attemptedAt: NOW - DRAFT_TTL_MS - 1 });
    expect(
      parseComposerDispatchAttempt(JSON.stringify({ ...attempt, attemptedAt: NOW + 1 }), NOW),
    ).toBeNull();
  });

  it("uses the actor/workspace scope and clears only the dispatch record", () => {
    const scope = draftScopeForRuntime({
      mode: "api",
      identity: { actorId: "actor-a", workspaceId: "workspace-a" },
    });
    const values = new Map<string, string>();
    const setItem = vi.fn((key: string, value: string) => values.set(key, value));
    const getItem = vi.fn((key: string) => values.get(key) ?? null);
    const removeItem = vi.fn((key: string) => values.delete(key));
    vi.stubGlobal("window", { localStorage: { setItem, getItem, removeItem } });

    expect(saveComposerDispatchAttempt(scope, attempt)).toBe(true);
    expect(loadComposerDispatchAttempt(scope, NOW)).toEqual(attempt);
    clearComposerDispatchAttempt(scope);

    expect(removeItem).toHaveBeenCalledWith(dispatchAttemptStorageKey(scope));
    expect(removeItem).not.toHaveBeenCalledWith(draftStorageKey(scope));
  });

  it("fails closed when the exact dispatch request cannot be persisted", () => {
    vi.stubGlobal("window", {
      localStorage: {
        setItem: vi.fn(() => {
          throw new DOMException("Storage full", "QuotaExceededError");
        }),
      },
    });

    expect(saveComposerDispatchAttempt("fixture", attempt)).toBe(false);
  });
});
