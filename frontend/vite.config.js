import { defineConfig } from "vite";
import solidPlugin from "vite-plugin-solid";

export default defineConfig(({ command }) => ({
  plugins: [solidPlugin()],
  server: {
    port: 3000,
  
    proxy: {
      
      '/api': {
        target: 'http://localhost:5000'
      }
    },
  base: "/site/",
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
