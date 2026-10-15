import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./browser",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  use: {
    baseURL: "http://127.0.0.1:8000",
    headless: true,
    reducedMotion: "reduce",
    ...(process.env.PLAYWRIGHT_CHANNEL ? { channel: process.env.PLAYWRIGHT_CHANNEL } : {}),
  },
  webServer: {
    command: "node scripts/browser-fixture.mjs",
    url: "http://127.0.0.1:8000",
    reuseExistingServer: false,
    timeout: 10000,
  },
});
