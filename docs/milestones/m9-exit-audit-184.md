# M9 accepted-scope exit audit — issue #184

## Finding — 2026-10-18

The accepted criteria and EPS contracts have no identified missing runtime
feature. This is a scope/evidence audit, not acceptance of the remaining proposed
SRS, a new financial convention or permission to begin M10. Final M9 exit is
**pending delivery gates**, not declared complete.

The owner requested continuation after reporting the dashboard PR merged.
Both the GitHub connector and direct GitHub REST currently report
[#183](https://github.com/daniilnahl/Stock-Tracking-App/pull/183) **open, unmerged**.
Its reviewed head is `f2097f7bbb397ab1df03936b5bb24f398b7ed47e`; its synthetic
`merge_commit_sha` is not evidence of a completed merge. This audit proceeds
independently, without starting an implementation that depends on that merge.

## Authority and scope

[SRS §23.9.6](../../SRS.md#2396-m9-exit-criteria-proposed) and RSH940 require
validated configurable criteria, a nonexecuting M10 handoff, approved known-stock
data and any **separately approved** watchlist/schedule scope. The controlling
accepted slices are [ADR-0015](../adr/0015-finnhub-upcoming-eps.md),
[ADR-0016](../adr/0016-upcoming-eps-api.md),
[ADR-0017](../adr/0017-user-criteria-taurus-discovery.md) and
[ADR-0018](../adr/0018-custom-criteria-editor.md). PR #183 contains ADR-0016's
stage-3 dashboard record; that record is reviewed but not yet merged at this
audit snapshot. The remaining broader SRS clauses retain their proposed status.

## Requirement-to-evidence map

| Accepted obligation | Implementation and verification evidence | Delivery state |
| --- | --- | --- |
| RSH914/916/921: user-defined criteria, validation and transparent limits | [criteria.ts](../../frontend/src/features/criteria.ts), [StockCriteria.tsx](../../frontend/src/features/StockCriteria.tsx); range/text, explicit units/context, all/any, exact endpoints, 1–20 rows and accessible errors; frontend criteria unit/component/browser tests | #176 / #177 merged; main Foundation 39083592809 passed |
| RSH920/923/925/926: explicit stable nonexecuting handoff; no claim of matches | Immutable version-1 prepared criteria snapshot and inspectable preview; edits label the prior snapshot outdated; tab-memory navigation/reload lifecycle. [ADR-0018](../adr/0018-custom-criteria-editor.md) defines the complete first handoff. No backend receiver, identifier, durable file or agent execution is required for this boundary | Delivered with #177; M10 execution remains unavailable |
| RSH901–905, within the accepted EPS slice: provider isolation and optional-source limits | [Finnhub adapter](../../src/stock_tracker/providers/finnhub.py), separate transport/protocol, additive FMP behavior; [coverage report](m9-provider-coverage.md) defers unlicensed FINVIZ. Existing provider/model/transport tests preserve core behavior | #166 / #167 merged; no claim that all proposed FMP/FINVIZ research fields exist |
| EPS-001–004; RSH906–908/913/917–918 in the approved data slice | Immutable non-GAAP upcoming-release observations; explicit source/field/units and unknown currency/share basis/vintage/end date; unreleased/null/zero/negative handling, exact values, server UTC request context, no financial comparison or completeness claim. Adapter/service/API tests include invalid, ambiguous and mismatched data | #167 / #169 / #179 merged; prior one-request live smoke passed as dated technical evidence only |
| RSH911/929/932/935 within the EPS slice: bounded manual authenticated access and errors | Default-disabled launcher, process-only key, lazy provider, bounded transport, startup/rolling/cooldown budget, one in-flight request, cancellation and safe error categories. [Composition record](m9-eps-composition-180.md); budget/composition/source-wheel tests | #180 / #181 merged at `3af4db73d734453737e956819ef232c4c9197fdd`; main Foundation 39097470838 passed |
| RSH929/934/938–939 within the dashboard slice: exact manual view, no stale publication, outage independence | [Reviewed UpcomingEps.tsx](https://github.com/daniilnahl/Stock-Tracking-App/blob/f2097f7bbb397ab1df03936b5bb24f398b7ed47e/frontend/src/features/UpcomingEps.tsx), shared client and strict schema/context validation. Explicit blank symbol/dates; no autofetch. Cancel/edit/route/session clearing, source/unknown metadata and exact strings; real default-disabled source/wheel UI checks | #182 / #183 reviewed and CI passed; merge and main CI pending |
| RSH924 and preservation of core workflows | Criteria perform no API call or watchlist mutation; EPS uses an independent resource. Existing full suite and source/wheel checks retain ordered rows, holdings digest, history/authentication behavior and absent cache/legacy outputs | Delivered backend/criteria evidence plus reviewed #183 UI evidence |
| RSH940 / §23.9.6: independent exit audit and required issue/CI closure | This report; independent `m9_analysis` inspection found no missing accepted runtime task. AGENTS §10.7 still requires actual required issue closure, passing CI and recorded deferrals | Pending #183 merge/main CI and this audit's verification/review/publication/merge |

The implementation paths above describe approved slices, not full satisfaction
of every broader proposed RSH clause sharing an identifier. No EPS calculation,
price forecast, known-currency equivalence or financial screening qualification
can be inferred from displayed observations or a user parameter label.

## Future scope is not an exit blocker by default

| Capability | Current disposition |
| --- | --- |
| Candidate search, ranked sectors, suggested stock, daily winner | M10 Taurus responsibility under ADR-0017; not an M9 exit requirement. No search is implemented or triggered by preparation |
| Research persistence, durable jobs, schedules, broad reports, watchlist change monitoring, external notifications | RSH912/927–928/930–931/933/936–937 remain proposed or separately gated. None was separately approved as required work in the delivered M9 slices |
| Broad freshness classes, cross-provider comparability, new FMP/FINVIZ fields | Future field/use/identity/quota contracts; accepted EPS and existing current/history policies remain independent. No paid access or scraping is assumed |
| Actual Taurus receiver, model/tools, privacy/cost controls, execution and evidence-backed matches | Separate M10 feasibility and execution contracts. The current exact prepared envelope is sufficient for M9's nonexecuting boundary |
| Undefined financial metrics, sector taxonomy, directional opinions | Need their own normative semantics/approval if requested. They do not require invented defaults to close the accepted M9 slice |

These are explicit scope dispositions, not silent completion or newly assigned
implementation issues. No new optional feature is selected by this audit. Future
work must be decomposed when its scope is accepted; M10 stays coarse for now.

## GitHub delivery snapshot

Before opening #184, milestone 10 contained nine closed engineering/planning
issues and one open implementation issue, #182. #184 is the independent audit
issue, not a replacement for #182. The milestone remains open.

PR #183's [Foundation 39098471335](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/39098471335)
passed all five jobs on its exact reviewed head: Python 3.11/3.12, Ruff,
configured mypy and credential patterns. Its recorded local verification passed
3178 Python, 273 frontend, 31 browser and two actual source/wheel tests, plus
build/package/static/dependency/hygiene checks. Those are prior #183 results,
not checks executed by this documentation-only audit.

Final exit may be recorded only after #183 is actually merged, the resulting
main CI passes, this audit is reviewed/merged and required issues are closed.
Do not close the milestone or begin dependent M10 implementation from this
snapshot. A further runtime wrapper is not the missing step.

## Audit plan and verification

Master owns the report/publication; `m9_analysis` independently inspects scope
and final documentation. Read source/tests and authoritative contracts, inspect
GitHub state, document evidence/deferrals, run canonical Python/static/dependency
and staged hygiene/link/diff checks, then publish one issue-linked audit PR.
No runtime, dependency, schema, credential, provider call or generated asset
changes. Frontend tests/build are not rerun for documentation alone.

The branch starts from verified current main
`3af4db73d734453737e956819ef232c4c9197fdd`, so these checks validate that baseline
plus audit documentation, not unmerged UI. Provider key environment variables
were blank, TEMP/TMP isolated, and the existing Python 3.12.14 environment/pins
were unchanged. Native Windows verification used approved execution.

| Audit-branch command actually executed | Result |
| --- | --- |
| `python -m pytest -q --tb=short` | 3178 passed, 216.57s |
| `python -m ruff check .` | Passed |
| `python -m mypy` | Passed; configured `config.py` boundary |
| `python -m pip check` | Passed |
| Staged relative Markdown links / diff check | Passed |
| Final staged `pytest tests/test_repository_hygiene.py -q` | 9 passed, 25.01s |

Independent final documentation review passed without actionable findings.
Audit exact-head CI remains a publication gate. Neither its success nor this
report would substitute for #183's actual merge/main CI.
