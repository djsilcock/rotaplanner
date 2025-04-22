import { defineConfig, defaultPlugins } from "@hey-api/openapi-ts";

export default defineConfig({
  input: "http://127.0.0.1:3000/openapi.json",
  output: "src/client",
  plugins: [
    ...defaultPlugins,
    "@hey-api/client-fetch",
    "@tanstack/solid-query",
  ],
});
