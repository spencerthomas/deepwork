export const INBOX_PAGE_SIZE = 50;

export interface InboxPage<T> {
  end: number;
  items: T[];
  page: number;
  pageCount: number;
  start: number;
  total: number;
}

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
  const pageCount = Math.max(1, Math.ceil(items.length / safePageSize));
  const normalizedPage = Number.isSafeInteger(requestedPage) ? requestedPage : 1;
  const page = Math.min(Math.max(normalizedPage, 1), pageCount);
  const startIndex = (page - 1) * safePageSize;
  const pageItems = items.slice(startIndex, startIndex + safePageSize);
  return {
    end: startIndex + pageItems.length,
    items: pageItems,
    page,
    pageCount,
    start: pageItems.length === 0 ? 0 : startIndex + 1,
    total: items.length,
  };
}
