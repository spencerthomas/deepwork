import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import {
  inspectCss,
  inspectSource,
  negativeFixtures,
} from "../scripts/check-boundaries.mjs";

const packageRoot = fileURLToPath(new URL("../", import.meta.url));

describe("UI negative boundary fixtures", () => {
  for (const fixture of negativeFixtures) {
    it(`reports actionable rules for ${fixture.path}`, async () => {
      const source = await readFile(
        join(packageRoot, fixture.path),
        "utf8",
      );
      const inspect = fixture.path.endsWith(".css")
        ? inspectCss
        : inspectSource;
      const violations = inspect(
        source,
        join(packageRoot, fixture.path),
      );
      const codes = violations.map(({ code }) => code);
      expect(codes).toEqual(expect.arrayContaining(fixture.expectedCodes));
      for (const { message } of violations) {
        expect(message).toContain("Legal destination:");
        expect(message).toContain("ARCHITECTURE.md#package-graph");
        expect(message).toContain(
          "pnpm --filter @deepwork/ui check-architecture",
        );
      }
    });
  }
});
