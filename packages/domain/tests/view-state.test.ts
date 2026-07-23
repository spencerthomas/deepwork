import { isTaskStatus, isViewStateKind } from "@deepwork/domain";
import { describe, expect, it } from "vitest";

describe("public state guards", () => {
  it("rejects unknown status and view-state strings", () => {
    expect(isTaskStatus("done")).toBe(true);
    expect(isTaskStatus("complete-ish")).toBe(false);
    expect(isViewStateKind("unavailable")).toBe(true);
    expect(isViewStateKind("supported-by-label")).toBe(false);
  });
});
