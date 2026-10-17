# ADR-0015: Scoped Finnhub Free upcoming-release EPS observations

## Status and authorization

Accepted for this bounded provider-observation task, 2026-10-16. The owner
explicitly requested implementation of EPS observation/comparison rules and a
narrow Finnhub adapter, emphasizing future estimated EPS, then selected
**“Upcoming release EPS estimate on Free (Recommended)”**. This authorizes the
reported-observation scope below for [issue #166](https://github.com/daniilnahl/Stock-Tracking-App/issues/166).
It does not accept the broader proposed M9 specification, unknown provider use
rights, a financial calculation or live activation. Existing accepted ADRs remain
authoritative. This is an additive capability, not a replacement of FMP services.

## Selected source and exact meaning

Use Finnhub `GET /api/v1/calendar/earnings` for one explicit provider symbol and
inclusive caller-supplied release-date range. The documentation identifies its
EPS as non-GAAP and associates estimates with earnings releases. This is not the
Premium `/stock/eps-estimate` consensus series, nor the historical estimate in
`/stock/earnings`. Those endpoints are outside this issue.

Sources checked 2026-10-16: [rendered calendar documentation](https://finnhub.io/docs/api/earnings-calendar),
[EPS estimates](https://finnhub.io/docs/api/company-eps-estimates),
[authentication/limits](https://finnhub.io/docs/api), [pricing](https://finnhub.io/pricing).
Free account access and allowed use have not been live-tested; no account/key
is assumed. The free calendar's published history window does not guarantee an
arbitrary future horizon or all-security completeness.

## Stable interface and observation contract

Add an independent `UpcomingEpsProvider` protocol with:

```python
get_upcoming_eps(symbol: str, *, start: date, end: date,
                 analysis_date: date) -> tuple[UpcomingEpsEstimate, ...]
```

The symbol is an explicit Finnhub provider symbol, not proof of globally unique
security identity or a mapping to an existing holding. Do not modify `Stock`,
mandatory `MarketDataProvider` methods, saved rows or their equality semantics.

`UpcomingEpsEstimate` is frozen and contains symbol, fiscal year and quarter,
release date, nullable release-session code (`bmo`, `amc`, `dmh`), nullable signed
finite Decimal estimate and aware UTC retrieval time. Its source is explicitly
Finnhub calendar, accounting basis non-GAAP, units currency-per-share. Currency,
basic/diluted share basis, publication/vintage timestamp and fiscal period end
remain **unknown**; they must not be inferred from ticker, release date or the
retrieval clock. No provider URL with credentials is stored in an observation.

The caller supplies `analysis_date` in the same date-only calendar convention
as the requested release dates; this adapter does not invent market timezone,
session-calendar or intraday publication policy. Require `analysis_date < start
<= end`. Retrieval time records receipt, not historical data availability.
Reject requests with an analysis date other than the caller's intended research
date at application integration; the isolated adapter does not prove a historical
as-of snapshot. No backtesting or forecast accuracy claim is authorized.

Validate every source row before selection: exact requested symbol, real ISO
date inside the requested range, fiscal quarter 1–4, fiscal year 1–9999,
explicit numeric-or-null `epsActual` and `epsEstimate`. Numeric booleans, strings,
nonfinite numbers, malformed JSON and inconsistent rows fail safely. Extra
unneeded revenue fields may be ignored. Unknown/absent session becomes None;
unrecognized nonblank session codes are malformed. Fiscal year need not equal
release calendar year. Do not manufacture a fiscal period-end date.

Only rows with `epsActual is None` qualify as upcoming observations. Preserve
an explicit null estimate as unavailable; zero and negative estimates are valid.
An existing actual excludes a row even when its release date is future. Missing
actual is malformed, not proof that earnings have not been released. Empty
successful results mean no observations returned, not an invalid symbol or
complete market coverage. Duplicate fiscal year/quarter rows fail as ambiguous;
never pick a favorable revision. Return increasing release date/year/quarter order.

## Comparison and financial boundaries

Observation matching may inspect source symbol, fiscal year/quarter, release
date and field identity. It must not imply numeric comparability. These records
cannot establish cross-provider equivalence or authorize EPS subtraction,
ratios, growth, annual/TTM sums, surprise calculations, PEG or ranking: currency,
share basis and forecast vintage are unknown. Displaying labeled observations
side by side is distinct from calculating a comparison. Identical values do not
prove compatible accounting definitions. No comparison arithmetic is added.

Known-value fixtures use synthetic estimates `1.250000000000000001`, `0`,
`-0.25` and null and assert exact preservation without rounding. A fixed future
release after an explicit analysis date is distinct from today/past input;
actual-present results are not future forecasts. These examples do not prescribe
thresholds or provider data values. See the financial specification's EPS section.

## Transport, failure and activation boundaries

Use injected `HttpTransport` and UTC clock. A separate Finnhub transport permits
only HTTPS `finnhub.io`, default/443 port and the exact calendar path; refuse
redirects and URL credentials/fragments. Keep the FMP transport's allowlist intact.
Authenticate with `X-Finnhub-Token`, never query-string credentials. Hide the
credential from repr, serialization, exceptions and logs. Construction/import
does no network, environment or filesystem access.

Each request makes at most one HTTP call. Timeout, maximum response bytes and
maximum rows are explicit validated constructor parameters, without a new
production default. Bound native response reads and parsed row counts. No retry,
cache, cross-request quota policy, fallback or background work is introduced.
HTTP 401 means authentication failure, 402/403 access failure, 429 rate limit,
408 timeout, 5xx unavailable, other non-success request failure. A JSON error
object returned with HTTP 200 is a malformed/unusable response, never data or
evidence of an invalid ticker. Retain only existing safe error categories and
sanitized diagnostics; no raw body, URL or infrastructure exception chain.

No default factory, API/UI/CLI route, persistence, scheduler, premium adapter,
SDK/dependency, account creation or live probe is part of this issue. An explicit
injected credential is supplied by a future approved configuration/composition
boundary; this class does not discover it. Live application wiring still needs
verified access/use, identity and date-convention contracts and quota ownership.
Tests inject synthetic credentials and network fixtures only.

## Verification and consequences

Add meaningful offline parser/model/transport tests, known-value preservation,
future/historical separation, errors and secret non-disclosure; validate package
inclusion and unchanged FMP behavior. Follow TESTING.md's full canonical checks,
independent review and owner merge; do not activate a connector from passing CI.
The result is an opt-in backend adapter ready for later composition, not a live
screen, full forward consensus feed or completed M9 milestone.
