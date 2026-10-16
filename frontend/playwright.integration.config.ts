import { defineConfig } from "@playwright/test";

// Pinned Playwright1.64.1 also captures failure ARIA context independently of
// trace/video/screenshot options (lib/index.js:_takePageSnapshot). Suppress it.
process.env.PLAYWRIGHT_NO_COPY_PROMPT = "1";

export default defineConfig({
  testDir: "./integration", outputDir: "./test-results/integration",
  fullyParallel: false, workers: 1, retries: 0,
  use: { baseURL: "http://127.0.0.1:8000", headless: true, trace: "off", video: "off", screenshot: "off", reducedMotion: "reduce",
    ...(process.env.PLAYWRIGHT_CHANNEL ? { channel: process.env.PLAYWRIGHT_CHANNEL } : {}) },
  projects: [{ name: "source" }, { name: "wheel", dependencies: ["source"] }],
});
