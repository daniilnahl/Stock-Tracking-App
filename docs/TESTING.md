# Testing Strategy

## Purpose

This document defines the testing contract for the Stock Tracking App.

The goal is to make tests deterministic, meaningful, isolated, and suitable for both human and AI-driven development.

---

# 1. Test Layers

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

Use repository-configured commands.

Expected baseline:

```bash
pytest
ruff check .
```

Type checking (the configured M0 scope):

```bash
python -m mypy
```

Targeted example:

```bash
pytest tests/test_baseline.py -v
```

Agents must not claim a command passed unless it was actually executed.

Use Python 3.11 or 3.12 and install the pinned development environment with
`python -m pip install ".[dev]"`. `python -m pytest` and
`python -m ruff check .` are equivalent module-based invocations. Pytest is
configured to collect `test_*.py` under `tests/`; root-level `test.py` is a
sanitized manual live-provider scratch script and must only run explicitly.
The checkout is placed on the test import path so both pytest invocations
verify current source instead of an older installed wheel.
Mypy checks the scope configured below; no `src/` layout exists yet.
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
financial calculations and persistence migration remain separately scoped work.

## Type-check readiness decision — issue #11

Implements DEV-001 and TEST-005; SRS §23 permits type checking when ready.
After the foundation repairs, `config.py` is ready: its configuration dataclass,
loader and credential validator have explicit annotations, including nullable
keys and the validator's non-null return. Enable strict mypy for this real
runtime module through `[tool.mypy]` in `pyproject.toml`. Run `python -m mypy`
from the checkout after the canonical development installation, locally and in
future CI. The pinned dev extra includes mypy and its additional dependency;
existing runtime pins supply typing_extensions. No separate tooling workflow
or stubs are introduced. Mypy follows the typed dotenv dependency normally;
there are no missing-import ignores, error suppressions or skipped imports.
Tests and fixtures are not substituted for the checked runtime source.

This is a configuration baseline, not whole-application type coverage. The
inspected legacy gaps are:

- `stock.py`: fields annotated `str` default to `None`; prices, ownership and
  returns are formatted strings or sentinel values, and most methods lack
  return annotations. M1 owns readiness work alongside the specified domain
  isolation and numeric model; this task does not define replacement interfaces.
- `watch_list.py`: the bare `list` loses element types, `add_stock` accepts
  `object`, and methods access Stock attributes through untyped collections.
  M1 owns typed domain collections as part of its refactor.
- `utils/utility_module.py`: JSON parsing has an untyped payload and a `None`
  failure return; CSV collections are unparameterized. M2 owns provider typing
  and error contracts, with no provider behavior changes in M0.
- `menu_watchlist.py` and `daniils_stock_method.py`: untyped command functions
  consume the legacy models and `pickle.load` results. M1 should reassess these
  callers after domain contracts stabilize; M3/M6 own persistence/presentation
  migration. `test.py` remains a manual scratch script outside this baseline.

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

Issue #7 coverage also rejects missing/blank keys before add/refresh work,
checks the shared configuration representation and dotenv failure diagnostics,
and captures HTTP/URL/JSON/unexpected request logs using synthetic credentials.
Successful add coverage inspects only a pickle produced in its temporary path;
the shared Configuration object is not persisted, while legacy Stock.API_KEY
storage remains explicitly covered as a deferred limitation.

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
evidence. Issue #12 and M0 must remain open until a passing `main` run is also
recorded after an owner-authorized merge; agents must not merge to obtain it.

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
