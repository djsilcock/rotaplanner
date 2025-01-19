import { defineConfig } from "vite";
import solidPlugin from "vite-plugin-solid";

export default defineConfig(({ command }) => ({
  plugins: [solidPlugin()],
  server: {
    port: 3000,
  },
  base: "/site/",
  define: {
    BACKEND_URL: command === "build" ? '""' : '"http://localhost:5000"',
  },
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
