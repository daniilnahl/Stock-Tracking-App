# Implementation status and documentation index

Verified 2026-10-18 for [#186](https://github.com/daniilnahl/Stock-Tracking-App/issues/186),
from merged main `6c5a3f9b975ebd2b0230c7a8ccb773de982ecf69`.
This is a delivery assessment, not new approval of proposed requirements.

**M10 offline implementation — 2026-10-19:** the owner accepted ADR-0019 and
authorized pure offline models/validation with sandbox preparation separate.
Codex owns [#207](https://github.com/daniilnahl/Stock-Tracking-App/issues/207),
the exact prepared-criteria parser/hash. Grok's disjoint implementation lane is
[#208](https://github.com/daniilnahl/Stock-Tracking-App/issues/208), resource-profile
validation; [#209](https://github.com/daniilnahl/Stock-Tracking-App/issues/209)
is static Linux readiness preparation. This supersedes the acceptance-pending
wording in the dated paragraphs below. No worker, sandbox/PoC or live/provider/
model/billable activation follows; owner-set execution configuration and reviewed
isolation remain gates.

**M10 contract revision — 2026-10-19:** #204's accepted ADR-0020 decisions and
#203's checklist/review are owner-merged. #192/#202 revises
[proposed ADR-0019](adr/0019-m10-feasibility-isolation.md) against both, including
the restricted holdings projection, accepted D9 policy, canonical statuses and
owner-set limits without inherited numeric defaults. #203's findings describe
the earlier `fcfa164` proposal; they are not verification of this revision.
Closed #201's new-head review continues in Grok's separate
[#205](https://github.com/daniilnahl/Stock-Tracking-App/issues/205). No runtime, PoC,
billable provider or sandbox enforcement is implemented/activated here. Contract
acceptance, explicit configuration and reviewed isolation remain separate gates.

**M10 owner decisions — 2026-10-19:** [ADR-0020](adr/0020-m10-owner-decisions.md)
records the owner's resolutions of mismatches M-01 through M-07. Hard per-run
and per-day dollar caps are configured by the owner and are not given numeric
defaults here. Billable providers stay disabled until those caps are set. The
zero-cost synthetic mode ships first. A run reserves its full estimated
maximum cost before any billable call, keeps that reservation on an in-flight
cancel, and releases it only after the provider's reported usage confirms the
real charge. Settlement requires that usage report to match or fall within
the reservation. Agents may read holdings locally. Holdings are never sent to
any LLM provider. The agent-visible projection is tickers and portfolio
weights only, with no quantities, cost basis, or account data. Opinion text
is allowed only when labeled "Research opinion, not financial advice", and
only in research output and the stock suggestion of the day, as Buy, Hold, or
Avoid plus a reason, with no numeric price targets and no forecasts. The
suggestion of the day is one deterministic watchlist pick per day from
existing factual criteria; the agent writes only the explanation. This
resolves D7 for that feature only and is not implemented. Canonical run
statuses are `pending`, `running`, `completed`, `completed_empty`, `partial`,
`failed`, `cancelled`, and `disabled`. Evidence comes only from the user's
own FMP and Finnhub data under those providers' existing terms. Reports are
retained locally only. #197 Phase B is retired, and its numeric charter
figures are not defaults. Where the 2026-10-18 paragraph below differs, this
decision controls. Nothing in this paragraph is a runtime.

**M10 revised direction — 2026-10-18:** the owner excluded
TauricResearch/TradingAgents and selected FinRobot's agent workflow. The
[revised scope](milestones/m10-plan.md) preserves criteria/evidence, safe bounded
execution, lifecycle/storage, API/dashboard integration and independent audit;
it replaces the former framework blocker with FinRobot-specific #197/#198
review inputs to #192. The tool, credential, egress, and budget map is the
proposal in [m10-finrobot-safety.md](milestones/m10-finrobot-safety.md)
(issue #198). On 2026-10-18 the owner further decided that M10 agents are
built without importing FinRobot code, that opinion text is allowed only for
research output and a stock suggestion of the day, and that agents may see
stored holdings in this single-user local app. Credential limits still apply.
D9 pricing and uncertain in-flight charges stay open in this 2026-10-18
paragraph. ADR-0020 supersedes that open status, the holdings field list, and
the opinion scope where they differ. Those 2026-10-18 sentences are policy
history, not enforcement. M9's editor/EPS remain delivered,
general assessment proposals remain reusable, and no FinRobot runtime/search
is implemented.
The starting-phase records below are historical snapshots superseded by this
framework direction and current issue dependencies.

**M10 starting phase — 2026-10-18:** after owner merge of #187 at
`3b3df5b2f43f1f8df00f88b76714385a865516be` and successful main Foundation
[39151805497](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/39151805497),
the owner requested concurrent issue work for M10. The
[parallel feasibility plan](milestones/m10-plan.md) records three independent
static/offline assessments. Recommended merge order is this plan first, then
the three assessment PRs, which were open on 2026-10-18:
[criteria and candidate evidence #193](https://github.com/daniilnahl/Stock-Tracking-App/pull/193),
[safety, rights and budgets #194](https://github.com/daniilnahl/Stock-Tracking-App/pull/194)
and [TradingAgents feasibility #195](https://github.com/daniilnahl/Stock-Tracking-App/pull/195).
This snapshot does not record their later merges.
[#192](https://github.com/daniilnahl/Stock-Tracking-App/issues/192)'s proposed
feasibility ADR now requires the criteria/general-safety and new FinRobot
findings under the revised dependency table; #195 is no longer required.
Taurus runtime/search remains unavailable; feasibility findings, owner decisions
and accepted implementation contracts are still required. The reconciliation
snapshot below keeps its original #186 context. Issue
[#186](https://github.com/daniilnahl/Stock-Tracking-App/issues/186) closed as
completed on 2026-10-18.

## Is everything implemented?

**No missing runtime requirement was identified within the accepted M0–M8 and
bounded M9 contracts. The entire proposed roadmap is not implemented.**
The accepted M9 scope consists of configurable descriptive criteria, an
inspectable nonexecuting Taurus handoff and the approved upcoming-release EPS
data path. It does not include executing a Taurus search or evaluating arbitrary
financial criteria. [SRS](../SRS.md) and accepted [ADRs](adr/) remain authoritative.

| Capability | Implemented evidence | Limits |
| --- | --- | --- |
| Domain validation and specified financial calculations | `src/stock_tracker/domain/`, domain/financial/snapshot tests; [financial specification](FINANCIAL_CALCULATIONS.md) | Only defined calculations; no invented currency, total-return, risk or EPS-growth conventions |
| FMP current data and observed history | `providers/`, `services/`, current/history/transport tests; [M2](milestones/m2-exit-evidence.md) and [M4](milestones/m4-exit-evidence.md) evidence | Accepted identities and actual provider access apply; no all-market coverage claim |
| SQLite holdings and separate historical cache | `persistence/`, migration/repository/cache tests; [storage guide](PERSISTENCE.md) | Ordered duplicates/namespaces preserved; no application pickle loading; historical cache is not research/run storage |
| CLI workflows | Injected services, maintained Typer apps, CLI/source-wheel tests; [CLI guide](CLI_SHOWCASE.md), [M6 evidence](milestones/m6-exit-evidence.md) | Existing prompts/commands; no installed `stocktracker` command tree or finished personal evaluation method |
| Local authenticated API and packaged dashboard | `api/`, `frontend/src/`, five closed packaged assets; API/hosting and actual source/wheel browser tests; [operations](API_OPERATIONS.md) | Loopback, single-user, no browser holdings mutations; live API/dashboard history still default-disabled behind its separate rights gate |
| Custom stock criteria | `frontend/src/features/criteria.ts` and `StockCriteria.tsx`; unit/component/browser tests; [ADR-0018](adr/0018-custom-criteria-editor.md), merged #177 | Custom range/text/all-any, exact values and immutable prepared preview. Tab memory only; preparation is not a verified match or search |
| Upcoming-release EPS | Finnhub transport/adapter, injected service, configuration, API, budget, launcher and dashboard; EPS tests and source/wheel profiles; [ADR-0015](adr/0015-finnhub-upcoming-eps.md), [ADR-0016](adr/0016-upcoming-eps-api.md) | Explicit symbol/dates and manual read. Default-disabled flag; server-side process key; personal/exclusive-quota assumptions. Exact non-GAAP EPS with unknown currency/share basis/vintage; no comparison/TTM/growth/score |

The prepared version-1 criteria preview is the implemented nonexecuting M10
handoff boundary. An actual Taurus receiver, backend criteria wrapper or durable
file is not required by that accepted contract. The EPS view is separate from
criteria evaluation and does not associate observations with a saved holding.

## Not implemented or not activated

| Feature | Disposition |
| --- | --- |
| Taurus agents, criteria-driven candidate search, and ranked sectors | M10, under [ADR-0017](adr/0017-user-criteria-taurus-discovery.md). No agent/model/tool call or candidate result exists |
| Stock suggestion of the day | Decided in [ADR-0020](adr/0020-m10-owner-decisions.md) for this feature only: one deterministic watchlist pick per day from existing factual criteria; the agent writes only the explanation. Not implemented. No new ranking metric |
| Browser search/add/remove/edit holdings | No accepted write API; CLI editing remains available. [Follow-up checklist](TO-DO-LIST.md) |
| Research persistence, monitoring/change detection, durable jobs, schedules, broad reports and external notifications | Proposed/separately gated work; not approved M9 exit obligations |
| FINVIZ enrichment and additional FMP fundamental/news fields | No verified paid entitlement or implemented new connector/field contract; [dated coverage research](milestones/m9-provider-coverage.md) is not activation |
| Premium multi-quarter EPS consensus, historical vintage/backtesting and calculated EPS comparisons | Outside the selected Free upcoming-release contract; unknown metadata cannot establish comparability |
| Live API/dashboard historical retrieval | Activation remains unverified/disabled by default; controlled success tests and a provider key do not establish rights |
| Hosted/multi-user release, trading, and personalized suitability | Not implemented or approved by the accepted local contracts |
| Directional model opinion text | Allowed by the owner's 2026-10-19 decision only when labeled "Research opinion, not financial advice", and only in research output and the stock suggestion of the day. Verdicts are Buy, Hold, or Avoid plus a reason. No numeric price targets and no forecasts. Not implemented. Not a brokerage action or a new financial calculation. Recorded in [ADR-0020](adr/0020-m10-owner-decisions.md) |

The one previously authorized Finnhub smoke returned one validated observation
through the native transport/service/API. It remains dated technical evidence,
not a new call, perpetual availability guarantee or broad license certification.
No live provider or model request was made for this reconciliation.

## Delivery and administrative state

- Dashboard [#183](https://github.com/daniilnahl/Stock-Tracking-App/pull/183)
  merged at `17bb77f18e5a6d75be19834dee506a19bf89d663`;
  [main Foundation 39150626845](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/39150626845) passed.
- Independent M9 audit [#185](https://github.com/daniilnahl/Stock-Tracking-App/pull/185)
  merged at `6c5a3f9b975ebd2b0230c7a8ccb773de982ecf69`;
  [main Foundation 39150641007](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/39150641007) passed.
- Required M9 delivery/audit issues #164/166/168/170/172/174/176/178/180/182/184
  and #186 are closed. #186 closed as completed on 2026-10-18; it is not an open
  M9 task. No missing runtime task was found
  in the accepted scope by the implementation inspection or independent audit.
- GitHub milestones M0/M2–M6 are closed. M1/M7/M8 remain administratively open
  with zero open issues; their delivered technical scope is distinct from that
  container state. The M9 milestone container remains administratively open with
  no open issues; the #186 reconciliation is closed. No milestone was
  closed by this task, and no full-roadmap completion is claimed.

Prior dashboard-head checks passed 273 frontend, 31 browser, two real source/wheel
and 3178 Python tests. Those are historical delivered-feature evidence, not new
frontend runs for this documentation change. Current reconciliation checks are
recorded below and on its PR; default automated checks use synthetic data and
isolated storage, never real credentials.

## Documentation catalog reconciliation

The audit inventoried all **68 previously tracked Markdown files**, including
the GitHub templates. A document need not be rewritten when its existing
contract remains accurate. Current instructions are updated where shipped
behavior changed; dated findings/results retain their original context.

| Document group | Reconciliation |
| --- | --- |
| Root README/SRS | Current capabilities, scope acceptance versus delivery and current-status entry point |
| API foundation/operations, frontend README/components/Overview/audit, TODO | EPS/criteria/five-route behavior, activation/security/lifecycle limits and future unavailable features |
| TESTING and FINANCIAL_CALCULATIONS | Existing canonical checks and normative formulas preserved; current evidence pointers; no new arithmetic |
| ADR-0005–0014, CLI/storage/cache guides, security record, preview asset notes | Existing contracts/dated records remain applicable; no dependency, data, credential or operating-policy changes |
| ADR-0015–0018 and M9 research/task/plan/decision/audit records | Current merged delivery pointers supersede earlier task-local gates without rewriting historical approval or test results |
| M0–M8 plans/exit evidence and M7–M10 decision report | Dated evidence retained; stale M7/M8 status headers reconciled and current-versus-proposed scope clarified |
| AGENTS and GitHub templates | Governing workflow unchanged; no permissions or definition-of-done weakening |

`eps_impl` reviews/updates frontend and TODO documentation; Master owns the other
documents and canonical checks. `m9_analysis` independently checks completeness
and final consistency against source/tests and accepted scope. Source, tests,
schemas, dependencies, CI and generated assets are unchanged.

## Reconciliation verification

Independent completeness/documentation review passed with no actionable
findings. Using the unchanged Python 3.12.14 environment, task-local TEMP/TMP
and blank provider-key variables:

| Command actually executed | Result |
| --- | --- |
| `python -m pytest -q --tb=short` | 3178 passed, 190.75s |
| `python -m ruff check .` | Passed |
| `python -m mypy` | Passed; configured `config.py` only |
| `python -m pip check` | Passed |
| Staged relative Markdown targets / `git diff --cached --check` | Passed |
| Final staged `pytest tests/test_repository_hygiene.py -q` | 9 passed, 24.67s |

Exact-head CI remains a publication gate. Frontend
build/browser profiles are unnecessary for this documentation-only change;
their prior results remain dated evidence. Native Windows subprocess checks
used approved execution; no system software or dependency pins changed.
