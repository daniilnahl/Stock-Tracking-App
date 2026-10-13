# M4 Historical Market Data exit audit

Audit date: **2026-10-12**. Milestone: [M4 — Historical Market Data](https://github.com/daniilnahl/Stock-Tracking-App/milestone/5).
Audit issue: [#94](https://github.com/daniilnahl/Stock-Tracking-App/issues/94).
Runtime baseline: `41ed11c01693a269bdb93bd2c2b11133681e4cb8` (owner-merged PR #100).
Audit PR: [#101](https://github.com/daniilnahl/Stock-Tracking-App/pull/101).
**Status: INCOMPLETE — behavior audit passed; hosted CI/merge/closure pending.**
Issues #88–93 are closed and their reviewed PRs are owner-merged on main. #94
and the milestone remain open. This audit cannot declare completion until its
own reviewed PR is owner-merged, required main CI passes and closure is reconciled.

## Approved deliverables and implementation trace

SRS §23 M4 requires OHLCV retrieval, explicit raw/adjusted usage, historical
caching, replacement of synthetic charts and date-range selection. Its exit is:

> Historical charts use genuine provider market history.

[ADR-0010](../adr/0010-historical-market-data-contracts.md) Option A was explicitly
accepted by the owner's “Approved and merged. Proceed.” instruction at reviewed
head `e455660774e9c96e8ea8851cdeabc9d63f6e6730`. The accepted contract defines
raw non-split-adjusted prices, prior-UTC-day/five-calendar-year defaults, bounded
inclusive ranges, exact NASDAQ facade identity, a one-hour neutral JSON sidecar
and observation-only charts. It authorizes no adjusted-return, dividend,
benchmark, FX or analytics formula and no agent merge.

| Closed issue | Deliverable | Owner-merged PR | Exact merge commit |
| --- | --- | --- | --- |
| [#88](https://github.com/daniilnahl/Stock-Tracking-App/issues/88) | Accepted history/cache/chart/date contracts | [#95](https://github.com/daniilnahl/Stock-Tracking-App/pull/95) | `7f67c322a9f96cadb6fd3f126ed7240a37ac68c5` |
| [#89](https://github.com/daniilnahl/Stock-Tracking-App/issues/89) | Raw FMP OHLCV retrieval | [#96](https://github.com/daniilnahl/Stock-Tracking-App/pull/96) | `921822996bf017869c424e049c1010d75f54491f` |
| [#90](https://github.com/daniilnahl/Stock-Tracking-App/issues/90) | Bounded persistent historical cache | [#97](https://github.com/daniilnahl/Stock-Tracking-App/pull/97) | `7385f7e82d2328573449154e8fca918d15d2152f` |
| [#91](https://github.com/daniilnahl/Stock-Tracking-App/issues/91) | Historical factory and facade composition | [#98](https://github.com/daniilnahl/Stock-Tracking-App/pull/98) | `c8f0d8f1b253d9133209e4aa56998c214f146aec` |
| [#92](https://github.com/daniilnahl/Stock-Tracking-App/issues/92) | Real raw observation chart rendering | [#99](https://github.com/daniilnahl/Stock-Tracking-App/pull/99) | `cd0b8284e0f1cb21aedd7f778acbc903a5697631` |
| [#93](https://github.com/daniilnahl/Stock-Tracking-App/issues/93) | Paired CLI dates and safe graph flow | [#100](https://github.com/daniilnahl/Stock-Tracking-App/pull/100) | `41ed11c01693a269bdb93bd2c2b11133681e4cb8` |

The Master reread each GitHub merge record and verified every merge above is an
ancestor of fetched main with `git merge-base --is-ancestor` (exit 0).
[PR #100's final Foundation run 38312333898](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38312333898)
and [post-merge main run 38312997700](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38312997700)
passed all five configured checks. The audit was dispatched after main passed.
Earlier exact-head/main evidence and the repaired color-sensitive help assertion
are preserved in the [live plan](m4-plan.md); earlier CI is not this audit's CI.

## Requirement and test map

| Requirement / M4 bullet | Implementation and meaningful evidence |
| --- | --- |
| OHLCV retrieval; DATA-001/002/004/006/007 | FMP raw endpoint parser, typed immutable `PriceBar`, safe transport and explicit exchange-session dates; `test_fmp_history.py`, transport/model/error matrices and source/wheel integration |
| Raw/adjusted usage; DATA-003/005; FC-060–062/100/101 | Endpoint-specific `adj*` fields map to raw OHLC with `adjusted_close=None`; chart plots raw closes only, labels split discontinuities and unknown historical currency; exact parser and Agg data assertions |
| Historical cache; PERF-001/002 | Exact provider/mapping/symbol/range/basis key, original UTC receipt time, 3600-second history TTL and no stale fallback; `test_history_cache.py`, persistent reuse/expiry/failure/source/wheel tests |
| Genuine charting; DATA-003; FIN-001–003 | Validated original Decimal observations convert only at rendering; actual sparse dates and unconnected markers, requested/observed labels, no summary/current-quote reconstruction; `test_history_charts.py` |
| Date selection; ARCH-005; DATA-007; ERR-001–003 | Paired strict ISO CLI options, accepted default/leap handling and 3660-day limit; identity before key/preflight, no save, safe failures and programming-error propagation; `test_history_date_selection.py` |
| ARCH-001–003/006; SEC-005; TEST-001–005 | Accepted ADR and separated domain/provider/persistence/presentation boundaries; source/wheel/domain probes, temporary fictional storage, controlled clocks, network/pickle guards, safe category diagnostics and staged hygiene |
| GH-003/004 | Seven bounded issues, one task branch/PR per issue, independent review, exact-head CI and owner-merge gates; GitHub state and ancestry trace above; #94 closure remains pending |

Provider summary displays and existing holdings arithmetic retain their contracts.
The sidecar is disposable provider data, separate from SQLite version 1,
migrations, neutral holdings transfer and backups. Existing M3 restart/schema/
preservation tests remain required. Symbol agreement cannot prove exchange
identity or full session completeness.

## Combined audit and verification

`history_exit_probe.py` runs independent write, read and expired subprocesses
against source and an offline installed wheel. Every child clears inherited
provider credentials, disables dotenv discovery, uses a fixed UTC clock and
verifies network/pickle/legacy-content/outside-write/SQLite guards before
application imports. Imported runtime paths must match the requested source or
wheel. Only the HTTP opener is synthetic: actual TLS/request construction,
header authorization, route/query validation, response parsing, factory,
persistent cache, SQLite restore, facade, Agg renderer and CLI execute.

The write process saves fictional menu and evaluation namespaces, then restores
the menu through the real lazy CLI load. Unordered provider-schema bars include
precise raw closes `100.1234567890123456` and `50.0617283945061728`, zero/null
volume and a split-like discontinuity. Requested boundary/weekend gaps stay
absent. Numeric history and exact Decimal text remain unchanged; only chart
values convert to float. Markers have no connecting lines. The requested range,
observed dates/count, raw basis, unknown historical currency and split warning
are asserted. Saved current price, summary percentages and EUR metadata cannot
replace the history data or authorize a historical currency label.

The fresh read process at receipt age 3,599 seconds restores SQLite again and
charts the exact cached observations without any HTTP request or cache rewrite.
At exactly 3,600 seconds, the expired process receives synthetic HTTP 503,
performs two accepted attempts with a 0.5-second backoff, and exits safely with
no figure or stale data. Cache and database bytes remain unchanged. Both
namespace records, version-1 schema/table set and opaque legacy file are
preserved. Guarded invalid ISO, unsupported exchange before key preflight,
missing key before factory construction and offline help checks also execute.
Output/cache/database assertions exclude the synthetic runtime key and provider
body. No live provider or real user file is required.

Independent baseline review ran the canonical existing Python 3.11.9 environment:

```text
python -m pytest tests/test_fmp_history.py tests/test_history_cache.py
  tests/test_history_integration.py tests/test_history_charts.py
  tests/test_history_date_selection.py -q
```

Result: **313 passed in 13.13 seconds**. These baseline results do not substitute
for the new combined audit, full canonical suite or fresh hosted checks.
Configured mypy covers `config.py` only; it does not certify full application typing.

Final canonical verification at audit implementation commit
`0f3d3c7f42d5c1bdcc4e45297393ed3e118e80a4` used that same environment.
The later tracking commit changes only this evidence and the live plan; tested
runtime/fixture contents remain unchanged. [PR #101](https://github.com/daniilnahl/Stock-Tracking-App/pull/101)
records final exact-head hosted CI and Master review.

```text
python -m pytest tests/test_history_exit.py tests/test_packaging.py
  tests/test_fmp_history.py tests/test_history_cache.py
  tests/test_history_integration.py tests/test_history_charts.py
  tests/test_history_date_selection.py tests/test_cli_persistence.py
  tests/test_repository_hygiene.py -q
python -m pytest -q
python -m ruff check .
python -m mypy
python -m pip check
```

The focused command passed **350 tests in 51.08 seconds**. Full pytest passed
**2,170 tests in 77.11 seconds**. Ruff, configured mypy (one source file), pip
check and diff checks passed. Final staged hygiene passed **8 tests in 8.28
seconds**. Independent final source/installed-wheel verification passed
**3 tests in 32.46 seconds**, with no actionable findings. Existing domain/M3
preservation tests passed in the full suite. No runtime source, schema, dependency,
toolchain or CI change is included in this audit.

During verification, an earlier broader run reported **1 failure and 349 passes
in 16,986.89 seconds** amid unusually long tool/session delays. The source
probe's substantive assertions passed, but a delayed Matplotlib font-cache
startup diagnostic violated its quiet-stderr assertion. The bounded probe-only
repair captures `matplotlib.font_manager` logging before application imports;
exceptions, provider diagnostics, guards and quiet-process assertions remain
intact. The final focused/full/independent checks above passed after that repair.
Earlier independent source/wheel execution also reported an anomalous elapsed
time; it is not substituted for the final 32.46-second verification.

## Exit and closure gates

| Gate | Current status |
| --- | --- |
| Accepted contracts and merged runtime issues #88–93 | PASS |
| Runtime PRs #95–100 included on main | PASS |
| Required main CI after PR #100 | PASS |
| Combined source/wheel exit probe and canonical checks | PASS |
| Independent final audit review | PASS, no actionable findings |
| Exact-head audit PR CI | PENDING |
| Owner merge of #94 audit PR and post-merge main CI | PENDING |
| #94 closed and milestone closure reconciled | PENDING |

No blocking runtime defect has been identified in the independent baseline
review. The remaining gates are audit hosted CI and owner merge
with final main CI/closure, not permission to mark the milestone complete early.

## Limits and follow-up ownership

Offline synthetic payloads matching the inspected official provider schema prove
the implementation charts parsed provider-schema observations rather than a
fabricated summary series. They do not verify live FMP account entitlement, real market values,
complete sessions, historical currency or correction finality. Current schema
exposes no trustworthy adjusted series for this mapping; no total-return or
dividend-reinvestment claim is made.

Cache concurrency may lose cache entries or spend duplicate quota; atomic
replacement does not promise adversarial-filesystem or power-loss durability.
The accepted sidecar has no automatic destructive repair command. These are
accepted ADR-0010 limits, not unassigned missing M4 deliverables.
Future analytics/adjustment/dividend/FX decisions belong to their separately
approved milestones and financial definitions. The M4 audit remains #94's
responsibility through its reviewed owner merge and final closure reconciliation.
