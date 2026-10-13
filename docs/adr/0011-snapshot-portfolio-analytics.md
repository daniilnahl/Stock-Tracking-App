# ADR-0011: Bounded snapshot portfolio analytics

## Status and acceptance gate

**PROPOSED — NOT ACCEPTED.** Prepared on 2026-10-12 for M5 — Portfolio
Analytics. The owner's request to begin M5 authorizes investigation, decomposition
and this reviewable proposal; it does not approve new financial semantics.

Runtime implementation is blocked until the owner explicitly accepts this ADR
and its accompanying proposed financial-specification additions, the owner merges
the reviewed documentation PR, and required Foundation CI passes on that merged
`main` revision. Passing PR CI or creating implementation issues does not satisfy
these gates. Agents must not merge. Record acceptance, merge and main-CI evidence
here before releasing dependent runtime issues.

This document proposes contracts and edge-case choices. It does not itself make
new formulas or conventions normative. Existing approved FC definitions remain
authoritative until the owner accepts the accompanying specification changes.

## Context and requirements

Approved SRS §§7–9, 13 and 23 require layer isolation, numeric financial values,
explicit metric definitions and known-value tests. Relevant IDs are
ARCH-001/002/006, DOM-002–004, FIN-001–005, AN-001 and the M5 exit criterion.
DATA-008 additionally requires the explicit same-currency validation below.
Financial authority is [FINANCIAL_CALCULATIONS.md](../FINANCIAL_CALCULATIONS.md),
particularly FC-001–004, FC-010, FC-020/030/040/041, FC-050/051, FC-091 and §17.

Accepted [ADR-0006](0006-domain-contracts.md) supplies immutable Stock/Position,
ordered duplicate-preserving Portfolio positions and pure `position_snapshot`.
Its arithmetic follows the caller's Decimal context, and a missing price leaves
valuation unavailable even when quantity is zero. Current Portfolio/Position/Stock
have no currency field. [ADR-0009](0009-persistence-contracts.md) preserves that
model in SQLite without quotes or currency in Portfolio records; Watchlist
records are separate display/storage data and never implicitly become Portfolios.

[ADR-0007](0007-market-provider-contracts.md) exposes optional quote currency,
explicitly rejects assuming USD and states that unknown currency cannot certify
portfolio aggregation. [ADR-0010](0010-historical-market-data-contracts.md)
supplies raw historical bars, without verified historical currency, adjusted
close or a complete-session guarantee. None of these capabilities settles M5's
currency provenance, empty/incomplete aggregates or allocation interface.

The existing implementation and tests inspected for this proposal are
`domain/calculations.py`, `domain/position.py`, `domain/stock.py`,
`domain/portfolio.py`, provider models/protocols, persistence models/protocols,
`tests/test_position_calculations.py`, `tests/test_portfolio_domain.py` and
`tests/test_sqlite_portfolios.py`. Existing arithmetic and identity behavior are
reused rather than replaced.

## Proposed Option A: explicit snapshot inputs only

Limit required M5 implementation to pure snapshot totals and ordered per-position
allocation. Add `src/stock_tracker/domain/analytics.py` inside the existing domain
package; add no new package, dependency or service layer. Domain imports only its
own modules and the standard library. It must not import providers, repositories,
configuration, compatibility, CLI, HTTP, SQL, environment or rendering libraries.

Inputs are explicitly supplied immutable rows. No provider lookup, profile
fallback, application fetching, clock access, watchlist conversion or persistence
occurs. A caller may construct these rows from known inputs, including Positions
obtained from an existing Portfolio, but supplying a Portfolio or its id does not
establish currency or quote evidence. The result evaluates supplied observations;
it does not assert that they are current, fresh, simultaneous or historically
aligned. Broader shared application-service API work remains M6/M7 under the
existing ADRs and is not introduced by this M5 plan.

### Exact proposed public shapes

All records below are frozen dataclasses with `slots=True` in `domain.analytics`.
The function is pure and returns a newly computed result on every call.

```python
@dataclass(frozen=True, slots=True)
class PositionValuationInput:
    position: Position
    current_price: Decimal | None
    cost_currency: str | None
    quote_currency: str | None

@dataclass(frozen=True, slots=True)
class PositionAllocation:
    input: PositionValuationInput
    snapshot: PositionSnapshot
    weight: Decimal | None

@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    currency: str
    positions: tuple[PositionAllocation, ...]
    total_cost_basis: Decimal
    total_market_value: Decimal | None
    aggregate_unrealized_pnl: Decimal | None
    aggregate_unrealized_return: Decimal | None

def portfolio_snapshot(
    rows: tuple[PositionValuationInput, ...], *, currency: str,
) -> PortfolioSnapshot: ...
```

Export these three records and `portfolio_snapshot` from `stock_tracker.domain`.
Add and export two errors in `domain.errors`, both subclasses of the existing
`DomainValidationError`:

```python
class SnapshotCurrencyUnavailableError(DomainValidationError): ...
class SnapshotCurrencyMismatchError(DomainValidationError): ...
```

