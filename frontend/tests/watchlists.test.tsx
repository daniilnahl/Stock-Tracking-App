// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../src/App";
import { ApiClient } from "../src/services/client";
import { deferred, response, watchlist } from "./fixtures";
import type { Namespace } from "../src/services/validation";

function credential() { return Array.from({ length: 48 }, (_, index) => String.fromCharCode(65 + index * 7 % 26)).join(""); }
function saved(namespace: Namespace = "menu_watchlist") {
  const view = watchlist(namespace);
  return { ...view, name: "SYNTHETIC DEMO / no real holdings", entries: [
    { ...view.entries[0]!, average_cost: "1.00000000000000000001", current_price: "2E-18",
      snapshot: { cost_basis: "0.1234567890123456789024691357801234567890123456789", market_value: "0.00000000000000000024691357802469135780246913578", unrealized_pnl: "-0.12345678901234567865555555775543209898654321", unrealized_return: "-0.999999999999999998" } },
    { ...view.entries[1]! },
    { ...view.entries[1]!, ordinal: 2, average_cost: "0", snapshot: { cost_basis: "0", market_value: "0", unrealized_pnl: "0", unrealized_return: null } },
  ] };
}
type Fetcher = (url: string, init: RequestInit) => Promise<Response>;
function mount(fetcher: Fetcher = vi.fn(async () => response(saved())), configured = true) {
  const client = new ApiClient({ origin: "http://127.0.0.1:8000", fetch: fetcher });
  if (configured) client.connect(credential());
  const view = render(<App createClient={() => client} />);
  return { client, view };
}
function read() { fireEvent.click(screen.getByRole("button", { name: "Read saved entries" })); }
function namespace(value: Namespace) { fireEvent.change(screen.getByLabelText("Saved namespace"), { target: { value } }); }
function navigate(hash: string) { act(() => { window.history.replaceState(null, "", `/${hash}`); window.dispatchEvent(new HashChangeEvent("hashchange")); }); }
beforeEach(() => { localStorage.clear(); sessionStorage.clear(); window.history.replaceState(null, "", "/#watchlists"); });
afterEach(cleanup);

