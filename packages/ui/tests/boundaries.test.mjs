import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import {
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
      const codes = inspectSource(source).map(({ code }) => code);
      expect(codes).toEqual(expect.arrayContaining(fixture.expectedCodes));
    });
  }
});