`PositionValuationInput` validates Position type, price as actual finite
nonnegative Decimal or None, and each currency as None or a nonblank string
without surrounding whitespace. Reject floats, bools, decorated numeric text,
NaN/infinity and malformed currency text with safe field-specific
`DomainValidationError`; do not echo supplied values. No currency normalization,
ISO-code registry, exchange aliasing or inferred identifier is introduced.
Optional currency permits explicit unknown evidence to be represented, not used
to calculate an aggregate. Existing immutable Position/Stock rules remain intact.

`portfolio_snapshot` requires an actual tuple containing only validated input
rows and a nonblank `currency` string without surrounding whitespace; validate
all inputs before arithmetic. Revalidate Position type, actual finite nonnegative
Decimal price or None, and currency text at the calculation boundary rather
than trusting arbitrary caller-shaped objects. General type or
structural failures use `DomainValidationError`.

Each input row's cost currency and quote currency must be known and match the
explicit caller currency exactly. Unknown currency raises
`SnapshotCurrencyUnavailableError`; known disagreement raises
`SnapshotCurrencyMismatchError`. Check rows in supplied order, cost currency
then quote currency, stopping on the first failure. Safe messages identify the
field/category and may include the ordinal; they must not echo raw inputs.
Neither missing price nor zero quantity waives currency checks. Empty input has
no row evidence to check, but still requires explicit caller currency.

The caller supplies separate cost/quote currency assertions for every row. The
function checks consistency, not authenticity or provenance beyond those
assertions. Preserve both assertions in `PositionAllocation.input`; do not infer
cost currency from quote currency or obtain missing evidence through IO. A known
portfolio label alone does not fill missing per-row evidence.

Result records contain numeric values and retained immutable inputs only. They
are outputs rather than a second financial-calculation implementation; their
constructors must not recompute metrics, perform IO or format values. No additional
public function for accepting precomputed aggregate values is introduced.

### Ordered association and duplicates

There is exactly one `PositionAllocation` per supplied row in the same order.
Retain duplicate rows, equal known security identities, and unresolved exchanges.
Do not deduplicate, net holdings or index inputs/results by ticker. A row binds
its supplied quote and currency evidence to its own Position explicitly; no
provider identity inference occurs. This preserves ADR-0006's distinction between
known `(symbol, exchange)` identities and unresolved object identities.

### Proposed financial behavior and units

After complete validation/currency checks, call existing `position_snapshot`
for each row. Never duplicate FC-020/030/040/041 arithmetic in the new module.
These proposed aggregation choices require acceptance with the companion
financial-specification section:

- `total_cost_basis` is the sum of all position cost bases, in explicit currency.
- If every position market value is available, `total_market_value` is their sum;
  aggregate unrealized P&L is total value minus total basis. Monetary outputs
  use the same explicit currency. If any row price is None, total value,
  aggregate P&L, aggregate return and every weight are None. Keep numeric total
  cost basis and available per-position snapshots. This includes a missing-price
  zero-quantity row, preserving the conservative M1 missing-quote rule.
- With complete valuation and positive total basis, aggregate unrealized return
  is aggregate P&L divided by total basis. Otherwise it is None. It is a
  dimensionless snapshot unrealized ratio, never historical performance or total
  shareholder return.
- With complete positive total market value, each weight is that row's market
  value divided by total market value. Otherwise every weight is None. Weights
  are dimensionless ratios; zero-value rows have numeric zero weight when the
  complete portfolio total is positive. Do not assign zero weights to unknown
  valuations or normalize a subset of available values.
- Empty rows with valid explicit currency yield numeric zero total basis,
  numeric zero total value and numeric zero aggregate P&L, None aggregate return,
  and an empty allocation tuple. A nonempty fully valued zero-total portfolio
  also has unavailable weights. Numeric zero quotes remain valid observations.

All arithmetic uses Decimal and the caller's existing context. Sum from
`Decimal(0)`; do not select a new context, quantize, round for display, force
weights to sum to exactly one or adjust a residual row. Repeating ratios may be
inexact under that context. No fixed scale or rounding mode is approved here.
Formatting belongs to a future presentation boundary and must not mutate results.
Existing Decimal arithmetic exceptions remain visible; do not replace an
arithmetic failure with zero, missing data or stale results.

## Hand-derived proposed fixtures

Use two explicit rows, all currency assertions and caller currency `USD`, and
distinct known security identities. A: Q=10, C=100. B: Q=5, C=200. Thus position
bases are 1000/1000 and total basis is 2000. Expected values below are derived
from multiplication, subtraction and division, not implementation output.

| Scenario / explicit prices | Position values / P&L / ratios | Aggregate value / P&L / ratio | Ordered weights |
| --- | --- | --- | --- |
| Positive: A=120, B=240 | A: 1200 / 200 / 0.20; B: 1200 / 200 / 0.20 | 2400 / 400 / 0.20 | (0.5, 0.5) |
| Loss: A=80, B=160 | A: 800 / -200 / -0.20; B: 800 / -200 / -0.20 | 1600 / -400 / -0.20 | (0.5, 0.5) |
| Missing: A=120, B=None | A: 1200 / 200 / 0.20; B: None / None / None | None / None / None; basis remains 2000 | (None, None) |
| Valid zero prices: A=0, B=0 | A: 0 / -1000 / -1; B: 0 / -1000 / -1 | 0 / -2000 / -1 | (None, None) |