describe("explicit saved watchlist reads", () => {
  it("does not fetch on mount, configuration or namespace selection and uses exactly two namespace values", () => {
    const fetcher = vi.fn(async () => response(saved()));
    const { client } = mount(fetcher, false);
    expect(screen.getByText("Saved reads disconnected")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Read saved entries" }).hasAttribute("disabled")).toBe(true);
    expect(screen.getAllByRole("option").map(option => option.getAttribute("value"))).toEqual(["menu_watchlist", "daniils_stock_method"]);
    act(() => client.connect(credential()));
    namespace("daniils_stock_method");
    expect(fetcher.mock.calls.length === 0).toBe(true);
    expect(screen.queryByRole("table")).toBeNull();
  });
  it("preserves ordered duplicates, exact decimals/exponents, owned zeros and null/unowned distinctions", async () => {
    mount(); read();
    const table = await screen.findByRole("table");
    const rows = within(table).getAllByRole("row").slice(1);
    expect(rows).toHaveLength(3);
    expect(rows.map(row => within(row).getAllByRole("cell").map(cell => cell.textContent))).toEqual([
      ["0", "DEMOSyntheticNASDAQ", "0.12345678901234567890123456789", "Owned", "1.00000000000000000001", "2E-18", "Open detail for row 0"],
      ["1", "DEMOSyntheticNASDAQ", "0", "Unowned", "Not applicable (unowned)", "0", "Open detail for row 1"],
      ["2", "DEMOSyntheticNASDAQ", "0", "Owned", "0", "0", "Open detail for row 2"],
    ]);
    expect(screen.getByText(/Currency: unknown for both costs and prices/)).toBeTruthy();
    expect(document.body.textContent?.includes("opaque label")).toBe(false);
    expect(screen.getByRole("button", { name: "Reload saved entries" })).toBeTruthy();
  });
  it("displays unavailable/null distinctly from zero, escapes all source text, and invents no currency", async () => {
    const view = saved();
    view.entries[0]!.current_price = null;
    mount(async () => response({ ...view, entries: view.entries.map((row, index) => index === 0 ? { ...row, stock: { symbol: "<script>blocked</script>", name: null, exchange: null } } : row) })); read();
    await screen.findByRole("table");
    expect(screen.getByText("<script>blocked</script>")).toBeTruthy();
    expect(document.querySelector("main script")).toBeNull();
    expect(screen.getByText("Unavailable")).toBeTruthy();
    expect(screen.getByText("Name unavailable")).toBeTruthy();
    expect(screen.getByText("Exchange unavailable")).toBeTruthy();
    expect(document.body.textContent?.includes("$" )).toBe(false);
  });
  it("handles an empty saved list as success rather than missing state", async () => {
    mount(async () => response({ ...saved(), entries: [] })); read();
    expect(await screen.findByText("This saved watchlist has no entries.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Reload saved entries" })).toBeTruthy();
  });
  it("clears old rows on reload, reports offline failure without stale fallback, and retries explicitly", async () => {
    const pending = deferred<Response>();
    let count = 0;
    mount(async () => ++count === 1 ? response(saved()) : count === 2 ? pending.promise : response(saved()));
    read(); await screen.findByRole("table");
    fireEvent.click(screen.getByRole("button", { name: "Reload saved entries" }));
    expect(screen.getByText("Reading saved entries")).toBeTruthy();
    expect(screen.queryByRole("table")).toBeNull();
    await act(async () => pending.reject(new Error("unsafe transport diagnostic")));
    expect(screen.getByRole("alert").textContent === "The local API could not be reached.Try again").toBe(true);
    expect(document.body.textContent?.includes("unsafe transport diagnostic")).toBe(false);
    const retry = screen.getByRole("button", { name: "Try again" });
    retry.focus(); fireEvent.click(retry);
    expect(document.activeElement).toBe(screen.getByLabelText("Saved namespace"));
    await screen.findByRole("table");
    expect(count).toBe(3);
  });
  it("cancels a read and replaces an abort-ignoring transport without late publication", async () => {
    const old = deferred<Response>();
    const next = deferred<Response>();
    let calls = 0;
    mount(async () => ++calls === 1 ? old.promise : next.promise);
    read(); await waitFor(() => expect(calls).toBe(1));
    fireEvent.click(screen.getByRole("button", { name: "Cancel read" }));
    expect(screen.getByText("Saved read cancelled")).toBeTruthy();
    read(); await waitFor(() => expect(calls).toBe(2));
    expect(screen.getByText("Reading saved entries")).toBeTruthy();
    await act(async () => old.resolve(response(saved())));
    expect(screen.queryByRole("table")).toBeNull();
    await act(async () => next.resolve(response({ ...saved(), name: "Replacement only" })));
    expect(screen.getByText("Replacement only")).toBeTruthy();
  });
  it("keeps namespace identity separate, cancels old work on switching, and preserves duplicate order", async () => {
    const old = deferred<Response>();
    const paths: string[] = [];
    mount(async url => { paths.push(url); return paths.length === 1 ? old.promise : response(saved("daniils_stock_method")); });
    read(); await waitFor(() => expect(paths.length).toBe(1));
    namespace("daniils_stock_method");
    expect(screen.getByText("Saved entries not loaded")).toBeTruthy();
    expect(paths.length).toBe(1);
    read(); await screen.findByRole("table");
    await act(async () => old.resolve(response({ ...saved(), name: "Late old list" })));
    expect(screen.queryByText("Late old list")).toBeNull();
    expect(paths).toEqual(["/api/v1/watchlists/menu_watchlist", "/api/v1/watchlists/daniils_stock_method"]);
    expect(screen.getByRole("region", { name: "Daniil's stock method / saved entries" })).toBeTruthy();
  });
  it.each(["route", "disconnect", "replace"])("aborts pending reads and rejects late data after %s", async action => {
    const pending = deferred<Response>();
    let signal: AbortSignal | null = null;
    const { client } = mount(async (_url, init) => { signal = init.signal as AbortSignal; return pending.promise; });
    read(); await waitFor(() => expect(signal !== null).toBe(true));
    screen.getByLabelText("Saved namespace").focus();
    act(() => { if (action === "route") navigate("#settings"); else if (action === "disconnect") client.disconnect(); else client.connect(credential()); });
    const focusAfterAction = document.activeElement;
    expect(signal!.aborted).toBe(true);
    await act(async () => pending.resolve(response(saved())));
    expect(screen.queryByRole("table")).toBeNull();
    expect(client.getSnapshot().watchlist.status).toBe("idle");
    expect(screen.queryByText("Saved read cancelled")).toBeNull();
    expect(document.activeElement).toBe(focusAfterAction);
  });
  it("clears private state and requests reconfiguration on 401 without displaying the body", async () => {
    const { client } = mount(async () => new Response("unsafe body", { status: 401 }));
    read();
    await screen.findByText("Saved reads disconnected");
    await waitFor(() => expect(screen.getByRole("alert").textContent === "Authentication is required. Private views were cleared.").toBe(true));
    expect(client.getSnapshot().connection).toBe("disconnected");
    expect(screen.queryByRole("table")).toBeNull();
    expect(document.body.textContent?.includes("unsafe body")).toBe(false);
  });
  it.each(["schema", "namespace", "legacy"])("reports safe %s failures with recovery and no partial table", async kind => {
    const value = kind === "legacy" ? response({ error: { code: "legacy_state_present", message: "Legacy state requires an explicit safe transition." } }, 409) :
      response(kind === "schema" ? { ...saved(), entries: [{ ...saved().entries[0], quantity: 12 }] } : saved("daniils_stock_method"));
    mount(async () => value); read();
    await screen.findByRole("alert");
    expect(screen.queryByRole("table")).toBeNull();
    expect(screen.getByRole("button", { name: "Try again" })).toBeTruthy();
    if (kind === "legacy") expect(screen.getByText(/Legacy saved state needs a separate/)).toBeTruthy();
  });
  it("reports unsupported parsing before any private request", () => {
    const native = JSON.parse;
    vi.spyOn(JSON, "parse").mockImplementation((text, reviver) => native(text, reviver ? (key, value) => reviver(key, value) : undefined));
    const fetcher = vi.fn(async () => response(saved()));
    const { client } = mount(fetcher, false);
    act(() => { try { client.connect(credential()); } catch { /* Expected fixed prerequisite failure. */ } });
    expect(screen.getByText("Saved reads unsupported")).toBeTruthy();
    expect(fetcher.mock.calls.length === 0).toBe(true);
  });
});
