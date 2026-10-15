import { expect, test } from "@playwright/test";

function luminance(hex: string): number {
  const value = hex.slice(1);
  const six = value.length === 3 ? [...value].map(char => char + char).join("") : value;
  const channels = [0, 2, 4].map(offset => {
    const channel = Number.parseInt(six.slice(offset, offset + 2), 16) / 255;
    return channel <= .04045 ? channel / 12.92 : ((channel + .055) / 1.055) ** 2.4;
  });
  return channels[0]! * .2126 + channels[1]! * .7152 + channels[2]! * .0722;
}
function contrast(left: string, right: string): number {
  const values = [luminance(left), luminance(right)].sort((a, b) => b - a);
  return (values[0]! + .05) / (values[1]! + .05);
}
for (const viewport of [{ width: 1440, height: 1100 }, { width: 768, height: 1024 }, { width: 390, height: 844 }]) {
  for (const theme of ["light", "dark"] as const) {
    test(`shell ${theme} at ${viewport.width}px preserves layout, font, contrast and honest states`, async ({ page }, testInfo) => {
      await page.setViewportSize(viewport);
      if (theme === "dark") await page.addInitScript(() => localStorage.setItem("stock-tracker.theme", "dark"));
      const requests: string[] = [];
      page.on("request", request => { if (request.url().includes("/api/")) requests.push(request.url()); });
      await page.route("**/*", route => route.request().url().startsWith("http://127.0.0.1:8000/") ? route.continue() : route.abort());
      await page.goto("/");
      await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
      await expect(page.getByRole("heading", { name: "Your watchlists, clearly." })).toBeVisible();
      await expect(page.getByRole("navigation").getByRole("link")).toHaveCount(3);
      await expect(page.getByText("Placeholder / unavailable")).toHaveCount(2);
      await page.evaluate(() => document.fonts.ready);
      expect(await page.evaluate(() => document.fonts.check('20px "Stock Pixel"'))).toBe(true);
      const layout = await page.evaluate(() => {
        const recommend = document.getElementById("recommend-title")!.getBoundingClientRect();
        const taurus = document.getElementById("taurus-title")!.getBoundingClientRect();
        const cards = document.querySelector(".cards")!.getBoundingClientRect();
        const style = getComputedStyle(document.documentElement);
        return { recommend: recommend.top, taurus: taurus.top, cards: cards.top,
          noOverflow: document.documentElement.scrollWidth <= innerWidth,
          colors: Object.fromEntries(["text", "muted", "background", "surface", "focus", "control-border"].map(name => [name, style.getPropertyValue(`--${name}`).trim()])),
          font: getComputedStyle(document.querySelector("button")!).fontFamily,
          motion: style.getPropertyValue("--motion-duration").trim(),
        };
      });
      expect(layout.recommend).toBeLessThan(layout.taurus);
      expect(layout.taurus).toBeLessThan(layout.cards);
      expect(layout.noOverflow).toBe(true);
      expect(layout.font).toContain("Stock Pixel");
      expect(layout.motion).toBe("0s");
      for (const background of ["background", "surface"]) {
        for (const text of ["text", "muted"]) expect(contrast(layout.colors[text]!, layout.colors[background]!)).toBeGreaterThanOrEqual(4.5);
        for (const control of ["focus", "control-border"]) expect(contrast(layout.colors[control]!, layout.colors[background]!)).toBeGreaterThanOrEqual(3);
      }
      await page.screenshot({ path: testInfo.outputPath(`shell-${theme}-${viewport.width}.png`), fullPage: true });
      await page.getByRole("button", { name: "Search / add stock" }).click();
      await expect(page.getByText("Unavailable - backend search/add is not implemented.")).toBeVisible();
      await expect(page.getByRole("link", { name: "Read the backend and frontend TO-DO LIST" })).toHaveAttribute("rel", "noopener noreferrer");
      const tableRegion = page.getByRole("region", { name: "Saved observations - not connected" });
      await tableRegion.focus();
      await expect(tableRegion).toBeFocused();
      if (viewport.width === 390) {
        expect(await tableRegion.evaluate(element => element.scrollWidth > element.clientWidth)).toBe(true);
        await expect(page.getByText("Scroll horizontally if the table extends beyond the screen.")).toBeVisible();
      }
      expect(requests).toEqual([]);
    });
  }
}
test("keyboard skip, navigation/back, theme controls and persistence", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Skip to content" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("main")).toBeFocused();
  expect(new URL(page.url()).hash).toBe("");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Your watchlists, clearly.");
  await page.getByRole("link", { name: "Settings", exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { level: 1, name: "Make yourself at home." })).toBeFocused();
  await expect(page.getByRole("link", { name: "Settings", exact: true })).toHaveAttribute("aria-current", "page");
  await page.getByRole("combobox", { name: "Theme" }).focus();
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Enter");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.getByRole("button", { name: "Light theme" })).not.toHaveAttribute("aria-pressed");
  expect(await page.evaluate(() => Object.keys(localStorage))).toEqual(["stock-tracker.theme"]);
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("link", { name: "Watchlists", exact: true }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Saved watchlists");
  await page.goBack();
  await expect(page.getByRole("heading", { level: 1, name: "Make yourself at home." })).toBeFocused();
  await page.getByRole("button", { name: "Light theme" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.getByRole("link", { name: "Synthetic client foundation demo", exact: true }).click();
  await expect(page.getByRole("main")).toHaveCount(1);
  await expect(page.getByRole("heading", { level: 1 })).toHaveCount(1);
});
test("blocked storage switches only the page theme and announces failure honestly", async ({ page }) => {
  await page.addInitScript(() => {
    Storage.prototype.getItem = () => { throw new DOMException("Blocked", "SecurityError"); };
    Storage.prototype.setItem = () => { throw new DOMException("Blocked", "SecurityError"); };
  });
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.getByRole("status")).toContainText("Theme preference storage is unavailable");
  await page.getByRole("button", { name: "Dark theme" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.getByRole("status")).toContainText("could not be saved");
});
