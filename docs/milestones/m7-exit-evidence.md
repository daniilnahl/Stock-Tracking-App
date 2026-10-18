# M7 independent combined exit audit — issue #134

**Current delivery — 2026-10-18:** audit issue #134 is closed and its accepted implementation is delivered. The incomplete/pending notices below describe the original audit snapshot. M7's milestone container remains administratively open with zero open issues; this is separate from technical delivery. See [current status](../CURRENT_STATUS.md).

## Scope and completion gate

This audit implements verification of accepted ADR-0013 Option A and applicable
SRS API701–724/X710–729: a local authenticated holdings read-only adapter sharing
existing services. It changes no runtime, public contract, financial formula,
schema, dependency, CI configuration or supported Python version. M8–M10,
mutations, Portfolio CRUD and hosted operation remain outside this evidence.

The predecessor gate is satisfied: required issues #129–133 are closed. Owner-
merged PR #139 is main `65efe21f5d6432e0e4e19d29f76d30d66b1c00be`;
[Foundation 38668340633](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38668340633)
passed all five configured jobs, including Python 3.11 and 3.12. This is a dated
prerequisite record, not CI for #134's forthcoming PR.

**M7 remains incomplete.** Audit implementation and verification must pass
independent review and required PR checks; #134's own owner merge, green main CI
and issue closure must precede milestone completion. Agents do not merge PRs.
Live historical rights remain unsupplied, and history defaults disabled. A
synthetic opt-in test does not activate a provider or establish entitlement.

## Combined scenario and requirement evidence

`tests/test_m7_exit.py` and `tests/test_packaging.py` execute
`tests/m7_exit_probe.py` in independent write, read and expired processes. Every
child uses isolated temporary state and verifies all imported application module
origins (including root configuration) against the source or installed-wheel
root. Installed verification cannot succeed through checkout imports.

| Requirement concern | Evidence |
|---|---|
| API702/706/717; ARCH-001–006 | Actual API configuration/composition, WatchlistService, HistoryService, repositories, factory, FMP parser, HTTP transport and neutral serializers execute; CLI/compatibility/UI modules remain absent. |
| API705/707/709/720; FIN-001–005; X711–715 | Both namespaces have distinct saved names and ordered duplicate Stock rows. Exact fractional quantities, known-value negative returns, zero/unowned/null distinctions, sparse raw OHLC Decimal values, null adjusted close/volume and maximum signed integer volume survive JSON. Unknown saved metadata remains unknown; raw history uses accepted-cache-policy provenance without invented currency/timestamps. |
| API708/710–714/722; SEC-002/005 | Health/schema and rejected authentication/Host/Origin calls acquire no SQLite/provider dependency; synthetic guards prove refusal. Disabled history remains unavailable. Missing ordinal, invalid dates and unsupported exchange fail safely; expiry yields fixed provider-unavailable error without sensitive response contents or credentials. |
| API719/723; PERS-005/007; DATA-003/006/007 | Both namespace records, holdings database bytes/schema v1 and both opaque legacy files remain unchanged. Only accepted history cache is written. Existing cancellation/admission tests remain required. |
| API715/716/724; TEST-001–005; DEV-001–004 | Source and installed-wheel child processes independently verify first fetch, restart reuse at 3599 seconds and exact expiry at 3600 seconds. Expiry executes two bounded production attempts per namespace, no stale response/cache replacement, no retry amplification by API. Full CLI regressions remain in required full pytest. |

Only the HTTP opener is synthetic; request construction, header-only synthetic
key, provider schema parsing, factory policy, cache receipt parsing and SQLite
restore are real. Fixed UTC and retry clocks avoid wall-clock/session assumptions.
Same-symbol duplicates intentionally share the accepted cache key while distinct
namespace/row names detect incorrect selection. Two expired namespace requests
produce four HTTP attempts and two fixed 0.5-second backoff records.

## Guard boundaries and disclosed bootstrap

Before application imports each child installs and negatively tests DNS/socket
connect/sendto, urllib, pickle load/loads/dump/dumps, explicit SQLite path,
legacy and dotenv content, ordinary open/io.open, low-level os.open, and atomic
os.replace/os.rename source/destination guards. `io.FileIO` is denied outright.
A denial ledger also fails the audit if application code catches a violation
and maps it to a safe HTTP error. Explicit dependency-denial controls precede
health/schema/access checks. No application listener or actual network request
is opened.

The interpreter, standard-library setup and native Windows asyncio control
sockets bootstrap before these guards. Import-loader/framework code reads and
the production TLS context's installed CA bundle reads remain possible; this
combined audit does not claim ordinary read isolation for all files. Existing
cold foundation/launcher source/wheel probes separately deny application data IO,
environment/provider acquisition and output. The combined probe clears inherited
credentials and supplies synthetic process values; dotenv discovery is replaced
with a no-op before real configuration loading. Fixture setup writes and final
byte comparisons use a retained original opener solely for the two temporary
opaque legacy files; production content access remains denied. Guards cover the
documented Python seams, not a complete operating-system sandbox.

## Verification record

Canonical Python **3.12.14**, 2026-10-14 (America/Los_Angeles):

- Focused combined source/wheel and API command documented in TESTING.md:
  **256 passed in 49.33 seconds**.
- Full `python -m pytest`: **2,761 passed in 122.98 seconds**.
- `python -m ruff check .`: passed.
- `python -m mypy`: passed, configured `config.py` only (one source file).
- `python -m pip check`: passed.
- Independent read-only review: passed; separate source audit rerun:
  **1 passed in 3.29 seconds**.
- Master staged hygiene rerun: **8 passed in 9.22 seconds**.

Audit implementation and local verification are ready for PR review. Required
PR CI and owner merge/main CI/closure remain separate pending gates; these local
checks do not establish M7 completion. No live provider, listener, real credential
or user state was used.
