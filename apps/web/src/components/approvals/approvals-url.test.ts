import { describe, expect, it } from "vitest";

import { DECISION_VERB_ORDER } from "./approvals-model";
import { approvalFilterToQuery, readApprovalFilter } from "./approvals-url";

const ALL_FILTERS = ["all", ...DECISION_VERB_ORDER] as const;

describe("readApprovalFilter", () => {
  it("defaults to 'all' when the query is empty", () => {
    expect(readApprovalFilter(new URLSearchParams(""))).toBe("all");
  });

  it("reads each known capability filter", () => {
    for (const filter of ALL_FILTERS) {
      expect(readApprovalFilter(new URLSearchParams(`capability=${filter}`))).toBe(filter);
    }
  });

  it("fails closed to 'all' for an unknown filter", () => {
    expect(readApprovalFilter(new URLSearchParams("capability=bogus"))).toBe("all");
  });
});

describe("approvalFilterToQuery", () => {
  it("emits nothing for the default filter", () => {
    expect(approvalFilterToQuery("all")).toBe("");
  });

  it("emits the capability param for a named filter", () => {
    expect(approvalFilterToQuery("approve")).toBe("capability=approve");
    expect(approvalFilterToQuery("respond")).toBe("capability=respond");
  });

  it("round-trips every known filter", () => {
    for (const filter of ALL_FILTERS) {
      const restored = readApprovalFilter(new URLSearchParams(approvalFilterToQuery(filter)));
      expect(restored).toBe(filter);
    }
  });
});
