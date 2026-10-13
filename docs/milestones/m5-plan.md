# M5 Portfolio Analytics implementation plan

Status: **COMPLETE — required issues closed; owner merges, review, CI and milestone closure verified**.
Snapshot: 2026-10-12. Baseline: `a0dc9432178e2037b719269b04c758bd142df9db`,
owner-merged M4 documentation reconciliation PR #103.
Parent: [M5 — Portfolio Analytics](https://github.com/daniilnahl/Stock-Tracking-App/milestone/6).
Contract: [Accepted ADR-0011](../adr/0011-snapshot-portfolio-analytics.md).
Completed implementation main: `11f7333abdac830e139dd74354c87b30fe4cd45d`.
Earlier analysis, dispatch and pending-gate statements remain historical snapshots;
the completion review below supersedes them.

The owner requested the supplied Master Engineering workflow for M5, superseding
the supplied document's M2 placeholders. The Master owns planning and independent
review; implementation is delegated only after dependencies stabilize. No model
or reasoning preference is inferred from older milestone records. Agent merges
remain prohibited. Beginning the milestone does not approve new product rules.

## Repository analysis and proposed scope

Approved SRS §23 M5 requires every implemented metric to have a normative formula
and known-value tests. FC-020/030/040/041 position snapshots already exist, with
Decimal money/ratios, explicit missing prices, zero-basis unavailability and no
IO. Portfolio preserves ordered duplicates and exchange-aware identity. SQLite
preserves ownership across restart, but Portfolio records have no quote or
currency evidence. Quote currency may be unknown. Watchlists are separate from
Portfolios and their display metadata cannot certify currency or freshness.

FC-050/051/091 define snapshot totals and allocation; their implementation needs
explicit currency, binding, missing/empty/zero and public-result choices. Proposed
Option A in ADR-0011 uses supplied immutable Position/price/cost-currency/quote-
currency rows, validates exact currency consistency before arithmetic, preserves
order and duplicates, reuses position_snapshot and returns complete totals or
explicit unavailability. No price fetching, service API, storage or CLI changes
are proposed. Broader shared application services remain M6/M7.

Proposed required metrics: total cost basis, total market value, aggregate
unrealized P&L, aggregate unrealized ratio and ordered allocation. The proposal
selects this bounded subset from SRS's optional metric candidates. Currency
assertions come from the caller; calculations check consistency without claiming
authenticity, observation time or freshness. No default USD, FX, transaction
ledger, quantization or historical performance methodology is introduced.

## Dependency and delegation map

| Issue | Objective | Status | Dependency / blocker | Agent | PR / review |
| --- | --- | --- | --- | --- | --- |
| [#104](https://github.com/daniilnahl/Stock-Tracking-App/issues/104) | Approve snapshot contracts and financial additions | Accepted and owner-merged; gates passed | None | `m5_readiness_audit` drafted ADR; Master drafted financial proposal/plan; `m5_contract_review` independent review | [#108](https://github.com/daniilnahl/Stock-Tracking-App/pull/108); no remaining independent review findings; PR/main CI passed |
| [#105](https://github.com/daniilnahl/Stock-Tracking-App/issues/105) | Complete pure totals and ordered allocation | Closed; owner-merged | None; required PR/main CI passed | `m5_readiness_audit`; `m5_contract_review` independent review | [#109](https://github.com/daniilnahl/Stock-Tracking-App/pull/109); reviewed head `3f197ec`; merge `9b94c1e` |
| [#107](https://github.com/daniilnahl/Stock-Tracking-App/issues/107) | Independent source/wheel isolation, restart and exit evidence | Closed completed; owner-merged | None; required PR/main CI passed | `m5_contract_review`; `m5_readiness_audit` independent review | [#110](https://github.com/daniilnahl/Stock-Tracking-App/pull/110); reviewed head `1a247b05`; merge `11f7333` |

Initial #106 allocation issue was consolidated into #105 and closed as a duplicate
during planning. Totals and weights share one small pure function/result contract;
separate implementations would expose an intermediate result with incorrect
allocation semantics. The final hierarchy is three bounded issues, with one
branch/PR per objective. #105 uses `feature/105-snapshot-analytics`, based on the
verified owner merge of #108. Its implementing agent follows the accepted contract.

## Approval decisions and deferred metrics

The owner accepted caller-supplied currency evidence,
all-row exact currency checks, positional quote association, unavailable totals
on any missing price (including zero quantity), empty/zero behavior, numeric
result/error shapes and the bounded snapshot-only required scope. See accepted
ADR-0011 and the normative M5 financial clarification. Existing formulas and
unrelated open financial conventions remain authoritative.

Daily portfolio change, daily return with zero prior price, historical portfolio
performance, benchmark comparison, volatility, maximum drawdown, Sharpe, beta,
correlation, dividends, held-position splits and FX remain blocked on their own
approved formulas/data conventions. These optional candidates are recorded here
for future specification work; they are not silently counted as implemented or
required by this accepted subset. They need explicitly assigned issues if later
approved as required scope. Do not claim all M5 exit gates passed until all required
issues/PRs in the accepted subset complete and main CI/evidence pass.

## Verification and review

Preserve Python 3.11/3.12, canonical pinned pip/pyproject dependencies, existing
package boundaries and configured mypy scope. Use targeted pytest, full pytest,
Ruff, configured mypy and pip check. Expected financial values are hand-derived;
tests remain offline, clocks fixed and databases temporary. Domain calculation
probes must deny infrastructure/output within pure computation, while separate
setup/restart steps may use temporary SQLite through the existing repository.
Installed-wheel probes verify actual packaged calculations and module origins.

The initial sandbox attempt to create a Python 3.12 environment failed in
ensurepip; approved execution reproduced the canonical setup successfully using
the existing Python 3.12.10 installation. No system software, runtime range or
dependency pins changed. An older checkout's Python 3.11 virtual environment
could not start its base interpreter; it was not used. Current proposal checks
and later runtime/CI checks must be reported separately, without treating baseline
tests as evidence of unimplemented M5 metrics.

Proposal verification on Python 3.12.10: focused position/Portfolio/SQLite/provider
models/domain isolation/packaging/hygiene tests passed **536 tests in 53.78s**;
full `python -m pytest -q` passed **2170 tests in 108.01s**. `python -m ruff
check .`, configured `python -m mypy` (one source file) and `python -m pip check`
passed. Independent `m5_contract_review` found no formula or architecture errors;
its totals/allocation task-split finding was resolved by consolidating #106 into
#105, and its boundary-field clarification was applied. Final independent review
of all three documents reported no remaining actionable findings. Staged hygiene
passed **8 tests in 9.41s** and `git diff --cached --check` passed. A sandbox-only
staging/temp-directory attempt was denied before tests could set up; the same
commands passed under approved execution. Exact proposal PR CI will be recorded
with submission/review evidence.
These checks verify the unchanged runtime baseline, not future M5 behavior.
The owner then instructed "PR merged, continue work". Verified owner merge of
#108 is `dddaeaf681cba6fe218f740e40be0df3b4a9318b`; final PR Foundation
[38343204134](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38343204134)
and post-merge main Foundation
[38343278997](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38343278997)
both completed successfully. This releases #105, without authorizing agent
merges or undefined metrics. M5 is not complete; runtime implementation and
independent exit evidence remain required.

## Snapshot implementation — issue #105

[PR #109](https://github.com/daniilnahl/Stock-Tracking-App/pull/109) adds the
accepted immutable input/result records, safe currency errors and pure numeric
totals/allocation, reusing position_snapshot. No provider/service/CLI/schema,
dependency or Python-version change is introduced. Source and installed-wheel isolation
probes exercise actual calculations under infrastructure guards, with explicit
persistence-import refusal and hand-derived weights. Inputs retain row order,
duplicates, separate currency assertions and Decimal precision.

On Python 3.12.10, focused analytics/position/isolation/packaging verification
passed **107 tests in 30.73s**; the final implementation full suite passed
**2242 tests in 82.00s**. Ruff, configured mypy (config.py only), pip check,
staged diff checks and **8 hygiene tests in 8.66s** passed. Independent review
passed 72 analytics cases and found no actionable defects, including final probe
strengthening. These verify #105, not #107's future combined restart/exit audit.
The owner instructed "PR merged, continue work". PR #109's reviewed head is
`3f197ec9995edf13d72ec672f80a7ffdaeeac433`, owner-merged at
`9b94c1e68bec37ebb9439d9b3815d44ba2e9b135`. Its required
[PR Foundation run 38344185574](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38344185574)
and [main Foundation run 38347202332](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38347202332)
passed all five checks; #105 is closed. #107 was dispatched after these gates
passed on `test/107-snapshot-exit-audit`. See
[M5 exit evidence](m5-exit-evidence.md) for the combined audit and remaining gates.
No agent merge is authorized and milestone completion is not claimed.

## Independent combined audit — issue #107

The audit adds separate source/wheel write/read/read processes using actual
SQLitePortfolioRepository and portfolio_snapshot, explicit supplied currencies/
observations and reusable proven domain guards. Exact decoded and stored Decimal
spellings, duplicate order, values/weights, unavailable/currency cases and database
bytes/schema are checked. Existing cold import probes and CLI regressions remain.
No runtime or financial contract is changed.

After the independent review's exact decoded-value assertion correction, focused
audit/financial/persistence/isolation/packaging tests passed **172 in 33.96s**;
full pytest passed **2243 in 84.82s** on Python 3.12.10. Ruff, configured mypy,
pip check and staged diff checks passed; staged hygiene passed **8 in 8.87s**.
See [exit evidence](m5-exit-evidence.md) for metric/requirement/fixture mapping.
Final audit PR/head review, required PR/main CI, owner merge, issue closure and
milestone completion remain pending.

## Completion review — 2026-10-12

The owner merged audit PR #110 and instructed the Master to continue. Reviewed
head `1a247b05a786d356ce2fb169b9005ed3d4f2d0c4` and merged main
`11f7333abdac830e139dd74354c87b30fe4cd45d` share tree
`eba5b822314e4cb87daacadf136889cabc476734`. All five required jobs passed in
[audit PR CI 38349919901](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38349919901)
and [main CI 38353960939](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38353960939).
Required #104/#105/#107 are closed completed; #106 remains a closed duplicate.
Master merged-main focused verification passed **180 tests in 49.10s**.

The accepted required snapshot subset has normative definitions and independent
known-value, guarded source/wheel and exact restart evidence. No required M5
work is deferred. Undefined optional analytics remain blocked as recorded above.
Independent final accepted-scope review passed. GitHub milestone 6 is closed with
zero open and seven closed items (three required issues, the #106 duplicate and
three merged PRs). The
[persisted completion report](https://github.com/daniilnahl/Stock-Tracking-App/issues/107#issuecomment-6139320638)
and [M5 exit evidence](m5-exit-evidence.md) record satisfied acceptance criteria,
exit evidence and closure. This documentation record has separate verification/PR
checks, not an unmet runtime completion gate, and introduces no requirement change.
