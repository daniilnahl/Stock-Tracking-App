// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { App } from "../src/App";
import { ApiClient } from "../src/services/client";
import { deferred, history, response, watchlist } from "./fixtures";

function saved(cost = "5") {
  const value = watchlist();
  return { ...value, entries: [
    { ...value.entries[0]!, quantity: "2", average_cost: cost, current_price: "0", metadata: { ...value.entries[0]!.metadata, sector: "<img src=x>", country: "", currency: "USD" },
      snapshot: { cost_basis: cost === "5" ? "10" : "14", market_value: "0", unrealized_pnl: cost === "5" ? "-10" : "-14", unrealized_return: "-1" } },
    { ...value.entries[1]!, quantity: "0" },
  ] };
}
type Fetcher = (url: string, init: RequestInit) => Promise<Response>;
function mount(fetcher: Fetcher = async url => response(url.includes("/history") ? history() : saved())) {
  const client = new ApiClient({ origin: "http://127.0.0.1:8000", fetch: fetcher });
  client.connect(Array.from({ length: 48 }, (_, index) => String.fromCharCode(65 + index * 7 % 26)).join(""));
  render(<App createClient={() => client} />);
  return client;
}
async function list() { fireEvent.click(screen.getByRole("button", { name: "Read saved entries" })); await screen.findByRole("table"); }
async function detail(ordinal = 0) { fireEvent.click(screen.getByRole("button", { name: `Open detail for row ${ordinal}` })); await screen.findByRole("heading", { name: "Stored-row detail / DEMO" }); }
function read() { fireEvent.click(screen.getByRole("button", { name: "Read raw history" })); }
function dates(start: string, end: string) { fireEvent.change(screen.getByLabelText("Start date"), { target: { value: start } }); fireEvent.change(screen.getByLabelText("End date"), { target: { value: end } }); }
function navigate(hash: string) { act(() => { window.history.replaceState(null, "", `/${hash}`); window.dispatchEvent(new HashChangeEvent("hashchange")); }); }
beforeEach(() => { localStorage.clear(); window.history.replaceState(null, "", "/#watchlists"); });
afterEach(cleanup);

