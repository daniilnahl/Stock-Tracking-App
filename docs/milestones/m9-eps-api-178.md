# Injected upcoming-EPS API — issue #178

**Current delivery — 2026-10-18:** this is a dated task/research record. The accepted criteria editor and EPS adapter/service/configuration/API/opt-in launcher/dashboard are now merged, and the independent audit is merged with passing main CI. Earlier pending/no-API/no-UI statements apply to their original scope or unapproved extensions. Provider research remains dated; no new entitlement, metric or live call is inferred. See [current implementation status](../CURRENT_STATUS.md).

The owner merged #177 at `d17c9df61d5ffb491d264c599a5dfdfe259c4e4f`;
post-merge Foundation 39083592809 passed all five jobs. The owner explicitly
approved [ADR-0016](../adr/0016-upcoming-eps-api.md) Option A and requested online
verification. [Issue #178](https://github.com/daniilnahl/Stock-Tracking-App/issues/178)
delivers stage 1 and one isolated live smoke; production composition, quota
budget, launcher flag and dashboard form remain later tasks.

## Plan and responsibilities

1. Master records acceptance and the single-symbol live exception.
2. `eps_impl` adds strict exact-route input handling, injected disabled service,
   typed validated projection, safe errors and EPS/shared admission, then tests.
3. `m9_analysis` independently reviews the contract and final source/tests.
4. Master verifies the complete offline suite and one separately invoked live
   request, reviews the final diff/hygiene, then publishes an issue-linked PR.
5. Exact-head CI and owner merge remain separate gates. No agent merge.

No saved-stock mapping, holdings access, candidate search, metric arithmetic,
provider fallback, persistence, retry or new dependency is introduced.

## Live verification boundary

Use one public provider symbol, AAPL, with a window beginning after the test's
server UTC reference day and at most 92 included dates. Execute the restricted
native Finnhub transport with 5.0s timeout, 262144-byte bound and 128-row bound,
then the existing adapter/service and new in-process API under a synthetic local
bearer. The existing `FINNHUB_API_KEY` is absent from the inherited process and
present in the Windows user environment (presence checked without printing it).
Pass it to the test process only; retain the production loader's process-only
contract. Never save/print credentials, raw responses or observations.

Only safe HTTP status, error category, request/row counts and validation outcome
are evidence. Empty observations are inconclusive. Do not retry a refused or
malformed response, expand to a stock scan or treat successful technical access
as production rights/account-wide quota evidence. The live test is excluded from
pytest and CI. No live data or key becomes a fixture or repository artifact.

## Results

Independent final source/tests/schema/docs review passed with no actionable
findings. Initial focused API/service checks: 164 passed in 2.83s. Final results:

| Command actually executed | Result |
| --- | --- |
| Focused API/service/foundation/history/boundary/serialization/packaging pytest profile | 313 passed in 51.63s, including source and installed-wheel probes. |
| `python -m pytest tests/test_api_upcoming_eps.py -q --tb=short` | 73 passed in 2.35s after the last two admission/disconnect regression tests. |
| Frontend `npm test` | 217 passed in 8.41s. |
| `npm run package:dashboard` and `npm run package:check` | Schema/type/build/byte-exact package checks passed in 5.52s. |
| `npm run test:browser` with installed Edge | 29 passed in 25.0s. |
| `npm run test:integration` with installed Edge | Actual source/wheel: 2 passed in 21.7s. |
| `python -m pytest tests/test_market_provider_boundary.py tests/test_api_upcoming_eps.py -q --tb=short` | 87 passed in 3.17s after the narrow scanner correction. |
| `python -m pytest -q --tb=short` | Final full rerun: 3151 passed in 132.93s. |
| `python -m ruff check .` / `python -m mypy` / `python -m pip check` | Passed; mypy covers configured `config.py` only; no broken requirements. |

Final staged hygiene passed: 9 tests in 13.85s. PR #179 exact-head Foundation
39091329131 passed all five checks; owner merge at
`e7f4647f393f423f8ac3243c804ae82ed25e9cec` was followed by successful main
Foundation 39094106222. Independent and Master review passed.
Python remains pinned 3.12.14;
frontend uses existing bundled Node
24.19.0/npm 10.8.2 and installed Edge. No dependency/runtime/CI change. Native
Windows profiles use task-local TEMP/TMP. An initial sandbox-only focused-test
startup stalled and was stopped; the native profile passed without weakened
tests. A cold probe initially rejected the new intentional `eps_disabled` log;
it now narrowly captures/asserts that fixed category while retaining ordinary
output denial. Production logging was not suppressed or changed to satisfy it.

The initial full Python run had 3149 passes and one static-boundary failure in
144.47s: the scanner classified `urllib.parse.parse_qsl` as outbound HTTP.
The correction permits only that pure function in `api/app.py`, with controlled
regressions continuing to deny network calls, broad imports, other functions and
other paths. Independent review passed. No runtime parser, HTTP protection or
provider behavior changed for this correction; the final full rerun passed.

The separately invoked live smoke **passed** on 2026-10-17 local client date
(UTC reference day 2026-10-18), for AAPL and inclusive window 2026-10-19 through
2027-01-18. Exactly one native Finnhub request returned HTTP 200; the injected
local API returned HTTP 200 with one validated observation and one non-null
estimate. Coverage remains `not_asserted`. No values, raw vendor response or
credentials were stored or printed. This proves that this key accessed the
calendar and the real transport/adapter/service/API accepted its response at
test time, not a future availability or production-use guarantee.

An initial local smoke-script import preflight resolved the older installed
`config` module and stopped before any network request. Selecting the checkout
and `src` import paths fixed the harness; no production source change, provider
retry or additional upstream request was needed. The key was never printed.
