# M5 Portfolio Analytics exit audit

Audit date: **2026-10-12**. Parent: [M5 — Portfolio Analytics](https://github.com/daniilnahl/Stock-Tracking-App/milestone/6).
Audit issue: [#107](https://github.com/daniilnahl/Stock-Tracking-App/issues/107).
Implementation baseline: owner-merged `9b94c1e68bec37ebb9439d9b3815d44ba2e9b135`.
**Status: IN PROGRESS — audit PR, independent review, owner merge, required CI
and audit issue closure remain pending. M5 completion is not claimed.**

## Accepted scope and prerequisite evidence

SRS §23 M5 exit requires every implemented metric to have a normative formula
and known-value tests. The owner accepted the bounded snapshot subset in
[ADR-0011](../adr/0011-snapshot-portfolio-analytics.md) and the normative
[M5 financial clarification](../FINANCIAL_CALCULATIONS.md#m5-snapshot-clarification--accepted-2026-10-12).
Inputs explicitly bind one Position, price and separate cost/quote currency
assertions per row; the caller supplies the aggregate currency. The function
checks exact consistency, not currency authenticity, observation time or freshness.
No provider fetching, Portfolio/watchlist conversion or new application service
is part of M5. Decimal values remain numeric; formatting and unrelated financial
conventions retain their existing boundaries.

| Issue | Reviewed deliverable | Owner merge / prerequisite verification |
| --- | --- | --- |
| [#104](https://github.com/daniilnahl/Stock-Tracking-App/issues/104) | Contract and financial additions, [PR #108](https://github.com/daniilnahl/Stock-Tracking-App/pull/108), reviewed head `20e8a8a77985208e4a63efa29fa155c3c0318433` | Owner merge `dddaeaf681cba6fe218f740e40be0df3b4a9318b`; required PR/main CI passed as recorded in ADR-0011 |
| [#105](https://github.com/daniilnahl/Stock-Tracking-App/issues/105) | Complete pure snapshot totals and ordered allocation, [PR #109](https://github.com/daniilnahl/Stock-Tracking-App/pull/109), reviewed head `3f197ec9995edf13d72ec672f80a7ffdaeeac433` | Owner merge `9b94c1e68bec37ebb9439d9b3815d44ba2e9b135`; issue closed; required PR/main CI passed |
| [#107](https://github.com/daniilnahl/Stock-Tracking-App/issues/107) | Independent combined source/wheel restart, isolation and exit evidence | This audit; review/PR/merge/main-CI/closure gates pending |

Allocation issue #106 was consolidated into #105 and closed as a duplicate before
implementation. It is not a separately missing deliverable. The Master verified
PR #109's [required PR Foundation run 38344185574](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38344185574)
and [post-merge main run 38347202332](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38347202332)
completed successfully with all five checks before dispatching #107. These are
prerequisite evidence, not this audit's future PR/main CI.

## Formula and requirement map

| Implemented result / requirement | Normative definition and independent evidence |
| --- | --- |
| Total cost basis; DOM-002/004, FIN-001–005, AN-001 | FC-020/091: sum `Q × C`; existing pure `position_snapshot` and new `portfolio_snapshot`; `test_snapshot_analytics.py` and combined restored holdings fixture |
| Total market value; FC-030/050 | Sum `Q × P` only with complete valuation; any missing row price withholds total, including zero quantity; source/wheel fixture preserves available per-position snapshots |
| Aggregate unrealized P&L; FC-040/091 | Complete total value minus total basis; positive/loss/zero-price cases are hand-derived, never historical or realized P&L |
| Aggregate unrealized ratio; FC-003/041/091 | P&L divided by positive basis; `None` for zero basis or incomplete valuation; no percentage display stored |
| Ordered allocation; FC-051 | Each position value divided by complete positive total; zero rows get zero only when total is positive; zero/incomplete totals yield unavailable weights; duplicates and unresolved identities remain separate |
| DATA-008, FC-010, §17 missing-data rules | Explicit matching cost/quote/aggregate currency required on every row; typed unknown/mismatch errors even on missing-price zero-quantity rows; no database-derived currency or implicit USD |
| ARCH-001/002, TEST-001–005 | Cold domain and combined audit calculations execute under independently proven import/environment/network/SQL/data-IO/output guards in source and installed wheel |
| PERS-005/007, DOM-004 | Real temporary SQLite repository write/read in separate processes; exact Decimal spelling, order and duplicates preserved; schema version 1, stored rows and database bytes unchanged by calculations |
| GH-004/005, M5 exit | Bounded #104/#105/#107 trace, independent review, required exact PR/main CI and owner merge gates; audit completion evidence remains pending |

## Combined scenario and hand-derived values

`tests/analytics_exit_probe.py` writes a real Portfolio to temporary SQLite,
then each independent read process restores it through the actual repository.
Both `test_analytics_exit.py` and the offline installed-wheel test run write,
read and a second read with `python -I`. Actual domain/calculation/repository
module origins must lie in the explicit source or wheel root. The wheel is built
and installed offline with no dependencies fetched; test helpers remain outside
its exact runtime payload.

The holdings are two duplicate A/NASDAQ rows, each Q=0.2500, C=100.00;
B/NASDAQ Q=0.5, C=200; A/NYSE Q=1, C=50; and two independent unresolved A rows
with Q=0E-30 and costs -0.00 / 100.123456789012345678901234567890. Inputs supply
USD separately for cost, quote and aggregate, after holdings restoration.
The database contains no Portfolio/Position currency or price fields.

| Supplied prices, in row order | Basis / value / P&L / ratio | Ordered weights |
| --- | --- | --- |
| 120, 120, 240, 60, 0, 0 | 200 / 240 / 40 / 0.2 | 0.125, 0.125, 0.5, 0.25, 0, 0 |
| 80, 80, 160, 40, 0, 0 | 200 / 160 / -40 / -0.2 | 0.125, 0.125, 0.5, 0.25, 0, 0 |
| All valid zero prices | 200 / 0 / -200 / -1 | All unavailable |
| Final zero-quantity price missing | 200 / unavailable / unavailable / unavailable | All unavailable |

Changing only the supplied costs to zero in new immutable Positions produces
basis=0, value=P&L=240 and undefined aggregate ratio. Empty supplied rows produce
zero sums, undefined ratio and no allocations. Missing/conflicting cost or quote
currency on the final zero-quantity missing-price row raises the specified typed
error. Repeated calculations produce fresh equal results without mutating holdings.
None of these alternative observations or derived results is saved.

The child installs and tests its own network/pickle guards for persistence
setup. Within pure computation it reuses `isolated_domain()` from the existing
cold domain probe, which proves import, environment, network, SQLite, data-open/
read/write and output guards before yielding. Persistence modules already loaded
by setup are temporarily unavailable during calculations. Setup/schema checks
use the synthetic local database; no open database handle crosses
the calculation boundary. Import-loader code reads remain possible, as in the
existing cold domain probe; ordinary data IO is denied. Byte and exact schema/input-row comparisons occur
before and after computation, and again across processes. Existing full CLI,
schema, persistence and financial unit regressions remain required.

## Verification and unresolved gates

Local verification on canonical `.venv` Python **3.12.10**:

| Command actually executed | Result |
| --- | --- |
| `python -m pytest tests/test_analytics_exit.py tests/test_snapshot_analytics.py tests/test_position_calculations.py tests/test_sqlite_portfolios.py tests/test_domain_isolation.py tests/test_packaging.py -q --tb=short` | **172 passed in 33.96s**, after exact restored-value review fix |
| `python -m pytest -q --tb=short` | **2243 passed in 84.82s** |
| `python -m ruff check .` | Passed |
| `python -m mypy` | Passed; one source file |
| `python -m pip check` | Passed |
| `python -m pytest tests/test_repository_hygiene.py -q --tb=short` | **8 passed in 8.87s**, with the audit files staged |
| `git diff --cached --check` | Passed |

Independent preliminary review identified an audit gap: SQL text assertions did
not independently establish decoded Position spelling. The audit now compares
all six restored quantity/cost/identity tuples against literal expected values,
including trailing zeros, signed zero, exponent and long precision. The affected
source/wheel command and full verification above passed after that correction.
No runtime defect or runtime patch was needed. Final-head review remains pending.
The test runs used approved execution for pytest temporary-directory access;
no system software or toolchain change was made.
Configured mypy checks `config.py` only and does not certify analytics typing.
No live provider, real user database, credential or current observation is used.
Runtime implementation, schema, CLI, dependency pins and Python range are unchanged
by #107; only tests and task-relevant documentation are changed.

Final audit head/PR, independent review, required PR CI, owner merge/main CI,
issue closure and milestone completion review remain pending. Agents must not
merge or substitute prerequisite checks for these final gates.

## Deferred financial work

Daily portfolio change, zero-prior-price daily return, historical/cash-flow
performance, benchmark alignment/normalization, risk metrics, dividends,
held-position split adjustments, FX and transaction-ledger evolution remain
undefined or blocked under financial sections 12–19. SRS lists these as optional
candidates; the owner-approved required subset excludes them. They are not
counted as completed metrics or required issues. If later approved as required
work, create explicitly assigned specification/implementation issues first.
