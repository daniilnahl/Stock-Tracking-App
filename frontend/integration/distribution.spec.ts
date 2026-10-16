import { test, expect } from "@playwright/test";
import { spawn, execFile } from "node:child_process";
import { createHash, randomBytes } from "node:crypto";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync } from "node:fs";
import { createServer } from "node:net";
import { resolve, join } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

const frontend = fileURLToPath(new URL("../", import.meta.url));
const repository = resolve(frontend, "..");
const python = process.env.STOCK_TRACKER_TEST_PYTHON ?? join(repository, process.platform === "win32" ? ".venv/Scripts/python.exe" : ".venv/bin/python");
const execute = promisify(execFile);
const origin = "http://127.0.0.1:8000";
const names = ["index.html", "hosting.js", "hosting.css", "stock-pixel.ttf", "LICENSE.txt"];
const digest = (bytes: Buffer) => createHash("sha256").update(bytes).digest("hex");
if (process.env.STOCK_TRACKER_DIAGNOSTIC_PROBE === "1") {
  test("explicit negative privacy diagnostic probe", async ({ page }) => {
    await page.setContent('<p>Synthetic diagnostic page marker</p><input type="password">');
    await page.locator("input").evaluate(element => {
      if (!(element instanceof HTMLInputElement)) throw new Error("Expected masked control");
      element.value = Array.from(crypto.getRandomValues(new Uint8Array(48)), value => String.fromCharCode(65 + value % 26)).join("");
    });
    // Deliberate fixed boolean failure: the separate manual probe must exit1
    // with no trace/video/screenshot or automatic page/ARIA snapshot artifact.
    expect(false).toBe(true);
  });
}
async function vacantPort() {
  const probe = createServer();
  await new Promise<void>((accept, reject) => {
    probe.once("error", () => reject(new Error("Port 8000 is occupied; no listener was stopped.")));
    probe.listen({ host: "127.0.0.1", port: 8000, exclusive: true }, () => probe.close(error => error ? reject(new Error("Port preflight failed.")) : accept()));
  });
}
test("actual source/wheel launcher serves the closed dashboard and authenticated synthetic workflows", async ({ page, request }, testInfo) => {
  test.setTimeout(90000);
  const wheel = testInfo.project.name === "wheel";
  mkdirSync(join(frontend, ".cache"), { recursive: true });
  const state = mkdtempSync(join(frontend, ".cache/issue155-"));
  let moduleRoot = join(repository, "src");
  if (wheel) {
    const env = { ...process.env, PIP_NO_INDEX: "1", PIP_DISABLE_PIP_VERSION_CHECK: "1" };
    // No installation mutates the canonical environment; output stays private.
    try {
      await execute(python, ["-m", "pip", "wheel", repository, "--no-deps", "--no-build-isolation", "--wheel-dir", state], { env, timeout: 60000 });
      const archive = readdirSync(state).filter(name => name.endsWith(".whl"));
      if (archive.length !== 1) throw new Error("Wheel count");
      moduleRoot = join(state, "installed");
      await execute(python, ["-m", "pip", "install", join(state, archive[0]!), "--no-deps", "--no-compile", "--target", moduleRoot], { env, timeout: 60000 });
    } catch { throw new Error("Offline isolated wheel preparation failed; subprocess output is not disclosed."); }
  }
  await vacantPort();
  const token = randomBytes(36).toString("base64url");
  const child = spawn(python, ["-I", "-B", join(repository, "tests/dashboard_browser_server.py"), moduleRoot, state], {
    cwd: state, windowsHide: true, stdio: ["ignore", "pipe", "pipe"],
    env: { ...process.env, STOCK_TRACKER_API_TOKEN: token, PYTHONDONTWRITEBYTECODE: "1" },
  });
  const output: Buffer[] = [];
  child.stdout.on("data", data => output.push(Buffer.from(data)));
  child.stderr.on("data", data => output.push(Buffer.from(data)));
  let spawnFailed = false;
  child.on("error", () => { spawnFailed = true; });
  try {
    let ready = false;
    for (let attempt = 0; attempt < 100; attempt++) {
      if (spawnFailed || child.exitCode !== null) throw new Error("Owned synthetic launcher exited before readiness; child output is not disclosed.");
      try { const response = await fetch(origin); ready = response.status === 200; await response.arrayBuffer(); } catch { /* Only startup connection refusal is expected. */ }
      if (ready) break;
      await new Promise(accept => setTimeout(accept, 100));
    }
    expect(ready).toBe(true);
    const before = digest(readFileSync(join(state, "holdings.sqlite3")));
    const assets = join(moduleRoot, "stock_tracker/api/dashboard_assets");
    expect(readdirSync(assets).sort()).toEqual([...names].sort());
    for (const name of names) {
      const route = name === "index.html" ? "/" : `/dashboard-assets/${name}`;
      const response = await request.get(route);
      expect(response.status()).toBe(200);
      const bytes = await response.body();
      expect(bytes.equals(readFileSync(join(assets, name)))).toBe(true);
      expect(bytes.equals(readFileSync(join(repository, "src/stock_tracker/api/dashboard_assets", name)))).toBe(true);
      expect(bytes.includes(Buffer.from(token))).toBe(false);
      expect(response.headers()["content-security-policy"]).toBe("default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; form-action 'none'");
      expect(response.headers()["cache-control"]).toBe("no-store");
    }
    expect((await request.get("/api/v1/watchlists/menu_watchlist")).status()).toBe(401);
    expect((await request.get("/", { headers: { Origin: "https://outside.invalid" } })).status()).toBe(403);
    expect((await request.get("/dashboard-assets/hosting.js.map")).status()).toBe(404);
    const apiPaths: string[] = [];
    let external = false; let pageError = false; let cspFailure = false;
    page.on("request", request => { const url = new URL(request.url()); if (url.origin !== origin) external = true; if (url.pathname.startsWith("/api/")) apiPaths.push(url.pathname); });
    page.on("pageerror", () => { pageError = true; });
    page.on("console", message => { if (/content security|violat|refused to/i.test(message.text())) cspFailure = true; });
    await page.setViewportSize(wheel ? { width: 390, height: 844 } : { width: 1440, height: 1100 });
    await page.goto("/#settings");
    let consumed = false;
    // Test-context-only one-shot binding: no credential argument is recorded by
    // Playwright and no production bridge/global secret is introduced.
    await page.exposeBinding("takeSyntheticConnectionOnce", () => {
      if (consumed) throw new Error("Synthetic credential transfer already consumed.");
      consumed = true; return token;
    });
    const field = page.getByLabel("Local API token", { exact: true });
    await field.evaluate(async element => {
      const obtain = (window as unknown as { takeSyntheticConnectionOnce: () => Promise<string> }).takeSyntheticConnectionOnce;
      if (!(element instanceof HTMLInputElement)) throw new Error("Expected masked field");
      element.value = await obtain(); element.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await page.getByRole("button", { name: "Configure connection" }).click();
    expect(await field.evaluate(element => element instanceof HTMLInputElement && element.value.length === 0)).toBe(true);
    expect(apiPaths.length).toBe(0);
    if (wheel) await page.getByLabel("Theme", { exact: true }).selectOption("dark");
    await page.getByRole("link", { name: "Watchlists", exact: true }).click();
    await page.getByRole("button", { name: "Read saved entries" }).click();
    await expect(page.getByRole("table")).toBeVisible();
    await expect(page.getByRole("cell", { name: "0.12345678901234567890123456789", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Open detail for row 2" })).toBeVisible();
    await page.getByRole("button", { name: "Open detail for row 0" }).click();
    await expect(page.locator("#stored-detail-title")).toBeFocused();
    const historyResponse = page.waitForResponse(response => new URL(response.url()).pathname.endsWith("/entries/0/history"));
    await page.getByRole("button", { name: "Read raw history" }).click();
    expect((await historyResponse).status()).toBe(503);
    await expect(page.getByText("Historical acquisition disabled", { exact: true })).toBeVisible();
    await page.evaluate(() => { const label = document.createElement("p"); label.className = "demo-label"; label.textContent = "Synthetic actual launcher / no live data / rights not activated"; document.querySelector("#stored-history-title")?.after(label); });
    expect((await page.content()).includes(token)).toBe(false);
    expect(await page.locator('input[type="password"]').count()).toBe(0);
    await page.locator(".stored-history").screenshot({ path: testInfo.outputPath(`issue155-${testInfo.project.name}-disabled-history.png`) });
    await page.getByRole("button", { name: "Close detail" }).click();
    await page.getByLabel("Saved namespace").selectOption("daniils_stock_method");
    await page.getByRole("button", { name: "Read saved entries" }).click();
    await expect(page.getByRole("heading", { name: "Synthetic local integration / Method" })).toBeVisible();
    await expect(page.getByRole("table").getByRole("row")).toHaveCount(3);
    await page.getByRole("link", { name: "Overview", exact: true }).click();
    expect(await page.getByRole("status", { name: "Saved entry count for Daniil's stock method" }).evaluate(element => element.textContent === "2")).toBe(true);
    await expect(page.getByRole("heading", { name: "Recommend stock of the day" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Taurus Agents Menu" })).toBeVisible();
    await page.evaluate(() => { const label = document.createElement("p"); label.className = "demo-label"; label.textContent = "Synthetic actual launcher / no live data / rights not activated"; document.querySelector("main h1")?.after(label); });
    expect((await page.content()).includes(token)).toBe(false);
    expect(await page.evaluate(() => document.fonts.check('20px "Stock Pixel"'))).toBe(true);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    expect(await page.evaluate(() => Object.keys(localStorage).every(key => key === "stock-tracker.theme") && Object.keys(sessionStorage).length === 0)).toBe(true);
    expect(await page.locator('input[type="password"]').count()).toBe(0);
    await page.screenshot({ path: testInfo.outputPath(`issue155-${testInfo.project.name}-overview.png`), fullPage: true });
    await page.getByRole("link", { name: "Settings", exact: true }).click();
    await page.getByRole("button", { name: "Disconnect", exact: true }).click();
    await page.reload();
    await expect(page.getByText("Disconnected", { exact: true })).toBeVisible();
    expect(await field.evaluate(element => element instanceof HTMLInputElement && element.value.length === 0)).toBe(true);
    expect(external || pageError || cspFailure).toBe(false);
    expect(JSON.stringify(apiPaths) === JSON.stringify(["/api/v1/watchlists/menu_watchlist", "/api/v1/watchlists/menu_watchlist", "/api/v1/watchlists/menu_watchlist/entries/0/history", "/api/v1/watchlists/daniils_stock_method"])).toBe(true);
    expect(digest(readFileSync(join(state, "holdings.sqlite3"))) === before).toBe(true);
    expect(["history.json", "menu.pkl", "method.pkl"].every(name => !existsSync(join(state, name)))).toBe(true);
  } finally {
    if (child.exitCode === null && !spawnFailed) {
      const exited = new Promise<void>(accept => child.once("exit", () => accept()));
      child.kill(); await exited;
    }
    const diagnostics = Buffer.concat(output).toString("utf8");
    expect(diagnostics.includes(token)).toBe(false);
    expect(diagnostics.split(/\r?\n/).filter(Boolean).every(line => /^API operation failed: (unauthorized|origin_forbidden|history_disabled|not_found)$/.test(line))).toBe(true);
  }
});
