import type { TaskEvent } from "@/lib/task-types";

import { paginateItems } from "./bounded-pagination";

export const STREAM_EVENT_PAGE_SIZE = 100;

export interface StreamEventWindow {
  end: number;
  hasEarlier: boolean;
  hasNewer: boolean;
  items: readonly TaskEvent[];
  newerEventCount: number;
  page: number;
  pageCount: number;
  start: number;
}

export interface StreamPagination {
  anchorEventId?: string;
  page: number;
  scope: string;
}

export function resolveStreamPagination(
  pagination: StreamPagination,
  scope: string,
): StreamPagination {
  return pagination.scope === scope ? pagination : { page: 1, scope };
}

/**
 * Page backward from the latest event while preserving chronological order
 * inside each page. Historical pages may be pinned to the last event that was
 * present when inspection began, so live arrivals cannot rewrite the window.
 * Page one deliberately ignores that anchor and continues to follow the tail.
 */
export function streamEventWindow(
  events: readonly TaskEvent[],
  requestedPage: number,
  pageSize = STREAM_EVENT_PAGE_SIZE,
  anchorEventId?: string,
): StreamEventWindow {
  const anchoredIndex =
    requestedPage > 1 && anchorEventId !== undefined
      ? events.findIndex((event) => event.id === anchorEventId)
      : -1;
  const anchoredEnd = anchoredIndex >= 0 ? anchoredIndex + 1 : events.length;
  const page = paginateItems(events.slice(0, anchoredEnd), requestedPage, pageSize, "end");

  return {
    ...page,
    hasEarlier: page.start > 1,
    hasNewer: page.page > 1,
    newerEventCount: events.length - anchoredEnd,
  };
}
