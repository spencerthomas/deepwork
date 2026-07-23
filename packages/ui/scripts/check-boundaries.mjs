import { builtinModules } from "node:module";
import { readFile, readdir } from "node:fs/promises";
import { dirname, extname, join, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = resolve(fileURLToPath(new URL("../", import.meta.url)));
const sourceRoot = join(packageRoot, "src");
const nodeBuiltins = new Set(
  builtinModules.flatMap((name) => [name, `node:${name}`]),
);
const help =
  "Legal destination: @deepwork/domain or React public entries, or packages/ui/src/**. " +
  "Architecture: ARCHITECTURE.md#package-graph and " +
  "ARCHITECTURE.md#mechanical-enforcement. " +
  "Repair: pnpm --filter @deepwork/ui check-architecture";

const NETWORK_PACKAGES =
  /^(?:axios|ky|undici|eventsource|ws)(?:\/|$)/;
const PROVIDER_PACKAGES =
  /^(?:@langchain\/(?:core|langgraph-api|langgraph-sdk)|langchain|openai|@anthropic-ai\/sdk)(?:\/|$)/;
const FORBIDDEN_ZONE =
  /(?:^|\/)(?:server|routes?|fixtures?|generated|database|db)(?:\/|$)/;
const FORBIDDEN_PACKAGES =
  /^(?:server-only|@tauri-apps\/|pg$|postgres$|better-sqlite3$|@prisma\/client$|drizzle-orm$)/;

export const negativeFixtures = [
  {
    path: "tests/fixtures/negative/sdk-side-effect.fixture.ts",
    expectedCodes: [
      "DW-UI-SDK-IMPORT",
      "DW-UI-IMPORT-NOT-ALLOWED",
    ],
  },
  {
    path: "tests/fixtures/negative/provider-side-effect.fixture.ts",
    expectedCodes: [
      "DW-UI-PROVIDER-IMPORT",
      "DW-UI-IMPORT-NOT-ALLOWED",
    ],
  },
  {
    path: "tests/fixtures/negative/raw-network.fixture.ts",
    expectedCodes: [
      "DW-UI-NETWORK-IMPORT",
      "DW-UI-NETWORK-API",
      "DW-UI-IMPORT-NOT-ALLOWED",
    ],
  },
  {
    path: "tests/fixtures/negative/self-next-node-environment-extension-html.fixture.ts",
    expectedCodes: [
      "DW-UI-SELF-IMPORT",
      "DW-UI-NEXT-IMPORT",
      "DW-UI-NODE-IMPORT",
      "DW-UI-ESM-EXTENSION",
      "DW-UI-ENVIRONMENT",
      "DW-UI-RAW-HTML",
      "DW-UI-IMPORT-NOT-ALLOWED",
    ],
  },
  {
    path: "tests/fixtures/negative/path-and-zone-bypass.fixture.ts",
    expectedCodes: [
      "DW-UI-PATH-ESCAPE",
      "DW-UI-DEEP-IMPORT",
      "DW-UI-FORBIDDEN-ZONE",
      "DW-UI-IMPORT-NOT-ALLOWED",
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

function isWithin(root, target) {
  return target === root || target.startsWith(`${root}${sep}`);
}

export function inspectSource(
  source,
  sourceFile = join(sourceRoot, "__inspection__.ts"),
) {
  const violations = [];
  const add = (code, message) =>
    violations.push({ code, message: `${message}. ${help}` });

  for (const specifier of importSpecifiers(source)) {
    const relative = specifier.startsWith(".");
    const bare = !relative && !specifier.startsWith("/");
    const allowedBare =
      specifier === "@deepwork/domain" ||
      specifier === "react" ||
      specifier === "react/jsx-runtime" ||
      specifier === "react/jsx-dev-runtime";

    if (bare && !allowedBare) {
      add(
        "DW-UI-IMPORT-NOT-ALLOWED",
        `UI dependency allowlist permits only @deepwork/domain and React public entries; found ${specifier}`,
      );
    }
    if (specifier === "@deepwork/sdk" || specifier.startsWith("@deepwork/sdk/")) {
      add("DW-UI-SDK-IMPORT", `UI cannot import SDK package ${specifier}`);
    }
    if (specifier === "@deepwork/ui" || specifier.startsWith("@deepwork/ui/")) {
      add(
        "DW-UI-SELF-IMPORT",
        `UI source cannot self-import through ${specifier}`,
      );
    }
    if (/^@deepwork\/[^/]+\//.test(specifier)) {
      add(
        "DW-UI-DEEP-IMPORT",
        `UI cannot deep-import package path ${specifier}`,
      );
    }
    if (specifier === "next" || specifier.startsWith("next/")) {
      add("DW-UI-NEXT-IMPORT", `UI cannot import Next.js package ${specifier}`);
    }
    if (NETWORK_PACKAGES.test(specifier)) {
      add(
        "DW-UI-NETWORK-IMPORT",
        `UI cannot import network package ${specifier}`,
      );
    }
    if (PROVIDER_PACKAGES.test(specifier)) {
      add(
        "DW-UI-PROVIDER-IMPORT",
        `UI cannot import provider package ${specifier}`,
      );
    }
    if (nodeBuiltins.has(specifier)) {
      add("DW-UI-NODE-IMPORT", `UI cannot import Node API ${specifier}`);
    }
    if (
      relative &&
      !specifier.endsWith(".js") &&
      !specifier.endsWith(".css")
    ) {
      add(
        "DW-UI-ESM-EXTENSION",
        `local runtime import requires a .js or .css extension: ${specifier}`,
      );
    }
    if (
      (relative &&
        !isWithin(sourceRoot, resolve(dirname(sourceFile), specifier))) ||
      specifier.startsWith("/")
    ) {
      add(
        "DW-UI-PATH-ESCAPE",
        `import escapes the package source boundary: ${specifier}`,
      );
    }
    if (
      FORBIDDEN_ZONE.test(specifier) ||
      FORBIDDEN_PACKAGES.test(specifier)
    ) {
      add(
        "DW-UI-FORBIDDEN-ZONE",
        `UI cannot import server, Tauri, route, fixture, generated, or database path ${specifier}`,
      );
    }
  }

  if (/\b(?:fetch|XMLHttpRequest|WebSocket|EventSource)\b/.test(source)) {
    add("DW-UI-NETWORK-API", "UI cannot use raw network APIs");
  }
  if (/\bprocess\.env\b|\bimport\.meta\.env\b/.test(source)) {
    add("DW-UI-ENVIRONMENT", "UI cannot read environment state");
  }
  if (/\bdangerouslySetInnerHTML\b|\.innerHTML\b|\binnerHTML\s*=/.test(source)) {
    add("DW-UI-RAW-HTML", "UI cannot enable raw HTML rendering");
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
    assertNoViolations(
      file,
      inspectSource(await readFile(file, "utf8"), file),
    );
  }

  for (const fixture of negativeFixtures) {
    const file = join(packageRoot, fixture.path);
    const codes = new Set(
      inspectSource(await readFile(file, "utf8"), file).map(({ code }) => code),
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
