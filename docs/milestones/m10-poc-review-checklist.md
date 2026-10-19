# M10 no-import PoC review checklist — issue #201

**Status: phase-1 review requirements, 2026-10-18. Not an accepted contract,
not a test result, and not a review of issue #192.** This file is the
exclusive document for
[#201](https://github.com/daniilnahl/Stock-Tracking-App/issues/201) in
[M10 — AI Research Agents](https://github.com/daniilnahl/Stock-Tracking-App/milestone/11).
It is the acceptance and negative-control matrix a later review of Codex's
#192 contract will use. It does not author, co-author, or replace
`docs/adr/0019-m10-feasibility-isolation.md`.

Reviewed baseline: `main` at
`02815554e204d36809da62775b22a552fec8a257`
(merge of #199). That is the same commit the issue names. No open pull
request, and no remote `#192` branch, was present when this file was written.
Every row below is therefore **unexecuted**. Nothing here proves a control.

## How to use a row

Each `SA`/`EN`/`FQ`/`IS`/`HP`/`RC`/`ZB`/`PS`/`FB`/`TF`/`AB` heading is one
matrix row. The five fields under it are the requirement, the authority
source, the pass condition, the negative control, and the evidence a reviewer
should expect. Pass conditions describe what the #192 contract must say and
what later tests must be specified to deny. They are not observations that
those tests passed.

Where a numeric ceiling, price, vendor, cadence, rank, or financial metric
would be required, the cell says **owner-set value required**. Accepted
ADR-0018 editor limits are cited only as the criteria envelope. They are not
PoC time, byte, token, or money caps. #197's charter figures are not restated
and are not approved.

Phase 2, after Codex links the #192 pull request, reviews that draft against
these IDs and reports file and line findings, or a bounded pass with
limitations. Phase 2 still does not accept the ADR or close the open gates
below. This revision does not perform phase 2.

## Sources read

| Source | Role in this matrix |
| --- | --- |
| [SRS §23.10](../../SRS.md#milestone-10--ai-research-agents) AI1001–AI1032, [§23.10.4](../../SRS.md#23104-m10-exit-criteria-proposed), [§4](../../SRS.md#4-non-goals-for-initial-development), [X716–X718](../../SRS.md#2371-cross-milestone-requirements-proposed) | Proposed M10 requirements and the permissions/privacy gates they cite. Not amended by this file. |
| [ADR-0017](../adr/0017-user-criteria-taurus-discovery.md), [ADR-0018](../adr/0018-custom-criteria-editor.md) | Accepted ownership and the exact criteria-snapshot envelope. |
| [m10-criteria-evidence.md](m10-criteria-evidence.md) | Merged #190/#193 proposal. |
| [m10-safety-assessment.md](m10-safety-assessment.md) | Merged #191/#194 proposal. |
| [m10-finrobot-feasibility.md](m10-finrobot-feasibility.md) | Merged #197/#200 static component review. |
| [m10-finrobot-safety.md](m10-finrobot-safety.md) | Merged #198/#199 safety map and the owner-policy record from #199. |
| [m10-plan.md](m10-plan.md) §What remains of M10 and §FinRobot preliminary review | Same #199 merge, planning record of the no-import decision. Not edited here. |
| [m7-m10-srs-review.md](m7-m10-srs-review.md) D7, D9, D10, D11 | Decision-register wording. Recommendations there are not owner approval. |
| [FINANCIAL_CALCULATIONS.md](../FINANCIAL_CALCULATIONS.md), [TESTING.md](../TESTING.md) | Financial definitions and the deterministic-test contract. |

`docs/adr/0019-m10-feasibility-isolation.md` is **absent** on the reviewed
commit. SRS §23.10.1 and AI1030 still require an accepted feasibility and
isolation ADR before production integration. Absence at phase 1 is expected.
A later draft is not that acceptance.

## Authority mismatches

These conflicts are recorded and left open. A #192 draft fails the related
row if it picks one source and omits the other, or if it presents a resolution
as already accepted. This file does not amend SRS, ADRs, or the merged reports.

### M-01 — Local holdings grant versus transmission ban

The #199 owner record in
[m10-finrobot-safety.md §Authority](m10-finrobot-safety.md#authority)
allows agents an explicit projection of this application's stored holdings
for this single-user local app, including the quantities and costs those
holdings already contain. The same record excludes API keys, tokens, `.env`
values, keyring entries, and provider secrets, and it says the grant does not
prove that a prompt, log, or provider copy is safe.

[SRS AI1007](../../SRS.md#23102-m10-requirements-proposed) still requires a
documented purpose, a provider-specific opt-in, and an owner-approved
exception to X716 before private holdings, costs, annotations, or account
data are used. General AI enablement is insufficient.
[X716](../../SRS.md#2371-cross-milestone-requirements-proposed) still forbids
private portfolio transmission to LLMs without separate owner approval, and
says that approval does not amend §4 or authorize implementation.
[X718](../../SRS.md#2371-cross-milestone-requirements-proposed) still limits
private holdings to the authorized local application, and excludes public
bundles, diagnostic artifacts, and exports unless a specific approval exists.

The merged #191 assessment still says to exclude holdings, quantities, and
costs, never to serialize a portfolio object into a prompt, and that no X716
exception was sought
([enforcement item 1](m10-safety-assessment.md#proposed-enforcement-boundaries),
[rights table](m10-safety-assessment.md#rights-retention-and-unresolved-decisions)).
That proposal was not rewritten when #199 recorded the later grant.

The later record is the owner policy for a local explicit projection. It does
not say it is the X716 exception for provider transmission. #191's exclusion
is not deleted by this checklist. See HP-01 and AB-05.

### M-02 — Scoped opinion text versus SRS D11 and §4

[SRS AI1019](../../SRS.md#23102-m10-requirements-proposed) still marks D11 as
decision-required and says whether BUY/HOLD/SELL text may be shown remains
blocked. The same sentence says that if display is explicitly approved, the
text is a model research opinion and is never an application instruction, a
deterministic score, a personalized portfolio recommendation, or a guarantee.
X716 and AI1004 still prohibit execution.
[SRS §4](../../SRS.md#4-non-goals-for-initial-development) still lists
financial advice and machine-learning price prediction as non-goals that need
separate requirements and approval. The decision register's D11 row still says
to block opinion behavior pending acceptance
([m7-m10-srs-review.md](m7-m10-srs-review.md#repository-conflicts-and-gaps-requiring-decisions)).

The #199 record allows opinion text only for research output and a stock
suggestion of the day, and says that text is not a brokerage or trading
action and creates no return, cost-basis, valuation, or ranking convention
([m10-finrobot-safety.md §Authority](m10-finrobot-safety.md#authority)).
#191 still says not to publish BUY/HOLD/SELL while D11 is unresolved. #197's
proposed charter still says not to publish opinions or forecasts. Those two
documents predate the #199 answer and were not the instrument that amended
AI1019. SRS was not edited. See FQ-03.

### M-03 — Price-target opinion versus AI1004

AI1004 says specialist risk and technical views cannot introduce undefined
application metrics or price forecasts. The #199 record allows a verdict or
price target only as labeled model opinion in the two M-02 scopes, and #198
says that display does not adopt upstream valuation operators or a new
financial calculation. Neither source defines a forecast metric. A contract
that turns a target into an application price forecast, a qualification
input, or a [FINANCIAL_CALCULATIONS.md](../FINANCIAL_CALCULATIONS.md) value
resolves this by invention. See FQ-04.

### M-04 — "Stock suggestion of the day" versus cadence and ranking

The #199 opinion scope uses the words "stock suggestion of the day."
[ADR-0017](../adr/0017-user-criteria-taurus-discovery.md#revised-responsibility)
still leaves exact daily cadence, ranking, and selection unresolved. Decision
D7 still has no calendar, rank, or tie-break for a stock of the day. The #199
plan record says the opinion allowance sets no ranking formula, cadence, or
financial calculation. The scope name and the unresolved selection policy are
not the same decision. See FQ-05.

### M-05 — D9 pricing and in-flight cancellation charges

[SRS AI1016](../../SRS.md#23102-m10-requirements-proposed) still marks D9 as
decision-required. It requires a worst-case reservation before each call,
blocks a vendor path when pricing or usage is unknown or a cap cannot be
enforced, and says cancellation cannot undo an already authorized billable
request. The decision register recommends the same gate and is explicit that
its recommendations are not owner approval.

The #199 record leaves pricing and the treatment of uncertain in-flight
charges on cancellation **open**, sets no cap, price version, or cancellation
charge rule, and says open D9 gates activation
([m10-finrobot-safety.md §Authority](m10-finrobot-safety.md#authority) and
[§Owner decisions still required](m10-finrobot-safety.md#owner-decisions-still-required)).
#191 proposes a further rule: retain the reservation until settlement or
charge the conservative maximum. The #199 plan sketch also says to retain
uncertain call reservations. Those sentences do not close D9. See RC-03,
RC-04, and AB-02.

### M-06 — Run-status words inside SRS

AI1015 names `pending`, `running`, `completed`, `partial`, `failed`, and
`cancelled`, and says partial text is never a completed report. AI1032 and
§23.10.4 also require `no candidates found` to stay distinct from an
incomplete, failed, or disabled search. SRS does not define one enum that
contains every word. #190 and #191 both record that gap and propose to use
AI1015's `partial` for the unfinished run while keeping `disabled` separate.
Both say that proposal is not an accepted enum. See FQ-06 and PS-07.

### M-07 — #197 import recommendation versus the later no-import rule

#197 recommends an isolated worker that loads selected V2 runner and step
seams, and a Phase B that executes that pinned component
([integration table](m10-finrobot-feasibility.md#integration-alternatives-and-recommendation),
[Phase B](m10-finrobot-feasibility.md#proposed-two-phase-synthetic-poc-charter)).
AI1001 says a spike compares direct integration, a separate worker or
service, and an adapter-only alternative, and recommends only compliant
approaches. The later #199 record forbids loading or importing FinRobot code,
keeps the pin as a reference design, and requires a new owner decision before
that changes. The plan text from the same merge says this supersedes the
earlier V2-import sketch. Vendoring is the same class of change. #197's
per-case durations, dispatch counts, and byte ceilings are unaccepted
proposals and are not copied into the rows below. See SA-01, ZB-04, and ZB-05.

### Noted, not treated as a second schema

ADR-0018 and #190 use different synthetic strings inside the same envelope
shape. Both documents call those strings illustrations, not presets. The
accepted shape is ADR-0018. See EN-01.

## 1. Scope and authority

Latest no-import direction, proposal status, and the boundary around product
choices. Eight rows.

### SA-01

- **Requirement:** M10 agents are specified without importing, loading,
  executing, or vendoring FinRobot code from V0, V1, or V2.
- **Authority:** [m10-finrobot-safety.md §Authority](m10-finrobot-safety.md#authority)
  and [§Prohibited paths](m10-finrobot-safety.md#prohibited-paths); #199 plan
  record in [m10-plan.md](m10-plan.md#what-remains-of-m10). Mismatch M-07.
- **Pass condition:** The contract states that rule for every generation and
  includes no dependency, import, or vendor step.
- **Negative control:** A root install, a V2 install, a vendored tree, an
  `import finrobot`, or an `importlib` load of the pin must fail closed.
- **Evidence expected:** Forbid-language in the draft ADR, and a specified
  static or runtime check that fails when that import or package is present.
  This row does not claim the check exists.

### SA-02

- **Requirement:** The inspected FinRobot commit is a reference design for
  surfaces to avoid. Reopening an import or a vendor copy requires a new
  owner decision. The reference pin is not an installation pin.
- **Authority:** [m10-finrobot-safety.md §Pin and generations inspected](m10-finrobot-safety.md#pin-and-generations-inspected)
  and [§Allowed research subset](m10-finrobot-safety.md#allowed-research-subset)
  items 1–3. Pin recorded there:
  `2717499b8e30f242640af08c4ad9afd1113c2d45`.
- **Pass condition:** The contract cites the pin as reference-only and states
  the new-decision gate. It does not add the pin to this application's
  dependency metadata.
- **Negative control:** "Install the reference pin," "vendor the reference,"
  or a lockfile/hash entry for FinRobot must fail review.
- **Evidence expected:** A reference-only statement next to any citation of
  that commit, and a diff with no FinRobot dependency.

### SA-03

- **Requirement:** TauricResearch/TradingAgents stays excluded. "Taurus" remains
  the product label for criteria-driven discovery. FinRobot is the selected
  framework direction and, under SA-01, is not the imported implementation.
- **Authority:** [ADR-0017 status addendum](../adr/0017-user-criteria-taurus-discovery.md#status-and-authorization);
  SRS approval record and AI1026; #199 owner record.
- **Pass condition:** The contract states all three facts together.
- **Negative control:** A TradingAgents package, graph, or blocker, or a
  sentence that equates the Taurus label with importing FinRobot, must fail
  review.
- **Evidence expected:** Explicit exclusion, product-label, and reference-only
  sentences in the draft scope section.

### SA-04

- **Requirement:** The #192 text is a proposed contract until the owner
  accepts it. Publication, review, or a passing checklist does not accept an
  ADR or authorize a PoC run.
- **Authority:** SRS §23.10.1 and AI1030; #201 scope; ADR-0017
  [§M10 execution remains gated](../adr/0017-user-criteria-taurus-discovery.md#m10-execution-remains-gated).
- **Pass condition:** The draft says it is proposed and that owner acceptance
  precedes execution.
- **Negative control:** "Accepted by this PR," an implementation issue split
  that treats the draft as binding, or a PoC execution step must fail review.
- **Evidence expected:** A status line that remains proposed, with no merge
  or execution instruction aimed at this review.

### SA-05

- **Requirement:** The contract preserves this application's Python version,
  pip-based packaging, and core dependency pins.
- **Authority:** ADR-0005 as cited by #197; SRS DEV-001–DEV-003; AI1002's
  prohibition on an unapproved package manager or Python change; #197
  compatibility section.
- **Pass condition:** No change to those pins or to the toolchain is proposed
  as part of the contract.
- **Negative control:** A second package manager, a Python-version change, or
  a core pin bump justified by FinRobot must fail review.
- **Evidence expected:** An explicit no-change statement and a diff that does
  not edit `pyproject.toml` runtime pins.

### SA-06

- **Requirement:** The contract approves no new financial metric, ranking
  rule, cadence, vendor, model price, or universe. Undefined calculations
  stay undefined.
- **Authority:** ADR-0017 responsibility table; FIN-004 and FIN-005;
  [FINANCIAL_CALCULATIONS.md](../FINANCIAL_CALCULATIONS.md); #199 limit on
  the opinion decision; #190 financial boundary.
- **Pass condition:** Any such choice is either absent or marked unresolved,
  with **owner-set value required** where a number would otherwise appear.
- **Negative control:** An approved threshold, score, rank, schedule, vendor
  price, or upstream DCF/DDM/LBO/multiples formula must fail review.
- **Evidence expected:** A blocked-decisions list. No new formula in the draft.

### SA-07

- **Requirement:** User criteria text, web pages, filings, tool output, and
  model text are data. They are never system instructions, SQL, shell, HTML,
  or permission to fetch a URL or change a tool budget.
- **Authority:** ADR-0018
  [§Representation and interpretation](../adr/0018-custom-criteria-editor.md#representation-and-interpretation);
  AI1009; #190 interpretation section.
- **Pass condition:** The contract keeps privilege checks outside the model
  and outside the criteria strings.
- **Negative control:** A criteria value such as an instruction to ignore
  limits, reveal keys, or open a URL must not change policy, spawn a process,
  or authorize a fetch.
- **Evidence expected:** A specified injection case whose failure is the
  forbidden side effect, not a model refusal string. See TF-05.

### SA-08

- **Requirement:** Controls that #191, #197, or #198 label as proposed stay
  proposed unless a later owner acceptance says otherwise. Merging those
  documents did not create a broker, ledger, or OS denial in this repository.
- **Authority:** #191 status; #198
  [§How to read this document](m10-finrobot-safety.md#how-to-read-this-document)
  and gating gap 10.
- **Pass condition:** The draft distinguishes owner policy, source facts about
  FinRobot, and still-proposed controls.
- **Negative control:** A sentence that the merged assessments already enforce
  a sandbox, or that this checklist proves one, must fail review.
- **Evidence expected:** Status labels on each proposed control. No claim of
  an implemented interceptor.

## 2. ADR-0018 criteria-snapshot envelope

The accepted prepared envelope has exactly this shape. The strings are
ADR-0018's synthetic illustrations, not a preset, a threshold, or a #190
substitute example.

```json
{
  "schema_version": 1,
  "kind": "user_stock_criteria",
  "match": "all",
  "criteria": [
    {
      "parameter": "Custom numeric parameter",
      "kind": "range",
      "unit": "user supplied units and period context",
      "minimum": "-0.25",
      "maximum": "1.250000000000000001"
    },
    {
      "parameter": "Custom text parameter",
      "kind": "text",
      "value": "user supplied requirement"
    }
  ]
}
```

Accepted editor limits, quoted so a review can see them, are not PoC resource
caps: `match` is `all` or `any`; one to 20 rows; decimal grammar
`^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$` with a maximum of 128 characters; names
and unit/context text nonblank and at most 80 characters; text requirements
nonblank and at most 256 characters. Seven rows.

### EN-01

- **Requirement:** A run binds this exact data-only envelope and no second
  criteria schema. #190's different illustration strings are not an alternate
  shape.
- **Authority:** ADR-0018
  [§Representation and interpretation](../adr/0018-custom-criteria-editor.md#representation-and-interpretation);
  #190 §Preserve the accepted input exactly.
- **Pass condition:** The contract copies or cites this shape and rejects any
  added, renamed, or missing field.
- **Negative control:** An extra key, a renamed `kind`, or a second public
  criteria schema must fail admission.
- **Evidence expected:** The shape, or a direct citation of this ADR section,
  plus a rejection case for an unexpected key.

### EN-02

- **Requirement:** Range endpoints stay exact plain decimal strings or null.
  At least one endpoint is present. Bounds are inclusive. Minimum and maximum
  are compared only as exact decimal strings. Signed zero and trailing
  fractional zeros survive.
- **Authority:** ADR-0018 representation section; #190 exact-range and
  signed-zero cases.
- **Pass condition:** The contract requires preservation and exact comparison,
  with no binary floating-point conversion.
- **Negative control:** `+1`, `01`, `1e3`, a numeric JSON number, a 129-digit
  string, both endpoints null, or a float comparison must fail admission or
  fail the preservation check.
- **Evidence expected:** Fixture cases for those inputs. No new numeric
  tolerance. A match distance is **owner-set value required** and is not
  invented here.

### EN-03

- **Requirement:** The contract keeps the accepted 1–20, 80, 256, and 128
  editor limits as envelope validation. It does not reuse them as time, byte,
  token, or money budgets.
- **Authority:** ADR-0018 representation section.
- **Pass condition:** Envelope validation cites those limits. Any PoC ceiling
  is a separate field written as **owner-set value required**.
- **Negative control:** Relaxing an editor limit, or presenting 20 rows or
  256 characters as a run budget, must fail review.
- **Evidence expected:** Two separate statements: envelope validation, and
  unresolved PoC ceilings.

### EN-04

- **Requirement:** `match` is stored as the user's explicit `all` or `any`.
  Preparing or handing off the envelope does not evaluate it.
- **Authority:** ADR-0018; ADR-0017 handoff section; AI1031.
- **Pass condition:** The contract says M9 preparation and the handoff itself
  perform no candidate qualification.
- **Negative control:** A preparation, navigation, or clear action that
  launches a search or rewrites `match` must fail.
- **Evidence expected:** A non-execution statement tied to this field.

### EN-05

- **Requirement:** Row order, duplicate parameter names, and distinct
  unit/context or text values are preserved. Evidence for one row does not
  satisfy another row by label.
- **Authority:** ADR-0018; #190 ordered-duplicates case; AI1031.
- **Pass condition:** The contract binds claims to row ordinals, not to the
  parameter name alone.
- **Negative control:** Trimming, aliasing, merging duplicates, reordering,
  or qualifying both rows from one similarly named fact must fail.
- **Evidence expected:** An ordered-duplicate fixture in the contract's
  verification list.

### EN-06

- **Requirement:** Unknown `schema_version` values are not read as version 1.
  Malformed types and control characters are rejected without dropping or
  rewriting the rest of the payload.
- **Authority:** ADR-0018; #190 §Preserve the accepted input exactly.
- **Pass condition:** The future receiver revalidates independently of the
  editor's draft validator.
- **Negative control:** Version 2 accepted as version 1, or an invalid row
  silently removed, must fail.
- **Evidence expected:** A rejection case for an unknown version and for a
  control character. No new normalization rule.

### EN-07

- **Requirement:** The run binds one immutable snapshot. A later edit marks
  that snapshot outdated and must not be selected in its place. Disabled or
  absent AI does not execute from preparation alone.
- **Authority:** ADR-0018 UI and lifecycle; #190 disabled/stale case; AI1031.
- **Pass condition:** Explicit initiation identifies the current immutable
  snapshot. Reload-cleared editor state is not a hidden store.
- **Negative control:** A run that uses a stale snapshot, an edited draft, or
  preparation alone must fail.
- **Evidence expected:** A stated binding and staleness check. No new
  localStorage, sessionStorage, or SQLite criteria store is approved here.

## 3. Factual qualification and optional opinion

Qualification stays factual. Opinion text, where the owner record allows it,
stays outside that decision. Seven rows.

### FQ-01

- **Requirement:** A claimed criterion match needs captured evidence that is
  compatible in identity, units, time, and support. Missing, conflicting, or
  unverified criteria stay visible.
- **Authority:** AI1032; AI1010; AI1011; ADR-0017 handoff section; #190
  evidence inventory.
- **Pass condition:** The contract withholds a factual match until those
  conditions are met, and it does not invent the missing financial meaning.
- **Negative control:** A match from a ticker string, a keyword, model
  agreement, or an unresolved unit must fail.
- **Evidence expected:** A qualification rule that cites captured evidence,
  plus a case that stays unverified when meaning or evidence is missing.

### FQ-02

- **Requirement:** Opinion text cannot satisfy a row, qualify a candidate,
  or change run completeness.
- **Authority:** #190 outcome inventory ("Opinion text cannot substitute for
  factual qualification"); AI1011; ADR-0017 handoff section.
- **Pass condition:** Factual row state and opinion text are separate fields
  in any proposed result.
- **Negative control:** A verdict or price target that changes an unverified
  row to a supported match must fail.
- **Evidence expected:** A negative case pairing an allowed opinion string
  with missing evidence, and an unchanged non-match.

### FQ-03

- **Requirement:** Opinion text is limited to the two #199 scopes: research
  output, and a stock suggestion of the day. Inside those scopes it is labeled
  model research opinion and is never an application instruction, a
  deterministic score, a personalized portfolio recommendation, a guarantee,
  or a brokerage action. The contract also records M-02 instead of claiming
  that SRS AI1019 or §4 was amended.
- **Authority:** #199 record in
  [m10-finrobot-safety.md §Authority](m10-finrobot-safety.md#authority);
  AI1019; SRS §4; #198 opinion rows. Mismatch M-02.
- **Pass condition:** Both the owner scopes and the AI1019 display constraints
  appear, and M-02 is left open for the owner.
- **Negative control:** Opinion outside those scopes, an unlabeled
  BUY/HOLD/SELL used as an order, or a claim that D11 is closed in SRS, must
  fail review. A draft that forbids the two scopes and omits the #199 record
  also fails review.
- **Evidence expected:** A scoped-opinion section that quotes both
  authorities and does not add a third publication surface.

### FQ-04

- **Requirement:** A verdict or price target may appear only as opinion text
  under FQ-03. It is not an application price forecast, a qualification
  input, or a value defined by the financial specification.
- **Authority:** AI1004; #199 opinion limit; #198 prohibited-path paragraph
  on trade and simulated performance. Mismatch M-03.
- **Pass condition:** The contract records M-03 and stores no forecast metric.
- **Negative control:** Persisting a target as an application calculation, or
  feeding it into a return, valuation, or rank, must fail.
- **Evidence expected:** A statement that upstream DCF and target fields are
  not adopted, with M-03 left unresolved.

### FQ-05

- **Requirement:** Allowing a "stock suggestion of the day" opinion does not
  approve a daily cadence, a ranking, a tie-break, or a winner-selection
  policy.
- **Authority:** ADR-0017; decision D7; #199 plan limit on the opinion
  allowance. Mismatch M-04.
- **Pass condition:** The contract records M-04 and leaves cadence and ranking
  unresolved. Any later number is **owner-set value required**.
- **Negative control:** An approved schedule, rank, or automatic winner must
  fail review.
- **Evidence expected:** An unresolved-selection note next to the opinion
  scope. No calendar rule.

### FQ-06

- **Requirement:** A completed empty search, an unfinished search, a failed
  search, a cancelled search, and a disabled search remain distinguishable.
  The contract does not adopt one status enum as accepted SRS text.
- **Authority:** AI1015; AI1032; §23.10.4; #190 and #191 status notes.
  Mismatch M-06.
- **Pass condition:** The draft lists the distinctions and records M-06.
- **Negative control:** Collapsing those outcomes into one success state, or
  declaring #190's word choice to be the accepted enum, must fail review.
- **Evidence expected:** A status section that keeps every distinction and
  marks any single vocabulary as proposed.

### FQ-07

- **Requirement:** No candidate is manufactured to fill an empty, disabled,
  or failed result. Agent disagreement cannot rewrite the user's criteria.
- **Authority:** ADR-0017 handoff section; AI1032; §23.10.3.
- **Pass condition:** Empty and disabled results render no synthetic winner.
- **Negative control:** A fabricated suggestion, or a criteria mutation after
  disagreement, must fail.
- **Evidence expected:** A specified empty-result case and an unchanged
  snapshot assertion.

## 4. Linux filesystem, egress, and process isolation

Owner platform choice plus the containment a contract must specify. These
rows do not prove an OS mechanism. Ten rows.

### IS-01

- **Requirement:** The agent sandbox is Linux-only. On Windows it runs through
  WSL or Docker. Native Windows sandboxing is not required. The tracker's
  existing Windows behavior stays in place for the core app.
- **Authority:** #199 record repeated in
  [m10-finrobot-safety.md §Authority](m10-finrobot-safety.md#authority)
  and [m10-safety-assessment.md](m10-safety-assessment.md#proposed-enforcement-boundaries).
- **Pass condition:** The contract states that platform rule and does not open
  a native Windows sandbox design.
- **Negative control:** A native Windows enforcement design presented as
  required, or a Linux-only claim that drops WSL/Docker as the Windows path,
  must fail review.
- **Evidence expected:** A platform paragraph with those three sentences.

### IS-02

- **Requirement:** Choosing Linux, WSL, or Docker is not evidence that the
  host filesystem, process, or network is confined.
- **Authority:** #197 authority section; #198 gating gap 4; #191 statement
  that a subprocess alone is insufficient.
- **Pass condition:** The contract requires a later demonstration on the
  supported Linux deployment and treats the OS choice as settled direction
  only.
- **Negative control:** "It runs in Docker" or "WSL is isolated" accepted as
  the confinement proof must fail review.
- **Evidence expected:** A proof obligation that is separate from the
  platform sentence. No mechanism is approved by this checklist.

### IS-03

- **Requirement:** The worker cannot read the user home, `.env`, browser
  profiles, core SQLite, core cache, or `~/.finrobot`, and it cannot inherit
  broad environment variables or open handles.
- **Authority:** AI1002; AI1006; AI1018; #191 enforcement item 2; #198
  prohibited paths and gating gap 4.
- **Pass condition:** The contract denies those paths for the Linux sandbox
  and for WSL/Docker host mounts.
- **Negative control:** A successful read or write of any of those locations
  must fail the future test. An application path-prefix check alone fails
  this row.
- **Evidence expected:** A denial list covering reads and writes, including
  the FinRobot home directory even though SA-01 forbids loading FinRobot.

### IS-04

- **Requirement:** Path traversal and symlink, junction, or reparse escapes
  outside the run root are denied at the OS boundary.
- **Authority:** #191 enforcement item 2; #198 synthetic row for `coding/../../`
  and for foreign `FINROBOT_*` paths.
- **Pass condition:** The contract specifies an OS-level denial, not only a
  string prefix.
- **Negative control:** A traversal or symlink that reaches a file outside the
  run root must fail before the read or write. The original bytes stay
  unchanged.
- **Evidence expected:** A planned escape fixture. This checklist does not
  select the sandbox mechanism.

### IS-05

- **Requirement:** The worker has no shell, no code execution, no pickle or
  arbitrary-object load, no child process, and no dynamic strategy import.
- **Authority:** AI1004; AI1009; #198 tool and code-execution source facts;
  #191 enforcement items 2 and 4.
- **Pass condition:** The contract denies those capabilities in the app-owned
  agent and does not register FinRobot's code, shell, or import tools.
- **Negative control:** An IPython cell, a child process, a pickle load, or a
  `module:Class` import must fail before any effect.
- **Evidence expected:** A deny-before-effect case. Upstream absence of a
  tool is not accepted as the denial.

### IS-06

- **Requirement:** Worker egress is denied by default, including DNS, proxy
  variables, loopback, and subprocess bypasses. Any later allowed host list
  is a separate reviewed broker rule.
- **Authority:** AI1006; #191 enforcement item 3; #198 gating gap 5.
- **Pass condition:** The contract states default deny and does not inherit
  `HTTP_PROXY` or upstream provider chains.
- **Negative control:** A DNS lookup, a proxy hop, or a direct socket from
  the worker must fail. No host is implied by this row.
- **Evidence expected:** A network-denial case. No permitted host is selected
  here, and none is implied before the rights gate in AB-03.

### IS-07

- **Requirement:** URLs found in criteria, evidence, or model output are not
  fetches. Redirects, URL userinfo, and loopback, private, link-local, or
  metadata destinations are refused before connection.
- **Authority:** AI1009; #191 enforcement item 3; #190 injection example.
- **Pass condition:** The contract keeps destination checks in trusted code.
- **Negative control:** An encoded, redirecting, or credential-bearing URL
  that connects must fail the case.
- **Evidence expected:** A broker or adapter refusal case that observes no
  connection. A model refusal string is not the evidence.

### IS-08

- **Requirement:** Upstream default tools and stores stay out of the contract's
  allowed set. That includes web search, yfinance, EDGAR-through-FinRobot,
  Adanos, Alpha Vantage, social or news downloaders, the lead-agent tool
  list, valuation and backtest tools, the secret store, and the upstream
  server.
- **Authority:** #198 allow/deny map and
  [§Allowed research subset](m10-finrobot-safety.md#allowed-research-subset)
  items 4–5; #197 callable-seams table.
- **Pass condition:** The contract's tool list is closed and app-owned, and
  it does not register those surfaces.
- **Negative control:** A model-selected call that opens one of those hosts
  or tools must fail before the call.
- **Evidence expected:** An explicit deny list mapped to the pinned surfaces.
  An empty allowlist is compliant. A named research tool needs a separate
  acceptance and is not created here.

### IS-09

- **Requirement:** Brokerage, order routing, simulated trading, and core-data
  mutation are disabled. If a path cannot be constrained to research-only,
  it is not shippable.
- **Authority:** AI1004; X716; SRS §4; #198 prohibited paths for trade and
  simulated performance.
- **Pass condition:** The contract has no order tool and does not publish
  backtest statistics as application results.
- **Negative control:** An order-shaped action, a BackTrader-style run, or a
  write to core holdings must fail before the effect.
- **Evidence expected:** A denied trading case and an unchanged core-database
  assertion.

### IS-10

- **Requirement:** Research scratch uses a distinct bounded directory. It does
  not overwrite user tables, and user reports are not treated as disposable
  cache. Upstream `~/.finrobot` paths are not the product store.
- **Authority:** AI1018; #191 publication item 6; #198 artifact source facts.
- **Pass condition:** The contract separates run scratch from core SQLite and
  from the FinRobot home directory.
- **Negative control:** A write into the holdings database, the history cache,
  or `~/.finrobot` must fail.
- **Evidence expected:** A path assertion after a fixture run. Retention
  lifetime is **owner-set value required**.

## 5. Holdings projection and secret exclusion

Latest owner policy allows one explicit local projection and excludes
secrets. It does not approve provider transmission. Seven rows.

### HP-01

- **Requirement:** The contract records both sides of M-01: the #199 grant of
  an explicit projection of stored holdings, and the still-unamended AI1007,
  X716, and #191 exclusion language. It does not silently drop either side.
- **Authority:** #199 holdings row; AI1007; X716; #191 enforcement item 1.
  Mismatch M-01.
- **Pass condition:** The draft quotes the grant and the transmission gate as
  different decisions.
- **Negative control:** A draft that only says "exclude all holdings," or
  only says "send holdings to the model," without M-01, must fail review.
- **Evidence expected:** A holdings section that contains both statements and
  leaves transmission blocked. See AB-05.

### HP-02

- **Requirement:** The projection is an explicit field list of stored holding
  data. It is not a mount of the home directory and not a serialization of a
  Stock, watchlist, or portfolio object.
- **Authority:** #198 allowed-research item 8; #191's still-proposed object
  ban, which remains relevant to the shape of the projection even though M-01
  is open on whether holdings are visible at all.
- **Pass condition:** The contract describes a field projection and forbids
  a home mount and a whole-object dump.
- **Negative control:** A mount of the user home, or a prompt that contains a
  serialized portfolio object, must fail.
- **Evidence expected:** A named projection boundary. The exact field list,
  beyond "stored holdings, including quantities and costs already stored," is
  not expanded into new attributes by this checklist.

### HP-03

- **Requirement:** Quantities and costs already present on stored holdings are
  inside the #199 grant's stated scope. The projection does not compute market
  value, weight, return, or any other undefined metric.
- **Authority:** #198 prohibited-paths private-data paragraph; FIN-004;
  FINANCIAL_CALCULATIONS.md. Mismatch M-01 remains open for transmission.
- **Pass condition:** The contract limits the projection to stored fields and
  cites the financial specification for anything calculated.
- **Negative control:** A derived valuation, weight, or return added to the
  projection must fail review.
- **Evidence expected:** A field boundary statement with no new formula.

### HP-04

- **Requirement:** API keys, tokens, `.env` values, keyring entries, provider
  secrets, FinRobot secret files, and this application's API bearer are
  outside the projection and outside prompts, logs, and provider payloads.
- **Authority:** #199 holdings limit; AI1006; X718; #198 prohibited paths.
- **Pass condition:** The contract excludes those classes by name.
- **Negative control:** Any of those values appearing in the projection,
  prompt, log, export, or provider payload must fail. A redaction regex is
  not a pass by itself.
- **Evidence expected:** A synthetic-secret fixture that asserts absence in
  each of those channels. No real secret is used.

### HP-05

- **Requirement:** A secret typed into criteria text, or placed beside a
  holding, is not disclosed by the holdings grant. Criteria text remains data.
- **Authority:** #198 synthetic matrix rows for criteria secrets; ADR-0018;
  #191 admission note that free-text criteria can contain private data.
- **Pass condition:** The contract refuses to treat criteria text as part of
  the holdings projection and does not silently rewrite the snapshot to hide
  it.
- **Negative control:** The secret string appearing in the prompt, log, or
  provider payload must fail, and the stored snapshot must stay exact.
- **Evidence expected:** A criteria-text secret case with an unchanged
  envelope and an absent secret in outputs.

### HP-06

- **Requirement:** Building or discarding a projection does not mutate stored
  holding bytes.
- **Authority:** AI1004; AI1021; #198 holdings synthetic row.
- **Pass condition:** The contract requires a byte-level unchanged assertion
  on the holdings store.
- **Negative control:** Any write to stored holdings during projection,
  research, cancel, or failure must fail.
- **Evidence expected:** A before-and-after comparison on a temporary
  synthetic database.

### HP-07

- **Requirement:** Local permission to project holdings is not permission to
  place holdings in a prompt that leaves the machine, a provider payload, a
  log, or an export.
- **Authority:** X716; X718; AI1007; #199 sentence that the grant does not
  prove a prompt, log, or provider copy is safe. Mismatch M-01.
- **Pass condition:** The contract keeps local projection and outbound
  transmission as separate gates, with transmission still blocked.
- **Negative control:** A provider payload that contains holdings, justified
  only by the local grant, must fail review.
- **Evidence expected:** Two labeled gates. See AB-05.

## 6. Resource limits and cancellation

Bounds and cancellation stay gated. No numeric default is created. Eight rows.

### RC-01

- **Requirement:** Hard bounds on time, requests, tokens, cost, storage, and
  concurrency are required before any billable path can activate. This
  checklist sets none of those numbers.
- **Authority:** AI1016; AI1005; #191 budget table; #198 gating gap 2.
- **Pass condition:** Every ceiling in the draft is either absent or written
  as **owner-set value required**, and activation stays blocked until the
  owner sets it.
- **Negative control:** A concrete cap, timeout, token count, byte limit, or
  concurrency number presented as approved must fail review.
- **Evidence expected:** The phrase **owner-set value required** wherever a
  ceiling would otherwise be filled in.

### RC-02

- **Requirement:** Unknown price, unknown currency, unknown hidden usage, or
  an unenforceable maximum produces zero dispatches on that path.
- **Authority:** AI1016; #191 cost and token rows; #198 reservation section.
- **Pass condition:** The contract refuses the call before any network effect
  when those inputs are unknown.
- **Negative control:** A dispatch under an unknown price or an unknown
  tokenizer must fail.
- **Evidence expected:** A zero-dispatch case for unknown pricing. This is a
  refusal rule, not a price of zero and not a closed D9.

### RC-03

- **Requirement:** D9 stays open. The contract does not activate a paid or
  live vendor path and does not mark D9 resolved.
- **Authority:** #199 costs row; AI1016 decision marker; #198
  [§Owner decisions still required](m10-finrobot-safety.md#owner-decisions-still-required).
  Mismatch M-05.
- **Pass condition:** The draft records D9 as an activation blocker and
  records M-05.
- **Negative control:** "D9 resolved," a selected vendor price, or an
  authorized paid run must fail review.
- **Evidence expected:** An open-gate statement. No price table.

### RC-04

- **Requirement:** The treatment of an uncertain in-flight charge after
  cancellation is undecided. The contract must not adopt #191's "charge the
  conservative maximum," the plan sketch's "retain the reservation," or a
  release-on-cancel rule as the owner's decision.
- **Authority:** #199 costs row; AI1016's statement that cancellation cannot
  undo an authorized billable request; #191 cancellation paragraph. Mismatch
  M-05.
- **Pass condition:** The draft leaves the charge rule undecided and still
  honors the AI1016 statement that cancellation is not itself a refund.
- **Negative control:** A chosen settlement or refund rule presented as
  accepted must fail review.
- **Evidence expected:** An explicit open item for the in-flight charge. No
  numeric reserve.

### RC-05

- **Requirement:** Cancellation stops future dispatch. Work that is known to
  be unsent is not sent. No queued task starts after cancellation.
- **Authority:** AI1015; AI1016; #191 cancellation paragraph; #198
  cancellation source facts.
- **Pass condition:** The contract states those three outcomes without
  choosing the open charge rule in RC-04.
- **Negative control:** A dispatch after cancel, or a send of work already
  known to be unsent, must fail.
- **Evidence expected:** Before-send and after-cancel cases. The during-send
  money outcome stays under RC-04.

### RC-06

- **Requirement:** Closing a stream, disconnecting a UI, killing a worker, or
  marking a local row cancelled does not prove that a remote provider stopped
  or that a charge was reversed.
- **Authority:** AI1016; #198 cancellation source facts; #191 cancellation
  paragraph.
- **Pass condition:** The contract says local cancellation is not remote
  settlement.
- **Negative control:** A test or contract clause that clears a reservation
  because the client disconnected must fail review.
- **Evidence expected:** A disconnect case that leaves the open D9 question
  untouched. See AB-04.

### RC-07

- **Requirement:** Crash recovery does not automatically replay a call that
  may have been sent, does not release the same reservation twice, and does
  not reset the authorized ceiling.
- **Authority:** #191 recovery paragraph; #198 synthetic crash row; AI1021.
- **Pass condition:** The contract states those prohibitions. The ceiling
  value itself remains **owner-set value required**.
- **Negative control:** Automatic replay, a double release, or a cap reset
  must fail.
- **Evidence expected:** A crash-between-reserve-and-settlement case
  specified with a fake endpoint. Not executed by this checklist.

### RC-08

- **Requirement:** FinRobot's process-local rate buckets, semaphore, retry
  counts, and HTTP timeouts are source facts about the pin. They are not this
  application's caps. SDK and CLI paths that skip those buckets are not a
  budget.
- **Authority:** #198 model-calls section and the HTTP-buckets row of the
  allow/deny map.
- **Pass condition:** The contract cites those figures only as upstream
  behavior that is not adopted.
- **Negative control:** Copying an upstream bucket, retry count, or timeout
  in as an approved app limit must fail review.
- **Evidence expected:** A non-adoption sentence. No restated upstream number
  used as a ceiling.

## 7. Zero-billable synthetic mode

A fixture mode may exercise mechanics only while it cannot create a billable
charge. Six rows.

### ZB-01

- **Requirement:** Synthetic mode performs zero billable model or provider
  dispatches. It uses fixture data and fake ports only.
- **Authority:** AI1005; AI1016; #198 synthetic-matrix introduction; #197
  Phase A description of fixture-only ports, which matches this direction
  and does not supply approved numbers.
- **Pass condition:** The contract defines the mode as mechanically
  non-billable and refuses a real endpoint inside it.
- **Negative control:** Any real model or provider HTTP call, including a
  call to a host the tester hopes is free, must fail the run.
- **Evidence expected:** A fake-port design and a denied-network assertion.
  "Price equals zero" is not a substitute and is not set here.

### ZB-02

- **Requirement:** Synthetic fixtures use fixed synthetic credentials,
  synthetic holdings, and temporary state. They do not read live keys, real
  holdings, or account data.
- **Authority:** TESTING.md determinism rules; AI1024; X719; #198 matrix
  introduction.
- **Pass condition:** The contract's synthetic charter forbids live material.
- **Negative control:** A real key, a real database, or a live account
  response in the fixture set must fail review.
- **Evidence expected:** A fixture description that names synthetic inputs
  only. No secret value appears in the draft.

### ZB-03

- **Requirement:** A passing synthetic run does not activate a vendor, close
  D9, or count as a passed production budget test.
- **Authority:** #198 statement that repository tests do not prove the
  matrix; #197 statement that Phase A proves mechanics only; AI1030.
- **Pass condition:** The contract labels synthetic results as mechanics
  evidence and leaves activation blocked.
- **Negative control:** "Synthetic pass authorizes the provider" must fail
  review.
- **Evidence expected:** A limitations sentence next to the synthetic charter.

### ZB-04

- **Requirement:** #197 Phase B, which loads pinned V2 code, is outside the
  authorized synthetic mode. Phase A's no-import direction is the only part
  of that charter consistent with the later owner rule, and even that part
  stays proposed until the owner accepts a contract.
- **Authority:** #199 no-import record; #197 Phase A and Phase B. Mismatch
  M-07.
- **Pass condition:** The draft follows SA-01 and records M-07. It does not
  schedule an import experiment.
- **Negative control:** A Phase B execution step, or an "unavoidable import"
  allowlist, must fail review unless a newer owner decision is cited. None
  is cited on this baseline.
- **Evidence expected:** A no-import synthetic scope and an explicit
  rejection of Phase B.

### ZB-05

- **Requirement:** #197's per-case durations, dispatch counts, byte ceilings,
  case counts, and worker counts are unaccepted proposals. The contract does
  not adopt them.
- **Authority:** #197 proposed charter; #201 instruction that checklist
  entries are not new approved numeric defaults. Mismatch M-07.
- **Pass condition:** Those figures are absent or marked unaccepted. Any
  replacement is **owner-set value required**.
- **Negative control:** Restating those figures as the approved synthetic
  bounds must fail review.
- **Evidence expected:** No approved numeric charter. A pointer that the
  figures remain #197 proposals.

### ZB-06

- **Requirement:** An unexpected import, network attempt, credential read,
  criteria mutation, or unbounded chargeable path stops the synthetic run.
  The run is not rescued by widening the allowlist or installing a provider.
- **Authority:** #197 stop list, as a proposed control that matches SA-01,
  IS-06, and HP-04; AI1021.
- **Pass condition:** The contract includes stop-and-do-not-widen behavior
  and still labels the surrounding charter proposed.
- **Negative control:** Continuing after a forbidden effect, or enabling a
  provider to make the case pass, must fail.
- **Evidence expected:** A stop condition for each of those effects. Not a
  claim that a run was stopped.

## 8. Provenance and status reporting

Claims stay tied to captured evidence, and statuses stay distinct. Eight rows.

### PS-01

- **Requirement:** Every source-dependent claim cites real captured evidence
  with a sanitized provider URL or ID, an effective time, and a retrieval
  time.
- **Authority:** AI1010; X713; #190 source-support and time rows.
- **Pass condition:** The contract requires those elements before publication
  of a factual claim.
- **Negative control:** A claim with a missing capture, a credential-bearing
  URL, or a manufactured timestamp must be withheld.
- **Evidence expected:** A provenance field list marked proposed, not a new
  accepted public schema. See PS-08.

### PS-02

- **Requirement:** A citation must support the particular claim. A real
  reference to an unrelated passage is not support. Reference existence alone
  is not proof.
- **Authority:** AI1010; #190 unsupported-citation case; decision-register
  note that citations must exist and support claims.
- **Pass condition:** The contract validates support separately from
  identifier existence.
- **Negative control:** Qualification from a mismatched passage, period, or
  identity must fail.
- **Evidence expected:** A forged-citation case and a real-but-irrelevant
  citation case, both withheld.

### PS-03

- **Requirement:** Unsupported factual claims are withheld from published
  results. Only sanitized validation failures or partial-run diagnostics may
  be retained.
- **Authority:** AI1010; AI1011; #191 publication item 5.
- **Pass condition:** The contract states the withhold rule and the
  sanitized-diagnostic limit.
- **Negative control:** Publishing the unsupported fact, or retaining the raw
  prompt as the diagnostic, must fail.
- **Evidence expected:** An output example that shows the gap and omits the
  unsupported sentence. Diagnostic retention lifetime is **owner-set value
  required**.

### PS-04

- **Requirement:** Requested cutoff, effective period, source publication or
  vintage when known, and UTC retrieval time stay distinct. Receipt is not
  publication. Unknown vintage blocks an as-of or backtest claim.
- **Authority:** AI1020; DATA-007; #190 cutoff case.
- **Pass condition:** The contract keeps those times separate and withholds
  historical qualification when vintage is unknown.
- **Negative control:** Using retrieval time as publication time, or claiming
  a backtest from current data, must fail.
- **Evidence expected:** A fixed-clock cutoff fixture. No market-timezone
  inference is approved here.

### PS-05

- **Requirement:** Status records may contain non-secret identifiers, safe
  categories, approved settings identifiers, durations, and counters. They
  contain no chain-of-thought, raw prompts, request headers, token-bearing
  URLs, or secret excerpts.
- **Authority:** AI1017; X718; X721; #191 diagnostics sentence.
- **Pass condition:** The contract limits status content to that safe set.
- **Negative control:** Chain-of-thought, a raw prompt, or a secret in the
  status record must fail.
- **Evidence expected:** A log-redaction case using synthetic secrets. No
  indefinite memory retention is approved.

### PS-06

- **Requirement:** Partial text is never stored or labeled as a completed
  report. A completed report is published only after the contract's mandatory
  gates pass.
- **Authority:** AI1015; AI1013; #191 publication item 6.
- **Pass condition:** The contract separates partial artifacts from completed
  reports.
- **Negative control:** Partial narrative labeled completed, or a completed
  publication after a failed gate, must fail.
- **Evidence expected:** A partial-output fixture with a non-completed status.
  The report object remains a proposal. See PS-08.

### PS-07

- **Requirement:** `no candidates found` is available only for a completed
  search inside an explicit bounded scope. It is not the label for a disabled,
  failed, cancelled, or unfinished run.
- **Authority:** AI1032; §23.10.4; #190 outcome table. Mismatch M-06.
- **Pass condition:** The contract keeps that distinction and records M-06
  rather than choosing the unresolved word `incomplete` or `partial` as
  accepted SRS.
- **Negative control:** An empty-success label on a disabled, failed,
  cancelled, or unfinished run must fail.
- **Evidence expected:** One case per outcome, with different observable
  statuses, and an open note on the enum words.

### PS-08

- **Requirement:** AI1013's versioned report contents are review targets.
  This checklist accepts no public report, API, or storage schema.
- **Authority:** AI1013; AI1023; #190 statement that transport and lifecycle
  enums remain a separate contract; #201 out of scope.
- **Pass condition:** Any schema in the draft is marked proposed and is not
  implemented.
- **Negative control:** An accepted public schema, a new route, or a core
  migration presented as part of this review must fail review.
- **Evidence expected:** Proposed-only labeling and a diff with no API or
  migration code.

## 9. Core-app fallback

The tracker remains usable when agents are off or fail. Six rows.

### FB-01

- **Requirement:** CLI, local API, dashboard, M9 criteria editing, and
  holdings remain usable when AI is absent, disabled, offline, limited,
  incompatible, or invalid.
- **Authority:** AI1014; AI1025; AI1029; §23.10.4; #198 local API section.
- **Pass condition:** The contract lists those surfaces and requires them to
  work in each of those AI states.
- **Negative control:** A core surface that errors because the optional agent
  is missing or failing must fail the fallback test.
- **Evidence expected:** A matrix cell per surface and per disabled state.
  Not executed here.

### FB-02

- **Requirement:** The agent capability is disabled by default and starts
  only from explicit user enablement or initiation. There is no silent paid
  run.
- **Authority:** AI1005; AI1029; X722; #191 admission item 1.
- **Pass condition:** The contract states the default and the explicit
  initiation rule.
- **Negative control:** A default-on flag, or a run that starts from
  preparation or application startup, must fail.
- **Evidence expected:** A default-disabled statement and a startup case with
  zero dispatches.

### FB-03

- **Requirement:** Core import paths do not import FinRobot and do not
  acquire model or provider credentials for an agent.
- **Authority:** AI1025; SA-01; #198 final synthetic row; existing cold-import
  practice cited by TESTING.md.
- **Pass condition:** The contract requires the core CLI, API, and dashboard
  imports to succeed with the agent package absent.
- **Negative control:** An import of FinRobot, or a credential read, on a
  core path must fail.
- **Evidence expected:** A specified cold-import check. Current repository
  tests are not that check. See TF-06.

### FB-04

- **Requirement:** Sanitized agent failures, timeouts, duplicate jobs, and
  exhausted budgets do not corrupt holdings, watchlists, M9 state, or API
  data, and they do not retry without a bound.
- **Authority:** AI1021; AI1025; #191 failure rows.
- **Pass condition:** The contract requires unchanged core bytes after those
  failures. Any retry bound is **owner-set value required**.
- **Negative control:** A core write, or an unbounded retry, after a failure
  must fail.
- **Evidence expected:** Failure fixtures with byte comparisons. No infinite
  loop is authorized.

### FB-05

- **Requirement:** Disabling or uninstalling the optional agent leaves
  holdings intact and does not change core dependency pins or delete user
  data as a side effect.
- **Authority:** AI1029; #191 publication item 6; PERS-005.
- **Pass condition:** The contract states that disablement is non-destructive
  for holdings and core pins.
- **Negative control:** A disable path that deletes holdings, deletes user
  reports, or edits core pins must fail.
- **Evidence expected:** A disable case with unchanged holdings bytes and
  unchanged pin metadata. Report-deletion policy is not decided here.

### FB-06

- **Requirement:** Preparing, editing, navigating, or clearing criteria
  performs no agent call and no network operation. A prepared snapshot is not
  an attempted search.
- **Authority:** ADR-0018 UI and lifecycle; ADR-0017; #190 disabled outcome;
  AI1032.
- **Pass condition:** The contract preserves that non-execution boundary.
- **Negative control:** A fetch, provider call, or agent start from those
  editor actions must fail.
- **Evidence expected:** A no-request assertion on the editor actions. The
  existing editor tests are evidence of the editor, not of a future agent.

## 10. Deterministic test fixtures

The future matrix #192 specifies must be deterministic. These rows do not
add tests. Six rows.

### TF-01

- **Requirement:** Time-dependent cases use a fixed injected clock. They do
  not read the current date, the current market session, or an unpatched
  wall clock to decide a deadline.
- **Authority:** TESTING.md determinism rules; AGENTS.md determinism rules;
  X719; #190 and #191 verification introductions.
- **Pass condition:** The contract's test plan says how the clock is fixed.
- **Negative control:** A case that passes only because today's market is
  open or closed must fail review. A wall-clock change that extends a run
  must fail the future test.
- **Evidence expected:** Named fixed timestamps in the planned fixtures. No
  live clock.

### TF-02

- **Requirement:** Persistence cases use an isolated temporary database and
  temporary directories. They do not open a user's real database.
- **Authority:** TESTING.md; PERS-007; #191 verification introduction.
- **Pass condition:** The contract specifies temporary paths and cleanup.
- **Negative control:** A fixture path under the user home, or a shared
  durable database, must fail review.
- **Evidence expected:** A temporary-directory and temporary-database note.
  No new migration is authorized.

### TF-03

- **Requirement:** HTTP is mocked. Tests do not use live internet, live DNS,
  or the current provider response.
- **Authority:** TEST-002; X719; #191 and #198 verification introductions.
- **Pass condition:** The contract specifies a fake transport and a denial
  when an unmocked socket opens.
- **Negative control:** A live HTTP call, or a test that needs the network,
  must fail review and must fail the run.
- **Evidence expected:** A mocked-transport case and a socket-open failure.
  Not a claim that the mock was executed.

### TF-04

- **Requirement:** Credentials in fixtures are synthetic. Tests do not read
  the process environment's real keys, a dotenv file, the OS keyring, or a
  FinRobot secret file.
- **Authority:** SEC-001; X718; TESTING.md; #198 keychain synthetic row.
- **Pass condition:** The contract denies those sources in the test plan and
  in the worker.
- **Negative control:** A read of a real key, dotenv file, or keyring entry
  must fail. An empty or missing synthetic key refuses the billable path
  under RC-02.
- **Evidence expected:** A synthetic-only credential note and a denied
  keyring or dotenv case. No real secret value is written down.

### TF-05

- **Requirement:** Each negative control must be able to fail when the
  forbidden effect still happens. A model refusal string, an upstream
  comment, or a prompt promise is not a pass.
- **Authority:** #191 verification introduction; #198 matrix introduction;
  AI1024.
- **Pass condition:** The contract pairs every denial with an observable
  effect check: process list, byte compare, socket, or dispatch count.
- **Negative control:** A case that passes while the process, write, or
  socket still occurs must fail review.
- **Evidence expected:** The observable named on each denial row above. This
  document's existence is not that observable.

### TF-06

- **Requirement:** Passing this repository's current pytest, Ruff, mypy, or
  pip check does not prove any row in this matrix. #198 already records that
  repository pytest does not cover its synthetic matrix.
- **Authority:** #198 repository-checks section; #191 closing paragraph;
  #201 tests-required statement.
- **Pass condition:** The #192 draft repeats that limitation for its own
  proposed controls.
- **Negative control:** A claim that green CI proves the sandbox, the budget,
  the holdings projection, or the no-import runtime must fail review.
- **Evidence expected:** A limitations paragraph in the #192 PR. Green checks
  on this documentation PR prove only this repository's existing suite.

## 11. Activation blockers

These stay closed until the owner decides them. Local holdings access does
not open them. Eight rows.

### AB-01

- **Requirement:** Unknown pricing and the rest of open D9 block activation
  of every billable path.
- **Authority:** AI1016; #199 costs row; decision D9. Mismatch M-05.
- **Pass condition:** The contract lists D9 as a blocker and names no vendor
  price.
- **Negative control:** A price, a price version, or an activated paid path
  must fail review.
- **Evidence expected:** An open D9 item. The number is **owner-set value
  required**.

### AB-02

- **Requirement:** The treatment of an uncertain in-flight charge when a run
  is cancelled remains an open activation blocker. It is the same undecided
  D9 question, stated so a review cannot treat local cancel as settlement.
- **Authority:** #199 costs row; AI1016; #198 gating gaps 2 and 3. Mismatch
  M-05.
- **Pass condition:** The contract keeps this question open and blocks
  activation on it.
- **Negative control:** A refund rule, a maximum-charge rule, or a
  release-on-cancel rule marked accepted must fail review.
- **Evidence expected:** A separate open item from the generic "have a
  budget" sentence. See RC-04.

### AB-03

- **Requirement:** Source-code license, NOTICE, trademark text, and possession
  of an API key are not permission to transmit evidence to a model, retain a
  report, or redistribute data. Unclear rights block that transmission.
- **Authority:** AI1008; AI1026; X717; X727; decision D10; #197 license
  section; #198 gating gap 8.
- **Pass condition:** The contract lists rights as an activation blocker and
  does not treat the Apache-2.0 / NOTICE facts as a data contract.
- **Negative control:** "Apache-2.0 covers the market data" or "the existing
  API key covers LLM input" must fail review.
- **Evidence expected:** A rights matrix with present status unknown, not a
  legal conclusion invented by the contract.

### AB-04

- **Requirement:** Unknown remote settlement blocks activation. A finished
  local task, a missing usage payload, or a late contradictory bill is not
  proof that the charge matched the reservation.
- **Authority:** AI1016; #191 settlement paragraph; #198 unverified
  reservation note. The charge rule itself stays under M-05.
- **Pass condition:** The contract says remote settlement is unverified and
  is a blocker. It does not invent the reconciliation rule.
- **Negative control:** Local completion or missing usage treated as settled
  or as a zero charge must fail review.
- **Evidence expected:** An unverified-settlement gate. This checklist does
  not set a settlement procedure.

### AB-05

- **Requirement:** The local holdings grant is not implicit approval to
  transmit holdings, costs, or criteria text to a provider or model.
  Provider-specific opt-in and an owner-approved X716 exception are still
  required for that transmission and are not recorded on this baseline.
- **Authority:** AI1007; X716; #199 limit sentence; #191 rights row "No
  exception sought." Mismatch M-01.
- **Pass condition:** The contract states that local projection and provider
  transmission are different decisions, and that transmission remains blocked.
- **Negative control:** A clause that the holdings grant authorizes provider
  transmission must fail review.
- **Evidence expected:** A blocked transmission item that cites the local
  grant as insufficient. See HP-07.

### AB-06

- **Requirement:** Provider retention, training, deletion, and subprocessor
  terms are unknown. No zero-retention or no-training property is assumed.
- **Authority:** AI1008; decision D10; #191 rights table for retention and
  training; #198 gating gap 8.
- **Pass condition:** The contract blocks transmission and report-retention
  claims on this unknown.
- **Negative control:** An assumed training opt-out or an indefinite
  retention approval must fail review.
- **Evidence expected:** An unknown-retention blocker. A retention period is
  **owner-set value required**.

### AB-07

- **Requirement:** On the reviewed commit there is no accepted feasibility
  ADR. A draft of ADR-0019, once published, still needs owner acceptance
  before implementation or a PoC run.
- **Authority:** SRS §23.10.1; AI1030; #201 dependencies; absence of
  `docs/adr/0019-m10-feasibility-isolation.md` at
  `02815554e204d36809da62775b22a552fec8a257`.
- **Pass condition:** The draft identifies itself as unaccepted and does not
  instruct implementation.
- **Negative control:** Implementation work, a runtime change, or "ADR-0019
  accepted" on the basis of opening the PR must fail review.
- **Evidence expected:** The draft's status line and this checklist's phase-2
  findings. This file does not supply acceptance.

### AB-08

- **Requirement:** Existing FMP, Finnhub, and upcoming-EPS entitlements do
  not transfer to candidate discovery, web search, yfinance, EDGAR-through-FinRobot,
  or LLM transmission. EPS display does not qualify a criteria row.
- **Authority:** AI1008; #190 EPS limitation; #191 rights table for public
  evidence; #197 and #198 provider-chain findings; ADR-0015 as the accepted
  EPS boundary.
- **Pass condition:** The contract keeps those entitlements inside their
  accepted uses and blocks the wider uses.
- **Negative control:** A discovery or model call justified only by an
  existing market-data key must fail review.
- **Evidence expected:** A non-transfer statement beside any mention of FMP
  or Finnhub. No new endpoint is approved.

## Section index

| Section | IDs | Rows | Question the #192 review answers |
| --- | --- | --- | --- |
| Scope and authority | SA-01–SA-08 | 8 | Does the draft keep the no-import direction and refuse new product choices? |
| Criteria-snapshot envelope | EN-01–EN-07 | 7 | Does the draft preserve the exact ADR-0018 envelope? |
| Qualification and opinion | FQ-01–FQ-07 | 7 | Is factual qualification separate from scoped opinion text? |
| Linux isolation | IS-01–IS-10 | 10 | Are filesystem, egress, and process denials specified with negative controls? |
| Holdings and secrets | HP-01–HP-07 | 7 | Is the explicit projection specified, and are secrets excluded? |
| Limits and cancellation | RC-01–RC-08 | 8 | Are ceilings and cancellation left owner-gated, with no invented numbers? |
| Zero-billable synthetic mode | ZB-01–ZB-06 | 6 | Can the synthetic mode create a billable call or an import? |
| Provenance and status | PS-01–PS-08 | 8 | Are claims sourced, and are statuses kept distinct? |
| Core-app fallback | FB-01–FB-06 | 6 | Do core surfaces survive agents being off or failing? |
| Deterministic fixtures | TF-01–TF-06 | 6 | Are future tests fixed, temporary, mocked, and able to fail? |
| Activation blockers | AB-01–AB-08 | 8 | Do pricing, rights, settlement, and transmission stay blocked? |
| **Total** | | **81** | |

Mismatches M-01 through M-07 are open. No row is a passed test.

## Phase 2

When a #192 pull request exists, review `docs/adr/0019-m10-feasibility-isolation.md`
against these IDs. Report exact file and line findings, or a bounded pass
that lists limitations. Do not edit that ADR, `SRS.md`, `m10-plan.md`,
`CURRENT_STATUS.md`, or `m10-finrobot-safety.md` from the review. Do not
claim a proposed control is proven because this repository's tests passed.
Do not accept D9, rights, remote settlement, cadence, ranking, or provider
transmission on the owner's behalf.
