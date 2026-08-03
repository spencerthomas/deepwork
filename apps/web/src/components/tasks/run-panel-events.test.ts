import { describe, expect, it } from "vitest";

import type { TaskEvent } from "../../lib/task-types";
import {
  resolveStreamPagination,
  streamEventWindow,
  type StreamPagination,
} from "./run-panel-events";

function events(count: number): TaskEvent[] {
  return Array.from({ length: count }, (_, index) => ({
    id: String(index + 1),
    name: "content.delta",
    data: { text: `Update ${String(index + 1)}` },
  }));
}

describe("streamEventWindow", () => {
  it("starts at the latest fixed-size page and preserves chronological order", () => {
    const window = streamEventWindow(events(251), 1, 100);
    expect(window.items).toHaveLength(100);
    expect(window.items[0]?.id).toBe("152");
    expect(window.items[99]?.id).toBe("251");
    expect(window).toMatchObject({ start: 152, end: 251, hasEarlier: true, hasNewer: false });
  });

  it("pages toward older events without growing the mounted window", () => {
    const middle = streamEventWindow(events(251), 2, 100);
    expect(middle.items).toHaveLength(100);
    expect(middle.items[0]?.id).toBe("52");
    expect(middle.items[99]?.id).toBe("151");
    expect(middle).toMatchObject({ start: 52, end: 151, hasEarlier: true, hasNewer: true });

    const oldest = streamEventWindow(events(251), 3, 100);
    expect(oldest.items).toHaveLength(51);
    expect(oldest.items[0]?.id).toBe("1");
    expect(oldest.items[50]?.id).toBe("51");
    expect(oldest).toMatchObject({ start: 1, end: 51, hasEarlier: false, hasNewer: true });
  });

  it("clamps invalid pages and handles an empty stream", () => {
    expect(streamEventWindow(events(3), 99, 2)).toMatchObject({ page: 2, start: 1, end: 1 });
    expect(streamEventWindow([], -4)).toMatchObject({ page: 1, start: 0, end: 0, items: [] });
  });

  it("keeps an older page stable while live events append", () => {
    const before = streamEventWindow(events(251), 2, 100, "251");
    const after = streamEventWindow(events(253), 2, 100, "251");
    const earlier = streamEventWindow(events(253), 3, 100, "251");

    expect(before.items.map((event) => event.id)).toEqual(after.items.map((event) => event.id));
    expect(after).toMatchObject({
      start: 52,
      end: 151,
      newerEventCount: 2,
      hasEarlier: true,
      hasNewer: true,
    });
    expect(earlier).toMatchObject({ start: 1, end: 51, newerEventCount: 2 });
    expect(earlier.items.at(-1)?.id).toBe("51");
    expect(after.items[0]?.id).toBe("52");
  });

  it("follows the live tail on page one even when an old anchor remains", () => {
    const window = streamEventWindow(events(253), 1, 100, "251");

    expect(window.items[0]?.id).toBe("154");
    expect(window.items[99]?.id).toBe("253");
    expect(window.newerEventCount).toBe(0);
  });

  it("reports every newer event when arrivals exceed one page", () => {
    const window = streamEventWindow(events(402), 2, 100, "251");

    expect(window.items[0]?.id).toBe("52");
    expect(window.items.at(-1)?.id).toBe("151");
    expect(window.newerEventCount).toBe(151);
  });
});

describe("resolveStreamPagination", () => {
  const history: StreamPagination = { scope: "task-a:all", page: 4, anchorEventId: "251" };

  it("preserves paging within the same task and filter", () => {
    expect(resolveStreamPagination(history, "task-a:all")).toBe(history);
  });

  it("returns synchronously to the live tail when task or filter changes", () => {
    expect(resolveStreamPagination(history, "task-b:all")).toEqual({
      scope: "task-b:all",
      page: 1,
    });
    expect(resolveStreamPagination(history, "task-a:plans")).toEqual({
      scope: "task-a:plans",
      page: 1,
    });
  });
});
