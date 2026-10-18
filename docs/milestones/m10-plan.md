# M10 — FinRobot integration: revised scope and parallel plan

## Current owner decision — 2026-10-18

The owner excluded TauricResearch/TradingAgents, then explicitly selected
[AI4Finance-Foundation/FinRobot](https://github.com/AI4Finance-Foundation/FinRobot)
as the agent workflow. M10 therefore retains agent-enabled research integration;
it is not infrastructure-only and does not substitute an invented agent stack.
Taurus remains the existing product label. The exact FinRobot generation,
revision, entry point, allowed workflow and execution contract still need review.
Framework selection does not accept upstream defaults, new financial formulas,
source/model rights, paid runs or a replacement toolchain.

This supersedes the TradingAgents-specific integration path and its mandatory
dependency on #189/#195. That report remains historical decision evidence;
merging it is not a prerequisite for FinRobot. The earlier assessment-phase
record below is preserved as history, including its original dependency graph,
PR heads and test results; it is not the current execution graph.

## What remains of M10

| Area | Already available / reusable | Remaining bounded work |
| --- | --- | --- |
| Criteria | ADR-0018 tab-memory editor and exact immutable prepared envelope | Revalidate backend handoff; bind snapshot to a run; resolve supported meanings without altering user input. #190/#193 is a reviewed proposal, not an implemented receiver. |
| FinRobot execution | Framework direction selected; preliminary static source review only | Review generation/revision, define isolated adapter and research-only tool subset, then prove a bounded synthetic PoC. No M10 runtime exists yet. |
| Data and discovery | Existing FMP current/history and explicit Finnhub EPS capabilities | Define permitted universe and discovery tools; map identities, dates/units and evidence. Ticker research does not establish criteria-driven discovery. Existing EPS unknowns still prevent unsupported comparisons. |
| Evidence/results | #190/#193 proposed qualification and source-support rules | Implement captured provenance, exact criterion association, candidate prerequisites, missing/conflicting evidence, no-candidate versus incomplete/failed/disabled outcomes and validated reports. |
| Safety/budgets | Existing API access/admission and #191/#194 general assessment | Apply controls to actual FinRobot effects; isolate credentials/files/network, enforce tool and spend/resource bounds, protect private input, sanitize diagnostics and retain uncertain call reservations. |
| Lifecycle/storage | Core SQLite holdings and history cache | Separately reviewed research run/report storage, start/status/cancel/partial/failure behavior, dedup/recovery/retention and user-owned-report rules. Core storage is not an existing research store. |
| API/dashboard | Authenticated local API and packaged dashboard | Add accepted versioned research routes and opt-in composition, then run/candidate/progress/source/cost views in the existing dashboard. Preserve core workflows and disabled-mode independence. |
| Verification/release | Existing deterministic core tests and source/wheel profiles | FinRobot adapter, evidence, injection, budget/cancellation, absent-AI and actual composition checks; independent audit, owner merges and main CI against accepted revised exit criteria. |

TradingAgents installation/pin resolution, graph pruning, memory/auth/checkpoint
adaptation and its component-specific notices are removed from M10 work. Its
four dependency conflicts are not FinRobot findings. Trading, autonomous holdings
changes, upstream valuation/backtest formulas, daily-winner policy, paid sources,
hosted release and unrelated browser holdings mutations are not silently added
by the phrase "everything besides". Their existing separate gates remain.

## FinRobot preliminary review and unresolved fit

Source inspected at commit
[`2717499b8e30f242640af08c4ad9afd1113c2d45`](https://github.com/AI4Finance-Foundation/FinRobot/commit/2717499b8e30f242640af08c4ad9afd1113c2d45).
This is a source-review pin, not an accepted installation/artifact pin.

- FinRobot contains V0 AutoGen, V1 equity and V2 desktop/backend generations.
  Root installation packages V0; do not assume it installs the V2 backend.
  See pinned [root setup](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/setup.py)
  and [V2 manifest](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/pyproject.toml).
- V0 declares Python `>=3.10,<3.12` and incompatible NumPy/Starlette/
  typing_extensions pins; V1 requires NumPy below 2. V2 declares Python `>=3.11`
  and its shared direct FastAPI/Uvicorn/Click/Matplotlib ranges allow the core
  pins. This does not prove transitive resolution or supported-runtime behavior.
  [V0 requirements](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_autogen/requirements.txt),
  [V1 requirements](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_equity/requirements.txt).
- The inspected V2 [SDK](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/sdk.py)
  exposes ticker research/valuation/Q&A/backtesting. It does not establish an
  ADR-0018 receiver or compliant criteria/universe discovery. Its deterministic
  valuation operators are not approved application financial definitions.
- V2 registers broader acquisition/backtest tools and stores settings/artifacts;
  default calls/retries do not establish this app's hard spend/cancellation
  contract. Inspect the [orchestrator](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/orchestrator.py),
  [runner](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/pipelines/runner.py)
  and [executor](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/pipelines/protocols.py).

Recommend reviewing a minimal V2 Python backend subset behind an adapter while
retaining this app's UI/authentication and core pins. This is a proposal; neither
the full desktop/server stack nor a default research pipeline is accepted.
No upstream package, runtime, code, model or provider was executed in this review.

## Current issue ownership and dependency order

| Issue | Exclusive ownership | State / dependencies |
| --- | --- | --- |
| #188 / [#196](https://github.com/daniilnahl/Stock-Tracking-App/pull/196) | Master: plan, SRS, ownership/status pointers and issue metadata | Scope revised in this existing planning PR; owner merge remains separate. Earlier verification below is dated, not this revision's check result. |
| [#197](https://github.com/daniilnahl/Stock-Tracking-App/issues/197) | `docs/milestones/m10-finrobot-feasibility.md` | Ready for bounded static component/adapter review; no unmerged-interface blocker. |
| [#198](https://github.com/daniilnahl/Stock-Tracking-App/issues/198) | `docs/milestones/m10-finrobot-safety.md` | Ready in parallel with #197 against pinned source; verify actual tool/IO/budget surfaces. |
| #190/#193 and #191/#194 | Existing criteria/evidence and general-safety proposal owners | Reuse reviewed findings; owner merges/acceptance remain gates. No duplicate criteria redesign. |
| [#192](https://github.com/daniilnahl/Stock-Tracking-App/issues/192) | `docs/adr/0019-m10-feasibility-isolation.md` and approved minimal links | Define selected FinRobot adapter/PoC contract after #190/#191/#197/#198 required delivery. #189 is removed as a mandatory blocker. |
| #189/#195 | Historical TradingAgents assessment | Excluded framework; optional decision evidence, not required FinRobot delivery. |

Each new issue receives its own branch/worktree/PR when implementation starts.
#197 and #198 may proceed together because both inspect stable source and write
different reports. They must not invent a shared runtime interface independently.

```mermaid
flowchart TD
    selection["FinRobot selected; TradingAgents excluded"] --> source["#197 Component/adapter review"]
    selection --> safety["#198 FinRobot safety applicability"]
    criteria["#190 Criteria/evidence proposal"] --> contract["#192 Proposed FinRobot adapter/PoC contract"]
    general["#191 General safety proposal"] --> contract
    source --> contract
    safety --> contract
    contract --> approval["Owner accepts precise PoC scope and contract"]
    approval --> poc["Bounded synthetic adapter/worker PoC"]
    poc --> stable["Accepted execution and evidence interfaces"]
    stable --> worker["FinRobot adapter"]
    stable --> validation["Criteria/evidence validation"]
    stable --> lifecycle["Budgets and lifecycle/storage"]
    worker --> integration["API/composition then dashboard"]
    validation --> integration
    lifecycle --> integration
    integration --> audit["Independent exit audit and owner merge/main CI"]
```

The remaining M10 goal is an explicitly initiated, bounded FinRobot-backed
criteria search with honest candidate evidence/status, optional approved research
and preserved tracker use when AI is disabled. Exact generation/workflow, supported
universe/metrics, model/pricing/rights, retention and execution limits still need
concrete accepted contracts. No new billable/live run is authorized here.

## Historical initial assessment phase

The following sections record the earlier TradingAgents candidate assessment
phase. The current owner decision and dependency table above supersede its
component selection and blocker graph; historical results are retained.

## Authorization and first delivery

On 2026-10-18 the owner requested starting Milestone 10 in a manner that lets
multiple agents work on different issues concurrently. This starts the bounded
static/offline feasibility and contract assessments below. It does not accept
the remaining proposed production requirements or select a framework from the
Taurus product label. [SRS §23.10](../../SRS.md#milestone-10--ai-research-agents)
and accepted [ADR-0017](../adr/0017-user-criteria-taurus-discovery.md) and
[ADR-0018](../adr/0018-custom-criteria-editor.md) govern the work.

The attached master-agent document supplies a coordination pattern. Its stale
Milestone 2 placeholder is not the requested milestone, and its conditional
approval/merge language does not override AGENTS.md's prohibition on agent
merges. Each issue receives one isolated branch/worktree and one reviewable PR.

Parent: [M10 — AI Research Agents](https://github.com/daniilnahl/Stock-Tracking-App/milestone/11).
GitHub's numeric milestone ID is **11**; milestone **10** is the M9 container.
Planning is [#188](https://github.com/daniilnahl/Stock-Tracking-App/issues/188).

## Verified starting point

All worktrees start at main
`3b3df5b2f43f1f8df00f88b76714385a865516be`, the owner merge of
[#187](https://github.com/daniilnahl/Stock-Tracking-App/pull/187).
[Main Foundation 39151805497](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/39151805497)
completed successfully, verified directly on 2026-10-18. The criteria editor,
upcoming-EPS dashboard and M9 accepted-scope audit are present on this baseline.
The M9 delivery issues #164/166/168/170/172/174/176/178/180/182/184/186 are closed
as completed on the current GitHub snapshot. The M9 milestone container remains
administratively open; that is separate from accepted runtime delivery.

Earlier pending-merge statements in dated M9 records describe their historical
snapshots. They do not authorize broader research or imply current missing
runtime work. [Current implementation status](../CURRENT_STATUS.md) separates
delivered behavior from the proposed roadmap.

## Stable inputs and shared boundaries

Agents consume merged files without changing them:

- AGENTS.md, SRS.md, docs/TESTING.md and relevant accepted ADRs.
- ADR-0018's exact version-1 prepared criteria envelope and
  `frontend/src/features/criteria.ts`, with its existing unit/component/browser
  tests. Preserve ordered duplicate rows, explicit all/any, range/text types,
  decimal strings/null and unit/context. These are descriptions, not metric
  definitions, qualified results or instructions to a model/tool.
- Existing financial definitions and EPS limitations. No new return, EPS,
  threshold, sector, identity, historical cutoff or ranking convention is
  invented to make the assessment appear complete.
- Existing core dependency pins, API/authentication, holdings and tab-memory
  criteria behavior. Existing local API guards are not proof of worker isolation.

Each assessment has a single focused session of at most 45 minutes. At the
boundary, record findings and unknowns rather than expanding scope. Public
primary-source metadata/source review is allowed; no upstream installation or
execution, model/provider request, paid run, scraping, private-data transmission
or credential access is part of the assessment. Recreating the unchanged
canonical application development environment for repository checks is separate
from installing a candidate framework.

## Issue ownership and live status

| Issue | Agent | Exclusive file ownership | Branch | Status / dependency | PR / review |
| --- | --- | --- | --- | --- | --- |
| [#188](https://github.com/daniilnahl/Stock-Tracking-App/issues/188) Parallel plan | Master | This plan; minimal SRS/current-status pointers; GitHub planning metadata | `codex/m10-parallel-feasibility` | Reviewed; no blocker | This planning change; owner merge remains separate |
| [#189](https://github.com/daniilnahl/Stock-Tracking-App/issues/189) Framework feasibility | `m10_framework` | `docs/milestones/m10-framework-feasibility.md` | `codex/189-m10-framework` | Assessment published; owner merge pending | [#195](https://github.com/daniilnahl/Stock-Tracking-App/pull/195); local checks and independent review passed; live CI on PR |
| [#190](https://github.com/daniilnahl/Stock-Tracking-App/issues/190) Criteria/evidence proposal | `m10_contract_review` | `docs/milestones/m10-criteria-evidence.md` | `codex/190-m10-criteria` | Assessment published; owner merge pending | [#193](https://github.com/daniilnahl/Stock-Tracking-App/pull/193); local checks and independent review passed; live CI on PR |
| [#191](https://github.com/daniilnahl/Stock-Tracking-App/issues/191) Safety/rights/budgets | `m10_safety` | `docs/milestones/m10-safety-assessment.md` | `codex/191-m10-safety` | Assessment published; owner merge pending | [#194](https://github.com/daniilnahl/Stock-Tracking-App/pull/194); local checks and independent review passed; live CI on PR |
| [#192](https://github.com/daniilnahl/Stock-Tracking-App/issues/192) Proposed feasibility/isolation ADR | Unassigned until ready | `docs/adr/0019-m10-feasibility-isolation.md`, then approved minimal status links | Assign at start | **Blocked** by #189/#190/#191 owner merges and required CI | Not started |

The three assessment worktrees are separate sibling checkouts outside the
repository source tree, under this chat's task-local workspace. They share a
read-only baseline, not an index or working files. Master owns shared planning
documents and issue metadata; agents do not edit one another's reports or the
plan. A review correction goes back to the owning agent. No agent independently
redesigns the criteria envelope or publishes a new public contract.

## Parallel execution and dependency graph

```mermaid
flowchart TD
    baseline["Merged main + accepted ADR-0017/0018"] --> framework["#189 Framework assessment"]
    baseline --> criteria["#190 Criteria/evidence proposal"]
    baseline --> safety["#191 Safety/rights/budgets"]
    framework --> review["Independent review, checks, owner merges"]
    criteria --> review
    safety --> review
    review --> adr["#192 Proposed feasibility/isolation ADR"]
    adr --> owner["Owner accepts precise PoC scope and contracts"]
    owner --> poc["Bounded isolated PoC"]
    poc --> decision["Reviewed findings and accepted integration ADR"]
    decision --> implementation["New bounded implementation issues"]
    implementation --> integration["API/UI integration, independent exit audit"]
```

#188 coordinates independently and does not block source assessments. #189,
#190 and #191 may run together because none consumes another unmerged output.
They produce proposals rather than executable interfaces. GitHub also records
native blocked-by relationships from #192 to all three assessment issues.
#192 may not start
from an agent's promise or an open PR; its merge/CI blockers are explicit.

After accepted findings stabilize the interfaces, plan independently owned
adapter, criteria/evidence validation and budget/lifecycle implementation issues.
Only then schedule composition, API/UI and independent adversarial/core-fallback
audit. Do not create speculative full-roadmap implementation tasks now. If a
shared interface must change, stop its downstream work until one reviewed
contract is stable. Do not merge PRs on the owner's behalf.

## Review and verification

For each assessment PR, review actual source references and distinguish
inspected facts, proposed design, unverified runtime behavior and owner/vendor
decisions. In particular, source availability is not data transmission rights;
schema-valid criteria are not verified matches; a disabled upstream trader
label is not proof of read-only confinement; citations must support claims.

Use supported Python 3.11/3.12 and unchanged `pip install ".[dev]"` pins.
Run canonical full pytest, Ruff, configured mypy (`config.py` only), pip check,
staged hygiene and changed Markdown target/diff checks before publication.
Serialize heavy Python/browser verification across worktrees; no frontend
build/browser profile is required for these documentation-only changes.
Independent review and exact-head CI are recorded on each PR. Passing checks
do not accept the proposed production contracts or close the milestone.

Executed locally in the unchanged canonical Python 3.12.10 environment: full
pytest passed **3,178 tests in each of the four worktrees** (plan 222.54s,
criteria 210.39s, safety 210.78s, framework 211.66s). Ruff, configured mypy,
pip check, staged hygiene (nine tests per worktree), changed local Markdown
targets and diff checks passed. Verification used task-local temporary state
and blank provider credentials. The Master plan was independently reviewed by
the criteria agent; criteria by the safety agent; safety by the framework
agent; and framework by the criteria agent, including independently fetched
pinned source spot-checks. Master reviewed each assessment. The criteria report
was clarified so that `any` cannot bypass candidate identity/core/mandatory
evidence gates. No remaining actionable review finding was identified. These
are repository regression results, not proof of future AI execution controls.

## Completion and next decision

This first phase is delivered when the three bounded assessments and plan have
reviewed PRs with honest verification and no overlap. Owner merges and #192's
subsequent proposed ADR remain separate gates. Before any upstream PoC, present
the concrete candidate/version, execution environment, permitted actions/data,
hard bounds, stop conditions and unresolved rights/cost/privacy questions for
owner review. No extra approval is requested for the assessments themselves.

M10 remains incomplete until its separately accepted production scope, required
issue closure, owner merges, CI and independent exit criteria are satisfied.
No Taurus search, candidate result, model call or new financial behavior is
delivered by this plan.
