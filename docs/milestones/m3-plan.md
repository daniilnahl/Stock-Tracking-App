# M3 Persistence implementation plan

Status: **contract accepted; #69 records/interfaces implementation in progress**.
Snapshot: 2026-10-05. Implementation baseline main: 48944f9.
Parent: [M3 — Persistence](https://github.com/daniilnahl/Stock-Tracking-App/milestone/4).
[ADR-0009](../adr/0009-persistence-contracts.md) Option A was accepted by the
owner's direct statement "Option A approved and PR merged" at exact commit
8e525177c7443fc92e1afc6b42e573ad3a3c43b2. The Master recorded acceptance in
[issue #68](https://github.com/daniilnahl/Stock-Tracking-App/issues/68#issuecomment-5999983033);
that comment is a faithful record, not independently human-authored approval.
Owner-merged [PR #77](https://github.com/daniilnahl/Stock-Tracking-App/pull/77)
reached main at 48944f98938639628cfe216d4d0bc6883f0f5f26 with all five required checks
passing in [Foundation](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37351164698).
The SRS §23 contract gate is satisfied; downstream implementation dependencies
and owner merges remain required. Acceptance is not M3 runtime completion.
No agent merge is authorized; reviewed PRs require owner merge under AGENTS.md.

## Repository analysis

Domain Stock, Position and Portfolio already exist and are isolated. Portfolio
preserves any non-bool integer/None id and ordered duplicate Positions. The two
root CLIs save separate cwd-relative pickle files and automatically load at
import. Watch_list is a distinct ordered collection with display/orchestration;
its unowned stock entries have no Position. Stock.__getstate__ excludes runtime
keys and restoration recomputes derived return. M2 routes provider operations
through typed interfaces; CSV is no longer validation evidence. No persistence
package, schema, repository, migration runner or backup policy exists.

PERS-001–007 runtime implementation and M3 restart behavior are outstanding;
PERS-008's decisions are accepted in ADR-0009. Decimal text avoids the
unapproved financial quantization question. Watchlist/Portfolio distinction,
namespaces, duplicates, missing quotes and ownership must survive restart; a
unique ticker table or implicit conversion would lose accepted semantics.
Accepted ADR-0009 defines database location, schema/versioning,
uniqueness, allocation, delete/cascade, legacy transition and backup/restore.
The approved legacy filename/loading extension is explicit. Manual neutral recovery does
not promise to recover arbitrary pickle contents. Existing user files remain
untouched; no safe-state test may read them.

## Live issue and dependency view

| Issue | Bounded objective | Status / dependencies | Assigned agent | PR / review | Blocking reason |
| --- | --- | --- | --- | --- | --- |
| [#68](https://github.com/daniilnahl/Stock-Tracking-App/issues/68) | Accepted persistence ADR and this issue map | Closed; contract gate satisfied | Completed | [#77](https://github.com/daniilnahl/Stock-Tracking-App/pull/77); owner merged/main CI passed | None |
| [#69](https://github.com/daniilnahl/Stock-Tracking-App/issues/69) | Records, repository interfaces, errors, packaging | In progress; #68 satisfied | persistence_analysis; Master/independent review | None; draft verification | Implementation/review/owner merge |
| [#70](https://github.com/daniilnahl/Stock-Tracking-App/issues/70) | SQLite connection/schema/migration runner | Open; #68, #69 | Unassigned | None | Contracts and interfaces |
| [#71](https://github.com/daniilnahl/Stock-Tracking-App/issues/71) | SQLite Portfolio repository | Open; #68, #69, #70 | Unassigned | None | Stable schema/interfaces |
| [#72](https://github.com/daniilnahl/Stock-Tracking-App/issues/72) | Ordered watchlist repository and facade mapping | Open; #68, #69, #70 | Unassigned | None | Stable schema/interfaces |
| [#73](https://github.com/daniilnahl/Stock-Tracking-App/issues/73) | Both CLI storage integration | Open; #68, #72 | Unassigned | None | Watchlist implementation/approval |
| [#74](https://github.com/daniilnahl/Stock-Tracking-App/issues/74) | Safe neutral transition, backup/restore, documentation | Open; #68, #70, #71, #72 | Unassigned | None | Approved transfer and repositories |
| [#75](https://github.com/daniilnahl/Stock-Tracking-App/issues/75) | Restart/installed-artifact verification and exit evidence | Open; #68–74 | Unassigned | None | All required implementation and owner merges |

Implement #69 then #70. #71/#72 may run concurrently only in isolated branches
after interfaces/schema stabilize, with non-overlapping implementation modules.
#73 waits for #72. #74 needs both repositories and must avoid changing their
contracts implicitly. Each issue owns its own tests; #75 does not defer testing.
Update this table with actual assignments, PRs, review findings and CI evidence.
One issue normally produces one branch, implementation agent and PR; do not
dispatch blocked implementation just to maximize concurrency.

## Requirement, caller and evidence map

| Requirement / deliverable | Issues | Required evidence and relevant callers |
| --- | --- | --- |
| Accepted persistence ADR; PERS-008, ARCH-006 | #68 | Recorded human exact-commit acceptance covering all six decisions and ADR-0006 compatibility extension |
| Repository abstraction; ARCH-001/002/004, DOM-001–004 | #69, #71, #72 | Typed protocols/records, independent imports; domain has no SQLite/environment/UI dependencies |
| Schema and SQLite; PERS-001–003 | #70–73 | Bound input SQL, every connection FK enabled, corrupt/future DB refusal; existing root save/load callers use repositories |
| One migration runner/data preservation; PERS-004/005 | #70, #74 | Version initialization/idempotence, unsupported versions, failed migration rollback, explicit backup before future upgrade |
| Atomic operations; PERS-006 | #71, #72, #74 | Full-validation-before-write, multi-row rollback, ID and neutral-import collision tests |
| Isolated persistence tests; PERS-007, TEST-001–005 | #69–75 | Temporary paths/databases and offline guards; no real user state or provider calls |
| Precision/missing data; FIN-001–003, FC-001–004/110 | #71–73 | Exact Decimal roundtrip including exponent/high precision; zero versus unowned/NULL; known-value snapshots recomputed |
| Identity/order compatibility; DOM-002, ADR-0006 | #71, #72 | Same-symbol/different-exchange, unknown exchange, repeated known identities, arbitrary explicit integer ids and ordinals |
| Safe credentials/errors; SEC-002/005, ERR-001–003 | #69, #72–74 | No persisted runtime key/client, current key rebinding, fixed safe diagnostic output and no raw cause leakage |
| Legacy transition and backup/restore | #74 | Reviewed neutral JSON, limits/strict validation, no pickle reader, untouched original files, conflict refusal, checked SQLite backup to new destination |
| Restart without pickle; SRS §23 exit | #73, #75 | Independent source/installed processes preserve Portfolio and both CLI namespaces; no automatic application pickle reads/writes |

Relevant implementation: stock.py; watch_list.py; both root CLI modules;
src/stock_tracker/domain/{stock,position,portfolio,calculations}.py;
compatibility/numeric.py; config.py; pyproject.toml and stock_tracker.exceptions.
Root CLI signatures remain reviewable; no public domain redesign is needed.

Existing tests requiring deliberate integration updates: test_cli_ownership.py,
test_configuration_security.py, test_provider_integration.py, test_baseline.py,
test_fmp_configuration.py and test_packaging.py. They assert exact legacy paths,
pickle bytes/decoding and empty-state no-write behavior. Update storage-specific
assertions to repository/restart evidence while preserving precision, credential
exclusion, failure/no-match state preservation, command/output and call counts.
Keep test_stock_facade.py trusted synthetic pickle compatibility coverage; it
does not imply application storage endorsement. tests/conftest.py temp cwd and
offline boundaries must also protect every new path. Wheel tests enumerate exact
payload, requiring new persistence modules and installed restart verification.

## Verification and milestone exit gates

Each issue runs targeted tests then the canonical full sequence:

```text
python -m pytest <relevant-test-path> -v
python -m pytest
python -m ruff check .
python -m mypy
```

Mypy currently checks config.py only; do not imply src/ is checked or silently
expand scope. Preserve pip/setuptools and Python 3.11/3.12. Report exact unavailable
tools/environment failures, never substitute a toolchain or invent pass results.
Inspect diffs, secrets/generated artifacts, scope and CI before PR publication.

Historical Master verification for the #68 documentation proposal on Windows Python 3.11.9 in
the pinned .venv: python -m pip check passed; targeted baseline/packaging/hygiene
passed 24 tests; full python -m pytest passed 1,334 tests in 22.69 seconds;
python -m ruff check . passed; python -m mypy passed config.py (one file).
These verified the existing baseline only. #68 owner acceptance, merge and CI
subsequently passed as recorded above. #69 verification and PR-head CI are
separate evidence. No M3 schema/repository/import/backup or restart exit behavior
has been implemented or verified.

#69 draft verification on the same Windows Python 3.11.9 pinned environment:
python -m pytest tests/test_persistence_contracts.py tests/test_packaging.py -q
passed 214 tests; python -m pytest passed 1,546 tests in 33.90 seconds;
python -m ruff check . passed; python -m mypy passed its configured one-file
config.py scope. Source and offline installed-wheel probes exercised import and
record construction with filesystem/environment/network/database access denied.
This verifies records/interfaces/errors and packaging, not concrete repository,
schema, CLI storage, neutral transfer, backup or M3 restart behavior. Independent
review and PR-head CI/owner merge remain publication gates.

#75 records all merged commits, required main CI and issue closure against the
unchanged SRS exit criterion: **Application restart preserves portfolio state
without pickle.** Test actual Portfolio persistence as well as both independent
legacy watchlists, ordered duplicates, names, holdings, optional ownership/quote,
metadata and offline display. Explicit subprocess path injection and network
guards are necessary because parent pytest patches do not propagate. Validate
source and installed wheel, help/no-state behavior, legacy-state refusal, failed
save/refresh protection, backup/restore and no credential storage.

Do not close M3 while an approval, implementation, owner merge, CI, issue or exit
criterion remains outstanding. Proposed decisions and green local documentation
checks are not runtime completion. Later history cache, portfolio analytics,
transaction ledger and CLI V2 remain outside M3; preserve any discovered
unrelated defect as an explicit follow-up instead of expanding this milestone.
