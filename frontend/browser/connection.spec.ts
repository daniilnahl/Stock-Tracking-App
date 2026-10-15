import { expect, test } from "@playwright/test";
import type { Locator } from "@playwright/test";

// Generate inside the page: no credential value is passed to/returned from a
// Playwright action, assertion, report, snapshot, trace, screenshot or fixture.
async function enterRuntimeCredential(input: Locator, offset = 0, oversized = false) {
  await input.evaluate((element, options) => {
    if (!(element instanceof HTMLInputElement)) throw new Error("Expected masked control");
    element.value = Array.from({ length: 48 }, (_, index) => String.fromCharCode(65 + (index * 7 + options.offset) % 26)).join("").repeat(options.oversized ? 8 : 1);
    element.dispatchEvent(new Event("input", { bubbles: true }));
  }, { offset, oversized });
}
async function expectEmpty(input: Locator) {
  // Boolean diagnostics only: never print a nonempty password as an Actual.
  expect(await input.evaluate(element => element instanceof HTMLInputElement && element.value.length === 0)).toBe(true);
}
for (const scenario of [{ theme: "light", width: 1440, height: 1100 }, { theme: "dark", width: 390, height: 844 }] as const) {
  test(`memory-only configuration ${scenario.theme} at ${scenario.width}px`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width: scenario.width, height: scenario.height });
    await page.addInitScript(theme => localStorage.setItem("stock-tracker.theme", theme), scenario.theme);
    let apiRequests = 0;
    page.on("request", request => { if (new URL(request.url()).pathname.startsWith("/api/")) apiRequests++; });
    await page.route("**/*", route => route.request().url().startsWith("http://127.0.0.1:8000/") ? route.continue() : route.abort());
    await page.goto("/#settings");
    const input = page.getByLabel("Local API token", { exact: true });
    await expect(input).toHaveAttribute("type", "password");
    await expect(input).toHaveAttribute("autocomplete", "off");
    await expectEmpty(input);
    await input.focus();
    await enterRuntimeCredential(input);
    await page.keyboard.press("Enter");
    await expectEmpty(input);
    await expect(page.getByText("Configured", { exact: true })).toBeVisible();
    await expect(page.getByText("Configuration alone does not verify authentication. Configuring this page does not request or load private data.")).toBeVisible();
    expect(apiRequests).toBe(0);
    expect(await page.evaluate(() => Object.keys(localStorage))).toEqual(["stock-tracker.theme"]);
    expect(await page.evaluate(() => Object.keys(sessionStorage))).toEqual([]);
    expect(new URL(page.url()).search).toBe("");
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath(`connection-configured-${scenario.theme}-${scenario.width}.png`), fullPage: true });
    await enterRuntimeCredential(input, 1);
    await page.getByRole("button", { name: "Replace connection" }).click();
    await expectEmpty(input);
    await enterRuntimeCredential(input, 2); // Unsubmitted replacement draft.
    await page.getByRole("link", { name: "Overview", exact: true }).click();
    await expect(page.getByText("Configured", { exact: true })).toBeVisible();
    await page.getByRole("link", { name: "Settings", exact: true }).click();
    await expectEmpty(input);
    await page.getByRole("button", { name: "Disconnect", exact: true }).focus();
    await page.keyboard.press("Enter");
    await expect(input).toBeFocused();
    await expect(page.getByText("Disconnected", { exact: true })).toBeVisible();
    await expectEmpty(input);
    await page.screenshot({ path: testInfo.outputPath(`connection-disconnected-${scenario.theme}-${scenario.width}.png`), fullPage: true });
    await enterRuntimeCredential(input);
    await page.getByRole("button", { name: "Configure connection" }).click();
    await expectEmpty(input);
    await page.reload();
    await expectEmpty(input);
    await expect(page.getByText("Disconnected", { exact: true })).toBeVisible();
    await expect(page.locator("html")).toHaveAttribute("data-theme", scenario.theme);
    expect(apiRequests).toBe(0);
  });
}
test("overlength input is rejected whole and safely cleared, then retry configures without a request", async ({ page }) => {
  await page.goto("/#settings");
  const input = page.getByLabel("Local API token", { exact: true });
  await enterRuntimeCredential(input, 0, true);
  await page.getByRole("button", { name: "Configure connection" }).click();
  await expectEmpty(input);
  await expect(input).toBeFocused();
  expect(await page.getByRole("alert").evaluate(element => element.textContent === "Request input is invalid.")).toBe(true);
  await expect(page.getByText("Disconnected", { exact: true })).toBeVisible();
  await enterRuntimeCredential(input);
  await page.keyboard.press("Enter");
  await expectEmpty(input);
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(page.getByText("Configured", { exact: true })).toBeVisible();
});
test("unsupported exact parsing fails visibly before any private request and clears the field", async ({ page }) => {
  await page.addInitScript(() => {
    const native = JSON.parse;
    JSON.parse = (text, reviver) => native(text, reviver ? (key, value) => reviver(key, value) : undefined);
  });
  let apiRequests = 0;
  page.on("request", request => { if (new URL(request.url()).pathname.startsWith("/api/")) apiRequests++; });
  await page.goto("/#settings");
  const input = page.getByLabel("Local API token", { exact: true });
  await enterRuntimeCredential(input);
  await page.getByRole("button", { name: "Configure connection" }).click();
  await expectEmpty(input);
  expect(await page.getByRole("alert").evaluate(element => element.textContent === "This browser cannot decode exact API numbers. Use a current supported browser.")).toBe(true);
  await expect(page.getByText("Unsupported", { exact: true })).toBeVisible();
  expect(apiRequests).toBe(0);
});
