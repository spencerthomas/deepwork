import type { TaskEvent } from "@/lib/task-types";

import { paginateItems } from "./bounded-pagination";

export const STREAM_EVENT_PAGE_SIZE = 100;

export interface StreamEventWindow {
  end: number;
  hasEarlier: boolean;
  hasNewer: boolean;
  items: readonly TaskEvent[];
  page: number;
  pageCount: number;
  start: number;
}

/**
 * Page backward from the latest event while preserving chronological order
 * inside each page. A fixed window keeps the Stream DOM bounded without
 * dropping any retained event from inspection.
 */
export function streamEventWindow(
  events: readonly TaskEvent[],
  requestedPage: number,
  pageSize = STREAM_EVENT_PAGE_SIZE,
): StreamEventWindow {
  const page = paginateItems(events, requestedPage, pageSize, "end");

  return {
    ...page,
    hasEarlier: page.start > 1,
    hasNewer: page.page > 1,
  };
}