Additional required fixtures:

- Same quantities with C=0 for both rows and prices 120/240: basis=0,
  value=2400, P&L=2400, aggregate return=None, weights=(0.5, 0.5).
- Q=0 for both rows with known valid prices/currencies: basis=value=P&L=0,
  return=None, weights=(None, None). If either price becomes None, aggregate
  value/P&L/return and weights become None while basis remains zero.
- Fractional rows: A Q=0.25, C=100, P=120; B Q=0.5, C=200, P=240.
  Bases=25/100, values=30/120, P&L=5/20; aggregate basis=125, value=150,
  P&L=25, ratio=0.20; weights=(0.2, 0.8).
- No rows with explicit USD: zero sums, None ratio, no allocation rows; missing
  or malformed caller currency is rejected.
- Duplicate equal known stocks and same-symbol/different-exchange rows retain
  their ordinal valuation inputs. Unknown-exchange rows remain separate.
- Missing or conflicting currencies raise the specified typed error even for
  zero-quantity rows or absent prices; nothing is summed across currencies.

## Alternatives and consequences

**Option A, recommended:** caller-supplied currency-qualified rows permit useful
pure snapshot analytics without changing persisted holdings, provider contracts
or CLI behavior. Currency consistency is explicit; evidence acquisition remains
the caller's responsibility and the result makes no freshness claim. Conservative
missing/unknown handling can withhold otherwise partially computable outputs.

**Option B, not proposed:** add currency to Portfolio/Position and persist it.
This expands domain/schema/neutral-transfer contracts and creates provenance and
migration questions beyond the smallest snapshot calculation task.

**Option C, not proposed:** create a provider/repository application service to
fetch and align quotes. This requires approved identity, missing-currency source,
freshness, request and error policies and expands the service API reserved for
M6/M7. It is not necessary for pure calculation fixtures or M5's bounded exit.

**Option D, not proposed:** publish partial totals or omit zero-quantity missing
rows. FC-050 permits explicit partial totals, but extra completeness metadata
and semantics are unnecessary for the initial contract; omission would diverge
from the existing conservative position missing-data behavior.

## Scope exclusions and remaining blockers

No CLI commands, facade/watchlist behavior, provider requests, repository
interfaces, persistence/schema/neutral format, stored derived values, dependency,
Python version or CI configuration changes are authorized by this proposal.
No automatic conversion of watchlists into Portfolios is introduced.

Daily portfolio change is not defined by FC-070's security price-return formula.
Zero prior-price daily return, historical portfolio performance/cash flows,
benchmark alignment/normalization, risk metrics, dividends, held-position split
adjustments, FX and transaction-ledger evolution remain blocked under the
financial specification. Current raw history and period-summary metadata must
not be reused to invent these metrics. No later milestone is fully decomposed.

## Implementation and verification after acceptance

Use [#104](https://github.com/daniilnahl/Stock-Tracking-App/issues/104) for contract
acceptance, [#105](https://github.com/daniilnahl/Stock-Tracking-App/issues/105) for
the complete pure snapshot calculation (totals and ordered allocation), and
[#107](https://github.com/daniilnahl/Stock-Tracking-App/issues/107) for independent
combined isolation/restart exit evidence. Initial allocation issue #106 was
consolidated into #105 and closed as a duplicate before implementation. Totals
and weights share one small function/result contract; splitting them would
expose an intermediate result that violates the accepted weight semantics.
Runtime issues
must link the accepted contract and depend on its owner-merge/main-CI gates;
the exit audit depends on the complete calculation's owner-merged PR and required
CI. Do not dispatch overlapping interface work before that dependency is satisfied.

Follow [TESTING.md](../TESTING.md): hand-derived normal/loss/fractional fixtures,
zero/missing/currency errors, exact order/duplicates, invalid inputs, precision
without context changes, immutability, repeated recomputation and no mutation or
output. Extend domain and offline installed-wheel probes to exercise real pure
analytics with environment/network/database/data-IO/output denied. Reopen
synthetic SQLite holdings and supply explicit synthetic currency/quote inputs;
verify recomputed results without schema or stored-state changes. Do not claim
storage establishes currency, observation time or freshness.

Required commands remain targeted `python -m pytest <paths> -v`, full
`python -m pytest`, `python -m ruff check .` and configured `python -m mypy`.
Current mypy coverage is `config.py` only; this proposal does not expand it or
claim that passing it checks analytics. Required CI, secret/artifact review and
source/installed-wheel checks remain completion gates. The M5 exit evidence must
map every implemented metric to its accepted definition and known-value tests,
record deferred metrics as blocked, and await owner merge and passing main CI
before claiming milestone completion.
