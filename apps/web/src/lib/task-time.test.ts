import { describe, expect, it } from "vitest";

import { formatTaskAge } from "./task-time";

const NOW = Date.parse("2026-07-24T12:00:00Z");

describe("formatTaskAge", () => {
  it("renders coarse relative buckets from the real creation instant", () => {
    expect(formatTaskAge("2026-07-24T11:59:30Z", NOW)).toBe("just now");
    expect(formatTaskAge("2026-07-24T11:45:00Z", NOW)).toBe("15m ago");
    expect(formatTaskAge("2026-07-24T09:00:00Z", NOW)).toBe("3h ago");
    expect(formatTaskAge("2026-07-19T12:00:00Z", NOW)).toBe("5d ago");
    expect(formatTaskAge("2026-05-24T12:00:00Z", NOW)).toBe("2mo ago");
    expect(formatTaskAge("2024-07-24T12:00:00Z", NOW)).toBe("2y ago");
  });

  it("returns undefined for missing, unparseable, or future timestamps", () => {
    expect(formatTaskAge(undefined, NOW)).toBeUndefined();
    expect(formatTaskAge("not-a-date", NOW)).toBeUndefined();
    // A future creation time is defensively suppressed rather than shown as "in".
    expect(formatTaskAge("2026-07-24T12:00:30Z", NOW)).toBeUndefined();
  });
});
