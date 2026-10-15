import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";
import { watchlist } from "../tests/fixtures";
import type { Namespace } from "../src/services/validation";

function synthetic(namespace: Namespace) {
  const data = watchlist(namespace);
  return { ...data, name: namespace === "menu_watchlist" ? "Synthetic Menu list" : "Synthetic Method list", entries: [
    { ...data.entries[0]!, average_cost: "1.00000000000000000001", snapshot: { cost_basis: "0.1234567890123456789024691357801234567890123456789", market_value: null, unrealized_pnl: null, unrealized_return: null } },
    data.entries[1]!,
    { ...data.entries[1]!, ordinal: 2, average_cost: "0", snapshot: { cost_basis: "0", market_value: "0", unrealized_pnl: "0", unrealized_return: null } },
  ] };
}
async function configure(page: Page) {
  await page.goto("/#settings");
  const input = page.getByLabel("Local API token", { exact: true });
  await input.evaluate(element => {
    if (!(element instanceof HTMLInputElement)) throw new Error("Expected masked control");
    element.value = Array.from({ length: 48 }, (_, index) => String.fromCharCode(65 + index * 7 % 26)).join("");
    element.dispatchEvent(new Event("input", { bubbles: true }));
  });
  await page.getByRole("button", { name: "Configure connection" }).click();
  expect(await input.evaluate(element => element instanceof HTMLInputElement && element.value.length === 0)).toBe(true);
  await page.getByRole("link", { name: "Watchlists", exact: true }).click();
}
async function banner(page: Page) {
  // Only the isolated browser test inserts this banner. Production has no
  // sample-price mode, fixture endpoint or synthetic holdings.
  await page.evaluate(() => {
    const label = document.createElement("p");
    label.textContent = "Synthetic browser fixture / no live data";
    label.className = "demo-label";
    document.querySelector("main h1")?.after(label);
  });
}
for (const scenario of [{ theme: "light", width: 1440, height: 1100 }, { theme: "dark", width: 390, height: 844 }] as const) {
  test(`saved lists ${scenario.theme} at ${scenario.width}px`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width: scenario.width, height: scenario.height });
    await page.addInitScript(theme => localStorage.setItem("stock-tracker.theme", theme), scenario.theme);
    const paths: string[] = [];
    await page.route("**/api/**", async route => {
      const path = new URL(route.request().url()).pathname;
      paths.push(path);
      const namespace: Namespace = path === "/api/v1/watchlists/daniils_stock_method" ? "daniils_stock_method" : "menu_watchlist";
      if (!["/api/v1/watchlists/menu_watchlist", "/api/v1/watchlists/daniils_stock_method"].includes(path) || route.request().method() !== "GET") return route.abort();
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(synthetic(namespace)) });
    });
    await configure(page);
    expect(paths.length).toBe(0);
    await page.getByRole("button", { name: "Read saved entries" }).focus();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("table")).toBeVisible();
    await expect(page.getByRole("cell", { name: "0.12345678901234567890123456789", exact: true })).toBeVisible();
    await expect(page.getByRole("cell", { name: "1.00000000000000000001", exact: true })).toBeVisible();
    await expect(page.getByRole("cell", { name: "Unowned", exact: true })).toHaveCount(1);
    await expect(page.getByRole("cell", { name: "Owned", exact: true })).toHaveCount(2);
    await expect(page.getByRole("cell", { name: "Unavailable", exact: true })).toHaveCount(1);
    expect(await page.getByText("menu_watchlist", { exact: true }).evaluate(element => getComputedStyle(element).fontFamily.includes("Stock Pixel"))).toBe(true);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const region = page.getByRole("region", { name: "Menu watchlist / saved entries" });
    await region.focus();
    await expect(region).toBeFocused();
    if (scenario.width === 390) {
      await page.keyboard.press("ArrowRight");
      await expect.poll(() => region.evaluate(element => element.scrollLeft)).toBeGreaterThan(0);
      await region.evaluate(element => { element.scrollLeft = 0; });
    }
    await banner(page);
    expect(await page.locator('input[type="password"]').count()).toBe(0);
    await page.screenshot({ path: testInfo.outputPath(`watchlists-${scenario.theme}-${scenario.width}.png`), fullPage: true });
    if (scenario.width === 390) {
      await region.evaluate(element => { element.scrollLeft = element.scrollWidth; });
      await page.screenshot({ path: testInfo.outputPath("watchlists-dark-390-saved-price.png"), fullPage: true });
    }
    await page.getByLabel("Saved namespace").selectOption("daniils_stock_method");
    await expect(page.getByRole("table")).toHaveCount(0);
    expect(paths.length).toBe(1);
    await page.getByRole("button", { name: "Read saved entries" }).click();
    await expect(page.getByRole("heading", { name: "Synthetic Method list" })).toBeVisible();
    expect(paths).toEqual(["/api/v1/watchlists/menu_watchlist", "/api/v1/watchlists/daniils_stock_method"]);
    if (scenario.width === 390) {
      expect(await page.locator('input[type="password"]').count()).toBe(0);
      await expect(page.getByText("Synthetic browser fixture / no live data", { exact: true })).toBeVisible();
      await page.screenshot({ path: testInfo.outputPath("watchlists-method-dark-390.png"), fullPage: true });
      await page.getByRole("region", { name: "Daniil's stock method / saved entries" }).evaluate(element => { element.scrollLeft = element.scrollWidth; });
      await page.screenshot({ path: testInfo.outputPath("watchlists-method-dark-390-saved-price.png"), fullPage: true });
    }
    await page.getByRole("button", { name: "Reload saved entries" }).click();
    await expect(page.getByRole("heading", { name: "Synthetic Method list" })).toBeVisible();
    expect(paths.length).toBe(3);
    await page.getByRole("link", { name: "Settings", exact: true }).click();
    await page.getByRole("button", { name: "Disconnect", exact: true }).click();
    await page.getByRole("link", { name: "Watchlists", exact: true }).click();
    await expect(page.getByRole("table")).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Read saved entries" })).toBeDisabled();
    expect(await page.evaluate(() => Object.keys(localStorage))).toEqual(["stock-tracker.theme"]);
    expect(await page.evaluate(() => Object.keys(sessionStorage))).toEqual([]);
  });
}
test("keyboard cancellation restores focus and an old response cannot become current", async ({ page }) => {
  let release!: () => void;
  const held = new Promise<void>(resolve => { release = resolve; });
  let reads = 0;
  await page.route("**/api/v1/watchlists/menu_watchlist", async route => {
    const current = ++reads;
    if (current === 1) await held;
    try { await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ...synthetic("menu_watchlist"), name: current === 1 ? "Late fixture" : "Replacement fixture" }) }); }
    catch (error) {
      // Only an already-aborted request is expected in this deliberate race.
      if (current !== 1 || route.request().failure()?.errorText !== "net::ERR_ABORTED") throw error;
    }
  });
  await configure(page);
  await page.getByRole("button", { name: "Read saved entries" }).click();
  await expect.poll(() => reads).toBe(1);
  await page.getByRole("button", { name: "Cancel read" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("button", { name: "Read saved entries" })).toBeFocused();
  await expect(page.getByText("Saved read cancelled", { exact: true })).toBeVisible();
  release();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "Replacement fixture" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Late fixture" })).toHaveCount(0);
});
test("failed reload removes previous observations and recovers; 401 clears the shared session", async ({ page }) => {
  let reads = 0;
  await page.route("**/api/v1/watchlists/menu_watchlist", async route => {
    reads++;
    if (reads === 2) return route.abort();
    if (reads === 4) return route.fulfill({ status: 401, body: "Not displayed" });
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(synthetic("menu_watchlist")) });
  });
  await configure(page);
  await page.getByRole("button", { name: "Read saved entries" }).click();
  await expect(page.getByRole("table")).toBeVisible();
  await page.getByRole("button", { name: "Reload saved entries" }).click();
  await expect(page.getByRole("alert")).toContainText("The local API could not be reached.");
  await expect(page.getByRole("table")).toHaveCount(0);
  await page.getByRole("button", { name: "Try again" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("table")).toBeVisible();
  await expect(page.getByLabel("Saved namespace")).toBeFocused();
  await page.getByRole("button", { name: "Reload saved entries" }).click();
  await expect(page.getByText("Saved reads disconnected", { exact: true })).toBeVisible();
  await expect(page.getByRole("table")).toHaveCount(0);
  await expect(page.getByRole("alert")).toHaveText("Authentication is required. Private views were cleared.");
  await page.getByRole("link", { name: "Open connection settings" }).click();
  await expect(page.getByText("Disconnected", { exact: true })).toBeVisible();
  expect(await page.getByLabel("Local API token", { exact: true }).evaluate(element => element instanceof HTMLInputElement && element.value.length === 0)).toBe(true);
});
