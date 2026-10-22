# Testing Strategy

**Current evidence:** [implementation status](CURRENT_STATUS.md) links the
merged M9 dashboard/audit and post-merge CI. Dated commands/results below are
task-specific records; older future/merge-gate wording does not undo delivered
capabilities. Default tests remain offline and require no real provider keys.

## M10 pure prepared-criteria receiver — issue #207

Run `python -m pytest tests/test_research_criteria.py -v` for the accepted
ADR-0019 offline phase. Check exact ADR-0018 prepared data, immutable duplicates/
order/strings, UTF-16 lengths, control/surrogate/nonblank rules, exact
decimal-string numeric ordering, fixed canonical bytes/hash, caller-bound raw
UTF-8 JSON parsing and
safe rejection of duplicate keys, unexpected types/fields and malformed inputs.
There is no default byte ceiling, predicate evaluation, credential acquisition or
worker/API/UI integration. Cold source and installed-wheel probes must prove
no network, environment/data IO or concrete infrastructure imports, with independent
negative controls. Fictional test bounds are inputs, not owner deployment settings.
Run canonical full pytest, Ruff, configured mypy, pip check and staged hygiene;
no frontend rebuild, container or live provider/model call is required.

## Purpose

This document defines the testing contract for the Stock Tracking App.

The goal is to make tests deterministic, meaningful, isolated, and suitable for both human and AI-driven development.

---

# 1. Test Layers

## Custom stock criteria editor — issue #176

Under [ADR-0018](adr/0018-custom-criteria-editor.md), frontend tests cover custom
names/text, explicit unit/context, exact signed decimal endpoint strings, range
ordering/limits, all/any, immutable snapshots, outdated edits, navigation and
pagehide/reload clearing. Criteria are unevaluated user requests, never provider
facts. Prove editing/preparing/clearing causes no API/provider/agent request or
browser persistence. Preserve the existing source/installed-wheel closed asset
set and actual local launcher profiles; rebuild with `npm run package:dashboard`
and verify `npm run package:check`. Run unit/type/build/browser and actual
`npm run test:integration` profiles before the canonical Python suite, avoiding
concurrent heavy browser/Python runs. Browser credentials/data remain synthetic;
no live provider/model, private data or real key is needed.

## Finnhub upcoming-release EPS — issue #166

