# M6 thin CLI exit evidence

Status: **LOCAL AUDIT PASSED — #118 remains open pending review, owner merge and required CI**.
Snapshot: 2026-10-13, America/Los_Angeles.
Baseline: owner-merged PR #124, `926171e34b518bea8d09a322f62482f3d54d56bc`.
Parent: [M6 — CLI V2](https://github.com/daniilnahl/Stock-Tracking-App/milestone/7).
Contract: [accepted ADR-0012](../adr/0012-cli-application-services.md), including
the owner-approved unowned-input amendment recorded during #117.

## Scope and accepted result

M6 Option A preserves both maintained root CLI command surfaces while moving
application orchestration into injected neutral services. The menu retains its
graph command; the evaluation CLI retains its existing command set. Numeric
financial values stay in the domain; prompts, display projection, charting and
concrete dependency composition remain outside services.

This #118 change adds independent combined process fixtures, bounded architecture
checks and operation/exit evidence. It changes no runtime source, dependency,
Python support, financial definition, schema, provider policy or CLI contract.
The audit fixture does not import earlier test helpers. Every audit phase starts
in a fresh `python -I -B` process over one explicit temporary directory.

## Implementation trace and dependency gates

| Issue / accepted objective | Owner-merged PR | Recorded prerequisite evidence |
| --- | --- | --- |
| #112 — accepted service contracts and exit criteria | [#120](https://github.com/daniilnahl/Stock-Tracking-App/pull/120), `96182b6e` | Exact-head Foundation `38442157132`; combined main `38442587378` passed |
| #113 — accurate financial headings | [#119](https://github.com/daniilnahl/Stock-Tracking-App/pull/119), `11e262c3` | Exact-head Foundation `38441573466`; included in passing combined main `38442587378` |
| #114 — local service/shared neutral contracts | [#121](https://github.com/daniilnahl/Stock-Tracking-App/pull/121), `aa6ecdd3` | Exact-head Foundation `38457696127`; main `38457958438` passed |
| #115 — current-data service | [#123](https://github.com/daniilnahl/Stock-Tracking-App/pull/123), `6c38eb9d` | Exact-head Foundation `38489752648`; main `38491378548` passed |
| #116 — historical service | [#122](https://github.com/daniilnahl/Stock-Tracking-App/pull/122), `a9739dca` | Exact-head Foundation `38459708966`; main `38489030065` passed |
| #117 — maintained CLI integration | [#124](https://github.com/daniilnahl/Stock-Tracking-App/pull/124), `926171e3` | [Exact-head Foundation `38494488364`](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38494488364) and [main `38494501665`](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38494501665) passed |
| #118 — this combined audit | Pending | Local verification below; exact PR/main CI and owner merge remain required |

Each passing Foundation run requires tests on Python 3.11/3.12, Ruff, configured
mypy and credential-pattern checks. #124 was merged with an unfilled PR template;
its description was completed through the GitHub website using the recorded
implementation/testing/CI evidence. All three #117 acceptance items were checked
and the issue closed completed after its owner merge and required CI passed.
Milestone state observed on GitHub remains open. A merged
implementation alone does not satisfy the final milestone completion gates.

## Accepted exit and requirement map

| Accepted ADR-0012 exit / requirement | Meaningful evidence |
| --- | --- |
| 1. Both maintained CLIs delegate application orchestration; ARCH-001/003/004/005 | `test_cli_architecture.py` scans actual commands/services with controlled violations; `test_cli_service_integration.py` and combined process spies call through real WatchlistService/CurrentDataService/HistoryService methods while legacy fetch/refresh/graph/existence methods are denied |
| 2. Neutral service imports/execution; ARCH-002/003/004, SEC-002 | Existing cold `watchlist_service_probe.py`, `current_data_service_probe.py`, `history_service_probe.py` prove UI/facade/configuration/environment/concrete IO denial in source and installed wheel; new static checks permit neutral contracts and reject direct infrastructure imports |
| 3. Real source/wheel commands and restarts; PERS-005/007, TEST-001–005 | `test_m6_exit.py` and `test_packaging.py` run the standalone combined probe through write, read, failures, read in separate processes, using the actual root commands, services, provider parser, cache and temporary SQLite repositories |
| 3. Prompt sequencing, invalid/duplicate/abort behavior; DATA-006, ERR-001–003 | Combined fixture checks lookup/profile/period order, invalid/duplicate one-lookup outcomes and terminal EOF without saving; existing `test_cli_ownership.py`, configuration and provider integration matrices retain repeated-input, configuration, application and programming-error distinctions |
| 3. Numeric/unowned/zero/missing/order/alias preservation; FIN-001–005, PERS-005, FC-020/030/040/041 | Combined fixture checks exact precise stored Decimal text, separate unowned/zero-cost/missing-price cases, ordered independent duplicates, untouched Portfolio and saved bytes; `test_cli_service_integration.py` separately checks repeated facade aliases and partial refresh |
| 3. Historical range/identity/cache/error guarantees; DATA-003/007/008, FC-060–062/100/101, PERF-001/002 | Combined fixture graphs sparse raw observations over explicit dates for both matching AAPL rows with one transport request, verifies fresh cache reuse in a key-free restart, and refuses expired-cache 403 without stale fallback; existing history date/integration/exit tests cover identity-before-key, clocks, retries, cache errors and pre-figure conversion guards |
| 4. Accurate labels and presentation-only formatting | Combined rendered headings and known arithmetic; `test_watchlist_terminology.py`, `test_percentage_metadata_display.py`, projection replay and ownership tests verify raw provider percentage-point formatting, ratio display, escaped literal metadata and unchanged numeric snapshots/state |
| 5. Independent combined audit, traceability and completion gates; ARCH-006, GH-004/005 | This evidence, standalone fixture, canonical checks, bounded PR linked to #118, verified owner merges and PR/main CI; this audit's owner merge, required CI and issue/milestone completion remain pending |

The static checker detects ordinary literal imports and calls; it does not
claim to analyze arbitrary dynamic Python. Proven runtime denial probes and
observable application behavior complement it. The combined fixture replaces
the transport capability with controlled HTTP responses while executing the
real provider parsing/error/cache policy. Existing historical exit probes also
exercise the real urllib transport with a synthetic opener.

## Combined scenario and known values

The standalone `tests/m6_exit_probe.py` starts with provider/socket/pickle/legacy
content guards before application imports. Guard controls deliberately attempt
prohibited work and must fail. Import/root/subcommand help execute with provider
acquisition, SQLite connections and legacy-entry inspection denied. Configuration
discovery is disabled; clocks and all HTTP responses are fixed.

Each namespace independently adds these rows through its actual commands:

- AAPL: quantity `.2500`, average cost `100.0000`, initial price 120.
- PRECISE: quantity `0.12345678901234567890123456789`, average cost
  `100.12345678901234567890123456789`; exact input spellings survive restart.
- UNOWNED: quantity `0.0000`, exact cost input `-`, missing quote; average cost
  remains None and no owned Position is fabricated.
- ZEROCOST: quantity `0.0000`, numeric cost `0.00`, quote zero; it remains owned.

For the AAPL known-value fixture, Q=0.25 and C=100 give cost basis 25. Price 120
gives market value 30, unrealized P&L 5 and numeric return 0.2. A successful refresh
to price 126 gives value 31.5, P&L 6.5 and return 0.26. These use existing pure
calculations; no aggregate or currency provenance is inferred. Provider 1D
percentage points 12.345 format as 12.34 under the existing display rule.

Invalid/duplicate inputs and an aborted ownership prompt preserve database bytes.
Successful refresh preserves the existing facade/list references and exact
provider order. A disposable REMOVE row verifies removal; an independent second
AAPL occurrence verifies ordered duplicates. Empty and markup-like saved period
metadata remain literal. A separately stored Portfolio 88 remains untouched.

Separate read processes restore both namespaces without credentials, display
locally without changing the database, and confirm ownership, quote, metadata,
row order and duplicate values. Failure processes exercise profile/period 403s
and an unexpected RuntimeError. Earlier safe in-memory publication remains,
later rows remain untouched, committed database bytes remain unchanged, and no
success or sensitive provider body appears in output/logs.

The menu graphs raw closes 101.25 and 102.5 on January 2 and 6, 2020, with the
existing requested/observed labels, marker-only line and unavailable currency.
Both matching AAPL rows consume one exact cache entry. After offline local
restoration, graph attempts explicitly supply the synthetic current runtime
key; a cache does not waive credential preflight. Fresh restart graphs use
no transport; an exactly expired entry receives a controlled 403 and is not used
as stale fallback. Temporary runtime key binding is restored after success and
failure. Graphing changes neither holdings nor committed bytes. Opaque legacy
files are preserved byte-for-byte throughout all phases.

## Verification and remaining gates

Canonical environment: existing repository Python 3.12.10 environment with the
unchanged pinned development dependencies. Source and wheel execute the same
standalone fixture, without importing the checkout into installed-wheel runs.

| Command actually run | Result |
| --- | --- |
| `python -m pytest tests/test_cli_architecture.py tests/test_m6_exit.py tests/test_packaging.py -q --tb=short` | 19 passed in 55.63s |
| `python -m ruff check .` | Passed |
| `python -m mypy` | Passed; `config.py` only |
| `python -m pip check` | Passed |
| `python -m pytest tests/test_repository_hygiene.py -q --tb=short` | 8 passed in 9.27s, audit files staged |
| `python -m pytest -q --tb=short` | 2507 passed in 129.16s |
| Staged/final whitespace, scope, secret and artifact review | Passed |

An initial fixture passed plain synthetic EOF to Click 8.1's input harness,
which repeated empty ownership input. Only the identified audit subprocesses
were stopped. The probe now uses terminal-style EOF and bounded subprocess
timeouts. A second assertion used an inaccurate safe-error spelling; it was
corrected against the existing ProviderAccessError definition, and provider
diagnostics are captured and checked for redaction. Runtime code was unchanged.

No live credentials, market prices, user databases or hosted service were used.
Configured mypy checks `config.py` only. This audit does not establish live FMP
entitlement, API endpoints, an installed command entrypoint, portfolio input/
currency acquisition, historical cash-flow/risk/dividend/FX conventions or a
deployment process. M7/M8 remain separately scoped future work.

M6 remains open until #118 is reviewed, owner-merged, its required exact-head and
post-merge main CI pass, required issues close and final exit/operation evidence
is reconciled. No agent merge or early milestone closure is authorized.
