import { defineConfig } from "vite";
import solidPlugin from "vite-plugin-solid";

export default defineConfig(({ command }) => ({
  plugins: [solidPlugin()],
  server: {
    host: "127.0.0.1",
    port: 3000,

    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
      },
      "/openapi.json": {
        target: "http://127.0.0.1:8000",
      },
    },
  },
  base: "/",
  build: {
    target: "esnext",
    outDir: "../rotaplanner/static",
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["node_modules/@testing-library/jest-dom/vitest"],
    // if you have few tests, try commenting this
    // out to improve performance:
    isolate: false,
  },
}));
