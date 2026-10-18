import { expect, test } from "@playwright/test";
import { epsResponse } from "../tests/eps-fixtures";
for (const scenario of [{ theme: "light", width: 1440 }, { theme: "dark", width: 320 }] as const) {
  test(`manual exact EPS ${scenario.theme} at ${scenario.width}px has honest provenance and private lifecycle`, async ({ page }, info) => {
    await page.setViewportSize({ width: scenario.width, height: 1000 });
    await page.addInitScript(theme => localStorage.setItem("stock-tracker.theme", theme), scenario.theme);
    const paths: string[] = [];
    let state: "success" | "empty" | "quota" | "auth" = "success";
    await page.route("**/api/**", async route => {
      const url = new URL(route.request().url()); paths.push(url.pathname + url.search);
      expect(url.pathname).toBe("/api/v1/research/upcoming-eps");
      expect(route.request().method()).toBe("GET");
      expect(url.search).toBe("?provider_symbol=TEST&start=2026-10-18&end=2027-01-17");
      const data = epsResponse(); if (state === "empty") data.observations = [];
      await route.fulfill({ status: state === "quota" ? 429 : state === "auth" ? 401 : 200,
        contentType: "application/json", body: JSON.stringify(state === "quota" ? { error: { code: "eps_rate_limited", message: "Upcoming EPS request budget is unavailable." } } : state === "auth" ? { error: { code: "unauthorized", message: "Authentication is required." } } : data) });
    });
    await page.goto("/#upcoming-eps");
    await expect(page.getByRole("button", { name: "Read upcoming EPS", exact: true })).toBeDisabled();
    await expect(page.getByLabel("Finnhub provider symbol", { exact: true })).toHaveValue("");
    expect(paths).toEqual([]);
    await page.getByRole("link", { name: "Settings", exact: true }).first().click();
    await page.getByLabel("Local API token", { exact: true }).evaluate(element => {
      if (!(element instanceof HTMLInputElement)) throw new Error("Expected masked control");
      element.value = Array.from({ length: 48 }, (_, i) => String.fromCharCode(65 + i * 7 % 26)).join("");
      element.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await page.getByRole("button", { name: "Configure connection", exact: true }).click();
    await page.getByRole("link", { name: "Upcoming EPS", exact: true }).click();
    await expect(page.getByRole("heading", { level: 1 })).toBeFocused();
    await page.getByRole("button", { name: "Read upcoming EPS", exact: true }).click();
    await expect(page.getByLabel("Finnhub provider symbol", { exact: true })).toBeFocused();
    expect(paths).toEqual([]);
    await page.getByLabel("Finnhub provider symbol", { exact: true }).fill("TEST");
    await page.getByLabel("EPS start date", { exact: true }).fill("2026-10-18");
    await page.getByLabel("EPS end date", { exact: true }).fill("2027-01-17");
    await page.getByRole("button", { name: "Read upcoming EPS", exact: true }).focus(); await page.keyboard.press("Enter");
    await expect(page.getByRole("cell", { name: "1.250000000000000001", exact: true })).toBeVisible();
    await expect(page.getByRole("cell", { name: "0", exact: true })).toHaveCount(1);
    await expect(page.getByRole("cell", { name: "-0.25", exact: true })).toHaveCount(1);
    await expect(page.getByRole("cell", { name: "Unavailable (null estimate)", exact: true })).toHaveCount(1);
    await expect(page.getByText(/Currency: unknown. Basic\/diluted share basis: unknown/)).toBeVisible();
    const table = page.getByRole("region", { name: "Exact upcoming non-GAAP EPS / unknown currency", exact: true });
    await table.focus();
    if (await table.evaluate(element => element.scrollWidth > element.clientWidth)) { await page.keyboard.press("ArrowRight"); await expect.poll(() => table.evaluate(element => element.scrollLeft)).toBeGreaterThan(0); }
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await expect(page.locator("html")).toHaveAttribute("data-theme", scenario.theme);
    await page.evaluate(() => { const label = document.createElement("p"); label.className = "demo-label"; label.textContent = "Synthetic EPS fixture / no live data / rights not activated"; document.querySelector("main h1")?.after(label); });
    expect(await page.locator('input[type="password"]').count()).toBe(0);
    await page.screenshot({ path: info.outputPath(`upcoming-eps-${scenario.theme}-${scenario.width}.png`), fullPage: true });
    expect(paths.length).toBe(1);
    await page.getByLabel("EPS end date", { exact: true }).fill("2027-01-16");
    await expect(page.getByRole("table")).toHaveCount(0);
    await page.getByLabel("EPS end date", { exact: true }).fill("2027-01-17");
    state = "empty"; await page.getByRole("button", { name: "Read upcoming EPS", exact: true }).click();
    await expect(page.getByText("No observations returned", { exact: true })).toBeVisible();
    state = "quota"; await page.getByRole("button", { name: "Read upcoming EPS", exact: true }).click();
    await expect(page.getByRole("alert")).toContainText("Wait at least 60 seconds"); expect(paths.length).toBe(3);
    state = "auth"; await page.getByRole("button", { name: "Read upcoming EPS", exact: true }).click();
    await expect(page.getByRole("alert")).toContainText("Authentication is required");
    await expect(page.getByRole("table")).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Read upcoming EPS", exact: true })).toBeDisabled();
    expect(paths.length).toBe(4);
    await page.getByRole("button", { name: "Clear EPS", exact: true }).click();
    await expect(page.getByLabel("Finnhub provider symbol", { exact: true })).toHaveValue("");
    await page.reload();
    await expect(page.getByLabel("EPS start date", { exact: true })).toHaveValue("");
    expect(await page.evaluate(() => Object.keys(localStorage))).toEqual(["stock-tracker.theme"]);
    expect(await page.evaluate(() => Object.keys(sessionStorage))).toEqual([]);
  });
}
