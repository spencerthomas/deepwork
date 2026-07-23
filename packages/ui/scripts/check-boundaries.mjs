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
  "Legal destination: @deepwork/domain or React public entries, packages/ui/src/**, or contained package CSS assets. " +
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
  {
    path: "tests/fixtures/negative/computed-dynamic-import.fixture.ts",
    expectedCodes: ["DW-UI-DYNAMIC-IMPORT"],
  },
  {
    path: "tests/fixtures/negative/css-path-network-escape.fixture.css",
    expectedCodes: [
      "DW-UI-CSS-DYNAMIC-REFERENCE",
      "DW-UI-CSS-IMPORT-NOT-ALLOWED",
      "DW-UI-CSS-NETWORK-URL",
      "DW-UI-CSS-PATH-ESCAPE",
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

function unsafeDynamicImportCount(source) {
  let count = 0;
  const start =
    /\bimport(?:\s|\/\*[\s\S]*?\*\/|\/\/[^\r\n]*(?:\r?\n|$))*\(\s*/g;
  for (const match of source.matchAll(start)) {
    const argument = source.slice((match.index ?? 0) + match[0].length);
    const staticString =
      !/\/[*/]/.test(match[0]) &&
      /^(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')\s*\)/.test(argument);
    if (!staticString) count += 1;
  }
  return count;
}

export function inspectSource(
  source,
  sourceFile = join(sourceRoot, "__inspection__.ts"),
) {
  const violations = [];
  const add = (code, message) =>
    violations.push({ code, message: `${message}. ${help}` });

  for (let index = 0; index < unsafeDynamicImportCount(source); index += 1) {
    add(
      "DW-UI-DYNAMIC-IMPORT",
      "UI cannot use a computed or template-literal dynamic import because its destination cannot be statically enforced",
    );
  }

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

function staticCssReference(value) {
  const trimmed = value.trim();
  if (
    (trimmed.startsWith("\"") && trimmed.endsWith("\"")) ||
    (trimmed.startsWith("'") && trimmed.endsWith("'"))
  ) {
    const unquoted = trimmed.slice(1, -1);
    return /[\\\r\n]/.test(unquoted) ? undefined : unquoted;
  }
  return /^[^\s"'()\\]+$/.test(trimmed) ? trimmed : undefined;
}

function importReference(clause) {
  const trimmed = clause.trim();
  if (/^url\s*\(/i.test(trimmed)) {
    const match = /^url\s*\((.*)\)(?:\s+.*)?$/i.exec(trimmed);
    return match === null ? undefined : staticCssReference(match[1]);
  }
  const match = /^(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')/.exec(trimmed);
  return match === null ? undefined : staticCssReference(match[0]);
}

function inspectCssReference(reference, sourceFile, add, imported) {
  if (
    reference !== reference.trim() ||
    /[\u0000-\u001f\u007f]/.test(reference)
  ) {
    add(
      "DW-UI-CSS-DYNAMIC-REFERENCE",
      "UI CSS reference cannot contain hidden whitespace or control characters",
    );
    return;
  }
  if (/^(?:[a-z][a-z0-9+.-]*:|\/\/)/i.test(reference)) {
    add(
      "DW-UI-CSS-NETWORK-URL",
      `UI CSS cannot load an external or scheme URL: ${reference}`,
    );
    return;
  }
  if (reference.startsWith("#")) return;
  if (
    /%(?:2e|2f|5c)/i.test(reference) ||
    reference.startsWith("/") ||
    !isWithin(
      packageRoot,
      resolve(dirname(sourceFile), reference.split(/[?#]/, 1)[0]),
    )
  ) {
    add(
      "DW-UI-CSS-PATH-ESCAPE",
      `UI CSS reference escapes or encodes traversal outside the package boundary: ${reference}`,
    );
  }
  if (
    imported &&
    (!reference.startsWith(".") || !reference.split(/[?#]/, 1)[0].endsWith(".css"))
  ) {
    add(
      "DW-UI-CSS-IMPORT-NOT-ALLOWED",
      `UI CSS @import must be a contained relative .css path: ${reference}`,
    );
  }
}

export function inspectCss(
  source,
  sourceFile = join(packageRoot, "__inspection__.css"),
) {
  const violations = [];
  const add = (code, message) =>
    violations.push({ code, message: `${message}. ${help}` });
  const inspectableSource = source.replace(/\/\*[\s\S]*?\*\//g, " ");

  for (const match of inspectableSource.matchAll(/@import\s+([^;]+);/gi)) {
    const reference = importReference(match[1]);
    if (reference === undefined) {
      add(
        "DW-UI-CSS-DYNAMIC-REFERENCE",
        "UI CSS @import must use a statically inspectable quoted or url() path",
      );
    } else {
      inspectCssReference(reference, sourceFile, add, true);
    }
  }
  for (const match of inspectableSource.matchAll(/\burl\s*\(\s*([^)]*)\)/gi)) {
    const reference = staticCssReference(match[1]);
    if (reference === undefined) {
      add(
        "DW-UI-CSS-DYNAMIC-REFERENCE",
        "UI CSS url() must use a statically inspectable path",
      );
    } else {
      inspectCssReference(reference, sourceFile, add, false);
    }
  }

  return violations;
}

async function sourceFiles(directory, extensions = [".ts", ".tsx"]) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await sourceFiles(path, extensions)));
    }
    if (entry.isFile() && extensions.includes(extname(entry.name))) {
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
  const rootCssFiles = (await readdir(packageRoot, { withFileTypes: true }))
    .filter((entry) => entry.isFile() && extname(entry.name) === ".css")
    .map((entry) => join(packageRoot, entry.name));
  for (const file of [
    ...rootCssFiles,
    ...(await sourceFiles(sourceRoot, [".css"])),
  ]) {
    assertNoViolations(
      file,
      inspectCss(await readFile(file, "utf8"), file),
    );
  }

  for (const fixture of negativeFixtures) {
    const file = join(packageRoot, fixture.path);
    const inspect = extname(file) === ".css" ? inspectCss : inspectSource;
    const codes = new Set(
      inspect(await readFile(file, "utf8"), file).map(({ code }) => code),
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
