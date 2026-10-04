# M2 Market Data Layer implementation plan

Status: **proposal; runtime blocked on owner acceptance of
[ADR-0007](../adr/0007-market-provider-contracts.md)**. Snapshot 2026-10-04.
Parent milestone: [M2 — Market Data Layer](https://github.com/daniilnahl/Stock-Tracking-App/milestone/3).
Planning and contract publication are safe to proceed; issue creation does not
authorize policy or runtime behavior. No agent merge is authorized.

Baseline main is `788d3c4119e9ebb196256e9355f24ce8b31dc037`. M1 integration
[#42](https://github.com/daniilnahl/Stock-Tracking-App/issues/42) is closed, with
[main Foundation CI](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37214866386)
passing all five checks. ADR-0005 pins/pip/Python 3.11/3.12 and ADR-0006 domain,
facade/state contracts remain authoritative. Canonical checks are
`python -m pytest`, `python -m ruff check .` and configured `python -m mypy`
(config.py only). Apply [TESTING.md](../TESTING.md) offline/temp-state isolation.

## Live issue and dependency view

All issues belong to M2. A runtime issue is dispatchable only after its listed
dependencies are implemented/included on main and #47's exact-commit acceptance
is recorded. Agent names below identify current assignment, not future automatic
dispatch. PR/review cells describe observed state, not expected outcomes.

| Issue | Bounded objective | Status / dependency state | Assigned agent | PR / review | Blocking reason |
| --- | --- | --- | --- | --- | --- |
| [#47](https://github.com/daniilnahl/Stock-Tracking-App/issues/47) | Proposed ADR, policy and this issue map | Documentation drafted; M1 dependency satisfied | m2_analysis (proposal implementation); master reviews | Publication pending / review in progress | Owner acceptance of exact reviewed commit remains required |
| [#48](https://github.com/daniilnahl/Stock-Tracking-App/issues/48) | Typed models, protocol, application errors, package discovery | Blocked (open); depends #47 | Unassigned | None / not started | Accepted contract |
| [#50](https://github.com/daniilnahl/Stock-Tracking-App/issues/50) | Injectable urllib transport and approved reliability policy | Blocked (open); depends #47, #48 | Unassigned | None / not started | Accepted contract, typed errors |
| [#51](https://github.com/daniilnahl/Stock-Tracking-App/issues/51) | FMP quote retrieval and validation | Blocked (open); depends #47, #48, #50 | Unassigned | None / not started | Stable transport/models |
| [#52](https://github.com/daniilnahl/Stock-Tracking-App/issues/52) | FMP company-profile retrieval | Blocked (open); depends #47, #48, #50; sequence after #51 | Unassigned | None / not started | Stable transport/models and shared adapter ordering |
| [#53](https://github.com/daniilnahl/Stock-Tracking-App/issues/53) | Typed provider period summaries | Blocked (open); depends #47, #48, #50; sequence after #52 | Unassigned | None / not started | Stable transport/models and shared adapter ordering |
| [#54](https://github.com/daniilnahl/Stock-Tracking-App/issues/54) | Exact-symbol validation and safe CSV behavior | Blocked (open); depends #47, #48, #50, #52 | Unassigned | None / not started | Accepted identity/CSV policy and stable profile/transport |
| [#55](https://github.com/daniilnahl/Stock-Tracking-App/issues/55) | Facade, both CLI and Watch_list provider integration | Blocked (open); depends #47, #48, #50–54 | Unassigned | None / not started | Implemented adapter operations and accepted compatibility corrections |
| [#56](https://github.com/daniilnahl/Stock-Tracking-App/issues/56) | M2 exit evidence and boundary verification | Blocked (open); depends #47, #48, #50–55 | Unassigned | None / not started | Runtime, review, owner merges and required main CI |

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
| Fix ticker validation; DATA-006, ERR-001–003 | #54 exact scoped match, unrelated/empty/truncated/malformed/failure distinctions, untouched CSV; #55 safe user messages and no failed add/save |
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

DATA-006's definitive network unknown-instrument classification is an explicit
#56 exit blocker until verified provider evidence or an explicitly accepted
supported-scope interpretation resolves it. The proposal's tests can demonstrate
local invalid input, unresolved scoped lookup, unavailable data for resolved
identity and every infrastructure category; a no-match search cannot certify
global nonexistence. Accepting the other ADR choices alone does not silently
satisfy this remaining requirement/evidence gate.

## Deferred scope and current blockers

M2 defines a separate historical protocol/PriceBar, not history retrieval,
adjustment/return conventions or charts. M4 owns real history, cache and removal
of synthetic charts under DATA-003–005; disabled TTL proposals authorize no cache
implementation. M3 owns persistence/unsafe pickle replacement and migration;
CSV bypass neither deletes nor migrates user data. M5 owns portfolio metrics;
M6/M7 own broader service/CLI/API work. No new dependencies, Python version,
CI architecture, SRS rewrite or financial formula is part of M2.

The owner must decide ADR-0007's Stable endpoint switch, exact NASDAQ lookup
limitations, missing/time/currency contracts, error/invalidation compatibility,
CSV bypass and all proposed reliability values. Public documentation does not
prove current account entitlements, complete search or quote freshness; no key
was tested. Any unverifiable external contract remains an explicit implementation
blocker. **M2 is incomplete and runtime is blocked; proposal review continues.**
