import { defineConfig, defaultPlugins } from "@hey-api/openapi-ts";

export default defineConfig({
  input: "./openapi.json",
  output: "generatedTypes",
  plugins: [
    ...defaultPlugins,
    "@hey-api/client-fetch",
    "@tanstack/solid-query",
    "zod",
    "valibot",
  ],
});
