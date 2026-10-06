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
financial calculations and persistence migration remain separately scoped work.

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
  consume the legacy facade and `pickle.load` results. Ownership prompts delegate
  validation to the domain; M3/M6 own persistence/presentation
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
imports. Repository/CLI restart and transfer/backup evidence remain later issues.
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
