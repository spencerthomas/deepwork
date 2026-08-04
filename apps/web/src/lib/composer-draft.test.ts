import { afterEach, describe, expect, it, vi } from "vitest";

import {
  DRAFT_MAX_LENGTH,
  DRAFT_TTL_MS,
  draftScopeForRuntime,
  draftStorageKey,
  formatDraftAge,
  loadComposerDraft,
  parseComposerDraft,
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
