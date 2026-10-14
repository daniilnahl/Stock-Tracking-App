# M6 CLI V2 implementation plan

Status: **REQUIRED IMPLEMENTATION COMPLETE — #112–118 closed; audit owner-merged and PR/main CI passed.**
Administrative documentation/showcase follow-up: #126.
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
| [#114](https://github.com/daniilnahl/Stock-Tracking-App/issues/114) | Local watchlist service boundary | Closed; owner-merged, review and required CI passed | None | `m6_readiness`, `m6_contract_review` independent review | [#121](https://github.com/daniilnahl/Stock-Tracking-App/pull/121), merge `aa6ecdd3` |
| [#115](https://github.com/daniilnahl/Stock-Tracking-App/issues/115) | Current-data orchestration service | Owner-merged; required PR/main CI passed | None | `codex/115-current-data-service`, resumed from `m6_readiness` draft | [#123](https://github.com/daniilnahl/Stock-Tracking-App/pull/123), merge `6c38eb9d` |
| [#116](https://github.com/daniilnahl/Stock-Tracking-App/issues/116) | Historical retrieval service | Closed; owner-merged, PR/main CI passed | None | `m6_terminology`, `feature/116-history-service`; `m6_contract_review` independent review | [#122](https://github.com/daniilnahl/Stock-Tracking-App/pull/122), merge `a9739dca` |
| [#117](https://github.com/daniilnahl/Stock-Tracking-App/issues/117) | Thin adapters for both maintained CLIs | Closed completed; owner-merged with passing PR/main CI | None | `codex/117-cli-service-adapters` | [#124](https://github.com/daniilnahl/Stock-Tracking-App/pull/124), merge `926171e3` |
| [#118](https://github.com/daniilnahl/Stock-Tracking-App/issues/118) | Independent combined exit audit and operation docs | Closed completed; audit owner-merged with passing PR/main CI | None | `codex/118-m6-exit-audit` | [#125](https://github.com/daniilnahl/Stock-Tracking-App/pull/125), merge `237c4c5f` |

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

#### Owner merge and next service wave

The owner instructed **"pr, merged, continue the work"**. PR #121's final head
`02cc10ac7a51dd073057a5e95d7dc5d85a655311` is owner-merged at
`aa6ecdd34b132ce4e987a7150bf4eae86c7a086e`. Exact-head
[Foundation 38457696127](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38457696127)
and post-merge [main Foundation 38457958438](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38457958438)
passed all five configured checks. Issue #114 is closed completed. No agent merge
was performed. This releases #115 and #116 from the stable accepted contracts.

Both start from merged main `aa6ecdd3`. #115 owns current-data service, pure
numeric parser reuse and external configuration acquisition; #116 owns historical
service and pure range/observation policy reuse. They use separate source/test
helpers and isolated branches. Package test inventory additions may require
mechanical reconciliation when owner merges both; no shared service interfaces
are redesigned in parallel. #117 remains blocked by both reviewed owner merges
and required main CI. Source/wheel service checks do not establish thin CLI or
combined M6 completion.

### Historical service — #116

The isolated branch adds injected HistoryService and a shared pure range/raw-bar
policy, with compatibility wrappers preserving late-bound clocks, acquisition
order and list returns. Exact NASDAQ identity precedes acquisition; each request
carries one resolved UTC date range and sparse numeric raw bars. Authoritative
Stock/PriceBar validators reject malformed typed subclasses. Existing factory/
parser/cache behavior remains unchanged. No root command or renderer integration
is included. The eight-file change has independent technical review **PASS**.

Canonical Python 3.12.10 from that isolated checkout: focused history service,
integration/date-selection/source-boundary/packaging command passed
**143 in 52.04s**; full pytest passed **2364 in 135.21s**. Ruff, configured mypy
(`config.py` only), pip check and staged diff checks passed. Master independently
ran the 62 new history cases: **62 passed in 1.41s**; independent reviewer ran
**140 new/existing history cases**, all passing. Separate source/wheel denial
probes and injected production cache reuse/expiry checks verify this capability.
Staged hygiene, PR creation and hosted CI are recorded once complete below;
owner merge/main CI remain required before #117.

Staged hygiene passed **8 in 8.41s**; staged/final branch diff checks passed.
The clean isolated branch is pushed at `922610fa69db8010495aea123c93382d1113f5a4`;
[PR #122](https://github.com/daniilnahl/Stock-Tracking-App/pull/122) was open at
submission. It is now owner-merged at `a9739dcaefb0a062ae4d1b09081f7773180230f6`.
Exact-head [Foundation 38459708966](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38459708966)
and post-merge [main Foundation 38489030065](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38489030065)
both completed successfully. Issue #116 is closed completed. No agent merge.

### Current-data service — #115

The current-data branch adds injected CurrentDataService, a pure shared decimal
parser with the legacy conversion function re-exported, and an external lazy
configuration-acquisition adapter. Lookup/duplicate/profile/period sequencing,
precise ownership, typed identity checks and per-row progress are retained.
Callbacks publish outside provider-error catches; configuration invalidation
attempts are tracked so a callback exception cannot create duplicate invalidation.
Typed models and complete candidates are revalidated before publication.
Raw market-cap and period values remain numeric for later presentation projection.
No root command wiring, persistence, provider policy or financial rule changes.

The unfinished #115 draft and its recorded prior review were preserved from the
earlier M6 worktree. Continuation uses `codex/115-current-data-service` based on
the owner-merged #116 main, leaving the original draft untouched. Wheel inventory
assertions include both service additions. The following results are from this
continuation in the existing canonical Python 3.12.10 environment:

| Check | Result |
| --- | --- |
| `python -m pytest tests/test_current_data_service.py tests/test_current_service_boundary.py tests/test_packaging.py tests/test_provider_integration.py tests/test_cli_ownership.py tests/test_stock_facade.py -q --tb=short` | **362 passed in 47.47s** |
| `python -m pytest -q --tb=short` | **2474 passed in 113.39s**, combined with merged history service |
| Ruff, configured mypy (`config.py` only), pip check | Passed |
| `python -m pytest tests/test_repository_hygiene.py -q --tb=short` | **8 passed in 8.84s**, task files staged |
| Staged/final diff whitespace checks | Passed |

The preserved draft records prior independent review of the final 109 current
service cases with no actionable findings; this is prior-draft evidence, not a
new independent review of the combined continuation. Cold source/
wheel processes deny UI, configuration, concrete providers/storage, environment,
network, output and deserialization, prove guards and exercise real service use
cases with controlled typed providers. Record publication, callback failure and
raw numeric unit boundaries are tested. Owner merge and required PR/main CI still
gate #117, and combined M6 completion is not claimed.

[PR #123](https://github.com/daniilnahl/Stock-Tracking-App/pull/123) is open from
`codex/115-current-data-service`. Hosted CI is pending at submission. No agent
merge occurred; owner merge and post-merge main verification still gate #117.

### CLI service adapters — #117

The owner instructed **"pr merged, continue the work"**. PR #123 is
owner-merged at `6c38eb9d9b6281d2eeeb2ad89ca50bf4e4b2ef87`; final-head
[Foundation 38489752648](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38489752648)
and post-merge [main Foundation 38491378548](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38491378548)
passed all five configured checks. This releases #117. No agent merge occurred.

Plan: retain root prompts/preflight/save shims; compose existing injected
services lazily; project numeric results at presentation; preserve facade/list
references and aliases; migrate orchestration mocks to provider ports while
retaining assertions; verify source/wheel commands and the full canonical suite.

Both maintained CLI surfaces now delegate local state, views, removal and
current-data orchestration to the approved services. The menu's graph command
uses HistoryService and renders its returned observations without another fetch.
The existing chart renderer is shared by legacy direct callers. A backward-
compatible optional `cache_path` factory argument lets CLI composition bind the
history sidecar once at import while retaining the legacy factory default.
No provider/cache policy, dependency, schema or command set changes.

The existing zero-quantity plus exact `-` cost input conflicted with the
Decimal-only OwnershipInput proposal. The owner explicitly approved None for
that unowned case; ADR-0012 and regression tests now record that narrow amendment.
Numeric zero cost remains owned. Alias compatibility stays outside neutral
services: explicit repeated facade references retain forward removal and observe
earlier refresh publication, while independent equal rows remain distinct.

Initial targeted CLI/provider/history checks passed **265 in 10.95s** (two
unowned cases held until owner approval). The next focused service/ownership/
storage/wheel checks passed **200 in 47.70s**. The initial full run reported
**4 failed, 2481 passed in 113.29s**: four configuration tests still mocked the
old facade/utility operations and correctly hit the network-denial guard. Their
fakes now enter at provider ports with all security/persistence assertions
retained; related configuration/integration checks passed **215 in 5.06s**.
Final canonical verification and PR evidence will be recorded below.

The strengthened historical probe initially denied a direct legacy API check
that the existing audit deliberately executes after its CLI check. Denial now
applies to CLI invocations, retaining the direct API assertions. A new synthetic
fixture's inline Stock key argument also triggered the existing bounded hygiene
scanner; using a named dummy value conforms to the existing fixture convention
without changing scanner rules. Affected source/wheel/history/hygiene checks
then passed **11 in 53.28s**. Final Ruff, configured mypy (`config.py` only),
pip check and staged whitespace checks passed.

Final canonical Python 3.12.10 verification:

| Command | Result |
| --- | --- |
| `python -m pytest -q --tb=short` | **2490 passed in 109.57s** |
| `python -m pytest tests/test_configuration_security.py tests/test_fmp_configuration.py tests/test_cli_service_integration.py tests/test_history_date_selection.py tests/test_current_data_service.py -q --tb=short` | **215 passed in 5.06s** |
| `python -m pytest tests/test_history_exit.py tests/test_packaging.py tests/test_repository_hygiene.py -q --tb=short` | **11 passed in 53.28s**, including staged hygiene and installed-wheel checks |
| `python -m ruff check .` | Passed |
| `python -m mypy` | Passed; `config.py` only |
| `python -m pip check` | Passed |
| Staged/final diff whitespace and scope review | Passed |

The final self-review found no unresolved source findings, unrelated dependency/
toolchain changes, secrets or generated artifacts. Hosted checks, owner review/
merge and post-merge main verification remain required. Independent combined
milestone exit is #118; this change does not claim M6 completion or M7/M8 scope.

### Combined exit audit — #118

The owner merged PR #124 at `926171e34b518bea8d09a322f62482f3d54d56bc` and
instructed continued work, with PR creation through the GitHub website in Codex.
Exact-head Foundation `38494488364` and main `38494501665` completed successfully.
The accepted prerequisites release #118. PR #124's unfilled description template
was reconciled through the website with its implementation, tests, issue link
and actual CI evidence. Its three acceptance items were verified, checked on
the website and issue #117 closed completed. The milestone remains open.

Plan: inspect the combined implementation against every accepted exit; add
bounded architecture checks with controlled violations; execute an independent
fixture across fresh source/wheel processes; preserve exact temporary state and
prove failure guards; publish requirement/operation evidence; run all canonical
checks and create one bounded audit PR. No runtime changes are planned.

`m6_exit_probe.py` now combines actual commands/services/provider parsing,
temporary SQLite namespaces, a separate Portfolio, exact holdings, invalid/
duplicate/abort outcomes, refresh failures and fresh/expired historical cache.
Four phases (write/read/failures/read) execute independently for source and wheel.
Earlier cold denial probes remain the independent UI/configuration/IO service
isolation checks. Bounded AST checks cover ordinary imports and orchestration
calls with positive/negative controls. See [exit evidence](m6-exit-evidence.md)
for the accepted requirement map, fixture arithmetic and limitations.

Focused audit/architecture/wheel checks passed **19 in 55.63s**. Fixture recovery
and actual final canonical results are recorded in the exit evidence; no runtime
behavior or valid assertion was weakened to repair the test harness. Full-suite,
staged hygiene and submission gates were pending at that focused-check snapshot.

Final Python 3.12.10 full pytest passed **2507 in 129.16s**. Ruff, configured mypy
(`config.py` only), pip check and staged hygiene (**8 in 9.27s**) passed. Final
scope/whitespace/secret/generated-artifact review passed. This eight-file change
contains only tests and documentation. GitHub shows #112–117 closed completed;
#118 is the only remaining open milestone issue. Its PR/main CI, owner merge and
completion reconciliation still gate M6 closure. PR creation follows the user's
requested signed-in GitHub website workflow in Codex.

[PR #125](https://github.com/daniilnahl/Stock-Tracking-App/pull/125) was created
through the signed-in GitHub website in Codex with the completed repository PR
template and `Closes #118`. Required hosted CI is pending at submission; owner
review/merge and passing post-merge main CI still gate milestone completion.

## Completion reconciliation — 2026-10-13

The owner merged audit PR #125 at `237c4c5f7d9825c284d706d6730bcdf9ed3510f6`.
Exact-head [Foundation 38496384271](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38496384271)
and post-merge [main Foundation 38500809992](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38500809992)
passed all five configured checks. All seven required issues #112–118 are closed
completed. Earlier open/blocked/pending statements above are dated execution
snapshots, superseded by this completion record. No required runtime work is
deferred. #126 records administrative documentation and the manual CLI showcase;
it introduces no runtime, financial, persistence or public-contract change.

See [exit evidence](m6-exit-evidence.md) and [manual CLI showcase](../CLI_SHOWCASE.md).

Manual showcase: **10 real-provider fresh CLI processes passed**, including add,
credential-free restart/display, duplicate refusal, refresh, real raw historical
charting, removal and final empty display. A separate 13-process controlled
failure demonstration passed. See [CLI showcase](../CLI_SHOWCASE.md)
for the observed data, safe configuration acquisition, exact scope and limitations.
