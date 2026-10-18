import { describe, expect, it, vi } from "vitest";
import { ApiClient } from "../src/services/client";
import { ClientError, decode, validateUpcomingEps, validUpcomingEpsRequest } from "../src/services/validation";
import { credential, deferred, response, watchlist } from "./fixtures";
import { epsRequest, epsResponse } from "./eps-fixtures";

function create(fetcher = vi.fn(async (_url: string, _init: RequestInit) => response(epsResponse()))) {
  const client = new ApiClient({ origin: "http://127.0.0.1:8000", fetch: fetcher });
  client.connect(credential); return { client, fetcher };
}
const turn = async () => { await Promise.resolve(); await Promise.resolve(); };
describe("explicit EPS exact decode and manual transport", () => {
  it("uses one authenticated local GET, preserves exact values and freezes validated results", async () => {
    const { client, fetcher } = create();
    expect(fetcher).not.toHaveBeenCalled();
    const view = await client.loadUpcomingEps(epsRequest);
    expect(view.observations.map(item => item.estimate)).toEqual(["1.250000000000000001", "0", "-0.25", null]);
    expect(Object.isFrozen(view)).toBe(true); expect(Object.isFrozen(view.observations[0])).toBe(true);
    expect(fetcher).toHaveBeenCalledTimes(1);
    const [url, init] = fetcher.mock.calls[0]!;
    expect(url).toBe("/api/v1/research/upcoming-eps?provider_symbol=TEST&start=2026-10-18&end=2027-01-17");
    expect(init).toMatchObject({ method: "GET", headers: { Authorization: `Bearer ${credential}`, Accept: "application/json" }, credentials: "omit", cache: "no-store", redirect: "error", referrerPolicy: "no-referrer" });
    expect(client.getSnapshot().upcomingEps).toMatchObject({ status: "success" });
    expect(JSON.stringify(client.getSnapshot())).not.toContain(credential);
  });
  it.each([
    { ...epsRequest, provider_symbol: "test" }, { ...epsRequest, provider_symbol: " TEST" }, { ...epsRequest, provider_symbol: ".A" },
    { ...epsRequest, provider_symbol: "A".repeat(33) }, { ...epsRequest, provider_symbol: "A\n" },
    { ...epsRequest, start: "2026-02-30" }, { ...epsRequest, start: "0000-10-18" }, { ...epsRequest, start: "2026-10-18\n" },
    { ...epsRequest, end: "2027-01-18" }, { ...epsRequest, end: "2026-10-17" },
  ])("rejects local invalid values before fetch", input => {
    const { client, fetcher } = create();
    expect(validUpcomingEpsRequest(input)).toBe(false);
    expect(() => client.loadUpcomingEps(input)).toThrow(ClientError);
    expect(fetcher).not.toHaveBeenCalled();
  });
  it("does not invent a browser-clock future cutoff and requires a configured exact browser", async () => {
    expect(validUpcomingEpsRequest({ provider_symbol: "A", start: "2000-01-01", end: "2000-01-01" })).toBe(true);
    const client = new ApiClient({ origin: "http://127.0.0.1:8000" });
    expect(() => client.loadUpcomingEps(epsRequest)).toThrow(ClientError);
    expect(fetch).not.toHaveBeenCalled();
  });
  it.each([
    (value: ReturnType<typeof epsResponse>) => { value.provider_symbol = "OTHER"; },
    value => { value.start = "2026-10-19"; }, value => { value.end = "2027-01-16"; }, value => { value.analysis_date = "2026-10-18"; },
    value => { value.analysis_date = "2026-02-30"; }, value => { value.observations[0]!.symbol = "OTHER"; },
    value => { value.observations[0]!.release_date = "2026-02-30"; }, value => { value.observations[0]!.release_date = "2026-10-17"; },
    value => { value.observations[0]!.retrieved_at = "2026-02-30T20:00:00Z"; }, value => { value.observations[0]!.retrieved_at = "2026-10-17T24:00:00Z"; },
    value => { value.observations[0]!.retrieved_at = "2026-10-17T20:60:00Z"; }, value => { value.observations[0]!.retrieved_at = "2026-10-17T20:00:60Z"; },
    value => { value.observations[0]!.retrieved_at = "2026-10-17T20:00:00+00:00"; },
    value => { value.observations[0]!.release_session = "unknown"; }, value => { value.observations[0]!.source = "other"; },
    value => { value.observations[0]!.accounting_basis = "GAAP"; }, value => { value.observations[0]!.estimate = "NaN"; },
    value => { value.observations[0]!.estimate = "Infinity"; }, value => { value.observations[0]!.fiscal_quarter = 5; },
    value => { value.observations[0]!.fiscal_year = 0; }, value => { value.observations[1]!.fiscal_quarter = 1; },
    value => { value.observations.reverse(); }, value => { value.observations = Array.from({ length: 129 }, () => value.observations[0]!); },
  ])("rejects schema/context/row/provenance inconsistencies without publishing", async mutate => {
    const value = epsResponse(); mutate(value);
    const { client } = create(vi.fn(async () => response(value)));
    await expect(client.loadUpcomingEps(epsRequest)).rejects.toMatchObject({ code: "incompatible_response" });
    expect(client.getSnapshot().upcomingEps).toMatchObject({ status: "error" });
  });
  it("rejects falsely known metadata and numeric EPS, while empty and zero differ", async () => {
    for (const changes of [{ currency: "USD" }, { share_basis: "diluted" }, { published_at: "2026-10-01" }, { fiscal_period_end: "2026-09-30" }, { estimate: 1.25 }]) {
      const value = epsResponse(); Object.assign(value.observations[0]!, changes);
      expect(() => validateUpcomingEps(decode("UpcomingEpsResponse", JSON.stringify(value)), epsRequest)).toThrow(ClientError);
    }
    const value = epsResponse(); value.observations = [];
    const { client } = create(vi.fn(async () => response(value)));
    expect((await client.loadUpcomingEps(epsRequest)).observations).toEqual([]);
  });
  it("cancel/clear/supersession suppress ignored late results, preserving the current request", async () => {
    const first = deferred<Response>(), second = deferred<Response>();
    const fetcher = vi.fn((_url: string, _init: RequestInit) => first.promise).mockImplementationOnce(() => first.promise).mockImplementationOnce(() => second.promise);
    const { client } = create(fetcher);
    const previous = client.loadUpcomingEps(epsRequest).catch(error => error.code); await turn();
    const pending = client.loadUpcomingEps(epsRequest); await turn();
    expect(await previous).toBe("cancelled");
    first.resolve(response(epsResponse()));
    expect(client.getSnapshot().upcomingEps.status).toBe("loading");
    second.resolve(response(epsResponse())); await pending;
    client.clearUpcomingEps(); expect(client.getSnapshot().upcomingEps.status).toBe("idle");
    expect(fetcher).toHaveBeenCalledTimes(2);
  });
  it("401 clears EPS, saved data and history; disconnect and replacement credentials suppress late reads", async () => {
    const { client, fetcher } = create(vi.fn(async () => response(watchlist())));
    await client.loadWatchlist("menu_watchlist");
    fetcher.mockImplementation(async () => response({ error: { code: "unauthorized", message: "Authentication is required." } }, 401));
    await expect(client.loadUpcomingEps(epsRequest)).rejects.toMatchObject({ code: "unauthorized" });
    expect(client.getSnapshot()).toMatchObject({ connection: "disconnected", upcomingEps: { status: "idle" }, watchlist: { status: "idle" }, history: { status: "idle" } });
    client.connect(credential);
    const late = deferred<Response>(); fetcher.mockImplementation(() => late.promise);
    const operation = client.loadUpcomingEps(epsRequest).catch(error => error.code); await turn();
    client.disconnect(); client.connect(credential);
    late.resolve(response(epsResponse())); expect(await operation).toBe("cancelled");
    expect(client.getSnapshot().upcomingEps.status).toBe("idle");
  });
});
