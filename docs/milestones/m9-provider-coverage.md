# M9 provider coverage: FMP first, FINVIZ enrichment

**Research date:** 2026-10-16 (America/Los_Angeles).
**Status:** public-documentation feasibility research, not an activated connector
or approved financial screen. Parent: [#164](https://github.com/daniilnahl/Stock-Tracking-App/issues/164),
[planning PR #165](https://github.com/daniilnahl/Stock-Tracking-App/pull/165).

The owner selected **FMP first, then FINVIZ**, and requested research into metrics
FINVIZ provides that FMP does not natively provide. The final phrase “for those
covered by FMP” is interpreted in that context as **not covered by FMP**; that
interpretation remains open to correction. This records source priority, not
acceptance of all M9 decisions, a preset or account entitlement.

## What counts as a gap

Distinguish four things: a metric absent from this application's small adapter;
a missing native vendor endpoint; an endpoint excluded by the owner's plan; and
a null/outage for one security. Only the second is the requested native-coverage
gap. A plan limitation or a failed FMP request must not silently change source.

“No native equivalent located” below means not identified in the current public
FMP stable catalog and targeted official-documentation searches. It does not
prove permanent vendor-wide absence. Educational articles, raw ingredients,
similar names and legacy endpoints do not establish a current native field.
Public documentation also does not establish authenticated account availability.

## FINVIZ enrichment shortlist

FINVIZ metric descriptions below come from its
[official screener help](https://finviz.com/help/screener.ashx).
FMP negative findings were checked against the
[stable catalog](https://site.financialmodelingprep.com/developer/docs), including
the listed technical indicators, quotes, share-float and ownership families.
These are **candidate fields**, not verified FINVIZ API column identifiers.

| Field | FINVIZ evidence | FMP comparison and decision |
| --- | --- | --- |
| Short Float | Exportable percentage of float sold short. | No native short-interest/short-float equivalent located. FMP share float is a different quantity. High-priority enrichment candidate. |
| Short Interest / Short Ratio | Labels appear on [official stock detail](https://finviz.com/stock?t=JPM&ty=si). | No native equivalent located. API exportability, dated observations and ratio denominator/window need verification; labels alone do not authorize a days-to-cover formula. |
| Relative Volume | Exportable; three-month baseline with intraday adjustment. | No matching native field located. Dividing FMP volume by an average is not proven equivalent. High-priority enrichment candidate. |
| ATR | Exportable; 14-day exponentially smoothed true range. | No native ATR endpoint located in the stable catalog. FMP OHLC inputs are ingredients, not an ATR field. Candidate, subject to exact API and smoothing semantics. |
| Volatility | Exportable average daily high/low percentage range. | FMP [standard deviation](https://site.financialmodelingprep.com/developer/docs/stable/standard-deviation) measures closing-price dispersion. Preserve distinct metric IDs; verify FINVIZ windows. |
| EPS next 5 years | Exportable long-term annual EPS growth estimate. | FMP [estimates](https://site.financialmodelingprep.com/developer/docs/stable/financial-estimates) provide forecast financial values. A multi-year estimate series is not a verified equivalent aggregate. Conditional semantic-gap candidate. |
| Insider Transactions | Exportable aggregate ownership-change percentage. | FMP [insider statistics](https://site.financialmodelingprep.com/developer/docs/stable/insider-trade-statistics) describe transaction statistics. No exact FINVIZ-equivalent window/denominator verified. Conditional candidate. |
| Institutional Transactions | Exportable aggregate ownership-change percentage. | FMP [positions summary](https://site.financialmodelingprep.com/developer/docs/stable/positions-summary) already includes ownership and changes. Compare periods/denominators before declaring a gap; FMP first. |

Priority is an engineering research order, not an investment ranking. All rows
remain activation-gated. Unknown observation dates or formula details cannot
qualify evidence requiring them, and current snapshots cannot prove historical
point-in-time availability. No metric has been added to FINANCIAL_CALCULATIONS.md.

## Keep documented overlapping capabilities with FMP

| Capability | Native FMP evidence | Routing implication |
| --- | --- | --- |
| Prices, volume and market identity | [Quote](https://site.financialmodelingprep.com/developer/docs/stable/quote), stable catalog profile/search | Extend the FMP adapter as needed; do not mistake its current small model for vendor absence. |
| Valuation, profitability, liquidity and leverage ratios | [TTM ratios](https://site.financialmodelingprep.com/developer/docs/stable/metrics-ratios-ttm), [ratio methods](https://site.financialmodelingprep.com/developer/docs/formula) | Prefer FMP for supported P/E, P/B, P/S, cash-flow ratios, margins and balance-sheet ratios. Verify exact response field/period before mapping. |
| ROA, ROE, ROIC and other key metrics | [Key metrics TTM](https://site.financialmodelingprep.com/developer/docs/stable/key-metrics-ttm) | Not FINVIZ-only. Same name does not guarantee matching calculation. |
| Shares outstanding / float | [Share float](https://site.financialmodelingprep.com/developer/docs/stable/shares-float) | FMP supports this family; float is not short float. |
| RSI and moving averages | [RSI](https://site.financialmodelingprep.com/developer/docs/stable/relative-strength-index), [SMA](https://site.financialmodelingprep.com/developer/docs/stable/simple-moving-average) | FMP provides native indicators. Percentage distance from a moving average is a separate derived output. |
| Historical statement growth | [Income growth](https://site.financialmodelingprep.com/developer/docs/stable/income-statement-growth), [financial growth](https://site.financialmodelingprep.com/developer/docs/stable/financial-statement-growth) | Prefer FMP; align annual/quarterly and year-over-year periods explicitly. |
| Analyst estimates and institutional ownership | Estimates and positions-summary sources above | Families overlap; do not classify all forecasts or institutional ownership as absent from FMP. |

Two important non-equivalences: FMP's published PEG method uses P/E and EPS
growth, whereas FINVIZ describes forward earnings and a long-term growth basis.
Their published ROIC definitions also differ. Do not average, overwrite or alias
these vendor-defined observations into one generic value without an approved
comparability contract. This document records the difference, not a new formula.

Chart/candlestick pattern labels are **not promised API fields**: official
FINVIZ help marks both non-exportable. Screening by a pattern or signal is a
separate capability from receiving a per-stock exported metric. No scraping
fallback is proposed. FMP's educational mentions of indicators likewise do not
prove native endpoint availability.

## Official API feasibility and rights

The [FINVIZ API announcement, October 7](https://finviz.com/blog/our-upgraded-api-higher-limits-clearer-data-and-more-ways-to-connect/)
confirms screen-specific API/CSV workflows, custom columns and token access.
It reports Elite limits of **10 requests per rolling five seconds shared across
all API/export products**, with HTTP 429 and `Retry-After: 5`. These are published
vendor facts, not a configured application budget or proof of the owner's plan.
An eventual FINVIZ adapter needs its own bounded policy and shared quota owner;
do not alter accepted FMP immediate-429 behavior to implement it.

Anonymous [API and Exports](https://finviz.com/api-and-exports) access showed an
Elite marketing view. Official [API documentation](https://finviz.com/knowledge-base/market-data-research/api/api-documentation),
[authentication](https://finviz.com/knowledge-base/market-data-research/api/api-access-authentication)
and [usage limits](https://finviz.com/knowledge-base/market-data-research/api/usage-limits)
did not expose substantive schemas to the research fetcher. A published
`/api/v1/screener-export-csv` link is not an authenticated schema test; no data
endpoint was invoked. Do not copy undocumented third-party numeric column IDs.

Still needed: owner-confirmed plans, sanitized official API instructions and
sample response/headers, field selectors/types/nulls, authentication placement,
filters, pagination/completeness, timestamps and per-use rights. Do not supply
keys or token-bearing URLs in chat, issue text, fixtures or repository files.
FINVIZ's terms fetch failed; no positive rights conclusion is drawn from that.
FMP's [licensing notice](https://site.financialmodelingprep.com/pricing-plans)
explicitly distinguishes display/redistribution permission from API access.
Actual permitted storage, local display, retention, automated use and report
rights remain account/contract-specific and unverified for both vendors.

## Proposed implementation contract after verification

1. Maintain a versioned field registry: canonical metric, provider-native name,
   endpoint, native/derived status, definition/units, period, identity scope,
   observation and retrieval dates, plan/use rights, and availability state.
2. Prefer an approved native FMP field. Use an explicitly allowed FINVIZ field
   only for a verified coverage/semantic gap. Preserve provider-qualified metric
   IDs when definitions differ; do not choose favorable conflicting values.
3. Do not route FMP outage, quota exhaustion, unauthorized access, stale data or
   security-level nulls into FINVIZ by default. Any later fallback is a separate
   accepted contract, not the requested native-gap policy.
4. Keep endpoints/authentication/parsing inside adapters. Services depend on
   typed interfaces. Preserve current quotes/history, holdings and namespaces;
   absent FINVIZ leaves supported FMP workflows usable and gaps explicit.
5. Add offline fixtures for exact decimals, percent versus ratio, missing/zero,
   header drift, invalid identity/dates, stale/conflicting fields, quota handling,
   coverage decisions and non-equivalent fields. Add no implementation until
   the relevant field/API/rights and architecture decisions are accepted.

## Research and verification limits

Master and delegated `m9_analysis` used Exa against official documentation;
81 search results were requested (51 Master, 30 delegated), with repeated URLs
deduplicated in the synthesis. This count is search results, not unique verified
sources. No third-party wrapper was accepted as authoritative API documentation.
Direct fetches supplement the searches. Several guessed FMP documentation slugs
returned 404; positive mappings above use working pages, not those guesses.
Negative catalog searches are scoped evidence, not an exhaustive vendor warranty.

No live provider request, subscription, account change, runtime edit or financial
calculation was made. No current stock values are test fixtures. Source precedence
is now selected; preset/ranking, daily selection, jobs/storage, exact research API
and entitlement remain unresolved as listed in [the decision brief](m9-decisions.md).

Independent source/document review by `m9_analysis` passed with no actionable
finding. Final documentation-update checks: staged repository hygiene **9 passed
in 15.38s**; Ruff, configured mypy, pip check, relative links and diff checks
passed. The earlier planning revision passed the full **2795-test** suite and
hosted Foundation **38956584523**; these are prior-revision results, not a new
full-suite run for this documentation-only addition. No runtime tests were added.
