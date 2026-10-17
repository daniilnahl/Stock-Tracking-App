# Stock Tracking App — Software Requirements Specification

**Version:** 1.2 proposed (approved baseline: 1.1)

**Status:** PARTIALLY ACCEPTED — M7 under ADR-0013; M8 under ADR-0014's read-only scope and approved design revisions; M9's bounded Finnhub upcoming-release EPS observation task under ADR-0015. Remaining M9–M10 and out-of-scope decisions remain proposed. Existing approved requirements remain authoritative.

**Primary implementation language:** Python  
**Current interface:** Typer CLI  
**Target:** Production-quality portfolio tracking and analytics application

## Approval record

**M9 bounded EPS task — 2026-10-16:** the owner explicitly requested
implementation of exact EPS observation/comparison rules and a narrowly scoped
Finnhub quarterly-EPS adapter, focusing on future estimated EPS, then selected
**“Upcoming release EPS estimate on Free (Recommended)”**. This authorizes
[ADR-0015](docs/adr/0015-finnhub-upcoming-eps.md) and EPS-001–004's reported-data
scope: an additive, explicitly injected backend calendar adapter, exact signed
numeric/null observations, unknown metadata and conservative comparison limits.
It does not approve computed EPS comparisons, TTM/growth/PEG, the Premium forward
series, a screen/ranking, live rights/access, default application activation,
research API/UI, persistence/scheduling, broader routing or the whole M9 proposal.
PR #167 is owner-merged at `74f787554e3cd7c7083738347a83c887e1a1c5d0`, with
post-merge Foundation CI passed. The owner's subsequent instruction to continue
authorizes the bounded injected application service in ADR-0015's #168 addendum:
retain explicit request context, obtain the intended research date once and
validate the existing raw observations without live/default activation. The
remaining exclusions above still apply. Issue-specific gates and accepted
M0–M8 contracts remain authoritative.

**M8 scoped acceptance — 2026-10-14:** after reviewing PR #149's revised
all-text retro pixel preview, requested unavailable placeholders, backend/
frontend TO-DO LIST and CI repair, the owner instructed **“approved continue
work”**. Owner merge was independently verified at
`dd7e9d52cb596f608bdb70c534407ae60d461be2`, containing reviewed head
`edeced0fe1d63ff3cf4a758b1f8e1d0ee72fe673`. This accepts §23.8/UI801–829 and
applicable cross-milestone requirements only within ADR-0014 Option A: local
opt-in same-origin read-only dashboard, exact M7 data, all-text original pixel
font, monochrome light/dark themes, memory-only access token and layout-only
unavailable future panels. D3 is resolved within that scope. Mutations, new
metrics, research/AI functionality, provider rights and external hosting remain
unapproved. Earlier proposal/M7-only records below retain their dated history;
they do not invalidate this scoped acceptance. See
[ADR-0014](docs/adr/0014-local-read-only-dashboard.md).

**M7 scoped acceptance — 2026-10-14:** following the explicit request to accept
the relevant M7 specification and Option A in PR #135, the owner instructed
**"pr merged, continue the work"**. Owner merge was verified at
`e03d116981c8c81b7899f7202040fefb23b9065b`, containing reviewed head
`94bde7d268bc423b907d89429e1c5d3b76c30c41`. This accepts M7 API701–724 and
applicable cross-milestone requirements only within accepted ADR-0013 Option A:
authenticated local holdings read-only views/history using M6 services. Its
precise endpoints, bounds, unknown provenance and activation gates resolve M7
D1/D2/D4. M8–M10, other decision gates, provider rights/entitlement, hosted
deployment, writes and new financial metrics remain unapproved. The proposal
wording below retains the original review history; it does not invalidate this
scoped acceptance. See [ADR-0013](docs/adr/0013-local-read-only-rest-api.md).

**M7–M10 proposal, prepared 2026-10-13 (America/Los_Angeles):** owner acceptance
is **PENDING**. The new §23 cross-milestone and M7–M10 text is a specification
change for review, not implementation authorization. Its MUST/SHOULD/MAY
language becomes normative only upon explicit owner acceptance. Existing
requirements, M0–M6 and accepted ADRs are preserved. The v1.1 record below
describes the approved baseline, not approval of this revision. See the
[conflict and decision report](docs/milestones/m7-m10-srs-review.md).

The repository owner approved SRS v1.1 on 2026-10-02 in the issue #2
implementation chat. The owner also explicitly authorized generating
`pyproject.toml` from the existing dependencies, making it the master dependency
file, and removing `reqs.txt` if environment setup no longer requires it.

For the v1.1 foundation revision, the only intentionally changed requirement
was DEV-003: its assertion that a
`pyproject.toml` workflow already existed has been corrected to the approved
canonical workflow below. Requirement IDs and milestone content are preserved.
See [ADR-0005](docs/adr/0005-canonical-python-dependencies.md) for the foundation
decision and the legacy repository evidence.

---

## 1. Purpose

The Stock Tracking App will evolve from a local CLI stock tracker into a well-architected financial software application capable of:

- Maintaining watchlists and portfolio positions.
- Retrieving current and historical market data.
- Calculating portfolio performance and analytics.
- Persisting data safely.
- Visualizing real historical market data.
- Exposing functionality through stable application interfaces.
- Supporting future REST API and web frontend development.
- Supporting safe, reviewable implementation by AI coding agents.

The application must prioritize correctness, security, testability, and traceability over feature volume.

---

## 2. Requirement Language

The terms **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are normative.

Each requirement has a stable identifier. GitHub issues and pull requests SHOULD reference the requirement IDs they implement.

Example:

```text
Implements: ARCH-001, DATA-003
```

---

## 3. Product Goals

- Clean separation between domain logic, persistence, external APIs, and presentation.
- Reliable market-data acquisition.
- Correct and explicitly defined financial calculations.
- Safe credential handling.
- Persistent portfolio data.
- Automated testing.
- Reproducible development environment.
- Small, independently reviewable pull requests.
- Architecture capable of supporting both CLI and web interfaces.
- Clear contracts for autonomous or semi-autonomous coding agents.

---

## 4. Non-Goals for Initial Development

The initial production-quality version will not include:

- Brokerage integration.
- Automated trading.
- Financial advice.
- Options trading.
- Cryptocurrency trading.
- High-frequency market data.
- Real-time order books.
- Tax filing.
- Machine-learning price prediction.
- Social/community features.

These require separate requirements and approval.

---

## 5. Current-System Context

The existing application includes:

- Python.
- Typer CLI.
- Stock/watchlist abstractions.
- Financial Modeling Prep market-data integration.
- Rich terminal tables.
- Matplotlib visualization.
- Local persistence.
- User-entered quantity owned and cost basis.

Existing behavior SHOULD remain backward compatible unless a requirement or approved issue explicitly authorizes a breaking change.

---

# 6. Architecture

## ARCH-001 — Layer separation

The application MUST separate:

```text
CLI / Presentation
        |
Application Services
        |
Domain / Analytics
   |           |
Persistence   Market Data
```

## ARCH-002 — Domain isolation

Domain entities MUST NOT:

- perform HTTP requests
- access environment variables
- issue SQL
- render CLI output
- hold API credentials

## ARCH-003 — Provider abstraction

Application/domain code MUST NOT depend directly on Financial Modeling Prep URLs or response schemas.

External market providers MUST implement a stable provider interface.

## ARCH-004 — Repository abstraction

Application/domain code MUST access persisted state through repository interfaces rather than direct database calls.

## ARCH-005 — Shared application services

Future CLI and REST interfaces MUST share the same application/service layer.

## ARCH-006 — Architecture changes

A material architecture change MUST be documented by an accepted ADR under `docs/adr/`.

---

# 7. Target Repository Structure

