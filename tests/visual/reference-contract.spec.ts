import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

import { expect, test } from "@playwright/test";
import sharp from "sharp";

interface Manifest {
  source: { commit: string };
  routes: Array<{
    name: string;
    path: string;
    canonicalPath: string;
    canonicalBaseline: string;
    maxPerceptualDelta: { desktop: number; phone: number };
    referenceSha256: { desktop: string; phone: string };
  }>;
}

function pngWidth(bytes: Buffer): number {
  if (bytes.toString("ascii", 1, 4) !== "PNG") throw new Error("Reference is not a PNG.");
  return bytes.readUInt32BE(16);
}

function sha256(bytes: Buffer): string {
  return createHash("sha256").update(bytes).digest("hex");
}

async function perceptualDelta(referencePath: string, canonicalPath: string): Promise<number> {
  const [referenceMetadata, canonicalMetadata] = await Promise.all([
    sharp(referencePath).metadata(),
    sharp(canonicalPath).metadata(),
  ]);
  const width = Math.min(referenceMetadata.width ?? 0, canonicalMetadata.width ?? 0);
  const height = Math.min(referenceMetadata.height ?? 0, canonicalMetadata.height ?? 0);
  if (width < 1 || height < 1) throw new Error("Visual comparison requires readable images.");
  const [reference, canonical] = await Promise.all(
    [referencePath, canonicalPath].map((path) =>
      sharp(path)
        .extract({ left: 0, top: 0, width, height })
        .removeAlpha()
        .toColourspace("srgb")
        .raw()
        .toBuffer(),
    ),
  );
  let total = 0;
  for (let index = 0; index < reference.length; index += 1) {
    total += Math.abs(reference[index] - canonical[index]);
  }
  return total / reference.length / 255;
}

test("the complete prototype route reference remains binding", async () => {
  const directory = join(process.cwd(), "tests/visual/reference/prototype");
  const manifest = JSON.parse(await readFile(join(directory, "manifest.json"), "utf8")) as Manifest;

  expect(manifest.source.commit).toBe("26c698b30ff08d5122cfaeedbd4a95296a7884f4");
  expect(manifest.routes).toHaveLength(12);
  for (const route of manifest.routes) {
    expect(route.canonicalPath, `${route.path} canonical mapping`).toMatch(/^\//);
    for (const viewport of ["desktop", "phone"] as const) {
      const referencePath = `${directory}/${viewport}/${route.name}.png`;
      const canonicalPath = join(
        process.cwd(),
        "tests/visual/expected/product-journey.spec.ts",
        `${viewport}-${route.canonicalBaseline}.png`,
      );
      const reference = await readFile(referencePath);
      expect(sha256(reference), `${route.path} ${viewport} source hash`).toBe(
        route.referenceSha256[viewport],
      );
      if (viewport === "desktop") {
        expect(pngWidth(reference), `${route.path} desktop reference width`).toBe(1440);
      } else {
        expect(pngWidth(reference), `${route.path} phone reference width`).toBeGreaterThanOrEqual(
          390,
        );
      }
      expect(
        await perceptualDelta(referencePath, canonicalPath),
        `${route.path} -> ${route.canonicalPath} ${viewport} visual delta`,
      ).toBeLessThanOrEqual(route.maxPerceptualDelta[viewport]);
    }
  }
});

test("the comparator detects brand-color and localized layout mutations", async ({}, testInfo) => {
  const baseline = testInfo.outputPath("comparator-baseline.png");
  const colorMutation = testInfo.outputPath("comparator-color.png");
  const layoutMutation = testInfo.outputPath("comparator-layout.png");
  const block = {
    input: { create: { width: 24, height: 24, channels: 3 as const, background: "#ef4444" } },
  };
  await Promise.all([
    sharp({ create: { width: 120, height: 80, channels: 3, background: "#2563eb" } })
      .composite([{ ...block, left: 8, top: 8 }])
      .png()
      .toFile(baseline),
    sharp({ create: { width: 120, height: 80, channels: 3, background: "#9333ea" } })
      .composite([{ ...block, left: 8, top: 8 }])
      .png()
      .toFile(colorMutation),
    sharp({ create: { width: 120, height: 80, channels: 3, background: "#2563eb" } })
      .composite([{ ...block, left: 72, top: 40 }])
      .png()
      .toFile(layoutMutation),
  ]);

  expect(await perceptualDelta(baseline, colorMutation)).toBeGreaterThan(0.1);
  expect(await perceptualDelta(baseline, layoutMutation)).toBeGreaterThan(0.03);
});
