import { schemas } from "./contracts.generated";
import type { Contracts, WatchlistResponse, HistoryResponse, StockResponse } from "./contracts.generated";

export type Namespace = WatchlistResponse["namespace"];
export type ClientErrorCode = "unsupported_browser" | "unsupported_origin" | "invalid_request" | "incompatible_response" | "disconnected" | "cancelled" | "selection_changed" | "network_error" | "unauthorized" | "api_error";
const messages: Record<ClientErrorCode, string> = {
  unsupported_browser: "This browser cannot decode exact API numbers. Use a current supported browser.",
  unsupported_origin: "Open the dashboard from the local API listener.",
  invalid_request: "Request input is invalid.",
  incompatible_response: "The API response is incompatible. No data was published.",
  disconnected: "Connect to the local API before reading saved data.",
  cancelled: "The request was cancelled.",
  selection_changed: "The request-local row changed. Reload and select it again.",
  network_error: "The local API could not be reached.",
  unauthorized: "Authentication is required. Private views were cleared.",
  api_error: "The local API could not complete the request.",
};
export class ClientError extends Error {
  constructor(readonly code: ClientErrorCode, readonly apiCode?: string) {
    // Never attach input, raw exception, URL, response message or credential.
    super(messages[code]);
    this.name = "ClientError";
  }
}
class NumericLexeme {
  constructor(readonly source: string) {}
}
type SourceContext = { source?: string };
type SourceParse = (text: string, reviver: (key: string, value: unknown, context?: SourceContext) => unknown) => unknown;
const sourceParse: SourceParse = (text, reviver) => (JSON.parse as SourceParse)(text, reviver);
export function supportsExactJSON(): boolean {
  try {
    const probe = sourceParse("9223372036854775807", (_key, _value, context) => context?.source);
    return probe === "9223372036854775807";
  } catch { return false; }
}
export function parseExactJSON(text: string): unknown {
  if (!supportsExactJSON()) throw new ClientError("unsupported_browser");
  try {
    return sourceParse(text, (_key, value, context) => {
      if (typeof value !== "number") return value;
      if (typeof context?.source !== "string") throw new ClientError("unsupported_browser");
      return new NumericLexeme(context.source);
    });
  } catch (error) {
    if (error instanceof ClientError) throw error;
    throw new ClientError("incompatible_response");
  }
}
type Schema = {
  readonly $ref?: string;
  readonly type?: string;
  readonly anyOf?: readonly Schema[];
  readonly const?: unknown;
  readonly enum?: readonly unknown[];
  readonly properties?: Readonly<Record<string, Schema>>;
  readonly required?: readonly string[];
  readonly additionalProperties?: boolean;
  readonly items?: Schema;
  readonly pattern?: string;
  readonly minimum?: string;
  readonly maximum?: string;
};
function incompatible(): never { throw new ClientError("incompatible_response"); }
function validate(value: unknown, schema: Schema): unknown {
  if (schema.$ref) {
    const name = schema.$ref.slice("#/components/schemas/".length) as keyof Contracts;
    if (!(name in schemas)) return incompatible();
    return validate(value, schemas[name]);
  }
  if (schema.anyOf) {
    for (const option of schema.anyOf) {
      try { return validate(value, option); } catch (error) {
        if (!(error instanceof ClientError) || error.code !== "incompatible_response") throw error;
      }
    }
    return incompatible();
  }
  if (Object.hasOwn(schema, "const") && value !== schema.const) return incompatible();
  if (schema.enum && !schema.enum.includes(value)) return incompatible();
  if (schema.type === "null") return value === null ? null : incompatible();
  if (schema.type === "string") {
    if (typeof value !== "string") return incompatible();
    // JSON schema's $ permits a final newline in JS; demand an entire match.
    if (schema.pattern) {
      const match = new RegExp(schema.pattern).exec(value);
      if (!match || match[0] !== value) return incompatible();
    }
    return value;
  }
  if (schema.type === "integer") {
    if (!(value instanceof NumericLexeme) || !/^(0|[1-9][0-9]*)$/.test(value.source)) return incompatible();
    const exact = BigInt(value.source);
    if ((schema.minimum !== undefined && exact < BigInt(schema.minimum)) ||
        (schema.maximum !== undefined && exact > BigInt(schema.maximum))) return incompatible();
    if (schema.maximum && BigInt(schema.maximum) > BigInt(Number.MAX_SAFE_INTEGER)) return exact;
    if (exact > BigInt(Number.MAX_SAFE_INTEGER)) return incompatible();
    return Number(exact); // Ordinals only, proven safe; never Decimal/volume.
  }
  if (schema.type === "array") {
    if (!Array.isArray(value) || !schema.items) return incompatible();
    return Object.freeze(value.map(item => validate(item, schema.items!)));
  }
  if (schema.type === "object") {
    if (!value || typeof value !== "object" || Array.isArray(value) || value instanceof NumericLexeme) return incompatible();
    const object = value as Record<string, unknown>;
    const properties = schema.properties ?? {};
    if (schema.required?.some(key => !Object.hasOwn(object, key))) return incompatible();
    if (schema.additionalProperties === false && Object.keys(object).some(key => !Object.hasOwn(properties, key))) return incompatible();
    return Object.freeze(Object.fromEntries(Object.keys(object).map(key => [key, validate(object[key], properties[key]!)])));
  }
  return incompatible();
}
export function decode<K extends keyof Contracts>(name: K, text: string): Contracts[K] {
  return validate(parseExactJSON(text), schemas[name]) as Contracts[K];
}
export function validDate(value: string): boolean {
  if (!/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(value) || value.slice(0, 4) === "0000") return false;
  const parsed = new Date(`${value}T00:00:00.000Z`);
  return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}
export function validNamespace(value: string): value is Namespace {
  return value === "menu_watchlist" || value === "daniils_stock_method";
}
export function sameStock(left: StockResponse, right: StockResponse): boolean {
  return left.symbol === right.symbol && left.name === right.name && left.exchange === right.exchange;
}
export function validateWatchlist(view: WatchlistResponse, namespace: Namespace): void {
  if (view.namespace !== namespace || view.entries.some((row, index) => row.ordinal !== index)) incompatible();
}
export function validateHistory(view: HistoryResponse, ordinal: number, stock: StockResponse, start?: string, end?: string): void {
  if (view.ordinal !== ordinal || !sameStock(view.stock, stock) || !validDate(view.start) || !validDate(view.end) ||
      view.start > view.end || (start !== undefined && (view.start !== start || view.end !== end)) || view.bars.length === 0) incompatible();
  let previous = "";
  for (const bar of view.bars) {
    if (bar.symbol !== stock.symbol.toUpperCase() || !validDate(bar.date) || bar.date < view.start || bar.date > view.end || bar.date <= previous) incompatible();
    previous = bar.date;
  }
}
