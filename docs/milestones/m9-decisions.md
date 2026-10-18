# M9 decision brief

**EPS API approval — 2026-10-17:** the owner explicitly approved ADR-0016
Option A and requested online verification. #178 implements the injected API
adapter plus one isolated real single-symbol request. This resolves the API
contract for stage 1; production composition/budget/use evidence and dashboard
design remain separate. The previously reported key is available as a Windows
user variable; no key or vendor response is recorded in this brief.

**Custom criteria answer — 2026-10-17:** the owner selected whatever parameter
names and range values users want. Accepted
[ADR-0018](../adr/0018-custom-criteria-editor.md) defines #176's nonexecuting
tab-memory editor: custom names, signed exact ranges with explicit user context,
text requirements and all/any mode. The older fixed-field-list question below
is superseded for this descriptive editor. It does not approve evaluation of
arbitrary financial metrics, a provider mapping, durable storage or agent calls.

**Owner ownership decision — 2026-10-17:** accepted
[ADR-0017](../adr/0017-user-criteria-taurus-discovery.md) supersedes the original
M9 screen/daily-selection allocation: M9 lets users configure stock criteria;
M10 Taurus searches for candidates using those parameters. M9 does not implement
an API-based stock-finding engine. Exact supported fields, operators, units,
validation, settings/API/UI schema and handoff remain the next criteria contract.
Ordinary permitted known-stock data calls remain independent. Earlier requests
below for an M9 preset/ranking/daily-selection contract are superseded for that
ownership, not silently resolved as financial or agent implementation choices.

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
| D6 / RSH914–917, RSH921, RSH936 | ADR-0018 now defines the custom range/text editor, explicit context/all-any, exact prepared envelope and tab-memory lifecycle. Backend storage and actual source-metric verification remain future contracts. | M9 prepares descriptive criteria and performs no discovery. A user label is not an approved financial metric, provider field or taxonomy. Taurus interpretation/search/results belong to M10. |
| FIN-004/005 / RSH915 | For each derived metric or score, approve formula, units, rounding boundary, input dates/periods, currency, zero/missing behavior and worked fixed examples in the financial specification. Even reported fields need an approved semantic registry. | Prefer the fewest fields necessary for the chosen question. No new arithmetic or known-value expectation can be written before that question is selected. |
| D7 / future M10 suggested-stock policy | Define any daily cadence, market calendar, ranking/tie-break, revision and empty/incomplete-search outcome under the future Taurus contract. | Moved out of M9 exit by ADR-0017. No M9 daily winner is required; do not infer a daily agent schedule or ranking from this reassignment. |
| D8 / RSH910–912, RSH929–931, RSH936 | Approve separate research storage ownership/location/versioning, retention/backup, job transitions, atomic completion, dedup/concurrency, cancellation, schedule bounds and missed-run/restart behavior. Supply actual plan quota evidence and per-class freshness choices. | Draft this architecture after field/snapshot needs stabilize. Preserve the single migration mechanism and prohibit inferred deletion of user-owned reports. Do not select retention periods, scheduler frequency or quota limits without evidence/approval. |
| Research API / RSH935 | Approve route/model/async semantics, criteria/job-command authorization, browser-origin defenses and concurrency/cancellation behavior. | Extend existing authenticated loopback architecture only after shared services stabilize. M7 read-only acceptance does not authorize research job commands. |

Existing D1/D2 acceptance applies only to M7/M8's accepted subset; research
extensions need review. D9/D10 AI feasibility, privacy/cost/model transmission
remain M10 gates. D5 rights must still cover any proposed non-AI report use.

## Review sequence

1. Define the supported user parameters/operators/units/null/combination rules
   and inspectable criteria settings/handoff. A user preference does not approve
   an undefined metric, hidden preset or default threshold. A search universe
   belongs to M10 unless explicitly defined as a supported user criterion.
2. Prepare bounded criteria/handoff and known-stock rights/storage/API contract
   proposals as needed. Verify current primary documentation when investigating external
   endpoints; the older SRS review's provider observations are dated evidence.
3. Independently review each proposal against approved requirements, record
   explicit owner acceptance and preserve unresolved gates by capability.
4. Only then create implementation-ready issues for accepted/unblocked contracts,
   delegate isolated branches and independently review tested PRs. Owner merges
   remain required. Approval of one contract does not unlock unrelated gates.

Source priority, M9-criteria/M10-discovery ownership and ADR-0018's first custom
descriptive editor are now selected. #176 implements that editor and local
prepared data. Future durable saving/backend routes and actual source-metric
evaluation need separate contracts/evidence. Taurus interpretation, search scope/
universe and suggested-result policy are M10 decisions. Existing accepted EPS/
configuration capabilities remain independently available; no stock-finding
engine is an M9 prerequisite.
