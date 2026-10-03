# Stock Tracking App — Software Requirements Specification

**Version:** 1.1  
**Status:** Approved  
**Primary implementation language:** Python  
**Current interface:** Typer CLI  
**Target:** Production-quality portfolio tracking and analytics application

## Approval record

The repository owner approved SRS v1.1 on 2026-10-02 in the issue #2
implementation chat. The owner also explicitly authorized generating
`pyproject.toml` from the existing dependencies, making it the master dependency
file, and removing `reqs.txt` if environment setup no longer requires it.

The only intentionally changed requirement is DEV-003: its assertion that a
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

**Review status (2026-10-03):** The implementation and three exit criteria have
supporting evidence at `e0bbeb1`. Formal milestone completion remains pending
closure of CI issue #12 under `AGENTS.md` §10.7. See the
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

FastAPI MAY be introduced after the service/domain layers stabilize.

CLI and REST MUST share application services.

## Milestone 8 — Web Dashboard

A React/Next.js frontend MAY be introduced after API contracts stabilize.

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
