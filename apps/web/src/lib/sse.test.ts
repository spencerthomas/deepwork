import { describe, expect, it } from "vitest";

import { decodeTaskEvent, isTaskEventName } from "./sse";

describe("decodeTaskEvent", () => {
  it("decodes a named JSON object event", () => {
    expect(
      decodeTaskEvent("content.delta", "event-3", '{"delta":"Working"}'),
    ).toEqual({
      id: "event-3",
      name: "content.delta",
      data: { delta: "Working" },
    });
  });

  it("rejects malformed or scalar event data", () => {
    expect(() => decodeTaskEvent("run.started", "1", "{")).toThrow(
      "invalid JSON",
    );
    expect(() => decodeTaskEvent("run.started", "1", '"running"')).toThrow(
      "must be an object",
    );
  });

  it("requires an id and accepts only the normalized event vocabulary", () => {
    expect(() => decodeTaskEvent("run.started", "", "{}")).toThrow(
      "missing its SSE id",
    );
    expect(isTaskEventName("interrupt.requested")).toBe(true);
    expect(isTaskEventName("message")).toBe(false);
    expect(() => decodeTaskEvent("message", "1", "{}")).toThrow(
      "Unsupported task event",
    );
  });

  it("rejects uncorrelated or invalid approval events", () => {
    expect(() =>
      decodeTaskEvent("interrupt.requested", "1", '{"question":"Continue?"}'),
    ).toThrow("valid interruptId");
    expect(() =>
      decodeTaskEvent(
        "decision.recorded",
        "2",
        '{"interruptId":"interrupt-1","decision":"skip"}',
      ),
    ).toThrow("approve or reject");
  });
});
