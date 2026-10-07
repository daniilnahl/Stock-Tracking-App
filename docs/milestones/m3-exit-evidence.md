# M3 Persistence exit audit

Audit date: **2026-10-06**. Milestone: [M3 — Persistence](https://github.com/daniilnahl/Stock-Tracking-App/milestone/4).
Audit issue: [#75](https://github.com/daniilnahl/Stock-Tracking-App/issues/75).
Completed main: `534a178005a5dd5662ec0cb261cadaf3ce5f2888` (owner-merged PR #86).
**Status: COMPLETE, all behavior and closure gates PASS.** The initial
combined audit found a valid display-metadata regression. Its separately scoped
repair, #84/PR #85, is now owner-merged with passing main CI. The exact empty
metadata case remains in the audit. The owner merged the audit, final main CI
passed and all nine required issues and milestone 4 are closed. The
[completion record](https://github.com/daniilnahl/Stock-Tracking-App/issues/75#issuecomment-6025782936)
records zero open and nine closed milestone issues, with no blocker or deferred
M3 requirement. The historical verification below retains its original context.

## Approved deliverables and implementation trace

SRS §23 requires an accepted persistence ADR, schema, repository interfaces,
SQLite repositories, one migration mechanism, integration tests and a defined
legacy transition. Its unchanged exit criterion is:

> Application restart preserves portfolio state without pickle.

[ADR-0009](../adr/0009-persistence-contracts.md) Option A was accepted by the
owner's direct milestone-chat instruction at reviewed commit
`8e525177c7443fc92e1afc6b42e573ad3a3c43b2`. The
[Master acceptance record](https://github.com/daniilnahl/Stock-Tracking-App/issues/68#issuecomment-5999983033)
faithfully records that instruction; it is not separately human-authored GitHub
approval. This includes the explicit ADR-0006 extension replacing maintained
CLI pickle storage and preserving legacy files without deserialization.

All nine required issues are closed; the following owner merges are included
in completed main.

| Issue | Deliverable | Owner-merged PR | Exact merge commit |
| --- | --- | --- | --- |
| [#68](https://github.com/daniilnahl/Stock-Tracking-App/issues/68) | Accepted persistence contracts | [#77](https://github.com/daniilnahl/Stock-Tracking-App/pull/77) | `48944f98938639628cfe216d4d0bc6883f0f5f26` |
| [#69](https://github.com/daniilnahl/Stock-Tracking-App/issues/69) | IO-free records/protocols, safe errors, packaging | [#78](https://github.com/daniilnahl/Stock-Tracking-App/pull/78) | `c32cc4a977b9c6436805ddcb68de31b6171e802c` |
| [#70](https://github.com/daniilnahl/Stock-Tracking-App/issues/70) | Connection/schema/one migration runner | [#79](https://github.com/daniilnahl/Stock-Tracking-App/pull/79) | `31a671acd31c9dd5c46f8111d4f3d9cde3ec6c88` |
| [#72](https://github.com/daniilnahl/Stock-Tracking-App/issues/72) | Ordered watchlists/offline facade mapping | [#81](https://github.com/daniilnahl/Stock-Tracking-App/pull/81) | `3af26f130598671246166599468df12d835b0b60` |
| [#71](https://github.com/daniilnahl/Stock-Tracking-App/issues/71) | Exact Portfolio aggregate CRUD | [#80](https://github.com/daniilnahl/Stock-Tracking-App/pull/80) | `dcb9eea2b5e59cdf56ff89e543e89c86f60b0c80` |
| [#73](https://github.com/daniilnahl/Stock-Tracking-App/issues/73) | Both existing CLI storage flows | [#82](https://github.com/daniilnahl/Stock-Tracking-App/pull/82) | `abd3fbae637f81c9ba1960cf5ad651ed0ecca26a` |
| [#74](https://github.com/daniilnahl/Stock-Tracking-App/issues/74) | Strict neutral import and checked backup/new-destination restore | [#83](https://github.com/daniilnahl/Stock-Tracking-App/pull/83) | `68134088556646c7b1bf586fc0c9ac67b02332ec` |
| [#84](https://github.com/daniilnahl/Stock-Tracking-App/issues/84) | Safe display of accepted empty/literal percentage metadata | [#85](https://github.com/daniilnahl/Stock-Tracking-App/pull/85) | `f690ddb6ca2f118abb8aafda93c2a511e29538e5` |
| [#75](https://github.com/daniilnahl/Stock-Tracking-App/issues/75) | Combined source/wheel restart and final exit audit | [#86](https://github.com/daniilnahl/Stock-Tracking-App/pull/86) | `534a178005a5dd5662ec0cb261cadaf3ce5f2888` |

The Master verified all five checks in the repaired baseline
[Foundation run 37512406525](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37512406525):
Tests (Python 3.11), Tests (Python 3.12), Ruff, Mypy (configuration), Credential
patterns. The earlier implementation baseline `6813408` also passed all five
checks in [run 37406946853](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37406946853).
These earlier implementation-main checks are historical. Final post-merge
[Foundation run 37533716609](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37533716609)
passed all five configured checks on completed main after PR #86. The reviewed
audit head `74d64f4c396d845327daffcf2a1b86aede50bff3` and final main have identical
Git tree `03febb29876f8cbdef4319d359d39faf01c1c03e`; the 1,850-test full local
verification therefore covers the final merged contents. The Master reran the
exact broader targeted command below on final merged main: **498 passed in
43.45 seconds**. PR review/CI, owner merge and closure are reconciled in the
completion record.

## Requirement and test map

| Requirement | Included implementation and meaningful verification |
| --- | --- |
| ARCH-001/002/004/006 | ADR-0009; separate domain/persistence/compatibility boundaries; protocol contracts; `test_domain_isolation.py`, `test_persistence_contracts.py`, installed probes |
| PERS-001 | Concrete SQLite Portfolio/watchlist repositories and lazy CLI namespaces; no application/transfer pickle storage; independent source/wheel probes and the combined imported/restored CLI audit |
| PERS-002 | Bound record queries in both repositories/import; malicious literal input in `test_sqlite_portfolios.py`/`test_sqlite_watchlists.py` |
| PERS-003 | Every connection enables/verifies FK enforcement; cascade/orphan refusal, integrity/FK checked copies in schema/repository/transfer tests |
| PERS-004/005 | One `migrations.py` runner, transactional schema version 1, unsupported/unversioned/corrupt refusal with preserved bytes; `test_sqlite_migrations.py`; strict additions/checked copies in `test_persistence_transfer.py` |
| PERS-006 | `BEGIN IMMEDIATE` allocation/replacement/import; injected multi-row/schema/commit rollback and snapshot concurrency tests in migration/repository/transfer matrices |
| PERS-007, TEST-001–005 | Temporary fictional SQLite/JSON/legacy state; default network/config isolation; subprocess-owned guards; actual canonical check results recorded below |
| PERS-008 | Accepted ADR's cwd path, schema/version, exact uniqueness, delete/cascade, neutral transition and checked backup/restore contracts |
| FIN-001–003; FC-001–004/020/030/040/041/110 | Numeric domain values, exact `str(Decimal)` ownership/quote storage, no quantization; giant canonical IDs, zero/unowned/missing distinctions, independent known-value and precision tests |
| SEC-005, ERR-001–003 | Fixed safe storage/provider errors and no credential values in output/logs; synthetic-only fixtures; `test_configuration_security.py` and provider/CLI failure matrices. No saved runtime keys; trusted synthetic facade compatibility remains isolated |
| SRS §23 exit | Separate source/wheel Portfolio and both CLI restarts; `persistence_exit_probe.py` combines nonempty Portfolio plus both namespaces through neutral import/checked backup/new-directory restore and actual fresh CLI/repository reads |

Tests verify data preservation rather than infer it from version numbers or
schema names. Every requested malformed aggregate/list is refused whole;
unknown/future data is not silently repaired or replaced with empty state.

## Combined audit and resolved regression

The new audit launches separate prepare, initial-read, checked-copy and
restored-read processes against source and an offline installed wheel. Each
process installs its own urllib/socket/pickle/provider/legacy-content guards
and synthetic guard controls. It clears provider keys, prevents dotenv discovery
and verifies imported runtime paths. The fixture has a nonempty Portfolio with
ordered duplicates, distinct NASDAQ/NYSE exchanges, unresolved identity, exact trailing-zero/high-precision
holdings and known `10 × 100`/`10 × 120` snapshot values, plus both watchlist
namespaces with precise ownership, zero/missing quotes, unowned versus zero-cost owned state and saved
display metadata. Original/restore directories contain untouched opaque legacy
fixtures; imported namespaces must be authoritative.

Actual command:

```text
python -m pytest tests/test_persistence_exit.py tests/test_packaging.py -q
```

Historical result on `6813408`: **2 failed, 1 passed in 18.87 seconds**. Source and
installed-wheel combined reads both reach actual `show-stocks` and fail with
`ValueError("could not convert string to float: ''")` from
`Watch_list.wrap_percent`. The neutral fixture's `price_1d=''` is expressly
valid display metadata under ADR-0009. It is retained correctly by storage,
but the CLI could not render it. The exact empty metadata case is preserved;
no assertion was weakened and no runtime repair is hidden in this audit.

The minimal source diagnostic command `python -m pytest
tests/test_persistence_exit.py -q -x` reproduced one failure in 2.47 seconds.
The separately reviewed/owner-merged #84/PR #85 repair handles empty and literal
nonnumeric metadata at presentation only, preserves the exact stored text and
existing numeric percentage behavior, and escapes literal Rich markup. Its
post-merge main CI passed as recorded above. The resumed audit also exercises
literal `No observation` metadata, distinct exchanges and zero-cost ownership.
The repaired combined source/wheel command passed **3 tests in 23.21 seconds**.
The independent reviewer reran it and passed **3 tests in 22.46 seconds**.

## Local verification — 2026-10-06

Commands used the existing pinned Windows Python 3.11.9 `.venv` without installs.
All state was fictional and temporary. The broader targeted command was:

```text
python -m pytest tests/test_persistence_contracts.py tests/test_sqlite_migrations.py tests/test_sqlite_portfolios.py tests/test_sqlite_watchlists.py tests/test_cli_persistence.py tests/test_persistence_transfer.py tests/test_persistence_exit.py tests/test_packaging.py -q
```

Result: **498 passed in 35.69 seconds**. The full canonical suite,
`python -m pytest -q`, passed **1,850 tests in 55.56 seconds**.
`python -m ruff check .` passed;
`python -m mypy` passed its configured **one source file, config.py**;
`python -m pip check` reported no broken requirements. `git diff --check`
passed. Master staged repository hygiene passed 8 tests via
`python -m pytest tests/test_repository_hygiene.py -q`; Master and independent
source/test/documentation review passed with no unresolved findings.

## Exit and closure gates

| Gate | Status |
| --- | --- |
| Eight required implementation/repair prerequisites accepted, owner-merged and closed | PASS on the recorded baseline |
| Five implementation-main CI checks | PASS, run 37512406525 |
| Combined valid import/restored CLI offline display | PASS, source and installed-wheel combined checks and independent rerun |
| Required repair owner merge and post-merge main CI | PASS, #84/PR #85 |
| Local targeted pytest, Ruff, configured mypy, pip check and diff check | PASS; exact commands/results above |
| Local full pytest | PASS, 1,850 tests in 55.56 seconds |
| Master staged hygiene and final review | PASS; 8 hygiene tests and no unresolved review findings |
| Audit PR review/CI, owner merge, final main CI and #75 closure | PASS, PR #86; final Foundation run 37533716609 |
| Final required-issue/blocker reconciliation and milestone closure | PASS; all nine issues closed, zero blockers; milestone 4 closed |

## Honest limits and later work

Storage is local and cwd-scoped, with last-successful-save replacement and no
cross-process optimistic conflict detection. Version 1 is the only supported
schema; there is no future upgrade to exercise. Future upgrades require verified
backup/data-preservation evidence. Backup/restore use new destinations, preserve
the source and promise no encryption, scheduled retention or hostile-filesystem
race protection. Failed new initialization/copy may leave an unusable empty file,
which is reported and never automatically deleted.

Legacy recovery requires manual reviewed neutral reconstruction; inaccessible
pickle-only information may remain unrecoverable. Neutral transfer's 4,096
character string cap cannot carry every giant ID supported by repositories;
values are never truncated. Saved quotes are last-observed, without freshness
claims. Configuration mypy checks **config.py only**, not all persistence/domain
modules. These accepted limits are not hidden as passed broader guarantees.
No runtime, dependency, Python, migration framework, CI or financial semantics
are changed by this audit. Historical data/charts, analytics, transaction ledger
and CLI V2 remain later approved milestones. The discovered display regression
was repaired within M3, not deferred to evade the exit criterion.

Final milestone status: **COMPLETE**. All SRS M3 deliverables and the unchanged
restart-without-pickle exit criterion pass. No human decision, blocking issue
or deferred M3 work remains. Accepted limits and later milestone scope above
remain unchanged; this completion does not authorize operations on real user data.
