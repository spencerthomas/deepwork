import { describe, expect, it } from "vitest";

import { schedulePresentation } from "./schedule-presentation";

describe("schedulePresentation", () => {
  it("does not infer a capability while status is loading", () => {
    const copy = schedulePresentation(true, "unknown");
    expect(copy.heading).toBe("Checking schedule availability");
    expect(copy.description).toContain("No execution or durability state is assumed");
  });

  it("fails closed when durable jobs are unknown", () => {
    const copy = schedulePresentation(false, "unknown");
    expect(copy.heading).toBe("Schedule availability is unknown");
    expect(copy.description).toContain("Nothing is assumed");
  });

  it("explains reported unavailability", () => {
    const copy = schedulePresentation(false, "unavailable");
    expect(copy.heading).toBe("Schedules are unavailable");
    expect(copy.description).toContain("runtime reports durable jobs unavailable");
  });

  it("acknowledges available durable jobs without enabling unshipped authoring", () => {
    const copy = schedulePresentation(false, "available");
    expect(copy.heading).toBe("Durable jobs are reported available");
    expect(copy.description).toContain("schedule authoring has not shipped");
    expect(copy.actionReason).toContain("has not shipped");
    expect(copy.description).not.toContain("durable jobs unavailable");
  });
});
