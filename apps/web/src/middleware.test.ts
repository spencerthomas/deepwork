import { describe, expect, it } from "vitest";

import { sessionGateTarget } from "./middleware";

describe("sessionGateTarget", () => {
  it("allows the credential-free fixture journey without a session", () => {
    expect(sessionGateTarget("/tasks", false, true)).toBeNull();
    expect(sessionGateTarget("/tasks/new", false, true)).toBeNull();
  });

  it("keeps the fixture harness away from the API login screen", () => {
    expect(sessionGateTarget("/login", false, true)).toBe("/tasks");
  });

  it("requires a session for application routes in API mode", () => {
    expect(sessionGateTarget("/tasks", false, false)).toBe("/login");
    expect(sessionGateTarget("/login", false, false)).toBeNull();
  });

  it("keeps authenticated users out of the login screen in API mode", () => {
    expect(sessionGateTarget("/login", true, false)).toBe("/tasks");
    expect(sessionGateTarget("/tasks", true, false)).toBeNull();
  });
});
