import { describe, expect, it } from "vitest";

import { INBOX_PAGE_SIZE, paginateInbox } from "./task-inbox-pagination";

describe("paginateInbox", () => {
  const thousand = Array.from({ length: 1_000 }, (_, index) => `task-${index + 1}`);

  it("bounds a 1,000-task result to fifty mounted rows", () => {
    const first = paginateInbox(thousand, 1);
    expect(first.items).toHaveLength(INBOX_PAGE_SIZE);
    expect(first).toMatchObject({ start: 1, end: 50, page: 1, pageCount: 20, total: 1_000 });
  });

  it("returns the requested page without changing source order", () => {
    const second = paginateInbox(thousand, 2);
    expect(second.items[0]).toBe("task-51");
    expect(second.items.at(-1)).toBe("task-100");
    expect(second).toMatchObject({ start: 51, end: 100, page: 2 });
  });

  it("clamps stale URL pages and represents an empty result honestly", () => {
    expect(paginateInbox(thousand, 999).page).toBe(20);
    expect(paginateInbox([], 4)).toEqual({
      end: 0,
      items: [],
      page: 1,
      pageCount: 1,
      start: 0,
      total: 0,
    });
  });
});
