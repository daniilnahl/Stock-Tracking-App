# ADR-0017: M9 user criteria, M10 Taurus stock discovery

## Status and authorization

**Later recorded policy — 2026-10-18:** merged #199 records FinRobot as a design
reference for app-owned agents, with no import/loading/vendoring. Its scoped
opinion and stored-holdings decisions retain credential, external-transmission,
financial and D9 activation gates. The exact M9 criteria envelope and M10
ownership remain unchanged. [Proposed ADR-0019](0019-m10-feasibility-isolation.md)
reconciles this later record; its PoC and interfaces are not accepted here. The
earlier selected-framework wording below is historical and does not authorize
the superseded upstream runtime experiment.

**Framework direction addendum — the owner's decision of 2026-10-18:** the owner
excluded TauricResearch/TradingAgents and selected FinRobot for M10's agent workflow.
This supersedes the earlier unresolved framework selection only. The accepted
M9/M10 responsibility and exact ADR-0018 handoff remain unchanged; generation,
workflow, tools, models, rights, budgets and execution contracts still need review.
See the [revised M10 plan](../milestones/m10-plan.md) and SRS approval record.
The original dated ownership decision below is retained as history.

**Accepted for milestone ownership, 2026-10-17.** The owner explicitly directed
that users should set stock criteria using different parameters, and that Taurus
agents should search for stocks with those parameters in M10 instead of M9
using API calls to find candidates. This is the owner-authorized specification
change recorded in [#174](https://github.com/daniilnahl/Stock-Tracking-App/issues/174).
It supersedes the earlier proposed allocation of screening, sector discovery
and suggested-stock discovery to M9. No duplicate acceptance is required for
this ownership decision. Runtime schemas, financial definitions and agent
integration remain separate contracts, not approved by this record.

## Revised responsibility

| M9 | M10 |
| --- | --- |
| Let the user configure stock-selection criteria across supported parameters, with explicit operators/values and validation. | Taurus agents search for candidate stocks using the user's criteria. |
| Prepare an explicit criteria definition for handoff; preserve the user's choices rather than imposing a hidden preset. | Preserve the exact criteria used for each search; do not silently relax, replace or invent them. |
| Continue permitted data retrieval/display for an explicitly selected stock, including the accepted EPS capability. | Present searched candidates and their source-backed relationship to the criteria, including missing evidence and search limits. |
| Show discovery as unavailable/pending M10; criteria configuration alone produces no winner. | Own the future suggested-stock and sector-discovery results; exact daily cadence, ranking and selection remain unresolved. |

M9 will not call a provider screener, enumerate a market to find matches or run
its own candidate-selection engine. This restriction concerns discovering stocks
from criteria; it does not remove ordinary permitted quote/profile/history/EPS
calls for a known stock. Existing FMP/Finnhub contracts and source priority remain
unchanged. Optional FINVIZ access is neither assumed nor required by this change.

## Criteria and handoff boundaries

The user chooses criteria rather than receiving a fixed agent-selected default.
The owner's subsequent custom-parameter answer and accepted
[ADR-0018](0018-custom-criteria-editor.md) define a first tab-memory descriptive
editor. That scoped contract supersedes the fixed-field-list question below for
the editor only; source-metric evaluation and M10 execution remain separate.
The supported parameter list, field meanings, operators, units, valid ranges,
null handling, combinations, persistence/versioning, API and UI design need a
bounded criteria contract before implementation. No particular metric, default
threshold, score, formula, storage table or generic free-text execution interface
is invented here. Undefined financial metrics still require normative definitions.

M9 validates and prepares criteria without launching agents. It remains usable
when M10 is absent or disabled. A saved/prepared criteria definition is not proof
that matching stocks exist or that any candidate has been evaluated.

The future Taurus search receives the exact criteria snapshot under a reviewed
handoff contract. A claimed match needs appropriate evidence; missing or
incompatible evidence cannot be presented as meeting a criterion. Distinguish
no candidates found from incomplete/failed/disabled search, and never manufacture
a suggestion to populate the UI. Agent opinions and factual matches remain
distinct; no trade execution, suitability claim or guaranteed return is added.

## M10 execution remains gated

"Taurus agents" selects the planned product responsibility, not a proven upstream
framework, package, model, tool set or deployment. Existing M10 feasibility,
isolation, permitted data/model use, privacy, budgets, cancellation and evidence
requirements remain. This instruction authorizes no model/provider call, paid
run, installation, account action, scraping or private-holdings transmission.
Search methods and capability must be verified in separately scoped M10 work.

## Plan and exit consequences

Remove provider-backed candidate screening, ranked sector results and a daily
stock winner from M9's exit criteria and current implementation sequence. M9's
criteria portion instead requires a reviewed supported-parameter contract,
user configuration/validation, inspectable criteria and a tested M10 handoff
boundary that performs no discovery while M10 is unavailable. Other independently
approved M9 data/watchlist capabilities retain their own gates; this does not
accept the entire milestone or complete it.

Keep M10 at a coarse planning level: Taurus criteria-driven candidate discovery
and evidence-backed results now belong there, followed by any separately approved
suggested-stock/daily-selection policy. Preserve the existing unavailable frontend
panels until their respective backends and tests are delivered. This change edits
specification/planning only, not current runtime behavior or financial arithmetic.
