import { builtinModules } from "node:module";
import { readFile, readdir } from "node:fs/promises";
import { dirname, extname, join, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

// TypeScript 7 has no API; the wrapper is pinned and its parser is asserted below.
import ts from "@typescript/typescript6";

const packageRoot = resolve(fileURLToPath(new URL("../", import.meta.url)));
const sourceRoot = join(packageRoot, "src");
const nodeBuiltins = new Set(builtinModules.flatMap((name) => [name, `node:${name}`]));
const help =
  "Legal destination: @deepwork/domain or React public entries, packages/ui/src/**, or contained package CSS assets. " +
  "Architecture: ARCHITECTURE.md#package-graph and " +
  "ARCHITECTURE.md#mechanical-enforcement. " +
  "Repair: pnpm --filter @deepwork/ui check-architecture";

const NETWORK_PACKAGES = /^(?:axios|ky|undici|eventsource|ws)(?:\/|$)/;
const PROVIDER_PACKAGES =
  /^(?:@langchain\/(?:core|langgraph-api|langgraph-sdk)|langchain|openai|@anthropic-ai\/sdk)(?:\/|$)/;
const FORBIDDEN_ZONE = /(?:^|\/)(?:server|routes?|fixtures?|generated|database|db)(?:\/|$)/;
const FORBIDDEN_PACKAGES =
  /^(?:server-only|@tauri-apps\/|pg$|postgres$|better-sqlite3$|@prisma\/client$|drizzle-orm$)/;

const dynamicImportLineTerminators = [
  ["lf", "\n"],
  ["crlf", "\r\n"],
  ["cr", "\r"],
  ["line-separator", "\u2028"],
  ["paragraph-separator", "\u2029"],
];
const unsafeDynamicArguments = [
  ["computed", "moduleName"],
  ["template", "`./${moduleName}`"],
];

function dynamicImportLineCommentFixtures(expectedCode) {
  return dynamicImportLineTerminators.flatMap(([terminatorName, terminator]) =>
    unsafeDynamicArguments.map(([argumentName, argument]) => ({
      path:
        `tests/fixtures/negative/in-memory/dynamic-import-` +
        `${terminatorName}-${argumentName}.fixture.ts`,
      source:
        'const moduleName = "./status-panel.js"; void import// fixture' +
        terminator +
        `(${argument});`,
      expectedCodes: [expectedCode],
    })),
  );
}

export const negativeFixtures = [
  {
    path: "tests/fixtures/negative/sdk-side-effect.fixture.ts",
    expectedCodes: ["DW-UI-SDK-IMPORT", "DW-UI-IMPORT-NOT-ALLOWED"],
  },
  {
    path: "tests/fixtures/negative/provider-side-effect.fixture.ts",
    expectedCodes: ["DW-UI-PROVIDER-IMPORT", "DW-UI-IMPORT-NOT-ALLOWED"],
  },
  {
    path: "tests/fixtures/negative/raw-network.fixture.ts",
    expectedCodes: ["DW-UI-NETWORK-IMPORT", "DW-UI-NETWORK-API", "DW-UI-IMPORT-NOT-ALLOWED"],
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
    path: "tests/fixtures/negative/in-memory/commented-static-import.fixture.ts",
    source: 'import/* fixture */"@deepwork/sdk";',
    expectedCodes: ["DW-UI-SDK-IMPORT", "DW-UI-IMPORT-NOT-ALLOWED"],
  },
  {
    path: "tests/fixtures/negative/in-memory/commented-static-export.fixture.ts",
    source: 'export { unavailableQueryPort } from/* fixture */"@deepwork/sdk";',
    expectedCodes: ["DW-UI-SDK-IMPORT", "DW-UI-IMPORT-NOT-ALLOWED"],
  },
  {
    path: "tests/fixtures/negative/in-memory/import-equals.fixture.ts",
    source: 'import legacy = require("@deepwork/sdk"); void legacy;',
    expectedCodes: ["DW-UI-DYNAMIC-IMPORT", "DW-UI-SDK-IMPORT", "DW-UI-IMPORT-NOT-ALLOWED"],
  },
  {
    path: "tests/fixtures/negative/in-memory/commonjs-require.fixture.ts",
    source: 'const legacy = require("@deepwork/sdk"); void legacy;',
    expectedCodes: ["DW-UI-DYNAMIC-IMPORT", "DW-UI-SDK-IMPORT", "DW-UI-IMPORT-NOT-ALLOWED"],
  },
  {
    path: "tests/fixtures/negative/in-memory/import-type.fixture.ts",
    source: 'type Legacy = import("@deepwork/sdk").SdkResult; void 0;',
    expectedCodes: ["DW-UI-SDK-IMPORT", "DW-UI-IMPORT-NOT-ALLOWED"],
  },
  ...dynamicImportLineCommentFixtures("DW-UI-DYNAMIC-IMPORT"),
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

function moduleImports(source, sourceFile) {
  if (ts.version !== "6.0.3") {
    throw new Error(
      `Boundary scanner requires resolved TypeScript parser 6.0.3; found ${ts.version}. ${help}`,
    );
  }
  const scriptKind =
    extname(sourceFile).toLowerCase() === ".tsx" ? ts.ScriptKind.TSX : ts.ScriptKind.TS;
  const transpileResult = ts.transpileModule(source, {
    compilerOptions: {
      jsx: ts.JsxEmit.Preserve,
      module: ts.ModuleKind.Preserve,
      target: ts.ScriptTarget.ESNext,
    },
    fileName: sourceFile,
    reportDiagnostics: true,
  });
  if (
    (transpileResult.diagnostics ?? []).some(
      ({ category }) => category === ts.DiagnosticCategory.Error,
    )
  ) {
    throw new SyntaxError(
      `Boundary scanner cannot safely parse ${sourceFile}; fix TypeScript syntax before retrying. ${help}`,
    );
  }
  const sourceNode = ts.createSourceFile(
    sourceFile,
    source,
    ts.ScriptTarget.Latest,
    true,
    scriptKind,
  );

  const specifiers = new Set();
  let unsafeDynamicImportCount = 0;
  const addSpecifier = (node) => {
    if (node !== undefined && ts.isStringLiteral(node)) {
      specifiers.add(node.text);
      return true;
    }
    return false;
  };
  const visit = (node) => {
    if (ts.isImportDeclaration(node)) {
      addSpecifier(node.moduleSpecifier);
    } else if (ts.isExportDeclaration(node)) {
      addSpecifier(node.moduleSpecifier);
    } else if (
      ts.isImportEqualsDeclaration(node) &&
      ts.isExternalModuleReference(node.moduleReference)
    ) {
      addSpecifier(node.moduleReference.expression);
      unsafeDynamicImportCount += 1;
    } else if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword) {
      const argument = node.arguments[0];
      const staticString = addSpecifier(argument);
      if (!staticString || node.arguments.length !== 1) {
        unsafeDynamicImportCount += 1;
      }
    } else if (ts.isImportTypeNode(node)) {
      const argument = node.argument;
      if (!ts.isLiteralTypeNode(argument) || !addSpecifier(argument.literal)) {
        unsafeDynamicImportCount += 1;
      }
    } else if (
      ts.isCallExpression(node) &&
      ts.isIdentifier(node.expression) &&
      node.expression.text === "require"
    ) {
      addSpecifier(node.arguments[0]);
      unsafeDynamicImportCount += 1;
    }
    ts.forEachChild(node, visit);
  };
  visit(sourceNode);

  return {
    specifiers: [...specifiers],
    unsafeDynamicImportCount,
  };
}

function isWithin(root, target) {
  return target === root || target.startsWith(`${root}${sep}`);
}

function normalizeSourceFile(sourceFile) {
  if (sourceFile instanceof URL) {
    if (sourceFile.protocol !== "file:") {
      throw new TypeError(`Boundary scanner source must be a local file path. ${help}`);
    }
    return fileURLToPath(sourceFile);
  }
  if (typeof sourceFile !== "string") {
    throw new TypeError(`Boundary scanner source must be a local file path. ${help}`);
  }
  if (/^file:/i.test(sourceFile)) {
    return fileURLToPath(new URL(sourceFile));
  }
  if (/^[a-z][a-z0-9+.-]*:\/\//i.test(sourceFile) && !/^[a-z]:[\\/]/i.test(sourceFile)) {
    throw new TypeError(`Boundary scanner source must be a local file path. ${help}`);
  }
  return resolve(sourceFile);
}

export function inspectSource(source, sourceFile = join(sourceRoot, "__inspection__.ts")) {
  const normalizedSourceFile = normalizeSourceFile(sourceFile);
  const violations = [];
  const add = (code, message) => violations.push({ code, message: `${message}. ${help}` });
  const imports = moduleImports(source, normalizedSourceFile);

  for (let index = 0; index < imports.unsafeDynamicImportCount; index += 1) {
    add(
      "DW-UI-DYNAMIC-IMPORT",
      "UI cannot use a computed or template-literal dynamic import or a CommonJS module load because its destination or module form cannot be safely enforced",
    );
  }

  for (const specifier of imports.specifiers) {
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
      add("DW-UI-SELF-IMPORT", `UI source cannot self-import through ${specifier}`);
    }
    if (/^@deepwork\/[^/]+\//.test(specifier)) {
      add("DW-UI-DEEP-IMPORT", `UI cannot deep-import package path ${specifier}`);
    }
    if (specifier === "next" || specifier.startsWith("next/")) {
      add("DW-UI-NEXT-IMPORT", `UI cannot import Next.js package ${specifier}`);
    }
    if (NETWORK_PACKAGES.test(specifier)) {
      add("DW-UI-NETWORK-IMPORT", `UI cannot import network package ${specifier}`);
    }
    if (PROVIDER_PACKAGES.test(specifier)) {
      add("DW-UI-PROVIDER-IMPORT", `UI cannot import provider package ${specifier}`);
    }
    if (nodeBuiltins.has(specifier)) {
      add("DW-UI-NODE-IMPORT", `UI cannot import Node API ${specifier}`);
    }
    if (relative && !specifier.endsWith(".js") && !specifier.endsWith(".css")) {
      add(
        "DW-UI-ESM-EXTENSION",
        `local runtime import requires a .js or .css extension: ${specifier}`,
      );
    }
    if (
      (relative && !isWithin(sourceRoot, resolve(dirname(normalizedSourceFile), specifier))) ||
      specifier.startsWith("/")
    ) {
      add("DW-UI-PATH-ESCAPE", `import escapes the package source boundary: ${specifier}`);
    }
    if (FORBIDDEN_ZONE.test(specifier) || FORBIDDEN_PACKAGES.test(specifier)) {
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
    (trimmed.startsWith('"') && trimmed.endsWith('"')) ||
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
  if (reference !== reference.trim() || /[\u0000-\u001f\u007f]/.test(reference)) {
    add(
      "DW-UI-CSS-DYNAMIC-REFERENCE",
      "UI CSS reference cannot contain hidden whitespace or control characters",
    );
    return;
  }
  if (/^(?:[a-z][a-z0-9+.-]*:|\/\/)/i.test(reference)) {
    add("DW-UI-CSS-NETWORK-URL", `UI CSS cannot load an external or scheme URL: ${reference}`);
    return;
  }
  if (reference.startsWith("#")) return;
  if (
    /%(?:2e|2f|5c)/i.test(reference) ||
    reference.startsWith("/") ||
    !isWithin(packageRoot, resolve(dirname(sourceFile), reference.split(/[?#]/, 1)[0]))
  ) {
    add(
      "DW-UI-CSS-PATH-ESCAPE",
      `UI CSS reference escapes or encodes traversal outside the package boundary: ${reference}`,
    );
  }
  if (imported && (!reference.startsWith(".") || !reference.split(/[?#]/, 1)[0].endsWith(".css"))) {
    add(
      "DW-UI-CSS-IMPORT-NOT-ALLOWED",
      `UI CSS @import must be a contained relative .css path: ${reference}`,
    );
  }
}

export function inspectCss(source, sourceFile = join(packageRoot, "__inspection__.css")) {
  const normalizedSourceFile = normalizeSourceFile(sourceFile);
  const violations = [];
  const add = (code, message) => violations.push({ code, message: `${message}. ${help}` });
  const inspectableSource = source.replace(/\/\*[\s\S]*?\*\//g, " ");

  for (const match of inspectableSource.matchAll(/@import\s+([^;]+);/gi)) {
    const reference = importReference(match[1]);
    if (reference === undefined) {
      add(
        "DW-UI-CSS-DYNAMIC-REFERENCE",
        "UI CSS @import must use a statically inspectable quoted or url() path",
      );
    } else {
      inspectCssReference(reference, normalizedSourceFile, add, true);
    }
  }
  for (const match of inspectableSource.matchAll(/\burl\s*\(\s*([^)]*)\)/gi)) {
    const reference = staticCssReference(match[1]);
    if (reference === undefined) {
      add("DW-UI-CSS-DYNAMIC-REFERENCE", "UI CSS url() must use a statically inspectable path");
    } else {
      inspectCssReference(reference, normalizedSourceFile, add, false);
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
  const details = violations.map(({ code, message }) => `${code}: ${message}`).join("\n");
  throw new Error(`Boundary violation in ${file}:\n${details}`);
}

export async function checkBoundaries() {
  for (const file of await sourceFiles(sourceRoot)) {
    assertNoViolations(file, inspectSource(await readFile(file, "utf8"), file));
  }
  const rootCssFiles = (await readdir(packageRoot, { withFileTypes: true }))
    .filter((entry) => entry.isFile() && extname(entry.name) === ".css")
    .map((entry) => join(packageRoot, entry.name));
  for (const file of [...rootCssFiles, ...(await sourceFiles(sourceRoot, [".css"]))]) {
    assertNoViolations(file, inspectCss(await readFile(file, "utf8"), file));
  }

  for (const fixture of negativeFixtures) {
    const file = join(packageRoot, fixture.path);
    const inspect = extname(file) === ".css" ? inspectCss : inspectSource;
    const codes = new Set(
      inspect(fixture.source ?? (await readFile(file, "utf8")), file).map(({ code }) => code),
    );
    for (const expectedCode of fixture.expectedCodes) {
      if (!codes.has(expectedCode)) {
        throw new Error(`Negative fixture ${fixture.path} did not trigger ${expectedCode}.`);
      }
    }
  }
}

if (process.argv[1] !== undefined && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await checkBoundaries();
}
