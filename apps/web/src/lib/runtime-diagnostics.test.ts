import { describe, expect, it } from "vitest";

import type { DemoStatus } from "./demo-status";
import { formatRuntimeDiagnostics } from "./runtime-diagnostics";

const status: DemoStatus = {
  mode: "api",
  evidenceClass: "live",
  capabilities: [
    { name: "local_task_loop", state: "available" },
    { name: "durable_jobs", state: "unavailable" },
  ],
  safeReason: "Local task loop is available; durability is not.",
  source: "api",
};

describe("formatRuntimeDiagnostics", () => {
  it("renders connection, capabilities, and evidence from a reported status", () => {
    const markdown = formatRuntimeDiagnostics({
      mode: "api",
      connectionTarget: "http://127.0.0.1:8000",
      status,
    });

    expect(markdown).toContain("# Runtime diagnostics");
    expect(markdown).toContain("- Client mode: api");
    expect(markdown).toContain("- Connection target: http://127.0.0.1:8000");
    expect(markdown).toContain("- local_task_loop: available");
    expect(markdown).toContain("- durable_jobs: unavailable");
    expect(markdown).toContain("- Evidence class: live");
    expect(markdown).toContain("- Status source: api");
    expect(markdown).toContain("- Safe reason: Local task loop is available; durability is not.");
    expect(markdown.endsWith("\n")).toBe(true);
  });

  it("states an unavailable status honestly instead of fabricating capabilities", () => {
    const markdown = formatRuntimeDiagnostics({
      mode: "api",
      connectionTarget: "http://127.0.0.1:8000",
      status: undefined,
    });

    expect(markdown).toContain("Runtime status unavailable");
    expect(markdown).toContain("- Evidence class: unknown");
    expect(markdown).toContain("- Status source: unknown");
    // No capability lines are fabricated when the status could not be read.
    expect(markdown).not.toContain("local_task_loop");
    expect(markdown).not.toContain(": available");
  });

  it("neutralizes active Markdown/HTML in server-provided fields", () => {
    const markdown = formatRuntimeDiagnostics({
      mode: "api",
      connectionTarget: "http://127.0.0.1:8000",
      status: {
        ...status,
        safeReason: "See ![x](http://evil/x) and <img src=y>",
        capabilities: [{ name: "weird`name", state: "available" }],
      },
    });

    // The bracket/angle construct-openers are backslash-escaped (parens are
    // left as-is), so the image and HTML are defused and paste as literal text.
    expect(markdown).toContain("See !\\[x\\](http://evil/x) and \\<img src=y\\>");
    expect(markdown).toContain("weird\\`name: available");
    expect(markdown).not.toContain("![x](http://evil/x)");
  });
});