```text
stock-tracking-app/
│
├── src/
│   └── stock_tracker/
│       ├── cli/
│       ├── domain/
│       ├── services/
│       ├── providers/
│       ├── persistence/
│       ├── visualization/
│       ├── config.py
│       └── exceptions.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── docs/
│   ├── TESTING.md
│   ├── FINANCIAL_CALCULATIONS.md
│   └── adr/
│
├── .github/
│   ├── workflows/
│   ├── ISSUE_TEMPLATE/
│   └── pull_request_template.md
│
├── AGENTS.md
├── SRS.md
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

---

# 8. Domain Model

## DOM-001 — Stock

A Stock represents a security identity.

Recommended shape:

```python
@dataclass(frozen=True)
class Stock:
    symbol: str
    name: str | None = None
    exchange: str | None = None
```

A Stock MUST NOT contain credentials, database connections, HTTP clients, or mutable portfolio state.

## DOM-002 — Security identity

Ticker symbol alone MUST NOT be assumed globally unique.

Where provider capabilities permit, security identity SHOULD include exchange or another provider-stable instrument identifier.

## DOM-003 — Position

A Position represents ownership of a security.

```python
@dataclass
class Position:
    stock: Stock
    quantity: Decimal
    average_cost: Decimal
```

## DOM-004 — Portfolio

A Portfolio contains positions and portfolio identity.

```python
@dataclass
class Portfolio:
    id: int | None
    name: str
    positions: list[Position]
```

Database/API concerns MUST NOT be implemented inside Portfolio.

---

# 9. Financial Numeric Rules

## FIN-001 — Numeric values

Financial values MUST remain numeric internally.

Formatted strings such as `$143.25`, `12.8%`, and `1.5M` MUST NOT be stored as domain values.

## FIN-002 — Money precision

Monetary values SHOULD use `Decimal`.

Binary floating-point MAY be used for analytics where technically appropriate, but conversions and precision decisions MUST be documented and tested.

## FIN-003 — Rounding

Rounding MUST occur only at defined boundaries.

Presentation rounding MUST NOT mutate stored domain values.

The exact rounding conventions are defined in [docs/FINANCIAL_CALCULATIONS.md](docs/FINANCIAL_CALCULATIONS.md).

## FIN-004 — Calculation definitions

Any implemented financial metric MUST have:

- an explicit formula
- defined units
- missing-data behavior
- zero-denominator behavior
- at least one known-value unit test

## FIN-005 — Ambiguous metrics

Agents MUST NOT invent the meaning of an undefined financial metric.

If a metric is requested but not defined in [docs/FINANCIAL_CALCULATIONS.md](docs/FINANCIAL_CALCULATIONS.md), implementation MUST stop and the ambiguity MUST be escalated.

---

# 10. Market Data

## DATA-001 — Market provider

The application MUST initially support an `FMPMarketDataProvider`.

## DATA-002 — Provider interface

The provider interface SHOULD expose behavior equivalent to:

```python
class MarketDataProvider(Protocol):
    def get_quote(self, symbol: str) -> Quote:
        ...

    def get_company_profile(self, symbol: str) -> CompanyProfile:
        ...

    def get_price_history(
        self,
        symbol: str,
        start: date,
        end: date,
    ) -> list[PriceBar]:
        ...
```

## DATA-003 — Real historical data

Historical charts MUST use actual historical market data.

Synthetic historical prices inferred from periodic percentage-return values MUST NOT be used as a historical time series.

## DATA-004 — Historical price representation

Historical price data SHOULD include:

```text
timestamp/date
open
high
low
close
adjusted_close when available
volume
```

## DATA-005 — Corporate actions

The application MUST distinguish raw close from adjusted historical prices when the provider exposes both.

Return calculations MUST follow `docs/FINANCIAL_CALCULATIONS.md`.

## DATA-006 — Invalid symbol vs provider failure

The application MUST distinguish:

- invalid/unknown instrument
- valid instrument with unavailable data
- provider outage
- timeout
- rate limiting
- malformed provider response

A provider outage MUST NOT be interpreted as proof that a ticker is invalid.

**Approved scoped interpretation (ADR-0008, issue #66):** a completed,
schema-valid successful FMP identity search with no exact supported NASDAQ
match classifies a newly entered candidate as invalid for this application.
Reject it without adding or saving; never remove existing holdings. This
accepts incomplete/truncated-search false-negative risk and does not assert
global nonexistence or provider completeness. Malformed responses and provider
failures, including HTTP 404, retain their distinct errors. See
[ADR-0008](docs/adr/0008-scoped-ticker-rejection.md).

## DATA-007 — Time semantics

Market-data timestamps MUST have an explicit timezone or documented date-only meaning.

Internally stored event timestamps SHOULD use UTC unless exchange-local time is required.

## DATA-008 — Currency

Version 1 MUST NOT silently combine instruments denominated in different currencies.

Until FX support is explicitly implemented, mixed-currency portfolio analytics MUST either be rejected or clearly reported as unsupported.

---

# 11. Market Provider Reliability Contract

The following operational values MUST be configured before production use:

```text
HTTP timeout
maximum retry attempts
retryable HTTP status codes
429/rate-limit behavior
quote cache TTL
historical-data cache TTL
stale-cache fallback policy
```

Until exact values are approved, agents MUST preserve the current configured behavior and MUST NOT invent production defaults in unrelated tasks.

## DATA-009 — Retries

Retries MUST only be applied to failures considered transient.

## DATA-010 — Backoff

Retry behavior SHOULD use bounded exponential backoff with jitter where appropriate.

## DATA-011 — Idempotence

Read-only provider operations MUST be safe to retry.

---

# 12. Persistence

## PERS-001 — Primary storage

Python `pickle` MUST NOT remain the primary long-term application storage format.

SQLite is the initial structured persistence target.

## PERS-002 — Parameterized SQL

All SQL containing user or external input MUST use parameterized queries.

## PERS-003 — Foreign keys

SQLite foreign-key enforcement MUST be explicitly enabled when foreign keys are used.

## PERS-004 — Migration ownership

Schema changes MUST use one documented migration mechanism.

Agents MUST NOT introduce a second migration framework without an approved ADR.

## PERS-005 — Data preservation

Schema migrations MUST preserve user data unless destructive migration is explicitly approved.

## PERS-006 — Transactions

Multi-step persistence operations that must succeed atomically MUST run inside a database transaction.

## PERS-007 — Test isolation

Persistence tests MUST use isolated temporary databases and MUST NOT modify the user's real application database.

## PERS-008 — Schema decisions

Before implementing the first persistent schema, the project MUST explicitly define:

- database file location
- schema versioning mechanism
- uniqueness rules
- delete/cascade behavior
- migration procedure
- backup/restore expectations

These decisions SHOULD be captured in an ADR.

---

# 13. Portfolio Analytics

Core analytics MAY include:

- market value
- cost basis
- unrealized gain/loss
- percentage gain/loss
- portfolio allocation
- daily portfolio change
- historical portfolio value
- benchmark comparison
- volatility
- maximum drawdown
- Sharpe ratio
- beta
- correlation
- sector exposure

## AN-001 — Specification dependency

No analytics metric may be implemented until its semantics are defined in [docs/FINANCIAL_CALCULATIONS.md](docs/FINANCIAL_CALCULATIONS.md).

## AN-002 — Benchmark behavior

Benchmark calculations MUST define:

- benchmark symbol
- time alignment
- missing trading-day handling
- adjusted-vs-raw price usage
- return convention

---

# 14. Configuration and Secrets

## SEC-001 — No committed credentials

Active credentials MUST NOT be committed to source control.

## SEC-002 — Configuration layer

API credentials MUST be loaded through the application configuration layer.

## SEC-003 — Environment files

`.env` MUST be ignored by Git.

`.env.example` MAY document required variable names but MUST NOT contain usable secrets.

## SEC-004 — Secret exposure

Previously committed secrets MUST be treated as compromised and rotated outside the codebase.

## SEC-005 — Logging

Secrets MUST NOT appear in logs, exceptions intended for end users, fixtures, screenshots, or PR descriptions.

---

# 15. Development Environment

## DEV-001 — Canonical environment

The project MUST have one canonical development setup documented in the README.

## DEV-002 — Python version

The supported Python version MUST be declared in project configuration.

Agents MUST NOT change the supported Python version unless the task explicitly requires it.

## DEV-003 — Dependency management

Dependencies MUST be managed through the canonical `pyproject.toml` workflow,
using `python -m pip install .` from the repository checkout. `pyproject.toml`
is the master dependency file; a separately maintained `reqs.txt` MUST NOT be
used. This workflow replaces the legacy `reqs.txt` setup under the approved
foundation decision in [ADR-0005](docs/adr/0005-canonical-python-dependencies.md).

Agents MUST NOT introduce a competing package-management system without an approved ADR.

## DEV-004 — Reproducibility

The dependency strategy SHOULD provide reproducible installs through a lockfile or equivalent pinned-resolution mechanism.

The exact tool MAY remain project-selected, but only one canonical mechanism should be documented.

---

# 16. Testing

Testing policy is defined in `docs/TESTING.md`.

## TEST-001 — Framework

`pytest` is the test framework.

## TEST-002 — No live API dependency

Normal automated tests MUST NOT require live third-party network calls.

## TEST-003 — Determinism

Automated tests MUST NOT depend on:

- the current wall-clock date without a controllable clock
- current market prices
- test execution order
- the user's application database
- non-deterministic randomness without a fixed seed

## TEST-004 — Regression tests

Bug fixes SHOULD include a regression test that fails before the fix and passes afterward.

## TEST-005 — Required verification

CI SHOULD run, when configured:

```bash
ruff check .
pytest
mypy src/
```

---

# 17. Error Handling

## ERR-001 — Explicit exceptions

The project SHOULD define application-level exceptions such as:

```python
class StockTrackerError(Exception):
    pass

