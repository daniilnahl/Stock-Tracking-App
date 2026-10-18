import { errorContracts } from "./contracts.generated";
import type { HistoryResponse, StockResponse, WatchlistResponse, UpcomingEpsResponse } from "./contracts.generated";
import { ClientError, decode, sameStock, supportsExactJSON, validDate, validNamespace, validateHistory, validateWatchlist, validUpcomingEpsRequest, validateUpcomingEps } from "./validation";
import type { Namespace, UpcomingEpsRequest } from "./validation";

export type Resource<T> =
  | { readonly status: "idle" | "loading" }
  | { readonly status: "success"; readonly data: T }
  | { readonly status: "error"; readonly error: ClientError };
export type Selection = Readonly<{ namespace: Namespace; ordinal: number; stock: StockResponse; revision: number }>;
export type ClientSnapshot = Readonly<{
  connection: "disconnected" | "connected" | "unsupported";
  namespace: Namespace | null;
  watchlist: Resource<WatchlistResponse>;
  selection: Selection | null;
  history: Resource<HistoryResponse>;
  upcomingEps: Resource<UpcomingEpsResponse>;
}>;
type Fetch = (input: string, init: RequestInit) => Promise<Response>;
type Pending = { controller: AbortController; promise: Promise<unknown>; consumers: Set<symbol> };
const idle = Object.freeze({ status: "idle" } as const);
const initial = (): ClientSnapshot => Object.freeze({ connection: "disconnected", namespace: null, watchlist: idle, selection: null, history: idle, upcomingEps: idle });
const maxResponseBytes = 4 * 1024 * 1024;

