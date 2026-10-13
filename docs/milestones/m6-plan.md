# M6 CLI V2 implementation plan

Status: **IN PROGRESS — contract proposal; service implementation blocked on owner acceptance**.
Snapshot: 2026-10-13 (America/Los_Angeles).
Baseline: `11f7333abdac830e139dd74354c87b30fe4cd45d`, owner-merged M5 audit PR #110.
Parent: [M6 — CLI V2](https://github.com/daniilnahl/Stock-Tracking-App/milestone/7).
Contract: [Proposed ADR-0012](../adr/0012-cli-application-services.md).

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
The missing architectural component is the maintained shared service layer.

Both root interfaces have tested callable compatibility surfaces: `API_KEY`,
`current_watchlist`, `_watchlist_loaded`, `load_watchlist`, `save_watchlist` and
`_prepare_command`. Existing tests/probes protect precise Decimal state, ordered
duplicates, namespace separation, existence-only legacy protection, offline help,
failure/no-save behavior and genuine history. Extraction must preserve these
meaningful guarantees, rather than delete tests because they constrain design.

## Proposed scope and owner decision

Recommended Option A is compatible thinning of both maintained watchlist CLIs:
local state, current-data operations and historical retrieval move to injected,
presentation-independent services; commands retain prompts, input parsing,
rendering and safe error mapping. Correct the established financial headings.
Keep current command names, namespaces, schema, runtime/dependency pins and
configured mypy scope. Service results must preserve numeric financial values
and existing legacy display metadata without promoting display text into domain
values. See the proposed ADR for exact contracts and adapters.

This recommendation is **not yet accepted**. The proposal must be independently
reviewed, explicitly accepted by the owner and owner-merged with required CI
before #114–117 runtime work begins. Alternative installed entrypoint or new
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
| [#112](https://github.com/daniilnahl/Stock-Tracking-App/issues/112) | Propose and approve service/CLI contracts and exit criteria | Proposal independently reviewed | Owner acceptance, owner merge, required CI gate downstream runtime | `m6_readiness` drafts ADR; Master plan; `m6_contract_review` independent review | Proposal submission pending |
| [#113](https://github.com/daniilnahl/Stock-Tracking-App/issues/113) | Correct financial table headings | PR open; local and hosted checks, Master review passed | Owner merge | `m6_terminology`, isolated `fix/113-financial-table-terminology` | [#119](https://github.com/daniilnahl/Stock-Tracking-App/pull/119), reviewed head `9aa7f026` |
| [#114](https://github.com/daniilnahl/Stock-Tracking-App/issues/114) | Local watchlist service boundary | Blocked | Accepted/owner-merged #112 and required CI | Unassigned | — |
| [#115](https://github.com/daniilnahl/Stock-Tracking-App/issues/115) | Current-data orchestration service | Blocked | #112 and complete owner-merged #114 | Unassigned | — |
| [#116](https://github.com/daniilnahl/Stock-Tracking-App/issues/116) | Historical retrieval service | Blocked | #112 and stable owner-merged #114; independent of #115 thereafter | Unassigned | — |
| [#117](https://github.com/daniilnahl/Stock-Tracking-App/issues/117) | Thin adapters for both maintained CLIs | Blocked | Owner-merged #114–116 with required CI | Unassigned | — |
| [#118](https://github.com/daniilnahl/Stock-Tracking-App/issues/118) | Independent combined exit audit and operation docs | Blocked | Approved exit criteria and owner-merged #113–117 | Unassigned | — |

Each issue belongs to GitHub milestone **7**, whose SRS identity is **M6**.
One bounded issue normally owns one branch and PR. #112 uses
`docs/112-cli-service-contracts`; #113 uses an isolated worktree so implementation
and proposal changes do not mix. #115/#116 may run concurrently only after the
shared approved boundary stabilizes; no implementation starts on a blocked issue.

## Proposed exit criteria

Pending owner acceptance, require:

- Both maintained CLI surfaces delegate application orchestration to shared
  services; service use cases do not depend on prompts, terminal/chart rendering,
  provider payload schemas or direct SQL.
- Existing use cases, exact numeric holdings, namespaces, legacy protection,
  safe failure behavior and genuine historical observation rules remain intact.
- Imports and help perform no provider/storage work; source and installed-wheel
  command/restart tests execute actual services with controlled infrastructure.
- Every required issue is closed, implementation PRs are owner-merged, required
  exact PR/main CI passes and an independent requirement/test/exit audit passes.

The SRS supplies the architectural objective; these observable criteria are a
proposal for testing it, not an agent-approved specification extension.

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
generated artifacts. Final staging verification follows the reviewed clarifications.

### Independent terminology task — #113

[PR #119](https://github.com/daniilnahl/Stock-Tracking-App/pull/119) changes two
production headings and adds real rendered/nonmutation coverage with both CLI
flows. Python 3.12.10 targeted checks passed **138 in 9.18s**; full pytest passed
**2249 in 98.41s**. Ruff, configured mypy, pip check and final/staged diff checks
passed. Master independently reviewed all four files and ran the rendered/both-CLI
cases: **58 passed in 3.02s**, no actionable findings. Final head is
`9aa7f0260a2b52185786f045119ed6cc46c010cd`. Exact-head
[Foundation run 38441573466](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38441573466)
completed successfully. Owner merge remains pending; no agent merge occurred.
Its six added cases do not verify future services.
