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
  "Legal destination: @deepwork/domain public entry or packages/sdk/src/**. " +
  "Architecture: ARCHITECTURE.md#package-graph and " +
  "ARCHITECTURE.md#mechanical-enforcement. " +
  "Repair: pnpm --filter @deepwork/sdk check-architecture";

const FRAMEWORK_PACKAGES = /^(?:react|react-dom|next)(?:\/|$)/;
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
        'const moduleName = "./ports.js"; void import// fixture' + terminator + `(${argument});`,
      expectedCodes: [expectedCode],
    })),
  );
}

export const negativeFixtures = [
  {
    path: "tests/fixtures/negative/ui-side-effect.fixture.ts",
    expectedCodes: ["DW-SDK-UI-IMPORT", "DW-SDK-IMPORT-NOT-ALLOWED"],
  },
  {
    path: "tests/fixtures/negative/provider-side-effect.fixture.ts",
    expectedCodes: ["DW-SDK-PROVIDER-IMPORT", "DW-SDK-IMPORT-NOT-ALLOWED"],
  },
  {
    path: "tests/fixtures/negative/raw-network.fixture.ts",
    expectedCodes: ["DW-SDK-NETWORK-IMPORT", "DW-SDK-NETWORK-API", "DW-SDK-IMPORT-NOT-ALLOWED"],
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
  {
    path: "tests/fixtures/negative/computed-dynamic-import.fixture.ts",
    expectedCodes: ["DW-SDK-DYNAMIC-IMPORT"],
  },
  {
    path: "tests/fixtures/negative/in-memory/commented-static-import.fixture.ts",
    source: 'import/* fixture */"@deepwork/ui";',
    expectedCodes: ["DW-SDK-UI-IMPORT", "DW-SDK-IMPORT-NOT-ALLOWED"],
  },
  {
    path: "tests/fixtures/negative/in-memory/commented-static-export.fixture.ts",
    source: 'export { StatusPanel } from/* fixture */"@deepwork/ui";',
    expectedCodes: ["DW-SDK-UI-IMPORT", "DW-SDK-IMPORT-NOT-ALLOWED"],
  },
  {
    path: "tests/fixtures/negative/in-memory/import-equals.fixture.ts",
    source: 'import legacy = require("@deepwork/ui"); void legacy;',
    expectedCodes: ["DW-SDK-DYNAMIC-IMPORT", "DW-SDK-UI-IMPORT", "DW-SDK-IMPORT-NOT-ALLOWED"],
  },
  {
    path: "tests/fixtures/negative/in-memory/commonjs-require.fixture.ts",
    source: 'const legacy = require("@deepwork/ui"); void legacy;',
    expectedCodes: ["DW-SDK-DYNAMIC-IMPORT", "DW-SDK-UI-IMPORT", "DW-SDK-IMPORT-NOT-ALLOWED"],
  },
  {
    path: "tests/fixtures/negative/in-memory/import-type.fixture.ts",
    source: 'type Legacy = import("@deepwork/ui").StatusPanelProps; void 0;',
    expectedCodes: ["DW-SDK-UI-IMPORT", "DW-SDK-IMPORT-NOT-ALLOWED"],
  },
  ...dynamicImportLineCommentFixtures("DW-SDK-DYNAMIC-IMPORT"),
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

export function inspectSource(source, sourceFile = join(sourceRoot, "__inspection__.ts")) {
  const violations = [];
  const add = (code, message) => violations.push({ code, message: `${message}. ${help}` });
  const imports = moduleImports(source, sourceFile);

  for (let index = 0; index < imports.unsafeDynamicImportCount; index += 1) {
    add(
      "DW-SDK-DYNAMIC-IMPORT",
      "SDK cannot use a computed or template-literal dynamic import or a CommonJS module load because its destination or module form cannot be safely enforced",
    );
  }

  for (const specifier of imports.specifiers) {
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
      add("DW-SDK-SELF-IMPORT", `SDK source cannot self-import through ${specifier}`);
    }
    if (/^@deepwork\/[^/]+\//.test(specifier)) {
      add("DW-SDK-DEEP-IMPORT", `SDK cannot deep-import package path ${specifier}`);
    }
    if (FRAMEWORK_PACKAGES.test(specifier)) {
      add("DW-SDK-FRAMEWORK-IMPORT", `SDK cannot import framework package ${specifier}`);
    }
    if (NETWORK_PACKAGES.test(specifier)) {
      add(
        "DW-SDK-NETWORK-IMPORT",
        `unreviewed SDK source cannot import raw network package ${specifier}`,
      );
    }
    if (PROVIDER_PACKAGES.test(specifier)) {
      add("DW-SDK-PROVIDER-IMPORT", `SDK cannot import provider package ${specifier}`);
    }
    if (nodeBuiltins.has(specifier)) {
      add("DW-SDK-NODE-IMPORT", `SDK cannot import Node API ${specifier}`);
    }
    if (relative && !specifier.endsWith(".js")) {
      add("DW-SDK-ESM-EXTENSION", `local runtime import requires a .js extension: ${specifier}`);
    }
    if (
      (relative && !isWithin(sourceRoot, resolve(dirname(sourceFile), specifier))) ||
      specifier.startsWith("/")
    ) {
      add("DW-SDK-PATH-ESCAPE", `import escapes the package source boundary: ${specifier}`);
    }
    if (FORBIDDEN_ZONE.test(specifier) || FORBIDDEN_PACKAGES.test(specifier)) {
      add(
        "DW-SDK-FORBIDDEN-ZONE",
        `SDK cannot import server, Tauri, route, fixture, generated, or database path ${specifier}`,
      );
    }
  }

  if (/\b(?:fetch|XMLHttpRequest|WebSocket|EventSource)\b/.test(source)) {
    add("DW-SDK-NETWORK-API", "unreviewed SDK source cannot use raw network APIs");
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
  const details = violations.map(({ code, message }) => `${code}: ${message}`).join("\n");
  throw new Error(`Boundary violation in ${file}:\n${details}`);
}

export async function checkBoundaries() {
  for (const file of await sourceFiles(sourceRoot)) {
    assertNoViolations(file, inspectSource(await readFile(file, "utf8"), file));
  }

  for (const fixture of negativeFixtures) {
    const file = join(packageRoot, fixture.path);
    const codes = new Set(
      inspectSource(fixture.source ?? (await readFile(file, "utf8")), file).map(({ code }) => code),
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
