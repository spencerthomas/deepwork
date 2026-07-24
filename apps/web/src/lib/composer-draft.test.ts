import { describe, expect, it } from "vitest";

import {
  DRAFT_MAX_LENGTH,
  DRAFT_TTL_MS,
  parseComposerDraft,
  serializeComposerDraft,
} from "./composer-draft";

const NOW = 1_700_000_000_000;

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
