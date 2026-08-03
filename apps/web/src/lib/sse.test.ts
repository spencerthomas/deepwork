import { afterEach, describe, expect, it, vi } from "vitest";

import { decodeTaskEvent, isTaskEventName, subscribeToTaskEvents } from "./sse";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("decodeTaskEvent", () => {
  it("decodes a named JSON object event", () => {
    expect(decodeTaskEvent("content.delta", "event-3", '{"delta":"Working"}')).toEqual({
      id: "event-3",
      name: "content.delta",
      data: { delta: "Working" },
    });
  });

  it("rejects malformed or scalar event data", () => {
    expect(() => decodeTaskEvent("run.started", "1", "{")).toThrow("invalid JSON");
    expect(() => decodeTaskEvent("run.started", "1", '"running"')).toThrow("must be an object");
  });

  it("requires an id and accepts only the normalized event vocabulary", () => {
    expect(() => decodeTaskEvent("run.started", "", "{}")).toThrow("missing its SSE id");
    expect(isTaskEventName("interrupt.requested")).toBe(true);
    expect(isTaskEventName("message")).toBe(false);
    expect(() => decodeTaskEvent("message", "1", "{}")).toThrow("Unsupported task event");
  });

  it("rejects uncorrelated or invalid approval events", () => {
    expect(() => decodeTaskEvent("interrupt.requested", "1", '{"question":"Continue?"}')).toThrow(
      "valid interruptId",
    );
    expect(() =>
      decodeTaskEvent("decision.recorded", "2", '{"interruptId":"interrupt-1","decision":"skip"}'),
    ).toThrow("approve, reject, or respond");
    expect(
      decodeTaskEvent(
        "decision.recorded",
        "3",
        '{"interruptId":"interrupt-1","decision":"respond","responseProvided":true}',
      ),
    ).toMatchObject({ data: { decision: "respond" } });
  });

  it("keeps session cookies on explicitly cross-origin event streams", () => {
    const source = {
      onopen: null,
      onerror: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      close: vi.fn(),
    };
    const EventSourceMock = vi.fn(function EventSourceStub(_url: string, _init?: EventSourceInit) {
      return source;
    });
    vi.stubGlobal("EventSource", EventSourceMock);

    const close = subscribeToTaskEvents("http://api.test/api/v1/tasks/task-1/events", {
      onConnectionChange: vi.fn(),
      onError: vi.fn(),
      onEvent: vi.fn(),
    });

    expect(EventSourceMock).toHaveBeenCalledWith("http://api.test/api/v1/tasks/task-1/events", {
      withCredentials: true,
    });
    close();
    expect(source.close).toHaveBeenCalledOnce();
  });
});
