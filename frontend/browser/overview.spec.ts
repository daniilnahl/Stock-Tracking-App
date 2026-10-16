import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";
import { watchlist } from "../tests/fixtures";

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
}
for (const scenario of [{ theme: "light", width: 1440, height: 1100 }, { theme: "dark", width: 390, height: 844 }] as const) {
  test(`supported overview ${scenario.theme} at ${scenario.width}px counts only one known namespace`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width: scenario.width, height: scenario.height });
    await page.addInitScript(theme => localStorage.setItem("stock-tracker.theme", theme), scenario.theme);
    const paths: string[] = [];
    await page.route("**/api/**", async route => {
      const path = new URL(route.request().url()).pathname;
      paths.push(path);
      if (!["/api/v1/watchlists/menu_watchlist", "/api/v1/watchlists/daniils_stock_method"].includes(path) || route.request().method() !== "GET") return route.abort();
      const namespace = path.endsWith("daniils_stock_method") ? "daniils_stock_method" : "menu_watchlist";
      const data = watchlist(namespace);
      const entries = namespace === "menu_watchlist" ? [...data.entries, { ...data.entries[0]!, ordinal: 2 }].map(row => ({ ...row, quantity: "0" })) : [];
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ...data, name: namespace === "menu_watchlist" ? "SYNTHETIC overview fixture / no real holdings" : "SYNTHETIC " + "DEMO".repeat(30), entries }) });
    });
    await configure(page);
    await page.getByRole("link", { name: "Overview", exact: true }).click();
    const count = page.getByRole("region", { name: "Saved entries", exact: true }).getByRole("status");
    await expect(count).toHaveText("Unavailable");
    expect(paths.length).toBe(0);
    await page.getByRole("link", { name: "Open Watchlists", exact: true }).click();
    await page.getByRole("button", { name: "Read saved entries" }).click();
    await expect(page.getByRole("table")).toBeVisible();
    await page.getByRole("link", { name: "Overview", exact: true }).click();
    await expect(count).toHaveText("3");
    await expect(page.getByRole("region", { name: "Saved watchlist access" }).getByText("menu_watchlist", { exact: true })).toBeVisible();
    await expect(page.getByText("This count covers only the loaded namespace. Overview makes no additional requests.")).toBeVisible();
    await expect(page.getByRole("table")).toHaveCount(0);
    expect(paths.length).toBe(1);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await expect(page.locator("html")).toHaveAttribute("data-theme", scenario.theme);
    await page.evaluate(() => {
      const banner = document.createElement("p");
      banner.className = "demo-label";
      banner.textContent = "Synthetic browser fixture / no live data";
      document.querySelector("main h1")?.after(banner);
    });
    expect(await page.locator('input[type="password"]').count()).toBe(0);
    await page.evaluate(() => document.fonts.ready);
    expect(await page.evaluate(() => document.fonts.check('20px "Stock Pixel"'))).toBe(true);
    await page.screenshot({ path: testInfo.outputPath(`overview-${scenario.theme}-${scenario.width}.png`), fullPage: true });
    await page.getByRole("link", { name: "Open Watchlists", exact: true }).click();
    await page.getByLabel("Saved namespace").selectOption("daniils_stock_method");
    await page.getByRole("button", { name: "Read saved entries" }).click();
    await expect(page.getByRole("table")).toBeVisible();
    await page.getByRole("link", { name: "Overview", exact: true }).click();
    await expect(count).toHaveText("0");
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await expect(page.getByRole("region", { name: "Saved watchlist access" }).getByText("daniils_stock_method", { exact: true })).toBeVisible();
    expect(paths).toEqual(["/api/v1/watchlists/menu_watchlist", "/api/v1/watchlists/daniils_stock_method"]);
    await page.getByRole("link", { name: "Settings", exact: true }).click();
    await page.getByRole("button", { name: "Disconnect", exact: true }).click();
    await page.getByRole("link", { name: "Overview", exact: true }).click();
    await expect(count).toHaveText("Unavailable");
    await expect(page.getByText("Saved list name:", { exact: false })).toHaveCount(0);
    expect(paths.length).toBe(2);
    expect(await page.evaluate(() => Object.keys(localStorage))).toEqual(["stock-tracker.theme"]);
    expect(await page.evaluate(() => Object.keys(sessionStorage))).toEqual([]);
  });
}
