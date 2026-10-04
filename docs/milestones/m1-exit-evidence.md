# M1 Domain Refactor technical evidence

## Status and publication boundary

This is the technical evidence proposal for [issue #33](https://github.com/daniilnahl/Stock-Tracking-App/issues/33),
based on the reviewed CLI topic head `0fa359585792b84c77e2fa8200b2402e76454b43`.
It does **not** declare M1 complete. At the 2026-10-03 evidence snapshot, `main`
was `7ea5867114b9cee9171413c9853facdee093e84f`: accepted ADR-0006 was included,
but the runtime topic source was not. A topic PR merged into another topic branch
does not establish source inclusion on main or close its implementation issue.

[Integration issue #42](https://github.com/daniilnahl/Stock-Tracking-App/issues/42)
owns main-target publication of the reviewed stack, final provenance reconciliation,
required main CI and issue closure after owner merge. Agents do not merge or prematurely close
the milestone. #33's own PR/head/CI are pending at document authoring; its eventual
PR and review record supply that exact-head evidence without a circular self-SHA.

## Contracts, scope and requirements

The approved [SRS](../../SRS.md), accepted [ADR-0006](../adr/0006-domain-contracts.md),
[M1 plan](m1-plan.md), [financial definitions](../FINANCIAL_CALCULATIONS.md) and
[testing policy](../TESTING.md) govern this evidence. Domain imports only its own
modules and stdlib; legacy HTTP, credential loading, formatting and charts live
outside domain. Root imports, constructors, CLI commands and trusted synthetic
root-class state remain compatible. Watchlists are not automatically portfolios.

| M1 bullet / requirement | Issue / PR | Concrete automated evidence |
| --- | --- | --- |
| Clean Stock; DOM-001/002 | #26 / [#38](https://github.com/daniilnahl/Stock-Tracking-App/pull/38) | `test_stock_domain.py`: `test_known_identity_ignores_name_but_preserves_symbol_and_exchange`, `test_unknown_identity_is_reflexive_and_distinct_from_other_instances`, field validation/immutability |
| Position; DOM-003, FIN-001–003 | #27 / [#39](https://github.com/daniilnahl/Stock-Tracking-App/pull/39) | `test_position_domain.py`: `test_exact_fractional_and_high_precision_inputs`, `test_failed_replacement_preserves_both_original_inputs`, finite Decimal/zero validation |
| Portfolio; DOM-004 | #28 / [#40](https://github.com/daniilnahl/Stock-Tracking-App/pull/40) | `test_portfolio_domain.py`: `test_defaults_and_explicit_none_have_independent_lists`, `test_constructor_copies_list_but_keeps_position_instances`, order/duplicate/exchange cases |
| Financial logic outside CLI; FIN-004/005, FC-020/030/040/041 | #29 / [#41](https://github.com/daniilnahl/Stock-Tracking-App/pull/41); #30/#31 | `test_position_calculations.py`: known values, missing versus zero, undefined zero-basis return, precision/context and recomputation; facade/CLI tests use actual arithmetic |
| Remove domain infrastructure; ARCH-001/002/005 | #26–31; #33 | `test_domain_isolation.py::test_source_domain_runs_with_independent_infrastructure_guards`; `test_packaging.py::test_wheel_contains_only_runtime_modules_and_safe_imports` runs the same domain-only probe before separate legacy smoke |
| Compatible facade and safe state; ERR-001–003, SEC-002/005 | #30 / [#43](https://github.com/daniilnahl/Stock-Tracking-App/pull/43) | `test_stock_facade.py`: atomic updates/restore, `test_new_pickle_state_excludes_credentials_and_unknown_handles`, `test_old_root_class_pickle_preserves_holdings_ignores_saved_key`, local restore with unusable runtime credentials |
| CLI ownership integration; FIN-001–005, ARCH-005 | #31 / [#44](https://github.com/daniilnahl/Stock-Tracking-App/pull/44) | `test_cli_ownership.py`: exact text inputs, re-prompts, missing quote refresh, zero/unowned display, aborted add preserving existing list/file; `test_baseline.py` preserves help/commands |
| Unit tests and isolation exit; TEST-001–005 | #33 plus each implementation issue | Domain, calculation, facade, credential and CLI suites run offline with temporary state; installed-wheel/source subprocess guards are independent of parent pytest patches |
| Architecture and traceability; ARCH-006, GH-003/004 | #25 / [#37](https://github.com/daniilnahl/Stock-Tracking-App/pull/37), #33, #42 | Dated [owner contract acceptance](https://github.com/daniilnahl/Stock-Tracking-App/pull/37#issuecomment-5973462602), atomic issue/PR reviews, the head/CI table below and main integration gate |

ARCH-005 evidence here is shared domain validation/calculation under both legacy
CLIs, not a claim that CLI V2 or a future REST service has been completed.

## Reviewed topic provenance and hosted checks

All listed heads are ancestors of the #33 baseline. The Foundation runs below
passed all five jobs: Tests (Python 3.11), Tests (Python 3.12), Ruff,
Mypy (configuration), and Credential patterns. These are exact-topic-head checks,
not substitutes for final main source/CI verification. PR states below are the
2026-10-03 authoring snapshot and may change after owner action.

| Issue / PR | Reviewed head | Passing Foundation run | Topic publication | Main inclusion at snapshot |
| --- | --- | --- | --- | --- |
| #25 / #37 | `73055483a1d20db599000c479c0649bc73cdebb8` | [37153905494](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37153905494) | Owner merged to main | Accepted docs included |
| #26 / #38 | `10be288e0059f45129c63467f6d0847baf50729a` | [37154428042](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37154428042) | Merged to docs/25-domain-contracts | Runtime pending |
| #27 / #39 | `3d02bea569168cb38eace3fe01524d8456075335` | [37154780788](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37154780788) | Merged to feature/26-stock-domain | Runtime pending |
| #28 / #40 | `3b38753609e070c9b8b3c4a5ede8b3c805e8e006` | [37155168697](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37155168697) | Merged to feature/27-position-domain | Runtime pending |
| #29 / #41 | `6f8d62dfdc9ac84ec2e7da33bc74bbf2e165c242` | [37155521592](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37155521592) | Merged to feature/28-portfolio-domain | Runtime pending |
| #30 / #43 | `fc8790e6ccfb45289bf4d74f4e2ec9650e8e9686` | [37172354474](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37172354474) | Reviewed, open | Runtime pending |
| #31 / #44 | `0fa359585792b84c77e2fa8200b2402e76454b43` | [37172939853](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37172939853) | Reviewed, open | Runtime pending |
| #33 | Pending publication | Pending #33 exact-head CI | This evidence/test proposal | Pending |
| #42 | Pending final integration | Pending integration PR and runtime main CI | Owner main publication required | Pending |

## Independent guard design

`tests/domain_isolation_probe.py` starts with stdlib guard setup, then denies
legacy/compatibility/UI/provider imports (including relative and dynamic imports),
environment reads/iteration, network/DNS/urllib transport, SQLite connection,
ordinary builtins/io/os data-file access, and output through print/streams/os.write.
Import-loader access needed to load Python code remains available. Preloading
stdlib guard objects does not preload domain or any root application module.

Each denial is demonstrated by safe synthetic probes before domain execution:
an unavailable root/compatibility import, fictional environment lookup, denied
socket/URL work, an in-memory SQLite target, temporary `domain-probe` file calls,
zero-byte os.read/os.write, and output writes. Probes fail before work and leave
no file; no temporary production-source patch or unconditional skip remains.
Positive checks construct Stock/Position/Portfolio, preserve list ownership and
replacement state, and verify hand-derived snapshot values, missing price and
zero basis. Every actual domain module path must lie inside the supplied source
or installed target. The installed probe runs in its own `python -I` process
before root-module smoke, with no checkout application fallback.

## Local verification

From the isolated #33 worktree, the existing canonical pinned environments
(`f2ad/.venv` for Python 3.11 and `570c/.venv` for Python 3.12) produced:

| Command | Python 3.11 | Python 3.12 |
| --- | --- | --- |
| `python -m pytest tests/test_domain_isolation.py tests/test_packaging.py tests/test_repository_hygiene.py -q` | 11 passed | 11 passed |
| `python -m pytest -q` | 310 passed | 310 passed |
| `python -m ruff check .` | Passed | Passed |
| `python -m mypy` | Passed, 1 source file | Passed, 1 source file |
| `python -m pip check` | No broken requirements | No broken requirements |

Targeted/full suites included staged-index credential scanning, independent
guard probes and offline actual-wheel imports. Git diff/secret/generated-artifact
review passed; no live provider, real database or user pickle was used.
Strict configured mypy checks `config.py` only; no whole-domain or whole-application
typing claim is made. Final #33 head/hosted CI remain pending publication rather
than inferred from these local results.

## Remaining limitations and completion gates

M2 owns FMP provider abstractions, malformed-response classification and
timeout/retry/cache policy. M3 owns safe structured persistence and legacy import;
current root CLIs still deserialize pickle at import and must never receive
untrusted state. M1 tests use trusted synthetic state only, discard historical
saved keys and exclude credentials/clients from new serialized state; this is not
a real-user migration. M4 owns genuine historical data: moved approximate charts
still reconstruct prices from summary returns and remain a known limitation.
M5 owns portfolio analytics and any unapproved financial conventions; M6 owns
CLI V2 and larger service/display redesign.

Snapshot inputs must share one currency. Missing values remain different from
zero; zero cost basis leaves return undefined. No intermediate display rounding,
money quantization default, transaction/tax-lot behavior, dividend/FX treatment,
historical portfolio return, benchmark or risk convention is approved here.

Before reporting M1 complete, #42 must verify actual runtime source on main,
passing required main CI after owner merge, required issue closures and no
blocking work. The evidence of source in this topic stack alone is insufficient.

## Main integration preparation — issue #42

The original topic-authoring snapshot above is retained as historical evidence.
The final independently reviewed [PR #45](https://github.com/daniilnahl/Stock-Tracking-App/pull/45)
head is `dd5a47d98e79b03642a3e67dec242092391dde7a`; its
[Foundation run 37177633168](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37177633168)
passed all five required checks. Both independent review and master review passed.

The isolated `codex/42-m1-main-integration` branch starts at that exact head.
On 2026-10-03, refreshing `origin/main` still resolved to
`7ea5867114b9cee9171413c9853facdee093e84f`; the common ancestor was accepted
ADR commit `73055483a1d20db599000c479c0649bc73cdebb8`. The seven implementation
commits listed above (#26–31 plus #33) are retained without rewriting history.
The main comparison contains only the reviewed M1 implementation/tests/docs and
accepted package-discovery extension; no dependency pins, supported Python,
configuration implementation, CI workflow or financial specification changed.
Issue #42 adds only this final evidence section to the reviewed topic source.

From this integration worktree, serial checks in the same existing pinned
Python 3.11.9 and 3.12.10 environments produced:

| Command | Python 3.11 | Python 3.12 |
| --- | --- | --- |
| `python -m pytest -q` | 310 passed | 310 passed |
| `python -m ruff check .` | Passed | Passed |
| `python -m mypy` | Passed, 1 source file | Passed, 1 source file |
| `python -m pytest tests/test_repository_hygiene.py --tb=short` | 8 passed | 8 passed |

Full suites include independent source/wheel isolation, installed legacy smoke,
known-value calculations, facade state/credential and both CLI regressions.
Staged credential scanning includes the integration documentation. Final diff,
secret and generated-artifact inspection passed; tests used only mocked provider
work and trusted temporary synthetic state. No live credentials or user state
were accessed. Configured strict mypy remains limited to `config.py`.

Integration PR publication, exact integration-head hosted checks, owner merge,
actual runtime inclusion on main, subsequent required main CI and closure of
#26/#27/#28/#29/#30/#31/#33/#42 remain pending. The integration PR will carry all
closing links; this preparation does not close issues or declare M1 complete.
Its eventual PR/review record supplies its own head and CI evidence without a
circular self-commit claim. Only the owner may merge; milestone completion still
requires the final gates recorded above.
