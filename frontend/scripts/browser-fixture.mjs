// Separate browser-test profile only. Serves existing production-built demo
// assets on loopback, with no API, credentials, proxy, or market-data access.
// Actual launcher/wheel integration is a separate profile; no API mocks live here.
import { createServer } from "node:http";
import { readFileSync } from "node:fs";

const dist = new URL("../dist/", import.meta.url);
const files = new Map([["/", [readFileSync(new URL("index.html", dist)), "text/html; charset=utf-8"]]]);
for (const [name, mime] of [["hosting.js", "text/javascript"], ["hosting.css", "text/css"], ["stock-pixel.ttf", "font/ttf"]]) {
  files.set(`/dashboard-assets/${name}`, [readFileSync(new URL(name, dist)), mime]);
}
const server = createServer((request, response) => {
  const file = request.method === "GET" && request.headers.host === "127.0.0.1:8000" ? files.get(request.url) : undefined;
  response.setHeader("Cache-Control", "no-store");
  response.setHeader("Referrer-Policy", "no-referrer");
  response.setHeader("X-Content-Type-Options", "nosniff");
  response.setHeader("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; connect-src 'self'; img-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'");
  response.writeHead(file ? 200 : 404, { "Content-Type": file?.[1] ?? "text/plain" });
  response.end(file?.[0] ?? "Fixture asset unavailable.");
});
server.listen(8000, "127.0.0.1");
for (const signal of ["SIGINT", "SIGTERM"]) process.on(signal, () => server.close());
