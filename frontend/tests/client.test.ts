import { describe, expect, it, vi } from "vitest";
import { ApiClient } from "../src/services/client";
import { ClientError } from "../src/services/validation";
import { credential, deferred, history, response, stock, watchlist } from "./fixtures";

function create(fetcher: (url: string, init: RequestInit) => Promise<Response> = vi.fn(async () => response(watchlist()))) {
  const client = new ApiClient({ fetch: fetcher, origin: "http://127.0.0.1:8000" });
  client.connect(credential);
  return { client, fetcher: vi.mocked(fetcher) };
}
const turn = async () => { await Promise.resolve(); await Promise.resolve(); };

describe("safe connection and transport", () => {
  it("does not fetch at construction or before connection, or expose the memory-only credential", async () => {
    const client = new ApiClient({ origin: "http://localhost:8000" });
    expect(() => client.loadWatchlist("menu_watchlist")).toThrow("Connect to the local API");
    client.connect(credential);
    expect(JSON.stringify(client)).toBe("{}");
    expect(JSON.stringify(client.getSnapshot())).not.toContain(credential);
    client.disconnect();
    expect(client.getSnapshot().connection).toBe("disconnected");
  });
  it.each(["\n", "\r\n", " "])("rejects trailing token whitespace before storing or fetching", ending => {
    const client = new ApiClient({ origin: "http://localhost:8000" });
    expect(() => client.connect(credential + ending)).toThrowError(ClientError);
    expect(client.getSnapshot().connection).toBe("disconnected");
    expect(() => client.loadWatchlist("menu_watchlist")).toThrowError(ClientError);
    expect(fetch).not.toHaveBeenCalled();
  });
  it.each(["https://localhost:8000", "http://localhost:5173", "http://example.invalid:8000", "null"])("rejects unsupported origin %s before fetch", origin => {
    const client = new ApiClient({ origin });
    expect(() => client.connect(credential)).toThrow("Open the dashboard from the local API listener.");
    expect(client.getSnapshot().connection).toBe("unsupported");
    expect(fetch).not.toHaveBeenCalled();
  });
  it("fails visibly before any private fetch when source-context support is absent", () => {
    const native = JSON.parse;
    vi.spyOn(JSON, "parse").mockImplementation((text, reviver) => native(text, reviver ? (key, value) => reviver(key, value) : undefined));
    const client = new ApiClient({ origin: "http://localhost:8000" });
    expect(() => client.connect(credential)).toThrow("This browser cannot decode exact API numbers.");
    expect(client.getSnapshot().connection).toBe("unsupported");
    expect(fetch).not.toHaveBeenCalled();
  });
  it("uses only exact relative read routes, memory Authorization and safe request options", async () => {
    const { client, fetcher } = create();
    await client.loadWatchlist("menu_watchlist");
    expect(fetcher).toHaveBeenCalledWith("/api/v1/watchlists/menu_watchlist", expect.objectContaining({ method: "GET", cache: "no-store", credentials: "omit", redirect: "error", referrerPolicy: "no-referrer", headers: { Authorization: `Bearer ${credential}`, Accept: "application/json" } }));
    expect(() => client.loadWatchlist("../escape" as never)).toThrowError(ClientError);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
  it("accepts both namespace responses without deduplicating entries", async () => {
    const fetcher = vi.fn(async (url: string) => response(watchlist(url.endsWith("daniils_stock_method") ? "daniils_stock_method" : "menu_watchlist")));
    const { client } = create(fetcher);
    expect((await client.loadWatchlist("menu_watchlist")).entries.map(row => row.ordinal)).toEqual([0, 1]);
    expect((await client.loadWatchlist("daniils_stock_method")).entries.map(row => row.stock.symbol)).toEqual(["DEMO", "DEMO"]);
  });
  it("rejects namespace-swapped and malformed responses before publishing", async () => {
    const { client } = create(vi.fn(async () => response(watchlist("daniils_stock_method"))));
    await expect(client.loadWatchlist("menu_watchlist")).rejects.toMatchObject({ code: "incompatible_response" });
    expect(client.getSnapshot().watchlist.status).toBe("error");
  });
  it("validates error code/status/message against the generated fixed contract", async () => {
    const fetcher = vi.fn(async () => response({ error: { code: "history_disabled", message: "Historical acquisition is disabled." } }, 503));
    const { client } = create(fetcher);
    await expect(client.loadWatchlist("menu_watchlist")).rejects.toMatchObject({ code: "api_error", apiCode: "history_disabled" });
    fetcher.mockResolvedValueOnce(response({ error: { code: "history_disabled", message: "private upstream details" } }, 503));
    await expect(client.loadWatchlist("menu_watchlist")).rejects.toMatchObject({ code: "incompatible_response" });
    fetcher.mockResolvedValueOnce(response({ error: { code: "history_disabled", message: "Historical acquisition is disabled." } }, 500));
    await expect(client.loadWatchlist("menu_watchlist")).rejects.toMatchObject({ code: "incompatible_response" });
  });
  it("maps network errors without leaking raw diagnostics; failed reload removes old data", async () => {
    const { client, fetcher } = create();
    await client.loadWatchlist("menu_watchlist");
    fetcher.mockRejectedValueOnce(new Error("private upstream details"));
    const operation = client.loadWatchlist("menu_watchlist");
    expect(client.getSnapshot().watchlist).toEqual({ status: "loading" });
    await expect(operation).rejects.toMatchObject({ code: "network_error", message: "The local API could not be reached." });
    expect(client.getSnapshot().watchlist).not.toHaveProperty("data");
  });
  it("refuses HTML, invalid UTF8, and oversized responses", async () => {
    for (const bad of [new Response("<html>private</html>"), new Response(new Uint8Array([255]), { headers: { "content-type": "application/json" } }), response(" ".repeat(4 * 1024 * 1024 + 1))]) {
      const { client } = create(vi.fn(async () => bad));
      await expect(client.loadWatchlist("menu_watchlist")).rejects.toMatchObject({ code: "incompatible_response" });
    }
  });
});
describe("request lifecycle", () => {
  it("coalesces identical inflight reads; aborting one consumer preserves another", async () => {
    const pending = deferred<Response>();
    const fetcher = vi.fn((_url: string, _init: RequestInit) => pending.promise);
    const { client } = create(fetcher);
    const cancelled = new AbortController();
    const first = client.loadWatchlist("menu_watchlist", { signal: cancelled.signal });
    const failed = expect(first).rejects.toMatchObject({ code: "cancelled" });
    const second = client.loadWatchlist("menu_watchlist");
    await turn();
    cancelled.abort();
    await failed;
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(fetcher.mock.calls[0]?.[1]?.signal?.aborted).not.toBe(true);
    pending.resolve(response(watchlist()));
    await expect(second).resolves.toHaveProperty("namespace", "menu_watchlist");
  });
  it("last consumer cancellation aborts transport and suppresses an ignored late result", async () => {
    const pending = deferred<Response>();
    const fetcher = vi.fn((_url: string, _init: RequestInit) => pending.promise);
    const { client } = create(fetcher);
    const cancellation = new AbortController();
    const result = client.loadWatchlist("menu_watchlist", { signal: cancellation.signal });
    const failure = expect(result).rejects.toMatchObject({ code: "cancelled" });
    await turn();
    cancellation.abort(); await failure;
    expect(fetcher.mock.calls[0]?.[1].signal?.aborted).toBe(true);
    expect(client.getSnapshot().watchlist.status).toBe("idle");
    pending.resolve(response(watchlist())); await turn();
    expect(client.getSnapshot().watchlist.status).toBe("idle");
  });
  it("does not start a pre-cancelled request", async () => {
    const { client, fetcher } = create();
    const cancel = new AbortController(); cancel.abort();
    await expect(client.loadWatchlist("menu_watchlist", { signal: cancel.signal })).rejects.toMatchObject({ code: "cancelled" });
    expect(fetcher).not.toHaveBeenCalled();
  });
  it("disconnect/reconnect suppresses every prior-generation result", async () => {
    const old = deferred<Response>();
    const fetcher = vi.fn((_url: string, _init: RequestInit) => old.promise);
    const { client } = create(fetcher);
    const request = client.loadWatchlist("menu_watchlist");
    const failure = expect(request).rejects.toMatchObject({ code: "cancelled" });
    await turn(); client.disconnect(); await failure;
    client.connect(credential);
    old.resolve(response(watchlist())); await turn();
    expect(client.getSnapshot().watchlist.status).toBe("idle");
    expect(client.getSnapshot().selection).toBeNull();
  });
  it("401 clears credential and all private views even for a malformed error body", async () => {
    const { client, fetcher } = create();
    await client.selectRow("menu_watchlist", 0, stock);
    fetcher.mockResolvedValueOnce(new Response("private", { status: 401 }));
    await expect(client.loadHistory(client.getSnapshot().selection!)).rejects.toMatchObject({ code: "unauthorized" });
    expect(client.getSnapshot()).toMatchObject({ connection: "disconnected", namespace: null, selection: null, watchlist: { status: "idle" }, history: { status: "idle" } });
    expect(() => client.loadWatchlist("menu_watchlist")).toThrow("Connect to the local API");
  });
  it("switching namespace cancels prior work without publishing it into the new namespace", async () => {
    const old = deferred<Response>();
    const fetcher = vi.fn((_url: string, _init: RequestInit) => old.promise);
    const { client } = create(fetcher);
    const first = client.loadWatchlist("menu_watchlist");
    const failure = expect(first).rejects.toMatchObject({ code: "cancelled" });
    await turn();
    fetcher.mockResolvedValueOnce(response(watchlist("daniils_stock_method")));
    await client.loadWatchlist("daniils_stock_method"); await failure;
    old.resolve(response(watchlist())); await turn();
    expect(client.getSnapshot().namespace).toBe("daniils_stock_method");
    expect(client.getSnapshot().watchlist).toMatchObject({ status: "success", data: { namespace: "daniils_stock_method" } });
  });
});
describe("request-local selection and history", () => {
  it("clears selection/history without disconnecting and aborts ignored late history on explicit close", async () => {
    const fetcher = vi.fn(async (_url: string, _init: RequestInit) => response(watchlist()));
    const client = new ApiClient({ fetch: fetcher, origin: "http://127.0.0.1:8000" });
    client.connect(Array.from({ length: 48 }, (_, index) => String.fromCharCode(65 + index * 7 % 26)).join(""));
    const selected = await client.selectRow("menu_watchlist", 0, stock);
    const pending = deferred<Response>();
    fetcher.mockImplementationOnce(() => pending.promise);
    const reading = client.loadHistory(selected);
    const cancelled = expect(reading).rejects.toMatchObject({ code: "cancelled" });
    await turn(); client.clearSelection(); await cancelled;
    pending.resolve(response(history())); await turn();
    expect(client.getSnapshot().connection).toBe("connected");
    expect(client.getSnapshot().watchlist.status).toBe("success");
    expect(client.getSnapshot().selection).toBeNull();
    expect(client.getSnapshot().history.status).toBe("idle");
    expect(() => client.loadHistory(selected)).toThrowError(ClientError);
  });
  it("re-reads ordered list before selection and exact history; reload invalidates selection", async () => {
    const { client, fetcher } = create();
    await client.loadWatchlist("menu_watchlist");
    const selected = await client.selectRow("menu_watchlist", 1, stock);
    expect(fetcher).toHaveBeenCalledTimes(2);
    fetcher.mockResolvedValueOnce(response(history(1)));
    const result = await client.loadHistory(selected, { start: "2020-01-02", end: "2020-01-06" });
    expect(result.bars[0]?.volume).toBe(0n);
    expect(fetcher).toHaveBeenLastCalledWith("/api/v1/watchlists/menu_watchlist/entries/1/history?start=2020-01-02&end=2020-01-06", expect.anything());
    await client.loadWatchlist("menu_watchlist");
    expect(client.getSnapshot().selection).toBeNull();
    expect(client.getSnapshot().history.status).toBe("idle");
    expect(() => client.loadHistory(selected)).toThrow("The request-local row changed");
  });
  it("does not publish selection if the consumer aborts after list settlement", async () => {
    const { client } = create();
    const cancel = new AbortController();
    const load = client.loadWatchlist.bind(client);
    vi.spyOn(client, "loadWatchlist").mockImplementation((namespace, options) => load(namespace, options).then(view => {
      queueMicrotask(() => cancel.abort());
      return view;
    }));
    await expect(client.selectRow("menu_watchlist", 0, stock, { signal: cancel.signal })).rejects.toMatchObject({ code: "cancelled" });
    expect(client.getSnapshot().selection).toBeNull();
  });
  it("does not accept a forged/copy selection or invalid paired dates", async () => {
    const { client, fetcher } = create();
    const selected = await client.selectRow("menu_watchlist", 0, stock);
    expect(() => client.loadHistory({ ...selected })).toThrowError(ClientError);
    expect(() => client.loadHistory(selected, { start: "2020-01-02" })).toThrowError(ClientError);
    expect(() => client.loadHistory(selected, { start: "2020-02-30", end: "2020-03-01" })).toThrowError(ClientError);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
  it.each(["changed", "gone"])("clears selection when row is %s after list reload", async change => {
    const document = watchlist();
    if (change === "changed") document.entries[0]!.stock.name = "Different stored row";
    else document.entries = [];
    const { client } = create(vi.fn(async () => response(document)));
    await expect(client.selectRow("menu_watchlist", 0, stock)).rejects.toMatchObject({ code: "selection_changed" });
    expect(client.getSnapshot().selection).toBeNull();
  });
  it("refuses wrong stock/ordinal and leaves no history data", async () => {
    const { client, fetcher } = create();
    const selected = await client.selectRow("menu_watchlist", 0, stock);
    fetcher.mockResolvedValueOnce(response(history(1)));
    await expect(client.loadHistory(selected)).rejects.toMatchObject({ code: "incompatible_response" });
    expect(client.getSnapshot().history).not.toHaveProperty("data");
  });
  it("list reload aborts pending history and suppresses its late result", async () => {
    const { client, fetcher } = create();
    const selected = await client.selectRow("menu_watchlist", 0, stock);
    const old = deferred<Response>(); fetcher.mockImplementationOnce(() => old.promise);
    const request = client.loadHistory(selected);
    const failure = expect(request).rejects.toMatchObject({ code: "cancelled" });
    await turn(); await client.loadWatchlist("menu_watchlist"); await failure;
    old.resolve(response(history())); await turn();
    expect(client.getSnapshot().selection).toBeNull();
    expect(client.getSnapshot().history.status).toBe("idle");
  });
  it("publishes loading for a same-range replacement after the last consumer aborts", async () => {
    const { client, fetcher } = create();
    const selected = await client.selectRow("menu_watchlist", 0, stock);
    const old = deferred<Response>();
    fetcher.mockImplementationOnce(() => old.promise);
    const cancel = new AbortController();
    const first = client.loadHistory(selected, { signal: cancel.signal });
    const failure = expect(first).rejects.toMatchObject({ code: "cancelled" });
    await turn(); cancel.abort(); await failure;
    expect(client.getSnapshot().history.status).toBe("idle");
    const replacement = deferred<Response>();
    fetcher.mockImplementationOnce(() => replacement.promise);
    const second = client.loadHistory(selected);
    expect(client.getSnapshot().history.status).toBe("loading");
    await turn(); replacement.resolve(response(history())); await second;
    old.resolve(response(history(1))); await turn();
    expect(client.getSnapshot().history).toMatchObject({ status: "success", data: { ordinal: 0 } });
  });
  it("a new history range cancels a prior range instead of publishing stale data", async () => {
    const { client, fetcher } = create();
    const selected = await client.selectRow("menu_watchlist", 0, stock);
    const old = deferred<Response>(); fetcher.mockImplementationOnce(() => old.promise);
    const first = client.loadHistory(selected);
    const failure = expect(first).rejects.toMatchObject({ code: "cancelled" });
    await turn(); fetcher.mockResolvedValueOnce(response(history()));
    await client.loadHistory(selected, { start: "2020-01-02", end: "2020-01-06" }); await failure;
    old.resolve(response(history(1))); await turn();
    expect(client.getSnapshot().history).toMatchObject({ status: "success", data: { ordinal: 0 } });
  });
});
