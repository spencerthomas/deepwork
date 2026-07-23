import { describe, expect, it } from "vitest";

import { inboxViewToQuery, readInboxView, type InboxView } from "./task-inbox-url";
import { EMPTY_TASK_INBOX_FILTER } from "../task-inbox-filter";

const DEFAULT_VIEW: InboxView = { filter: EMPTY_TASK_INBOX_FILTER, grouped: true };

function view(over: Partial<InboxView["filter"]>, grouped = true): InboxView {
  return { filter: { ...EMPTY_TASK_INBOX_FILTER, ...over }, grouped };
}

describe("readInboxView", () => {
  it("defaults to a grouped, unfiltered inbox when the query is empty", () => {
    expect(readInboxView(new URLSearchParams(""))).toEqual(DEFAULT_VIEW);
  });

  it("reads status, query, and the recent view", () => {
    const result = readInboxView(new URLSearchParams("status=running&q=deploy&view=recent"));
    expect(result.filter.status).toBe("running");
    expect(result.filter.query).toBe("deploy");
    expect(result.grouped).toBe(false);
  });

  it("fails closed to defaults for an unknown status or view", () => {
    const result = readInboxView(new URLSearchParams("status=bogus&view=weird"));
    expect(result.filter.status).toBe("all");
    expect(result.grouped).toBe(true);
  });

  it("caps an over-long query the same way the search field does", () => {
    const long = "x".repeat(5_000);
    expect(readInboxView(new URLSearchParams(`q=${long}`)).filter.query).toHaveLength(200);
  });
});

describe("inboxViewToQuery", () => {
  it("emits nothing for the default view", () => {
    expect(inboxViewToQuery(DEFAULT_VIEW)).toBe("");
  });

  it("emits only the params that differ from the default", () => {
    expect(inboxViewToQuery(view({ status: "waiting-approval" }))).toBe("status=waiting-approval");
    expect(inboxViewToQuery(view({}, false))).toBe("view=recent");
    expect(inboxViewToQuery(view({ query: "hello world" }))).toBe("q=hello+world");
  });

  it("omits a whitespace-only query", () => {
    expect(inboxViewToQuery(view({ query: "   " }))).toBe("");
  });

  it("round-trips a fully specified view", () => {
    const original = view({ status: "failed", query: "retry" }, false);
    const restored = readInboxView(new URLSearchParams(inboxViewToQuery(original)));
    expect(restored).toEqual(original);
  });
});
