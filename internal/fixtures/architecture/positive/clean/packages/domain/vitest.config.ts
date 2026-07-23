import { fileURLToPath } from "node:url";

export const sourceEntry = fileURLToPath(
  new URL("./src/index.ts", import.meta.url),
);
