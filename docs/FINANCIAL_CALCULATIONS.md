# Financial Calculations Specification

## Status

**Version:** 0.1  
**Status:** Initial normative baseline

This document defines financial semantics for the Stock Tracking App.

If a metric is not defined here, an agent MUST NOT invent its behavior. Add or approve the definition before implementation.

## Scoped EPS observation contract — 2026-10-16

The owner requested EPS observation/comparison implementation and selected
Finnhub Free's upcoming-release estimate. [ADR-0015](adr/0015-finnhub-upcoming-eps.md)
defines this additive, reported-data contract for issue #166. It does not approve
new financial arithmetic or the full M9 specification.

- **EPS-001:** an upcoming-release EPS estimate is Finnhub calendar's reported
  `epsEstimate`, associated with provider symbol and fiscal year/quarter. It is
  non-GAAP currency-per-share; currency, basic/diluted basis and vintage remain
  unknown. Release date is not fiscal period end.
- **EPS-002:** preserve the finite signed value as Decimal, with no computation
  or rounding. Null means unavailable, zero is numeric zero, negative is valid.
  Synthetic known values `1.250000000000000001`, `0` and `-0.25` remain exact.
- **EPS-003:** only explicitly unreleased (`epsActual` null) events strictly
  after a caller-supplied analysis date qualify. Missing actual is not null.
  Receipt time is not evidence publication time or a historical forecast vintage.
- **EPS-004:** matching observation identity is not a financial comparison.
  Unknown currency/share basis/vintage prevents claims of comparable EPS.
  No actual-minus-estimate, growth, annual/TTM sum, ratio, surprise percentage,
  PEG or score is defined or implemented by this scope. Historical earnings
  estimates and Premium forward consensus data are different datasets.

---

# 1. Scope

Version 0.1 defines:

- quantity
- average cost
- cost basis
- market value
- unrealized gain/loss
- unrealized return
- position weight
- daily price return
- simple historical return
- portfolio aggregation rules

It intentionally does not yet define:

- realized P&L
- tax lots
- FIFO/LIFO/specific identification
- dividends
- total-return reinvestment
- time-weighted return
- money-weighted return / IRR
- FX conversion
- Sharpe ratio
- beta
- advanced benchmark analytics

Those features are blocked until defined.

---

# 2. Numeric Representation

## FC-001 — Money

Monetary domain values SHOULD use `Decimal`.

## FC-002 — Quantity

Share quantity MUST support fractional shares.

`Decimal` is preferred.

## FC-003 — Percentages

Internal percentage returns SHOULD be represented as decimal ratios.

Example:

```text
0.125 = 12.5%
```

Formatting to `12.50%` is presentation behavior.

## FC-004 — Rounding

Domain calculations SHOULD avoid intermediate rounding.

Presentation MAY round according to display requirements.

Where persisted money requires quantization, the quantization rule must be defined with the field/schema.

---

# 3. Currency

## FC-010 — Initial currency scope

Version 1 assumes a portfolio calculation operates in one currency.

Mixed-currency portfolio aggregation is unsupported until FX conversion is implemented.

The application MUST NOT silently sum USD and non-USD values as if equivalent.

---

# 4. Position Inputs

For a position:

```text
Q = quantity held
C = average cost per share
P = current market price per share
```

Constraints:

```text
Q >= 0
C >= 0
P >= 0 when a valid quote exists
```

A missing market price is not equivalent to zero.

---

# 5. Cost Basis

## FC-020 — Position cost basis

For the initial model:

```text
cost_basis = Q × C
```

This specification treats `average_cost` as an input/state value.

It does not yet define how average cost changes after buys/sells because transaction-ledger semantics are not yet specified.

Agents MUST NOT implement tax-lot or realized-P&L behavior based on assumptions.

---

# 6. Market Value

## FC-030 — Position market value

```text
market_value = Q × P
```

If `P` is unavailable:

- market value is unavailable
- it MUST NOT be silently substituted with zero

---

# 7. Unrealized Gain/Loss

## FC-040 — Dollar unrealized P&L

