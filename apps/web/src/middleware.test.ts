import { NextRequest } from "next/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

const runtimeConfig = vi.hoisted(() => ({
  demoMode: undefined as string | undefined,
}));

vi.mock("../config/runtime", () => ({
  webRuntimeConfig: runtimeConfig,
}));

import { middleware, sessionGateTarget } from "./middleware";

function request(pathname: string, hasSession = false): NextRequest {
  return new NextRequest(`https://deepwork.test${pathname}`, {
    headers: hasSession ? { cookie: "deepwork_session=test-session" } : undefined,
  });
}

describe("middleware", () => {
  beforeEach(() => {
    runtimeConfig.demoMode = undefined;
  });

  it("allows every destination in the credential-free fixture shell", () => {
    runtimeConfig.demoMode = "fixture";

    for (const pathname of [
      "/tasks",
      "/approvals",
      "/agents",
      "/schedules",
      "/activity",
      "/settings",
    ]) {
      expect(middleware(request(pathname)).status).toBe(200);
    }
  });

  it("keeps fixture users away from the API login screen", () => {
    runtimeConfig.demoMode = "fixture";

    const response = middleware(request("/login"));

    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe("https://deepwork.test/tasks");
  });

  it("redirects unauthenticated API-mode users to login", () => {
    const response = middleware(request("/tasks"));

    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe("https://deepwork.test/login");
  });

  it("redirects authenticated API-mode users away from login", () => {
    const response = middleware(request("/login", true));

    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe("https://deepwork.test/tasks");
  });
});

describe("sessionGateTarget", () => {
  it("allows the credential-free fixture journey without a session", () => {
    expect(sessionGateTarget("/tasks", false, true)).toBeNull();
    expect(sessionGateTarget("/tasks/new", false, true)).toBeNull();
    expect(sessionGateTarget("/approvals", false, true)).toBeNull();
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
