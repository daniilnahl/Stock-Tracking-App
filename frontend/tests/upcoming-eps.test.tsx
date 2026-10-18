// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../src/App";
import { ApiClient } from "../src/services/client";
import { credential, deferred, response, watchlist } from "./fixtures";
import { epsRequest, epsResponse } from "./eps-fixtures";

beforeEach(() => { localStorage.clear(); sessionStorage.clear(); window.history.replaceState(null, "", "/#upcoming-eps"); });
afterEach(cleanup);
function navigate(hash: string) { act(() => { window.history.replaceState(null, "", `/${hash}`); window.dispatchEvent(new HashChangeEvent("hashchange")); }); }
function form(symbol = epsRequest.provider_symbol, start = epsRequest.start, end = epsRequest.end) {
  for (const [label, value] of [["Finnhub provider symbol", symbol], ["EPS start date", start], ["EPS end date", end]]) fireEvent.change(screen.getByLabelText(label!), { target: { value } });
}
function mount(fetcher = vi.fn(async (_url: string, _init: RequestInit) => response(epsResponse())), connect = true) {
  const client = new ApiClient({ origin: "http://127.0.0.1:8000", fetch: fetcher });
  if (connect) client.connect(credential);
  render(<App createClient={() => client} />);
  return { client, fetcher };
}
async function read() { await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Read upcoming EPS" })); }); }
describe("manual upcoming EPS page", () => {
  it("starts blank/disconnected with no request, presets, provider key or persistence", () => {
    const { fetcher } = mount(undefined, false);
    for (const label of ["Finnhub provider symbol", "EPS start date", "EPS end date"]) expect((screen.getByLabelText(label) as HTMLInputElement).value).toBe("");
    expect((screen.getByRole("button", { name: "Read upcoming EPS" }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByText(/The Finnhub key stays on the server/)).toBeTruthy();
    expect(fetcher).not.toHaveBeenCalled();
    expect(Object.keys(localStorage)).toEqual([]); expect(Object.keys(sessionStorage)).toEqual([]);
  });
  it("displays exact positive/zero/negative/null values and all limitations without converting", async () => {
    const { fetcher } = mount(); form(); await read();
    expect(screen.getByRole("cell", { name: "1.250000000000000001" })).toBeTruthy();
    expect(screen.getByRole("cell", { name: "0" })).toBeTruthy();
    expect(screen.getByRole("cell", { name: "-0.25" })).toBeTruthy();
    expect(screen.getByRole("cell", { name: "Unavailable (null estimate)" })).toBeTruthy();
    expect(screen.getByText(/Currency: unknown. Basic\/diluted share basis: unknown/)).toBeTruthy();
    expect(screen.getByText(/Source: earnings_calendar. Source field: epsEstimate/)).toBeTruthy();
    expect(screen.getByText(/receipt time records retrieval, not forecast publication/)).toBeTruthy();
    expect(screen.getByText(/Coverage: not asserted/)).toBeTruthy();
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(Object.keys(localStorage)).toEqual([]); expect(Object.keys(sessionStorage)).toEqual([]);
  });
  it.each([["test", "2026-10-18", "2027-01-17", "Finnhub provider symbol"], ["TEST", "2026-02-30", "2027-01-17", "EPS start date"], ["TEST", "2026-10-18", "2027-01-18", "EPS start date"]])("rejects invalid local inputs with accessible focus", async (symbol, start, end, field) => {
    const { fetcher } = mount(); form(symbol, start, end); await read();
    expect(document.activeElement).toBe(screen.getByLabelText(field));
    expect(screen.getByLabelText(field).getAttribute("aria-invalid")).toBe("true");
    expect(screen.getByRole("alert").textContent).toContain("92-date");
    expect(fetcher).not.toHaveBeenCalled();
  });
  it.each([
    [503, "eps_disabled", "Upcoming EPS acquisition is disabled.", "disabled on this local API"],
    [429, "eps_rate_limited", "Upcoming EPS request budget is unavailable.", "Wait at least 60 seconds"],
    [503, "api_busy", "API operation capacity is unavailable.", "still finishing"],
    [429, "provider_rate_limited", "Market-data rate limit reached.", "provider rate limit"],
    [422, "invalid_request", "Request input is invalid.", "server's UTC reference day"],
  ])("provides fixed actionable API state %s/%s without auto retry", async (status, code, message, expected) => {
    const { fetcher } = mount(vi.fn(async () => response({ error: { code, message } }, status as number)));
    form(); await read();
    expect(screen.getByRole("alert").textContent).toContain(expected);
    if (code === "invalid_request") expect(document.activeElement).toBe(screen.getByLabelText("EPS start date"));
    expect(screen.queryByRole("table")).toBeNull(); expect(fetcher).toHaveBeenCalledTimes(1);
  });
  it("distinguishes an empty result without a complete-market or invalid-symbol claim", async () => {
    const data = epsResponse(); data.observations = [];
    mount(vi.fn(async () => response(data))); form(); await read();
    expect(screen.getByText("No observations returned")).toBeTruthy();
    expect(screen.getByText(/not proof of an invalid symbol, complete coverage/)).toBeTruthy();
    expect(screen.queryByRole("table")).toBeNull();
  });
  it("clears on edits and cancellation, ignores late success and restores keyboard focus", async () => {
    const pending = deferred<Response>();
    const { fetcher } = mount(vi.fn((_url: string, _init: RequestInit) => pending.promise));
    form(); await read();
    fireEvent.click(screen.getByRole("button", { name: "Cancel EPS read" }));
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Read upcoming EPS" }));
    await act(async () => pending.resolve(response(epsResponse())));
    expect(screen.queryByRole("table")).toBeNull();
    expect(screen.getByText("EPS read cancelled")).toBeTruthy();
    fetcher.mockImplementation(async () => response(epsResponse())); await read();
    expect(screen.getByRole("table")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("EPS end date"), { target: { value: "2027-01-16" } });
    expect(screen.queryByRole("table")).toBeNull(); expect(fetcher).toHaveBeenCalledTimes(2);
  });
  it.each(["clear", "navigation", "disconnect", "pagehide", "401"])("%s removes private EPS and suppresses ignored late work", async mode => {
    const pending = deferred<Response>();
    const { client, fetcher } = mount(vi.fn((_url: string, _init: RequestInit) => pending.promise));
    form(); await read();
    if (mode === "clear") fireEvent.click(screen.getByRole("button", { name: "Clear EPS" }));
    else if (mode === "navigation") { navigate("#overview"); navigate("#upcoming-eps"); }
    else if (mode === "disconnect") act(() => client.disconnect());
    else if (mode === "pagehide") act(() => window.dispatchEvent(new Event("pagehide")));
    else {
      fetcher.mockImplementation(async () => response({ error: { code: "unauthorized", message: "Authentication is required." } }, 401));
      await act(async () => { await client.loadWatchlist("menu_watchlist").catch(() => undefined); });
    }
    await act(async () => pending.resolve(response(epsResponse())));
    expect(screen.queryByRole("table")).toBeNull();
    expect(client.getSnapshot().upcomingEps.status).toBe("idle");
  });
  it("401 current EPS read clears already loaded saved observations and gives auth guidance", async () => {
    const { client, fetcher } = mount(vi.fn(async () => response(watchlist())));
    await act(async () => { await client.loadWatchlist("menu_watchlist"); });
    fetcher.mockImplementation(async () => response({ error: { code: "unauthorized", message: "Authentication is required." } }, 401));
    form(); await read();
    expect(screen.getByRole("alert").textContent).toContain("Authentication is required");
    expect(client.getSnapshot().watchlist.status).toBe("idle");
    expect(screen.queryByRole("table")).toBeNull();
  });
});
