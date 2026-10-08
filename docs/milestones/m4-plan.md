# M4 Historical Market Data implementation plan

Status: **retrieval owner-merged and verified; #90 cache PR ready for hosted checks and owner review**.
Snapshot: 2026-10-08. Planning baseline: `534a178` (owner-merged M3 audit PR #86).
Current runtime branch baseline: `9218229` (owner-merged retrieval PR #96).
Parent: [M4 — Historical Market Data](https://github.com/daniilnahl/Stock-Tracking-App/milestone/5).
Contract: [Accepted ADR-0010](../adr/0010-historical-market-data-contracts.md).

The owner requested the supplied Master Engineering workflow for M4, superseding
its M3 placeholders. All delegated agents use **`gpt-6.1-sol`, reasoning effort
`low`**. The Master owns planning and independent review; agents own bounded
implementation. Issue creation is not contract acceptance. No agent merge is
authorized under AGENTS.md; owner merges and required CI remain dependency gates.

## Repository analysis

Approved SRS §23 M4 requires OHLCV retrieval, explicit adjusted/raw usage,
historical caching, replacement of synthetic charts and date-range selection.
Its exit criterion is: **historical charts use genuine provider market history**.

Accepted ADR-0007 already supplies immutable Decimal `PriceBar`, date-only
exchange-session meaning, the separate `HistoricalMarketDataProvider` protocol,
safe FMP transport and bounded retries. The FMP adapter has no history operation.
The approved history TTL is `0.0`, with stale fallback disabled; that is a disabled
cache baseline, not an implemented M4 cache. ADR-0007 explicitly reserves OHLC,
adjustment, range and freshness decisions for an accepted M4 contract.

The sole chart path is `menu_watchlist.graph_stock` → `Watch_list.graph_stock`
→ `Stock.graph_performance` → `compatibility.presentation.graph_performance`.
It reconstructs prices from eight summary percentages and a current quote,
uses calendar offsets and an uncontrolled clock, and assumes USD. The existing
synthetic-chart test must be deliberately replaced after contract acceptance.
`Stock.get_price_over_time` is a retained period-summary capability consumed by
both CLIs, refresh/table display and persisted metadata; it must not silently
become a history method. Historical clients/cache must not enter holdings state.

M3 has a strictly validated version-1 holdings schema and one migration runner.
A cache must not add undocumented tables to that database. Proposed cache
storage, lifecycle, freshness and bounds need explicit acceptance. Financial
return, benchmark, dividend, FX, risk and transaction semantics remain outside M4.

## Live issue and agent schedule

| Issue | Bounded objective | Status / dependencies | Agent | PR / review | Blocking reason |
| --- | --- | --- | --- | --- | --- |
| [#88](https://github.com/daniilnahl/Stock-Tracking-App/issues/88) | Historical ADR and dependency plan | Accepted and owner-merged | `m4_contract_audit`, GPT-6.1 low | [#95](https://github.com/daniilnahl/Stock-Tracking-App/pull/95); independent review, local checks and PR/main CI passed | None |
| [#89](https://github.com/daniilnahl/Stock-Tracking-App/issues/89) | FMP OHLCV retrieval and approved validation | Owner-merged and verified | `m4_retrieval_impl`, GPT-6.1 low | [#96](https://github.com/daniilnahl/Stock-Tracking-App/pull/96); `m4_retrieval_review`, GPT-6.1 low: no findings; local and PR/main CI passed | None |
| [#90](https://github.com/daniilnahl/Stock-Tracking-App/issues/90) | Bounded historical cache and freshness | Awaiting owner merge on `feature/90-history-cache` | `m4_history_cache`, GPT-6.1 low | [#97](https://github.com/daniilnahl/Stock-Tracking-App/pull/97); `m4_cache_review`, GPT-6.1 low: no findings; local checks passed; hosted checks tracked in PR | Required hosted CI and owner merge |
| [#91](https://github.com/daniilnahl/Stock-Tracking-App/issues/91) | Historical composition and facade | Queued; #88–90 | `m4_history_integration`, GPT-6.1 low | None | Stable retrieval/cache contracts |
| [#92](https://github.com/daniilnahl/Stock-Tracking-App/issues/92) | Genuine-observation chart rendering | Queued; #88/#91 | `m4_chart_rendering`, GPT-6.1 low | None | Stable facade data boundary |
| [#93](https://github.com/daniilnahl/Stock-Tracking-App/issues/93) | Existing chart command date selection | Queued; #88/#91/#92 | `m4_date_selection`, GPT-6.1 low | None | Approved UI/defaults and real chart |
| [#94](https://github.com/daniilnahl/Stock-Tracking-App/issues/94) | Independent combined exit evidence | Queued; #88–93 | `m4_exit_audit`, GPT-6.1 low | None | All runtime prerequisites |

Queued agent names are assignments for future dispatch, not claims of running
agents. Two completed read-only audits (`m4_contract_audit`, `m4_chart_audit`)
established provider/chart callers and approval blockers. Documentation drafting
and independent review are complete. The retrieval agent was dispatched after
the owner's direct “Approved and merged. Proceed.” instruction accepted complete
Option A at `e455660774e9c96e8ea8851cdeabc9d63f6e6730`. PR #95 merged as
`7f67c322a9f96cadb6fd3f126ed7240a37ac68c5`; post-merge
[Foundation run 37705325479](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37705325479)
passed. The initial retrieval dispatch was interrupted before source edits;
`m4_retrieval_impl` resumed the bounded work on 2026-10-08, with
`m4_retrieval_review` assigned independent review at the same model/effort.
Each runtime issue receives an isolated
branch/worktree after prerequisites are accepted, reviewed and owner-merged.
Avoid simultaneous changes to FMP, facade or CLI interfaces. Update this table
with actual dispatch, branch, PR, CI, review and blocking evidence as work advances.

## Review and verification

Every issue includes scope, acceptance criteria, requirements, tests and
dependencies, belongs to milestone 5 and follows AGENTS.md. Implementation
agents inspect source/callers/tests, add deterministic tests, run targeted and
full canonical checks, inspect staged secrets/artifacts, commit/push and open a
PR without merging. The Master reviews the actual diff and CI independently,
returns routine defects for repair and records successful review. Formal review
permissions do not authorize bypassing repository controls.

Use the canonical pinned Python 3.11/3.12 environment:

```text
python -m pip check
python -m pytest <issue-relevant tests> -v
python -m pytest
python -m ruff check .
python -m mypy
```

Configured mypy covers `config.py` only. Normal tests never use live network,
real keys, current market values or user storage. Control clocks, use supplied
observations and isolated temporary cache/storage. Installed-wheel probes must
verify the real packaged wiring. Required PR/main CI must pass on actual heads.
Report exact unavailable checks; do not substitute Python 3.14 for the supported
runtime. Verification evidence for the proposal will be recorded in its PR.

Proposal verification on 2026-10-07 used a fresh canonical Python 3.11 virtual
environment in this isolated checkout, installed with `python -m pip install
".[dev]"`. Targeted provider models/protocols, facade, baseline, packaging and
hygiene tests passed **483 tests in 48.59 seconds**. Full `python -m pytest -q`
passed **1,850 tests in 76.53 seconds**. Ruff, configured mypy (one source file)
and `pip check` passed. These verify the unchanged runtime baseline and proposal
hygiene; they do not claim M4 runtime behavior. Initial sandbox interpreter
execution was denied; the same supported environment ran successfully through
approved execution. No supported runtime, pins or system installation changed.

Retrieval verification on 2026-10-08 used the same canonical Python 3.11.9
environment. The implementation's focused history/models/errors/transport/wheel
suite passed 686 tests; the final history boundary suite passed 129 tests.
The exact final runtime/test diff passed **1,984 full tests in 87.63 seconds**.
Ruff, configured mypy (`config.py` only), pip check and staged hygiene (8 tests)
passed. Independent review passed 578 focused tests, including the offline wheel,
then 129 final history tests; no actionable finding remained. These verify #89
retrieval, not downstream caching, charts, date selection or M4 completion.
Exact-head hosted CI/review is tracked in [PR #96](https://github.com/daniilnahl/Stock-Tracking-App/pull/96).
The owner confirmed PR #96 merged on 2026-10-08. Verified merge
`921822996bf017869c424e049c1010d75f54491f` includes exact reviewed head
`8b7fd14933c322a7cc4b625696ad3db93ab50970`;
[post-merge Foundation run 37844832081](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37844832081)
passed all five checks. This resolves #90's retrieval prerequisite. Cache
implementation and independent review were dispatched after those gates passed.
Later issues retain their reviewed, owner-merged prerequisite gates.

Cache verification on 2026-10-08 used the same Python 3.11.9 environment.
Focused cache/history/wheel checks passed 212 tests; final cache/boundary checks
passed 94 tests. The final stable full suite passed **2,066 tests in 77.35 seconds**
with no skips or failures. Ruff, configured mypy (one source file), pip check and
staged diff checks passed. Independent review passed 212 focused tests and then
21 final staged hygiene/boundary tests, with no remaining actionable findings.
The neutral sidecar retains holdings/schema isolation. Explicit production
composition remains #91; cache verification does not establish M4 completion.
[PR #97](https://github.com/daniilnahl/Stock-Tracking-App/pull/97) records exact-head
hosted checks and the Master review. Runtime/test implementation commit is
`ca8dbe7bce2d054c5bd4da68e34a0225a003d4e2`; the subsequent tracking change edits
only this plan. Required hosted CI and owner merge remain #91 dependency gates.

## Exit mapping and completion gates

| SRS M4 deliverable | Owning issues | Required evidence |
| --- | --- | --- |
| Retrieve OHLCV history | #88/#89 | Official schema and controlled genuine observations; precision/errors/ranges |
| Define adjusted/raw usage | #88/#89/#92 | Accepted endpoint-specific semantics and accurate labels; no total-return claim |
| Add historical cache | #88/#90/#91 | Accepted lifecycle/TTL/bounds plus deterministic hit/miss/expiry/failure tests |
| Replace synthetic charting | #91/#92 | Exact observed dates/prices plotted; no summary-derived fallback |
| Add date-range selection | #88/#93 | Approved defaults/input validation and exact requested range |
| Genuine-provider-history chart exit | #94 | Combined source/wheel provider/cache/facade/chart/CLI evidence |

Related requirements: ARCH-001–003/005/006; DATA-001–007/009–011;
FIN-001–003; PERF-001/002; SEC-002/005; ERR-001–003; TEST-001–005;
FC-060–062/100/101. Persistence requirements apply if accepted cache storage
introduces persistence behavior, without changing the holdings schema implicitly.

The contract acceptance gate is satisfied. M4 remains **INCOMPLETE** until
all required issues are closed, reviewed PRs are owner-merged into main, required
CI and milestone verification pass, each deliverable is evidenced, no blocking
requirement remains and deferred work has explicit follow-up ownership. Do not
close the milestone or declare success from a proposal or queued agent schedule.
