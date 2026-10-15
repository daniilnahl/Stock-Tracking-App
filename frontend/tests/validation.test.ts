import { describe, expect, it, vi } from "vitest";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { schemas } from "../src/services/contracts.generated";
import { ClientError, decode, parseExactJSON, supportsExactJSON, validDate, validateHistory, validateWatchlist } from "../src/services/validation";
import { history, stock, watchlist } from "./fixtures";

describe("reviewed schema generation", () => {
  it("is reproducible and retains the exact int64 schema bound", () => {
    execFileSync(process.execPath, ["scripts/generate-contracts.mjs", "--check"], { stdio: "pipe" });
    const volume = schemas.BarResponse.properties.volume.anyOf[0];
    expect(volume.maximum).toBe("9223372036854775807");
    expect(readFileSync("src/services/contracts.generated.ts", "utf8")).not.toContain("9223372036854776000");
  });
});
describe("lossless decoding", () => {
  it("preserves max volume as bigint, precision text and zero/null distinctly", () => {
    const document = JSON.stringify(history()).replace('"volume":0', '"volume":9223372036854775807');
    const result = decode("HistoryResponse", document);
    expect(result.bars[0]?.volume).toBe(9223372036854775807n);
    expect(result.bars[1]?.volume).toBe(0n);
    expect(result.bars[0]?.close).toBe("110.0000000000000000001");
    expect(Object.isFrozen(result.bars)).toBe(true);
    const saved = decode("WatchlistResponse", JSON.stringify(watchlist()));
    expect(saved.entries[0]?.quantity).toBe("0.12345678901234567890123456789");
    expect(saved.entries[0]?.current_price).toBeNull();
    expect(saved.entries[1]?.current_price).toBe("0");
    expect(saved.entries[1]?.snapshot).toBeNull();
  });
  it.each(["9223372036854775808", "-1", "-0", "1.1", "1e3", '"1"', "true", "{}", "1e400"])("refuses invalid volume %s without rounding", volume => {
    const text = JSON.stringify(history()).replace('"volume":0', `"volume":${volume}`);
    expect(() => decode("HistoryResponse", text)).toThrowError(ClientError);
  });
  it("preserves absent volume as null", () => {
    expect(decode("HistoryResponse", JSON.stringify(history()).replaceAll('"volume":0', '"volume":null')).bars[0]?.volume).toBeNull();
  });
  it.each(["0.000000000000000000001", "1E-2000", "1e999999999", "-0", "+0", ".5", "1."])("retains exact finite Decimal syntax %s", value => {
    const document = watchlist(); document.entries[0]!.quantity = value;
    expect(decode("WatchlistResponse", JSON.stringify(document)).entries[0]?.quantity).toBe(value);
  });
  it.each(["NaN", "Infinity", "", " 1", "1\n", "0x10"])("rejects invalid Decimal string %s", value => {
    const document = watchlist(); document.entries[0]!.quantity = value;
    expect(() => decode("WatchlistResponse", JSON.stringify(document))).toThrowError(ClientError);
  });
  it.each(["9007199254740992", '"0"', "-0", "1.0"])("rejects incompatible ordinal %s", ordinal => {
    expect(() => decode("HistoryResponse", JSON.stringify(history()).replace('"ordinal":0', `"ordinal":${ordinal}`))).toThrowError(ClientError);
  });
  it("rejects missing/extra fields, wrong literals, JSON numeric Decimal and malformed JSON with safe diagnostics", () => {
    for (const text of [JSON.stringify({ ...history(), secret: "untrusted" }), JSON.stringify({ ...history(), price_basis: "adjusted" }),
      JSON.stringify(watchlist()).replace('"quantity":"0"', '"quantity":0'), '{"untrusted":', JSON.stringify({})]) {
      expect(() => decode("HistoryResponse", text)).toThrow("The API response is incompatible. No data was published.");
    }
    expect(() => parseExactJSON("{malformed private text}")).toThrow("The API response is incompatible. No data was published.");
  });
  it("requires source-context support and has no fallback to a rounded value", () => {
    const native = JSON.parse;
    vi.spyOn(JSON, "parse").mockImplementation((text, reviver) => native(text, reviver ? (key, value) => reviver(key, value) : undefined));
    expect(supportsExactJSON()).toBe(false);
    expect(() => parseExactJSON("9223372036854775807")).toThrow("This browser cannot decode exact API numbers.");
  });
});
describe("response association", () => {
  it("validates namespace and ordered duplicate ordinals", () => {
    const view = decode("WatchlistResponse", JSON.stringify(watchlist()));
    validateWatchlist(view, "menu_watchlist");
    expect(() => validateWatchlist(view, "daniils_stock_method")).toThrowError(ClientError);
    const document = watchlist(); document.entries[1]!.ordinal = 0;
    expect(() => validateWatchlist(decode("WatchlistResponse", JSON.stringify(document)), "menu_watchlist")).toThrowError(ClientError);
  });
  it("validates stock, ordinal, resolved dates and sparse bar association", () => {
    const view = decode("HistoryResponse", JSON.stringify(history()));
    validateHistory(view, 0, stock, "2020-01-02", "2020-01-06");
    expect(() => validateHistory(view, 1, stock)).toThrowError(ClientError);
    expect(() => validateHistory(view, 0, { ...stock, name: "Other row" })).toThrowError(ClientError);
    expect(() => validateHistory(view, 0, stock, "2020-01-03", "2020-01-06")).toThrowError(ClientError);
    for (const change of ["date", "symbol", "order", "empty"]) {
      const document = history();
      if (change === "date") document.bars[0]!.date = "2020-02-30";
      if (change === "symbol") document.bars[0]!.symbol = "OTHER";
      if (change === "order") document.bars.reverse();
      if (change === "empty") document.bars = [];
      expect(() => validateHistory(decode("HistoryResponse", JSON.stringify(document)), 0, stock)).toThrowError(ClientError);
    }
    expect(validDate("2020-02-29")).toBe(true);
    expect(validDate("2019-02-29")).toBe(false);
    expect(validDate("0000-01-01")).toBe(false);
  });
});
