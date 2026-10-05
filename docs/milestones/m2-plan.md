# M2 Market Data Layer implementation plan

Status: **COMPLETE — implemented and verified on main, 2026-10-05**.
All ten required issues (#47, #48, #50–56 and #66) are closed after human
merges of PR #57–65 and #67. No M2 blocker remains. The
[final completion report](https://github.com/daniilnahl/Stock-Tracking-App/issues/56#issuecomment-5999403521)
and [exit evidence](m2-exit-evidence.md#completion-review--2026-10-05) record the
six delivered objectives, passing boundary exit criterion and final checks.
Milestone 3 is closed at 100%, with zero open and 20 closed items.
The owner stated **"I approve A"** in the Codex milestone chat on **2026-10-04**,
accepting [ADR-0007](../adr/0007-market-provider-contracts.md) exactly at
`cf909dfc6c9766c440b1aeaf408d10c1f112e6a4`, while retaining the DATA-006
definitive network unknown-instrument classification exit blocker. The
[PR #57 acceptance record](https://github.com/daniilnahl/Stock-Tracking-App/pull/57#issuecomment-5982448860)
is the Master's faithful record of that human chat instruction, not an
independently authored human GitHub approval. That historical gate decision is
superseded for scoped product invalidity by the owner's later instruction,
recorded in accepted [ADR-0008](../adr/0008-scoped-ticker-rejection.md) and
[#66](https://github.com/daniilnahl/Stock-Tracking-App/issues/66). Snapshot 2026-10-05.
Parent milestone: [M2 — Market Data Layer](https://github.com/daniilnahl/Stock-Tracking-App/milestone/3).
The contract acceptance, implementation, human merge/main inclusion and final
verification gates are satisfied. No agent merge is authorized.

Planning baseline main was `788d3c4119e9ebb196256e9355f24ce8b31dc037`. M1 integration
[#42](https://github.com/daniilnahl/Stock-Tracking-App/issues/42) is closed, with
[main Foundation CI](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37214866386)
passing all five checks. ADR-0005 pins/pip/Python 3.11/3.12 and ADR-0006 domain,
facade/state contracts remain authoritative. Canonical checks are
`python -m pytest`, `python -m ruff check .` and configured `python -m mypy`
(config.py only). Apply [TESTING.md](../TESTING.md) offline/temp-state isolation.
Current verified main is `5eccf3b24edbe03a6f01e86b9dfcffb80a1ad0c7`, after
human merge of PR #67. [Foundation run 37346059176](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37346059176)
passed all five checks. See [exit evidence](m2-exit-evidence.md) for the current
requirement/test mapping and historical gate. Final exit audit passed 301 focused
cases; fresh full verification passed 1,334 tests, Ruff and configured mypy.
This later documentation-only update has separate PR/CI publication gates.

## Live issue and dependency view

All issues belong to M2. A runtime issue is dispatchable only after its listed
dependencies are implemented/included on main and #47's exact-commit acceptance
is recorded. Acceptance and dependencies #47/#48/#50–55 are now included on main.
Agent names identify current assignment, not future automatic
dispatch. PR/review cells describe observed state, not expected outcomes.

| Issue | Bounded objective | Status / dependency state | Assigned agent | PR / review | Blocking reason |
| --- | --- | --- | --- | --- | --- |
| [#47](https://github.com/daniilnahl/Stock-Tracking-App/issues/47) | Accepted ADR, policy and this issue map | Closed; included on main | Completed | [#57](https://github.com/daniilnahl/Stock-Tracking-App/pull/57) / human merged | None |
| [#48](https://github.com/daniilnahl/Stock-Tracking-App/issues/48) | Typed models, protocol, application errors, package discovery | Closed; dependency #47 satisfied | Completed | [#58](https://github.com/daniilnahl/Stock-Tracking-App/pull/58) / human merged | None |
| [#50](https://github.com/daniilnahl/Stock-Tracking-App/issues/50) | Injectable urllib transport and approved reliability policy | Closed; dependencies #47, #48 satisfied | Completed | [#59](https://github.com/daniilnahl/Stock-Tracking-App/pull/59) / human merged | None |
| [#51](https://github.com/daniilnahl/Stock-Tracking-App/issues/51) | FMP quote retrieval and validation | Closed; dependencies #47, #48, #50 satisfied | Completed | [#60](https://github.com/daniilnahl/Stock-Tracking-App/pull/60) / human merged | None |
| [#52](https://github.com/daniilnahl/Stock-Tracking-App/issues/52) | FMP company-profile retrieval | Closed; dependencies #47, #48, #50 satisfied; sequenced after #51 | Completed | [#61](https://github.com/daniilnahl/Stock-Tracking-App/pull/61) / human merged | None |
| [#53](https://github.com/daniilnahl/Stock-Tracking-App/issues/53) | Typed provider period summaries | Closed; dependencies #47, #48, #50 satisfied; sequenced after #52 | Completed | [#62](https://github.com/daniilnahl/Stock-Tracking-App/pull/62) / human merged | None |
| [#54](https://github.com/daniilnahl/Stock-Tracking-App/issues/54) | Exact-symbol validation and safe CSV behavior | Closed; dependencies #47, #48, #50, #52 satisfied | Completed | [#63](https://github.com/daniilnahl/Stock-Tracking-App/pull/63) / human merged | None |
| [#55](https://github.com/daniilnahl/Stock-Tracking-App/issues/55) | Facade, both CLI and Watch_list provider integration | Closed; dependencies #47, #48, #50–54 satisfied | Completed | [#64](https://github.com/daniilnahl/Stock-Tracking-App/pull/64) / human merged | None |
| [#56](https://github.com/daniilnahl/Stock-Tracking-App/issues/56) | M2 exit evidence and boundary verification | Closed; final exit review passed | Completed | [#65](https://github.com/daniilnahl/Stock-Tracking-App/pull/65) / human merged; final report after #67/main CI | None |
| [#66](https://github.com/daniilnahl/Stock-Tracking-App/issues/66) | Approved scoped no-match rejection | Closed; ADR-0008 implemented on main | Completed | [#67](https://github.com/daniilnahl/Stock-Tracking-App/pull/67) / human merged, PR/main CI passed | None |

One issue normally produces one isolated branch/worktree and PR. Do not dispatch
blocked issues merely because scaffold edits seem additive. #51–54 share fmp.py
and exports: implement sequentially or agree separate parser modules/merge order
after the contract stabilizes. Tests accompany each implementation; #56 does not
defer error/correctness testing. Reconcile this table to actual issue dependencies,
assignments, PRs and evidence at every milestone update.

## Requirement and acceptance map

| SRS §23 M2 objective / requirement | Owner and expected evidence |
| --- | --- |
| Create MarketDataProvider; ARCH-001/002/003/006, DATA-002 | #47 accepted contract; #48 interfaces, package/wheel imports; #55 provider-only application calls |
| Implement FMP adapter; DATA-001, DATA-006 | #50 transport; #51 quote, #52 profile, #53 summary, #54 resolution; schema fixtures and safe explicit failure classification |
| Typed provider models; DATA-002/007/008 | #48 immutable Decimal/nullable/UTC models and history capability; #51–54 parsing; currency metadata without FX/aggregate assumptions |
| Define timeout/retry/rate-limit policy; DATA-009–011, SRS §11/18, SEC-002/005, ERR-001/002 | #47 exact value acceptance; #50 deterministic timeout/status/retry/429/backoff tests and credential-safe logs/errors |
| Fix ticker validation; DATA-006, ERR-001–003 | #54 exact scoped match and untouched CSV; #55 safe messages/no failed save; #66 approved successful-no-match rejection with malformed/provider failure distinctions preserved |
| Mocked provider tests; TEST-001–005 | #48, #50–55 targeted tests under default network/temp-state guards; #56 source/wheel/full-suite and required CI evidence |
| No direct FMP calls from application code; ARCH-003, PERF-001 | #55 all four URL/schema sites replaced, preserved root callers; #56 static caller scan and request-count/injected-provider integration checks |

## Verification and exit gates

Each implementation PR records exact commands/results, scoped diff and staged
secret scan, required CI and requirement/issue linkage. Test success, empty/null,
wrong symbol/shape/type, malformed JSON, 400/401/402/403/404/429/5xx, timeout,
connection failure and retry exhaustion with synthetic fixtures. Test no cache
mutation on failure, no raw exception/key/header/URL leakage, fixed UTC clocks,
controlled jitter/sleep and bounded attempt counts. Both CLI flows use real
domain arithmetic beneath fake provider infrastructure. Preserve runtime-only
key rebinding, root class pickle globals and holdings through trusted temporary
fixtures; no real user file, database, credential or API call.
Include a restored runtime key differing from the module key: preserve pre-work
configuration checks and render safe ConfigurationError from the provider factory.

#56 must demonstrate the actual exit criterion: **application code no longer
calls FMP directly**. Search tracked Python for provider URLs/schema keys and
transport imports; allow FMP knowledge only in adapter and deliberate sanitized
tests/documentation, not facade, Watch_list, CLI or domain. The retained generic
legacy utility is no longer used by maintained application paths. Verify both
source and installed wheel, no hidden validation/profile/quote calls, no duplicate
requests within an operation apart from approved transport retries, and unchanged
domain isolation. Record actual PR/main commits, all five required CI checks,
owner merges, issue closure and unresolved blockers. Green local tests alone do
not establish milestone completion.

The previous DATA-006 definitive unknown evidence gate is superseded by the
explicitly accepted ADR-0008 supported-scope product rule. #66 implemented
successful schema-valid no-match rejection and is now human
merged, with passing exact-head/main CI and final #56 review. Malformed and
infrastructure errors remain distinct. A no-match still cannot certify global
nonexistence; completion relies on the approved scoped product interpretation.

## Deferred scope and limitations

M2 defines a separate historical protocol/PriceBar, not history retrieval,
adjustment/return conventions or charts. M4 owns real history, cache and removal
of synthetic charts under DATA-003–005; accepted disabled TTLs authorize no cache
implementation. M3 owns persistence/unsafe pickle replacement and migration;
CSV bypass neither deletes nor migrates user data. M5 owns portfolio metrics;
M6/M7 own broader service/CLI/API work. No new dependencies, Python version,
CI architecture, SRS rewrite or financial formula is part of M2.

The owner accepted ADR-0007's Stable endpoint switch, exact NASDAQ lookup
limitations, missing/time/currency contracts, error/invalidation compatibility,
CSV bypass and all reliability values. Live-account entitlements, complete
search and quote freshness are not certified by this offline completion
evidence; no key was tested. **M2 is complete under its accepted scope,
with no open blocker.**
#54's historical inconclusive contract is superseded only by the approved
ADR-0008 scoped rejection rule. Persistence/history/analytics remain later work.
