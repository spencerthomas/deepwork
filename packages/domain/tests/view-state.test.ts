import {
  isTaskStatus,
  isViewStateKind,
  TASK_STATUSES,
  VIEW_STATE_KINDS,
} from "@deepwork/domain";
import { describe, expect, it } from "vitest";

describe("public state guards", () => {
  it("rejects unknown status and view-state strings", () => {
    expect(isTaskStatus("done")).toBe(true);
    expect(isTaskStatus("complete-ish")).toBe(false);
    expect(isViewStateKind("unavailable")).toBe(true);
    expect(isViewStateKind("supported-by-label")).toBe(false);
  });

  it("freezes status vocabularies at runtime", () => {
    expect(Object.isFrozen(TASK_STATUSES)).toBe(true);
    expect(Object.isFrozen(VIEW_STATE_KINDS)).toBe(true);
  });
});
