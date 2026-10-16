import { afterEach, describe, expect, it } from "vitest";
import { mkdtempSync, mkdirSync, readFileSync, readdirSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { packageDashboard } from "../scripts/package-dashboard.mjs";

const directories: string[] = [];
afterEach(() => { for (const directory of directories.splice(0)) {
  if (dirname(directory) !== resolve(tmpdir()) || !directory.startsWith(join(resolve(tmpdir()), "dashboard-bridge-"))) throw new Error("Unexpected test cleanup target");
  rmSync(directory, { recursive: true });
} });
function fixture() {
  const root = mkdtempSync(join(resolve(tmpdir()), "dashboard-bridge-")); directories.push(root);
  const dist = join(root, "dist"); const destination = join(root, "packaged"); const modules = join(root, "modules");
  for (const directory of [dist, destination, join(root, "docs/previews/assets")]) mkdirSync(directory, { recursive: true });
  const data = { "index.html": '<div id="root"></div><script type="module" src="/dashboard-assets/hosting.js"></script><link href="/dashboard-assets/hosting.css">',
    "hosting.js": "// synthetic compiled application", "hosting.css": '@font-face{src:url(/dashboard-assets/stock-pixel.ttf)}', "stock-pixel.ttf": "synthetic font bytes" };
  for (const [name, text] of Object.entries(data)) { writeFileSync(join(dist, name), text); writeFileSync(join(destination, name), "prior packaged bytes"); }
  writeFileSync(join(destination, "LICENSE.txt"), "prior license");
  writeFileSync(join(root, "LICENSE"), "MIT project/font license\r\n");
  writeFileSync(join(root, "docs/previews/assets/stock-pixel.ttf"), data["stock-pixel.ttf"]);
  for (const [name, version] of [["react", "19.3.1"], ["react-dom", "19.3.1"], ["scheduler", "0.28.0"], ["vite", "8.3.4"]]) {
    mkdirSync(join(modules, name!), { recursive: true });
    writeFileSync(join(modules, name!, "package.json"), JSON.stringify({ name, version, license: "MIT" }));
    writeFileSync(join(modules, name!, name === "vite" ? "LICENSE.md" : "LICENSE"), name === "vite" ? "# Vite core license\nMIT notice for vite\n# Licenses of bundled dependencies\nDev-only bundled notice\n" : `MIT notice for ${name}\r\n`);
  }
  return { root, dist, destination, modules };
}
const bytes = (directory: string) => Object.fromEntries(readdirSync(directory).map(name => [name, readFileSync(join(directory, name)).toString("hex")]));
describe("deliberate closed distribution bridge", () => {
  it("copies exact bytes and production notices deterministically, and --check writes nothing", () => {
    const options = fixture();
    expect(packageDashboard(options)).toEqual(["LICENSE.txt", "hosting.css", "hosting.js", "index.html", "stock-pixel.ttf"]);
    const first = bytes(options.destination);
    packageDashboard(options); expect(bytes(options.destination)).toEqual(first);
    packageDashboard({ ...options, check: true }); expect(bytes(options.destination)).toEqual(first);
    const license = readFileSync(join(options.destination, "LICENSE.txt"), "utf8");
    expect(license).toContain("MIT project/font license\n");
    for (const name of ["react", "react-dom", "scheduler", "vite"]) expect(license).toContain(`MIT notice for ${name}\n`);
    expect(license).not.toContain("Dev-only bundled notice");
  });
  it("detects drift without overwriting package files, then accepts a deliberate update", () => {
    const options = fixture(); packageDashboard(options);
    const before = bytes(options.destination);
    writeFileSync(join(options.dist, "hosting.js"), "// changed synthetic production application");
    expect(() => packageDashboard({ ...options, check: true })).toThrow("Packaged dashboard byte drift.");
    expect(bytes(options.destination)).toEqual(before);
    packageDashboard(options); packageDashboard({ ...options, check: true });
  });
  it.each(["hosting.js.map", "unexpected-lazy.js", ".env"])("refuses unexpected build file %s before package writes", name => {
    const options = fixture(); const before = bytes(options.destination);
    writeFileSync(join(options.dist, name), "synthetic extra");
    expect(() => packageDashboard(options)).toThrow("Unexpected distribution files.");
    expect(bytes(options.destination)).toEqual(before);
  });
  it("refuses unexpected destination files or subdirectories rather than deleting them", () => {
    const options = fixture(); mkdirSync(join(options.destination, "unexpected"));
    expect(() => packageDashboard(options)).toThrow("Unexpected distribution files.");
  });
  it("rejects a linked distribution directory instead of writing through it", () => {
    const options = fixture(); const before = bytes(options.destination);
    const alias = join(options.root, "linked-package");
    symlinkSync(options.destination, alias, "junction");
    expect(() => packageDashboard({ ...options, destination: alias })).toThrow("Unexpected distribution directory.");
    expect(bytes(options.destination)).toEqual(before);
  });
  it("rejects inline script/style, font or dependency license/version drift before writes", () => {
    const options = fixture(); const before = bytes(options.destination);
    const html = readFileSync(join(options.dist, "index.html"), "utf8");
    writeFileSync(join(options.dist, "index.html"), html + "<script>syntheticInline()</script>");
    expect(() => packageDashboard(options)).toThrow("Unexpected dashboard HTML.");
    writeFileSync(join(options.dist, "index.html"), html);
    writeFileSync(join(options.modules, "react/package.json"), JSON.stringify({ name: "react", version: "other", license: "MIT" }));
    expect(() => packageDashboard(options)).toThrow("Production dependency license/version drift.");
    expect(bytes(options.destination)).toEqual(before);
  });
});
