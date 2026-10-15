import { expect, test } from "@playwright/test";

for (const viewport of [{ width: 1440, height: 1100 }, { width: 390, height: 844 }]) {
  test(`production demo exact values and keyboard at ${viewport.width}px`, async ({ page }, testInfo) => {
    await page.setViewportSize(viewport);
    const privateRequests: string[] = [];
    page.on("request", request => { if (request.url().includes("/api/")) privateRequests.push(request.url()); });
    await page.route("**/*", route => route.request().url().startsWith("http://127.0.0.1:8000/") ? route.continue() : route.abort());
    await page.goto("/");
    await expect(page.getByText("Synthetic client foundation demo - no live data")).toBeVisible();
    await page.evaluate(() => document.fonts.ready);
    expect(await page.evaluate(() => document.fonts.check('20px "Stock Pixel"'))).toBe(true);
    await page.keyboard.press("Tab");
    await expect(page.getByRole("button", { name: "Check synthetic response" })).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page.getByText("110.0000000000000000001")).toBeVisible();
    await expect(page.getByText("9223372036854775807")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath(`client-foundation-${viewport.width}.png`), fullPage: true });
    await page.getByRole("button", { name: "Show safe error state" }).click();
    await expect(page.getByRole("alert")).toHaveText("The API response is incompatible. No data was published.");
    await expect(page.getByText("9223372036854775807")).toHaveCount(0);
    await page.getByRole("button", { name: "Clear demonstration" }).click();
    await expect(page.getByText("No demonstration values loaded.")).toBeVisible();
    expect(privateRequests).toEqual([]);
  });
}
test("unsupported browser displays prerequisite and prevents numeric demo", async ({ page }) => {
  await page.addInitScript(() => {
    const native = JSON.parse;
    JSON.parse = (text, reviver) => native(text, reviver ? (key, value) => reviver(key, value) : undefined);
  });
  await page.goto("/");
  await expect(page.getByRole("status")).toHaveText("This browser cannot decode exact API numbers. Use a current supported browser.");
  await expect(page.getByRole("button", { name: "Check synthetic response" })).toBeDisabled();
});