class InvalidTickerError(StockTrackerError):
    pass

class MarketDataUnavailableError(StockTrackerError):
    pass

class ProviderUnavailableError(StockTrackerError):
    pass

class RateLimitError(StockTrackerError):
    pass

class RepositoryError(StockTrackerError):
    pass
```

## ERR-002 — No swallowed errors

Errors MUST NOT be silently swallowed.

## ERR-003 — Presentation mapping

CLI code MAY convert application exceptions into human-readable messages, but domain code MUST NOT print directly to users.

---

# 18. HTTP Requirements

HTTP clients SHOULD support:

- explicit timeout
- retry policy
- bounded backoff
- rate-limit handling
- response validation
- testable/mocked sessions
- structured logging without secrets

Network requests MUST NOT occur during unit tests.

---

# 19. Logging

The application SHOULD use Python `logging`.

Suggested levels:

```text
DEBUG   request/cache diagnostics
INFO    significant normal application events
WARNING retryable failures, degraded behavior, rate limits
ERROR   failed operations requiring attention
```

Diagnostic logging MUST remain separate from user-facing CLI output.

---

# 20. GitHub Development Process

## GH-001 — Main branch

`main` is the primary branch.

Direct development on `main` SHOULD be avoided.

## GH-002 — Branch naming

```text
feature/<issue-number>-<description>
fix/<issue-number>-<description>
refactor/<issue-number>-<description>
test/<issue-number>-<description>
docs/<issue-number>-<description>
```

## GH-003 — Issues

Agent coding tasks SHOULD originate from a GitHub issue containing:

- problem
- goal
- scope
- out of scope
- requirement IDs
- acceptance criteria
- required tests
- dependencies

## GH-004 — Pull requests

One logical task SHOULD normally produce one PR.

PRs MUST state:

- requirement IDs implemented
- related issue
- architecture impact
- tests actually run
- breaking changes
- security considerations
- assumptions
- unresolved concerns

## GH-005 — Merge protection

Repository settings SHOULD require CI checks before merge.

Agents MUST NOT bypass required checks.

---

# 21. Agent Authority

The operational authority of AI agents is defined in `AGENTS.md`.

The SRS defines system requirements. `AGENTS.md` defines how an agent is allowed to implement them.

A GitHub issue may narrow or implement this SRS, but MUST NOT silently contradict it.

A change that intentionally modifies an SRS requirement MUST explicitly state that it is a specification change and receive human approval.

---

# 22. Definition of Done

A feature is complete only when:

- applicable acceptance criteria are satisfied
- applicable requirement IDs are satisfied
- tests are added or updated where needed
- targeted tests pass
- full test suite passes
- linting passes
- type checking passes when configured
- no secrets are introduced
- relevant documentation is updated
- no unrelated changes are included
- PR is created and references the issue
- unresolved assumptions are documented

---

# 23. Milestones

## Milestone 0 — Security and Development Foundation

**Review status (2026-10-03):** M0 is complete under `AGENTS.md` §10.7.
All thirteen required issues are closed, and all three exit criteria have
supporting evidence at `e0bbeb1`. CI issue #12 was implemented in merged PR #34;
its completed state was reconciled after owner confirmation. See the
[M0 verification record](docs/milestones/m0-verification.md) for the complete
deliverable checklist, CI runs, security evidence and remaining boundaries.
This status note does not change the approved requirements or exit criteria.

- Rotate exposed credentials.
- Remove secrets from source.
- Add `.env.example`.
- Update `.gitignore`.
- Add configuration module.
- Standardize `pyproject.toml`.
- Add pytest.
- Add Ruff.
- Add type checking when ready.
- Add CI.
- Add PR and issue templates.
- Add `AGENTS.md`.
- Add `docs/TESTING.md`.
- Add `docs/FINANCIAL_CALCULATIONS.md`.

Exit criteria:

```text
CI passes on main.
No active credentials exist in source.
Canonical setup/test commands are documented.
```

## Milestone 1 — Domain Refactor

**Review status (2026-10-04):** M1 is achieved under `AGENTS.md` §10.7 at
`788d3c4119e9ebb196256e9355f24ce8b31dc037` on `main`, after owner merge of
PR #46. All nine required issues (#25–31, #33 and #42) are closed; the
post-merge Foundation run passed all five checks, including Python 3.11/3.12.
The [M1 exit evidence](docs/milestones/m1-exit-evidence.md#completion-review--2026-10-04)
maps every deliverable to source/tests and records verification and remaining
later-milestone limitations. GitHub's milestone container remains open with
zero open issues at this review. This status note changes no requirement or
exit criterion.

- Introduce clean Stock model.
- Introduce Position.
- Introduce Portfolio.
- Move financial logic out of CLI.
- Remove infrastructure concerns from domain objects.
- Add unit tests.

Exit criterion:

```text
Domain code runs without network, database, environment, or CLI dependencies.
```

## Milestone 2 — Market Data Layer

**Completion review (2026-10-05; status note only):** M2 is achieved at
`5eccf3b24edbe03a6f01e86b9dfcffb80a1ad0c7` on `main`, after human merge of
PR #67. All ten required issues (#47, #48, #50–56 and #66) are closed; the
post-merge Foundation run passed all five checks. The
[completion evidence](docs/milestones/m2-exit-evidence.md#completion-review--2026-10-05)
records all six deliverables and the provider-boundary exit criterion under
accepted ADR-0007/0008. GitHub milestone 3 is closed at 100% with zero open and
20 closed items. This note changes no requirement, product rule or later scope.

- Create MarketDataProvider.
- Implement FMP adapter.
- Add typed provider models.
- Define timeout/retry/rate-limit policy.
- Fix ticker validation.
- Add mocked provider tests.

Exit criterion:

```text
Application code no longer calls FMP directly.
```

## Milestone 3 — Persistence

**Completion review (2026-10-06; status note only):** M3 is complete under
`AGENTS.md` §10.7 at `534a178005a5dd5662ec0cb261cadaf3ce5f2888` on `main`,
after owner merge of PR #86. All nine required issues (#68–75 and #84) are
closed; milestone 4 is closed with zero open and nine closed issues. All five
post-merge Foundation checks passed. The
[completion evidence](docs/milestones/m3-exit-evidence.md) records all seven
deliverables, exact Decimal state, source/installed-wheel restart without
application pickle storage and checked import/backup/new-destination restore
under accepted ADR-0009. This note changes no requirement or exit criterion.

- Approve persistence ADR.
- Design schema.
- Implement repository interfaces.
- Implement SQLite repositories.
- Add migration mechanism.
- Add integration tests.
- Define migration path from legacy storage.

Exit criterion:

```text
Application restart preserves portfolio state without pickle.
```

## Milestone 4 — Historical Market Data

**Implementation status (non-normative): COMPLETE.** All five deliverables below
and the unchanged exit criterion have verified implementation under accepted
[ADR-0010](docs/adr/0010-historical-market-data-contracts.md). Issues #88–94 and
PRs #95–101 are closed; [M4 evidence](docs/milestones/m4-exit-evidence.md) records
source/wheel verification, owner merges, required main CI and milestone closure.
Raw charts do not establish adjusted/dividend return semantics, historical
currency, live entitlement or session completeness. This status note changes no
requirement ID, formula or approved milestone scope.

- Retrieve OHLCV history.
- Define adjusted/raw price usage.
- Add historical cache.
- Replace synthetic charting.
- Add date-range selection.

Exit criterion:

```text
Historical charts use genuine provider market history.
```

## Milestone 5 — Portfolio Analytics

**Completion status (2026-10-12; status note only):** M5 is complete under
AGENTS §10.7. The owner-accepted
snapshot subset under ADR-0011 is implemented and independently audited at main
`11f7333abdac830e139dd74354c87b30fe4cd45d`, after owner merges of PR #109/#110.
Required #104/#105/#107 are closed and exact audit PR/post-merge main CI passed
all five checks. [M5 exit evidence](docs/milestones/m5-exit-evidence.md) maps every
implemented metric to normative formulas and known-value/source/wheel tests.
Independent final review passed; milestone 6 is closed with zero open and seven
closed items, as recorded in the
[completion report](https://github.com/daniilnahl/Stock-Tracking-App/issues/107#issuecomment-6139320638).
No required M5 work was deferred.
Undefined optional conventions remain blocked. This note changes no requirement,
candidate list or exit criterion below.

This milestone is BLOCKED until applicable formulas are defined in `docs/FINANCIAL_CALCULATIONS.md`.

Initial metrics may include:

- market value
- cost basis
- unrealized gain/loss
- allocation
- daily change
- benchmark comparison

Advanced metrics may include:

- volatility
- maximum drawdown
- Sharpe ratio
- beta
- correlation

Exit criterion:

```text
Every implemented metric has a normative formula and known-value tests.
```

## Milestone 6 — CLI V2

**Implementation status (non-normative): COMPLETE under accepted ADR-0012
Option A.** Required issues #112–118 are closed; owner-merged audit PR #125 at
`237c4c5f7d9825c284d706d6730bcdf9ed3510f6` passed exact-head and post-merge
main CI. [M6 exit evidence](docs/milestones/m6-exit-evidence.md) maps the accepted
use cases and boundaries to source/installed-wheel verification. Administrative
completion documentation/showcase is tracked in #126. This note changes no
requirement, approved command contract or financial definition; the commands
below remain potential examples.

CLI becomes a thin application-service interface.

Potential commands:

```bash
stocktracker portfolio show
stocktracker portfolio summary
stocktracker position add AAPL
stocktracker position remove AAPL
stocktracker stock show NVDA
stocktracker stock history NVDA
stocktracker analytics performance
stocktracker analytics risk
```

## Milestone 7 — REST API

**Current acceptance status — 2026-10-14:** API701–724 and applicable X710–729
are accepted within ADR-0013 Option A as recorded above. The proposal-status,
illustrative issue-group and decision-gate wording below retains the original
review snapshot; unaccepted M8–M10 and out-of-scope decisions remain pending.

### 23.7.0 Proposal status, interpretation and dependencies

**PROPOSED — NOT OWNER-APPROVED.** This revision replaces the brief M7/M8
entries and introduces M9 Automated Stock Research and M10 AI Research Agents.
It does not approve any framework, endpoint, financial preset, subscription,
paid model call, scraping, deployment, dependency installation or new toolchain.
Items marked **[DECISION REQUIRED]** block their dependent implementation until
owner acceptance and any required ADR are recorded. Approval of the SRS alone
does not settle decisions left open here. Existing §§4, 6, 9–16, 24–25 and
accepted ADR-0005–0012 remain authoritative; a material conflict requires review.

**Proposed §4 reconciliation [DECISION REQUIRED, D11]:** M9/M10 are intended to
provide informational screening and clearly labeled, fallible research opinions.
They do not authorize financial advice, individualized suitability assessments,
machine-learning price prediction, brokerage connectivity or automated trading.
The existing §4 exclusions are unchanged. The owner must explicitly accept this
boundary, including whether upstream BUY/HOLD/SELL opinions are allowed at all,
or approve a separate §4 amendment. Labels alone do not settle that conflict.

The intended outcome is a simple, coherent, monochrome, local-first research
workspace: tracked stocks, source-aware security investigation, configurable
approved screens, sector discovery, a qualified Stock of the Day and optional
AI research. Reduced manual navigation does not imply complete data or certainty.

| Milestone | Owns | Dependency / boundary |
| --- | --- | --- |
| M7 REST API | Typed versioned transport, errors and local security | Accepted M6 shared services; no new financial calculations or speculative research endpoints |
| M8 Web Dashboard | Reusable shell, actual-data views, themes and settings | Stabilized M7 contracts; no provider parsing or financial business logic |
| M9 Automated Stock Research | Permitted evidence acquisition, deterministic screening, approved selection and opt-in scheduling | Accepted provider/domain/repository services and separately approved research API; no LLM reasoning or trading |
| M10 AI Research Agents | Optional bounded, auditable read-only research adapter | M9 evidence where supported, accepted feasibility/privacy/worker contracts; no mandatory core dependency or modification of M9 qualification |

M7 and the CLI share injected Python application services; the existing CLI is
not required to use HTTP. M8 consumes M7 APIs. Research and AI API extensions
belong to M9/M10 respectively. Completed M6 exit evidence must be verified before
M7 implementation. Later feasibility research may precede earlier delivery, but
cannot bypass approval or dependency gates.

Illustrative routes, directory layouts, data inventories and agent roles below
are nonbinding. Issue groups are review aids only: create no implementation
issues under this proposal. After owner-approved specification and relevant
architecture decisions, decompose only the current milestone in detail and the
next milestone coarsely, following AGENTS §10.5. Each bounded objective normally
gets one issue/branch/PR; owner merge, required PR/main CI, independent exit
review, issue closure and recorded evidence precede milestone completion.

### 23.7.1 Cross-milestone requirements (proposed)

- **X710 — Architecture:** UI → versioned API → injected application services → typed domain / repositories / provider adapters. Presentation and agent orchestration MUST NOT issue SQL, call provider endpoints directly or calculate financial metrics.
- **X711 — Stability:** Preserve M0–M6 CLI callable behavior, ordered duplicates, namespace separation, persistence guarantees, unavailable/zero distinctions, Decimal holdings and accepted ADR semantics unless separately approved changes explicitly replace them.
- **X712 — Instrument identity:** Never assume global ticker uniqueness. Research MUST use provider-stable identity where available, otherwise supported exchange + symbol with explicit ambiguity handling. Sector/industry labels retain source and effective date. Extending existing identity models requires an accepted contract; unresolved legacy rows remain intact.
- **X713 — Provenance:** Every provider-derived research datum and published conclusion MUST be traceable to provider/source, security identity, observation/effective date, retrieval time, units, usage constraints and reported-versus-calculated status. Unknown provenance MUST be explicit and cannot qualify evidence requiring it; serializers MUST NOT manufacture missing dates.
- **X714 — Currency and precision:** Preserve numeric precision in APIs/storage; use decimal strings for exact values, explicit units and known ISO 4217 currencies for new contracts. No inferred FX or cost/quote currency. Document percentage points versus ratios. Existing accepted arbitrary currency-label validation is unchanged; ISO normalization needs a reviewed mapping contract.
- **X715 — Unavailable data:** Missing, stale, unsupported, invalid, zero, estimated and conflicting values MUST remain distinguishable. No fabricated bars, quotes, fundamentals, citations, scores or market sessions.
- **X716 — Permissions:** No trade execution, brokerage access, private portfolio transmission to LLMs, cloud hosting or externally accessible listeners without separate owner approval. Such approval does not implicitly amend §4 or authorize implementation.
- **X717 — Provider/legal gate:** Before activating an external connector, document official access, subscription/entitlement, storage, display, redistribution, retention, attribution, automation/rate limits and fallback. Unsupported entitlement disables that integration without disabling core local functionality.
- **X718 — Secrets and privacy:** Keys, provider/LLM credentials and session tokens MUST NOT appear in bundles, URLs, logs, screenshots, exports or fixtures. Credentials remain server-side. Private holdings may appear only in the authorized local application, not public bundles, diagnostic artifacts or exports absent specific approval; authenticated local payloads require D1/D2 controls.
- **X719 — Testing:** Fast tests MUST be offline/deterministic with controlled clocks/provider/model fixtures, preserving full-suite checks. Live-provider and paid-model smoke tests require explicit opt-in in a separate profile; browser E2E remains separately invoked under TESTING.md.
- **X720 — Idempotence:** Manual/scheduled research MUST have deterministic task identity, bounded retries/concurrency, safe restart and no partial publication labeled successful.
- **X721 — Observability:** Record non-secret run IDs/states, source availability/timestamps, request counts, retry/rate-limit outcomes, cache use, duration and estimated/actual LLM cost where applicable.
- **X722 — Safe defaults:** Optional sources, notifications, automation and paid AI SHOULD default disabled until configured; core local functionality remains usable when they are unavailable.
- **X723 — Performance budgets:** Define measured UX targets, quotas, retention and task budgets before optimization; no invented SLO or unlimited-request commitment.
- **X724 — Configuration:** Themes, criteria, provider access and AI settings MUST use typed validation. Persisted structures are versioned, with migration/rollback tests for changes. Server configuration and local browser theme preference have distinct ownership.
- **X725 — Accessibility:** Interactive UI MUST meet keyboard, screen reader, focus and contrast requirements, targeting WCAG 2.2 AA; meaning cannot depend on color alone.
- **X726 — Offline:** Local history/completed research MAY be shown explicitly cached/as-of. This does not change ADR-0010's no-expired-history-fallback contract; any broader stale-history mode needs separate approval. Offline results cannot claim live, complete or refreshed status.
- **X727 — Licensing boundaries:** Read permission alone does not authorize public display, extended storage, resale, redistribution, generated-report publication or third-party LLM transmission.
- **X728 — Auditability:** Record code/config/ruleset version and analysis cutoff; model outputs additionally record provider/model/version or identifiable selection, agent configuration and evidence references. Input reproducibility does not guarantee identical LLM text.
- **X729 — Release boundary:** Local-first single-user is a proposed assumption, not approval. Hosted/multi-user release requires REL-003 decisions covering identity, isolation, authentication, deployment, backups, rollback and observability.

### 23.7.2 M7 goal

Expose available, approved capabilities through a small typed, versioned HTTP
API sharing M6 application services with the CLI. Prepare extension points
without fictional future routes or duplicated business logic.

### 23.7.3 M7 requirements (proposed)

- **API701 — Architecture choice:** FastAPI + Pydantic SHOULD be the default subject to a reviewed ADR; alternatives need a documented reason. Python >=3.11,<3.13 remains authoritative.
- **API702 — Layer isolation:** Handlers MUST only validate HTTP inputs, invoke services, serialize and map safe errors; no provider HTTP, direct SQL, CLI imports, Rich/Matplotlib rendering or financial arithmetic.
- **API703 — Versioning:** Public routes MUST have an explicit version prefix and evolution/deprecation policy. `/api/v1` is a candidate pending D2.
- **API704 — Schema:** Inputs/outputs MUST have typed schemas, generated OpenAPI and success/failure examples. Frontend types SHOULD derive from that schema.
- **API705 — Exactness:** Decimal/money MUST cross JSON as documented decimal strings or proven lossless encoding. Dates, timestamps, timezones and units are unambiguous.
- **API706 — Scope:** Implement only approved available services. Watchlist operations and stock/current/history views are candidate categories, not mandatory endpoints.
- **API707 — Legacy semantics:** Ordered entries/duplicates, exact identity, watchlist/Portfolio separation, exchange limits, save/failure behavior and no-match results MUST survive transport.
- **API708 — Errors:** Define stable invalid-input, ambiguity, unsupported-scope, unavailable-provider, rate-limit, stale/unavailable-observation, storage-conflict and internal-error categories. No secrets, stack traces or misleading empty successes.
- **API709 — Metadata:** Quote/history/provider responses MUST include or link available source/time/currency/unit/status metadata. Explicitly represent unknown underlying metadata; never forge it.
- **API710 — Host default:** Local runtime SHOULD bind loopback with private access; remote hosting requires separate approval.
- **API711 — Browser origins:** Explicit CORS origins, no wildcard credentials. Mutation protection MUST address unauthorized origins, CSRF and DNS rebinding as appropriate to the approved local deployment; CORS alone is insufficient.
- **API712 — Authentication:** **[DECISION REQUIRED, D1/D2]** Approve local mutation-access controls before shipping writes; approve identity, authorization and user isolation before network hosting.
- **API713 — Rate bounds:** Bound payloads, timeouts, throttles and concurrency. Provider adapters retain external quota ownership; API layers cannot silently add retry amplification.
- **API714 — Health:** Provide safe local readiness/health without live market fetches or sensitive configuration exposure.
- **API715 — Integration tests:** Inject fake services; verify OpenAPI snapshots/diffs, zeros/nulls/exact Decimals, duplicate/order behavior, safe errors and browser-origin security.
- **API716 — Packaging:** Retain canonical Python setup and CLI source/wheel compatibility; document API start, stop and startup-failure recovery.
- **API717 — Extensibility:** Feature routers/service injection MUST permit new modules without changing existing endpoint semantics.
- **API718 — No premature coupling:** No TradingAgents, FINVIZ parser, generic AI queue, screening algorithm or heavyweight frontend dependency merely to anticipate later work.
- **API719 — Persistence:** Use existing repositories. New state requires an approved schema/migration decision and backup/rollback tests; no unapproved tables in strict SQLite schema v1.
- **API720 — Ownership:** Reads/writes MUST select an explicit existing namespace/record, not mix the two root watchlists or persisted Portfolios.
- **API721 — Documentation:** Publish requests/errors, units, unsupported cases and local security limitations in an operator/developer guide.
- **API722 — Freshness:** Never label cached/old observations real-time. Preserve accepted history and provider missing-data/freshness contracts.
- **API723 — Cancellation:** Disconnect/interruption MUST NOT corrupt state or report uncommitted writes successful. HTTP-specific acknowledgement/concurrency behavior needs a contract preserving ADR-0012's CLI partial-memory/failure semantics.
- **API724 — Done:** Approved API ADR, endpoints/schemas, deterministic service/contract tests, CLI regression suite, required CI, independent audit, owner-merged PRs and issue closure.

### 23.7.4 M7 architecture and review groups (illustrative)

`M8 frontend → M7 versioned routers → M6 services → repositories / providers`.
Candidate families: `/watchlists`, `/stocks`, `/stocks/{id}/history`, `/health`.
URLs, verbs, selection, pagination, errors and schemas require D2/D4 approval.
No route exists merely because it appears here.

Future bounded groups: contract/capability/security readiness; factory/injection/
health; approved watchlist operations; quote/history views; OpenAPI/error/security/
type generation; source/wheel audit and operating evidence. These are not issues.

### 23.7.5 M7 exit criteria (proposed)

Each approved capability works with injected services and accepted CLI domain
semantics, exact numbers, honest timestamps and safe local browser controls.
Independent contract/security/compatibility review and required checks pass;
there are no invented endpoints, credentials or unapproved financial metrics.

## Milestone 8 — Minimalist, Modular Web Dashboard

### 23.8.1 Goal and design reference

A responsive, uncomplicated monochrome interface inspired by Trevor Van Meter's
Fly Guy: whitespace, fine borders, simple interactions and subtle personality.
This is mood inspiration only; readable financial information takes precedence.
It grants no license to copy artwork, sprites, characters, animation, layouts
or source code. React/TypeScript/Vite is a proposal subject to D3.

### 23.8.2 M8 requirements (proposed)

- **UI801 — Framework:** React + TypeScript with Vite SHOULD be initial; Next.js MAY be chosen only with reviewed SSR/deployment rationale.
- **UI802 — Modules:** Independently testable overview/watchlist/stock/analytics/settings features, reusable primitives and typed API client. Research/AI modules wait for backends.
- **UI803 — Shell:** One coherent header/navigation/page-title or breadcrumb/content-boundary system; no separate per-feature styling/navigation paradigms.
- **UI804 — Navigation:** Typed central route/navigation inventory SHOULD allow small shell changes, not arbitrary-code runtime plugins or a marketplace.
- **UI805 — Tokens:** Semantic CSS variables for text, background, surfaces, borders, accents, gain/loss, charts, spacing, typography, focus, radius and motion; no per-feature hard-coded brand colors.
- **UI806 — Default:** Light monochrome MUST be default: white-like background, dark text, subtle gray borders and generous whitespace.
- **UI807 — Themes:** Central extensible registry MUST ship working monochrome light/dark and persistent local preference. Palette editor/cloud sync deferred.
- **UI808 — Theme correctness:** Tables/charts/tooltips/forms/states/focus/modals/popovers MUST switch correctly; gains/losses distinguishable without color.
- **UI809 — Legibility:** Tabular numbers, units/currency/dates, meaningful headings and keyboard-accessible sorting/filtering where supported.
- **UI810 — Actual data:** Prices/performance/history MUST come from approved API outputs; no production sample figures presented live.
- **UI811 — States:** Every data view MUST handle loading, empty, unsupported, stale/offline, error and success; failed refresh never makes stale data current.
- **UI812 — Responsive:** Desktop/tablet/phone preserve navigation, data access, keyboard usability and readable tables; clear horizontal-scroll indications where needed.
- **UI813 — Accessibility:** Target WCAG 2.2 AA; test keyboard/focus, screen reader naming/status, semantic controls, reduced motion and contrast.
- **UI814 — Motion:** Optional subtle transitions/loading MUST respect reduced motion and cancellation where appropriate.
- **UI815 — Copyright:** No copied Fly Guy assets/code. Original minimalist art/icons require appropriate licenses.
- **UI816 — One API layer:** Features MUST use a centralized typed HTTP client/hooks; no provider URLs, keys or database access.
- **UI817 — Server state:** Consistent caching/invalidation/refetch/cancellation/in-flight coalescing SHOULD use one lightweight library or approved native approach, not overlapping systems.
- **UI818 — Settings:** Theme persists locally; server/provider/AI behavior uses validated server APIs and server-owned secrets, not browser-only claims.
- **UI819 — Overview:** Only supported meaningful summaries (such as entry counts/observation status); no portfolio return/risk without normative formulas and verified cost/quote provenance.
- **UI820 — Watchlists:** Ordered entries and supported add/remove/refresh retain M6/M7 namespace/duplicate semantics, including accepted removal behavior.
- **UI821 — Detail:** Available profile/current data and observed history carry source/time labels; no synthetic sessions or implied adjusted returns.
- **UI822 — Analytics:** Only implemented normative M5 snapshot analytics with valid inputs; otherwise omit the route or show unsupported. Pure M5 calculation availability does not establish a fetched-summary service or currency evidence.
- **UI823 — Flags:** Future research/AI screens cannot imply working functionality; enable only after their API gates pass.
- **UI824 — Rendering:** Treat headlines/source names/reports/model output as untrusted; no unsanitized HTML, credential leakage or open redirects.
- **UI825 — Component guide:** Document Button, PageLayout, Navigation, DataTable, Chart, EmptyState, ErrorState, FilterPanel and SettingsField inputs/usage.
- **UI826 — Verification:** Unit/component/schema-driven mock tests and separate browser E2E MUST cover navigation, persistent themes, failures/refresh, responsive/accessibility and stock/watchlist workflows.
- **UI827 — Packaging:** Define startup, frontend/backend compatibility and local static-asset distribution; assume no public hosting platform.
- **UI828 — Theme scope:** M8 supplies architecture/basic selection; custom palettes, seasonal packs, uploads and account sync remain future work.
- **UI829 — Done:** Approved technology/design ADR, reused M7 contracts, genuine working views, theme/accessibility tests, independent UX/API audit and completion evidence.

### 23.8.3 M8 organization and review groups (illustrative)

Candidate `frontend/src/` areas: `app` (router/Shell/navigation/providers),
`components`, `features` (overview/watchlists/stocks/analytics/settings),
`services` (API client/generated types), `themes` and `styles`. Features own
routes/pages/hooks/tests and optional navigation metadata; reuse shell/themes.

Future groups: design/API inventory; scaffold/client; themes/preferences;
shell/navigation/accessibility; watchlist/stock/history states; supported overview/
analytics/settings; browser/responsive/accessibility/distribution audit.

### 23.8.4 M8 exit criteria (proposed)

Clean install supports a legible monochrome dashboard with actual service-backed
stocks/watchlists and only supported history/analytics, recoverable states,
persistent light/dark choice and reusable modular UI without duplicated logic.

## Milestone 9 — Automated Stock Research

### 23.9.1 Goal

Replace repetitive site navigation with permitted, source-aware, reproducible
evidence acquisition, explicit screening, sector discovery, qualified Stock of
the Day and opt-in watchlist research. M9 is deterministic/rule-driven; AI
narrative belongs to M10. No default metric, threshold or ranking is approved.

### 23.9.2 Data sources and ingestion (proposed)

- **RSH901 — Provider-first:** Extend approved provider interfaces; no FMP/FINVIZ URLs in screeners, routers, UI or domain entities.
- **RSH902 — FMP:** Continue within authorized plan/current contracts; validate each new fundamental/news/screen field before activation.
- **RSH903 — FINVIZ API:** Investigate official API/exports as optional second source; record coverage, entitlement, authentication, rights, metadata and quota. No assumed Elite account or redistribution permission.
- **RSH904 — Scraping gate:** FINVIZ scraping is outside default scope. A separate owner-approved ADR may propose it only after official API suitability, terms, robots and permissions review. Never bypass authentication, quotas, access controls, bots/paywalls or disallowed URLs.
- **RSH905 — Optional source:** Missing/unlicensed FINVIZ MUST degrade to labeled supported-source research without breaking core workflows or substituting differently defined fields.
- **RSH906 — Records:** Facts MUST carry identity, provider, metric, value/type, units/currency, observation/effective date, retrieval time, source method/ID and availability/conflict state. Unknown dates remain explicit and cannot satisfy cutoff requirements.
- **RSH907 — Comparability:** Check definition, period, statement type, fiscal calendar, currency, adjustment, timing, estimation and units before combining; incompatible facts remain separate, never averaged/overwritten.
- **RSH908 — Disagreement:** Approved per-field precedence or explicit conflict state; retain provenance instead of choosing favorable values.
- **RSH909 — History:** Bars/returns follow accepted M4/financial contracts; current metadata/provider percentages/screens do not replace historical evidence.
- **RSH910 — Freshness:** **[DECISION REQUIRED]** Per-class age policies for quotes/fundamentals/news/ratings/universe; mark expiry and refresh within budget. No universal TTL or silent replacement of accepted current/history policies.
- **RSH911 — Quotas:** Shared per-provider budgets, coalescing, caching, bounded retry and documented Retry-After. Actual enabled-plan limits must be verified; existing FMP immediate-429 behavior is unchanged unless separately approved.
- **RSH912 — Persistence:** Separate research cache/run snapshots from user watchlists/Portfolios; approved retention/license constraints, migrations and deletion policy for explicitly cache-owned expired data. Never delete user-owned reports/data by inference.
- **RSH913 — Coverage:** Show supported instruments/exchanges, delisted/ambiguous exclusions, missing fields/outages; no all-market completeness claim.

### 23.9.3 Screening and explainable selection (proposed)

- **RSH914 — Screens:** Versioned named rules over explicit dated universe/sectors; typed predicates/operators/units/null policy/stable tie-break.
- **RSH915 — Math approval:** Every derived financial metric, score, weight, indicator or claimed default threshold MUST have normative semantics and known-value tests in FINANCIAL_CALCULATIONS.md or an approved decision cross-referenced there. No invented valuation/attractiveness heuristics.
- **RSH916 — User criteria:** UI/API MUST run at least one explicitly approved screen with inspectable/adjustable documented filters; unsupported criteria reject clearly. **[DECISION REQUIRED, D6]** First preset/field list remains undefined.
- **RSH917 — Missing inputs:** Missing required input cannot pass; count unknown/excluded with reason. Missing is not zero; optional values cannot silently alter ranking.
- **RSH918 — Cutoff:** One analysis cutoff and compatible dates; no future-filed evidence in historical screening. Save vintage and ruleset version.
- **RSH919 — Sectors:** Bounded ranked per-sector results show evaluated/qualified/excluded counts. Taxonomy, unmapped sectors and bounds require approval; no assumed fixed quota.
- **RSH920 — Stock of the Day:** At most one candidate per defined local market date, from approved universe/rules/rank/tie-break. No qualified data/candidate means explicit “No qualifying stock today” with reasons. **[DECISION REQUIRED, D7]** Market calendar/date/ranking remain blocked.
- **RSH921 — Explanation:** Show passed rules, thresholds/actuals, disqualifying/missing criteria, dated source references and freshness; separate observed data, computed scores and narrative opinion.
- **RSH922 — Advice boundary:** Screening results for research only; no order, guarantee, prediction or personalized suitability. D11 remains blocking.
- **RSH923 — Stability:** Identical snapshot/rules/config produce identical ordering/results; reruns create dated revisions, never silently mutate original snapshots.
- **RSH924 — Duplicates:** Approved canonical-ID research deduplication MUST NOT mutate ordered watchlist/position duplicates.
- **RSH925 — Transparency:** Publish universe/exclusions/coverage/tie-break; historical evaluation cannot assume current surviving tickers.
- **RSH926 — Qualification:** Missing mandatory evidence, invalid/stale core input or unresolved identity conflict cannot receive qualified state.

### 23.9.4 Monitoring, jobs, reports and UI (proposed)

- **RSH927 — Watchlists:** Research selected rows/instruments without changing quantities, costs, order, namespaces or financial state.
- **RSH928 — Changes:** Verifiable criterion/data changes, not predictive signals; record prior/current facts and source/effective times.
- **RSH929 — Manual controls:** Research now/rerun/status/sources/actionable errors and cancellation at safe boundaries.
- **RSH930 — Scheduling:** Opt-in periodic runs with explicit timezone, calendar and frequency bounds. Local jobs run only while scheduler operates; approved restart/missed-run policy, no implied 24/7 hosting.
- **RSH931 — Durability:** Approved states equivalent to queued/running/completed/partial/failed/cancelled; non-secret IDs, counters, bounded concurrency, restart/dedup policies and atomic completed-snapshot publication.
- **RSH932 — Errors:** Distinguish invalid symbol, unsupported universe, config/credentials, license, quota, outage, incomplete snapshot and data conflict; partial remains partial.
- **RSH933 — Reports:** Compact stock/company/sector, timestamps, criteria, meaningful supported fundamentals/history, sources/gaps and approved conclusions. Export/PDF optional and separately rights/retention-gated.
- **RSH934 — UI:** Research/Discover, filters, sectors, Stock-of-the-Day and watchlist panel only after approved routes/models; reuse M8.
- **RSH935 — API:** Versioned research/criteria/jobs contracts use M7 precision/errors/security and server authorization; async semantics require approval.
- **RSH936 — Settings:** Enabled providers/presets/sectors/schedules/notification preferences validated/versioned/migrated separately from financial watchlist state.
- **RSH937 — Notifications:** In-app status MAY ship; email/phone/push/webhooks/always-on delivery require explicit channels/privacy/deployment approval. Unconfigured means no external delivery.
- **RSH938 — Evaluation:** Curated multi-sector, missing/stale/conflict, holiday, no-candidate and cutoff fixtures; record coverage/reproducibility, not forecast accuracy.
- **RSH939 — Outage:** Smaller labeled subset SHOULD run only if approved rules permit degraded evidence; otherwise incomplete/blocked. Never relax thresholds to force a result.
- **RSH940 — Done:** Approved rights/screening contracts, provenance, reproducible universe/selection, no-candidate behavior, opt-in durable schedule, safe watchlists, schema/tests and independent audit.

### 23.9.5 M9 contract inventory and review groups (illustrative)

Candidate records, not public schemas: ResearchObservation (identity/metric/value/
units/currency/source/dates/availability/license); ScreenDefinition (ID/version/
universe/cutoff/predicates/ranking/taxonomy/tie-break); ResearchRun (ID/status/
times/as-of/coverage/config digest/rules/vintage/errors); QualifiedCandidate
(identity/sector/rank/state/predicates/missing evidence/observations/references).
No assumption about nullability, public visibility or persistence is approved.

Future groups: scope/universe/metric/screen ADR; rights/API feasibility; typed
observations/run storage; optional official adapter; normalization/freshness/
conflicts/quotas; screening/sectors; daily selection; watchlist/jobs; research
API/UI; independent rights/correctness/cutoff/security/exit audit.

### 23.9.6 M9 exit criteria (proposed)

Permitted controlled data supports documented reproducible sector screens,
inspectable criteria/sources, a daily candidate only when qualified, opt-in
watchlist research without holdings mutation, honest data-quality states and
previous dated runs. No subscription, scraping right or financial convention
is assumed; all dependent decision gates must be resolved.

## Milestone 10 — AI Research Agents

### 23.10.1 Goal and feasibility gate

Explore TauricResearch/TradingAgents or an approved equivalent as an optional,
read-only multi-perspective engine. Ground fallible analyst-style reports in
M9 evidence and keep them separate from deterministic qualification. This is
not autonomous portfolio management. No upstream default graph is accepted.

M10 approval first permits only separately scoped, time-boxed feasibility work;
production integration waits for an accepted feasibility/isolation ADR. The
sequence is approved spike scope → isolated PoC → reviewed findings/accepted
adapter/privacy/read-only ADR → bounded implementation → independent audit.
No spike, environment installation or paid run is authorized by this proposal.

### 23.10.2 M10 requirements (proposed)

- **AI1001 — Spike:** Isolated time-boxed compatibility PoC before dependency acceptance; compare direct integration, separate worker/service and adapter-only alternative, recommending only compliant approaches.
- **AI1002 — Isolation:** Separate process/environment or isolated service behind small adapter SHOULD protect core pins and filesystem/network boundaries; reviewed ADR, no unapproved package manager or Python change.
- **AI1003 — Version:** Review specific tag/commit, license/NOTICE, dependencies/Python, default sources, persistence/logs and behavior; pin tested approved version, not moving main.
- **AI1004 — Read-only:** Disable brokerage/order/trader routing and simulated core mutations. If upstream cannot be constrained to research-only, do not ship. Specialist risk/technical views cannot introduce undefined app metrics or price forecasts.
- **AI1005 — Consent/cost:** Explicit user enablement/initiation or opt-in; configurable provider/model, spend/token estimate, depth, timeout and concurrency SHOULD have safe defaults; no silent paid run. Budget enforcement contract is required before activation.
- **AI1006 — Credentials:** Server-side isolated keys, absent from reports/traces/exports/client payloads and prompts.
- **AI1007 — Privacy:** Only public licensed security evidence by default. Private holdings/costs/annotations/account data require documented purpose/provider-specific opt-in AND owner-approved exception to X716; general AI enablement is insufficient.
- **AI1008 — Rights:** Verify evidence transmission and report retention rights with model/data vendors. Unclear rights block transmission or require separate permitted dataset.
- **AI1009 — Untrusted inputs:** Websites/articles/filings/social/tool responses/summaries/model text are evidence, never system instructions; prompt-injection and command/URL validation defenses required.
- **AI1010 — Grounding:** Every source-dependent claim MUST cite real captured evidence with sanitized provider URL/ID and effective/retrieval time. Validate references and support; unsupported factual claims MUST be withheld from published reports and retained only as sanitized validation failures/partial-run diagnostics. No invented evidence/tool execution; reference existence alone does not prove a claim.
- **AI1011 — Uncertainty:** Separate opinions, observations and deterministic qualification; show conflict, missing evidence and time lag.
- **AI1012 — Workflow:** Bounded configured viewpoints such as fundamentals/technical/news/bull-bear/risk; exact graph/stopping/consensus needs approval, not upstream defaults.
- **AI1013 — Output:** Versioned AIResearchReport with status/identity/cutoff/evidence/agent sections/agreement/limits/settings/token-cost usage/safety flags.
- **AI1014 — Fallback:** CLI/M7/M8/M9 remain usable with absent/disabled/offline/limited/incompatible/invalid AI.
- **AI1015 — Lifecycle:** Reuse approved M9 durable conventions where suitable, including pending/running/completed/partial/failed/cancelled, dedup/retry/crash recovery; partial text is never completed report.
- **AI1016 — Budgets:** Enforce hard time/request/token/cost/storage/concurrency bounds; stop runaway debate/retry/new calls. **[DECISION REQUIRED, D9]** Reserve worst-case authorized spend before each call; unknown pricing/usage or inability to enforce a cap blocks that vendor/path. Cancellation cannot undo an already authorized billable request.
- **AI1017 — Observability:** Sanitized step/status/evidence/settings/model/cost/error/duration; no chain-of-thought logs, sensitive prompt dumps or indefinite memory retention.
- **AI1018 — Storage:** Separate approved report/checkpoint paths; control upstream defaults, retention/deletion/idempotence/run isolation. No overwrite of user tables; user reports are not automatically disposable cache.
- **AI1019 — Opinions:** **[DECISION REQUIRED, D11]** Whether BUY/HOLD/SELL text may be shown remains blocked. If explicitly approved, label it model research opinion, never app instruction, deterministic score, personalized portfolio recommendation or guarantee; X716/AI1004 still prohibit execution.
- **AI1020 — Historical integrity:** Use only evidence available by cutoff, dated publication/universe. Unverified point-in-time sources cannot support historical validation/backtest claims; identify any limitation and withhold unsupported claims.
- **AI1021 — Failure:** Sanitized actionable exceptions cannot corrupt holdings/watchlists/M9/API; no infinite expensive retry.
- **AI1022 — UI:** Optional stock/Research panel reuses M8, showing progress/settings/cost/sources/disagreement/limits/age independently of M9 badges.
- **AI1023 — API:** Appropriately secured/authenticated request/inspect/list/cancel/delete run/report endpoints use approved versioned M7 schemas; deletion needs explicit record ownership and approved data policy.
- **AI1024 — Evaluation:** Fixed offline evidence and curated historical cases assess attribution/schema/missing data/injection/input reproducibility/cost/failure; no profit or prediction claim from small backtests.
- **AI1025 — Regression:** Absent optional imports, model failure, disabled feature, malicious evidence, permission refusal, timeout, duplicate job and exhausted budgets cannot break core workflows.
- **AI1026 — Licenses:** Review actual TradingAgents Apache-2.0 distribution/NOTICE obligations and separate data/news/model licensing; source code permission is not data permission.
- **AI1027 — Local model:** MAY support proven compatible/resources/security backend; not required and no silent large-model download.
- **AI1028 — Quality:** Label AI text, source references, unresolved claims, cutoff and configuration; never “verified analyst consensus.”
- **AI1029 — Rollout:** Explicit disabled-by-default flag and documented disable/uninstall; disabling leaves core functionality and holdings intact.
- **AI1030 — Done:** Accepted feasibility ADR, pinned isolated adapter, read-only/privacy/rights controls, bounded runs, grounded UI/API, failure/attack/cost tests, independent audit, owner merge and exit evidence.

### 23.10.3 M10 pipeline and review groups (illustrative)

Selection/cutoff → opt-in/identity/rights/budget checks → approved M9 evidence
snapshot → bounded optional worker → validated references/output/warnings →
persisted read-only report → M8 via M7 API. LLM disagreement cannot overwrite
M9 eligibility or deterministic results.

Future groups: authorized license/dependency/storage/security/cost spike;
accepted worker/adapter/privacy decision; evidence/prompt/tool/output controls;
bounded graph/configuration; lifecycle/cancellation/retention/observability;
API/UI integration; independent rights/cost/injection/cutoff/regression audit.

### 23.10.4 M10 exit criteria (proposed)

With AI explicitly enabled and permitted evidence, the user can request bounded
read-only analysis, inspect source-linked claims/disagreement/costs/limits,
cancel or inspect failure and retain normal tracker use with AI disabled.
No application trade instruction or execution; unresolved feasibility, rights,
privacy, cost enforcement or §4 gates block release.

### 23.11 Owner acceptance and release gates (proposed)

Acceptance is **PENDING** for this diff and all new architecture choices.
The [decision report](docs/milestones/m7-m10-srs-review.md) tracks D1–D11 and
additional contract gaps, verified baseline and external-source limits. Obtain
explicit acceptance of the specification and relevant ADRs/precise exit
contracts before creating implementation issues. Do not implement milestones,
merge this proposal, close future milestones or reinterpret recommendations as
approved behavior. Owner acceptance must identify the reviewed diff and resolved
decisions; unresolved gates remain blocked after any partial acceptance.

---

# 24. Release and Deployment

## REL-001 — Versioning

The project SHOULD use semantic versioning once releases are published.

## REL-002 — CLI-stage deployment

Before a hosted service exists, "deployment" means producing a reproducible installable/testable application artifact and release from a tagged commit.

## REL-003 — Hosted deployment

A hosted deployment process MUST NOT be invented as part of unrelated feature work.

When hosting begins, deployment requirements MUST define:

- target environment
- secret storage
- database backup/migration process
- health checks
- rollback process
- observability
- release approval rules

---

# 25. Performance and API Usage

## PERF-001 — No accidental request amplification

Application behavior MUST avoid unnecessary duplicate provider requests within one operation.

## PERF-002 — Cache semantics

Caching behavior MUST define freshness and stale-data handling before it is relied upon for correctness.

## PERF-003 — Performance targets

Concrete latency and throughput targets are currently not established.

Agents MUST NOT invent production SLOs. Add them when the product has a hosted runtime or measured usage requirements.

---

# 26. Architecture Decision Records

Use `docs/adr/` for material decisions.

Suggested ADRs:

```text
0001-use-sqlite.md
0002-market-provider-abstraction.md
0003-money-and-decimal-policy.md
0004-persistence-migration-strategy.md
```

ADR template:

```markdown
# ADR-XXXX: Decision Name

## Status
Accepted

## Context
What problem requires a decision?

## Decision
What was selected?

## Alternatives
What alternatives were considered?

## Consequences
What benefits and drawbacks result?
```

---

# 27. Engineering Principle

The project should make ambiguous requirements difficult to implement silently.

For agentic development, the desired chain is:

```text
SRS requirement
      ↓
GitHub issue
      ↓
implementation
      ↓
test
      ↓
pull request
```

The goal is not autonomous code volume. The goal is controlled engineering progress.
