import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Production assets only: no API proxy or extra listener is part of this task.
  build: { sourcemap: false, assetsInlineLimit: 0 },
});