```text
unrealized_pnl = market_value - cost_basis
```

## FC-041 — Percentage unrealized return

When:

```text
cost_basis > 0
```

then:

```text
unrealized_return = unrealized_pnl / cost_basis
```

If:

```text
cost_basis == 0
```

percentage unrealized return is undefined unless a future approved rule specifies otherwise.

Do not return `0%` merely to avoid division by zero.

---

# 8. Position Weight

## FC-050 — Portfolio market value

For positions with available market values:

```text
portfolio_market_value = Σ position_market_value
```

However, if any held position lacks a required market price, the application MUST NOT silently present an incomplete total as a complete portfolio value.

It may either:

- mark total as unavailable, or
- explicitly mark the value as partial

The chosen UI behavior must be clear.

## FC-051 — Position weight

When complete portfolio market value is available and greater than zero:

```text
position_weight = position_market_value / portfolio_market_value
```

Weights should sum to approximately 1 subject to display rounding.

---

# 9. Historical Prices

## FC-060 — Historical source

Historical returns and charts MUST use actual provider historical data.

Summary return percentages MUST NOT be reverse-engineered into synthetic historical price points.

## FC-061 — Adjusted vs raw prices

For return calculations across time, use an adjusted price series when the provider supplies a trustworthy adjusted close and the calculation is intended to account for split effects.

Raw OHLC values may still be shown for charting/trading-price inspection.

Dividend treatment is NOT yet defined as total return.

Therefore, adjusted-close usage must not be described as dividend-reinvested total return unless the provider semantics and product requirement explicitly support that interpretation.

## FC-062 — Missing dates

Markets do not trade every calendar day.

Historical calculations should use available trading observations rather than invent weekend/holiday prices.

If a requested boundary date has no observation, the exact selection rule must be defined by the feature (for example, prior available trading close).

Do not silently invent interpolation.

---

# 10. Daily Price Return

## FC-070 — Daily price return

Using two consecutive valid trading observations:

```text
R_t = (P_t / P_(t-1)) - 1
```

The selected price field must be consistent across both observations.

Missing prior data means the return is unavailable.

---

# 11. Simple Historical Return

## FC-080 — Simple return

Given starting price `P0` and ending price `P1`:

```text
simple_return = (P1 / P0) - 1
```

Requirements:

```text
P0 > 0
```

If `P0 <= 0` or either price is unavailable, the return is undefined.

---

# 12. Portfolio Return

## FC-090 — Current limitation

A mathematically correct portfolio performance return becomes ambiguous when:

- positions are purchased at different dates
- cash enters/leaves the portfolio
- partial sales occur
- dividends occur

Therefore:

**Do not implement a historical "portfolio return" across cash flows until the project explicitly chooses a methodology.**

Candidate future methodologies include:

- simple return for a static portfolio
- time-weighted return (TWR)
- money-weighted return / IRR

The choice requires a specification update.

## FC-091 — Aggregate unrealized return

For a snapshot portfolio where all required values are available, an aggregate unrealized return MAY be calculated as:

```text
total_cost_basis = Σ position_cost_basis
total_market_value = Σ position_market_value
aggregate_unrealized_pnl = total_market_value - total_cost_basis
aggregate_unrealized_return = aggregate_unrealized_pnl / total_cost_basis
```

only when:

```text
total_cost_basis > 0
```

This metric is a snapshot unrealized return, not a time-weighted historical performance measure.

The UI must name it accordingly.

---

# 13. Corporate Actions

## FC-100 — Stock splits

When historical adjusted price data is available, return calculations should avoid treating stock splits as economic gains/losses.

Position quantity/cost-basis adjustments caused by real corporate actions are not yet specified for a transaction ledger and must not be invented.

## FC-101 — Dividends

Dividend income and dividend-reinvestment return are not defined in version 0.1.

Do not label price return as total shareholder return.

---

# 14. Cost-Basis Method

## FC-110 — Current model

The current `average_cost` value is treated as authoritative input/state.

## FC-111 — Future transaction ledger

Before transactions are introduced, the project must define:

