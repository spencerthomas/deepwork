import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import {
  mkdtemp,
  mkdir,
  readFile,
  readdir,
  rm,
  writeFile,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const domainRoot = resolve(packageRoot, "../domain");
const expectedName = "@deepwork/ui";
const requiredFiles = [
  "README.md",
  "dist/index.d.ts",
  "dist/index.js",
  "status-panel.css",
  "tailwind.preset.mjs",
  "tokens.css",
];
const forbiddenArchivePrefixes = [
  "package/src/",
  "package/tests/",
  "package/scripts/",
];

function run(command, args, cwd) {
  const result = spawnSync(command, args, {
    cwd,
    encoding: "utf8",
    maxBuffer: 10 * 1024 * 1024,
  });
  assert.equal(
    result.status,
    0,
    `${command} ${args.join(" ")} failed:\n${result.stderr || result.stdout}`,
  );
  return result.stdout;
}

function runPnpm(args, cwd) {
  const pnpmExecPath = process.env.npm_execpath;
  assert.ok(
    pnpmExecPath,
    "package-check must run through the pinned pnpm package script.",
  );
  return run(process.execPath, [pnpmExecPath, ...args], cwd);
}

async function pack(packageDirectory, archiveDirectory) {
  const before = new Set(await readdir(archiveDirectory));
  runPnpm(["pack", "--pack-destination", archiveDirectory], packageDirectory);
  const created = (await readdir(archiveDirectory)).filter(
    (entry) => entry.endsWith(".tgz") && !before.has(entry),
  );
  assert.equal(created.length, 1, "Expected exactly one package archive.");
  return join(archiveDirectory, created[0]);
}

function exportTargets(value) {
  if (typeof value === "string") return [value];
  if (value === null || typeof value !== "object") return [];
  return Object.values(value).flatMap(exportTargets);
}

async function inspectArchive(archive, extractionRoot) {
  const entries = run("tar", ["-tzf", archive], packageRoot)
    .trim()
    .split("\n");
  for (const prefix of forbiddenArchivePrefixes) {
    assert.ok(
      !entries.some((entry) => entry.startsWith(prefix)),
      `Archive leaked private path ${prefix}`,
    );
  }
  assert.ok(
    !entries.some((entry) => entry.endsWith("pnpm-lock.yaml")),
    "Archive must not contain a workspace lock.",
  );

  await mkdir(extractionRoot, { recursive: true });
  run("tar", ["-xzf", archive, "-C", extractionRoot], packageRoot);
  const packedRoot = join(extractionRoot, "package");
  const manifestText = await readFile(join(packedRoot, "package.json"), "utf8");
  assert.ok(
    !manifestText.includes("workspace:"),
    "Packed manifest leaked a workspace protocol.",
  );
  const manifest = JSON.parse(manifestText);
  assert.equal(manifest.name, expectedName);

  for (const path of requiredFiles) {
    const contents = await readFile(join(packedRoot, path));
    assert.ok(contents.length > 0, `Packed file is empty: ${path}`);
  }
  for (const target of exportTargets(manifest.exports)) {
    assert.ok(target.startsWith("./"), `Unsafe export target: ${target}`);
    const contents = await readFile(join(packedRoot, target.slice(2)));
    assert.ok(contents.length > 0, `Packed export is empty: ${target}`);
  }

  const statusCss = await readFile(
    join(packedRoot, "status-panel.css"),
    "utf8",
  );
  const tokensCss = await readFile(join(packedRoot, "tokens.css"), "utf8");
  assert.ok(
    statusCss.includes("var(--space-4)"),
    "Packed status styles must consume canonical spacing tokens.",
  );
  assert.ok(
    tokensCss.includes("--touch-target-min:"),
    "Packed tokens must include the shared touch target.",
  );
}

const temporaryRoot = await mkdtemp(
  join(tmpdir(), "deepwork-ui-package-check-"),
);

try {
  const archives = join(temporaryRoot, "archives");
  const extraction = join(temporaryRoot, "extracted");
  const consumer = join(temporaryRoot, "consumer");
  await mkdir(archives);
  await mkdir(consumer);

  const domainArchive = await pack(domainRoot, archives);
  const uiArchive = await pack(packageRoot, archives);
  await inspectArchive(uiArchive, extraction);

  await writeFile(
    join(consumer, "package.json"),
    `${JSON.stringify(
      { name: "ui-clean-consumer", private: true, type: "module" },
      null,
      2,
    )}\n`,
  );
  runPnpm(
    [
      "add",
      "--offline",
      "--ignore-scripts",
      "--save-exact",
      domainArchive,
      uiArchive,
      "react@19.2.8",
      "@types/react@19.2.17",
      "typescript@7.0.2",
    ],
    consumer,
  );
  await writeFile(
    join(consumer, "verify.mjs"),
    `import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import * as ui from "@deepwork/ui";
import preset from "@deepwork/ui/tailwind-preset";

if (typeof ui.StatusPanel !== "function" || typeof preset !== "object") {
  throw new Error("UI JavaScript entry points are not importable.");
}
for (const entry of ["@deepwork/ui/tokens.css", "@deepwork/ui/status-panel.css"]) {
  const contents = await readFile(fileURLToPath(import.meta.resolve(entry)), "utf8");
  if (contents.length === 0) throw new Error(\`\${entry} is empty.\`);
}
`,
  );
  run(process.execPath, ["verify.mjs"], consumer);
  await writeFile(
    join(consumer, "verify.tsx"),
    `import { StatusPanel, type StatusPanelProps } from "@deepwork/ui";
const props: StatusPanelProps = {
  state: "success",
  title: "Packed consumer",
};
const panel = <StatusPanel {...props} />;
void panel;
`,
  );
  await writeFile(
    join(consumer, "tsconfig.json"),
    `${JSON.stringify(
      {
        compilerOptions: {
          jsx: "react-jsx",
          lib: ["ES2022", "DOM"],
          module: "ESNext",
          moduleResolution: "Bundler",
          noEmit: true,
          skipLibCheck: false,
          strict: true,
          target: "ES2022",
        },
        include: ["verify.tsx"],
      },
      null,
      2,
    )}\n`,
  );
  runPnpm(["exec", "tsc", "--project", "tsconfig.json"], consumer);
  process.stdout.write(
    `clean consumer verified ${expectedName} from ${basename(uiArchive)}\n`,
  );
} finally {
  await rm(temporaryRoot, { recursive: true, force: true });
}
