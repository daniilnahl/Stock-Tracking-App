# M9: Finnhub free-tier EPS feasibility

**Checked:** 2026-10-16 (America/Los_Angeles). **Status:** research only.
The owner requires EPS and requested evaluation of Finnhub's free tier after
confirming no paid subscriptions. Parent: [#164](https://github.com/daniilnahl/Stock-Tracking-App/issues/164),
[PR #165](https://github.com/daniilnahl/Stock-Tracking-App/pull/165).

## Finding

Finnhub is a plausible free source for **recent quarterly EPS actuals and
associated estimates**. It is not a verified free source for a forward EPS
estimate series or five-year expected EPS growth. Keep these separate metrics;
the existence of an `estimate` field does not establish a forward forecast feed.
FMP remains the selected primary source; this request authorizes investigation
of a targeted EPS supplement, not a general provider switch or activation.

## Verified endpoints and boundaries

The following details were read in the rendered official documentation because
plain-text fetchers returned only a JavaScript shell. Endpoint paths are relative
to `https://finnhub.io/api/v1`; none was invoked during this research.

| Need | Endpoint / documented fields | Free-tier finding |
| --- | --- | --- |
| Recent quarterly EPS results and associated estimates | [Earnings Surprises](https://finnhub.io/docs/api/company-earnings): `GET /stock/earnings?symbol=…`; `actual`, `estimate`, `period`, `quarter`, `year`, `symbol`, `surprise`, `surprisePercent` | Last **four quarters**. A `limit` parameter does not override account history restrictions. No annual EPS or longer history promised. |
| Release-calendar actual/estimated EPS | [Earnings Calendar](https://finnhub.io/docs/api/earnings-calendar): `GET /calendar/earnings`; `epsActual`, `epsEstimate`, release `date`/`hour`, fiscal `quarter`/`year`, `symbol` | **One month of historical earnings and new updates**. This is not an unrestricted forecast/history horizon. Calendar EPS is documented as non-GAAP; estimates combine sell-side and buy-side sources. |
| Annual or quarterly forward EPS estimate series | [EPS Estimates](https://finnhub.io/docs/api/company-eps-estimates): `GET /stock/eps-estimate`; `epsAvg`, `epsHigh`, `epsLow`, `numberAnalysts`, `period`, fiscal quarter/year; `freq=annual` or `quarterly` | Explicitly **Premium**. Do not route this requirement to a free key. |
| TTM EPS or long-term growth from basic metrics | [Basic Financials](https://finnhub.io/docs/api/company-basic-financials): `GET /stock/metric?symbol=…&metric=all`; generic `metric` and `series` maps | Section has no Premium label, but its example does not enumerate or guarantee EPS TTM/growth fields. Exact names, accounting basis, dates and free-account availability remain unverified. Do not promise these from a generic map. |

The surprise endpoint describes quarterly actual/estimate values but does not
fully define their accounting basis, currency, filing/publication time or
restatement vintage. Do not infer GAAP diluted EPS, reporting currency or
point-in-time reproducibility. Calendar non-GAAP documentation does not silently
settle the separate surprise endpoint's accounting basis.

## Access, limits and rights

[Finnhub pricing](https://finnhub.io/pricing) lists a free US/personal-use tier
with **60 calls/minute**, four quarters of EPS surprises and the calendar window
above; forward EPS estimates sit in the paid column. These are published plan
facts, not proof of an existing owner account or a runtime quota implementation.
[Authentication and limits](https://finnhub.io/docs/api) document an API token,
the `X-Finnhub-Token` header alternative and HTTP 429 on exceeded limits, with an
additional all-plan 30-calls/second ceiling. Prefer header authentication in an
eventual adapter; no credential belongs in logs, URLs, fixtures or artifacts.

Personal-use labeling is not blanket authorization for hosted redistribution,
arbitrary retention or report publication. Exact permitted local app use and
retention need review before activation. No account creation, key access,
subscription, provider data request or private holdings transmission occurred.
No Finnhub SDK/dependency was installed. The
[official Python client](https://github.com/Finnhub-Stock-API/finnhub-python/blob/master/finnhub/client.py)
independently confirms route names, not free entitlement or complete semantics.

## Recommended next contract

Start with a narrowly named **recent quarterly EPS actual/estimate observation**,
if that meets the owner's EPS need. Keep a distinct optional release-calendar
observation. Each record needs source, instrument mapping, fiscal year/quarter,
period end versus release date, retrieval time, actual versus estimate, units,
accounting basis and explicit unknown metadata. Unknown/missing values are not
zero; a negative EPS is valid data, not automatically a parser failure.

Do not sum four surprise values into GAAP TTM EPS, compute growth/PEG, mix FMP
GAAP with Finnhub adjusted numbers or infer future annual growth. Those would
require approved financial definitions, compatible inputs and known-value tests.
An earnings release date is not interchangeable with a fiscal period end.
Unknown historical availability cannot satisfy a backtest cutoff.
Four quarters alone also cannot establish latest-quarter year-over-year EPS
growth: the comparable prior-year quarter would require a fifth observation.

Before an implementation issue: choose quarterly actual versus TTM/annual/
forward EPS, accept the field/identity/accounting/missing-data contract, verify
free-account access and allowed use without exposing keys, and approve the
provider/service extension under existing architecture rules. Only then add an
isolated adapter with controlled fixture tests for negative/null EPS, precision,
period alignment, malformed results, entitlement errors, 429 and safe secrets.
Existing FMP/CLI/history/watchlist behavior must remain unchanged.

## Research evidence and verification limits

Sixteen Exa search results were requested in this focused investigation (eleven
Master, five independent reviewer). Official rendered docs and
pricing were inspected; no third-party coverage claim determines entitlement.
Documentation samples are illustrative, not live-account tests or financial
test expectations. No EPS financial calculation or runtime source was changed.
Independent review and local documentation checks are tracked in #164/PR #165;
existing full-suite results belong to their recorded earlier revisions.
