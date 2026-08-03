import { paginateItems, type PageWindow } from "./bounded-pagination";

export const INBOX_PAGE_SIZE = 50;

export type InboxPage<T> = PageWindow<T>;

/**
 * Keep the task inbox DOM bounded without hiding matches from filtering or
 * search. Pagination happens after the complete loaded result set is filtered
 * and ordered, so counts and keyboard order stay truthful.
 */
export function paginateInbox<T>(
  items: readonly T[],
  requestedPage: number,
  pageSize: number = INBOX_PAGE_SIZE,
): InboxPage<T> {
  const safePageSize = Number.isSafeInteger(pageSize) && pageSize > 0 ? pageSize : INBOX_PAGE_SIZE;
  return paginateItems(items, requestedPage, safePageSize, "start");
}
