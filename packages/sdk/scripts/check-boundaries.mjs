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
  "Legal destination: @deepwork/domain public entry or packages/sdk/src/**. " +
  "Architecture: ARCHITECTURE.md#package-graph and " +
  "ARCHITECTURE.md#mechanical-enforcement. " +
  "Repair: pnpm --filter @deepwork/sdk check-architecture";

const FRAMEWORK_PACKAGES = /^(?:react|react-dom|next)(?:\/|$)/;
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
    path: "tests/fixtures/negative/ui-side-effect.fixture.ts",
    expectedCodes: [
      "DW-SDK-UI-IMPORT",
      "DW-SDK-IMPORT-NOT-ALLOWED",
    ],
  },
  {
    path: "tests/fixtures/negative/provider-side-effect.fixture.ts",
    expectedCodes: [
      "DW-SDK-PROVIDER-IMPORT",
      "DW-SDK-IMPORT-NOT-ALLOWED",
    ],
  },
  {
    path: "tests/fixtures/negative/raw-network.fixture.ts",
    expectedCodes: [
      "DW-SDK-NETWORK-IMPORT",
      "DW-SDK-NETWORK-API",
      "DW-SDK-IMPORT-NOT-ALLOWED",
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
      "DW-SDK-IMPORT-NOT-ALLOWED",
    ],
  },
  {
    path: "tests/fixtures/negative/path-and-zone-bypass.fixture.ts",
    expectedCodes: [
      "DW-SDK-PATH-ESCAPE",
      "DW-SDK-DEEP-IMPORT",
      "DW-SDK-FORBIDDEN-ZONE",
      "DW-SDK-IMPORT-NOT-ALLOWED",
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
    const allowedBare = specifier === "@deepwork/domain";

    if (bare && !allowedBare) {
      add(
        "DW-SDK-IMPORT-NOT-ALLOWED",
        `SDK dependency allowlist permits only @deepwork/domain; found ${specifier}`,
      );
    }
    if (specifier === "@deepwork/ui" || specifier.startsWith("@deepwork/ui/")) {
      add("DW-SDK-UI-IMPORT", `SDK cannot import UI package ${specifier}`);
    }
    if (specifier === "@deepwork/sdk" || specifier.startsWith("@deepwork/sdk/")) {
      add(
        "DW-SDK-SELF-IMPORT",
        `SDK source cannot self-import through ${specifier}`,
      );
    }
    if (/^@deepwork\/[^/]+\//.test(specifier)) {
      add(
        "DW-SDK-DEEP-IMPORT",
        `SDK cannot deep-import package path ${specifier}`,
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
    if (nodeBuiltins.has(specifier)) {
      add("DW-SDK-NODE-IMPORT", `SDK cannot import Node API ${specifier}`);
    }
    if (relative && !specifier.endsWith(".js")) {
      add(
        "DW-SDK-ESM-EXTENSION",
        `local runtime import requires a .js extension: ${specifier}`,
      );
    }
    if (
      (relative &&
        !isWithin(sourceRoot, resolve(dirname(sourceFile), specifier))) ||
      specifier.startsWith("/")
    ) {
      add(
        "DW-SDK-PATH-ESCAPE",
        `import escapes the package source boundary: ${specifier}`,
      );
    }
    if (
      FORBIDDEN_ZONE.test(specifier) ||
      FORBIDDEN_PACKAGES.test(specifier)
    ) {
      add(
        "DW-SDK-FORBIDDEN-ZONE",
        `SDK cannot import server, Tauri, route, fixture, generated, or database path ${specifier}`,
      );
    }
  }

  if (/\b(?:fetch|XMLHttpRequest|WebSocket|EventSource)\b/.test(source)) {
    add(
      "DW-SDK-NETWORK-API",
      "unreviewed SDK source cannot use raw network APIs",
    );
  }
  if (/\bprocess\.env\b|\bimport\.meta\.env\b/.test(source)) {
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
