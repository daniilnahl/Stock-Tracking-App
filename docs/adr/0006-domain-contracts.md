# ADR-0006: M1 domain contracts and legacy compatibility

## Status

**Subsequent persistence completion (2026-10-06):** accepted ADR-0009 expressly
extends this ADR's M1 legacy filename/pickle-IO preservation for maintained CLI
storage. [M3 is complete](../milestones/m3-exit-evidence.md): SQLite namespaces
replace application pickle IO, with lazy loading and preserved legacy files.
The original accepted M1 contract and context below remain intact; their
pickle-loading limitations describe that historical scope.

**Accepted.** The repository owner accepted the complete proposal at commit
`f4693ab` on **2026-10-03**, recorded in the
[PR #37 acceptance comment](https://github.com/daniilnahl/Stock-Tracking-App/pull/37#issuecomment-5973462602).
This records the contract decision for
[issue #25](https://github.com/daniilnahl/Stock-Tracking-App/issues/25) in
[M1](https://github.com/daniilnahl/Stock-Tracking-App/milestone/2).
The contract-acceptance gate is satisfied. Runtime implementation reached `main`
at `788d3c4` through owner-merged PR #46 on 2026-10-04; the
[M1 completion review](../milestones/m1-exit-evidence.md#completion-review--2026-10-04)
records passing main CI, source/test evidence and closure of all required issues.
Acceptance does not authorize agent
merges, user-data migration, unrelated public-contract changes or a new SRS.

## Context

Approved [SRS](../../SRS.md) §§5, 7, 8 and 23 require isolated Stock, Position
and Portfolio while preserving existing callers. Root `stock.Stock` currently
combines credentials, string values, ownership, HTTP and charting. Root
`watch_list.Watch_list` combines an ordered watchlist with presentation and
refresh orchestration. It is not a portfolio. Existing pickle state names both
root classes. The CLIs load cwd-relative state at import time.

This ADR implements the planning boundary for ARCH-001/002/005/006,
DOM-001–004, FIN-001–005 and ERR-001–003. Financial meaning comes only from
[FC-001–004, FC-020/030/040/041, FC-110 and §17](../FINANCIAL_CALCULATIONS.md).
The [M1 issue map](../milestones/m1-plan.md) owns implementation and verification.

## Decision

### Package and dependency direction

Add the following bounded source tree; retain all root modules and `utils`:

```text
src/stock_tracker/
    __init__.py
    domain/
        __init__.py
        errors.py
        stock.py
        position.py
        portfolio.py
        calculations.py
    compatibility/
        __init__.py
        numeric.py
        stock_operations.py
        presentation.py
```

`stock_tracker.domain` exports Stock, Position, Portfolio, PositionSnapshot,
position_snapshot and DomainValidationError. Domain imports only its own
modules and the standard library. It never imports compatibility, root stock,
watch_list, configuration, HTTP utilities, Rich, Typer or Matplotlib. Domain
construction/calculation does not read environment, clock, filesystem or DB,
fetch quotes, print, or validate a ticker with a provider. Compatibility may
import domain; domain cannot import compatibility. Existing CLI entrypoints
remain unchanged; CLI V2 and a shared public service API remain M6/M7 work.

[ADR-0005](0005-canonical-python-dependencies.md) remains canonical for Python
3.11/3.12, pip, setuptools, dependency pins and root-module contracts. The only
accepted extension is explicit package discovery for this source tree alongside
installed root modules/`utils`, and adding `src` to checkout test imports. No
whole-repository relocation, dependency or Python change is authorized. Acceptance
of this ADR authorizes that narrow extension to ADR-0005's flat packaging
choice, without superseding its environment decision. #26 owns those edits and
installed-wheel tests; this PR changes no toolchain configuration.

### Local errors and numeric conversion

`DomainValidationError(ValueError)` lives in `domain.errors`. Invalid domain
construction/update/quote inputs raise this explicit error with a field-specific
safe message. Errors do not echo supplied data, credentials, URLs or provider
payloads. Domain does not catch infrastructure errors or render messages; the
facade/CLI maps validation errors to existing re-prompts. A wider application
exception hierarchy is not introduced by M1.

Domain numeric parameters require actual `Decimal` objects. They reject other
runtime types, negative values, NaN and infinities. Zero and finite fractional
values are valid. Domain does not silently accept formatted strings or floats.
Boundary conversion is `to_decimal(value: Decimal | str | int | float,
field: str) -> Decimal` in `compatibility.numeric`: preserve Decimal, parse
plain stripped decimal text, convert integer exactly, and convert a finite
legacy/provider float with `Decimal(str(value))`. Reject bool, empty/malformed
text, decorated money/percent text, NaN and infinities with DomainValidationError.
Nonnegativity remains domain validation. Float conversion preserves the supplied
float's decimal spelling, not precision already lost upstream. #31 prompts for
raw text, eliminating that roundtrip for new user holdings. This does not alter
JSON transport/provider parsing policy in M2.

No fixed quantization scale, money rounding mode, altered Decimal context,
transaction rule or FX rule is selected. Decimal arithmetic follows the caller's
context; no extra intermediate display rounding is applied. Division can be
inexact for repeating ratios. Tests use hand-verifiable terminating fixtures and
check that display never mutates numeric state.

### Stock identity — #26

```python
Stock(symbol: str, name: str | None = None, exchange: str | None = None)
```

Stock is immutable and hashable, holding exactly these fields. Symbol must be a
nonblank string without surrounding whitespace; optional strings must be None
or nonblank strings without surrounding whitespace. No case folding, exchange
alias resolution, regex for valid tickers, or provider lookup is performed.
Callers already uppercase CLI symbols; provider identity normalization is M2.
Name is descriptive and excluded from equality/hash. The external legacy/provider
boundary maps None and the exact legacy sentinel 'N/A' for name/exchange to
domain None before constructing Stock; 'N/A' must never become a known exchange
identity. Nonblank malformed identity values fail local validation instead of
being silently normalized.

When both objects have a known exchange, equality/hash use the exact
`(symbol, exchange)` pair. Same symbol on different exchanges is unequal. When
either exchange is absent, distinct instances are unequal, even with the same
symbol; an instance still equals itself and uses object identity for hashing.
Unknown exchange does not create a global ticker identity. No provider-stable
identifier is invented: future support needs a reviewed contract extension.
Portfolio construction never deduplicates either known or unresolved identities.
This conservative equality choice is included in the recorded owner acceptance.

### Position — #27

```python
Position(stock: Stock, quantity: Decimal, average_cost: Decimal)
Position.with_owned_data(quantity: Decimal, average_cost: Decimal) -> Position
```

Position is immutable. Construction validates Stock type and finite nonnegative
quantity/average_cost. `with_owned_data` creates a new fully validated Position
for the same Stock; it never changes the old instance. A failed replacement
preserves both old inputs. Quantity is shares, average_cost is currency per
share and authoritative input (FC-110), not total basis. No currency aggregation
or currency inference is performed. No buys/sells or average-cost evolution is
implemented. The facade constructs/validates a candidate and its snapshot before
assigning ownership state, so a failed operation cannot partially change it.

### Portfolio — #28

```python
Portfolio(id: int | None, name: str, positions: list[Position] | None = None)
Portfolio.positions: list[Position]
```

Portfolio is a simple dataclass with an owned mutable `positions` list. Id is
None or int excluding bool; no generated ids or database-specific positivity rule.
Name is a nonblank string without surrounding whitespace. Construction validates
these inputs and requires a list containing only Positions (or None for empty),
then defensively copies the supplied list. An omitted collection creates a fresh
empty list for each instance, using default_factory or an equivalent constructor
implementation. Mutating `portfolio.positions` changes its own list, without
changing the constructor's caller list or another portfolio's list. Position
elements are immutable. Validation of list elements occurs at construction; the
public list is typed thereafter, without attempting to police every list mutation.
Supplied order and duplicates are retained, including equal known identities and
same-symbol/different-exchange instances. M1 adds no CRUD methods, deduplication,
transactions or id allocation. Future portfolio operations need their own contract.
A Watch_list remains separate; no watchlist conversion creates holdings or a
Portfolio automatically.

### Pure position snapshot — #29

```python
PositionSnapshot(
    cost_basis: Decimal,
    market_value: Decimal | None,
    unrealized_pnl: Decimal | None,
    unrealized_return: Decimal | None,
)
position_snapshot(position: Position, current_price: Decimal | None) -> PositionSnapshot
```

Result is immutable; function validates Position and quote, returns a newly
computed result, and never stores a quote on Stock/Position or carries an earlier
result forward. Current price is per-share in the same currency as average cost,
a caller precondition; M1 has no FX or mixed-currency totals.

| Output | Formula / meaning | Requirement |
| --- | --- | --- |
| cost_basis | Q × C, currency | FC-020 |
| market_value | Q × P, currency; None if P absent | FC-030 |
| unrealized_pnl | value − basis, currency; None if value absent | FC-040, §17 |
| unrealized_return | P&L / basis, dimensionless ratio; None if price absent or basis zero | FC-041, FC-003 |

None is the unavailable/undefined result, distinguishable from Decimal zero.
The cause is derivable from inputs: missing P means unavailable valuation; zero
basis means undefined percentage. No additional financial convention is implied.
Zero P is valid numeric data. With zero Q and an available P, basis, value and
P&L are zero by the formulas, while return is undefined because basis is zero.
With zero Q and absent P, basis is zero but value/P&L remain unavailable under
FC-030; a zero holding must not fabricate a quote. With positive Q, zero C and
available P, basis is zero, value/P&L follow formulas and return remains undefined.
A negative/non-finite quote is invalid, not missing.

Hand checks: Q=10, C=100, P=120 gives 1000/1200/200/0.20; Q=0.25 gives
25/30/5/0.20; Q=10, C=100, P=80 gives 1000/800/−200/−0.20. For Q=10,
C=100, P=0, results are 1000/0/−1000/−1. No aggregate, historical or total
shareholder return is implemented.

### Legacy facade and runtime-only credentials — #30

Keep `stock.Stock` as an external facade with its existing constructor order and
keyword names, including `Stock(ticker_symbol, API_KEY, ...)` and existing
optional legacy field arguments/defaults. Keep methods `set_owned_data`,
`calculate_return`, `get_stock_info`, `get_realtime_price`, `get_price_over_time`,
`graph_performance` and static `format_mcap`. Ownership getters retain strings
for legacy callers; accepted finite numeric setter inputs become validated
Position state. Quote setters map None/`N/A` to missing; invalid nonmissing
numbers fail explicitly. `set_owned_data` validates both fields and computes a
candidate snapshot before publishing them. `calculate_return` always recomputes,
including valid→missing and valid→zero-basis transitions. Snapshot's ratio is the
single arithmetic implementation; external formatting multiplies by 100 only
for display, preserving the legacy percentage-point string boundary.

Move existing HTTP/profile/price-change orchestration to
`compatibility.stock_operations`, and market-cap/percent formatting and plotting
to `compatibility.presentation`. Preserve current request order/count and
provider behavior; do not introduce provider protocols, retries or default
policies. Facade delegates remain monkeypatchable for existing tests. Keep
synthetic chart behavior explicitly legacy and outside domain until M4; moving
it does not certify it as real history.

`API_KEY` remains a readable/writable compatibility property backed by a private
runtime-only value in the facade; constructor key remains usable for existing
callers. Repr omits that value and property. Neither Configuration nor transport
handles nor runtime keys enter domain or `__getstate__`. For newly constructed
facades the caller-supplied key is the current runtime binding. For restored
facades, saved key fields are discarded and current `load_configuration()`
rebinding occurs only at this external boundary; `require_api_key` still checks
before network work. FMP_API_KEY precedence/blank rules and sanitized diagnostics
from #7/config.py remain unchanged. Missing configuration does not prevent local
restoration/display, but blocks a later request. Existing tests asserting saved
API_KEY must be deliberately revised to assert absent credentials and runtime
rebinding, preserving all configuration/security assertions.

### Trusted synthetic state compatibility; no migration

Keep class globals `stock.Stock` and `watch_list.Watch_list` available. Their
load/save contract retains numeric holdings, metadata, ordered watchlist entries
and names. New facade serialization uses an allowlist of legacy nonsecret data
fields (the matrix below); excludes API_KEY/private runtime bindings, clients
and Configuration; and recomputes derived return on restoration. Restoration
accepts the old plain field dictionary in trusted fixtures, ignores saved
credential fields, converts holdings through the accepted boundary, and
rebuilds identity/Position only after complete validation. Nonzero holdings with
missing/malformed average cost fail visibly without writing or partially changing
state. Never replace missing nonzero holding cost with zero. Legacy unowned
state (`amount_owned='0'`, `cost_basis='-'`) retains its display state and has no
Position until ownership inputs are supplied; numeric zero quantity/cost inputs
may create a zero Position. Provider sentinels never enter domain. Formatted
market cap and provider summary percentages stay facade display fields and are
not reverse-parsed into new domain financial metrics.

Watch_list retains its root name and ordered `stocks`/`name` state, public methods
and Stock-like test doubles; it is not replaced with Portfolio. It may continue
orchestrating facade calls/rendering outside domain. Both CLI filenames, file
paths (including `daniils_stock_methodd.pkl`) and commands remain unchanged.
No new pickle loader, import utility, bulk rewrite or real user-state access is
authorized. Only trusted synthetic dictionaries and pickles generated in isolated
tests verify this contract. Existing unsafe pickle loading remains a documented
M3 limitation, not an endorsement of arbitrary deserialization or a migration.

### Caller and field contract matrix

| Caller / legacy field | Preserved surface / mapping | Owner |
| --- | --- | --- |
| Both CLIs `Stock(ticker, API_KEY)` | Root constructor and monkeypatchable methods; runtime key only | #30 |
| `test.py` | Root Stock import/provider call; current configuration delivery | #30 |
| `ticker_symbol`, `name`, `exchange` | Identity fields map to symbol/name/exchange; absent exchange remains unresolved | #26/#30 |
| `amount_owned`, `cost_basis` | String getters over numeric quantity/per-share average cost; `-` only unowned legacy state | #27/#30 |
| `current_price` | Numeric quote passed explicitly to snapshot; None/`N/A` are unavailable | #29/#30 |
| `total_return` | Ratio ×100 only for external percentage-point display; `-` for undefined/unavailable | #29/#30 |
| `market_cap`, `price_1d` through `price_5y` | Existing external display/provider-summary values; no new domain fields | #30 |
| `sector`, `country`, `currency` | Facade metadata, no inferred FX/aggregation | #30 |
| `Watch_list` | name/stocks/list order and all public methods, including `check_stock_existance`; no implicit portfolio | #30/#31 |
| Watch_list tables / `wrap_percent` | Minimum `-`/None/`N/A` safe mapping in wrap_percent, without float conversion, lands with facade; broader display integration/signs/colors retained | #30/#31 |
| Both add flows | Raw text prompts → boundary Decimal conversion → domain validation; semantic failures re-prompt; per-share cost wording clarified | #31 |
| Both refresh flows | Existing facade sequence; one pure snapshot calculation, no stale return | #30/#31 |
| `tests/test_baseline.py` | Help/command names, ordered add/remove/presence, Stock-like test doubles, unfinished method unchanged | #26/#30/#31 |
| `tests/test_fmp_configuration.py`, `tests/test_configuration_security.py` | Precedence, safe failures and runtime key delivery retained; credential serialization assertion replaced explicitly | #30/#31 |
| `tests/test_packaging.py` | Root modules/utility retained; explicit new package contents, exclusions and offline installed imports | #26/#33 |
| CLI `save_watchlist`/`load_watchlist` | Existing paths/root pickle globals; sanitized facade state tested only with trusted synthetic fixtures | #30 |

`set_owned_data` still accepts old float callers, but new CLI text preserves
precision. Financial displays retain external rounding behavior without mutating
Decimal values; no new formatting convention is approved here. A missing or
zero-basis result is `-` rather than a crash, stale percentage or fabricated zero.
These corrections, immutable Stock/Position models, conservative unknown-identity equality,
owned copied lists and exclusion of saved credentials are covered by the recorded
acceptance. Runtime implementation must follow the issue plan; no unrelated public-contract change
is authorized.

## Alternatives and consequences

Replacing root Stock with the domain class breaks constructor meaning, callers
and pickle globals. Moving every module to src adds unnecessary M1 churn.
Retaining arithmetic/credentials in a purported domain class violates isolation.
The facade preserves the transition surface with one numeric implementation and
known legacy limitations. It is deliberate transition code, not a second domain
model. Recorded owner acceptance resolves the API/equality/collection choices;
financial formulas remain those already approved.

## Review and acceptance gate

The owner accepted the package extension, field/signature/error contracts,
identity/list semantics, pure result and facade/state corrections as one coherent
proposal at `f4693ab`, with dated evidence recorded above. The #25 human acceptance
criterion is satisfied. Runtime work for #26–31/#33 and main integration #42
is now included on `main`, with completion evidence linked in the status above.
No agent merge is authorized; acceptance alone did not complete implementation
or M1. The package/field/caller contracts in this ADR remain the accepted decision.
M0 is complete on the current baseline; old issue text describing open #13 or
unconfigured mypy is historical. Strict mypy currently checks config.py with
`python -m mypy`; extending its coverage needs maintained typed implementation,
not an assumed whole-application type migration. No tests or behavior are changed
by recording this Accepted ADR.
