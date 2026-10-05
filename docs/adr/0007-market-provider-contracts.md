# ADR-0007: M2 market provider contracts and reliability policy

## Status

**Accepted.** On **2026-10-04**, the repository owner stated **"I approve A"**
in the Codex milestone chat, accepting the complete proposal at exact commit
`cf909dfc6c9766c440b1aeaf408d10c1f112e6a4` and retaining the DATA-006
definitive network unknown-instrument classification exit blocker. The Master
Agent faithfully recorded that user approval in the
[PR #57 acceptance record](https://github.com/daniilnahl/Stock-Tracking-App/pull/57#issuecomment-5982448860);
the GitHub comment is the Master's record of the human chat instruction, not
an independently authored human GitHub approval. This decision is for
[#47](https://github.com/daniilnahl/Stock-Tracking-App/issues/47) in
[M2 — Market Data Layer](https://github.com/daniilnahl/Stock-Tracking-App/milestone/3).
The exact reviewed contracts and reliability values below are accepted; their
original proposal wording documents how the decision was presented. Acceptance
does not implement runtime behavior, satisfy unresolved implementation dependencies,
close the DATA-006 evidence gate, authorize agent merges or change other milestones.

Implements the contract planning for ARCH-001/002/003/006, DATA-001/002/006/007,
DATA-009–011, SEC-002/005, ERR-001–003 and PERF-001; references DATA-004/005/008
and PERF-002 for boundaries. The approved [SRS](../../SRS.md) §§5, 10–11, 18,
23 and 25, accepted [ADR-0005](0005-canonical-python-dependencies.md), accepted
[ADR-0006](0006-domain-contracts.md), [testing policy](../TESTING.md) and
[financial definitions](../FINANCIAL_CALCULATIONS.md) remain authoritative.
This document changes neither SRS nor runtime behavior.

## Context and current behavior

**Subsequent decision:** [ADR-0008](0008-scoped-ticker-rejection.md) supersedes
the successful no-match/local-only invalidity provisions and corresponding
DATA-006 evidence gate for the approved scoped product rule. The original
accepted proposal below is preserved as historical decision content; all other
contracts remain unchanged.

Baseline main is `788d3c4119e9ebb196256e9355f24ce8b31dc037`. Domain models are
isolated. Three legacy FMP calls live in
`src/stock_tracker/compatibility/stock_operations.py`: profile, quote-short and
stock-price-change. `utils/utility_module.py` constructs search-ticker requests
and implements urllib JSON transport. All four use `/api/v3` and URL credentials.
Transport makes one request with implicit socket timeout, no backoff and no
quote/history cache; HTTP, URL, JSON and unexpected failures become `None` with
sanitized logs. Ticker validation trusts indefinite CSV positives, restricts
search to NASDAQ, accepts any result except `[]`, and writes even failed or
unrelated results. A missing CSV prevents validation.

Profile/quote failures print and overwrite fields with `N/A`. Period-summary
failures can crash or partially publish fields. Both CLIs validate then fetch
profile and summaries; Watch_list refresh fetches profile then summaries.
At that baseline no configured reliability values resolved SRS §11. The values
in this ADR now have the explicit acceptance recorded above; runtime application
remains dependent implementation work, not inferred production defaults.

## Accepted package and dependency direction

Add `stock_tracker.providers` with `models.py`, `protocols.py`, `transport.py`
and `fmp.py`; add application errors in `stock_tracker.exceptions`. Keep root
modules, compatibility package, pip/setuptools pins and Python 3.11/3.12.
Use standard-library urllib with an SSL context using the existing certifi
bundle. No new HTTP dependency, domain change or package relocation is needed.
Explicit setuptools package enumeration and offline wheel tests must include
the new package. Configured mypy remains `config.py`; expanding checker scope
requires its own readiness evidence, rather than checker suppressions.

Domain imports none of these modules. Compatibility and CLI depend on the
provider protocol and typed models, never endpoint URLs, JSON keys or HTTP
statuses. FMP-specific parsing, credentials and transport stay in the adapter.
Existing facade delegation remains monkeypatchable. M6/M7 own a broader shared
application service API; this proposal does not create one prematurely.

## Exact typed contracts

All models below are frozen dataclasses with the listed fields, no implicit
defaults and no credentials, HTTP handles or formatted display strings.
Numeric fields use finite Decimal; prices and market cap are nonnegative;
summary percentages may be negative. Zero is available data. Bool is never
numeric data. Optional values mean unavailable metadata or data, never zero.

```python
@dataclass(frozen=True)
class InstrumentIdentity:
    symbol: str
    exchange: str | None
    name: str | None
    currency: str | None

@dataclass(frozen=True)
class Quote:
    symbol: str
    price: Decimal | None
    exchange: str | None
    currency: str | None
    as_of: datetime | None
    retrieved_at: datetime

@dataclass(frozen=True)
class CompanyProfile:
    symbol: str
    name: str
    exchange: str | None
    currency: str | None
    sector: str | None
    country: str | None
    price: Decimal | None
    market_cap: Decimal | None
    as_of: datetime | None
    retrieved_at: datetime

@dataclass(frozen=True)
class PeriodChanges:
    symbol: str
    day_1: Decimal | None
    day_5: Decimal | None
    month_1: Decimal | None
    month_3: Decimal | None
    month_6: Decimal | None
    year_1: Decimal | None
    year_3: Decimal | None
    year_5: Decimal | None
    as_of: datetime | None
    retrieved_at: datetime

@dataclass(frozen=True)
class PriceBar:
    symbol: str
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adjusted_close: Decimal | None
    volume: int | None

class MarketDataProvider(Protocol):
    def resolve_symbol(self, symbol: str) -> InstrumentIdentity: ...
    def get_quote(self, symbol: str) -> Quote: ...
    def get_company_profile(self, symbol: str) -> CompanyProfile: ...
    def get_period_changes(self, symbol: str) -> PeriodChanges: ...

class HistoricalMarketDataProvider(Protocol):
    def get_price_history(
        self, symbol: str, start: date, end: date,
    ) -> list[PriceBar]: ...
```

Constructors validate their own contract rather than trusting adapter callers:
symbol is a nonblank uppercase string without surrounding/internal whitespace,
control characters or comma; no constructor normalizes it. Required name is a
nonblank string without surrounding whitespace. Optional text is None or a
nonblank string without surrounding whitespace; constructors reject blanks while
the adapter maps permitted missing text to None. No exchange alias or currency
whitelist is inferred. Numeric fields require actual finite Decimal objects and
the sign constraints above; int/float/string/bool constructor inputs fail.
Datetime fields require aware zero-UTC-offset datetime values; other offsets
fail rather than normalize. The adapter converts timestamps before construction.
retrieved_at cannot be None. PriceBar.date requires date excluding datetime;
volume is None or nonnegative int excluding bool. M2 selects no cross-field OHLC,
adjustment, range or freshness invariant; M4 must approve those before retrieval.
Invalid constructor input raises ProviderResponseError with fixed field-specific
safe messages, separate from DomainValidationError. Construction does no IO,
environment or clock access.

The separate history capability makes DATA-002's equivalent interface explicit
without falsely advertising M2 retrieval. M2 defines PriceBar and that protocol;
the M2 FMP adapter implements MarketDataProvider only. M4 implements history,
date-range ordering, missing sessions, raw/adjusted semantics, cache and charts
after its own accepted contract. A PriceBar date is an exchange trading-session
label, not midnight UTC; volume is a nonnegative integer when present. The fields
do not select an adjustment methodology or authorize synthetic history.

`FMPMarketDataProvider` takes keyword-only `api_key: str`,
`transport: HttpTransport`, `policy: ProviderPolicy`, `clock: Callable[[], datetime]`,
`monotonic: Callable[[], float]`, `sleep: Callable[[float], None]` and
`jitter: Callable[[float], float]`. The jitter callable returns a value in
`[0, upper_bound]`. Required injections have no implicit production policy.
The external composition factory supplies approved policy and real clocks;
tests supply fakes. All clock values are aware UTC datetimes. Credentials are
validated by existing `require_api_key`, private, excluded from repr and never
serialized. `stock_tracker.providers.factory.create_market_data_provider(
api_key: str | None) -> MarketDataProvider` is the external monkeypatchable
composition boundary. It validates the supplied key, supplies approved policy
and real injections, and does no request on construction. Current configuration
and facade restoration retain `FMP_API_KEY`/`MY_API_KEY` precedence. Factories
never read saved keys, retain global clients or change domain imports.

```python
@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes

class HttpTransport(Protocol):
    def get(
        self, url: str, *, headers: Mapping[str, str], timeout_seconds: float,
    ) -> HttpResponse: ...
```

HttpResponse repr includes status only, excluding headers and body, which may
contain provider-echoed input. Status is an integer HTTP code excluding bool,
headers a string-to-string mapping and body bytes. The adapter matches headers
case-insensitively. The snapshot retains no live response handle.

Transport normalizes HTTPError into status/headers/body, closes responses, and
reports connection/timeout/TLS failures through internal safe typed errors;
the adapter maps these to application errors. Request URLs have a fixed HTTPS
host/base and `urlencode` parameters. Credentials use the documented `apikey`
header, never the URL. Redirects are rejected so headers cannot reach another
host. Transport construction is IO-free; requests happen only on method calls.
Bodies, headers, URLs and exception causes are never logged or rendered.

## Identity, missing data, currency and time

- Normalize request symbols at the external provider boundary with strip and
  uppercase. Reject nonstrings, blank values, internal whitespace/control
  characters and comma-separated batch requests with InvalidTickerError before
  IO. Preserve punctuation and do not invent exchange aliases. Domain's accepted
  validation/equality rules remain unchanged.
- Resolve within the existing NASDAQ scope, using exact normalized symbol and
  exact `NASDAQ` exchange. A unique matching identity succeeds; malformed rows,
  missing required symbol/exchange or multiple exact rows fail explicitly.
  Search name/currency are optional under the text rules below. Unrelated
  search hits never succeed. Scope is an application limitation, not proof that
  a symbol is globally invalid. Broader exchange support is an alternative
  requiring separate approval, not a silent expansion here.
- Propose search `limit=100`. A successful result without an exact scoped match,
  whether empty, unrelated, exchange-mismatched or at the full limit, raises
  InstrumentLookupInconclusiveError. FMP documentation promises neither complete
  lookup nor exact-match ordering, so no result count proves global nonexistence.
  Reserve InvalidTickerError for local invalid input. Network-based definitive
  unknown-instrument classification requires verified provider evidence and a
  further accepted contract; it is not fabricated from search/HTTP failures.
  An alternative is owner-approved interpretation of a no-match as scoped unknown,
  but that assumption and its false-negative risk require explicit approval.
- Quote/profile/summary retrieval never performs a hidden validation request.
  An empty successful payload means MarketDataUnavailableError, not invalid
  ticker. HTTP 404 does not prove an instrument invalid. resolve_symbol is the
  only network identity lookup; inconclusive lookup remains distinguishable from
  unavailable data for an identity that was already resolved.
- Retrieval arrays must contain exactly one matching object. Reject wrong
  symbol, extra rows, wrong top-level types and required missing keys. Unknown
  extra keys are ignored. Required keys are symbol and price for Quote; symbol,
  companyName, price and marketCap for CompanyProfile; symbol for PeriodChanges.
  Required symbol/name strings are nonblank. Optional text omitted/null/blank
  becomes None; nonstring text is malformed. A non-null price or market cap
  of wrong type, negative or nonfinite is malformed, never missing.
- JSON numbers are parsed with Decimal for fractional numbers and exact ints;
  reject nonstandard NaN/Infinity. Numeric strings, bools and decorated values
  are malformed. Explicit null price/market cap maps to None. Missing/null
  period fields map to None independently; a present malformed period fails
  the entire response before publication. All eight unavailable periods are
  a valid missing-data result, not fabricated zero returns.
- PeriodChanges contains provider-reported percentage points, preserving the
  existing display meaning (e.g. Decimal("12.5") displays 12.5%). This is external
  summary metadata, not a new domain return metric or historical price series.
  Domain return ratios and FC-003 remain unchanged. No dividend, split, FX or
  return methodology is inferred.
- `retrieved_at` is injected client receipt time in UTC, never a market timestamp.
  Quote `timestamp`, when present, is proposed as nonnegative integral Unix
  seconds converted to aware UTC; malformed values fail. Missing/null becomes
  `as_of=None`. The observed sample supports seconds, but endpoint marketing
  alone is not a unit guarantee. Profile and summaries expose no verified market
  timestamp: `as_of=None`; do not fabricate one or label client time as realtime.
- Currency is provider text when available, else None. The documented full
  quote sample omits currency: do not add a hidden profile request or assume USD.
  A separate profile may supply currency to the facade; missing/conflicting
  currency never authorizes FX or mixed-currency aggregation (DATA-008/FC-010).
  Quote price means per-share in the provider's currency; unknown currency
  remains explicit and cannot certify any portfolio aggregation.

## Exact application error contract

All names below are public classes in `stock_tracker.exceptions` and subclass
`StockTrackerError(Exception)` directly, except where specified. They have safe
fixed messages, with no supplied payload, URL, header, key or raw cause in their
string/repr. No provider failure becomes a boolean validation result.

| Error | Classification and behavior |
| --- | --- |
| InvalidTickerError | Local invalid symbol input only; never transport failure or inferred network no-match |
| MarketDataUnavailableError | Successful empty retrieval for the requested symbol |
| InstrumentLookupInconclusiveError (MarketDataUnavailableError) | Successful search with no exact scoped match; fixed message identifies supported NASDAQ lookup, not global invalidity |
| ProviderUnavailableError | Nonretryable connection/TLS failure, exhausted transient connection/status failure, or unsupported endpoint/status |
| ProviderTimeoutError (ProviderUnavailableError) | Timeout or retry admission budget exhausted; distinct catchable type |
| RateLimitError | HTTP 429, immediately; never invalid symbol; optional safe retry_after_seconds diagnostic |
| ProviderAuthenticationError | HTTP 401; current key cannot authorize request |
| ProviderAccessError | HTTP 402/403; access/entitlement denied; never suggest a symbol is invalid |
| ProviderRequestError | HTTP 400/422; reject request without retry, not unknown ticker |
| ProviderResponseError | Invalid JSON/UTF-8, wrong shape/identity/type, invalid timestamp/numeric field, or unrecognized error object in a 200 response |

Remaining HTTP 4xx/3xx map to ProviderUnavailableError and are nonretryable;
remaining 5xx are nonretryable unless listed below. A 200 error object is
ProviderResponseError, not success or invalid ticker; do not guess authorization
from free-text bodies. ConfigurationError remains the existing credential
configuration type. Unexpected programming errors propagate; no catch-all
converts them to None. Safe exception translations use `raise ... from None`.
Adapter diagnostics use logging with operation/category/status/attempt only;
no payloads, headers, URLs, transport repr or traceback containing credentials.
Error constructors accept no arbitrary user/provider message. All take no
arguments except `RateLimitError(*, retry_after_seconds: float | None = None)`
(finite/nonnegative, excluded from fixed message) and
`ProviderResponseError(*, field: str | None = None)`. Its optional field argument
is validated against the model field names and consumed FMP keys listed here;
unknown fields cannot carry arbitrary input into error messages.

## Accepted reliability values

`ProviderPolicy` is a frozen dataclass with exactly the following field names
and types. Production construction must explicitly supply approved values;
there are no automatic environment overrides or fallback policies in M2.

| Field | Approved value | Meaning |
| --- | --- | --- |
| timeout_seconds: float | 10.0 | urllib blocking socket-operation timeout; not a total-request wall-time guarantee |
| max_attempts: int | 2 | Total attempts including the first, hence at most one retry |
| retryable_statuses: frozenset[int] | {408, 500, 502, 503, 504} | Only these HTTP statuses retry |
| backoff_base_seconds: float | 0.5 | Exponential upper bound base |
| backoff_cap_seconds: float | 2.0 | Delay upper bound cap |
| retry_budget_seconds: float | 30.0 | Monotonic admission window from first request; never launch retry after budget |
| retry_on_429: bool | False | Fail immediately; no automatic 429 sleep/retry |
| quote_cache_ttl_seconds: float | 0.0 | Cache disabled in M2 |
| history_cache_ttl_seconds: float | 0.0 | Cache disabled; future implementation M4 |
| stale_cache_fallback: bool | False | Never substitute stale data for a failed request |

Validate finite positive timeout/budget, nonnegative finite backoff/TTLs,
max_attempts at least 1 excluding bool, cap >= base and a set of valid HTTP
statuses. This reviewed profile admits only the listed statuses and 429=False;
changing production values requires explicit approval and updated evidence.
Zero TTL means no cache, not an infinite lifetime. M2 implements no TTL cache.

Retry only idempotent GETs. Retry socket timeout, connection reset and temporary
DNS failure (`EAI_AGAIN`); do not retry certificate failures, permanent DNS,
authentication/access errors, invalid symbols, malformed data or programming
errors. Retry delay after failed attempt n (one-based) is full jitter over
`[0, min(cap, base * 2 ** (n - 1))]`. Inject sleep/jitter/monotonic for deterministic
tests. Check remaining admission window before sleeping and before issuing the
retry; if exhausted, raise ProviderTimeoutError. Pass min(configured timeout,
remaining budget) into a retry. No unbounded loop or layer can add retries.

The proposed profile permits at most two network attempts and one delay of at
most 0.5 seconds. A nominal two-timeout path is 20.5 seconds, **not a hard wall-time
ceiling**: urllib socket timeouts do not bound DNS or an entire trickling body.
The 30-second value bounds retry admission, not interruption of an in-flight
request. Hard request cancellation would require a separately justified
transport contract; do not claim it here.

For 429, expose only a safe optional retry-delay diagnostic parsed from
Retry-After (integer seconds or HTTP date using injected UTC clock); ignore
malformed/overflowing values and clamp past dates to zero. Do not sleep, retry
or persist it under this profile.
No negative/invalid-symbol cache is introduced.

Alternatives: one attempt/no backoff minimizes quota consumption but loses
transient recovery; more attempts increase quota and interactive delay. Retaining
implicit timeout preserves legacy behavior but gives users no bounded socket
wait. Respecting Retry-After through automatic 429 retries needs an approved
maximum delay and total budget; fail-fast keeps that decision visible. Nonzero
quote/history TTLs reduce quota use but require freshness/storage/invalidation
rules; defer implementation to M4. Stale fallback may hide outages and requires
an explicit freshness indicator; disabled is the conservative proposal.

## Endpoint decision and primary-source evidence

Propose Stable endpoints only, with no automatic legacy fallback. This avoids
duplicated requests and mixed schemas; changing endpoint family requires review.
The existing `/api/v3` integration remains the unchanged baseline until acceptance.
Public documentation was inspected on **2026-10-04**, without credentials or
authenticated API calls. Endpoint pages establish routes; response fields below
were inspected in the official documentation index's rendered search snapshot.
Endpoint descriptions alone do not establish every missing/error/unit behavior.

| Operation | Proposed route; consumed FMP keys | Primary source |
| --- | --- | --- |
| resolve_symbol | `/stable/search-symbol`, query/limit/exchange; symbol, exchange, name, currency | [Symbol search](https://site.financialmodelingprep.com/developer/docs/stable/search-symbol) |
| get_quote | `/stable/quote`, symbol; symbol, price, exchange, timestamp; optional currency if supplied | [Full quote](https://site.financialmodelingprep.com/developer/docs/stable/quote) |
| get_company_profile | `/stable/profile`, symbol; symbol, companyName, price, marketCap, exchange, currency, sector, country | [Profile](https://site.financialmodelingprep.com/developer/docs/stable/profile-symbol) |
| get_period_changes | `/stable/stock-price-change`, symbol; symbol, 1D, 5D, 1M, 3M, 6M, 1Y, 3Y, 5Y | [Price change](https://site.financialmodelingprep.com/developer/docs/stable/quote-change) |

The [official documentation index](https://site.financialmodelingprep.com/developer/docs)
documents header authorization and sample schemas. Stable profile uses
`marketCap`; current legacy source expects `mktCap`. Stable query parameters
replace path symbols. Full quote is proposed instead of quote-short because the
short sample lacks market time. Its sample contains timestamp but no currency.
Summary samples contain the eight consumed periods; other periods are ignored.
These differences belong inside the adapter, not in the facade.

[Quickstart](https://site.financialmodelingprep.com/developer/docs/quickstart)
documents 401, 429 and 500; the application's finer error policy is a proposal,
not an assertion that FMP guarantees every status/body combination. The
[legacy directory](https://site.financialmodelingprep.com/developer/docs/legacy-endpoints)
lists the old endpoint family. Retaining it is an alternative but would need
verified account access and separate parsers. Public samples are documentation,
not guarantees of entitlement, latency, complete lookup, live price freshness
or corporate-action methodology. No key or entitlement was tested. Implementation
must use small sanitized fixtures tagged with this date/schema and reconfirm
documentation if it changes; an unverifiable contract must be escalated.

## Compatibility and caller matrix

Accepting this ADR explicitly authorizes typed provider errors to replace the
legacy swallowed-None behavior at the external infrastructure boundary, plus
the endpoint switch and safe validation behavior below. Existing method names,
holding arithmetic, serialization and CLI command/file paths stay unchanged.

| Caller / surface | Proposed integration and preserved behavior |
| --- | --- |
| root stock.Stock constructor and API_KEY property | Preserve all positional/keyword arguments and runtime rebinding; add no required caller argument. Use a monkeypatchable external factory with current runtime key when a network method is invoked; no client/key enters serialized state |
| stock.Stock.get_stock_info | Delegate get_company_profile; map typed metadata and Decimal values to existing display fields; use profile price without extra get_quote; prepare complete candidate before mutation |
| stock.Stock.get_realtime_price | Delegate get_quote; missing price becomes unavailable snapshot; preserve pure domain recalculation |
| stock.Stock.get_price_over_time | Delegate get_period_changes; map all eight fields together and preserve external two-decimal summary formatting; None becomes N/A |
| utils.utility_module.check_ticker(symbol, API_KEY) | Keep two-argument boolean wrapper for legacy callers; True on exact scoped resolve, False only for locally invalid input; propagate inconclusive lookup and other explicit errors; no endpoint/schema logic |
| utils.utility_module.get_jsonparsed_data | Preserve generic legacy utility signature for existing callers/tests; no maintained application/provider flow uses its swallowed-None transport after M2 |
| menu_watchlist.py / daniils_stock_method.py add-stock | Existing uppercase prompt/key precheck and holding prompts; catch provider exceptions and print safe category messages with exit 1; locally invalid input retains normal invalid-input flow; do not add/save after failed validation/profile/summary |
| Both CLI refresh commands | Existing facade/Watch_list sequence; render provider errors and exit 1; do not save a partially failed refresh |
| watch_list.Watch_list.refresh_stocks | Preserve ordered Stock-like calls profile then summary then calculate_return; errors propagate to caller; no provider URL/schema dependency |
| test.py manual scratch | Preserve root Stock/configuration delivery; methods reach provider; never part of normal automated provider traffic |
| Packaging / tests | Include providers package and exceptions in exact wheel payload; offline installed imports, domain isolation, credential and legacy compatibility checks |

Both add/refresh callbacks preserve existing ConfigurationError prechecks; work
also catches safe ConfigurationError from a facade/factory (a restored runtime
binding can differ from the module key). Catch only those and StockTrackerError,
not programming exceptions. No exact lookup displays an inconclusive scoped
message rather than declaring a globally invalid ticker.

Before publishing profile/quote data, compare known returned exchange/currency
with known existing facade metadata. A conflict raises ProviderResponseError
and invalidates current price before any new identity/price is published;
do not recalculate a EUR price against known USD holdings or reinterpret holding
identity. Absent returned metadata keeps known metadata but supplies no proof of
currency agreement; preserve the existing caller's same-currency precondition,
with no USD inference, hidden request, FX or currency aggregation. Map nullable
name/exchange metadata at the facade to the accepted None/N/A boundary; these
sentinels never become domain instrument identifiers.

Missing metadata does not become a transport failure. On a failed profile/quote
attempt, invalidate current price to None (recompute unavailable return), keep
last known identity metadata and rethrow the safe error; do not fabricate fresh
metadata. Failed summary retrieval invalidates all period fields to N/A before
rethrowing, so an old value is not presented as refreshed. This is an explicit
proposed correction to ADR-0006's M1-only failure behavior; tests must be revised
deliberately, preserving credential and missing-versus-zero assertions. A refresh
can already update earlier entries before a later failure; this proposal does
not promise watchlist-wide rollback, but prevents saving failed refresh results.

PERF-001: an add operation issues at most one resolve, one profile and one
summary request (excluding the explicitly bounded transport retry); refresh
issues one profile and one summary per stock. No hidden quote/profile/validation
fetches, automatic endpoint fallbacks or persistence-lifetime client caches.
Read-only get_quote is one request. Injected fakes replace the external factory
in tests; root method monkeypatches and Stock-like doubles remain usable.

CSV positives are unverified hints, never evidence of current identity. Propose
that check_ticker does not read, append, rewrite, truncate or delete
`list_of_valid_tickers.csv`; perform exact provider resolution every operation.
Missing/malformed/unreadable CSV therefore cannot block validation. Keep read_file
and write_file legacy helpers available for their explicit callers, but remove
them from validation. No persistent positive/negative cache, user-state migration
or bulk revalidation occurs. Users' existing data remains intact. Alternative:
verified timestamped/exchange-qualified cache entries with approved TTL; that
requires a separate data contract and belongs with later cache/persistence work.

## Acceptance and implementation gate

The owner accepted exact commit `cf909dfc6c9766c440b1aeaf408d10c1f112e6a4`,
including model signatures, Stable family, NASDAQ/exact-search limitations,
typed failure propagation/invalidation, CSV bypass and every reliability value.
The status section links the faithful Master record of the human instruction.
The contract-acceptance gate is satisfied; implementation still follows the
[M2 dependency plan](../milestones/m2-plan.md), review and publication gates.
The DATA-006 definitive network unknown-instrument classification remains an
explicit #56 exit blocker until verified evidence or a further explicitly
accepted supported-scope interpretation resolves it. This acceptance does not
silently certify that incomplete search proves global nonexistence. M2 remains
incomplete; changes to these accepted decisions require further human approval.
