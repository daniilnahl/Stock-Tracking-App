# ADR-0010: M4 historical market data, cache and chart contracts

## Status and approval gate

**Proposed, 2026-10-07. Not accepted.** This documentation-only proposal is for
[issue #88](https://github.com/daniilnahl/Stock-Tracking-App/issues/88) in
[M4 — Historical Market Data](https://github.com/daniilnahl/Stock-Tracking-App/milestone/5).
The owner must explicitly accept the complete proposal at the exact reviewed
commit before dependent runtime work starts. A merged proposal PR, agent review,
green CI or an issue closure does not by itself establish acceptance. Record the
human instruction and exact commit in this status section only after it occurs.
Acceptance authorizes the bounded contracts below, not agent merges or live
credential/data operations. Until then, ADR-0007's history TTL remains **0.0**,
quote TTL remains **0.0**, and stale fallback remains **False**.

Governing sources: approved [SRS](../../SRS.md) §§5–6, 9–11, 18 and 23;
[AGENTS.md](../../AGENTS.md); [TESTING.md](../TESTING.md);
[financial definitions](../FINANCIAL_CALCULATIONS.md) FC-001–004, FC-060–062,
FC-100/101 and missing-data rules; accepted ADRs [0005](0005-canonical-python-dependencies.md),
[0006](0006-domain-contracts.md), [0007](0007-market-provider-contracts.md),
[0008](0008-scoped-ticker-rejection.md) and [0009](0009-persistence-contracts.md).
The [M4 plan](../milestones/m4-plan.md) owns atomic issue/dependency/agent/PR tracking.

Proposes contracts for ARCH-001–003/005/006, DATA-001–007/009–011,
FIN-001–003, PERF-001/002, ERR-001–003 and TEST-001–005. DATA-008 also constrains
currency labels. It changes no financial formula, Python version, dependency,
configured mypy scope or M3 schema.

## Context and boundaries

M2 supplies immutable numeric PriceBar and an independent
HistoricalMarketDataProvider protocol, but FMP has no history implementation.
ADR-0007 deliberately leaves OHLC/range/adjustment/freshness decisions for M4.
The current compatibility chart reconstructs nine prices from periodic return
summaries and current price, uses approximate calendar offsets and labels USD.
SRS DATA-003 and FC-060 prohibit that series as historical data.

Keep domain free of HTTP, environment, cache IO and plotting. FMP-specific
routes/keys remain in providers; cache storage uses a repository boundary outside
domain; compatibility orchestration depends on the historical protocol, and
presentation receives validated observations. Keep both root CLI modules,
existing commands, holdings and summary methods. Add no portfolio/benchmark,
daily/simple-return, dividend, risk, FX or transaction metric in M4.

## Public official evidence inspected 2026-10-07

Only unauthenticated public documentation was inspected. No API key, live API
request, account entitlement or real historical response was used. Schema
examples are documentation examples, not market facts or completeness evidence.

| Evidence | Observation and limit |
| --- | --- |
| [Official documentation index](https://site.financialmodelingprep.com/developer/docs) and its [rendered schema snapshot](https://site.financialmodelingprep.com/developer/docs?trk=article-ssr-frontend-pulse_little-text-block) | Header authorization supports `apikey`. Chart parameter tables list `symbol`, `from`, `to` and a 5,000-record limit. Rendered sample arrays expose the keys below. Static endpoint-page extraction does not show all dynamic tables. |
| [Unadjusted endpoint](https://site.financialmodelingprep.com/developer/docs/stable/historical-price-eod-non-split-adjusted) | Route `/stable/historical-price-eod/non-split-adjusted` is described as prices without split adjustment. |
| [Official historical API guide, updated March 31, 2026](https://site.financialmodelingprep.com/how-to/fmp-historical-price-apis-from-light-charts-to-dividendadjusted-analysis) | Explicitly describes this route's prices as literal past trading prices and demonstrates `symbol`, `date`, `adjOpen`, `adjHigh`, `adjLow`, `adjClose`, `volume`. The `adj` key prefix does not make this endpoint's values adjusted. |
| [Full endpoint](https://site.financialmodelingprep.com/developer/docs/stable/historical-price-eod-full) | Offers OHLCV; guide sample has `open/high/low/close`, without a distinct adjusted-close field. Its endpoint page alone does not establish a complete adjustment methodology. |
| [Dividend-adjusted endpoint](https://site.financialmodelingprep.com/developer/docs/stable/historical-price-eod-dividend-adjusted) | Advertises dividend adjustment. Neither marketing claims nor shared `adjClose` spelling approve product dividend-reinvestment semantics. |

These sources establish the proposed raw route and parser schema. They do not
guarantee boundary inclusivity, ascending order, complete sessions, historical
currency, correction latency, account access or a trustworthy split-only
adjusted close. The policies below are explicit application choices, not claims
of undocumented FMP guarantees. Implementation must reconfirm these sources and
use small synthetic fixtures tagged with route/schema and this inspection date.
If the route/schema can no longer be verified, stop that portion for review;
never silently switch endpoint families or reinterpret keys.

## Proposed Option A: raw OHLCV first

Implement FMPMarketDataProvider.get_price_history using exactly the Stable
non-split-adjusted route with `symbol`, `from=start.isoformat()` and
`to=end.isoformat()`. Authorize through the existing header transport; add no URL
credentials, hidden identity/profile/quote requests or fallback endpoint. One
history cache miss issues one logical GET, with ADR-0007's existing at-most-two
attempts. Preserve every existing retry/status/error policy and timeout meaning.

Map this endpoint's `adjOpen/adjHigh/adjLow/adjClose` into PriceBar's
**raw** `open/high/low/close`. Set `adjusted_close=None` on every returned bar.
Do not copy its `adjClose` into adjusted_close. A future verified adjusted series
requires separately accepted mapping/provenance and date alignment. Raw charts
may display split discontinuities and must say so. FC-061/100's split-aware
return use remains a future calculation concern; no return is computed here.
Never label raw price movement total return or dividend reinvestment.

Retain the exact public interface and model fields accepted in ADR-0007:

```python
class HistoricalMarketDataProvider(Protocol):
    def get_price_history(self, symbol: str, start: date, end: date) -> list[PriceBar]: ...

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
```

M4 strengthens PriceBar constructor validation to `low <= open <= high` and
`low <= close <= high`, in addition to existing finite nonnegative Decimal and
date/volume validation. No comparison between raw and adjusted_close is valid
across adjustment bases. Existing legal zero bars stay legal. Construction
continues to perform no IO, normalization or clock access.

### Input, response and session rules

- Normalize/reject symbols exactly as ADR-0007; history does no NASDAQ search.
  Existing identity lookup still uses ADR-0008. Empty history never proves an
  instrument invalid and never removes holdings.
- `start` and `end` must be actual date objects excluding datetime; both required
  at provider boundary, `start <= end`, and `(end - start).days + 1 <= 3660`.
  Neither may exceed the injected UTC clock's prior calendar date. Same-day
  historical ranges are allowed. Reject inputs before cache IO or HTTP.
- The public result interval is inclusive `[start, end]`. Parse every row before
  filtering valid outside-range rows; then return in-range rows ascending by
  session date. Filtering enforces application bounds without assuming FMP's
  undocumented boundary behavior. It cannot manufacture a missing boundary.
- Require a JSON array of objects. Each row requires exact normalized `symbol`,
  strict round-trippable `YYYY-MM-DD` date, and all four numeric `adj*` price keys.
  Null/missing OHLC, bool/string/nonfinite/negative numbers, malformed dates,
  wrong identity or impossible OHLC fail the whole response. Unknown extra keys
  are ignored. Reject duplicate dates anywhere in the response, even identical
  rows or rows outside the requested interval. Never repair or deduplicate.
- Parse numbers using the existing exact Decimal JSON path. Volume omitted/null
  maps to None; otherwise require a nonnegative integral numeric value excluding
  bool, at most **9223372036854775807**, and reject fractional volume. Compare
  the Decimal against this bound before converting exactly to int: a compact
  exponent such as `1e100000000` must not allocate a giant integer. This is a
  proposed adapter/cache resource limit, not a market-volume claim or
  a change to the general PriceBar model. Oversized volume raises
  ProviderResponseError(field="volume"). Zero is present. An alternative is a
  separately bounded larger integer representation; unbounded conversion is
  unsuitable for remote input and would need a different accepted resource policy.
- Cap decoded response at 5,000 rows; the allowed range has at most 3,660 distinct
  calendar dates, reducing documented truncation risk without proving completeness.
  Do not paginate, combine request ranges or add automatic retries above M2.
- Valid empty arrays or no in-range observations raise MarketDataUnavailableError.
  A malformed row causes ProviderResponseError before empty-result classification.
  Nonempty sparse history is usable observed data, with no completeness claim.
  Display requested range, observed first/last date and observation count.
- Dates mean provider exchange trading-session labels, not midnight UTC events.
  Do not fabricate weekends, holidays, missing closes, interpolation or a prior
  boundary observation outside the requested range. No calendar dependency is
  added; a sparse response cannot distinguish a closure from a missing session.

Add no-argument HistoryRangeError(StockTrackerError), fixed message
`Historical date range is invalid.` for invalid typed/date/range inputs; local
symbol failures retain InvalidTickerError. Add no-argument HistoryCacheError
(StockTrackerError), fixed message `Historical cache operation failed.` for cache
filesystem/validation failures. Existing provider error mapping is unchanged.
Extend ProviderResponseError's safe field allowlist only for consumed `adjOpen`,
`adjHigh`, `adjLow`, `adjClose` keys; retain fixed diagnostics without payloads.
Programming exceptions propagate; anticipated errors use safe translation from
None. No error object, body, credentials, URL or path is logged/rendered.

## Proposed persistent cache policy

Option A uses one bounded **neutral JSON sidecar** at
`Path.cwd() / 'stock_tracker.history-cache.json'`, resolved once at composition.
It is disposable provider data, separate from `stock_tracker.sqlite3`, watchlist
state, neutral transfer and backups. Read/write through HistoryCacheRepository
in the persistence boundary; a provider-capability decorator owns cache lookup
and delegates misses to HistoricalMarketDataProvider. Domain and presentation
never open it. Constructors/factories do no IO. Tests inject explicit tmp paths.
Fresh adapters and separate CLI invocations in the same working directory reuse
the sidecar; an instance-only cache would not reduce this application's quota.

Exact new internal frozen records: HistoryCacheKey(provider: str,
mapping_version: str, symbol: str, start: date, end: date, price_basis: str) and
HistoryCacheEntry(key: HistoryCacheKey, retrieved_at: datetime,
bars: tuple[PriceBar, ...]). Constants are the literals below, dates/symbol obey
history validation, retrieved_at requires aware zero-UTC-offset time, bars are
nonempty ascending unique in-range observations. `raw-eod-v1` entries require
every bar's adjusted_close to be None; otherwise reject the entry before storage
or publication. Volume also obeys the adapter's signed-64-bit resource bound.
Constructors perform no IO.
HistoryCacheRepository exposes `get(key: HistoryCacheKey) -> HistoryCacheEntry | None`
and `put(entry: HistoryCacheEntry) -> None`; concrete JsonHistoryCacheRepository
takes explicit `path: Path` and `clock: Callable[[], datetime]`. Repository get
returns stored validated data; decorator owns freshness/admission. Repository put
owns bounded eviction using injected clock and writes a complete candidate.
This cache interface does not alter PortfolioRepository/WatchlistRepository.

After owner acceptance only, set production history TTL to **3600.0 seconds**;
quote TTL stays **0.0**, stale fallback stays **False**, no environment overrides.
Use the existing ProviderPolicy history TTL field, supplied explicitly by the
history composition factory. Current-data factory retains its M2 policy.
The TTL is an application freshness tolerance, not FMP's correction/finality SLA.

Exact cache behavior:

- Key: provider `fmp`, schema/mapping version `raw-eod-v1`, normalized symbol,
  exact start and end ISO dates, and price basis `raw`. No range stitching or
  superset reuse. No keys, key hashes, request URLs, headers, portfolio records,
  negative lookup results or summaries are stored. Cached data do not certify
  current account entitlement; credentials are still validated at construction.
  This symbol-only key cannot distinguish exchange-qualified instruments.
  Application graph use is therefore scoped to an already known exact NASDAQ
  identity under the facade gate below. A hit does not verify exchange identity;
  lower-level history capability is not a universal exchange resolver.
- Value: original aware-UTC `retrieved_at` from provider receipt clock and full
  validated ordered bars. Fresh iff `0 <= now - retrieved_at < TTL`; exact expiry
  or a backwards clock is a miss. TTL zero bypasses all cache IO. A hit does not
  update retrieved_at. Decorator returns a fresh list; frozen bars remain numeric.
- To retain receipt time without changing the public list-returning protocol,
  define an internal FMP history result containing bars and retrieved_at for the
  decorator, with public get_price_history projecting a fresh list. Do not stamp
  cache insertion time as market time. Independent fakes can supply this internal
  receipt metadata through an injected loader used by decorator tests. Exact
  internal result is frozen HistoryObservation(bars: tuple[PriceBar, ...],
  retrieved_at: datetime): require aware zero-UTC-offset retrieved_at, a nonempty
  tuple of valid PriceBars, strictly ascending unique dates, adjusted_close=None
  and the volume resource bound. It has no key and cannot independently validate
  request identity/range; FMP loader and decorator validate every bar's symbol
  against the normalized request and date against its inclusive start/end before
  publishing or caching. A mismatch raises ProviderResponseError. Injected loader
  signature is `(symbol: str, start: date, end: date) -> HistoryObservation`.
  FMP's private loader obtains _request_json's receipt time. Decorator implements
  only HistoricalMarketDataProvider, validating input before repository access.
- Cache only successful nonempty fully validated results after the request.
  Do not cache emptiness, malformed rows, invalid input, HTTP failures or partial
  parse state. Never return expired data after an upstream failure. Existing
  cache data remains unchanged on request failure; the safe provider error wins.
- File format has exactly `format='stock-tracker-history-cache'`, integer
  `version=1` excluding bool, and `entries` array. Each entry has exactly `key`,
  `retrieved_at`, `bars`; `key` is an object with exactly `provider`,
  `mapping_version`, `symbol`, `start`, `end`, `price_basis`. Their values are
  respectively `fmp`, `raw-eod-v1`, the normalized symbol, strict ISO start/end
  dates and `raw`. Each bar has exactly `symbol`, `date`, `open`, `high`, `low`,
  `close`, `adjusted_close`, `volume`; adjusted_close is always JSON null for
  this mapping, volume is null or an integer within the resource bound.
  OHLC are Decimal strings matching ASCII grammar
  `[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?`, then validated
  finite/nonnegative without arithmetic or quantization. Whitespace, underscores,
  decorated text and nonstandard constants are invalid. Encoder uses str(Decimal).
  Dates use exact `YYYY-MM-DD`. retrieved_at uses canonical
  `YYYY-MM-DDTHH:MM:SS.ffffff+00:00` with six fractional digits: write aware UTC
  datetimes with microsecond precision, accept only that spelling on read. `Z`,
  other offsets, naive timestamps and alternate precision are invalid cache
  encodings, though the in-memory UTC contract permits any zero-offset tzinfo.
  Validate types, decimal grammar, finite/sign/OHLC/range/order/identity, duplicate
  keys/dates, timezone, unknown/missing fields and duplicate entries on every read.
  Cache JSON does not use provider JSON numeric rules; its strings preserve exact
  Decimal exponent/precision. Reject arbitrary objects/pickle entirely.
- Bounds: at most 32 entries, at most 3,660 bars each, at most 16 MiB UTF-8 file
  bytes and 4,096 characters per string. Bounded read checks file bytes before
  parsing; reject oversized/malformed/unsupported files without overwriting them.
  An individual validated result too large for these bounds is returned uncached
  with a safe category-only debug diagnostic. It is never truncated. Do not call
  repository put or perform eviction for this bypass; existing entries and file
  remain untouched.
- Successful insertion removes expired entries and evicts oldest retrieved_at
  entries until count/byte limits fit; ties use lexicographic key order. This is
  explicitly approved eviction of cache-owned data only. No holdings, database
  rows, legacy files or user-supplied files are pruned. No CLI clear/delete command.
- Missing file is a read miss without create-on-read. Unknown existing contents,
  a directory/symlink at the path, unsupported format/version, unreadable file or
  missing parent fail with HistoryCacheError. Do not silently replace or rename
  them. An invalid cache blocks graph retrieval before HTTP; documentation must
  explain the safe error, without an automatic repair/destructive command.
- Write a bounded complete candidate into a uniquely created same-directory
  temporary file, flush/close, and atomically replace only a validated cache file
  or absent target. Recheck target type/format immediately before replace. Failed
  writes raise HistoryCacheError and do not plot/claim a cache write succeeded.
  Clean up only the temporary file created by that operation. Atomic replacement
  prevents torn reads; it is not a power-loss durability or adversarial-filesystem
  guarantee. Simultaneous writers may lose cache entries, never holdings; no locks
  or cross-process quota suppression are promised. A concurrent unknown target
  discovered during recheck fails rather than being overwritten.

The strict M3 version-1 schema rejects extra application tables. Do not add cache
tables or change PRAGMA user_version under this option. JSON cache format version
is its own envelope version, not a second database migration runner. SQLite
storage remains governed solely by persistence.migrations. Sidecar contents are
not trusted financial holdings and are never imported as portfolio state.

## Compatible date selection and chart flow

Add keyword-only optional `start: date | None = None, end: date | None = None`
to root Stock.graph_performance and Watch_list.graph_stock after its existing
ticker argument. Neither supplied selects the default; both supplied selects the
explicit range; exactly one supplied raises HistoryRangeError. Preserve old
positional/no-argument calls and Stock-like doubles on the default path.

Default end is the injected UTC clock's prior calendar date. Default start is
the same month/day five calendar years earlier than end; February 29 clamps to
February 28 when the target year has no such date. This is date-range selection,
not a claim of five years of sessions. Clock injection lives outside domain.
Reject an unrepresentable default with HistoryRangeError. Excluding today's
session avoids displaying a current partial daily bar; yesterday may still be
unavailable or revised and is not claimed final.

Keep menu CLI `graph-stock` and ticker prompt; add optional string options
`--start YYYY-MM-DD` and `--end YYYY-MM-DD`, both or neither. Validate exact ISO
syntax/date pairing/range before provider/cache access. Invalid options render
the fixed range message and exit 1; help performs no credential/cache/state IO.
For a selected existing stock, use network configuration precheck and current
runtime key, including restored objects, only after the identity gate below.
No graph save or quote refresh occurs.
Missing ticker retains current no-graph behavior and performs no history IO.
Catch ConfigurationError and StockTrackerError, render safe message and exit 1;
do not catch programming errors. No new graph command in evaluation CLI.

Add monkeypatchable IO-free
`create_historical_market_data_provider(api_key: str | None) -> HistoricalMarketDataProvider`
to the existing external factory module; its decorator uses the sidecar above.
Keep create_market_data_provider and its current-data callers unchanged. The
facade does not retain a provider, cache repository, credentials beyond existing
runtime binding, or fetched bars in serialized state. Preserve summary refresh
order and holding/snapshot arithmetic. Cache belongs to graph invocation.

ADR-0006/0009 allow restored/imported stocks with non-NASDAQ or unresolved
exchanges; the NASDAQ lookup rule for newly added candidates does not validate
all saved entries. Before credential validation, factory construction, cache IO
or HTTP, the facade graph flow requires the stock's known exchange to be exactly
`NASDAQ`. None, `N/A`, another exchange or an alias raises the existing fixed
MarketDataUnavailableError, without resolving symbols, guessing an alias or
deleting/modifying holdings. CLI must not run its network key precheck before
this gate for a selected stock. Even a known NASDAQ identity relies on FMP's
symbol mapping: history rows contain no exchange proof, so matching symbols
cannot certify that the returned series belongs to that exchange. Broader
exchange-qualified history requires a separately verified/accepted contract.

Plot ascending actual dates against raw close, converting Decimal only at
Matplotlib boundary. Before creating any figure, convert every close to float
and require finite results; a strictly positive Decimal close must not convert
to zero. Catch conversion overflow and reject overflow, nonfinite or positive
underflow with fixed MarketDataUnavailableError. A genuine Decimal zero remains
legal. No figure or partial plot is created on rejection; stored/cached Decimal
values remain untouched. This rendering limit neither rounds domain values nor
changes the provider's finite-Decimal validity. One observation yields one marker. Use observation markers
without connected interpolation across missing dates. No synthetic/current-price
point, summary reconstruction, moving average, normalization or return annotation.
Title identifies ticker, `Raw historical close`, requested range; caption includes
observed span/count and `Unadjusted prices; splits may appear as discontinuities.`
Y label is `Price (currency unavailable)` because selected history schema exposes
no currency. Do not infer USD or treat saved current profile currency as verified
historical currency; later verified metadata can authorize a separately reviewed
label. Empty/error result produces no figure; plotting never mutates holdings,
current quote, summaries or SQLite state.

| Caller | Proposed change and preserved contract |
| --- | --- |
| Stock.graph_performance() | Compatible optional date arguments; obtain history through factory, delegate validated bars to plotting, return existing plotting result. |
| Watch_list.graph_stock(ticker) | Preserve ordered matching entries, including duplicates; default invokes each Stock-like object's no-argument method, explicit range passes the new keyword dates. |
| menu_watchlist.graph_stock | Preserve ticker prompt/command; add paired date options, safe provider/cache/range handling, no save. |
| daniils_stock_method.py | No history command or behavior change. |
| get_price_over_time / get_period_changes | Remain provider summary display methods, never chart inputs. |
| Root serialization / M3 mapping | Keep existing state fields; do not persist bars, cache handles or provider clients. |
| Packaging/probes/tests | Include any new explicitly enumerated package/module; retain domain isolation and source/installed-wheel contracts. Replace synthetic-chart expectation deliberately. |

## Alternatives and consequences

**B: Full endpoint charts.** Less surprising JSON key names and existing examples,
but do not call its close raw without endpoint-specific adjustment proof. A
separately accepted typed price-basis model could make this safe; do not silently
reuse PriceBar raw fields for a differently adjusted series.

**C: Fetch both raw and dividend-adjusted endpoints.** Could preserve both series
with explicit provenance and exact date alignment, but doubles quota/reliability
surfaces and requires trustworthy adjustment/corporate-action semantics.
Dividend-reinvested return remains undefined even if such data are retrieved.
Defer rather than infer FC-061 compliance from a field name.

**D: SQLite cache through approved additive migration.** Integrates transactions
and concurrent writes with primary storage, but requires a separately accepted
version-2 schema, the existing sole migration runner, exact-schema updates,
preservation/backup tests and M3 compatibility review. Adding a table to version
1 is invalid. This proposal selects the JSON sidecar to preserve M3 exactly.

**E: In-memory cache or disabled TTL.** Simplest and avoids disk errors, but fresh
facade factories and separate command processes miss every time. Disabled cache
does not satisfy the intended M4 caching work. One-hour persistent tolerance
reduces repeated identical graph quota while leaving correction delay explicit.
Longer TTL increases correction staleness; shorter TTL reduces reuse. Automatic
stale fallback would conceal failures and requires a different accepted policy.

**F: Same-day/default or arbitrary-length ranges.** More recent/current results,
but incomplete daily sessions, provider cap and paging introduce additional
contracts. Prior-day end and 3,660-day bound give deterministic bounded requests.
Observations-only markers expose gaps without claiming session completeness.

Option A delivers genuine raw historical charts and useful repeated-invocation
cache reuse, while deliberately withholding adjusted-return claims. It adds a
cache-owned local file, new safe errors and optional public date selection; these
are explicit approval subjects, not incidental implementation decisions. Cache
disk failures can block charts; simultaneous writers may spend duplicate quota.

## Verification and exit evidence required after acceptance

Independent review must check evidence, caller signatures, issue ordering and
every policy value before acceptance. Runtime issues add deterministic coverage:

- Hand-verifiable raw mapping, fractional Decimal precision, zero prices/volume,
  nullable volume, impossible OHLC, malformed/error arrays and safe diagnostics.
- Fixed-clock default/leap/date limits, missing sessions, ascending sort,
  duplicate/wrong-identity/outside-range rows and atomic parsing/empty behavior.
- Fake transport verifies route/query/header, no extra requests, existing retry
  and error categories, no malformed/empty caching and no endpoint fallback.
- Temporary sidecar verifies exact keys/format, new adapter and subprocess reuse,
  TTL boundary/backwards clock, mutation isolation, eviction/size bounds,
  corruption/future version/IO failures, atomic replacement and no stale fallback.
- Plot-data and both CLI regressions prove actual provider observations replace
  summary fabrication; no mutation/save, safe errors, help IO isolation, compatible
  Stock-like callers and explicit dates. Assert exact numeric data before plotting.
  Test imported/restored non-NASDAQ and unresolved identities reject before key,
  cache and network access, exact NASDAQ admits the scoped flow, no alias/lookup
  is inferred, and no holdings are changed. Rendering fixtures include huge and
  tiny finite Decimal closes, genuine zero and ordinary fractional prices;
  rejection must precede figure creation and preserve exact Decimal data.
- Preserve exact M3 schema/restart/backup tests and domain/source/wheel isolation.
  Canonical Python 3.11/3.12 `pip check`, full pytest, Ruff and configured mypy
  (`config.py` only) plus targeted tests must actually pass for runtime PRs.

The M4 exit is genuine provider history driving charts, with all five M4 bullets
mapped to merged issues and passing required CI. Synthetic fixtures establish
parser/integration behavior, not live entitlement or full session completeness.
No live credential request is required to claim offline implementation evidence.
Record unverifiable endpoint evidence or unavailable canonical tooling honestly;
do not run the suite under an unsupported Python version or install system tools.

This ADR is a proposal artifact. It neither satisfies the runtime exit nor closes
adjusted-price, dividend, portfolio-performance or other financial open decisions.
