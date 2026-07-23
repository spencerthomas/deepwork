// @vitest-environment node

import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import { describe, expect, it } from "vitest";

import { inspectCss, inspectSource, negativeFixtures } from "../scripts/check-boundaries.mjs";

const packageRoot = fileURLToPath(new URL("../", import.meta.url));

describe("UI negative boundary fixtures", () => {
  for (const fixture of negativeFixtures) {
    it(`reports actionable rules for ${fixture.path}`, async () => {
      const source = fixture.source ?? (await readFile(join(packageRoot, fixture.path), "utf8"));
      const inspect = fixture.path.endsWith(".css") ? inspectCss : inspectSource;
      const violations = inspect(source, join(packageRoot, fixture.path));
      const codes = violations.map(({ code }) => code);
      expect(codes).toEqual(expect.arrayContaining(fixture.expectedCodes));
      for (const { message } of violations) {
        expect(message).toContain("Legal destination:");
        expect(message).toContain("ARCHITECTURE.md#package-graph");
        expect(message).toContain("pnpm --filter @deepwork/ui check-architecture");
      }
    });
  }

  it("fails closed on malformed source with actionable help", () => {
    let failure;
    try {
      inspectSource("import/* unterminated");
    } catch (error) {
      failure = error;
    }
    expect(failure).toBeInstanceOf(SyntaxError);
    expect(failure.message).toContain("Legal destination:");
    expect(failure.message).toContain("ARCHITECTURE.md#package-graph");
    expect(failure.message).toContain("pnpm --filter @deepwork/ui check-architecture");
  });

  it("normalizes contained and escaping file URL source locations", () => {
    const sourceFile = pathToFileURL(join(packageRoot, "src", "file-url.fixture.ts"));
    const contained = inspectSource('import "./status-panel.js";', sourceFile);
    const escaping = inspectSource('import "../../outside.js";', sourceFile.href);

    expect(contained.map(({ code }) => code)).not.toContain("DW-UI-PATH-ESCAPE");
    expect(escaping.map(({ code }) => code)).toContain("DW-UI-PATH-ESCAPE");
  });

  it("rejects non-file URL source locations", () => {
    expect(() => inspectCss(".fixture {}", new URL("https://fixture.invalid/theme.css"))).toThrow(
      "Boundary scanner source must be a local file path.",
    );
    expect(() => inspectCss(".fixture {}", "https://fixture.invalid/theme.css")).toThrow(
      "Boundary scanner source must be a local file path.",
    );
  });

  it("preserves ordinary path inputs containing colons", () => {
    const posixPath = join(packageRoot, "src", "fixture:local.ts");
    const windowsPath = String.raw`C:\deepwork\packages\ui\src\fixture.ts`;

    expect(inspectSource('import "./status-panel.js";', posixPath)).toEqual([]);
    expect(() => inspectSource("export {};", windowsPath)).not.toThrow();
  });
});
