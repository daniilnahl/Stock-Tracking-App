# M9 decision brief

**Proposed — owner review required.** Prepared 2026-10-16 for
[#164](https://github.com/daniilnahl/Stock-Tracking-App/issues/164).
This brief narrows the questions that block SRS §23.9. It does not approve a
screen, financial formula, provider use, calendar, quota or persistence design.
See [the execution plan](m9-plan.md) for capability evidence and dependencies.

**Scoped acceptance update — 2026-10-16:** the owner subsequently selected
Finnhub Free's upcoming-release EPS estimate and requested implementation.
[ADR-0015](../adr/0015-finnhub-upcoming-eps.md) and EPS-001–004 now define that
narrow observation capability, owner-merged in #167. The owner's instruction
to continue authorizes #168's injected application service under the ADR's
addendum. Earlier investigation-only statements below are superseded for this
bounded offline capability. Live/default wiring still needs actual access/use,
trusted date convention, identity and quota ownership; full M9 and the remaining
screen/calculation/storage/API decisions are not accepted.

**Owner source-direction update — 2026-10-16:** the owner selected “first use
FMP then use finviz” and requested a native-metric gap comparison. Source priority
is selected: FMP first, optional FINVIZ enrichment. See the
[sourced coverage report](m9-provider-coverage.md) for candidate gaps, overlapping
capabilities and unresolved API/rights evidence. This does not select a financial
preset, approve unknown entitlement or accept the whole M9 specification.

**Owner access update — 2026-10-16:** “no subscription.” No paid FMP/FINVIZ
entitlement is available. Evaluate an FMP free-tier subset only after verifying
its exact fields/rights/access; defer FINVIZ API activation. Free account/key
existence is unconfirmed. See the coverage report for current published limits.

**EPS requirement:** the owner requires EPS and requested Finnhub free-tier
evaluation. [Research](m9-finnhub-eps.md) distinguishes recent quarterly actuals/
estimates from TTM/annual/forward EPS. Free recent results do not resolve the
long-term expected-growth requirement; precise accounting/period semantics and
allowed use remain contract decisions before implementation.

## Recommended scope boundary

Use the existing local single-user Python service/API/dashboard architecture.
Keep research deterministic and informational: inspect dated evidence and
explain approved filters, without personalized suitability, trade instructions,
predictions or BUY/HOLD/SELL opinions. Keep M10 separate. Preserve exact holdings,
ordered duplicates, namespaces, current/history contracts and offline core use.
This recommendation needs explicit owner acceptance for M9/D11; it does not
reopen already accepted M7/M8 behavior or settle the remaining choices below.

Start provider feasibility with FMP and the existing exact NASDAQ identity
boundary. This is a proposed bounded first universe, not proof of coverage or
entitlement. FINVIZ remains optional and disabled until independently verified.
No scraping, subscription purchase, live credential test, model call, external
notification or deployment is proposed. An offline fixture can demonstrate a
contract but cannot establish rights or satisfy a live-data requirement.

## Decisions and required evidence

| Gate | Concrete owner input / contract needed | Recommendation / consequence |
| --- | --- | --- |
| M9 acceptance and D11 | Explicitly accept the intended SRS §23.9 scope and informational boundary; identify any deferred exit requirements. | Accept deterministic evidence/filter research only; omit directional model opinions. No full M9 acceptance is inferred from requesting planning. |
| D5 / RSH901–905 / X717, X727 | Identify the actual FMP plan and permitted fields/uses; provide sanitized applicable entitlement/contract evidence for acquisition, display, storage, automation, retention and report use. No credentials in chat/repo. | Prepare a dated field/use rights matrix from official documentation plus owner entitlement evidence. Unknown rights keep that path disabled. Technical API availability alone is insufficient. |
| D6 / RSH913–919, RSH924–926 | Select the first research question and exact fields/filters; approve universe membership source/date, identity ambiguity handling, sector taxonomy/version, units/periods, missing/conflict rules, stable ordering and bounds. | Begin with one narrow named screen over the supported universe. Do not invent a value/growth/momentum preset, thresholds, weighting or attractiveness rank. Existing profile labels do not constitute an approved taxonomy. |
| FIN-004/005 / RSH915 | For each derived metric or score, approve formula, units, rounding boundary, input dates/periods, currency, zero/missing behavior and worked fixed examples in the financial specification. Even reported fields need an approved semantic registry. | Prefer the fewest fields necessary for the chosen question. No new arithmetic or known-value expectation can be written before that question is selected. |
| D7 / RSH918, RSH920, RSH923 | Approve market timezone/date/calendar, analysis cutoff, eligibility/rank/tie-break, rerun/revision and holiday/no-candidate behavior. | Persist immutable dated results; never select an arbitrary fallback to force a daily stock. Existing raw history does not prove complete sessions or adjusted returns. |
| D8 / RSH910–912, RSH929–931, RSH936 | Approve separate research storage ownership/location/versioning, retention/backup, job transitions, atomic completion, dedup/concurrency, cancellation, schedule bounds and missed-run/restart behavior. Supply actual plan quota evidence and per-class freshness choices. | Draft this architecture after field/snapshot needs stabilize. Preserve the single migration mechanism and prohibit inferred deletion of user-owned reports. Do not select retention periods, scheduler frequency or quota limits without evidence/approval. |
| Research API / RSH935 | Approve route/model/async semantics, criteria/job-command authorization, browser-origin defenses and concurrency/cancellation behavior. | Extend existing authenticated loopback architecture only after shared services stabilize. M7 read-only acceptance does not authorize research job commands. |

Existing D1/D2 acceptance applies only to M7/M8's accepted subset; research
extensions need review. D9/D10 AI feasibility, privacy/cost/model transmission
remain M10 gates. D5 rights must still cover any proposed non-AI report use.

## Review sequence

1. Owner selects the research question, initial universe/source direction and
   informational boundary. A sample question is useful; it is not an approved
   financial preset until exact semantics and examples are reviewed.
2. Prepare separate bounded rights, screen/selection and storage/job/API contract
   proposals. Verify current primary documentation when investigating external
   endpoints; the older SRS review's provider observations are dated evidence.
3. Independently review each proposal against approved requirements, record
   explicit owner acceptance and preserve unresolved gates by capability.
4. Only then create implementation-ready issues for accepted/unblocked contracts,
   delegate isolated branches and independently review tested PRs. Owner merges
   remain required. Approval of one contract does not unlock unrelated gates.

Source priority is now selected. Remaining immediate human decisions are the
**research question and exact universe**, together with acceptance of the
informational boundary and exact free-tier field/access/use evidence. A broad
instruction to start M9 cannot safely choose these product
semantics. Broader runtime implementation remains blocked by the relevant SRS
and AGENTS requirements. The accepted offline EPS adapter and injected-service
continuation above are separate, bounded exceptions to that broader block.
