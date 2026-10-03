# M1 Domain Refactor implementation plan

Status: accepted contract plan for [#25](https://github.com/daniilnahl/Stock-Tracking-App/issues/25).
[ADR-0006](../adr/0006-domain-contracts.md) is **Accepted**: the owner accepted
proposal commit `f4693ab` on 2026-10-03 in the
[PR #37 acceptance comment](https://github.com/daniilnahl/Stock-Tracking-App/pull/37#issuecomment-5973462602).
The contract gate is satisfied; runtime implementation remains pending and
requires resolved upstream implementation dependencies. This plan does not close
an issue or milestone and does not authorize agent merges.

The current baseline is main `d94a0cacc73f986581680e4e26167c67ee2c583c`.
M0 exit issue #13 is closed; canonical Python/pip/pins remain ADR-0005.
Strict mypy is configured for config.py; run `python -m mypy` alongside full
`python -m pytest` and `python -m ruff check .`. Older M1 issue notes saying
mypy is unconfigured or M0 remains open describe planning-time state and must
not drive implementation. Follow [TESTING.md](../TESTING.md) isolation rules.

| Issue | Owned files / contract | Blocking implementation dependencies | Required evidence |
| --- | --- | --- | --- |
| [#25](https://github.com/daniilnahl/Stock-Tracking-App/issues/25) | Accepted ADR, this map; no runtime edits | Acceptance recorded; review/issue completion tracked separately | Requirement/link review, hand checks, dated acceptance |
| [#26](https://github.com/daniilnahl/Stock-Tracking-App/issues/26) | Package skeleton, domain Stock/errors; narrow setuptools/checkout discovery; packaging tests | #25 accepted | Immutability, local validation, known/unknown exchange equality, offline wheel/root imports |
| [#27](https://github.com/daniilnahl/Stock-Tracking-App/issues/27) | domain Position and ownership tests | #25, #26 | Exact Decimal/fractional/zero values, finite/nonnegative validation, immutable replacement atomicity |
| [#28](https://github.com/daniilnahl/Stock-Tracking-App/issues/28) | domain Portfolio and container tests | #25, #27 | Owned list copied at construction, independent defaults, ids/names, order/duplicates, differing exchanges |
| [#29](https://github.com/daniilnahl/Stock-Tracking-App/issues/29) | domain calculations/PositionSnapshot and known-value tests | #25, #27 | FC fixture, fractional/loss/zero cases, missing versus zero, wrong-type/negative/nonfinite quotes, no stale result/rounding |
| [#30](https://github.com/daniilnahl/Stock-Tracking-App/issues/30) | root Stock facade, compatibility numeric/operations/presentation modules, minimum Watch_list.wrap_percent sentinel mapping, synthetic state/credential tests | #25, #26, #27, #29; completed #7 configuration preserved | Constructor/method/field mapping, real calculation beneath mocked IO, serialized-state/bytes key exclusion, saved-key discard/current rebinding, local restore with missing/blank config then blocked request, trusted state holdings |
| [#31](https://github.com/daniilnahl/Stock-Tracking-App/issues/31) | Both CLI ownership prompts/errors and broader Watch_list display/refresh integration | #25, #30 | High-precision text, meaningful re-prompts, no invalid save, safe unavailable/undefined display, unchanged help/commands |
| [#33](https://github.com/daniilnahl/Stock-Tracking-App/issues/33) | Focused domain isolation/installed wheel tests and exit documentation | #25–31 complete | Guarded fresh process on 3.11/3.12, canonical checks and real required CI evidence |

#26 creates package export/error scaffolding; later model owners extend the
exports only after those contracts land. Implement sequentially where shared
files/contracts overlap. #28 and #29 can be reviewed independently after #27;
parallel execution requires separate worktrees and stable contracts. Tests stay
with each implementation issue; #33 supplies transitive architecture evidence,
not deferred correctness coverage. One issue normally produces one branch/PR.
No agent merges; blocked dependencies are not bypassed by additive scaffolding.

| SRS §23 M1 bullet / requirement | Implementation evidence owner |
| --- | --- |
| Clean Stock; DOM-001/002 | #26, facade identity bridge #30 |
| Position; DOM-003, FIN-001–003 | #27, precision integration #30/#31 |
| Portfolio; DOM-004 | #28 |
| Financial logic outside CLI; FIN-004/005 | #29 single FC calculation; #30 delegates; #31 removes duplicate semantic input validation |
| Remove domain infrastructure; ARCH-001/002/005 | #26–29 pure package; #30 external facade; #31 existing caller integration |
| Architecture traceability; ARCH-006, GH-003/004 | #25 accepted ADR; individual issue PR evidence |
| Unit tests and isolation exit; TEST-001–005, ERR-001–003 | Each issue's tests/errors plus #33 process/wheel checks and exit report |

Legacy calculation lives on Stock, not in CLI; extraction and CLI validation
integration together satisfy the financial-logic milestone bullet. Watch_list
continues representing watched securities and can contain unowned entries;
Portfolio does not silently inherit or merge that state.

M2 owns provider models/interfaces, malformed-response classifications,
validation fixes, timeout/retry/cache choices and schema handling. M3 owns SQLite,
repository/schema decisions, safe legacy import/migration and removal of primary
pickle storage; M1 synthetic-state compatibility is not migration. M4 owns real
historical charts and trading-date/adjusted-price decisions. M5 owns portfolio
metrics and unresolved financial conventions. M6 owns CLI V2, larger service
wiring/table relabeling and redesign. Existing synthetic charts and unsafe legacy
pickle loading remain visible limitations; no production certification is implied.

Before recommending M1 complete, #33 must record all required issue/PR statuses,
actual passing canonical checks and required PR/main CI after human merges, and
prove domain imports/construction/calculation work without environment, network,
DB, CLI/chart or legacy imports. Subprocess guards must be independent of parent
pytest patches and demonstrated by safe temporary probes removed before commit.
Installed-wheel tests must import the wheel from an empty temporary cwd, with no
checkout fallback. No user pickle/database, live quote or credential is used.
Missing implementation or verification evidence keeps completion blocked; recorded
contract acceptance does not establish milestone completion.
