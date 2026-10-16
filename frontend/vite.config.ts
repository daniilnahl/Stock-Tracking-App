import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/dashboard-assets/",
  // These names match the deliberately closed Python route/package allowlist.
  build: { sourcemap: false, assetsInlineLimit: 0, rolldownOptions: { output: {
    entryFileNames: "hosting.js",
    chunkFileNames: "unexpected-[name].js",
    assetFileNames: asset => asset.names.some(name => name.endsWith(".css")) ? "hosting.css" : "[name][extname]",
  } } },
});
