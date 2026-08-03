export interface PageWindow<T> {
  end: number;
  items: T[];
  page: number;
  pageCount: number;
  start: number;
  total: number;
}

/** Page a fixed-size window from either edge without changing item order. */
export function paginateItems<T>(
  items: readonly T[],
  requestedPage: number,
  pageSize: number,
  anchor: "start" | "end",
): PageWindow<T> {
  const size = Number.isSafeInteger(pageSize) && pageSize > 0 ? pageSize : 1;
  const pageCount = Math.max(1, Math.ceil(items.length / size));
  const normalizedPage = Number.isSafeInteger(requestedPage) ? requestedPage : 1;
  const page = Math.min(Math.max(normalizedPage, 1), pageCount);
  const startIndex =
    anchor === "start" ? (page - 1) * size : Math.max(0, items.length - page * size);
  const endIndex =
    anchor === "start"
      ? Math.min(items.length, startIndex + size)
      : Math.max(0, items.length - (page - 1) * size);
  const pageItems = items.slice(startIndex, endIndex);

  return {
    end: endIndex,
    items: pageItems,
    page,
    pageCount,
    start: pageItems.length === 0 ? 0 : startIndex + 1,
    total: items.length,
  };
}
