import type { UpcomingEpsRequest } from "../src/services/validation";
export const epsRequest: UpcomingEpsRequest = { provider_symbol: "TEST", start: "2026-10-18", end: "2027-01-17" };
export function epsResponse() {
  return {
    provider: "finnhub", provider_symbol: "TEST", start: epsRequest.start, end: epsRequest.end, analysis_date: "2026-10-17",
    date_convention: "utc-reference-day/vendor-date-labels", observation_kind: "upcoming_release_eps_estimate", coverage: "not_asserted",
    observations: ["1.250000000000000001", "0", "-0.25", null].map((estimate, index) => ({
      symbol: "TEST", fiscal_year: 2026, fiscal_quarter: index + 1, release_date: "2026-10-20", release_session: index === 3 ? null : "amc",
      estimate, retrieved_at: "2026-10-17T20:00:00.000001Z", provider: "finnhub", source: "earnings_calendar", source_field: "epsEstimate",
      accounting_basis: "non-GAAP", units: "currency-per-share", currency: null, share_basis: null, published_at: null, fiscal_period_end: null,
    })),
  };
}
