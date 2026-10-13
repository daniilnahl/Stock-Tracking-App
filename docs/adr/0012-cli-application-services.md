# ADR-0012: Compatible CLI application services

## Status and acceptance gate

**Accepted — 2026-10-13.** The owner directly instructed **"Option A approved,
pr merged, continue"** after reviewing
[PR #120](https://github.com/daniilnahl/Stock-Tracking-App/pull/120). This accepts
the complete Option A service/CLI contracts and exit criteria below. Owner merge
was independently verified at `96182b6e9b28c743a05a9e8cfb7985b5c8b833f6`,
containing reviewed proposal head `23169daa36e751c021506dead62b52eaf0c0ff3e`.
Its exact-head [Foundation run 38442157132](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38442157132)
and post-merge [main run 38442587378](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38442587378)
passed all five configured checks, including Python 3.11/3.12. Acceptance,
owner-merge and main-CI prerequisites are satisfied; #114 may begin. Later
issues retain their own dependency/owner-merge/CI gates. No agent merge,
unapproved financial convention or expanded command scope is authorized.

The original proposal wording below documents the accepted decision, rather
than indicating that it remains unapproved. This is the contract for
[issue #112](https://github.com/daniilnahl/Stock-Tracking-App/issues/112), in
[M6 — CLI V2](https://github.com/daniilnahl/Stock-Tracking-App/milestone/7).
Publication, issue creation, passing checks and the initial request to begin M6
did not establish acceptance; the direct owner instruction above does. Runtime
work depended on explicit acceptance, owner merge and passing required CI.
Agents must not merge. The independent terminology correction in #113 uses
already approved financial definitions and does not depend on this decision.

## Context and authority

SRS §23 M6 requires the CLI to become a thin application-service interface.
Its listed commands are **potential commands**, with neither a mandatory new
command set nor a detailed exit criterion. ARCH-001/003/004/005 require layer
separation, provider/repository interfaces and a service layer reusable by future
REST callers. ARCH-006 requires an accepted ADR for this architecture choice.
Other relevant requirements are ARCH-002, DOM-002–004, FIN-001–005,
DATA-003/006/007/008, PERS-005/007, SEC-002/005, ERR-001–003, PERF-001/002,
TEST-002–005 and DEV-001–004.

Accepted ADR-0006 supplies numeric positions and calculations, with conservative
exchange identity and ordered duplicate preservation. ADR-0007/0008 supply
typed provider capabilities and scoped lookup/error semantics. ADR-0009 supplies
independent watchlist namespaces, exact numeric SQLite state and existence-only
legacy protection. ADR-0010 supplies raw historical data, range/identity/cache
rules and presentation guarantees. ADR-0011 supplies pure currency-qualified
portfolio snapshots; it explicitly reserves shared services and input acquisition
for later work. None approves inferred cost currency or watchlist conversion.

At baseline `11f7333abdac830e139dd74354c87b30fe4cd45d`, both root CLIs still
orchestrate load, lookup, profile/period retrieval, ownership and persistence.
`stock.py` imports presentation code, and `watch_list.py` imports Rich. Hiding
those objects inside a service would retain the presentation dependency.
`compatibility/cli_persistence.py` also returns Watch_list facades and therefore
cannot be the service's local-storage interface unchanged.

Inspected callers/tests include both root CLIs, `stock.py`, `watch_list.py`,
the compatibility numeric/presentation/stock/history/persistence modules,
provider and persistence models/protocols, domain calculations,
`tests/test_cli_ownership.py`, `tests/test_cli_persistence.py`,
`tests/test_provider_integration.py`, `tests/test_history_date_selection.py`,
`tests/test_baseline.py`, `tests/test_packaging.py` and their subprocess probes.
These sources define compatibility evidence; this proposal is not a claim that
future implementation checks have passed.

## Proposed Option A: existing use cases, neutral services

Required M6 scope is compatible thinning of the two maintained watchlist CLIs.
Keep the root `menu_watchlist` and `daniils_stock_method` modules, command names,
prompt sequencing, help, callable compatibility surfaces and separate storage
namespaces. Keep the menu's graph command and paired date options; add no graph
command to the evaluation CLI. No installed entrypoint, Portfolio CRUD,
portfolio summary acquisition, performance or risk command is required here.

Add `stock_tracker.services` for application orchestration and a maintained
presentation/composition adapter package, `stock_tracker.cli`. Add these to the
existing explicit setuptools package list. No dependency, runtime version,
schema, package manager, provider endpoint, retry/cache policy or configured
mypy scope changes. Pure financial calculations remain in the domain.

Services may import the standard library, domain models/calculations, neutral
provider models/protocols, neutral persistence records/protocols and safe
application exceptions. They must not import Typer, Rich, Matplotlib,
configuration/environment loaders, SQL/database/HTTP implementations, provider
URLs/payload schemas, root facade/watchlist modules, or compatibility modules
whose import graph reaches those components. Dependencies are explicit inputs;
services never construct production providers or SQLite repositories.

### Exact proposed neutral shapes

The following shapes are contracts for implementation, not existing runtime
code. Use frozen dataclasses with tuple collections. Existing `Stock` below
means the domain security, not the root facade. Reuse existing validated
`WatchlistEntry`, `WatchlistRecord`, `CompanyProfile`, `PeriodChanges`,
`PriceBar`, `Position` and `PositionSnapshot` rather than provider dictionaries.

```python
@dataclass(frozen=True, slots=True)
class EntryView:
    entry: WatchlistEntry
    snapshot: PositionSnapshot | None

@dataclass(frozen=True, slots=True)
class WatchlistView:
    record: WatchlistRecord
    entries: tuple[EntryView, ...]

@dataclass(frozen=True, slots=True)
class AddPreparation:
    status: Literal["ready", "invalid", "duplicate"]
    profile: CompanyProfile | None
    periods: PeriodChanges | None

@dataclass(frozen=True, slots=True)
class OwnershipInput:
    quantity: Decimal
    average_cost: Decimal

@dataclass(frozen=True, slots=True)
class EntryUpdate:
    ordinal: int
    entry: WatchlistEntry
    # None means leave these saved display fields untouched.
    # A typed model containing null values means publish unavailable metadata.
    profile: CompanyProfile | None
    periods: PeriodChanges | None
    invalidate_periods: bool

@dataclass(frozen=True, slots=True)
class PreparedWatchlist:
    record: WatchlistRecord
    updates: tuple[EntryUpdate, ...]

@dataclass(frozen=True, slots=True)
class HistoryView:
    stock: Stock
    start: date
    end: date
    bars: tuple[PriceBar, ...]
```

`WatchlistView.entries` has exactly one row for every record entry, in order.
An unowned row has `snapshot=None`; an owned zero-cost/zero-quantity row remains
owned. Snapshot computation constructs a Position only for explicit non-null
average cost and delegates to `position_snapshot`, retaining Decimal/None.
No total/weight/portfolio calculation is introduced. Existing same-currency
position input preconditions remain; no display field certifies cost currency.

`AddPreparation` has both models exactly when status is ready, and neither for
invalid/duplicate. Revalidate typed results and required associations at service
boundaries so malformed fakes cannot bypass production adapter validation.
`EntryUpdate.ordinal` binds to an individual row, never a globally unique ticker.
`invalidate_periods=True` requires `periods=None`; reject the conflicting shape.
It signals the existing unavailable display markers without fabricating a
PeriodChanges observation or its receipt timestamp. Ordinary profile/period
success updates set the flag False.
`PreparedWatchlist.record` contains validated identity, ownership, numeric price
and non-financial metadata. For newly fetched market-cap/period fields it carries
existing opaque display text (or initial unavailable markers); `updates` carries
their unformatted provider values for the presentation projection below.

Saved market-cap and period strings are **opaque compatibility metadata**, not
numeric domain input. They may include empty strings or literal nonnumeric text.
Do not parse them to obtain financial calculations or manufacture history.
Fetched market-cap and period values stay Decimal/None until the presentation
boundary. Existing period inputs are provider-reported percentage points;
position unrealized return is a decimal ratio. Do not interchange those units.

### Injected interfaces and usable service signatures

```python
class LegacyPresence(Protocol):
    def __call__(self) -> bool: ...

class CurrentProviderSource(Protocol):
    def __call__(
        self, operation: Literal["resolve", "profile", "periods"],
        ordinal: int | None,
        *, on_configuration_failure: Callable[[], None] | None = None,
    ) -> MarketDataProvider: ...

class HistoricalProviderSource(Protocol):
    def __call__(self, ordinal: int) -> HistoricalMarketDataProvider: ...

class WatchlistService:
    def __init__(
        self, repository: WatchlistRepository, *, namespace: str,
        legacy_present: LegacyPresence,
    ) -> None: ...
    def load(self) -> WatchlistRecord: ...
    def save(self, record: WatchlistRecord) -> None: ...
    def view(self, record: WatchlistRecord) -> WatchlistView: ...
    def remove(self, record: WatchlistRecord, symbol: str) -> WatchlistRecord: ...

class CurrentDataService:
    def __init__(self, providers: CurrentProviderSource) -> None: ...
    def prepare_add(self, record: WatchlistRecord, symbol: str) -> AddPreparation: ...
    def validate_ownership(self, quantity: str, average_cost: str) -> OwnershipInput: ...
    def finish_add(
        self, record: WatchlistRecord, prepared: AddPreparation,
        ownership: OwnershipInput,
    ) -> PreparedWatchlist: ...
    def refresh(
        self, record: WatchlistRecord, *,
        on_update: Callable[[EntryUpdate], None],
    ) -> PreparedWatchlist: ...

class HistoryService:
    def __init__(
        self, providers: HistoricalProviderSource, *,
        clock: Callable[[], datetime],
    ) -> None: ...
    def validate_range(self, start: date, end: date) -> tuple[date, date]: ...
    def history(
        self, stock: Stock, *, ordinal: int,
        start: date | None = None, end: date | None = None,
    ) -> HistoryView: ...
```

Constructors perform no IO. `WatchlistService` uses only the existing repository
protocol and injected existence check. It does not receive a Path or issue SQL.
On `load`, call repository.get(namespace) first; an existing namespace remains
authoritative. If absent, check legacy presence and refuse with the existing
`LegacyStatePresentError`, otherwise return the explicit empty Watchlist record.
On `save`, validate the complete record and require its exact namespace to match
the service before the absence/legacy check; then repository.save atomically.
Never turn storage errors/corrupt/future schema into an empty fallback.
The production existence adapter uses `lstat`, maps OSError safely, and never
opens/follows/deserializes legacy contents. Help does not invoke this adapter.

`remove` preserves the existing root Watch_list removal algorithm, including its
forward-iteration behavior when ordered duplicate symbols occur, rather than
silently inventing remove-first/remove-all semantics. Implement its neutral
equivalent with known fixtures; this compatibility proposal does not repair that
legacy ambiguity. No identity normalization, deduplication or exchange-wide
holdings policy is authorized. Existing no-match removal still saves the
resulting namespace as the current command does.

Provider sources allow lazy construction at the exact requested operation and
row. They are dependency ports, not credential records or provider-policy knobs.
Production composition owns factories and current runtime key bindings.
Services call only capability methods and enforce existing result identities;
no new retries, cache fallback or request aggregation is added.

### Add sequencing and ownership

The root network preflight remains before state restoration and ticker prompt.
The root reads/uppercases the ticker; the service performs supported lookup,
then duplicate-by-exact-symbol checking, then profile, then period retrieval.
A validated InvalidTickerError produces `invalid`; infrastructure/inconclusive
errors propagate with their established categories. Duplicate lookup still
occurs before the duplicate result, preserving provider request order.
Do not read or write CSV hints. Lookup metadata does not supply missing profile
metadata or establish an owned position's cost currency.

Only ready preparation reaches ownership prompts. The command reads both text
inputs, calls `validate_ownership`, renders DomainValidationError and repeats
both prompts when invalid. Parsing preserves the existing plain-decimal grammar,
whitespace trimming and finite/nonnegative validation without float conversion
or quantization. Refactor/reuse this pure parser without importing the facade or
presentation. Zero quantity and zero average cost are valid explicit ownership.
Minus-one, underscores, NaN, Infinity and malformed text remain invalid.

Retrying the ownership pair performs no additional provider lookup/profile/
period calls. EOF/abort leaves existing objects and saved bytes unchanged.
`finish_add` creates a fully validated neutral entry and snapshot before any
root candidate publication; it does not save. The presenter projects fetched
display metadata, then the root invokes its save shim and reports success only
after successful persistence. Invalid/no-match/duplicate/provider failure does
not append, save, or prompt for ownership.

### Refresh failure and publication contract

Refresh preserves per-entry order and profile-then-period requests. Validate
profile identity against the entry's exact known exchange/currency and symbol;
retain known metadata on absent incoming exchange/currency, reject conflicts,
and keep unavailable values distinct from zero. A stored display currency is
only the existing metadata consistency check, not verified cost currency.

`on_update` receives neutral progress after a validated profile, after validated
period data, and after the relevant safe invalidation on an anticipated failure.
The callback is an external compatibility adapter; no Typer/Rich/facade code
enters the service through imports or hidden construction. Profile failure emits
the row with absent numeric quote and unchanged ownership/other metadata.
Period failure emits `periods=None, invalidate_periods=True` while retaining the
successful profile price and metadata. No fake period result or observation
timestamp is constructed. Profile failure uses `invalidate_periods=False`.
Earlier completed rows remain published in memory.
The service stops at the first failure and rethrows the original safe category.
The callback must not save. Programming errors propagate without fabricated
invalidation or success. On complete success return the ordered candidate; only
the caller's later explicit save commits it.

This intentional partial **in-memory** publication preserves
`test_cli_failed_refresh_keeps_saved_file_and_invalidates_in_memory` and
`test_partial_two_stock_refresh_preserves_saved_file_and_order`. SQLite state
remains all-or-nothing and unchanged after any provider failure. This proposal
does not replace existing safe invalidation with stale current-price claims.

For each refresh stage, the service supplies `on_configuration_failure` to the
provider source: a zero-argument closure owned by the service that emits exactly
the same stage-specific invalidation EntryUpdate through `on_update`. The
production source adapter catches only the existing ConfigurationError from
factory acquisition, invokes the supplied closure once, then rethrows that
original exception. Add acquisition supplies None, because add failure must not
publish a candidate or invalidate an existing row. A source fake may exercise
this same callback contract without importing configuration into the service.
The service catches existing StockTrackerError stage failures and performs
their invalidation itself; it does not catch ConfigurationError, duplicate the
adapter's callback, or turn programming errors into invalidation. Services never
import ConfigurationError. Tests must distinguish configuration failure,
application failure and programming failure and prove one invalidation per
anticipated failing refresh stage. Unexpected errors must not become invalid
tickers.

### Presentation and composition contracts

The maintained presentation adapter exposes:

```python
project_prepared(result: PreparedWatchlist) -> WatchlistRecord
apply_entry_update(entry: WatchlistEntry, update: EntryUpdate) -> WatchlistEntry
render_watchlist(view: WatchlistView) -> None
render_history(view: HistoryView) -> None
```

`apply_entry_update(existing, update)` copies identity, numeric quote/ownership
and plain metadata from the validated `update.entry`. Market-cap and the eight
period display fields start from the supplied existing entry's already projected
values, then are overwritten only by a present profile/period model or the
explicit period invalidation flag. Thus a later period callback cannot restore
stale opaque market-cap text over an earlier profile callback's formatted value.
Formatting changes only display fields using existing market-cap and period
formatting rules; projection performs no financial arithmetic. Numeric price,
quantity and average cost remain exact Decimal/None.
When `invalidate_periods=True`, projection sets exactly the existing eight
period display fields to `N/A`; it does not infer a numeric missing observation.
`project_prepared` starts with `result.record.entries`, validates each update's
ordinal bounds and exact symbol association to that row, and replays its ordered update tuple using
`apply_entry_update`. Multiple updates for a row are applied sequentially; a
final callback/result replay must produce the same projected metadata. New add
rows are present in the prepared record before projection. Return a fully
validated WatchlistRecord with the unchanged namespace, name and row order.
Unchanged saved strings preserve spelling, empty and escaped-literal behavior.
Rendering formats the numeric snapshot unrealized ratio at display only; #113's
approved headings say Average Cost per Share and Unrealized Return.
The history renderer consumes HistoryView directly; it must not call a facade
fetch method and trigger a second request. Keep observed dates, marker-only raw
closes, conversion guards before figure creation, requested/observed labels,
currency unavailable and split-discontinuity notice.

Production composition selects cwd-relative SQLite/cache paths once per process,
constructs existing repository/provider implementations lazily, and injects a
fixed-namespace existence adapter. Retain root module API_KEY capture through
the existing configuration loader and explicit command preflight; add no second
dotenv discovery or refresh-on-every-call configuration lifecycle. Import/help
may load configuration as today but never require a key, inspect legacy state,
open storage, construct provider transports or perform requests.

Local display/load/remove remain credential-free. Network preflight uses the
root captured key; legacy current-data operations retain per-facade runtime-key
bindings through provider-source closures, including safe factory configuration
failure on an explicitly supplied facade with a different key. Historical source
composition temporarily binds the current root key for selected legacy objects
and restores previous keys after success, anticipated failure and programming
error. No credential crosses into records/views/domain/persistence/log messages.

### History identity and dates

Validate paired exact ISO option syntax and explicit range before local command
preflight as currently. After loading and selecting, reject unsupported known
identity before historical key checks/cache/HTTP. Only exact NASDAQ is supported;
unknown/other/alias exchanges fail safely without changing holdings.
No ticker match remains a no-op. Ordered matching rows, including duplicates,
are retained rather than coalesced by ticker.

Use the injected UTC clock and accepted range policy: default end is yesterday,
default start is five calendar years earlier with leap-day fallback; paired dates,
maximum span and rejection of today/future dates remain unchanged. Resolve each
service request's range once and carry those exact dates in HistoryView through
retrieval and rendering. An explicit range validated before preflight is still
checked at the retrieval boundary against its injected clock; this is validation,
not a second default-range calculation.
Use the existing historical factory/cache policy. Revalidate nonempty ordered
PriceBars, exact symbol/range, raw adjusted_close=None and volume bounds. Do not
invent exchange proof, complete sessions, historical currency, adjusted returns
or stale fallback. History never saves watchlist or portfolio state.

### Root compatibility shims and test migration

Keep `app`, `API_KEY`, `WATCHLIST_FILE`, `WATCHLIST_NAMESPACE`,
`LEGACY_WATCHLIST_FILE`, `current_watchlist`, `_watchlist_loaded`,
`load_watchlist`, `save_watchlist` and `_prepare_command` callable/globals.
Keep command-level calls through root save/preflight shims so existing guards
remain meaningful. Preserve current list/object references and explicitly supplied
in-memory contents rather than replacing them on lazy load. Neutral mapping
between those facades and service records lives outside services/domain.

Compatibility helpers may adapt lightweight Stock-like direct callers for
existing Watch_list rendering/graph methods. They are not service inputs and
must not bypass validated production records. Root Stock facade methods remain
supported for existing direct callers; service execution must not call them.
Tests that patch facade HTTP orchestration may move their injection to the
explicit service provider source, but retain their observable assertions for
safe errors, exact request order, invalidation, state preservation and aborts.
Do not weaken/delete tests to hide a changed public behavior. Keep source/wheel
subprocess probes and root help/save/preflight guard surfaces.

## Accepted exit criteria (original proposal)

1. Both maintained CLI command surfaces delegate local/market/history business
   orchestration to the injected, presentation-independent service contracts.
   CLI code owns prompts, input syntax, render projection and safe error mapping;
   composition adapters own configuration and concrete dependencies.
2. Service imports/execution are usable with neutral fakes without Typer, Rich,
   Matplotlib, facade modules, configuration access, SQL or HTTP implementations.
   Meaningful boundary-denial tests demonstrate this, rather than naming alone.
3. Existing help, prompt sequencing, namespace/legacy protection, exact Decimal,
   unowned/zero/missing distinctions, request/error/invalidation and history/cache
   guarantees survive actual source and installed-wheel commands/restarts.
4. #113 terminology is integrated; display does not mutate numeric snapshots or
   reinterpret provider percentage metadata. No unapproved metric is exposed.
5. Independent combined exit audit and required canonical checks pass, owner
   merges and required CI are verified, required issues close, and operation/
   milestone evidence documents actual checks and remaining limitations.

These owner-accepted criteria make the SRS objective testable under Option A.
They certify no REST endpoint,
new installed CLI contract, portfolio summary provenance or live entitlement.

## Issue map and dependency ordering

| Issue | Bounded objective | Blocking dependencies |
| --- | --- | --- |
| [#112](https://github.com/daniilnahl/Stock-Tracking-App/issues/112) | Review/approve this service/CLI contract and exit proposal | Owner acceptance, owner merge and required CI |
| [#113](https://github.com/daniilnahl/Stock-Tracking-App/issues/113) | Correct existing financial table headings | Independent approved financial definitions |
| [#114](https://github.com/daniilnahl/Stock-Tracking-App/issues/114) | Local watchlist service boundary and shared neutral contracts | Accepted, owner-merged #112 with required CI |
| [#115](https://github.com/daniilnahl/Stock-Tracking-App/issues/115) | Current-data orchestration service | Owner-merged #114 with stable shared contracts |
| [#116](https://github.com/daniilnahl/Stock-Tracking-App/issues/116) | Historical retrieval service | Owner-merged #114; independent of #115 after stable contracts |
| [#117](https://github.com/daniilnahl/Stock-Tracking-App/issues/117) | Thin adapters for both maintained root CLIs | Owner-merged #114–116 and required CI |
| [#118](https://github.com/daniilnahl/Stock-Tracking-App/issues/118) | Independent combined exit audit and operation docs | Approved exit criteria and owner-merged #113–117 |

All belong to M6, GitHub milestone 7. Detailed progress and assignment live in
[the M6 plan](../milestones/m6-plan.md). No blocked implementation begins.

## Verification expected from implementation

Service tests use typed fake providers, real pure calculations, fixed UTC clocks
and explicit temporary state. Cover local legacy/absence/schema rejection,
ownership grammar and repeated-input/no-extra-request behavior, exact stage/order,
identity conflicts, null/zero prices, profile/period failure progress, programming
errors and no-save boundaries. History tests cover sparse real bars, request
range and exact rendering inputs with cache reuse/expiry failures. Boundary tests
deny UI/config/facade/concrete IO imports and verify enforcement with controls.

Retain relevant existing CLI/provider/persistence/history/financial tests and
subprocess source/wheel probes. The independent exit combines both namespaces,
precise persisted holdings, help/local display without keys, controlled request
and failure paths, and cached historical rendering with guards active before
imports. Tests never use real user state or live network/credentials.

Run targeted tests, `python -m pytest`, `python -m ruff check .`,
`python -m mypy` and `python -m pip check` in the canonical environment.
Configured mypy remains `config.py` only; report this accurately. Verify wheel
package inclusion and real command execution offline. Passing a documentation
proposal check does not satisfy these runtime exit tests.

## Alternatives and consequences

**Option A, recommended:** preserve existing command/product contracts while
introducing reusable neutral services and presentation adapters. This delivers
the explicit M6 objective without inventing portfolio ownership/currency rules.
Its cost is deliberate legacy progress/shim support and projection of existing
saved display metadata. It does not implement every potential SRS command.

**Option B:** add an installed `stocktracker` entrypoint with an explicitly chosen
command tree. Requires owner-reviewed arguments/options, namespace/path/default
selection, exit behavior and compatibility policies, with bounded follow-up
issues. It may wrap Option A services after those decisions; it is not implicitly
required or authorized by this proposal.

**Option C:** introduce new Portfolio/Position CRUD and fetched summary commands.
Requires explicit selection, duplicate/removal, ownership-update and cost/quote
currency provenance contracts. Current Portfolio storage has no currency or
quote observation; accepted ADR-0011 forbids inferential shortcuts. Any required
schema/domain/public-contract changes need separate accepted decisions and
preservation tests before implementation. Historical cash-flow performance,
benchmark, FX, dividend and risk metrics also require normative financial
definitions; adding command names does not approve them.

No option authorizes agent merges, destructive migrations, production actions,
credential rotation or a toolchain/framework replacement.
