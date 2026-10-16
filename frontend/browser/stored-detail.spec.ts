import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";
import { history, watchlist } from "../tests/fixtures";

function saved() {
  const view = watchlist();
  return { ...view, name: "Synthetic stored rows", entries: view.entries.map((row, ordinal) => ({ ...row, quantity: "0", average_cost: ordinal === 1 ? "100.00000000000000001" : null,
    current_price: "0", snapshot: ordinal === 1 ? { cost_basis: "0", market_value: "0", unrealized_pnl: "0", unrealized_return: null } : null })) };
}
function rawHistory() {
  const view = history(1);
  return JSON.stringify({ ...view, provenance: { ...view.provenance, source: "fmp", freshness: "accepted_cache_policy" }, bars: [
    { ...view.bars[0]!, volume: 0 },
    { ...view.bars[0]!, date: "2020-01-03", close: "113.0000000000000000002", volume: 0 },
    { ...view.bars[1]!, close: "115.0000000000000000003", volume: null },
  ] })
    .replace('"volume":0', '"volume":9223372036854775807');
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
async function open(page: Page) {
  await page.getByRole("button", { name: "Read saved entries" }).click();
  await page.getByRole("button", { name: "Open detail for row 1" }).click();
  await expect(page.getByRole("heading", { name: "Stored-row detail / DEMO" })).toBeFocused();
}
async function label(page: Page) {
  await page.evaluate(() => {
    for (const selector of ["#stored-detail-title", "#stored-history-title", ".stored-history figcaption"]) {
      const element = document.createElement("p");
      element.className = "demo-label";
      element.textContent = "Synthetic browser fixture / no live data / rights not activated";
      document.querySelector(selector)?.after(element);
    }
  });
}
for (const scenario of [{ theme: "light", width: 1440, height: 1100 }, { theme: "dark", width: 390, height: 844 }] as const) {
  test(`stored row and exact sparse history ${scenario.theme} at ${scenario.width}px`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width: scenario.width, height: scenario.height });
    await page.addInitScript(theme => localStorage.setItem("stock-tracker.theme", theme), scenario.theme);
    const paths: string[] = [];
    await page.route("**/api/**", async route => {
      const url = new URL(route.request().url());
      paths.push(url.pathname + url.search);
      if (route.request().method() !== "GET") return route.abort();
      if (url.pathname === "/api/v1/watchlists/menu_watchlist") return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(saved()) });
      if (url.pathname === "/api/v1/watchlists/menu_watchlist/entries/1/history") return route.fulfill({ status: 200, contentType: "application/json", body: rawHistory() });
      return route.abort();
    });
    await configure(page);
    expect(paths.length).toBe(0);
    await open(page);
    expect(paths).toEqual(["/api/v1/watchlists/menu_watchlist", "/api/v1/watchlists/menu_watchlist"]);
    await expect(page.getByText("History not loaded", { exact: true })).toBeVisible();
    await page.getByLabel("Start date", { exact: true }).fill("2020-01-02");
    await page.getByLabel("End date", { exact: true }).fill("2020-01-06");
    await page.getByRole("button", { name: "Read raw history" }).focus();
    await page.keyboard.press("Enter");
    const table = page.getByRole("table", { name: "Exact raw history / saved row" });
    await expect(table).toBeVisible();
    await expect(table.getByRole("cell", { name: "9223372036854775807", exact: true })).toBeVisible();
    await expect(table.getByRole("cell", { name: "110.0000000000000000001", exact: true })).toHaveCount(1);
    await expect(table.getByRole("cell", { name: "115.0000000000000000003", exact: true })).toHaveCount(1);
    await expect(table.getByRole("row")).toHaveCount(4);
    expect(paths[2]).toBe("/api/v1/watchlists/menu_watchlist/entries/1/history?start=2020-01-02&end=2020-01-06");
    await expect(page.getByRole("img", { name: "Approximate raw close observations, 2020-01-02 to 2020-01-06" })).toBeVisible();
    expect(await page.locator("svg circle").count()).toBe(3);
    expect(await page.locator("svg polyline,svg line").count()).toBe(0);
    expect(await page.locator(".history-chart-dates").evaluate(element => parseFloat(getComputedStyle(element).fontSize) >= 20 && getComputedStyle(element).fontFamily.includes("Stock Pixel"))).toBe(true);
    expect(await page.locator(".history-axis").evaluate(element => getComputedStyle(element).stroke === getComputedStyle(element.closest("svg")!).color)).toBe(true);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await label(page);
    expect(await page.locator('input[type="password"]').count()).toBe(0);
    await page.screenshot({ path: testInfo.outputPath(`stored-history-${scenario.theme}-${scenario.width}.png`), fullPage: true });
    await page.locator(".stored-history").screenshot({ path: testInfo.outputPath(`stored-history-focused-${scenario.theme}-${scenario.width}.png`) });
    await page.locator(".stored-history .chart-placeholder").screenshot({ path: testInfo.outputPath(`stored-history-chart-${scenario.theme}-${scenario.width}.png`) });
    if (scenario.width === 390) {
      await page.getByRole("region", { name: "Exact raw history / saved row" }).focus();
      await page.keyboard.press("ArrowRight");
      await expect.poll(() => page.getByRole("region", { name: "Exact raw history / saved row" }).evaluate(element => element.scrollLeft)).toBeGreaterThan(0);
      await page.getByRole("region", { name: "Exact raw history / saved row" }).evaluate(element => { element.scrollLeft = element.scrollWidth; });
      await page.screenshot({ path: testInfo.outputPath("stored-history-dark-390-volume.png"), fullPage: true });
      await page.locator(".stored-history").screenshot({ path: testInfo.outputPath("stored-history-focused-dark-390-volume.png") });
    }
    await page.getByRole("button", { name: "Close detail" }).focus();
    await page.keyboard.press("Enter");
    await expect(page.getByLabel("Saved namespace")).toBeFocused();
    await expect(page.getByRole("heading", { name: "Stored-row detail / DEMO" })).toHaveCount(0);
  });
}
test("disabled history is explicit and invalid paired dates never send a history request", async ({ page }, testInfo) => {
  let historyReads = 0;
  await page.route("**/api/**", async route => {
    if (new URL(route.request().url()).pathname === "/api/v1/watchlists/menu_watchlist") return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(saved()) });
    historyReads++;
    await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ error: { code: "history_disabled", message: "Historical acquisition is disabled." } }) });
  });
  await configure(page); await open(page);
  await page.getByLabel("Start date", { exact: true }).fill("2020-01-02");
  await page.getByRole("button", { name: "Read raw history" }).click();
  await expect(page.getByLabel("Start date", { exact: true })).toBeFocused();
  await expect(page.getByRole("alert").locator("p")).toHaveText("Request input is invalid.");
  expect(historyReads).toBe(0);
  await page.getByLabel("End date", { exact: true }).fill("2020-01-06");
  await page.getByRole("button", { name: "Read raw history" }).click();
  await expect(page.getByText("Historical acquisition disabled", { exact: true })).toBeVisible();
  await expect(page.getByRole("img")).toHaveCount(0);
  await expect(page.getByRole("table", { name: "Exact raw history / saved row" })).toHaveCount(0);
  expect(historyReads).toBe(1);
  await label(page);
  expect(await page.locator('input[type="password"]').count()).toBe(0);
  await page.locator(".stored-history").screenshot({ path: testInfo.outputPath("stored-history-disabled-desktop.png") });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator(".stored-history").screenshot({ path: testInfo.outputPath("stored-history-disabled-mobile.png") });
});
test("changed duplicate association requires a new choice and 401 clears private detail", async ({ page }) => {
  let listReads = 0;
  await page.route("**/api/**", async route => {
    if (new URL(route.request().url()).pathname.includes("/history")) return route.fulfill({ status: 401, body: "Not displayed" });
    const view = saved();
    const current = ++listReads;
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(current >= 2 ? { ...view, entries: view.entries.map(row => ({ ...row, stock: { ...row.stock, name: "Changed stored identity" } })) } : view) });
  });
  await configure(page);
  await page.getByRole("button", { name: "Read saved entries" }).click();
  await page.getByRole("button", { name: "Open detail for row 1" }).click();
  await expect(page.getByRole("alert")).toContainText("The request-local row changed.");
  await expect(page.getByRole("heading", { name: "Stored-row detail / DEMO" })).toHaveCount(0);
  await page.getByRole("button", { name: "Open detail for row 1" }).click();
  await expect(page.getByRole("heading", { name: "Stored-row detail / DEMO" })).toBeFocused();
  await page.getByRole("button", { name: "Read raw history" }).click();
  await expect(page.getByText("Saved reads disconnected", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Stored-row detail / DEMO" })).toHaveCount(0);
  await expect(page.getByRole("table")).toHaveCount(0);
});
test("keyboard history cancellation keeps focus and rejects a cancelled late response", async ({ page }) => {
  let release!: () => void;
  const held = new Promise<void>(resolve => { release = resolve; });
  let reads = 0;
  await page.route("**/api/**", async route => {
    if (new URL(route.request().url()).pathname === "/api/v1/watchlists/menu_watchlist") return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(saved()) });
    const current = ++reads;
    if (current === 1) await held;
    try { await route.fulfill({ status: 200, contentType: "application/json", body: rawHistory() }); }
    catch (error) { if (current !== 1 || route.request().failure()?.errorText !== "net::ERR_ABORTED") throw error; }
  });
  await configure(page); await open(page);
  await page.getByRole("button", { name: "Read raw history" }).click();
  await expect.poll(() => reads).toBe(1);
  await page.getByRole("button", { name: "Cancel history read" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("button", { name: "Read raw history" })).toBeFocused();
  await expect(page.getByText("History read cancelled", { exact: true })).toBeVisible();
  release();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("table", { name: "Exact raw history / saved row" })).toBeVisible();
  expect(reads).toBe(2);
});
test("long untrusted stored symbols wrap inside the phone detail heading", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const view = saved();
  await page.route("**/api/v1/watchlists/menu_watchlist", route => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ...view,
    entries: view.entries.map(row => ({ ...row, stock: { ...row.stock, symbol: "SYNTHETIC".repeat(100) } })),
  }) }));
  await configure(page);
  await page.getByRole("button", { name: "Read saved entries" }).click();
  await page.getByRole("button", { name: "Open detail for row 1" }).click();
  await expect(page.locator("#stored-detail-title")).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
