// @vitest-environment jsdom
import { act, cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../src/App";
import { SessionContext } from "../src/app/session";
import { OverviewSummary } from "../src/features/OverviewSummary";
import { ApiClient } from "../src/services/client";
import type { Namespace } from "../src/services/validation";
import { deferred, response, watchlist } from "./fixtures";

function credential() { return Array.from({ length: 48 }, (_, index) => String.fromCharCode(65 + index * 7 % 26)).join(""); }
function saved(namespace: Namespace = "menu_watchlist", length = 3) {
  const value = watchlist(namespace);
  return { ...value, name: "SYNTHETIC overview / no real holdings", entries: Array.from({ length }, (_, ordinal) => ({ ...value.entries[0]!, quantity: "0", ordinal })) };
}
function mount(fetcher = vi.fn(async (_url: string, _init: RequestInit) => response(saved()))) {
  const client = new ApiClient({ origin: "http://127.0.0.1:8000", fetch: fetcher });
  const view = render(<App createClient={() => client} />);
  return { client, fetcher, view };
}
function count() { return within(screen.getByRole("region", { name: "Saved entries" })).getByRole("status"); }
beforeEach(() => { localStorage.clear(); sessionStorage.clear(); window.history.replaceState(null, "", "/"); });
afterEach(cleanup);

describe("supported overview evidence", () => {
  it("starts unavailable, preserves the two placeholders, and does not fetch or create another client", () => {
    const { client, fetcher } = mount();
    expect(count().textContent).toBe("Unavailable");
    expect(screen.getAllByText("Placeholder / unavailable")).toHaveLength(2);
    expect(screen.queryByText("0")).toBeNull();
    expect(screen.getByText("No successful saved list is available for a count. Unavailable does not mean an empty list.")).toBeTruthy();
    act(() => client.connect(credential()));
    expect(count().textContent).toBe("Unavailable");
    expect(fetcher.mock.calls.length === 0).toBe(true);
    expect(Object.keys(localStorage)).toEqual([]);
    expect(Object.keys(sessionStorage)).toEqual([]);
  });
  it.each(["menu_watchlist", "daniils_stock_method"] as const)("counts duplicate-inclusive rows only in the loaded %s namespace", async namespace => {
    const fetcher = vi.fn(async (_url: string, _init: RequestInit) => response(saved(namespace)));
    const { client } = mount(fetcher);
    act(() => client.connect(credential()));
    await act(async () => { await client.loadWatchlist(namespace); }); // Explicit controlled test read; never initiated by Overview.
    expect(count().textContent).toBe("3");
    expect(within(screen.getByRole("region", { name: "Saved watchlist access" })).getByText(namespace, { exact: true })).toBeTruthy();
    expect(screen.getByText("Saved list name: SYNTHETIC overview / no real holdings")).toBeTruthy();
    expect(screen.getByText("This count covers only the loaded namespace. Overview makes no additional requests.")).toBeTruthy();
    expect(fetcher.mock.calls.length === 1).toBe(true);
    expect(fetcher.mock.calls[0]?.[0] === `/api/v1/watchlists/${namespace}`).toBe(true);
    expect(screen.getByText("Source, observation time and retrieval time: unknown. Currency and freshness: unknown.")).toBeTruthy();
    expect(document.body.textContent?.includes("0.12345678901234567890123456789")).toBe(false);
    expect(document.body.textContent?.includes("opaque label")).toBe(false);
    expect(screen.getByRole("link", { name: "Open Watchlists" }).getAttribute("href")).toBe("#watchlists");
  });
  it("shows zero only for a successful empty namespace, and escapes its saved name", async () => {
    const { client } = mount(vi.fn(async () => response({ ...saved("menu_watchlist", 0), name: "<img src=x onerror=blocked>" })));
    act(() => client.connect(credential()));
    await act(async () => { await client.loadWatchlist("menu_watchlist"); });
    expect(count().textContent).toBe("0");
    expect(screen.getByText("Saved list name: <img src=x onerror=blocked>")).toBeTruthy();
    expect(document.querySelector("main img")).toBeNull();
  });
  it("hides the count during reload, failure and cancellation without stale fallback", async () => {
    const delayed = deferred<Response>();
    const fetcher = vi.fn(async (_url: string, _init: RequestInit) => response(saved()));
    const { client } = mount(fetcher);
    act(() => client.connect(credential()));
    await act(async () => { await client.loadWatchlist("menu_watchlist"); });
    expect(count().textContent).toBe("3");
    fetcher.mockImplementationOnce(() => delayed.promise);
    let pending!: Promise<unknown>;
    await act(async () => { pending = client.loadWatchlist("menu_watchlist").catch(error => error.code); await Promise.resolve(); });
    expect(count().textContent).toBe("Unavailable");
    expect(screen.getByText("A saved read is in progress. No count is available.")).toBeTruthy();
    await act(async () => { delayed.reject(new Error("untrusted transport diagnostic")); expect(await pending).toBe("network_error"); });
    expect(count().textContent).toBe("Unavailable");
    expect(screen.getByText("The saved read failed. No count is available.")).toBeTruthy();
    expect(document.body.textContent?.includes("untrusted transport diagnostic")).toBe(false);
    const ignored = deferred<Response>();
    fetcher.mockImplementationOnce(() => ignored.promise);
    const controller = new AbortController();
    await act(async () => { pending = client.loadWatchlist("menu_watchlist", { signal: controller.signal }).catch(error => error.code); await Promise.resolve(); });
    await act(async () => { controller.abort(); expect(await pending).toBe("cancelled"); });
    expect(count().textContent).toBe("Unavailable");
    await act(async () => { ignored.resolve(response(saved())); await Promise.resolve(); });
    expect(count().textContent).toBe("Unavailable");
  });
  it("replaces the scope rather than adding namespaces, and removes evidence on disconnect/replacement/401", async () => {
    const fetcher = vi.fn(async (url: string, _init: RequestInit) => response(saved(url.endsWith("daniils_stock_method") ? "daniils_stock_method" : "menu_watchlist", url.endsWith("daniils_stock_method") ? 1 : 3)));
    const { client } = mount(fetcher);
    act(() => client.connect(credential()));
    await act(async () => { await client.loadWatchlist("menu_watchlist"); });
    await act(async () => { await client.loadWatchlist("daniils_stock_method"); });
    expect(count().textContent).toBe("1");
    expect(screen.queryByText("menu_watchlist", { exact: true })).toBeNull();
    act(() => client.disconnect());
    expect(count().textContent).toBe("Unavailable");
    act(() => client.connect(credential()));
    await act(async () => { await client.loadWatchlist("menu_watchlist"); });
    act(() => client.connect(credential()));
    expect(count().textContent).toBe("Unavailable");
    await act(async () => { await client.loadWatchlist("menu_watchlist"); });
    fetcher.mockResolvedValueOnce(new Response(null, { status: 401 }));
    await act(async () => { expect(await client.loadWatchlist("menu_watchlist").catch(error => error.code)).toBe("unauthorized"); });
    expect(count().textContent).toBe("Unavailable");
    expect(screen.getByText("Disconnected")).toBeTruthy();
  });
  it("refuses an inconsistent snapshot's namespace and unsupported connection as count evidence", () => {
    const client = new ApiClient();
    const data = { ...saved(), observation: "saved" as const, provenance: { source: null, observed_at: null, retrieved_at: null, freshness: "unknown" as const } };
    const inconsistent = { ...client.getSnapshot(), connection: "connected" as const, namespace: "daniils_stock_method" as const, watchlist: { status: "success" as const, data } };
    const view = render(<SessionContext.Provider value={{ client, snapshot: inconsistent }}><OverviewSummary /></SessionContext.Provider>);
    expect(count().textContent).toBe("Unavailable");
    view.rerender(<SessionContext.Provider value={{ client, snapshot: { ...inconsistent, connection: "unsupported" } }}><OverviewSummary /></SessionContext.Provider>);
    expect(count().textContent).toBe("Unavailable");
    expect(screen.queryByText(data.name)).toBeNull();
  });
});