For [#182](https://github.com/daniilnahl/Stock-Tracking-App/issues/182), add frontend
unit/component and browser coverage for explicit manual requests, exact string/
zero/negative/null/empty distinctions, generated-schema plus request/row/date/
receipt/provenance validation, no automatic requests, safe errors, editing/
supersession/cancel/route departure and session-wide 401/disconnect/reload clears.
Use fixed synthetic payloads/clocks and the existing same-origin client. Show
mobile/keyboard/light-dark layouts with conspicuous synthetic screenshot labels.
Rebuild/check packaged assets and extend actual source/wheel launcher integration
to submit against the real default-disabled route without API mocks or provider
keys. Run full frontend/browser/integration and canonical Python profiles
sequentially. No real Finnhub request or credential is needed or authorized here.

For [#180](https://github.com/daniilnahl/Stock-Tracking-App/issues/180), use fixed
monotonic/civil clocks to test startup quiet time, trailing-window boundaries,
configuration/construction failures consuming attempts, 429 receipt cooldown,
concurrency and cancellation cleanup. Verify default/help/health/schema/static/
invalid/disabled paths acquire no Finnhub key/provider. Exercise real
configuration/launcher/service/provider/native transport behind a controlled
synthetic HTTP opener in source and installed-wheel profiles, retaining cold
import/IO denial guards. Process-only synthetic keys must never fall back to
dotenv, FMP variables or the Windows user registry. No new actual provider call
or live CI is authorized; #178's separate dated smoke remains prior evidence.

For [#178](https://github.com/daniilnahl/Stock-Tracking-App/issues/178), verify the
injected API's exact query admission, default-disabled dependencies, exact
projection/provenance/request matching, safe error distinction and EPS/shared
cancellation lifetime, alongside existing service/API/access/schema/source-wheel
checks. Keep fixed clocks, synthetic credentials and fake providers in pytest.
The owner's separately authorized one-symbol native live smoke is manual only:
read the process Finnhub key privately, issue at most one bounded request through
transport/service/injected API, and report only safe status/parsing/counts. No
raw payload, observation or credential belongs in fixtures/logs/docs. A missing
or refused key/entitlement records an unverified or failed live result; offline
success cannot substitute for live access. No automatic live CI, retry, startup
probe or production acquisition is added.

For [#172](https://github.com/daniilnahl/Stock-Tracking-App/issues/172)'s explicit
environment loader, run `python -m pytest tests/test_finnhub_configuration.py
tests/test_configuration_security.py -v`. All keys are synthetic; tests isolate
`FINNHUB_API_KEY`, FMP and legacy variables and must never inspect the owner's
real credential. Verify no dotenv call/fallback/import-time lookup, unchanged
FMP precedence, native Windows name handling, safe header validation and exact
header injection into the real adapter behind a controlled HTTP transport.
Configured mypy covers the changed `config.py`. Full source/installed-wheel and
staged-hygiene checks remain required; no live access is tested.

For the injected application-service continuation [#168](https://github.com/daniilnahl/Stock-Tracking-App/issues/168),
also run `python -m pytest tests/test_upcoming_eps_service.py -v`.
Use fixed research-date suppliers and lazy fake providers to verify admission
before acquisition, one date sample, no historical override, immutable request
context, exact Decimal/null values, empty results, provenance and malformed
provider-output rejection. Failures propagate without retries or fallback.
The cold source/installed-wheel EPS probe must also exercise the real service
with injected fixtures. This does not select a production date convention,
map saved stock identities or enable a live connector or public route.

Run `python -m pytest tests/test_finnhub_eps.py tests/test_finnhub_transport.py
tests/test_packaging.py -v` for [ADR-0015](adr/0015-finnhub-upcoming-eps.md).
These offline tests cover injected calendar payloads, exact signed Decimal/null
values, fixed analysis dates, fiscal periods, actual-present exclusion, unknown
metadata, duplicates, safe errors and bounded requests. Native transport tests
mock HTTPS and verify the Finnhub-only path/host, header authentication, redirect
refusal, bounded reads and response closure. FMP's transport allowlist and default
factories remain separate and unchanged. Installed-wheel verification exercises
the new capability with synthetic payloads and no account or provider calls.

The receipt clock is UTC; the caller's analysis/release dates use an explicit
date-only convention. Tests do not equate those dates or infer market timezone.
Same-day releases are excluded by this scope. No test authorizes live access,
claims complete future coverage or computes EPS growth/TTM/PEG/comparisons.
Full canonical Python, lint, configured type/dependency and staged-hygiene
checks remain required. Browser tests are separate and unnecessary for this
backend-only change. Live free-key probes require a separately authorized profile.

## M8 opt-in hosting and packaged dashboard — issues #142/#155

Run `python -m pytest tests/test_dashboard_hosting.py tests/test_api_foundation.py
tests/test_api_launcher.py tests/test_packaging.py -v` for source and installed
dashboard resources, exact Origin/Host matching, unchanged default refusals,
authentication, static path/method/query/body boundaries, safe missing assets,
headers and loader-issued configuration. These are offline ASGI tests without
a real listener. The installed-wheel probe serves actual packaged bytes and
checks the complete intended asset set; cold foundation/launcher probes also
construct opt-in apps and exercise health/schema under existing IO denial.
The original font and project/production dependency license notices are checked.
An isolated Git checkout-index regression enables core.autocrlf=true and verifies
LF-pinned generated text remains byte-identical on Windows checkout. The wheel
archive's complete five-resource byte set must match the reviewed source package.
No Node/browser dependency is introduced. Actual browser layout, font loading
and visual demonstration are separate manual verification, not implied by ASGI
success. The deliberate `frontend` command `npm run package:dashboard` builds and
copies only reviewed stable filenames; `npm run package:check` detects drift without
writes. No Python build hook invokes Node. See the frontend README for offline
fixture tests and separate actual source/wheel integration via `npm run test:integration`.
That profile launches the production loopback entry point with temporary synthetic
SQLite, process-only random credentials, disabled history and no API-route mocks.
It verifies asset/CSP/font parity, both namespaces, detail, overview and disabled
history while preserving SQLite bytes and absent cache/legacy paths. Browser and
canonical Python heavy suites run sequentially. Default pytest never starts a listener.

The independent #148 [exit audit](milestones/m8-exit-evidence.md) reuses this
actual source/installed-wheel launcher profile, adding keyboard/skip/table access
across eight viewport/theme combinations (including320 CSSpx), bounded user text
spacing/200% text checks, forced-colors/reduced-motion and real reload/401 clearing.
Its [reproduction guide](../frontend/AUDIT.md) distinguishes actual API operation
from the separate controlled successful-history fixtures and records accessibility
limitations, the narrowly corrected header wrap and remaining owner/CI exit gates.

## Unit tests

Unit tests cover isolated behavior such as:

- domain calculations
- validation
- provider-response parsing
- service behavior with fakes/mocks
- error mapping
- analytics formulas

Unit tests MUST NOT require:

- network access
- the user's database
- current stock prices
- current date/time unless explicitly controlled

## Integration tests

Integration tests cover:

- SQLite repositories
- schema/migration behavior
- application-service wiring
- provider adapters with controlled mocked HTTP responses
- CLI flows where appropriate

Integration tests must still avoid dependence on live third-party services.

## End-to-end tests

End-to-end tests MAY be introduced later for a REST/web application.

They require a separate execution profile and MUST NOT become a hidden dependency of fast local unit tests.

---

# 2. Canonical Commands

Use Python 3.11 or 3.12 in a fresh virtual environment created and activated
as described in the [canonical README setup](../README.md#canonical-setup).
From the checkout, use the same installation and verification commands:

```bash
python -m pip install ".[dev]"
python -m pip check
python -m pytest tests/test_baseline.py tests/test_packaging.py tests/test_repository_hygiene.py -v
python -m pytest
python -m ruff check .
python -m mypy
```

The targeted checks cover both CLI help surfaces in empty temporary working
directories, pinned dependencies/offline packaging and tracked-source hygiene.
For a narrower task, select the relevant test path with `python -m pytest <path> -v`.
Optional packaging verification uses
`python -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist`.

Agents must not claim a command passed unless it was actually executed.

Repository credential-pattern checks scan staged blobs, including binary assets.
Only blob content uses UTF-8 `surrogateescape` to preserve undecodable bytes
while retaining ASCII assignment/URL detection; other Git output stays strict.
No binary extension is skipped. The isolated binary regression verifies clean
data, synthetic credential patterns and an unstaged cleanup that must not hide
staged findings. Diagnostics report paths/line numbers, never credential values.

`pytest` and `ruff check .` are equivalent console-script invocations in the
activated environment. Pytest is
configured to collect `test_*.py` under `tests/`; root-level `test.py` is a
sanitized manual live-provider scratch script and must only run explicitly.
The checkout is placed on the test import path so both pytest invocations
verify current source instead of an older installed wheel.
Mypy checks the scope configured below; the added `src/stock_tracker` package
does not automatically expand that configured scope.
Ruff's explicit baseline in
`pyproject.toml` selects `E4`, `E7`, `E9` and `F`: import/statement errors,
syntax errors and Pyflakes checks such as undefined names and unused imports.
These are Ruff's default rule families, made explicit to keep the baseline
focused without imposing a broad style rewrite. The target is `py311`, the
oldest supported runtime in ADR-0005; Python 3.12 remains supported.
`ruff check .` covers application modules, automated tests and the sanitized
scratch script `test.py`. Standard Ruff artifact/virtual-environment exclusions
and Git ignore rules apply; there are no source exclusions, rule ignores or
per-file suppressions. No formatter is introduced by this lint baseline.

The baseline covers compilation of every tracked Python module, independent
watchlists, add/remove/presence, ticker listing, both CLI help surfaces, and
the explicitly unavailable unfinished evaluation method. Provider semantics,
financial calculations and persistence were separately scoped work at that
foundation snapshot. Subsequent M1–M3 evidence below records their implemented
scope; baseline checks alone do not certify those milestones.

## Type-check readiness decision — issue #11

Implements DEV-001 and TEST-005; SRS §23 permits type checking when ready.
After the foundation repairs, `config.py` is ready: its configuration dataclass,
loader and credential validator have explicit annotations, including nullable
keys and the validator's non-null return. Enable strict mypy for this real
runtime module through `[tool.mypy]` in `pyproject.toml`. Run `python -m mypy`
from the checkout after the canonical development installation, locally and in
the Foundation CI workflow. The pinned dev extra includes mypy and its additional
dependency; existing runtime pins supply typing_extensions. No separate tooling workflow
or stubs are introduced. Mypy follows the typed dotenv dependency normally;
there are no missing-import ignores, error suppressions or skipped imports.
Tests and fixtures are not substituted for the checked runtime source.

This is a configuration baseline, not whole-application type coverage. The
inspected legacy gaps are:

- `stock.py` is now an external legacy facade over typed numeric domain models.
  Its display fields remain strings/sentinels and external methods are not all
  annotated. The domain has an accepted typed contract, but this configured
  check still covers only `config.py`.
- `watch_list.py`: the bare `list` loses element types, `add_stock` accepts
  `object`, and methods access Stock attributes through untyped collections.
  M1 owns typed domain collections as part of its refactor.
- `utils/utility_module.py`: JSON parsing has an untyped payload and a `None`
  failure return; CSV collections are unparameterized. M2 owns provider typing
  and error contracts, with no provider behavior changes in M0.
- `menu_watchlist.py` and `daniils_stock_method.py`: untyped command functions
  consume the legacy facade and SQLite-restored watchlists. Ownership prompts delegate
  validation to the domain; configured mypy coverage still does not check
  CLI/persistence modules. `test.py` remains a manual scratch script outside this baseline.

Review evidence with `git ls-files '*.py'`, `git grep -n 'load_configuration'`,
and the source links: [configuration](../config.py), [Stock](../stock.py),
[watchlist](../watch_list.py), [utility](../utils/utility_module.py),
[menu CLI](../menu_watchlist.py), [evaluation CLI](../daniils_stock_method.py).
These gaps are deliberately deferred, not hidden with checker suppressions.
Expand `files` only when the corresponding maintained modules are ready.

When changing the baseline, verify enforcement: temporarily introduce an
incompatible annotated assignment in `config.py`, run the exact command above
and require a nonzero exit with an assignment error in that file. Remove the
probe and rerun successfully before committing. This check does not import or
execute credential loading and requires no credentials or provider transport.

---

# 3. Determinism

## M6 local application-service boundary — issue #114

Run `python -m pytest tests/test_watchlist_service.py tests/test_service_boundary.py
tests/test_packaging.py tests/test_sqlite_watchlists.py tests/test_cli_persistence.py -v`.
The injected local service tests use real domain calculations and temporary
SQLite state, checking complete input revalidation before IO, exact namespace
selection, missing/corrupt/future-schema refusal, existence-only legacy protection,
precise Decimal/None/unowned state, ordered rows and compatible forward-removal
behavior. Saved percentage/market-cap strings remain opaque display metadata.

`watchlist_service_probe.py` runs in fresh source and offline installed-wheel
processes. Its boundary phase installs and proves UI/facade/configuration/
concrete-provider/database/network/environment/legacy-deserialization guards
before importing services, then executes real local use cases over a neutral
repository fake. Separate write/read phases use an explicit temporary SQLite
repository and existence adapter, verifying both namespaces, exact restart state,
no reads of opaque legacy contents and unchanged database bytes after local
display. This checks #114's service capability; existing root commands are not
yet integrated with it. Current-data/history implementations, thin CLI wiring
and combined M6 exit evidence belong to their later bounded issues.

## M6 current-data application service — issue #115

Run `python -m pytest tests/test_current_data_service.py
tests/test_current_service_boundary.py tests/test_stock_facade.py
tests/test_provider_integration.py tests/test_cli_ownership.py
tests/test_packaging.py -v`. Typed controlled providers exercise lookup/profile/
period order, candidate identity validation, exact ownership grammar, repeated
input without new requests, raw numeric payloads, known snapshots and ordered
refresh progress. Stage failure matrices preserve error categories, ownership
and quote/period invalidation. Configuration acquisition callbacks execute once;
callback programming/application failures propagate without duplicate progress.
Malformed typed/frozen candidates are revalidated before publication.

The pure decimal parser is shared with the unchanged legacy conversion surface.
`current_data_service_probe.py` denies and proves UI/facade/configuration/concrete
provider/database/network/environment/legacy IO boundaries before cold service
imports, then executes add, ownership validation and refresh under those guards
in fresh source and offline installed-wheel processes. Services never save or
format market values; display projection and root command integration remain
issue #117. Existing facade and CLI regressions verify parser compatibility.

## M6 thin CLI adapters — issue #117

Run `python -m pytest tests/test_cli_service_integration.py
tests/test_cli_ownership.py tests/test_cli_persistence.py
tests/test_history_date_selection.py tests/test_configuration_security.py
tests/test_fmp_configuration.py tests/test_packaging.py -v`.
Both root command surfaces execute the actual application services. Typed fakes
enter at provider ports rather than facade orchestration, retaining existing
credential, error, ordering, precision, abort and saved-byte assertions.
Spies call through the real services to prove delegation; legacy market-data
methods are denied. Alias cases distinguish independent equal securities from
repeated references to the same facade, including a later refresh failure.

The owner-approved unowned input maps zero quantity plus exact `-` cost to
None; explicit numeric zero cost remains owned. Projection checks ordered
profile/period replay, row association and unchanged numeric inputs. History
checks retained plotting, current-key restoration, one fetch per request and a
cache path bound before cwd changes. Guarded source and installed-wheel restart
processes execute add/refresh/remove/show in both namespaces; historical exit
probes deny facade graph/fetch orchestration while exercising service/cache/
transport/render integration. The independent combined M6 exit remains #118.

## M6 combined independent-process exit audit — issue #118

Run `python -m pytest tests/test_cli_architecture.py tests/test_m6_exit.py
tests/test_packaging.py -v`. The bounded AST checker inspects actual service
dependencies and root command orchestration with controlled violations and safe
controls. Existing cold source/wheel probes remain the runtime isolation checks.

`m6_exit_probe.py` provides a standalone fixture independent of earlier test
helpers. Four fresh source and installed-wheel phases (write/read/failures/read)
combine actual commands and services, controlled transport with the real provider
parser, exact temporary SQLite state in both namespaces, a separate Portfolio,
unowned/zero/missing inputs, ordered duplicates, safe profile/period/programming
failures, offline help/display and cached raw historical graphing. Network,
pickle, legacy-content and explicit-database guards precede application imports
and are proved by controls. Spies call through real services; legacy market-data
orchestration is denied. Terminal-style EOF and subprocess deadlines bound abort
tests. See [M6 exit evidence](milestones/m6-exit-evidence.md) for the requirement
map, hand-derived fixture values, actual results and remaining completion gates.

Tests MUST be deterministic.

## Time

Tests MUST NOT depend directly on `datetime.now()`, `date.today()`, or the current market session without a controllable boundary.

Preferred patterns:

- inject a clock
- pass an explicit date/time
- patch the smallest clock boundary

Use fixed test timestamps.

## Market calendar behavior

Weekend and holiday behavior must be represented by explicit fixtures.

A test must not pass or fail depending on whether today's exchange is open.

## Randomness

If randomness is used:

- fix the seed
- avoid probabilistic pass/fail assertions

## Ordering

Tests MUST NOT depend on execution order.

Each test must create and clean up its own state.

---

# 4. Network Isolation

Normal automated tests MUST NOT call live market-data providers.

Use:

- mocked HTTP transports
- provider fakes
- recorded provider fixtures only if sanitized and stable

Fixtures MUST NOT contain real credentials.

`tests/conftest.py` blocks urllib transport and socket connection/DNS/datagram
operations by default. Denials fail tests even through legacy handlers that
catch ordinary exceptions. Tests import application modules inside test
functions or fixtures so these boundaries are active before application imports.
Mock transports explicitly when testing provider responses. Subprocess tests
must install their own network guard; parent-process patches do not propagate.
The packaging subprocess uses offline pip flags and its own socket guard.

Every test runs in its own `tmp_path` working directory, removes `FMP_API_KEY`
and the legacy `MY_API_KEY`
from its test environment, disables dotenv discovery at the loading boundary,
and redirects Matplotlib configuration to temporary storage with the Agg
backend. Import CLI modules only after isolation is active. This prevents
cwd-relative pickle/CSV access and source-relative dotenv discovery from
touching user state. Never import application modules at collection time.
Credential-loading regression tests opt into real dotenv parsing only for
explicit temporary files. They exercise all three runtime scripts and mock
only scratch-script transport work, using the actual Stock and Watch_list
classes. CLI tests also verify that the canonical key reaches ticker validation.
The CSV harness test writes only fictional ticker data in its temporary cwd.
M2 CLI ownership tests use the real FMP adapter through a factory-injected fake
HTTP transport for lookup, profiles and period summaries. Facade and CLI failure
matrices use typed fake providers over real domain calculations, checking price
invalidation, strict identity/currency conflicts and no save after failure.
Lookup tests deny CSV reads/writes
and preserve temporary CSV bytes on success and every failure. CSV entries are
unverified hints; check_ticker always performs exact supported provider lookup.

Issue #7 coverage also rejects missing/blank keys before add/refresh work,
checks the shared configuration representation and dotenv failure diagnostics,
and captures HTTP/URL/JSON/unexpected request logs using synthetic credentials.
Successful add coverage restores the real temporary SQLite namespace through
the maintained CLI load surface and checks its database bytes;
the shared Configuration object and runtime Stock.API_KEY are not persisted.
Facade compatibility tests use trusted synthetic legacy state, discard saved keys,
preserve numeric holdings and rebind current runtime configuration under ADR-0006.
Maintained CLIs no longer load/save pickle. Trusted synthetic facade compatibility
tests retain their narrow pickle checks; no test reads real legacy user data.

Test cases should cover:

- 200 success
- empty valid response
- malformed payload
- 400-class invalid request where relevant
- 404/not-found semantics where provider uses them
- 429/rate limiting
- 500-class transient failure
- timeout
- connection failure

Provider-specific behavior must be mapped to application-level exceptions according to the SRS.

---

# 5. Database Isolation

Persistence tests MUST use temporary databases.

Never point tests at the user's production/local application database.

Each test or test group must begin from a known schema state.

Test:

- inserts
- reads
- updates
- deletes
- uniqueness constraints
- foreign-key behavior
- transactions
- rollback behavior
- migrations
- data preservation across migrations where applicable

## M3 schema integration — issue #70

Run `python -m pytest tests/test_sqlite_migrations.py tests/test_packaging.py -v`.
Tests use real temporary SQLite files to check exact version-1 shape, both child
foreign keys/cascade, default lock timeout, encoded read-only paths, missing-file
absence and missing-parent failure. Unsupported versions, corrupt/unversioned
populated files and altered constraints/extra objects must be refused without
changing existing bytes. Injected DDL/commit failures prove schema, version and
rows roll back together and acquired connections close. Installed-wheel smoke
initializes/reopens a temporary database with its own urllib/socket network guard.
The persistence contract probe continues to prohibit database IO during package
imports. Repository/CLI restart and transfer/backup have separate included tests.
See [Persistence operations](PERSISTENCE.md) for the single runner and its limits.

## M3 CLI integration — issue #73

Run `python -m pytest tests/test_cli_persistence.py tests/test_cli_ownership.py
tests/test_configuration_security.py tests/test_provider_integration.py
tests/test_baseline.py tests/test_fmp_configuration.py tests/test_packaging.py -v`
as one command. Both root entrypoints use real temporary SQLite storage and
controlled providers. Existing known values, high precision, prompt counts,
unowned/missing quotes, provider call order and outage/no-match/abort byte
preservation remain checked. Storage failures must exit nonzero without success
messages; corruption/future schema/malformed records refuse empty replacement.

Import and every root/subcommand help surface are tested with missing keys,
synthetic legacy entries and corrupt state while database/pickle access and
legacy inspection are denied. Empty local display creates no database. Legacy
existence refuses absent-namespace load/save without opening contents; existing
namespaces stay authoritative. Controlled dangling-directory-entry and OSError
fixtures exercise existence-only protection without requiring OS symlink privileges.

`cli_persistence_probe.py` executes independent write/read processes against
source and the offline installed wheel with their own network/provider/pickle
guards. It runs actual add/local-display flows, persists both namespaces,
ordered duplicate and unowned entries, exact holdings and a separate Portfolio,
then proves restart display with no key and original synthetic legacy files
untouched. Fresh process paths are verified against source/wheel roots. Package
contract import guards remain unchanged. See [CLI storage](CLI_PERSISTENCE.md).
Milestone exit closure, neutral transfer and checked backup/restore remain separate
evidence; these tests do not certify all M3 requirements.

## M3 combined exit audit — issue #75

`tests/test_persistence_exit.py` and the installed-wheel audit in
`tests/test_packaging.py` launch the same independent-process helper,
`persistence_exit_probe.py`. It combines strict neutral import of a nonempty
precise Portfolio and both CLI namespaces, initial restart, checked backup,
restore to a new directory and fresh offline CLI/repository reads. Child processes
install and probe their own network/pickle/provider/legacy-content guards,
clear provider keys, disable dotenv discovery and verify runtime import paths.
Original JSON/database/opaque legacy fixtures are temporary and preserved.

The initial 2026-10-06 audit found a valid empty percentage-metadata display
regression. It was separately fixed in owner-merged PR #85 for #84; the
post-merge main checks passed. The combined fixture retains the exact empty
metadata and also verifies literal nonnumeric metadata, distinct exchanges and
zero-cost owned state. See [M3 exit evidence](milestones/m3-exit-evidence.md)
for current results, the historical failure, exact issue/PR/CI trace,
requirement mapping and completed audit merge/closure gates. Existing repository,
migration, transfer, precision and CLI failure matrices remain meaningful
separate evidence; they do not replace the combined exit criterion.

## M3 completion evidence — 2026-10-06

M3 is complete on owner-merged main `534a178005a5dd5662ec0cb261cadaf3ce5f2888`
(PR #86). All nine required issues (#68–75 and #84) and milestone 4 are closed.
The reviewed head's identical merged tree passed 1,850 full pytest tests;
final merged-main targeted persistence verification passed 498 tests in
43.45 seconds. All five checks in
[Foundation run 37533716609](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37533716609)
passed. [Exit evidence](milestones/m3-exit-evidence.md) records exact commands,
source/wheel combined restart, preservation/security guards and accepted limits.
Configured mypy still covers **config.py only**. These are milestone completion
results, not CI for subsequent documentation changes, whose actual verification
is recorded in their PR.

---

# 6. Financial Tests

Financial calculations require known-value tests.

For each metric:

1. Define the exact formula.
2. Provide simple hand-verifiable fixtures.
3. Test normal case.
4. Test zero denominator.
5. Test missing data.
6. Test negative values when valid.
7. Test precision/rounding boundary when relevant.

Do not obtain expected values from the implementation under test.

Expected results should come from the normative
[Financial Calculations Specification](FINANCIAL_CALCULATIONS.md) or
independently computed fixtures.

---

# 7. Price-History Tests

Historical-data tests must explicitly state whether they use:

- raw close
- adjusted close
- OHLC
- split-adjusted data
- dividend-adjusted data

Test fixtures should include at least one corporate-action scenario once that behavior is supported.

Do not infer historical prices from summary return percentages.

## M4 raw retrieval — issue #89

`tests/test_fmp_history.py` uses synthetic fixtures for the Stable
`historical-price-eod/non-split-adjusted` schema, reconfirmed against the
[official FMP guide](https://site.financialmodelingprep.com/how-to/fmp-historical-price-apis-from-light-charts-to-dividendadjusted-analysis)
on 2026-10-08. Its `adj*` fields map to raw OHLC; adjusted close stays unavailable.
Tests verify exact Decimal precision, OHLC bounds, zero/missing volume, the
signed-64-bit volume resource bound, strict dates, inclusive range/order,
duplicates and invalid rows outside range, fixed-clock input limits and empty
versus malformed classifications. Fake HTTP checks exact route/header/query,
bounded retries, safe failure categories and absence of hidden requests.
The existing guarded provider integration probe now exercises raw history in
both a source subprocess and the offline installed wheel, including receipt
metadata and public list isolation. These fixtures establish parser behavior,
not live entitlement, session completeness, adjusted returns or the M4 exit.
Cache, facade, chart and CLI integration are now completed #90–94 work with
their own coverage below; retrieval tests alone do not establish those contracts.

---

# 8. CLI Tests

CLI tests should verify behavior observable to the user without coupling unnecessarily to terminal formatting details.

Test:

- command success/failure
- validation
- meaningful error messages
- service invocation
- exit codes where relevant

Avoid asserting whole formatted tables unless formatting itself is the requirement.

---

# 9. Regression Testing

A bug fix SHOULD include a regression test.

Preferred workflow:

1. Reproduce the defect with a failing test.
2. Implement the smallest fix.
3. Confirm the new test passes.
4. Run related tests.
5. Run the full suite.

If reproducing the bug in a test is impractical, explain why in the PR.

---

# 10. Mocking Rules

Mock boundaries, not arbitrary internals.

Good mock targets:

- HTTP transport
- market provider interface
- clock
- repository interface
- filesystem boundary

Avoid mocks that simply return the implementation's desired output from the method under test.

Tests should verify behavior, not implementation trivia.

---

# 11. Fixtures

Fixtures should be:

- small
- explicit
- reusable only where reuse improves clarity
- sanitized
- stable

Provider-response fixtures must identify the provider/schema version or date when useful.

Do not store unnecessarily large live payloads.

---

# 12. Coverage

Coverage percentage alone is not a quality target.

Prioritize coverage for:

- financial calculations
- persistence/migrations
- provider parsing
- error handling
- security-sensitive boundaries
- regression-prone logic

A high percentage does not justify weak assertions.

---

# 13. Flaky Test Policy

A flaky test is a defect.

Do not repeatedly rerun CI until it passes.

When a flaky test is found:

1. reproduce if possible
2. identify nondeterministic dependency
3. isolate time/network/randomness/shared state
4. fix or quarantine only with an issue and justification

Skipping a flaky test permanently is not an acceptable default resolution.

---

# 14. Failure Diagnostics

Tests should fail with enough information to identify:

- input
- expected result
- actual result
- relevant identifier/symbol/date

Do not expose credentials in failure output.

---

# 15. Test Data Safety

Test data must be fictional or public/non-sensitive.

Do not use personal brokerage data, passwords, API keys, or private account information.

---

# 16. CI Contract

CI should fail when:

- tests fail
- linting fails
- type checking fails once configured
- secret scanning fails
- migration checks fail once configured

Required CI checks should be enforced through branch protection when available.

Agents must not bypass failed required checks.

## Foundation Actions workflow — issue #12

`.github/workflows/foundation.yml` runs on every pull request and every push
to `main`, without path filters. The stable job/check names are:

| Check name | Command | Runtime |
| --- | --- | --- |
| Tests (Python 3.11) | `python -m pytest` | Python 3.11 |
| Tests (Python 3.12) | `python -m pytest` | Python 3.12 |
| Ruff | `python -m ruff check .` | Python 3.11 |
| Mypy (configuration) | `python -m mypy` | Python 3.11 |
| Credential patterns | `python -m pytest tests/test_repository_hygiene.py --tb=short` | Python 3.11 |

Each job uses an isolated Ubuntu 24.04 runner, the same exact-pinned
`python -m pip install ".[dev]"` strategy and `python -m pip check`.
Checkout/setup actions are pinned to commit SHAs. The token has only
`contents: read`, checkout does not persist it, and no job references secrets
or uses `pull_request_target`. Provider key variables are explicitly empty.
Package installation and action setup need internet access; normal tests
retain the default transport guard and temporary filesystem isolation in §4.
The matrix does not cancel other checks when one fails, and no failure is
ignored. Mypy enforces the readiness decision above on real `config.py`;
Ruff retains the existing source coverage and artifact exclusions.

The secret-scanning gate deliberately reuses the tested issue #4 scanner:
it examines **every tracked file in the checked-out Git index**, including
legacy Python, configuration, docs and CSV, without source exclusions.
It rejects nonempty literal credential assignments and credential-bearing URL
patterns, and reports file/line identifiers with redacted findings. Short
tracebacks omit local variables. This bounded scanner is justified for the
known repository exposures, requires no new dependency or scanning credential,
and includes synthetic-positive and safe-dynamic-value regression cases.
It does not certify arbitrary secret formats, binary artifacts, Git history,
or credential rotation. Generated/untracked artifacts are outside the scan.

Before changing this workflow, validate its syntax with `actionlint` and run
the canonical checks in a fresh supported-Python environment. Verify enforcement
using temporary probes: a failing pytest assertion, an undefined name for Ruff,
a staged synthetic credential assignment for the index scanner, and an
incompatible annotated assignment in `config.py` for mypy. Require nonzero
exits, verify scanner output omits the synthetic value, and remove all probes
(including the staged probe) before final checks or commits. Never use a real
credential or weaken checks to demonstrate a passing run.

Only the repository owner may configure branch protection/rulesets. After
these checks have appeared on a PR, the owner can select all five exact names
above as required checks for `main` in repository Settings, using GitHub Actions
as the source where available. This workflow creates checks; it does not change
protections or bypass them. Record the PR Actions run URL and results in review
evidence. A passing `main` run after an owner-authorized merge is required
before issue #12 can close; agents must not merge to obtain it.

### Recorded main CI evidence — 2026-10-03

The [Foundation run after PR #34](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37147831762)
passed all five checks on `main` at
`40ebf656f2017b59b31845696efc19e0e2b139bd`. The
[Foundation run after PR #35](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37149517565)
also passed all five checks at
`e0bbeb1b743405a5019e11d55eaea7577aa03977`, including the canonical setup docs.
Both are completed push runs on `main`, rather than PR-only verification.
This satisfies issue #12's main-run evidence requirement. Its implementation
was merged in [PR #34](https://github.com/daniilnahl/Stock-Tracking-App/pull/34);
the owner confirmed completion and its issue state was reconciled to completed.
All thirteen required M0 issues are closed, with no open M0 blocker.
See the [M0 verification record](milestones/m0-verification.md) for local
verification, requirement coverage and the limits of this foundation baseline.
Branch-protection enforcement has not been verified or changed by this review.

---

# 17. Manual Verification

Manual verification may complement automated tests but must not replace them for deterministic logic.

Manual checks are useful for:

- CLI usability
- chart appearance
- installation flow
- release packaging

PRs should state exactly what was manually verified.

---

# 18. Test Completion Checklist

Before PR creation:

```text
[ ] Targeted tests pass
[ ] Full pytest suite passes
[ ] Ruff passes
[ ] Type checking passes when configured
[ ] No live provider calls occurred
[ ] No real user database was modified
[ ] No secrets exist in fixtures/logs
[ ] Regression tests were added for bug fixes where practical
[ ] Time/randomness are controlled where relevant
```

## M5 combined snapshot audit — issue #107

Run `python -m pytest tests/test_analytics_exit.py tests/test_snapshot_analytics.py
tests/test_position_calculations.py tests/test_sqlite_portfolios.py
tests/test_domain_isolation.py tests/test_packaging.py -v` for hand-derived
financial cases, exact SQLite restart and real source/installed-wheel isolation.
`analytics_exit_probe.py` uses independent write/read/read processes and synthetic
holdings; quote/currency assertions are supplied explicitly after restoration.
The actual pure calculation runs under the existing domain probe's reusable
`isolated_domain()` guards and violation controls. Cold import isolation remains
independently tested. Network/pickle are denied during storage setup; SQL/data IO,
environment, infrastructure imports and output are denied during computation.
Exact schema/input rows and database bytes remain unchanged by analytics and
across restart. No currency or derived metric is persisted. See
[M5 exit evidence](milestones/m5-exit-evidence.md) for accepted scope, metric/test
mapping and completion evidence. Audit PR #110 is owner-merged on main
`11f7333abdac830e139dd74354c87b30fe4cd45d`; required exact PR/main CI passed
all five checks and #107 is closed completed. The Master reran the focused
merged-main source/wheel audit: **180 passed in 49.10s**. Independent final review
passed and milestone 6 is closed with zero open/seven closed items, recorded in
the exit evidence and
[completion report](https://github.com/daniilnahl/Stock-Tracking-App/issues/107#issuecomment-6139320638).
Completion-documentation verification is
separate from these implemented-behavior checks. No testing contract changes.

## M1 domain isolation — issue #33

Run the focused source, offline wheel and staged-index security checks with:

```bash
python -m pytest tests/test_domain_isolation.py tests/test_packaging.py tests/test_repository_hygiene.py -v
```

`tests/domain_isolation_probe.py` is a subprocess helper, not a live application
entry point. Source and installed-wheel tests launch it independently with
`python -I` and an explicit application import root. It installs its own resolved
import/environment/network/database/data-IO/output guards before domain imports;
parent pytest patches are not assumed to propagate. Safe synthetic probes verify
the guards, then actual models and known/missing/zero snapshot cases execute.
Installed module paths must lie inside the wheel target, and that domain-only
process runs before a separate legacy root-module smoke. Exact wheel contents
still exclude tests, local state, CSV and scratch files. Import-loader code reads
remain possible; ordinary data opens/output are denied.

The stronger focused probe replaces the earlier narrow Stock subprocess smoke.
Financial correctness remains covered by independent known-value tests in
`test_position_calculations.py`; facade and both CLI flows retain real domain
arithmetic under mocked infrastructure. Strict mypy still checks `config.py`
only. See [M1 evidence](milestones/m1-exit-evidence.md) for requirement/test/topic
PR mapping and the [2026-10-04 completion review](milestones/m1-exit-evidence.md#completion-review--2026-10-04).
Owner-merged PR #46 includes the domain, facade, CLI and isolation tests on
`main` at `788d3c4119e9ebb196256e9355f24ce8b31dc037`; all nine required M1
issues are closed. The [post-merge Foundation run](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37214866386)
passed Tests (Python 3.11), Tests (Python 3.12), Ruff, Mypy (configuration)
and Credential patterns. This establishes M1 exit evidence without expanding
configured mypy coverage or certifying later provider/persistence/history work.

## M2 completion evidence — 2026-10-05

The [M2 completion review](milestones/m2-exit-evidence.md#completion-review--2026-10-05)
records 301 focused exit-audit cases, 1,334 full pytest cases, Ruff and configured
mypy (one source file, `config.py`) passing on completed implementation main
`5eccf3b24edbe03a6f01e86b9dfcffb80a1ad0c7`. Human-merged PR #67's
[exact-head Foundation run](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37345838578)
and [post-merge main run](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37346059176)
passed all five checks. All ten required M2 issues and milestone 3 are closed.
Source boundary violation controls, installed-wheel provider/facade probes,
scoped no-match rejection and malformed/provider failure matrices establish
M2 evidence using synthetic offline fixtures. This does not expand mypy scope,
prove global ticker nonexistence/search completeness or certify later historical,
persistence or analytics behavior. Current documentation-only verification is
reported separately in its PR; earlier implementation runs are not its CI.

## M4 historical cache — issue #90

Run `python -m pytest tests/test_history_cache.py tests/test_fmp_history.py
tests/test_packaging.py -v` for explicit-path cache policy, precise neutral JSON,
request counts, freshness boundaries, malformed-data preservation and atomic
write failures. Fixed UTC clocks, injected receipt loaders and temporary files
keep these checks deterministic and offline. `history_cache_probe.py` independently
denies network and pickle in write/read subprocesses for source and installed-wheel
reuse. Windows without symlink creation privilege exercises the lstat refusal
boundary with a synthetic symlink mode; privileged/POSIX runs use a real symlink.
The existing holdings isolation probes retain their provider-free contracts.
See [cache operations](HISTORICAL_CACHE.md) for bounds and failure behavior.
This verifies the cache capability. Production composition and the combined
exit are completed #91/#94 work with separate evidence below.

## M4 historical composition — issue #91

Run `python -m pytest tests/test_history_integration.py tests/test_history_cache.py
tests/test_fmp_history.py tests/test_packaging.py -v` for the historical factory
and additive facade boundary. Fixed UTC clocks, temporary working directories
and synthetic transport results verify exact production policy, persistent reuse,
default/explicit ranges, the NASDAQ gate, fake-result validation, restored runtime
keys and unchanged holdings/summary state. `history_integration_probe.py` denies
network and pickle and checks real composition reuse across write/read processes
for source and installed wheels. The renderer and CLI are completed #92/#93
work; the combined #94 audit below verifies their integrated M4 exit.

## M4 historical charts — issue #92

Run `python -m pytest tests/test_history_charts.py tests/test_stock_facade.py
tests/test_history_integration.py tests/test_packaging.py -v` for actual Agg
dates/closes, marker-only sparse observations, requested/observed labels and
rendering limits. Every Decimal close is converted before figure creation;
overflow and positive underflow fail safely while genuine zero remains usable.
Fixed clocks verify one range resolution and matching request/title dates.
The source and installed-wheel composition probe renders cached raw closes
without network or state mutation. Completed #93 tests verify CLI date options
and safe error handling; #94 establishes the combined exit. None of these tests
certify live entitlement.

## M4 CLI date selection — issue #93

Run `python -m pytest tests/test_history_date_selection.py tests/test_history_charts.py
tests/test_history_integration.py tests/test_cli_persistence.py tests/test_packaging.py -v`
for paired exact ISO options, default leap-day selection, real request/cache/chart
data, unsupported identity before key checks, safe typed errors and unchanged
SQLite bytes. Fixed clocks and temporary storage keep the tests offline.
Restored stocks use the current runtime key; temporary key bindings are restored
after success, anticipated failures and programming errors. Watchlist tests
preserve ordered duplicates and default no-argument Stock-like callers.
The source/installed-wheel history probe executes the actual cached CLI graph,
invalid ISO rejection and help with command preflight denied. Existing help and
domain isolation probes remain required. These checks do not replace #94's
combined exit audit or verify live provider entitlement/session completeness.

## M4 combined exit audit — issue #94

`tests/test_history_exit.py` and the installed-wheel audit in
`tests/test_packaging.py` launch `history_exit_probe.py` in independent write,
read and expired processes. Each child sets its own fixed UTC time and temporary
configuration, verifies network/pickle/legacy-content/outside-write/database
guards before application imports, and checks source/wheel module origins.
Only the HTTP opener is synthetic: production request construction, parser,
factory, persistent cache, SQLite restore, facade, Agg renderer and CLI execute.
Sparse precise raw closes and a split-like discontinuity reach chart markers;
current quotes, summary percentages and saved currency cannot supply the chart.
Fresh restart reuse makes no HTTP request, while exact one-hour expiry performs
the accepted bounded retries and fails safely without stale chart data or cache/
holdings replacement. Both CLI namespaces, database bytes/schema version 1 and
opaque legacy files remain preserved. Existing unit/error/resource matrices and
domain/M3 preservation probes remain required alongside this combined scenario.
See [completed M4 exit evidence](milestones/m4-exit-evidence.md) for actual
verification and passed owner-merge/main-CI/closure gates. No live entitlement or session
completeness is inferred from these controlled provider-schema fixtures.

## M4 completion and documentation reconciliation

M4 implementation is complete under accepted ADR-0010. All seven required issues
and their implementation PRs are closed; the combined audit and post-owner-merge
main CI passed. PR #102's completion record is also owner-merged. Its
[main run 38341070787](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38341070787)
passed all five configured checks. The user-requested documentation review
reran the full focused M4 command: **350 passed in 51.32 seconds**, and full
pytest: **2,170 passed in 87.98 seconds**. Ruff, configured mypy (`config.py`
only) and pip check passed in canonical Python 3.11.9.

The [completion evidence](milestones/m4-exit-evidence.md) retains earlier audit
results as dated records. Current operation docs reflect completed graph/date/
cache behavior; older milestone/ADR snapshots identify their historical scope.
This reconciliation changes no runtime, tests, dependency, formula or contract.

## M6 historical retrieval service — issue #116

Run `python -m pytest tests/test_history_service.py tests/test_history_integration.py
tests/test_history_date_selection.py tests/test_service_boundary.py tests/test_packaging.py -v`.
The injected `HistoryService` returns the accepted immutable `HistoryView` with
one resolved request range and exact sparse raw Decimal observations. Fixed-clock
tests cover NASDAQ identity before provider acquisition, row ordinals, default
leap-day fallback, inclusive limits, missing/invalid bars, authoritative model
validation, unchanged error objects and absence of retry or presentation work.
An injected production historical provider verifies cache reuse and expiry failure
without stale fallback, cache replacement or SQLite creation.

`history_service_probe.py` runs against fresh source and installed-wheel imports
with UI, configuration, legacy facades, concrete providers/persistence, network,
environment, data IO and output denied. Negative controls prove the guards work
before the real service executes with a typed fake. Existing facade/range wrappers
retain their late-bound clock and list-return surfaces while sharing pure service
policy. Root command and renderer integration remains separately scoped #117;
these checks do not certify live entitlement or historical session completeness.

## M6 completion reconciliation and manual showcase — issue #126

Audit PR #125 is owner-merged at `237c4c5f7d9825c284d706d6730bcdf9ed3510f6`.
Its exact-head Foundation `38496384271` and post-merge main `38500809992` passed
all five checks, including Python 3.11/3.12. All required issues #112–118 are
closed completed under accepted ADR-0012 Option A.

Current merged-main Python 3.12.10 verification: combined architecture, service
boundary, source and installed-wheel command passed **34 in 61.69s**; full pytest
passed **2507 in 132.58s**. Ruff, configured mypy (`config.py` only) and pip check
passed. This documentation change adds no runtime behavior or testing contract.

The [manual CLI showcase](CLI_SHOWCASE.md) records actual commands, state isolation
and provider provenance separately. Live market requests are optional manual
checks and never become an automated-test dependency or replace deterministic
known-value fixtures. Manual entitlement failures do not justify weakening
provider validation, identity checks, credential handling or tests.

## M7 REST foundation — issue #130

Run `python -m pytest tests/test_api_foundation.py tests/test_api_serialization.py
tests/test_api_boundary.py tests/test_packaging.py -v` for injected health/schema,
exact neutral serialization, fixed safe failures, access/body/size boundaries,
admission/actual disconnect and cancellation-before-start regressions, and cold
source/installed-wheel isolation. In-process ASGI needs no application listener.
The Windows module-owned event loop bootstraps native control sockets before
normal per-test network denial; explicit connect/getaddrinfo controls prove
application transport remains denied. Independent subprocess guards disclose
their narrowly allowed framework code-metadata/tuning reads while prohibiting
application credentials, ordinary data IO, concrete storage/providers and UI.
See [API foundation details](API_FOUNDATION.md) for dependency decisions,
boundary exceptions, the typed OpenAPI snapshot and the remaining route/launcher
scope. This check establishes foundation behavior, not M7 completion or rights.

## M7 saved watchlist route - issue #131

Add `tests/test_api_watchlists.py` to the focused API verification above. It
executes real shared services with temporary SQLite state, verifying exact
Decimal and zero/null/unowned snapshots, namespace binding and ordered duplicate
rows. Successful, missing, corrupt and future-schema reads preserve bytes and
never create missing state; legacy checks inspect existence without pickle reads.
HTTP rejection precedes service acquisition, and actual route tests enforce
admission and bounded responses. The unchanged cold source/wheel guards also
execute both namespaces through the shared service without configuration,
provider/cache, SQL or ordinary file IO. This remains an injected adapter test,
not production launcher or historical acquisition certification.

## M7 stored-entry history route - issue #132

Add `tests/test_api_history.py` to the focused API command. Real temporary SQLite
records and the actual HistoryService prove exact duplicate ordinals, namespace
and Stock association, paired ISO syntax, leap-day UTC defaults, range validation
and NASDAQ refusal. Sparse precise OHLC values, null adjusted values/volume and
maximum integer volume cross JSON losslessly. Typed failures and missing/corrupt/
future state preserve holdings and opaque legacy bytes. A real historical cache
with a controlled observation loader proves restart reuse, exact TTL expiry and
no stale fallback. Access/disabled checks prohibit dependency acquisition.
Actual-route cancellation and closed ASGI delivery keep admission until provider
termination, with deterministic worker completion rather than timing polls.
Cold source and installed-wheel foundation probes now invoke stored history via
the real shared service under independently proven network, configuration,
ordinary IO, concrete infrastructure and UI import guards. The reviewed schema
snapshot documents unique typed request parameters and exact integer limits.
Production composition, launcher, live rights and combined M7 exit remain #133–134.

## M7 local composition and launcher — issue #133

Add `tests/test_api_launcher.py` to the focused API command. It verifies the
required process-only token, fixed safe parser/startup failures, four resolved
distinct paths, actual temporary hard links, native Windows ambiguous namespace
aliases, native junction/reparse-point handling and symlink handling. Tests
exercise real temporary junctions on Windows and synthetic non-symlink reparse
metadata on all platforms. Tests attempt real symlink creation; Windows
without privilege uses synthetic metadata/resolution refusal fixtures instead
of changing system settings. Loader-only configuration issuance prevents an
unchecked constructor from bypassing alias validation, while composition
validates its provenance without repeating filesystem resolution.

Actual shared WatchlistService/SQLite views preserve both namespaces, duplicate
rows, holdings and opaque legacy bytes. Typed fake historical factories verify
lazy existing configuration, explicit cache path, accepted provenance and safe
upstream configuration errors; invalid identity/range/row requests acquire no
provider configuration. Uvicorn is replaced only at its run boundary to verify
fixed loopback/worker/log/proxy settings without a listener. Cold source and
installed-wheel `api_launcher_probe.py` imports/help run under the independently
proven foundation guards before a separately disclosed synthetic-token/metadata
launch preflight. No-IO health/schema/disabled-history then use the issued
production configuration. Safe category logs are captured explicitly; ordinary
output, credentials, providers, SQL, network and data contents remain denied.
The static help/parser avoids locale and terminal environment/file discovery.
See [local API operation](API_OPERATIONS.md). Live rights and the combined M7
exit audit remain independent gates.

## M7 combined REST exit audit — issue #134

Run `python -m pytest tests/test_m7_exit.py tests/test_api_foundation.py
tests/test_api_serialization.py tests/test_api_boundary.py tests/test_api_watchlists.py
tests/test_api_history.py tests/test_api_launcher.py tests/test_packaging.py -v`.
The source and installed-wheel `m7_exit_probe.py` children execute real local API
composition, shared services, temporary SQLite, production factory/FMP parser and
JSON cache behind a synthetic HTTP opener. Independent write/read/expired
processes prove exact values, namespace-specific duplicate selection, saved-view
zero/null/unowned distinctions, restart reuse and exact one-hour expiry without
stale fallback or holdings/legacy changes. Proven network, pickle, legacy-content,
outside-write/atomic-move and explicit-database guards include a denial ledger;
safe HTTP errors cannot hide violations. Native Windows event-loop control
sockets bootstrap before network denial. Import/framework and installed TLS CA
reads remain possible; dotenv discovery is disabled and all credentials are
synthetic. Existing cold import/help probes and broad access/cancellation/error
matrices remain independently required. See [M7 exit evidence](milestones/m7-exit-evidence.md)
for guard exceptions and the historical requirement mapping. The audit issue
is closed and delivered; see [current status](CURRENT_STATUS.md) for technical
versus administrative milestone state. It does not certify live entitlement.
