# TO-DO LIST — Stock search/add and future dashboard panels

## Current capability and scope

The M8 preview is illustrative. The current M7 REST API exposes health,
schema, saved watchlist reads and exact stored-row history only
(`src/stock_tracker/api/app.py`). There is **no browser stock-search or add
endpoint**. `CurrentDataService` already provides candidate resolution and
in-memory add behavior for the CLI; `WatchlistService` owns local load/save.
Their presence does not establish an approved HTTP mutation contract.
ADR-0013 and proposed ADR-0014 scope the dashboard to read-only operations.

The visible **Search / add stock** control in the preview opens an explanation
of this missing capability. It must not pretend to search or save. The two
requested panels, **Recommend stock of the day** and **Taurus Agents Menu**,
are explicitly unavailable placeholders. Their presence authorizes layout
only, not recommendations, agents, provider activation or new APIs.

## Backend — stock search and add

- [ ] Approve a bounded extension to the read-only API/SRS/ADR contract before
  implementation. Specify lookup semantics and exact supported NASDAQ identity
  under ADR-0008; do not silently broaden exchange coverage.
- [ ] Specify versioned lookup and add request/response schemas, bounded query
  length/results/rate and request budgets, validation, safe error categories,
  cancellation and timeout semantics. Route names/verbs remain a review choice.
- [ ] Reuse provider interfaces and shared application services; no provider
  credentials/URLs/parsing or financial logic in the browser or router.
- [ ] Define add persistence atomicity: load latest namespace, resolve/validate
  identity, preserve ordered duplicates, save safely, and report committed
  outcome. Approve concurrency/version checking, duplicate policy, retry
  idempotency and disconnect-before/after-commit behavior. Request-local ordinal
  is not a durable mutation identifier. Do not copy CLI partial in-memory
  publication behavior into HTTP without an approved contract.
- [ ] Define ownership inputs (quantity/average cost) or explicitly scope add
  to unowned entries, following existing Decimal/domain rules. Never infer
  cost currency or invent cost-basis/return semantics.
- [ ] Approve authenticated write controls, exact Origin/Host policy and browser
  token lifecycle; reject unauthorized requests before acquiring dependencies.
  Preserve default read-only API behavior and holdings on pre-commit rejection
  or rolled-back transactions. A lost response after a successful commit is an
  uncertain outcome, not evidence the write failed; use the approved replay and
  reconciliation contract rather than retrying blindly.
- [ ] Keep provider invalid-symbol, unavailable-data, malformed-response,
  timeout, outage and rate-limit failures distinct. Confirm rights for each new
  search/display/cache use; credentials alone do not prove entitlement.
- [ ] Add deterministic service/API/persistence tests with temporary SQLite,
  fake providers, duplicate rows, concurrent edits, replay/disconnect cases,
  exact decimals and unchanged-data failures. Run canonical checks and CI.

## Frontend — search and add

- [ ] Keep an obvious Search / add stock entry point near the watchlist.
  Until an accepted backend is available, activate only an explanation with
  “Unavailable — backend search/add is not implemented”; issue no requests,
  show no fabricated results and expose no enabled save action.
- [ ] After contract approval, add a labeled keyboard-accessible search dialog
  or page through the centralized typed API client; support query validation,
  debouncing/cancellation and reject late responses after query/namespace change.
- [ ] Show loading, empty, invalid identity, provider unavailable/rate-limited,
  unsupported and recoverable error states distinctly. Display identity/exchange
  for the user's explicit selection; no automatic stock substitution.
- [ ] Request the approved ownership inputs and explicit namespace selection.
  Keep financial values exact; never convert saved Decimal inputs through Number.
- [ ] Show success only after confirmed persistence. Handle uncertain commit
  outcomes according to the approved replay contract, not blind retries. Reload
  the saved watchlist and clear stale detail/ordinal selection after success.
- [ ] Verify keyboard focus/escape, status announcements, mobile layout, themes,
  duplicate handling and failure recovery using schema fixtures and separate
  browser E2E. Provide a labeled isolated visual demo with the completed issue.

## Future placeholders — separate backend work

- [ ] **User stock criteria — M9:** following owner-accepted
  [ADR-0017](adr/0017-user-criteria-taurus-discovery.md), let users configure
  supported parameters. First define exact fields/operators/units/null rules,
  settings/API/UI and handoff contracts. M9 validates/prepares criteria without
  calling a screener or executing a market search. Known-stock data calls remain
  separate. No criteria form is implemented by this checklist.
- [ ] **Recommend stock of the day — M10:** Taurus searches for stocks using
  the M9 user criteria. Candidate/sector discovery and suggested results are
  deferred to M10; any daily cadence, rank/tie-break and no-candidate policy need
  a separate contract. Keep the current placeholder unavailable, with no sample
  winner or claim that criteria configuration has searched the market.
- [ ] **Taurus Agents Menu — M10:** Taurus is the chosen responsibility for
  criteria-driven search, not a verified framework/model integration. Define
  intended agents/search tools and operations, then approve any
  backend/vendor, data transmission/retention, authentication, budgets,
  cancellation, failure and opinion-display rules. M10 gates still apply where
  AI is involved; no provider/model calls, keys, spending or private holdings
  transmission are authorized by this placeholder.
- [ ] Frontend keeps both panels visibly marked “Placeholder · unavailable”
  with concise explanations. Enable future controls only after their backend
  contracts, scope and verification pass. Keep pixel typography and established
  monochrome light/dark themes across all states.

This checklist records prerequisites; it does not approve mutation semantics,
new financial rules or future milestone implementation. Decompose approved
backend work into bounded issues before beginning it.