- buy transaction representation
- sell transaction representation
- fees
- realized P&L
- average-cost update rules
- tax-lot method if applicable
- stock split adjustments
- dividend/cash representation

Do not create behavior for these implicitly.

---

# 15. Benchmark Comparison

Benchmark comparison is not yet fully defined.

Before implementation, define:

- benchmark symbol
- comparison date range
- adjusted/raw price field
- missing-date alignment
- starting-value normalization
- whether dividends are included
- whether portfolio cash flows exist

Until then, agents may build infrastructure but MUST NOT present a benchmark-performance metric as finalized.

---

# 16. Risk Metrics

The following are intentionally undefined in version 0.1:

- volatility annualization
- Sharpe ratio
- risk-free rate source
- beta
- covariance
- correlation lookback
- maximum drawdown conventions

Do not implement these as production metrics until formulas and data conventions are approved.

---

# 17. Missing Data Rules

Missing data MUST remain distinguishable from zero.

Examples:

```text
price unavailable != price 0
return unavailable != return 0%
volume unavailable != volume 0
```

Analytics depending on missing required inputs must either:

- return an explicit unavailable result, or
- return a typed error according to the service contract

They must not silently fabricate values.

---

# 18. Financial Test Fixtures

Every metric implementation must include hand-verifiable tests.

Example:

```text
quantity = 10
average_cost = 100
current_price = 120

cost_basis = 1000
market_value = 1200
unrealized_pnl = 200
unrealized_return = 0.20
```

Also test:

- zero quantity
- zero cost basis
- unavailable price
- fractional quantity
- negative-return scenario

Expected results must be derived from this specification, not generated by the implementation under test.

---

# 19. Open Decisions

These decisions require future approval before related features are implemented:

1. Exact money quantization policy.
2. Supported currencies and FX source.
3. Transaction ledger model.
4. Cost-basis update method.
5. Realized P&L method.
6. Dividend treatment.
7. Historical portfolio performance methodology.
8. Benchmark calculation convention.
9. Trading-calendar source.
10. Risk metric formulas and annualization assumptions.
11. Risk-free rate source for Sharpe ratio.
12. Corporate-action handling for held positions.

These are deliberate blockers, not invitations for agent interpretation.

---

# 20. Publication and Units

