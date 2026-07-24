import { describe, expect, it } from "vitest";

import { approvalsNavLabel, formatPendingCount, NAV_BADGE_MAX } from "./nav-badge";

describe("formatPendingCount", () => {
  it("returns null when nothing is pending", () => {
    expect(formatPendingCount(0)).toBeNull();
    expect(formatPendingCount(-3)).toBeNull();
    expect(formatPendingCount(Number.NaN)).toBeNull();
  });

  it("shows an exact count up to the cap", () => {
    expect(formatPendingCount(1)).toBe("1");
    expect(formatPendingCount(NAV_BADGE_MAX)).toBe(String(NAV_BADGE_MAX));
  });

  it("collapses counts above the cap to an overflow marker", () => {
    expect(formatPendingCount(NAV_BADGE_MAX + 1)).toBe("9+");
    expect(formatPendingCount(250)).toBe("9+");
  });

  it("floors a fractional count", () => {
    expect(formatPendingCount(2.9)).toBe("2");
  });
});

describe("approvalsNavLabel", () => {
  it("is the plain label when nothing is pending", () => {
    expect(approvalsNavLabel(0)).toBe("Approvals");
    expect(approvalsNavLabel(-1)).toBe("Approvals");
  });

  it("uses the singular for a single pending task", () => {
    expect(approvalsNavLabel(1)).toBe("Approvals, 1 task needs review");
  });

  it("uses the plural for multiple pending tasks", () => {
    expect(approvalsNavLabel(4)).toBe("Approvals, 4 tasks need review");
  });

  it("announces the true count even past the visual cap", () => {
    expect(approvalsNavLabel(42)).toBe("Approvals, 42 tasks need review");
  });
});
