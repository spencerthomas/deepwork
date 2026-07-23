import { fileURLToPath } from "node:url";

import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      "@deepwork/domain": fileURLToPath(
        new URL("../domain/src/index.ts", import.meta.url),
      ),
      "@deepwork/sdk": fileURLToPath(
        new URL("./src/index.ts", import.meta.url),
      ),
    },
  },
});
