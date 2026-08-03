import { readFile } from "node:fs/promises";
import { join } from "node:path";

import { expect, test } from "@playwright/test";

interface Manifest {
  source: { commit: string };
  routes: Array<{ name: string; path: string }>;
}

function pngWidth(bytes: Buffer): number {
  if (bytes.toString("ascii", 1, 4) !== "PNG") throw new Error("Reference is not a PNG.");
  return bytes.readUInt32BE(16);
}

test("the complete prototype route reference remains binding", async () => {
  const directory = join(process.cwd(), "tests/visual/reference/prototype");
  const manifest = JSON.parse(
    await readFile(join(directory, "manifest.json"), "utf8"),
  ) as Manifest;

  expect(manifest.source.commit).toBe("26c698b30ff08d5122cfaeedbd4a95296a7884f4");
  expect(manifest.routes).toHaveLength(12);
  for (const route of manifest.routes) {
    const desktop = await readFile(`${directory}/desktop/${route.name}.png`);
    const phone = await readFile(`${directory}/phone/${route.name}.png`);
    expect(pngWidth(desktop), `${route.path} desktop reference width`).toBe(1440);
    // Full-page prototype captures preserve its known horizontal overflow.
    expect(pngWidth(phone), `${route.path} phone reference width`).toBeGreaterThanOrEqual(390);
  }
});