Published for [issue #9](https://github.com/daniilnahl/Stock-Tracking-App/issues/9)
in M0 — Security & Foundation from the supplied primary-checkout v0.1 draft.
Sections 1–19, all FC requirement IDs, formulas and the known-value fixture are
preserved. These publication notes do not approve any open decision or certify
the legacy implementation. See [SRS](../SRS.md), [agent policy](../AGENTS.md)
and [testing policy](TESTING.md).

The formulas above have the following units:

| Input or result | Unit |
|---|---|
| `Q` | Shares, including fractional shares |
| `C`, `P`, `P0`, `P1`, `P_t`, `P_(t-1)` | Currency per share, in a consistent currency |
| Position/portfolio cost basis, market value and unrealized P&L | The portfolio's single currency |
| Unrealized return, aggregate unrealized return, position weight, daily and simple return | Dimensionless decimal ratio; multiply by 100 only for percentage display |

The label "Dollar unrealized P&L" in FC-040 does not authorize FX conversion;
FC-010 still limits aggregation to one currency. The section 18 example gives
`10 × 100 = 1000`, `10 × 120 = 1200`, `1200 - 1000 = 200`, and
`200 / 1000 = 0.20` (20% at presentation).

Exact quantization scale and rounding mode remain unapproved under FC-004 and
section 19. Accepted ADR-0009 defines M3's field mappings as lossless Decimal
text, preserving exponent/trailing-zero spelling without quantization; the
[M3 completion evidence](milestones/m3-exit-evidence.md) verifies those mappings
and restart recomputation. This implementation adds no financial rounding rule.
Benchmark normalization and
alignment, portfolio cash-flow methodology and risk conventions remain blocked
under sections 12, 15, 16 and 19. Missing or zero-denominator cases not fully
specified by this baseline require an approved definition before implementation;
publication must not supply a default. In particular, FC-070 does not yet define
a zero prior-price rule, and FC-051 authorizes weights only for a complete,
positive portfolio value.

---

# M5 snapshot clarification — accepted 2026-10-12

**Accepted, 2026-10-12.** The owner instructed "PR merged, continue work" after
the Master presented complete Option A in
[PR #108](https://github.com/daniilnahl/Stock-Tracking-App/pull/108) for approval.
This accepts the additive snapshot choices below and
[ADR-0011](adr/0011-snapshot-portfolio-analytics.md), tracked by
[issue #104](https://github.com/daniilnahl/Stock-Tracking-App/issues/104).
Owner merge was independently verified at `dddaeaf681cba6fe218f740e40be0df3b4a9318b`;
required PR and main Foundation CI passed, as recorded in ADR-0011. The bounded
snapshot clarification is now normative. Existing formulas and unrelated open
decisions remain unchanged; publication or merge alone would not approve them.

The accepted required M5 subset is snapshot cost basis, market value, unrealized
P&L, aggregate unrealized ratio and ordered allocation. Each input row supplies
a Position, a Decimal price or None, and separate cost/quote currency assertions.
The caller also supplies the aggregate currency. Require known, exact matching
currency on every row, including zero-quantity or missing-price rows; unknown or
conflicting currency produces the ADR's typed error before arithmetic. Currency
consistency checks do not establish authenticity, freshness or observation time.
Do not infer cost currency from quote currency, assume USD, use saved display
metadata as evidence, perform FX, or combine unlike currencies.

Reuse FC-020/030/040/041 for each position and FC-050/091 for totals. Monetary
outputs use the explicit single currency; returns and weights are dimensionless
ratios. Retain every row and its order, including duplicates and unresolved
exchanges. Inputs bind prices to individual Positions; ticker alone is not a
global identity or a deduplication key.

If any row price is None, including a zero-quantity row, total market value,
aggregate P&L, aggregate return and all weights are None. Total cost basis remains
numeric after successful currency validation. No partial value is published as
a complete total. With complete valuation, aggregate return is P&L divided by
total basis only when basis is positive; otherwise it is None. With complete
positive market value, each weight is its position value divided by total value;
otherwise every weight is None. A zero-value row has zero weight only when the
complete total is positive.

Empty input with explicit valid currency has zero basis, market value and P&L,
undefined aggregate return and no allocation rows. A complete nonempty portfolio
with zero market value has undefined weights. Zero prices remain valid numeric
observations and differ from absent prices.

Use Decimal arithmetic under the caller's context, without display rounding,
quantization, context changes or residual weight adjustment. Arithmetic errors
remain errors. This snapshot is not historical performance, a total shareholder
return or an assertion that supplied prices are current.

Hand-derived example: A has Q=10, C=100, P=120; B has Q=5, C=40, P=60.
In a single explicitly supplied currency, bases are 1000 and 200, values 1200
and 300, and P&L 200 and 100. Totals are basis=1200, value=1500, P&L=300,
unrealized ratio=0.25, with ordered weights (0.8, 0.2). Missing B's price leaves
basis=1200 and aggregate valuation/P&L/ratio/weights unavailable. More zero,
loss, fractional and precision fixtures are required by ADR-0011.

Daily portfolio change, zero-prior-price daily returns, benchmark comparison,
historical cash-flow performance, dividends, split-adjusted holdings, FX and
risk metrics remain blocked under sections 12–19. They are optional candidates
in SRS M5, not metrics implemented by this accepted subset.

---

# 21. Legacy Discrepancies and Milestone Ownership

**M4 reconciliation (2026-10-12):** [M4 completion evidence](milestones/m4-exit-evidence.md)
records genuine provider raw OHLCV retrieval and chart replacement under accepted
[ADR-0010](adr/0010-historical-market-data-contracts.md). Charts use actual observed
session dates and raw closes as unconnected markers, preserving sparse dates
without interpolation. Decimal observations stay numeric and exact until the
plotting boundary converts closes to finite floats; plots identify currency as
unavailable and warn that splits may appear as discontinuities. The raw mapping
sets `adjusted_close=None`. No historical return, dividend-reinvestment, FX or
portfolio metric is computed, and no financial definition or rounding policy
changes. Earlier future-M4 statements and the table below describe dated snapshots.

**M3 reconciliation (2026-10-06):** structured SQLite state now preserves exact
Decimal holdings/quotes and zero/missing/unowned distinctions for Portfolio
and both CLI namespaces. Imported/restored snapshots use the existing domain
calculations; no derived return or runtime credential is stored. M3 also repairs
display of accepted empty/literal percentage metadata without changing formulas.
The table below remains a historical M0 snapshot, supplemented by M1 and M3
evidence. Unapproved quantization and later financial conventions remain open.

**M1 reconciliation (2026-10-04):** the table below preserves the M0 publication
snapshot. M1 now supplies numeric domain Position/PositionSnapshot values and
one pure Decimal calculation in `src/stock_tracker/domain/calculations.py` for
FC-020/030/040/041. The root Stock facade delegates to that calculation; its
legacy `cost_basis` string getter still means average cost per share, while
snapshot `cost_basis` means `Q × C`. Both CLI ownership prompts preserve decimal
text and identify average cost per share. Missing-price and zero-basis results
are explicit `None` values, displayed as `-`; display does not mutate domain
values. See the [M1 completion review](milestones/m1-exit-evidence.md#completion-review--2026-10-04)
for known-value, precision, recomputation and nonmutation tests on `main`.
At the M1 review, legacy table labels/provider summaries and approximate charts
were assigned to M4/M6; M4 has since replaced approximate charts as recorded above.
Table-label/CLI V2 work remains M6; portfolio aggregation and unapproved
conventions remain later M5 work. This
reconciliation changes no FC definition, rounding policy or open decision.

These observations describe the tracked legacy code at publication. They are
future work under [SRS §23](../SRS.md#23-milestones), not approved financial
semantics or repairs included in M0.

| Legacy behavior | Specification gap | Later milestone ownership |
|---|---|---|
| [Stock](../stock.py) stores quantity, price, per-share cost and returns as strings; `format_mcap` stores formatted market-cap text. | FIN-001–003 and FC-001–004 require numeric domain values and presentation-only formatting/rounding. | M1 — Domain Refactor; M6 — CLI V2 for presentation integration |
| `Stock.set_owned_data` calls its per-share purchase-price input `cost_basis`. | FC-020 defines position cost basis as `Q × C`; the legacy name must not redefine that formula. | M1 — Domain Refactor |
| `Stock.calculate_return` uses floats, multiplies a price-based ratio by 100, rounds to two places and stores a string. It updates only for positive cost and quantity; missing prices can fail conversion and other paths can retain the previous value. | FC-003/004 define an internal ratio without intermediate rounding; FC-030/041 and section 17 distinguish unavailable values and undefined zero-cost return. The legacy gate does not define future zero-quantity semantics. | M1 — Domain Refactor; M5 — Portfolio Analytics for specified snapshot metrics |
| [Watch_list.wrap_percent](../watch_list.py) consumes percentage-point strings and converts them to floats; `show_stocks` labels the legacy value "Your Total Return". | Presentation must follow FC-003; FC-091 distinguishes snapshot unrealized return and FC-101 forbids labeling price return as total shareholder return. | M6 — CLI V2, after M1/M5 contracts stabilize |
| `Stock.get_price_over_time` rounds provider summary percentages; `graph_performance` reconstructs prices from them, uses calendar-day offsets and labels the axis USD. | FC-060–062 and DATA-003 require genuine provider history and explicit price/date conventions; FC-010 does not authorize a USD assumption or mixed-currency aggregation. | M4 — Historical Market Data; M6 — CLI V2 for display |

No runtime metric, chart, domain model or legacy behavior is changed by this
publication. M5 remains blocked wherever the relevant formula or convention is
undefined; benchmark, dividend, cash-flow and risk features are not marked ready.
