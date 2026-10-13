# M6 CLI V2 implementation plan

Status: **IN PROGRESS — Option A accepted; #114 local service implementation active**.
Snapshot: 2026-10-13 (America/Los_Angeles).
Baseline: `11f7333abdac830e139dd74354c87b30fe4cd45d`, owner-merged M5 audit PR #110.
Parent: [M6 — CLI V2](https://github.com/daniilnahl/Stock-Tracking-App/milestone/7).
Contract: [Accepted ADR-0012](../adr/0012-cli-application-services.md).

The owner requested the Master Engineering workflow for M6. The supplied
master-agent document's old M2 placeholders do not override that request.
Master owns planning and independent review; bounded implementation is delegated
only when requirements and dependencies permit. Agents must not merge.

## Authority and readiness

Approved SRS §23 M6 requires the CLI to become a thin application-service
interface. Its `stocktracker portfolio`, `position`, `stock` and `analytics`
commands are explicitly **potential commands**, not an approved required CLI
contract. ARCH-001/003/004/005 require layer separation, provider/repository
abstractions and reusable services; ARCH-006 requires an accepted ADR for a
material architecture decision. Beginning M6 does not approve new public
commands, financial conventions, portfolio selection rules or service contracts.

GitHub issue #107 is closed completed and its embedded M5 milestone is closed,
with no open required issues. The completion record identifies final PR Foundation
[38349919901](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38349919901)
and post-owner-merge main Foundation
[38353960939](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38353960939)
as passing all five configured checks. This readiness evidence is historical M5
verification, not verification of future M6 behavior. Local M5 plan/evidence files
still retain pre-merge snapshots; this task does not rewrite those unrelated records.

Typed domain calculations, numeric provider models/protocols, SQLite repositories
and genuine historical data/cache/chart capabilities exist. The root CLIs still
orchestrate configuration, restoration, lookup/profile/summary calls, ownership
input, mutation and persistence. No `services` or `cli` package or installed
console entrypoint exists. Watchlists remain separate from domain Portfolios.
At that readiness baseline, the missing architectural component was the maintained
shared service layer. #114 now adds the accepted local boundary and contracts.

Both root interfaces have tested callable compatibility surfaces: `API_KEY`,
`current_watchlist`, `_watchlist_loaded`, `load_watchlist`, `save_watchlist` and
`_prepare_command`. Existing tests/probes protect precise Decimal state, ordered
duplicates, namespace separation, existence-only legacy protection, offline help,
failure/no-save behavior and genuine history. Extraction must preserve these
meaningful guarantees, rather than delete tests because they constrain design.

## Accepted scope and owner decision

Recommended Option A is compatible thinning of both maintained watchlist CLIs:
local state, current-data operations and historical retrieval move to injected,
presentation-independent services; commands retain prompts, input parsing,
rendering and safe error mapping. Correct the established financial headings.
Keep current command names, namespaces, schema, runtime/dependency pins and
configured mypy scope. Service results must preserve numeric financial values
and existing legacy display metadata without promoting display text into domain
values. See the accepted ADR for exact contracts and adapters.

The owner directly instructed **"Option A approved, pr merged, continue"** on
2026-10-13. PR #120's reviewed head `23169daa36e751c021506dead62b52eaf0c0ff3e`
is owner-merged at `96182b6e9b28c743a05a9e8cfb7985b5c8b833f6`; exact PR
Foundation [38442157132](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38442157132)
and post-merge main Foundation
[38442587378](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38442587378)
passed all five configured checks. The contract prerequisites are satisfied and
#114 is dispatched on `feature/114-local-watchlist-service` from this merged
main. #115–117 retain their own dependency merge/CI gates. Alternative installed entrypoint or new
Portfolio/Position CLI scope requires defined selection/duplicate semantics,
input provenance and command contracts before issues are expanded or added.

Portfolio summary acquisition is not implied by existing pure M5 arithmetic:
stored Portfolio positions contain no currencies or observations; ADR-0011
requires separate explicit cost/quote currency assertions. Saved display metadata
and provider quote currency do not establish cost currency. Risk, historical
performance, benchmark, FX, dividends and transaction conventions stay outside
the proposed scope; their undefined semantics remain blocked.

The independent #113 headings correction is already specified by FC-020/041/091/101:
`Cost Basis` currently displays average per-share cost and `Your Total Return`
displays snapshot unrealized return. Replace headings with `Average Cost per Share`
and `Unrealized Return` while preserving values, formatting and arithmetic.

## Dependency and delegation map

| Issue | Objective | Status | Dependency / blocker | Agent | PR / review |
| --- | --- | --- | --- | --- | --- |
| [#112](https://github.com/daniilnahl/Stock-Tracking-App/issues/112) | Propose and approve service/CLI contracts and exit criteria | Accepted, owner-merged; closure gates passed | None | `m6_readiness` drafts ADR; Master plan; `m6_contract_review` independent review | [#120](https://github.com/daniilnahl/Stock-Tracking-App/pull/120); technical review PASS; PR/main CI passed |
| [#113](https://github.com/daniilnahl/Stock-Tracking-App/issues/113) | Correct financial table headings | Owner-merged; review and CI passed | None | `m6_terminology`, isolated `fix/113-financial-table-terminology` | [#119](https://github.com/daniilnahl/Stock-Tracking-App/pull/119), reviewed head `9aa7f026`; merge `11e262c3` |
| [#114](https://github.com/daniilnahl/Stock-Tracking-App/issues/114) | Local watchlist service boundary | PR open; local verification and independent review passed | Owner merge and required PR/main CI | `m6_readiness`, `m6_contract_review` independent review | [#121](https://github.com/daniilnahl/Stock-Tracking-App/pull/121) |
| [#115](https://github.com/daniilnahl/Stock-Tracking-App/issues/115) | Current-data orchestration service | Blocked | #112 and complete owner-merged #114 | Unassigned | — |
| [#116](https://github.com/daniilnahl/Stock-Tracking-App/issues/116) | Historical retrieval service | Blocked | #112 and stable owner-merged #114; independent of #115 thereafter | Unassigned | — |
| [#117](https://github.com/daniilnahl/Stock-Tracking-App/issues/117) | Thin adapters for both maintained CLIs | Blocked | Owner-merged #114–116 with required CI | Unassigned | — |
| [#118](https://github.com/daniilnahl/Stock-Tracking-App/issues/118) | Independent combined exit audit and operation docs | Blocked | Approved exit criteria and owner-merged #113–117 | Unassigned | — |

Each issue belongs to GitHub milestone **7**, whose SRS identity is **M6**.
One bounded issue normally owns one branch and PR. #112 uses
`docs/112-cli-service-contracts`; #113 uses an isolated worktree so implementation
and proposal changes do not mix. #115/#116 may run concurrently only after the
shared approved boundary stabilizes; no implementation starts on a blocked issue.

During #114 review, distinguish independent neutral row occurrences from repeated
references to the **same** root facade supplied by an explicit in-memory caller.
Root facades use object identity; neutral record equality must not substitute for
that identity. #114 preserves positional deletion and forward skips for structured
rows and changes no root command. #117 must test and preserve the legacy alias
case (for example `[same A, same A, B, same A]` removes to `[B, A]`) when adapting
root in-memory state. This is existing callable compatibility work, not a new
financial, identity-deduplication or removal-policy decision.

## Accepted exit criteria

Under owner-accepted Option A, require:

- Both maintained CLI surfaces delegate application orchestration to shared
  services; service use cases do not depend on prompts, terminal/chart rendering,
  provider payload schemas or direct SQL.
- Existing use cases, exact numeric holdings, namespaces, legacy protection,
  safe failure behavior and genuine historical observation rules remain intact.
- Imports and help perform no provider/storage work; source and installed-wheel
  command/restart tests execute actual services with controlled infrastructure.
- Every required issue is closed, implementation PRs are owner-merged, required
  exact PR/main CI passes and an independent requirement/test/exit audit passes.

The SRS supplies the architectural objective; the owner-accepted criteria make
it testable without expanding required command or financial scope.

## Verification and operational notes

Use canonical Python 3.11/3.12 with `python -m pip install ".[dev]"`, targeted
pytest, full pytest, Ruff, configured `python -m mypy` (`config.py` only) and
pip check. No runtime/toolchain pins change. Tests must use controlled providers,
fixed clocks, temporary state and subprocess guards proven by safe controls.
Source/wheel service isolation must detect hidden presentation dependencies.

The sandbox attempt to create Python 3.12 `.venv` failed in ensurepip. The same
canonical creation/install succeeded under approved execution using the existing
Python 3.12.10 installation. No system software was installed. Browser automation
could not initialize (`CreateProcessWithLogonW failed: 1056`); GitHub's connector
does not expose milestone management and rejected issue writes with HTTP 403.
The existing Git credential manager and normal GitHub REST API successfully
created the milestone/issues under approved execution; credentials remained in
memory and were neither logged nor committed. Temporary tooling stays ignored.

Proposal and terminology verification results are recorded separately below;
passing unchanged-runtime proposal checks does not verify future service behavior.

### Proposal baseline verification

Canonical `.venv` Python **3.12.10**:

| Command actually run | Result |
| --- | --- |
| `python -m pytest tests/test_cli_ownership.py tests/test_cli_persistence.py tests/test_history_date_selection.py tests/test_snapshot_analytics.py tests/test_packaging.py -q --tb=short` | **183 passed in 53.61s** |
| `python -m pytest -q --tb=short` | **2243 passed in 101.93s** |
| `python -m ruff check .` | Passed |
| `python -m mypy` | Passed; one configured source file |
| `python -m pip check` | Passed |

Initial sandbox pytest could not create numbered temporary fixture directories;
all 183 cases failed at setup before behavior executed. The identical targeted
command passed under approved execution with normal temporary-directory access.
No fixture or production behavior was altered to resolve the environment restriction.
Python 3.11 and hosted proposal CI have not yet been verified for this change.
Independent ADR review, staged hygiene and final diff review are tracked below
when performed. Runtime services remain unimplemented and unverified.

Independent `m6_contract_review` reviewed the final proposed interfaces and
compatibility against authoritative sources. The configuration-failure callback,
explicit period invalidation without fabricated observations, and sequential
display projection contracts were clarified. Final review **PASS**, no remaining
actionable findings. This review approves the proposal's technical coherence,
not product/architecture acceptance. Master staged-source hygiene passed
**8 tests in 6.47s** and reviewed the two-document diff for scope, secrets and
generated artifacts. Final staged hygiene after the reviewed clarifications
passed **8 in 6.27s**, and final staged/branch diff checks passed. Proposal
[PR #120](https://github.com/daniilnahl/Stock-Tracking-App/pull/120) was open for
explicit owner acceptance; hosted proposal CI was pending. No service runtime
implementation had been dispatched at that proposal snapshot. The later owner
acceptance and verified merge/main-CI record above releases #114.

### Independent terminology task — #113

[PR #119](https://github.com/daniilnahl/Stock-Tracking-App/pull/119) changes two
production headings and adds real rendered/nonmutation coverage with both CLI
flows. Python 3.12.10 targeted checks passed **138 in 9.18s**; full pytest passed
**2249 in 98.41s**. Ruff, configured mypy, pip check and final/staged diff checks
passed. Master independently reviewed all four files and ran the rendered/both-CLI
cases: **58 passed in 3.02s**, no actionable findings. Final head is
`9aa7f0260a2b52185786f045119ed6cc46c010cd`. Exact-head
[Foundation run 38441573466](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38441573466)
completed successfully. PR #119 is now owner-merged at
`11e262c391da129250afa8f04d8e82a432cceadb`, included in the passing combined
main run `38442587378`. No agent merge occurred.
Its six added cases do not verify future services.

### Local service boundary — #114

The implementation adds injected `WatchlistService.load/save/view/remove`,
accepted shared neutral records/ports, and the lazy existence-only
`LegacyFilePresence` composition adapter. Local views use the existing pure
position calculator; ownership, price and ratios remain Decimal/None. Complete
candidate revalidation and exact namespace checks precede save dependencies;
existing corrupt/malformed data is never treated as an empty replacement.
The explicit wheel package list includes services and CLI storage adapters.
Current-data/history use cases and root command integration remain #115–117.

Canonical Python **3.12.10** actual verification:

| Command | Result |
| --- | --- |
| `python -m pytest tests/test_watchlist_service.py tests/test_service_boundary.py tests/test_packaging.py tests/test_sqlite_watchlists.py tests/test_cli_persistence.py -q --tb=short` | **159 passed in 53.33s**, final probe guards |
| `python -m pytest -q --tb=short` | **2302 passed in 110.72s** |
| `python -m ruff check .` | Passed |
| `python -m mypy` | Passed; `config.py` only |
| `python -m pip check` | Passed |
| `python -m pytest tests/test_repository_hygiene.py -q --tb=short` | **8 passed in 8.24s**, task files staged |
| `git diff --cached --check` | Passed |

Master independently reviewed source/tests and ran local service/source-process
cases: **53 passed in 2.06s**. After strengthening restart guards before production
imports, Master reran that source process: **1 passed in 1.47s**. Independent
review also ran **53 in 2.96s**. Missing frozen optional slots are now rejected
without substituting absence, and equal-valued independent rows retain the
correct survivor. Guard controls prove denial before actual service imports;
separate source/wheel SQLite write/read processes preserve exact state and
both namespaces without legacy content reads or local display writes.

No required local verification remains outstanding. PR/main CI and owner merge
remain dependency gates before #115/#116 begin. Passing this local capability
does not establish the later thin CLI or combined milestone exit.

[PR #121](https://github.com/daniilnahl/Stock-Tracking-App/pull/121) is open;
initial implementation head is `e0b37f4e7131c67657b78e6295ec482affd5aa97`.
Independent final technical review passed all 15 task files, with no remaining
actionable findings. Final branch diff checks passed and the worktree was clean
before this PR-link status record. Required exact-head hosted CI and owner merge
remain pending at submission. No agent merge occurred.