describe("fresh request-local stored-row detail", () => {
  it("re-reads before opening and shows returned inputs/snapshot with exact units and no automatic history", async () => {
    const paths: string[] = [];
    mount(async url => { paths.push(url); return response(saved(paths.length === 1 ? "5" : "7")); });
    await list(); await detail();
    expect(paths).toEqual(["/api/v1/watchlists/menu_watchlist", "/api/v1/watchlists/menu_watchlist"]);
    expect(document.activeElement).toBe(screen.getByRole("heading", { name: "Stored-row detail / DEMO" }));
    expect(screen.getByText("14")).toBeTruthy();
    expect(screen.getByText("-14")).toBeTruthy();
    expect(screen.getByText("-1")).toBeTruthy();
    expect(screen.getByText("Unrealized return / decimal ratio")).toBeTruthy();
    expect(screen.getByText("History not loaded")).toBeTruthy();
    expect(screen.getByText("<img src=x>")).toBeTruthy();
    expect(document.querySelector("main img")).toBeNull();
    expect(screen.getByText("Empty saved text")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Close detail" }));
    expect(screen.queryByRole("heading", { name: "Stored-row detail / DEMO" })).toBeNull();
    expect(document.activeElement).toBe(screen.getByLabelText("Saved namespace"));
  });
  it("does not invent a snapshot for an unowned zero row", async () => {
    mount(); await list(); await detail(1);
    expect(screen.getByText("Unowned / no position snapshot")).toBeTruthy();
    expect(screen.queryByText("Unrealized return / decimal ratio")).toBeNull();
  });
  it("keeps an owned zero position and undefined return distinct from an unowned row", async () => {
    const view = saved();
    mount(async () => response({ ...view, entries: [{ ...view.entries[0], quantity: "0", average_cost: "0", snapshot: { cost_basis: "0", market_value: "0", unrealized_pnl: "0", unrealized_return: null } }] }));
    await list(); await detail();
    const label = screen.getByText("Unrealized return / decimal ratio");
    expect(label.nextElementSibling?.textContent).toBe("Unavailable");
    expect(screen.queryByText("Unowned / no position snapshot")).toBeNull();
  });
  it.each(["gone", "changed"])("requires a new selection if ordinal is %s on fresh read", async change => {
    let count = 0;
    mount(async () => {
      const data = saved();
      return response(++count === 1 ? data : change === "gone" ? { ...data, entries: [] } : { ...data, entries: data.entries.map(row => ({ ...row, stock: { ...row.stock, name: "Changed identity" } })) });
    });
    await list(); fireEvent.click(screen.getByRole("button", { name: "Open detail for row 0" }));
    await screen.findByRole("alert");
    expect(screen.queryByRole("heading", { name: "Stored-row detail / DEMO" })).toBeNull();
    expect(document.activeElement).toBe(screen.getByLabelText("Saved namespace"));
  });
  it("cancels pending fresh selection and ignores an abort-ignoring late result", async () => {
    const pending = deferred<Response>();
    let count = 0;
    const client = mount(async () => ++count === 1 ? response(saved()) : pending.promise);
    await list(); fireEvent.click(screen.getByRole("button", { name: "Open detail for row 0" }));
    await waitFor(() => expect(count).toBe(2));
    fireEvent.click(screen.getByRole("button", { name: "Cancel opening detail" }));
    await act(async () => pending.resolve(response(saved())));
    expect(client.getSnapshot().selection).toBeNull();
    expect(screen.queryByRole("heading", { name: "Stored-row detail / DEMO" })).toBeNull();
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Read saved entries" }));
  });
});

describe("explicit sparse raw history", () => {
  it("preserves exact OHLC/int64/null values and plots only returned observations with declared limits", async () => {
    const paths: string[] = [];
    mount(async url => { paths.push(url); return url.includes("/history") ? response(JSON.stringify(history()).replace('"volume":0', '"volume":9223372036854775807')) : response(saved()); });
    await list(); await detail(); dates("2020-01-02", "2020-01-06"); read();
    const table = await screen.findByRole("table", { name: "Exact raw history / saved row" });
    expect(within(table).getByText("9223372036854775807")).toBeTruthy();
    expect(within(table).getAllByText("110.0000000000000000001")).toHaveLength(2);
    expect(within(table).getAllByText("Unavailable")).toHaveLength(2);
    expect(within(table).getAllByRole("row")).toHaveLength(3);
    expect(document.querySelectorAll("svg circle")).toHaveLength(2);
    expect(document.querySelector("svg polyline")).toBeNull();
    expect(paths[2]).toBe("/api/v1/watchlists/menu_watchlist/entries/0/history?start=2020-01-02&end=2020-01-06");
    expect(screen.getByText(/History source: unknown/)).toBeTruthy();
  });
  it.each([["2020-01-02", ""], ["2020-02-30", "2020-03-01"], ["2020-01-06", "2020-01-02"]])("rejects invalid paired range %s/%s before fetch", async (start, end) => {
    let count = 0;
    mount(async () => { count++; return response(saved()); });
    await list(); await detail(); dates(start, end); read();
    await screen.findByRole("alert");
    expect(count).toBe(2);
    expect(document.activeElement).toBe(screen.getByLabelText("Start date"));
    expect(screen.queryByRole("table", { name: "Exact raw history / saved row" })).toBeNull();
  });
  it("discloses rights-disabled history without enabling it or displaying sample points", async () => {
    mount(async url => url.includes("/history") ? response({ error: { code: "history_disabled", message: "Historical acquisition is disabled." } }, 503) : response(saved()));
    await list(); await detail(); read();
    expect(await screen.findByText("Historical acquisition disabled")).toBeTruthy();
    expect(document.querySelector("svg")).toBeNull();
    expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
  });
  it("keeps exact values and null/zero volumes even when chart projection overflows", async () => {
    const view = history();
    mount(async url => !url.includes("/history") ? response(saved()) : response({ ...view, bars: view.bars.map((bar, index) => ({ ...bar, open: "1E+9999", high: "1E+9999", low: "1E+9999", close: "1E+9999", volume: index === 0 ? null : 0 })) }));
    await list(); await detail(); read();
    const table = await screen.findByRole("table", { name: "Exact raw history / saved row" });
    expect(within(table).getAllByText("1E+9999")).toHaveLength(8);
    expect(within(table).getAllByText("Unavailable")).toHaveLength(3);
    expect(within(table).getByText("0")).toBeTruthy();
    expect(screen.getByText(/Chart unavailable: values cannot/)).toBeTruthy();
    expect(document.querySelector("svg")).toBeNull();
  });
  it("cancels and re-reads another range, preserving focus and ignoring an old response", async () => {
    const pending = deferred<Response>();
    let reads = 0;
    mount(async url => !url.includes("/history") ? response(saved()) : ++reads === 1 ? pending.promise : response({ ...history(), end: "2020-01-07" }));
    await list(); await detail(); read(); await waitFor(() => expect(reads).toBe(1));
    fireEvent.click(screen.getByRole("button", { name: "Cancel history read" }));
    expect(screen.getByText("History read cancelled")).toBeTruthy();
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Read raw history" }));
    dates("2020-01-02", "2020-01-07"); read();
    await screen.findByRole("table", { name: "Exact raw history / saved row" });
    await act(async () => pending.resolve(response(history())));
    expect(screen.getByText(/Returned inclusive range: 2020-01-02 to 2020-01-07/)).toBeTruthy();
  });
  it("clears prior history on failed reload or invalid submission, then retries with keyboard focus retained", async () => {
    let reads = 0;
    mount(async url => { if (!url.includes("/history")) return response(saved()); if (++reads === 2) throw new Error("Not rendered"); return response(history()); });
    await list(); await detail(); read(); await screen.findByRole("table", { name: "Exact raw history / saved row" });
    fireEvent.click(screen.getByRole("button", { name: "Reload raw history" }));
    await screen.findByRole("alert");
    expect(screen.queryByRole("table", { name: "Exact raw history / saved row" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await screen.findByRole("table", { name: "Exact raw history / saved row" });
    expect(document.activeElement).toBe(screen.getByLabelText("Start date"));
    dates("2020-01-02", ""); fireEvent.click(screen.getByRole("button", { name: "Reload raw history" }));
    await screen.findByRole("alert");
    expect(screen.queryByRole("table", { name: "Exact raw history / saved row" })).toBeNull();
    expect(reads).toBe(3);
  });
  it("a history 401 clears detail, history and the shared private session", async () => {
    const client = mount(async url => url.includes("/history") ? new Response("Unsafe failure body", { status: 401 }) : response(saved()));
    await list(); await detail(); read();
    await screen.findByText("Saved reads disconnected");
    expect(client.getSnapshot().connection).toBe("disconnected");
    expect(client.getSnapshot().selection).toBeNull();
    expect(client.getSnapshot().history.status).toBe("idle");
    expect(screen.queryByRole("heading", { name: "Stored-row detail / DEMO" })).toBeNull();
    expect(document.body.textContent?.includes("Unsafe failure body")).toBe(false);
  });
  it.each(["ordinal", "stock", "empty", "network"])("rejects %s history without publishing a table/chart", async kind => {
    mount(async url => {
      if (!url.includes("/history")) return response(saved());
      if (kind === "network") throw new Error("Untrusted transport text");
      const view = history();
      return response(kind === "ordinal" ? { ...view, ordinal: 1 } : kind === "stock" ? { ...view, stock: { ...view.stock, exchange: "OTHER" } } : { ...view, bars: [] });
    });
    await list(); await detail(); read(); await screen.findByRole("alert");
    expect(screen.queryByRole("table", { name: "Exact raw history / saved row" })).toBeNull();
    expect(document.querySelector("svg")).toBeNull();
    expect(document.body.textContent?.includes("Untrusted transport text")).toBe(false);
  });
  it.each(["close", "namespace", "reload", "disconnect", "route"])("clears history/selection and suppresses late work on %s", async action => {
    const pending = deferred<Response>();
    let signal: AbortSignal | null = null;
    const client = mount(async (url, init) => { if (url.includes("/history")) { signal = init.signal as AbortSignal; return pending.promise; } return response(saved()); });
    await list(); await detail(); read(); await waitFor(() => expect(signal !== null).toBe(true));
    act(() => {
      if (action === "close") fireEvent.click(screen.getByRole("button", { name: "Close detail" }));
      else if (action === "namespace") fireEvent.change(screen.getByLabelText("Saved namespace"), { target: { value: "daniils_stock_method" } });
      else if (action === "reload") fireEvent.click(screen.getByRole("button", { name: "Reload saved entries" }));
      else if (action === "disconnect") client.disconnect();
      else navigate("#settings");
    });
    expect(signal!.aborted).toBe(true);
    await act(async () => pending.resolve(response(history())));
    expect(client.getSnapshot().selection).toBeNull();
    expect(client.getSnapshot().history.status).toBe("idle");
    expect(screen.queryByRole("table", { name: "Exact raw history / saved row" })).toBeNull();
  });
});
