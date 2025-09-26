import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import solidPlugin from "vite-plugin-solid";
import relay from "vite-plugin-relay-lite";
import { cjsInterop } from "vite-plugin-cjs-interop";

export default defineConfig({
  plugins: [
    solidPlugin(),
    tailwindcss(),
    relay(),
    cjsInterop({ dependencies: ["relay-runtime"] }),
  ],
  server: {
    port: 3000,
    proxy: {
      "/graphql": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    target: "esnext",
  },
});
