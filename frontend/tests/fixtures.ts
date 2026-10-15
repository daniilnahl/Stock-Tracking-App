import type { Namespace } from "../src/services/validation";

export const stock = { symbol: "DEMO", name: "Synthetic", exchange: "NASDAQ" };
export function watchlist(namespace: Namespace = "menu_watchlist") {
  return {
    namespace, name: "Synthetic only", observation: "saved",
    provenance: { source: null, observed_at: null, retrieved_at: null, freshness: "unknown" },
    entries: [0, 1].map(ordinal => ({ ordinal, stock: { ...stock },
      quantity: ordinal === 0 ? "0.12345678901234567890123456789" : "0",
      average_cost: null, current_price: ordinal === 0 ? null : "0",
      metadata: { sector: null, country: null, currency: "opaque label", market_cap: null, price_1d: null,
        price_5d: null, price_30d: null, price_3m: null, price_6m: null, price_1y: null, price_3y: null, price_5y: null },
      snapshot: null,
    })),
  };
}
export function history(ordinal = 0) {
  return { stock: { ...stock }, ordinal, start: "2020-01-02", end: "2020-01-06", price_basis: "raw",
    provenance: { source: null, observed_at: null, retrieved_at: null, currency: null, freshness: "unknown" },
    bars: ["2020-01-02", "2020-01-06"].map(date => ({ symbol: "DEMO", date, open: "100.0000", high: "120",
      low: "99", close: "110.0000000000000000001", adjusted_close: null, volume: 0 })),
  };
}
export function response(value: unknown, status = 200): Response {
  return new Response(typeof value === "string" ? value : JSON.stringify(value), { status, headers: { "content-type": "application/json" } });
}
export function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
export const credential = ["synthetic", "not", "a", "real", "credential", "0000"].join("_");
