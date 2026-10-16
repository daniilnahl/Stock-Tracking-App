import { expect } from "@playwright/test";
import type { Page, TestInfo } from "@playwright/test";

// Independent exit assertions against the already-running real launcher.
// No route interception, credential access or application test hook.
export async function auditPresentation(page: Page, info: TestInfo, assertSafeCapture: () => Promise<void>) {
  for (const width of [1440, 820, 390, 320]) for (const theme of ["light", "dark"]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.getByRole("link", { name: "Settings", exact: true }).click();
    await page.getByLabel("Theme", { exact: true }).selectOption(theme);
    await page.getByRole("link", { name: "Watchlists", exact: true }).focus();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("heading", { level: 1 })).toBeFocused();
    await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
    await expect(page.getByRole("table")).toBeVisible();
    const region = page.getByRole("region", { name: "Daniil's stock method / saved entries", exact: true });
    await region.focus();
    if (await region.evaluate(element => element.scrollWidth > element.clientWidth)) {
      await page.keyboard.press("ArrowRight");
      await expect.poll(() => region.evaluate(element => element.scrollLeft > 0)).toBe(true);
    }
    await page.getByRole("link", { name: "Skip to content", exact: true }).focus();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("main")).toBeFocused();
    expect(new URL(page.url()).hash === "#watchlists").toBe(true);
    const pageOverflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    if (pageOverflow) {
      const shapes = await page.evaluate(() => [...document.querySelectorAll("body *")].filter(element => element.getBoundingClientRect().right > innerWidth && !element.closest("table"))
        .map(element => ({ tag: element.tagName, className: typeof element.className === "string" ? element.className : "svg" })));
      throw new Error(`Viewport ${width} overflow in element types: ${JSON.stringify(shapes)}`);
    }
    expect(await page.locator("main").evaluate(element => [...element.querySelectorAll("h1,h2,p,button,a,th,td")]
      .every(node => getComputedStyle(node).fontFamily.includes("Stock Pixel")))).toBe(true);
    await page.getByRole("link", { name: "Overview", exact: true }).click();
    if (info.project.name === "wheel") {
      expect(await page.locator('input[type="password"]').count()).toBe(0);
      await assertSafeCapture();
      await page.evaluate(() => {
        document.querySelectorAll(".demo-label").forEach(element => element.remove());
        const label = document.createElement("p"); label.className = "demo-label";
        label.textContent = "M8 exit audit / synthetic installed-wheel launcher / no live data / rights not activated";
        document.querySelector("main h1")?.after(label);
      });
      await page.screenshot({ path: info.outputPath(`issue148-wheel-${theme}-${width}.png`), fullPage: true });
    }
  }

  // CSSOM emulates a user's text override under the unchanged strict CSP.
  // This is 200% text sizing, not a claim about browser chrome zoom or every AT.
  await page.setViewportSize({ width: 820, height: 1000 });
  await page.evaluate(() => {
    document.documentElement.style.fontSize = "40px";
    for (const node of document.querySelectorAll<HTMLElement>("h1,h2,h3,p,a,button,select,label")) {
      node.style.lineHeight = "1.5"; node.style.letterSpacing = ".12em"; node.style.wordSpacing = ".16em";
      if (node.tagName === "P") node.style.marginBottom = "2em";
    }
  });
  const overflow = await page.evaluate(() => [...document.querySelectorAll("body *")].filter(element => element.getBoundingClientRect().right > innerWidth)
    .map(element => ({ tag: element.tagName, className: typeof element.className === "string" ? element.className : "svg" })));
  expect(overflow).toEqual([]);
  await expect(page.getByRole("heading", { name: "Taurus Agents Menu" })).toBeVisible();
  if (info.project.name === "wheel") {
    expect(await page.locator('input[type="password"]').count()).toBe(0);
    await assertSafeCapture();
    await page.locator(".demo-label").evaluate(element => {
      element.textContent = "Synthetic wheel / 200% CSS text (not native zoom) / no live data / rights not activated";
      if (element instanceof HTMLElement) element.style.fontSize = "20px"; // Artifact label only.
      document.body.prepend(element); // Keep the disclosure inside this viewport-only capture.
    });
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: info.outputPath("issue148-wheel-text-200percent-820.png"), fullPage: false });
    await page.locator(".demo-label").evaluate(element => element.remove());
  }
  await page.getByRole("link", { name: "Open Watchlists", exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { level: 1 })).toBeFocused();
  await expect(page.getByRole("table")).toBeVisible();
  await page.evaluate(() => {
    document.documentElement.style.removeProperty("font-size");
    for (const node of document.querySelectorAll<HTMLElement>("[style]")) {
      for (const name of ["line-height", "letter-spacing", "word-spacing", "margin-bottom"]) node.style.removeProperty(name);
    }
  });
  await page.emulateMedia({ forcedColors: "active", reducedMotion: "reduce" });
  expect(await page.evaluate(() => matchMedia("(forced-colors: active)").matches && matchMedia("(prefers-reduced-motion: reduce)").matches)).toBe(true);
  await page.getByRole("button", { name: "Reload saved entries" }).focus();
  expect(await page.getByRole("button", { name: "Reload saved entries" }).evaluate(element => {
    const style = getComputedStyle(element);
    return style.outlineStyle !== "none" && parseFloat(style.outlineWidth) >= 2 && style.boxShadow === "none" && style.transitionDuration === "0s";
  })).toBe(true);
  await page.emulateMedia({ forcedColors: "none", reducedMotion: "reduce" });
  await page.getByRole("link", { name: "Overview", exact: true }).click();
}

export async function auditReloadAndUnauthorized(page: Page) {
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.getByRole("status", { name: "Saved entry count unavailable" })).toHaveText("Unavailable");
  expect(await page.getByText("Synthetic local integration / Method", { exact: false }).count()).toBe(0);
  await page.getByRole("link", { name: "Settings", exact: true }).click();
  const field = page.getByLabel("Local API token", { exact: true });
  expect(await field.evaluate(element => element instanceof HTMLInputElement && element.value.length === 0)).toBe(true);
  await field.evaluate(element => {
    if (!(element instanceof HTMLInputElement)) throw new Error("Expected masked control");
    // Invalid for this server, syntactically valid; never returned or logged.
    element.value = Array.from(crypto.getRandomValues(new Uint8Array(48)), value => String.fromCharCode(65 + value % 26)).join("");
    element.dispatchEvent(new Event("input", { bubbles: true }));
  });
  await page.getByRole("button", { name: "Configure connection" }).click();
  await page.getByRole("link", { name: "Watchlists", exact: true }).click();
  const denied = page.waitForResponse(response => new URL(response.url()).pathname === "/api/v1/watchlists/menu_watchlist");
  await page.getByRole("button", { name: "Read saved entries" }).click();
  expect((await denied).status()).toBe(401);
  await expect(page.getByText("Saved reads disconnected", { exact: true })).toBeVisible();
  expect(await page.getByRole("table").count()).toBe(0);
  await page.getByRole("link", { name: "Overview", exact: true }).click();
  await expect(page.getByRole("status", { name: "Saved entry count unavailable" })).toHaveText("Unavailable");
  expect(await page.evaluate(() => Object.keys(localStorage).every(key => key === "stock-tracker.theme") && Object.keys(sessionStorage).length === 0)).toBe(true);
}
