import { defineConfig } from "vite";
import solidPlugin from "vite-plugin-solid";
import { heyApiPlugin } from "@hey-api/vite-plugin";

export default defineConfig({
  plugins: [
    heyApiPlugin({
      config: {
        input: "http://127.0.0.1:5000/openapi.json",
        output: "rotaplanner/generated/client",
        plugins: [{ name: "@hey-api/client-fetch", baseUrl: "/" }],
      },
    }),
    solidPlugin(),
  ],
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:5000",
        changeOrigin: true,
        secure: false,
      },
      "/openapi.json": {
        target: "http://127.0.0.1:5000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    target: "esnext",
  },
});
