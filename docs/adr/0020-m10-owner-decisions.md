# ADR-0020: M10 owner decisions of 2026-10-19

## Status and authorization

**Accepted as owner decisions, 2026-10-19.** The owner accepted the resolutions
below for the authority mismatches M-01 through M-07 recorded in the #201
review checklist, and for the open owner decisions that checklist left
unresolved. This record amends the named SRS requirements. It does not
authorize runtime implementation, a PoC execution, a FinRobot import, a
numeric cap, a new ranking metric, or transmission of holdings to a provider.

ADR-0019 remains reserved for
[#192](https://github.com/daniilnahl/Stock-Tracking-App/issues/192)'s
feasibility-isolation record, `docs/adr/0019-m10-feasibility-isolation.md`.
That file is not on main and is not edited here. This decision uses ADR-0020
so it does not take that number or filename.

## Context

SRS §23.10, accepted ADR-0017 and ADR-0018, and the owner's 2026-10-18
FinRobot and no-import policy left seven mismatches open: the local holdings
grant versus the transmission ban, scoped opinion text versus D11 and §4,
price-target text versus AI1004, "stock suggestion of the day" versus
unresolved cadence and ranking, open D9 pricing and in-flight cancellation
charges, run-status words that SRS did not collect into one list, and #197
Phase B versus the later no-import rule. Licensing of evidence and what
counts as a settled run were also still open.

The 2026-10-18 policy in
[m10-finrobot-safety.md](../milestones/m10-finrobot-safety.md) and the #197
charter in
[m10-finrobot-feasibility.md](../milestones/m10-finrobot-feasibility.md)
stay historical records. Where they differ from this ADR, this ADR and the
amended SRS control.

## Decision

### 1. Costs (D9)

Hard per-run and per-day caps are expressed in dollars. The owner sets the
amounts in configuration. This decision states no numeric default.

A run reserves its full estimated maximum cost before any billable call. On
an in-flight cancel, the whole reservation is kept and released only after
the provider's reported usage confirms the real charge.

The zero-cost synthetic mode ships first. Billable providers stay disabled
until the caps are configured.

### 2. Holdings

Agents may read holdings locally. Holdings are never sent to any LLM
provider. The agent-visible projection is tickers and portfolio weights
only, with no quantities, cost basis, or account data.

Portfolio weight means the accepted portfolio-weight figure the application
already computes. This decision defines no new weight formula. X716 stays
as written, because nothing is transmitted. The 2026-10-18 grant that
included quantities and costs is superseded for the agent-visible fields.

### 3. Opinion text

Opinion text is allowed only when labeled "Research opinion, not financial
advice", and only in research output and the stock suggestion of the day.
Verdicts are limited to Buy, Hold, or Avoid plus a reason. No numeric price
targets and no forecasts. AI1004 and the §4 non-goals stay in force. The
labeled text is not financial advice, not machine-learning price prediction,
and not a brokerage action.

### 4. Stock suggestion of the day

One suggestion per day, picked deterministically from the user's watchlist
using existing factual criteria the application already computes. The agent
only writes the explanation. No new ranking metric.

This resolves D7 for this feature only. It does not accept a market
calendar, a new day-boundary rule, a tie-break outside this feature, or any
other open D7 item. The suggestion universe is the user's watchlist. It is
distinct from the ADR-0018 criteria-driven market search in AI1031. An empty
result is not filled with a manufactured suggestion.

### 5. Run status

One canonical list: `pending`, `running`, `completed`, `completed_empty`,
`partial`, `failed`, `cancelled`, `disabled`.

No candidates found is `completed_empty`. Partial text is never a completed
report. `disabled` means the path is not active. SRS AI1015 carries the list.
AI1032 and §23.10.4 use the same words.

### 6. Licensing

Evidence comes only from the user's own FMP and Finnhub data under those
providers' existing terms. Reports are retained locally only. This does not
certify redistribution, publication, or a right to send holdings to a model.

### 7. Settlement

A run counts as settled only when the provider's usage report matches or is
within the reservation. A finished local task or a missing usage payload is
not settled. A usage report outside the reservation does not settle the run
and does not authorize another billable call.

### 8. #197 Phase B

#197 Phase B, which loads FinRobot V2 code, is formally retired in favor of
the #199 no-import rule. Its numeric charter figures are not defaults. This
decision does not adopt any number from that charter as a cap, duration, or
case count. Reopening an import or a code load still requires a new owner
decision.

## Mismatch resolution

| Mismatch | Resolution |
| --- | --- |
| M-01 holdings grant versus transmission ban | Decision 2. Local read of tickers and portfolio weights only. Holdings are never sent to an LLM provider. X716 is unchanged. |
| M-02 scoped opinion versus D11 and §4 | Decision 3. The labeled Buy, Hold, or Avoid text is the accepted boundary. |
| M-03 price-target opinion versus AI1004 | Decision 3. No numeric price targets and no forecasts. |
| M-04 suggestion of the day versus cadence and ranking | Decision 4, for this feature only. |
| M-05 open D9 versus proposed charge rules | Decisions 1 and 7. Configured dollar caps, full reservation until reported usage, and settlement only inside that reservation. |
| M-06 run-status words | Decision 5. |
| M-07 #197 Phase B versus the no-import rule | Decision 8. |

The #201 checklist on #203 still describes these mismatches as open. This
branch does not edit that checklist. A later edit of that file should mark
M-01 through M-07 resolved by this ADR.

## Alternatives

Leaving the mismatches open would keep SRS, the 2026-10-18 policy, and the
#197 charter in conflict. Editing ADR-0019 was rejected because that number
and filename belong to #192. Copying Phase B's numeric charter figures
forward as defaults was rejected by decision 8. Inventing cap amounts, a
sort key, or a day-boundary timezone was rejected because the owner set
those as configured or already-computed behavior.

## Consequences

SRS §4, AI1004, AI1007, AI1008, AI1015, AI1016, AI1019, AI1026, AI1032,
§23.10.4, RSH920, and RSH922 now state these decisions. ADR-0017's
responsibility table remains the 2026-10-17 history, with an addendum that
points here for the suggestion of the day only.

Billable providers cannot be activated until the owner sets the per-run and
per-day dollar caps in configuration. The zero-cost synthetic mode is the
first mode. No runtime, schema, or financial formula changes with this
record.
