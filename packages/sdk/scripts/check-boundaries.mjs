import { readFile, readdir } from "node:fs/promises";
import { extname, join } from "node:path";
import { fileURLToPath } from "node:url";

const sourceRoot = fileURLToPath(new URL("../src/", import.meta.url));
const forbidden = [
  /@deepwork\/(?:sdk|ui)/,
  /\b(?:react|next)(?:\/|["'])/,
  /\bnode:/,
  /\b(?:fetch|XMLHttpRequest|WebSocket|EventSource)\b/,
  /\bprocess\.env\b/,
];

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

for (const file of await sourceFiles(sourceRoot)) {
  const source = await readFile(file, "utf8");
  for (const pattern of forbidden) {
    if (pattern.test(source)) {
      throw new Error(`Forbidden SDK boundary match in ${file}: ${pattern}`);
    }
  }

  for (const match of source.matchAll(/from\s+["'](\.[^"']+)["']/g)) {
    if (!match[1].endsWith(".js")) {
      throw new Error(`Local ESM import lacks .js extension in ${file}`);
    }
  }
}
