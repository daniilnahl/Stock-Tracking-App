// Deliberate build-time bridge only. Python never imports or executes this file.
import { lstatSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const builtNames = ["hosting.css", "hosting.js", "index.html", "stock-pixel.ttf"];
const packagedNames = ["LICENSE.txt", ...builtNames].sort();
function requireFiles(directory, names) {
  const information = lstatSync(directory);
  if (!information.isDirectory() || information.isSymbolicLink()) throw new Error("Unexpected distribution directory.");
  const actual = readdirSync(directory).sort();
  if (JSON.stringify(actual) !== JSON.stringify([...names].sort()) || actual.some(name => !lstatSync(resolve(directory, name)).isFile() || lstatSync(resolve(directory, name)).isSymbolicLink())) throw new Error("Unexpected distribution files.");
}
export function packageDashboard({ dist, destination, root, modules, check = false }) {
  requireFiles(dist, builtNames);
  requireFiles(destination, packagedNames);
  const files = new Map(builtNames.map(name => [name, readFileSync(resolve(dist, name))]));
  const html = files.get("index.html").toString("utf8");
  const scripts = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)];
  if (scripts.length !== 1 || scripts[0][1].trim() || !scripts[0][0].includes('src="/dashboard-assets/hosting.js"') ||
    !html.includes('href="/dashboard-assets/hosting.css"') || !html.includes('<div id="root"></div>') || /<style\b|\bstyle\s*=/.test(html)) throw new Error("Unexpected dashboard HTML.");
  if (!files.get("hosting.css").toString("utf8").includes("/dashboard-assets/stock-pixel.ttf") ||
    [...files.values()].some(bytes => bytes.includes(Buffer.from("sourceMappingURL=")))) throw new Error("Unexpected dashboard asset references.");
  const normalize = text => text.replaceAll("\r\n", "\n").trimEnd() + "\n";
  let license = "Stock Tracking App and original Stock Pixel font\n\n" + normalize(readFileSync(resolve(root, "LICENSE"), "utf8"));
  for (const [name, version] of [["react", "19.3.1"], ["react-dom", "19.3.1"], ["scheduler", "0.28.0"], ["vite", "8.3.4"]]) {
    const metadata = JSON.parse(readFileSync(resolve(modules, name, "package.json"), "utf8"));
    if (metadata.name !== name || metadata.version !== version || metadata.license !== "MIT") throw new Error("Production dependency license/version drift.");
    let notice = normalize(readFileSync(resolve(modules, name, name === "vite" ? "LICENSE.md" : "LICENSE"), "utf8"));
    if (name === "vite") {
      if (!notice.startsWith("# Vite core license\n") || !notice.includes("# Licenses of bundled dependencies")) throw new Error("Vite core notice format drift.");
      // Only the emitted modulepreload helper is distributed, not Vite's CLI.
      notice = normalize(notice.split("# Licenses of bundled dependencies")[0]);
    }
    license += `\n${name} ${version} / MIT${name === "vite" ? " (modulepreload runtime helper)" : ""}\n\n` + notice;
  }
  files.set("LICENSE.txt", Buffer.from(license));
  if (!files.get("stock-pixel.ttf").equals(readFileSync(resolve(root, "docs/previews/assets/stock-pixel.ttf")))) throw new Error("Original font drift.");
  const drift = [...files].some(([name, bytes]) => !bytes.equals(readFileSync(resolve(destination, name))));
  if (check && drift) throw new Error("Packaged dashboard byte drift.");
  if (!check) for (const [name, bytes] of files) writeFileSync(resolve(destination, name), bytes);
  return [...files.keys()].sort();
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    if (process.argv.slice(2).some(argument => argument !== "--check") || process.argv.length > 3) throw new Error("Invalid bridge options.");
    packageDashboard({ dist: fileURLToPath(new URL("../dist/", import.meta.url)), destination: fileURLToPath(new URL("../../src/stock_tracker/api/dashboard_assets/", import.meta.url)),
      root: fileURLToPath(new URL("../../", import.meta.url)), modules: fileURLToPath(new URL("../node_modules/", import.meta.url)), check: process.argv.includes("--check") });
    process.stdout.write(process.argv.includes("--check") ? "Packaged dashboard bytes match.\n" : "Packaged the reviewed dashboard asset set.\n");
  } catch { process.stderr.write("Dashboard packaging failed. Inspect the deliberate build/package step and closed asset set.\n"); process.exitCode = 1; }
}
