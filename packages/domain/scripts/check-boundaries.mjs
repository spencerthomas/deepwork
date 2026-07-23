import { readFile, readdir } from "node:fs/promises";
import { extname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = resolve(
  fileURLToPath(new URL("../", import.meta.url)),
);
const sourceRoot = join(packageRoot, "src");

const FRAMEWORK_PACKAGES =
  /^(?:react|react-dom|next|vue|svelte)(?:\/|$)/;
const NETWORK_PACKAGES =
  /^(?:axios|ky|undici|eventsource|ws)(?:\/|$)/;
const PROVIDER_PACKAGES =
  /^(?:@langchain\/(?:core|langgraph-api|langgraph-sdk)|langchain|openai|@anthropic-ai\/sdk)(?:\/|$)/;

export const negativeFixtures = [
  {
    path: "tests/fixtures/negative/framework-side-effect.fixture.ts",
    expectedCodes: ["DW-DOMAIN-FRAMEWORK-IMPORT"],
  },
  {
    path: "tests/fixtures/negative/browser-network.fixture.ts",
    expectedCodes: [
      "DW-DOMAIN-BROWSER-API",
      "DW-DOMAIN-NETWORK-API",
    ],
  },
  {
    path: "tests/fixtures/negative/provider-network-side-effect.fixture.ts",
    expectedCodes: [
      "DW-DOMAIN-PROVIDER-IMPORT",
      "DW-DOMAIN-NETWORK-IMPORT",
    ],
  },
  {
    path: "tests/fixtures/negative/internal-node-environment-extension.fixture.ts",
    expectedCodes: [
      "DW-DOMAIN-INTERNAL-IMPORT",
      "DW-DOMAIN-NODE-IMPORT",
      "DW-DOMAIN-ESM-EXTENSION",
      "DW-DOMAIN-ENVIRONMENT",
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
    if (specifier.startsWith("@deepwork/")) {
      add(
        "DW-DOMAIN-INTERNAL-IMPORT",
        `domain cannot import internal package ${specifier}`,
      );
    }
    if (FRAMEWORK_PACKAGES.test(specifier)) {
      add(
        "DW-DOMAIN-FRAMEWORK-IMPORT",
        `domain cannot import framework package ${specifier}`,
      );
    }
    if (NETWORK_PACKAGES.test(specifier)) {
      add(
        "DW-DOMAIN-NETWORK-IMPORT",
        `domain cannot import network package ${specifier}`,
      );
    }
    if (PROVIDER_PACKAGES.test(specifier)) {
      add(
        "DW-DOMAIN-PROVIDER-IMPORT",
        `domain cannot import provider package ${specifier}`,
      );
    }
    if (specifier.startsWith("node:")) {
      add(
        "DW-DOMAIN-NODE-IMPORT",
        `domain cannot import Node API ${specifier}`,
      );
    }
    if (specifier.startsWith(".") && !specifier.endsWith(".js")) {
      add(
        "DW-DOMAIN-ESM-EXTENSION",
        `local runtime import requires a .js extension: ${specifier}`,
      );
    }
  }

  if (/\b(?:window|document|navigator|localStorage|sessionStorage)\b/.test(source)) {
    add(
      "DW-DOMAIN-BROWSER-API",
      "domain cannot use browser globals",
    );
  }
  if (/\b(?:fetch|XMLHttpRequest|WebSocket|EventSource)\b/.test(source)) {
    add(
      "DW-DOMAIN-NETWORK-API",
      "domain cannot use raw network APIs",
    );
  }
  if (/\bprocess\.env\b/.test(source)) {
    add(
      "DW-DOMAIN-ENVIRONMENT",
      "domain cannot read environment state",
    );
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