export class ApiClient {
  #token: string | null = null;
  #generation = 0;
  #revision = 0;
  #epsRevision = 0;
  #snapshot: ClientSnapshot = initial();
  #listeners = new Set<() => void>();
  #requests = new Map<string, Pending>();
  #fetch: Fetch;
  #origin: string;
  constructor(options: { fetch?: Fetch; origin?: string } = {}) {
    this.#fetch = options.fetch ?? ((input, init) => fetch(input, init));
    this.#origin = options.origin ?? globalThis.location?.origin ?? "";
  }
  getSnapshot = (): ClientSnapshot => this.#snapshot;
  subscribe = (listener: () => void): (() => void) => {
    this.#listeners.add(listener);
    return () => { this.#listeners.delete(listener); };
  };
  #publish(next: ClientSnapshot): void {
    this.#snapshot = Object.freeze({ ...next, watchlist: Object.freeze(next.watchlist), history: Object.freeze(next.history), upcomingEps: Object.freeze(next.upcomingEps) });
    for (const listener of this.#listeners) listener();
  }
  #reset(except?: AbortController): void {
    this.#generation++;
    this.#revision++;
    this.#token = null;
    for (const request of this.#requests.values()) if (request.controller !== except) request.controller.abort();
    this.#requests.clear();
    this.#publish(initial());
  }
  disconnect(): void { this.#reset(); }
  connect(credential: string): void {
    this.#reset();
    // Check prerequisites before retaining a credential or making private fetches.
    if (!supportsExactJSON()) {
      this.#publish({ ...initial(), connection: "unsupported" });
      throw new ClientError("unsupported_browser");
    }
    if (!["http://127.0.0.1:8000", "http://localhost:8000"].includes(this.#origin)) {
      this.#publish({ ...initial(), connection: "unsupported" });
      throw new ClientError("unsupported_origin");
    }
    if (typeof credential !== "string" || /^[A-Za-z0-9_-]{32,256}$/.exec(credential)?.[0] !== credential) throw new ClientError("invalid_request");
    this.#token = credential;
    this.#publish({ ...initial(), connection: "connected" });
  }
  #connected(): void {
    if (this.#snapshot.connection === "unsupported") throw new ClientError("unsupported_browser");
    if (this.#token === null) throw new ClientError("disconnected");
    // Also gate each request in case capabilities changed during the session.
    if (!supportsExactJSON()) {
      this.#reset();
      this.#publish({ ...initial(), connection: "unsupported" });
      throw new ClientError("unsupported_browser");
    }
  }
  #invalidateSelection(): void {
    this.#revision++;
    for (const [key, request] of this.#requests) {
      if (key.startsWith("history:")) { request.controller.abort(); this.#requests.delete(key); }
    }
    this.#publish({ ...this.#snapshot, selection: null, history: idle });
  }
  clearSelection(): void { this.#invalidateSelection(); }
  clearUpcomingEps(): void {
    this.#epsRevision++;
    for (const [key, request] of this.#requests) {
      if (key.startsWith("eps:")) { request.controller.abort(); this.#requests.delete(key); }
    }
    this.#publish({ ...this.#snapshot, upcomingEps: idle });
  }
  #consume<T>(pending: Pending, signal?: AbortSignal): Promise<T> {
    const id = Symbol();
    pending.consumers.add(id);
    return new Promise<T>((resolve, reject) => {
      let done = false;
      const finish = (value: unknown, failed: boolean): void => {
        if (done) return;
        done = true;
        signal?.removeEventListener("abort", cancelled);
        pending.controller.signal.removeEventListener("abort", cancelled);
        pending.consumers.delete(id);
        if (failed) reject(value); else resolve(value as T);
      };
      const cancelled = (): void => {
        finish(new ClientError("cancelled"), true);
        if (pending.consumers.size === 0) pending.controller.abort();
      };
      signal?.addEventListener("abort", cancelled, { once: true });
      pending.controller.signal.addEventListener("abort", cancelled, { once: true });
      if (signal?.aborted || pending.controller.signal.aborted) cancelled();
      pending.promise.then(value => finish(value, false), error => finish(error, true));
    });
  }
  #request<T>(key: string, run: (controller: AbortController) => Promise<T>, signal?: AbortSignal): Promise<T> {
    if (signal?.aborted) return Promise.reject(new ClientError("cancelled"));
    let pending = this.#requests.get(key);
    if (pending?.controller.signal.aborted) { this.#requests.delete(key); pending = undefined; }
    if (!pending) {
      const controller = new AbortController();
      const generation = this.#generation;
      const promise = Promise.resolve().then(async () => {
        if (controller.signal.aborted || generation !== this.#generation) throw new ClientError("cancelled");
        const result = await run(controller);
        if (controller.signal.aborted || generation !== this.#generation) throw new ClientError("cancelled");
        return result;
      });
      pending = { controller, promise, consumers: new Set() };
      this.#requests.set(key, pending);
      controller.signal.addEventListener("abort", () => {
        if (generation !== this.#generation || this.#requests.get(key)?.controller !== controller) return;
        if (key.startsWith("watchlist:") && this.#snapshot.namespace === key.slice("watchlist:".length)) this.#publish({ ...this.#snapshot, watchlist: idle });
        if (key.startsWith("history:")) this.#publish({ ...this.#snapshot, history: idle });
        if (key.startsWith("eps:")) this.#publish({ ...this.#snapshot, upcomingEps: idle });
      }, { once: true });
      const owned = pending;
      const remove = (): void => { if (this.#requests.get(key) === owned) this.#requests.delete(key); };
      promise.then(remove, remove);
    }
    return this.#consume<T>(pending, signal);
  }
  async #read(path: string, controller: AbortController): Promise<string> {
    this.#connected();
    try {
      const response = await this.#fetch(path, {
        method: "GET", headers: { Authorization: `Bearer ${this.#token}`, Accept: "application/json" },
        signal: controller.signal, cache: "no-store", credentials: "omit", redirect: "error", referrerPolicy: "no-referrer",
      });
      if (controller.signal.aborted) throw new ClientError("cancelled");
      if (response.status === 401) {
        this.#reset(controller);
        throw new ClientError("unauthorized");
      }
      if (response.redirected || !/^application\/json(?:\s*;|$)/i.test(response.headers.get("content-type") ?? "")) throw new ClientError("incompatible_response");
      const reader = response.body?.getReader();
      if (!reader) throw new ClientError("incompatible_response");
      const chunks: Uint8Array[] = [];
      let size = 0;
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (controller.signal.aborted) throw new ClientError("cancelled");
          if (done) break;
          size += value.byteLength;
          if (size > maxResponseBytes) throw new ClientError("incompatible_response");
          chunks.push(value);
        }
      } catch (error) {
        await reader.cancel().catch(() => undefined); // Cleanup only, preserve original failure.
        throw error;
      } finally { reader.releaseLock(); }
      const bytes = new Uint8Array(size);
      let offset = 0;
      for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
      let text: string;
      try { text = new TextDecoder("utf-8", { fatal: true }).decode(bytes); }
      catch { throw new ClientError("incompatible_response"); }
      if (!response.ok) {
        const error = decode("ErrorResponse", text).error;
        const contract = Object.hasOwn(errorContracts, error.code) ? errorContracts[error.code as keyof typeof errorContracts] : undefined;
        if (!contract || contract[0] !== response.status || contract[1] !== error.message) throw new ClientError("incompatible_response");
        throw new ClientError("api_error", error.code);
      }
      return text;
    } catch (error) {
      if (error instanceof ClientError) throw error;
      throw new ClientError(controller.signal.aborted ? "cancelled" : "network_error");
    }
  }
  loadWatchlist(namespace: Namespace, options: { signal?: AbortSignal } = {}): Promise<WatchlistResponse> {
    this.#connected();
    if (!validNamespace(namespace)) throw new ClientError("invalid_request");
    if (options.signal?.aborted) return Promise.reject(new ClientError("cancelled"));
    const key = `watchlist:${namespace}`;
    const existing = this.#requests.get(key);
    if (existing && !existing.controller.signal.aborted) return this.#consume(existing, options.signal);
    // Switching namespace abandons pending list work; reloading always discards detail.
    for (const [otherKey, request] of this.#requests) {
      if (otherKey.startsWith("watchlist:")) { request.controller.abort(); this.#requests.delete(otherKey); }
    }
    this.#invalidateSelection();
    this.#publish({ ...this.#snapshot, namespace, watchlist: { status: "loading" } });
    const generation = this.#generation;
    return this.#request(key, async controller => {
      try {
        const view = decode("WatchlistResponse", await this.#read(`/api/v1/watchlists/${namespace}`, controller));
        validateWatchlist(view, namespace);
        if (controller.signal.aborted || generation !== this.#generation) throw new ClientError("cancelled");
        this.#publish({ ...this.#snapshot, watchlist: { status: "success", data: view } });
        return view;
      } catch (error) {
        if (error instanceof ClientError && error.code !== "unauthorized" && !controller.signal.aborted && generation === this.#generation && this.#snapshot.namespace === namespace) {
          this.#publish({ ...this.#snapshot, watchlist: { status: "error", error } });
        }
        throw error;
      }
    }, options.signal);
  }
  async selectRow(namespace: Namespace, ordinal: number, expected: StockResponse, options: { signal?: AbortSignal } = {}): Promise<Selection> {
    if (!Number.isSafeInteger(ordinal) || ordinal < 0) throw new ClientError("invalid_request");
    // Re-read before detail, then bind to the returned request-local stock/ordinal.
    const view = await this.loadWatchlist(namespace, options);
    if (options.signal?.aborted) throw new ClientError("cancelled");
    const row = view.entries[ordinal];
    if (this.#snapshot.watchlist.status !== "success" || this.#snapshot.watchlist.data !== view || !row || !sameStock(row.stock, expected)) {
      this.#invalidateSelection();
      throw new ClientError("selection_changed");
    }
    this.#invalidateSelection();
    const selection = Object.freeze({ namespace, ordinal, stock: row.stock, revision: this.#revision });
    this.#publish({ ...this.#snapshot, selection });
    return selection;
  }
  loadHistory(selection: Selection, options: { start?: string; end?: string; signal?: AbortSignal } = {}): Promise<HistoryResponse> {
    this.#connected();
    if (selection !== this.#snapshot.selection || selection.revision !== this.#revision) throw new ClientError("selection_changed");
    const { start, end } = options;
    if ((start === undefined) !== (end === undefined) || (start !== undefined && (!validDate(start) || !validDate(end!) || start > end!))) throw new ClientError("invalid_request");
    if (options.signal?.aborted) return Promise.reject(new ClientError("cancelled"));
    const query = start === undefined ? "" : `?start=${start}&end=${end}`;
    const key = `history:${selection.namespace}:${selection.ordinal}:${selection.revision}:${query}`;
    const existing = this.#requests.get(key);
    if (!existing || existing.controller.signal.aborted) {
      for (const [oldKey, request] of this.#requests) {
        if (oldKey.startsWith("history:")) { request.controller.abort(); this.#requests.delete(oldKey); }
      }
      this.#publish({ ...this.#snapshot, history: { status: "loading" } });
    }
    const generation = this.#generation;
    return this.#request(key, async controller => {
      try {
        const view = decode("HistoryResponse", await this.#read(`/api/v1/watchlists/${selection.namespace}/entries/${selection.ordinal}/history${query}`, controller));
        validateHistory(view, selection.ordinal, selection.stock, start, end);
        if (controller.signal.aborted || generation !== this.#generation || selection !== this.#snapshot.selection) throw new ClientError("cancelled");
        this.#publish({ ...this.#snapshot, history: { status: "success", data: view } });
        return view;
      } catch (error) {
        if (error instanceof ClientError && error.code !== "unauthorized" && !controller.signal.aborted && generation === this.#generation && selection === this.#snapshot.selection) this.#publish({ ...this.#snapshot, history: { status: "error", error } });
        throw error;
      }
    }, options.signal);
  }
  loadUpcomingEps(request: UpcomingEpsRequest, options: { signal?: AbortSignal } = {}): Promise<UpcomingEpsResponse> {
    this.#connected();
    if (!validUpcomingEpsRequest(request)) throw new ClientError("invalid_request");
    if (options.signal?.aborted) return Promise.reject(new ClientError("cancelled"));
    const expected = Object.freeze({ provider_symbol: request.provider_symbol, start: request.start, end: request.end });
    this.clearUpcomingEps();
    const revision = this.#epsRevision, generation = this.#generation;
    const query = `provider_symbol=${expected.provider_symbol}&start=${expected.start}&end=${expected.end}`;
    this.#publish({ ...this.#snapshot, upcomingEps: { status: "loading" } });
    return this.#request(`eps:${query}`, async controller => {
      try {
        const view = decode("UpcomingEpsResponse", await this.#read(`/api/v1/research/upcoming-eps?${query}`, controller));
        validateUpcomingEps(view, expected);
        if (controller.signal.aborted || generation !== this.#generation || revision !== this.#epsRevision) throw new ClientError("cancelled");
        this.#publish({ ...this.#snapshot, upcomingEps: { status: "success", data: view } });
        return view;
      } catch (error) {
        if (error instanceof ClientError && error.code !== "unauthorized" && !controller.signal.aborted && generation === this.#generation && revision === this.#epsRevision) this.#publish({ ...this.#snapshot, upcomingEps: { status: "error", error } });
        throw error;
      }
    }, options.signal);
  }
}
