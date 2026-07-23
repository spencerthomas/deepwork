import { readFile, readdir } from "node:fs/promises";
import { extname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = resolve(
  fileURLToPath(new URL("../", import.meta.url)),
);
const sourceRoot = join(packageRoot, "src");

const FRAMEWORK_PACKAGES =
  /^(?:react|react-dom|next)(?:\/|$)/;
const NETWORK_PACKAGES =
  /^(?:axios|ky|undici|eventsource|ws)(?:\/|$)/;
const PROVIDER_PACKAGES =
  /^(?:@langchain\/(?:core|langgraph-api|langgraph-sdk)|langchain|openai|@anthropic-ai\/sdk)(?:\/|$)/;

export const negativeFixtures = [
  {
    path: "tests/fixtures/negative/ui-side-effect.fixture.ts",
    expectedCodes: ["DW-SDK-UI-IMPORT"],
  },
  {
    path: "tests/fixtures/negative/provider-side-effect.fixture.ts",
    expectedCodes: ["DW-SDK-PROVIDER-IMPORT"],
  },
  {
    path: "tests/fixtures/negative/raw-network.fixture.ts",
    expectedCodes: [
      "DW-SDK-NETWORK-IMPORT",
      "DW-SDK-NETWORK-API",
    ],
  },
  {
    path: "tests/fixtures/negative/self-framework-node-environment-extension.fixture.ts",
    expectedCodes: [
      "DW-SDK-SELF-IMPORT",
      "DW-SDK-FRAMEWORK-IMPORT",
      "DW-SDK-NODE-IMPORT",
      "DW-SDK-ESM-EXTENSION",
      "DW-SDK-ENVIRONMENT",
    ],
  },
];

function importSpecifiers(source) {
  const specifiers = new Set();
  for (const pattern of [
    /\bfrom\s+["']([^"']+)["']/g,
    /\bimport\s*(?:\(\s*)?["']([^"']+)["']/g,
  ]) {
    for (const match of source.matchAll(pattern)) specifiers.add(match[1]);
  }
  return [...specifiers];
}

export function inspectSource(source) {
  const violations = [];
  const add = (code, message) => violations.push({ code, message });

  for (const specifier of importSpecifiers(source)) {
    if (specifier === "@deepwork/ui" || specifier.startsWith("@deepwork/ui/")) {
      add("DW-SDK-UI-IMPORT", `SDK cannot import UI package ${specifier}`);
    }
    if (specifier === "@deepwork/sdk" || specifier.startsWith("@deepwork/sdk/")) {
      add(
        "DW-SDK-SELF-IMPORT",
        `SDK source cannot self-import through ${specifier}`,
      );
    }
    if (FRAMEWORK_PACKAGES.test(specifier)) {
      add(
        "DW-SDK-FRAMEWORK-IMPORT",
        `SDK cannot import framework package ${specifier}`,
      );
    }
    if (NETWORK_PACKAGES.test(specifier)) {
      add(
        "DW-SDK-NETWORK-IMPORT",
        `unreviewed SDK source cannot import raw network package ${specifier}`,
      );
    }
    if (PROVIDER_PACKAGES.test(specifier)) {
      add(
        "DW-SDK-PROVIDER-IMPORT",
        `SDK cannot import provider package ${specifier}`,
      );
    }
    if (specifier.startsWith("node:")) {
      add("DW-SDK-NODE-IMPORT", `SDK cannot import Node API ${specifier}`);
    }
    if (specifier.startsWith(".") && !specifier.endsWith(".js")) {
      add(
        "DW-SDK-ESM-EXTENSION",
        `local runtime import requires a .js extension: ${specifier}`,
      );
    }
  }

  if (/\b(?:fetch|XMLHttpRequest|WebSocket|EventSource)\b/.test(source)) {
    add(
      "DW-SDK-NETWORK-API",
      "unreviewed SDK source cannot use raw network APIs",
    );
  }
  if (/\bprocess\.env\b/.test(source)) {
    add("DW-SDK-ENVIRONMENT", "SDK cannot read environment state");
  }

  return violations;
}

async function sourceFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) files.push(...(await sourceFiles(path)));
    if (entry.isFile() && [".ts", ".tsx"].includes(extname(entry.name))) {
      files.push(path);
    }
  }
  return files;
}

function assertNoViolations(file, violations) {
  if (violations.length === 0) return;
  const details = violations
    .map(({ code, message }) => `${code}: ${message}`)
    .join("\n");
  throw new Error(`Boundary violation in ${file}:\n${details}`);
}

export async function checkBoundaries() {
  for (const file of await sourceFiles(sourceRoot)) {
    assertNoViolations(file, inspectSource(await readFile(file, "utf8")));
  }

  for (const fixture of negativeFixtures) {
    const file = join(packageRoot, fixture.path);
    const codes = new Set(
      inspectSource(await readFile(file, "utf8")).map(({ code }) => code),
    );
    for (const expectedCode of fixture.expectedCodes) {
      if (!codes.has(expectedCode)) {
        throw new Error(
          `Negative fixture ${fixture.path} did not trigger ${expectedCode}.`,
        );
      }
    }
  }
}

if (
  process.argv[1] !== undefined &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  await checkBoundaries();
}
