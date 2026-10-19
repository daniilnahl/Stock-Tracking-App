# Review of PR #202 — issue #201 phase 2

**Status: review record, 2026-10-19. Not owner acceptance, not a test result,
and not an edit to the proposed contract.** This file scores
[PR #202](https://github.com/daniilnahl/Stock-Tracking-App/pull/202) for
[#201](https://github.com/daniilnahl/Stock-Tracking-App/issues/201). The
matrix is [m10-poc-review-checklist.md](m10-poc-review-checklist.md). The
reviewed tree is commit `fcfa1648a610533664a0a18b646ce0e0f8349235` on
`codex/192-no-import-poc-contract`, confirmed equal to that pull request's
head. This branch does not edit `docs/adr/0019-m10-feasibility-isolation.md`,
`SRS.md`, `docs/CURRENT_STATUS.md`, `docs/milestones/m10-plan.md`, or
`docs/milestones/m10-finrobot-safety.md`. It does not comment on PR #202.

## Overall verdict

**CHANGES REQUESTED.**

The proposal keeps the no-import rule, retires #197 Phase B, and specifies a
zero-cost synthetic mode before any live call. Those parts match ADR-0020.
The same text freezes holdings fields, opinion text, status words, a numeric
charter, and a D9/settlement story that diverge from ADR-0020 and from the
SRS amendments in draft PR #204. Fifteen rows fail. Owner acceptance of
ADR-0019 stays a separate gate. This review does not accept ADR-0019, close
any remaining gate, or approve provider transmission. ADR-0020's own
acceptance is the owner's, recorded in that draft; this file does not
re-approve it.

## Counts

| Verdict | Rows |
| --- | --- |
| PASS | 39 |
| FAIL | 15 |
| PARTIAL | 27 |
| N/A | 0 |
| **Total** | **81** |

| Section | PASS | FAIL | PARTIAL | N/A |
| --- | --- | --- | --- | --- |
| SA-01–SA-08 | 7 | 0 | 1 | 0 |
| EN-01–EN-07 | 4 | 0 | 3 | 0 |
| FQ-01–FQ-07 | 3 | 4 | 0 | 0 |
| IS-01–IS-10 | 4 | 0 | 6 | 0 |
| HP-01–HP-07 | 2 | 2 | 3 | 0 |
| RC-01–RC-08 | 3 | 3 | 2 | 0 |
| ZB-01–ZB-06 | 5 | 1 | 0 | 0 |
| PS-01–PS-08 | 5 | 1 | 2 | 0 |
| FB-01–FB-06 | 0 | 1 | 5 | 0 |
| TF-01–TF-06 | 4 | 0 | 2 | 0 |
| AB-01–AB-08 | 2 | 3 | 3 | 0 |

FAIL rows: FQ-03, FQ-04, FQ-05, FQ-06, HP-01, HP-03, RC-01, RC-03, RC-04,
ZB-05, PS-07, FB-01, AB-02, AB-04, AB-08.

Line numbers below are the file at `fcfa1648`, unless a path is explicitly
this repository's merged text. ADR-0019 is absent on this branch; citations
of it are locations in that commit, not links.

## Authority used

Scored against the checklist's pass condition, the SRS on this branch
(AI1001–AI1032 as still unamended here), accepted ADR-0017 and ADR-0018, and
the merged #190, #191, #197, and #199 records.

The owner decisions of 2026-10-19 are written in
[ADR-0020](https://github.com/daniilnahl/Stock-Tracking-App/blob/2a93c7027181ba33e1011480a33732b3d2dd3bfd/docs/adr/0020-m10-owner-decisions.md)
on draft [PR #204](https://github.com/daniilnahl/Stock-Tracking-App/pull/204),
head `2a93c7027181ba33e1011480a33732b3d2dd3bfd` (pending merge). That pull
request also amends SRS AI1004, AI1007, AI1015, AI1016, AI1019, and AI1032.
This review cites that head and does not edit those files. Until #204 merges,
`SRS.md` on this branch remains the unamended specification. #202 is judged
against both. Where they differ, ADR-0020 is the owner's later decision, and
a contract that follows only the older open wording fails the row.

M-01 through M-07 in the checklist are marked resolved by that ADR, pending
merge. Line numbers for ADR-0020 and for the amended SRS sentences are the
file at `2a93c70`. Line numbers for ADR-0019 are the file at `fcfa1648`.

| Topic | ADR-0020 at `2a93c70` | #202 at `fcfa1648` |
| --- | --- | --- |
| D9 costs | Decision 1, lines 38–48, and amended AI1016 at `SRS.md:1430`. Hard per-run and per-day dollar caps. The owner sets the amounts. No numeric default. Reserve the full estimated maximum before a billable call. On in-flight cancel, keep the whole reservation and release it only after provider usage confirms the real charge. Zero-cost synthetic mode first. | D9 is stated open (`0019` lines 17 and 326). No per-run or per-day dollar cap. The future broker reserves a worst case and may release a proven-unused reservation (lines 326–334). Zero-cost synthetic mode is specified (lines 236 and 244–245). |
| Holdings | Decision 2, lines 50–59, and amended AI1007 at `SRS.md:1421`. Local read only. Never sent to an LLM provider. Tickers and portfolio weights only, with no quantities, cost basis, or account data. Weight is the figure the application already computes. | Synthetic projection is `quantity` and `average_cost`, plus namespace, ordinal, symbol, and exchange (lines 107–120). Weight is excluded as a derived valuation (line 117). Outward transmission is not authorized (lines 126–128). |
| Opinion | Decision 3, lines 61–68, and amended AI1019 at `SRS.md:1433`. Only when labeled "Research opinion, not financial advice", and only in research output and the stock suggestion of the day. Buy, Hold, or Avoid plus a reason. No numeric price targets and no forecasts. | Optional `synthetic_model_opinion` text, at most 512 UTF-16 units, with no required label, no verdict vocabulary, and no ban on a numeric target (lines 157–161 and 173–175). |
| Daily suggestion | Decision 4, lines 70–80, and amended AI1032 at `SRS.md:1446`. One per day, deterministic, from the user's watchlist, using existing factual criteria the application already computes. The agent writes only the explanation. No new ranking metric. D7 for this feature only. | "No ranking, daily scheduler" (line 160). Cadence and ranking "need separate contracts" (line 340). The synthetic universe is manifest fiction, not the watchlist (lines 133–135). |
| Status enum | Decision 5, lines 82–89, and amended AI1015 at `SRS.md:1429`. `pending`, `running`, `completed`, `completed_empty`, `partial`, `failed`, `cancelled`, `disabled`. No candidates found is `completed_empty`. | `pending`, `running`, then `completed`, `partial`, `failed`, or `cancelled` (lines 205–215). Empty is a phrase on `completed`. `disabled` is outside the result record. |
| Data | Decision 6, lines 91–95. The user's own FMP and Finnhub data under those providers' existing terms. Reports retained locally only. | No FMP or Finnhub sentence. Fixture IDs only (lines 137–138). Retention "need[s] separate contracts" (line 341). |
| Settlement | Decision 7, lines 97–102, also in amended AI1016. Settled only when the provider usage report matches or is within the reservation. A finished local task or a missing usage payload is not settled. | "Only proven unused reservation may be released under an accepted settlement policy" (lines 332–333). |
| #197 Phase B | Decision 8, lines 104–110. Formally retired. Charter figures are not defaults. | Superseded; "no Phase B importing FinRobot" (lines 15, 38, and 43). The per-case caps at lines 226–236 restate the charter figures. |

On this branch, before PR #204 merges, the SRS sentences #202 would replace
are still the older ones: AI1016 marks D9 decision-required, AI1019 blocks
BUY/HOLD/SELL display, AI1007 requires an X716 exception before private
holdings are used, and AI1015 names six statuses without `completed_empty` or
`disabled`. #202's new SRS paragraph restates that older open-D9 and broader
holdings grant. ADR-0020, pending merge, amends those requirements. Judging
#202 against both is why a sentence that was accurate on 2026-10-18 now fails.

Portfolio weight in ADR-0020 decision 2 is the figure the application already
computes. [FC-051](../FINANCIAL_CALCULATIONS.md) is that figure:
`position_market_value / portfolio_market_value` when complete portfolio
market value is available. Stored holdings in
`src/stock_tracker/persistence/models.py` have quantity and average cost, not
a weight field. This review does not invent a second formula.

The checklist now marks M-01 through M-07 resolved by ADR-0020 in PR #204
(pending merge). A #202 sentence that still calls one of those items open
fails the row that covers it.

## Blocking findings

### B-1 — D9 is written as open, and the charge rule differs

`docs/adr/0019-m10-feasibility-isolation.md:17` and `:326` say pricing and the
in-flight charge decision remain open. Lines 326–334 require a future broker
to reserve the worst case, keep uncertain sent work encumbered after cancel,
and release only a proven-unused reservation. ADR-0020 decision 1 (PR #204,
`0020:38-48`, pending merge) instead requires hard per-run and per-day dollar
caps with no numeric default, a reservation of the full estimated maximum
before any billable call, and release of that reservation only after provider
usage confirms the real charge. Amended AI1016 is `SRS.md:1430` at `2a93c70`.

The same "D9 remains open" sentence is new shared text at `SRS.md:21-22` in
that commit. `docs/milestones/m10-plan.md:17-21` leaves price and charge
settlement gated and says the opinion and holdings policies grant no cadence
or ranking rule. `docs/adr/0017-user-criteria-taurus-discovery.md:5-8` retains
the older D9 activation gate and the stored-holdings grant.

Rows: RC-03, RC-04, AB-02. RC-01 fails with B-3.

### B-2 — Settlement is a proven-unused release

`docs/adr/0019-m10-feasibility-isolation.md:332-334` allows release of a
proven-unused reservation under a future settlement policy, and it says that
paragraph is not acceptance. ADR-0020 decision 7 (`0020:97-102`, pending
merge) settles a run only when the provider usage report matches or is within
the reservation. A finished local task or a missing usage payload is not
settled. Lines 331–332 do keep an encumbrance after cancel, which refuses a
local finish as settlement. The usage-report rule is absent, and a
proven-unused release is a different rule.

Row: AB-04.

### B-3 — Concrete ceilings replace the open caps, including the #197 charter

`docs/adr/0019-m10-feasibility-isolation.md:226-236` sets inclusive caps: ten
cases, one worker, at most five fake-model attempts, ten fixture lookups,
65,536 input bytes, 65,536 output bytes, 60 seconds, and 1,048,576 scratch
bytes, with zero currency. Those per-case figures are the unaccepted charter
at `docs/milestones/m10-finrobot-feasibility.md:197-199` (ten cases, one
worker, 60 seconds, five fake dispatches, ten lookups, 64 KiB in and out, 1
MiB scratch, monetary budget zero). The ADR does not mark them unaccepted and
does not say **owner-set value required**. The phrase does not occur in the
ADR. ADR-0020 decision 8 (`0020:104-110`) says those charter figures are not
defaults and adopts none of them as a cap, duration, or case count. Decision 1
states no numeric dollar default. Amended AI1016 is `SRS.md:1430` at `2a93c70`.

Further filled numbers, also unmarked: 32 KiB frames (`:249-251`), the 256
KiB / 640 KiB / 128 KiB scratch split (`:261-262`), 128 MiB, PID limit 1, CPU
quota 1, and 32 file descriptors (`:284-285`), a 512-unit opinion cap
(`:174`), six holding rows (`:107`), and 60 evidence records (`:180`).

ADR-0020 decision 1 asks for hard per-run and per-day dollar caps and sets no
amount. No dollar amount or per-day cap appears in #202. Zero synthetic
currency (line 236) is the required zero-cost mode and does not supply those
caps.

Rows: RC-01, ZB-05. EN-03 is partial: editor limits stay on the envelope
(`:70`), but the PoC ceilings are these filled numbers.

### B-4 — Holdings fields are quantity and average cost

`docs/adr/0019-m10-feasibility-isolation.md:107-120` defines
`holdings_projection` as `namespace`, `ordinal`, `stock.symbol`,
`stock.exchange`, `quantity`, and `average_cost`. Line 117 forbids derived
valuation, so weight is out. Line 23 says the later #199 policy takes
precedence over a blanket exclusion of local holding fields. ADR-0020
decision 2 (`0020:50-59`; amended AI1007 at `SRS.md:1421` in PR #204, pending
merge) is narrower: tickers and portfolio weights only, with no quantities,
cost basis, or account data. Weight is the figure the application already
computes (FC-051). Quantity and average cost are the fields that decision
removes from the agent-visible projection.

Local read versus provider transmission is separated at lines 124–128, and
the worker input is local (lines 63 and 277). That part matches "never sent
to LLM providers." The field list does not.

`SRS.md:16-17` in that commit records "an explicit view of stored holdings"
without the ticker-and-weight limit.

Rows: HP-01, HP-03. HP-07 and AB-05 pass on the transmission gate alone.

### B-5 — Opinion text is not Buy, Hold, or Avoid, and a numeric target is not banned

`docs/adr/0019-m10-feasibility-isolation.md:157-161` publishes an optional
`synthetic_model_opinion` and calls scoped research or suggestion opinion
recorded policy. Lines 173–175 allow manifest `text` up to 512 UTF-16 units.
Nothing limits that text to Buy, Hold, or Avoid plus a reason, nothing
requires the label "Research opinion, not financial advice", and nothing
forbids a numeric price target or a forecast. "No real target calculation"
(line 160) blocks a calculation, not a number in the text. ADR-0020 decision 3
is `0020:61-68`, and amended AI1019 is `SRS.md:1433` at `2a93c70` (PR #204,
pending merge). Amended AI1004 at `SRS.md:1418` adds no numeric price target
and no forecast.

On this branch, AI1019 still says BUY/HOLD/SELL display remains blocked. The
#202 ADR does not record that unamended sentence, and it does not state the
ADR-0020 label and verdict list that replace it.

`SRS.md:19-21` in that commit says opinion text does not approve a ranking
formula or a daily cadence. That sentence misses the verdict list and the
price-target ban.

Rows: FQ-03, FQ-04.

### B-6 — The daily suggestion is left for a later contract

`docs/adr/0019-m10-feasibility-isolation.md:160` introduces no daily
scheduler. Line 340 says cadence and ranking need separate acceptance. The
case universe is at most three fictional security IDs (lines 133–135), not
the watchlist. ADR-0020 decision 4 (`0020:70-80`; amended AI1032 at
`SRS.md:1446` in PR #204, pending merge) is one suggestion per day, picked
deterministically from the user's watchlist using existing factual criteria
the application already computes. The agent writes only the explanation. No
new ranking metric. D7 is resolved for that feature only. Leaving the whole
cadence open reopens that feature. Synthetic fixtures may stay fictional; the
contract still has to record this rule.

`SRS.md:19-21` and `docs/milestones/m10-plan.md:19-20` in that commit say the
opinion decision grants no daily cadence and no ranking rule.

Row: FQ-05.

### B-7 — The status enum is not the accepted set

`docs/adr/0019-m10-feasibility-isolation.md:205-215` uses `pending`,
`running`, `completed`, `partial`, `failed`, and `cancelled`. Empty success is
a phrase allowed only on `completed` with zero qualified candidates and zero
unverified evaluations (lines 211–212). `disabled` is "outside the result
record" (lines 205–206). `completed_empty` does not appear. M-06 is not
recorded. The distinctions among empty, partial, failed, and cancelled are
present; the ADR-0020 list is not.

ADR-0020 decision 5 (`0020:82-89`; amended AI1015 at `SRS.md:1429` and AI1032
at `SRS.md:1446` in PR #204, pending merge) is the eight-value list, and no
candidates found is `completed_empty`. On this branch, AI1015 still has the
six words #202 adopted. The contract does not use the pending list.

Rows: FQ-06, PS-07.

### B-8 — Own FMP and Finnhub data, with local reports, is not stated

The ADR has no FMP or Finnhub sentence. Evidence references are `fixture:`
IDs (lines 137–138). Line 147 says not to invent an EPS basis. Line 341 defers
durable storage and retention to a separate contract. ADR-0020 decision 6
(`0020:91-95`, PR #204, pending merge) limits evidence to the user's own FMP
and Finnhub data under those providers' existing terms, and it retains reports
locally only. The synthetic mode correctly uses fixtures. The contract still
treats the production data source and report location as undecided.

Row: AB-08. AB-06 is partial: provider training and subprocessors stay
unstated, and local report retention is the B-8 gap.

### B-9 — Core surfaces are not required to survive an agent failure

`docs/adr/0019-m10-feasibility-isolation.md:51` says criteria preparation
remains inert. Line 222 says runtime errors do not write core storage. The
contract does not list the CLI, local API, dashboard, M9 criteria editor, and
holdings, and it does not require each of them to work when AI is absent,
disabled, offline, limited, incompatible, or invalid.

Row: FB-01. FB-02 through FB-06 are partial gaps in the same section.

## What matches

These are the reasons the verdict is not a rejection of the whole proposal.

- No install, import, load, execute, vendor, or copy of FinRobot V0, V1, or
  V2 (`0019:34-38`). Case 10 requires an actual denial (`:324`).
- The pin `2717499b8e30f242640af08c4ad9afd1113c2d45` is reference-only, and
  reopening it needs a new owner decision (`:32-38`). The diff does not change
  `pyproject.toml`.
- Phase B is not scheduled (`:15`, `:38`, `:43`, `:338`). That matches the
  retirement of #197 Phase B.
- The ADR is marked **PROPOSED** (`:5-9`). Merge and tests do not authorize
  execution (`:336-342`).
- Synthetic mode uses fake ports and zero provider, model, token, and currency
  use (`:236`, `:244-245`). That is the required zero-cost mode first.
- The criteria snapshot is the ADR-0018 envelope, revalidated independently,
  with order, duplicates, signed zero, and trailing zeros preserved
  (`:68-75`).
- Factual qualification is separate from opinion (`:155-161`, `:173`).
- Linux Docker, including Windows through WSL or Docker, is the platform
  (`:272-273`). Network none, no host binds, and a seccomp deny for socket,
  fork, and exec are specified (`:282-295`). The text says those denials are
  not already proven (`:299-300`).
- Outward transmission of holdings is not authorized (`:126-128`).
- Repository checks are stated not to prove the sandbox (`:344-347`).

## Row verdicts

PASS means the contract meets the checklist pass condition, as read with the
ADR-0020 resolutions in PR #204 (pending merge), and does not contradict that
ADR. FAIL means the pass condition is missed or the contract contradicts the
SRS on this branch or ADR-0020. PARTIAL means the main obligation is present
and a named piece is missing, without a contradiction that fails the row.
N/A is unused. Verdicts were rechecked against `2a93c70` and did not change.

### 1. Scope and authority

| ID | Verdict | Evidence at `fcfa1648` |
| --- | --- | --- |
| SA-01 | PASS | `0019:34-38` forbids install, import, load, execute, vendor, and copy for V0, V1, and V2. `:324` requires an actual denial of an import or vendor attempt. No dependency file is in the diff. |
| SA-02 | PASS | `0019:32-38` cites the pin as reference design only and requires a new owner decision before any load. The diff has no FinRobot dependency metadata. |
| SA-03 | PARTIAL | `0019:35-36` excludes TradingAgents, and `:32-34` keeps FinRobot as reference only. The draft scope section does not state that Taurus remains the product label for criteria-driven discovery. |
| SA-04 | PASS | `0019:5-9` is **PROPOSED**. `:8-9` says publication, merge, and tests do not accept the ADR or authorize execution. `:336-338` puts implementation after owner acceptance. |
| SA-05 | PASS | `0019:31` and `:49-50` keep approved dependencies and the stdlib and authorize no core pin change. `pyproject.toml` is outside the diff. Image Python 3.11/3.12 at `:274-275` matches `requires-python` `>=3.11,<3.13` and is the sandbox image, not an application pin change. |
| SA-06 | PASS | `0019:48-51`, `:134-135`, `:147`, and `:339-341` add no financial formula, vendor price, market universe, or ranking. The open cadence is FQ-05, not a new formula in this row. |
| SA-07 | PASS | `0019:59` says strings are data, never code, URLs, or policy. `:320` requires a separated opinion and no trade, criterion change, or new tool. `:305-306` requires the forbidden effect itself to fail the test. |
| SA-08 | PASS | `0019:11-17` separates settled records from proposed controls. `:299-300` and `:346-347` say the denials are not already proven and repository checks do not prove them. |

### 2. ADR-0018 criteria-snapshot envelope

| ID | Verdict | Evidence at `fcfa1648` |
| --- | --- | --- |
| EN-01 | PASS | `0019:68-70` binds `criteria_snapshot` to the exact ADR-0018 envelope and revalidates exact keys. `:56-58` rejects unexpected fields and forbids repair. The outer `m10_synthetic_run` kind is a wrapper, not a second criteria schema. |
| EN-02 | PARTIAL | `0019:70-72` requires the decimal grammar, inclusive bounds, signed zero, and trailing zeros. `:315` covers signed zero and malformed types. `:145` allows a predicate to compare decimal strings "numerically" without naming non-float decimal comparison. The case list does not include `+1`, `01`, `1e3`, a JSON number, a 129-character string, or both endpoints null. |
| EN-03 | PARTIAL | `0019:70` keeps the 1–20 row limit and the length limits on the envelope. The PoC ceilings at `:229-236` are separate from those editor limits, and 20 rows is not used as a time or money budget. Those ceilings are concrete figures rather than **owner-set value required**. See B-3. |
| EN-04 | PASS | `0019:51` says current criteria preparation remains inert. `:68-69` stores `all` or `any` on the envelope. `:75` does not pass a prepared snapshot through `prepareCriteria`. |
| EN-05 | PASS | `0019:71-72` preserves duplicates, units, and context. `:172` and `:196-197` bind row results to ordinals in original order. `:315` requires the same row bindings for duplicates. |
| EN-06 | PASS | `0019:56-58` rejects unknown versions and forbids dropping the rest of a bad record. `:70` and `:73-74` reject control-restriction failures and unpaired surrogates without normalizing other Unicode. `:315` includes version rejection. |
| EN-07 | PARTIAL | `0019:64-66` and `:87` bind one immutable manifest and fail a hash mismatch. `:51` and `:205` keep preparation and a disabled admission from starting a worker. The contract does not say a later edit marks that snapshot outdated, and it does not deny a hidden editor store. |

### 3. Factual qualification and optional opinion

| ID | Verdict | Evidence at `fcfa1648` |
| --- | --- | --- |
| FQ-01 | PASS | `0019:139-154` requires bound identity, units, period, and mandatory evidence, and it leaves unknown units unverified. `:317-318` covers missing evidence, collisions, and false citations. |
| FQ-02 | PASS | `0019:155-161` separates candidate state from `synthetic_model_opinion` and forbids opinion from asserting an unsupported match. `:173` sets `is_qualification: false`. `:320` injects opinion into qualification and requires it to stay separated. |
| FQ-03 | FAIL | `0019:157-161` and `:173-175` name the two scopes and a synthetic label. They do not require "Research opinion, not financial advice", do not limit verdicts to Buy, Hold, or Avoid plus a reason, and do not forbid a numeric price target. ADR-0020 decision 3, PR #204. See B-5. |
| FQ-04 | FAIL | `0019:160` says no real target calculation. The opinion `text` at `:173-175` can still carry a numeric target or a forecast. ADR-0020 decision 3 and amended AI1004 forbid both. No forecast field is stored, which is the part that holds. See B-5. |
| FQ-05 | FAIL | `0019:160`, `:218`, and `:340` leave ranking and cadence unresolved. ADR-0020 decision 4 is one deterministic watchlist suggestion per day from criteria the application already computes, for that feature only. See B-6. |
| FQ-06 | FAIL | `0019:205-215` lists six status words and a phrase for empty success. `completed_empty` is absent, `disabled` is outside the record, and M-06 is not recorded. See B-7. |
| FQ-07 | PASS | `0019:153` withholds unsupported facts. `:188` admits no extra candidate beyond the manifest. `:318` forbids a fabricated qualified result. `:320` forbids a criterion change. |

### 4. Linux filesystem, egress, and process isolation

| ID | Verdict | Evidence at `fcfa1648` |
| --- | --- | --- |
| IS-01 | PARTIAL | `0019:272-273` states a Linux Docker runtime, native or through WSL/Docker on Windows, and does not open a native Windows sandbox design. It does not say native Windows sandboxing is not required, and it does not say the core app's existing Windows behavior stays. |
| IS-02 | PASS | `0019:279-280` blocks the experiment when the reviewed image is absent. `:299-301` says the proposal does not claim the denials already work and requires host-file, DNS, and re-exec tests before dispatch. |
| IS-03 | PARTIAL | `0019:282-289` denies host binds, devices, inherited file descriptors, proxy variables, and `FINROBOT` or API-token environment variables, and it gives the worker an empty read-only home. `:324` requires an actual home and host read denial. The denial list does not name `.env`, browser profiles, core SQLite, core cache, or `~/.finrobot`. |
| IS-04 | PARTIAL | `0019:282-283` uses no host binds, which is an OS mount boundary. `:267-268` checks symlink escape when deleting scratch, which is a userspace path check. The case table has no `../` or symlink fixture. `:301` tests quota escapes, not traversal. |
| IS-05 | PARTIAL | `0019:244-245` allows only scripted fake functions and no shell or commands. `:284` sets PID limit 1. `:292-295` denies fork, clone, and exec. `:324` requires a child and re-exec denial. Pickle, arbitrary-object load, and in-process dynamic import are not denied. |
| IS-06 | PASS | `0019:282` sets network none. `:289` drops proxy variables. `:294` denies socket and network calls. `:301` and `:324` test DNS, IPv4, IPv6, loopback, and proxy. No permitted host is selected. |
| IS-07 | PARTIAL | `0019:59` and `:138` say strings and evidence IDs are not fetches. Network none makes a connection impossible inside this PoC. The contract does not specify trusted-code refusal of redirects, URL userinfo, or loopback, private, link-local, and metadata destinations for a later broker. |
| IS-08 | PASS | `0019:244-245` closes capabilities at supervisor-owned fake functions. `:324` forbids copied FinRobot default tools. An empty real-tool allowlist meets the row. The pinned names (yfinance, EDGAR, Adanos, Alpha Vantage, and the rest) are not itemized. |
| IS-09 | PASS | `0019:160` introduces no trade. `:222` forbids core-storage writes. `:320` requires no action on a trade request. No backtest statistic is published. |
| IS-10 | PARTIAL | `0019:235`, `:261-268`, and `:285` give the worker a distinct scratch tmpfs and forbid evicting user reports to meet caps. `~/.finrobot` is not named as a non-product store. Retention lifetime is deferred at `:341` rather than marked **owner-set value required**. |

### 5. Holdings projection and secret exclusion

| ID | Verdict | Evidence at `fcfa1648` |
| --- | --- | --- |
| HP-01 | FAIL | `0019:23` treats the #199 local-holdings grant as precedence over the earlier exclusion. `:124-128` keeps transmission gated. The field list contradicts ADR-0020 decision 2: tickers and portfolio weights only, no quantities or cost basis. See B-4. |
| HP-02 | PASS | `0019:107-113` and `:121-125` are an explicit field list, not a home mount and not a serialized portfolio object. Which fields are allowed is HP-03. |
| HP-03 | FAIL | `0019:107-120` projects quantity and average cost and forbids derived valuation, so the existing portfolio-weight figure is not included. ADR-0020 decision 2, PR #204. See B-4. |
| HP-04 | PARTIAL | `0019:122`, `:128-129`, `:169`, `:236`, and `:289` omit credentials and key objects, exclude private text from diagnostics, and drop API-token environment variables. The named set `.env`, keyring, FinRobot secret files, and the API bearer is incomplete. There is no per-channel synthetic-secret fixture. `:129` correctly says content detection is not a data-loss control. |
| HP-05 | PARTIAL | `0019:128` refuses secret-looking test text at admission. That avoids a rewrite, and it is not the required case of an exact stored snapshot whose secret is absent from prompt, log, and provider payload. |
| HP-06 | PARTIAL | `0019:125` acquires no actual holding, and `:222` forbids core writes. No before-and-after byte comparison on a temporary holdings database is specified. |
| HP-07 | PASS | `0019:126-128` separates the local grant from outward transmission and leaves provider opt-in and rights as gates. That matches "never sent to LLM providers." The fields the local worker would see are HP-03. |

### 6. Resource limits and cancellation

| ID | Verdict | Evidence at `fcfa1648` |
| --- | --- | --- |
| RC-01 | FAIL | `0019:226-236`, `:249-251`, `:261-262`, and `:284-285` fill time, byte, token-count, and concurrency ceilings. None is **owner-set value required**. Per-run and per-day dollar caps are absent. See B-3. |
| RC-02 | PASS | `0019:329-330` gives unknown price, version, currency, hidden usage, or an unenforceable maximum zero dispatches. That is a refusal, not a price of zero, and it does not by itself close D9. |
| RC-03 | FAIL | `0019:17` and `:326` say D9 remains open. Live activation stays blocked until caps are configured, which ADR-0020 decision 1 also requires. Recording D9 as open contradicts that decision in PR #204. See B-1. |
| RC-04 | FAIL | `0019:331-334` keeps uncertain work encumbered and refuses an automatic refund, then releases a proven-unused reservation. ADR-0020 decision 1 releases the full reservation only after provider usage confirms the real charge. See B-1. |
| RC-05 | PASS | `0019:207-208` cancels pending work with no dispatch. `:240-243` and `:253-254` stop admission at cancel and kill the worker. `:322` requires an atomic dispatch stop. The charge outcome stays under RC-04. |
| RC-06 | PARTIAL | `0019:331-332` keeps cancel, timeout, and crash encumbered. Closing a stream, disconnecting a UI, or treating client disconnect as settlement is not named. |
| RC-07 | PARTIAL | `0019:66`, `:208`, `:323`, and `:331-332` forbid auto-resume, retry, replay, and a budget reset. A double release of the same reservation is not stated. The ceiling value is the concrete cap from RC-01. |
| RC-08 | PASS | The limits table at `0019:229-236` does not copy the pinned 120/min buckets or the 2, 5, and 10 second retries. The safety-file errata at `m10-finrobot-safety.md:261-274` in that commit describes pinned behavior and says the library default is not an accepted cap (`:274`). |

### 7. Zero-billable synthetic mode

| ID | Verdict | Evidence at `fcfa1648` |
| --- | --- | --- |
| ZB-01 | PASS | `0019:42`, `:236`, and `:244-245` define fixture and fake ports with zero network, provider, model, token, and currency use. `:324` requires an actual network denial. This is the zero-cost synthetic mode first. |
| ZB-02 | PASS | `0019:113` and `:125-126` use manifest-owned fictional holdings and acquire no actual holding. `:236` and `:307` forbid credentials, host secrets, and live billing. |
| ZB-03 | PASS | `0019:47-49`, `:334`, `:342`, and `:345-347` say the experiment does not prove production cost enforcement and that repository checks do not prove the sandbox. A synthetic pass is not an activation. |
| ZB-04 | PASS | `0019:15`, `:38`, `:43`, and `:338` supersede Phase B and schedule no import. That matches ADR-0020 decision 8, which retires Phase B. |
| ZB-05 | FAIL | `0019:226-236` restates the #197 per-case duration, dispatch counts, byte ceilings, case count, and worker count from `m10-finrobot-feasibility.md:197-199` as inclusive caps. ADR-0020 decision 8 says those figures are not defaults. See B-3. |
| ZB-06 | PASS | `0019:45` says a failed synthetic path is not a reason to fall back to a live broker. `:297-298` refuses to start when a negative control fails. `:324` stops on import, home read, and network. `:320` stops a criterion mutation. The ADR remains proposed (`:5`). |

### 8. Provenance and status reporting

| ID | Verdict | Evidence at `fcfa1648` |
| --- | --- | --- |
| PS-01 | PASS | `0019:135-138` and `:180-185` bind evidence id, fixture digest, effective time, publication time, and receipt time. Display references are `fixture:` IDs. `:55-56` marks the records internal and proposed. |
| PS-02 | PASS | `0019:152-153` says a real reference that does not support the claim is insufficient. `:318` withholds a relevant-looking false citation and does not fabricate a qualified result. |
| PS-03 | PARTIAL | `0019:153`, `:169`, and `:179` withhold unsupported facts and keep reasons to manifest codes, with no raw prompt in the output. Diagnostic retention lifetime is not **owner-set value required**; `:341` defers retention. Local report retention is B-8. |
| PS-04 | PASS | `0019:90-92` fixes the civil cutoff and says receipt never substitutes for publication. `:181-185` keeps effective, published, and received times as separate manifest fields. `:318` and `:322` cover stale evidence and a backward civil clock. |
| PS-05 | PARTIAL | `0019:168-169` and `:179` exclude arbitrary model fields, prompts, traces, raw exceptions, private text, and chain-of-thought from output. A synthetic-secret log fixture is not in the case table; `:316` covers metadata leak only. |
| PS-06 | PASS | `0019:210-211` requires successful cleanup and full evaluation for `completed`. `:220-221` says partial and cancelled evidence never become a completed report. |
| PS-07 | FAIL | `0019:211-215` allows the empty phrase only on a completed, fully evaluated, empty result, and it keeps partial, failed, and cancelled distinct. `completed_empty` is not a status, `disabled` is outside the enum (`:205-206`), and M-06 is not recorded. See B-7. |
| PS-08 | PASS | `0019:5-9` and `:55-56` mark the records proposed and internal. The diff adds no route, API model, or migration. |

### 9. Core-app fallback

| ID | Verdict | Evidence at `fcfa1648` |
| --- | --- | --- |
| FB-01 | FAIL | `0019:51` and `:222` cover inert preparation and no core writes. The CLI, local API, dashboard, M9 editor, and holdings are not listed against absent, disabled, offline, limited, incompatible, and invalid AI. See B-9. |
| FB-02 | PARTIAL | `0019:65-66` requires a deliberately authorized invocation and forbids auto-resume. `:205` gives a disabled admission no worker. `:236` is zero paid use inside the PoC. The product capability is not stated as disabled by default, and application startup is not given a zero-dispatch case. |
| FB-03 | PARTIAL | `0019:34-35` forbids importing FinRobot on the proposed path. No cold-import check requires the core CLI, API, and dashboard to import with the agent package absent and without reading agent credentials. |
| FB-04 | PARTIAL | `0019:208`, `:222`, and `:242` forbid retry and core writes after failure. No failure fixture compares holdings, watchlist, M9, or API bytes. A retry bound is unnecessary only because retry is forbidden outright. |
| FB-05 | PARTIAL | `0019:50` authorizes no core pin change, and `:222` forbids core writes. No disable case asserts unchanged holdings bytes and unchanged pin metadata, and report deletion on disable is unstated. |
| FB-06 | PARTIAL | `0019:51` says preparation remains inert. Editing, navigating, and clearing are not named, and no no-request assertion is attached to those editor actions. |

### 10. Deterministic test fixtures

| ID | Verdict | Evidence at `fcfa1648` |
| --- | --- | --- |
| TF-01 | PASS | `0019:90-95` fixes `2026-01-15T12:00:00Z`, forbids current-date access, injects a scripted monotonic clock for races, and keeps a real monotonic watchdog for enforcement. `:322` includes a backward civil clock. |
| TF-02 | PARTIAL | `0019:254` and `:267-268` remove only owned scratch after an ownership and symlink check. `:285` uses a tmpfs scratch mount. `:125` reads no actual holdings database. An isolated temporary database for persistence cases is not specified. |
| TF-03 | PASS | `0019:282` and `:294` deny the network and the socket calls. `:301` and `:324` fail the run on DNS or a socket. Tests are not allowed a live HTTP call (`:307`). |
| TF-04 | PARTIAL | `0019:236`, `:289`, and `:307` use no credentials, drop API-token environment variables, and forbid host secrets. A dotenv file and the OS keyring are not named as denied reads. |
| TF-05 | PASS | `0019:305-307` requires each negative control to detect the forbidden effect, including by a relaxed counter that must fail. The case table states dispatch, byte, process, and socket observables. |
| TF-06 | PASS | `0019:344-347` says full pytest, Ruff, mypy, and pip check do not prove the sandbox, and that no PoC or provider operation was run. The pull request text repeats that limit. |

### 11. Activation blockers

| ID | Verdict | Evidence at `fcfa1648` |
| --- | --- | --- |
| AB-01 | PARTIAL | `0019:17`, `:326`, and `:339-340` block live activation and name no vendor price. They record D9 as open instead of ADR-0020 decision 1's per-run and per-day dollar caps. Dollar amounts stay unset in that decision and are not invented here. See B-1 and B-3. |
| AB-02 | FAIL | `0019:326-334` keeps an in-flight charge question open and then specifies encumbrance plus a proven-unused release. ADR-0020 decision 1 keeps the full reservation until provider usage confirms the real charge. See B-1. |
| AB-03 | PARTIAL | `0019:48-49`, `:127-128`, and `:339-340` leave vendor and model rights as gates and do not treat a license as a data contract. There is no rights matrix whose present status is unknown. Apache-2.0 is not claimed as market-data permission. |
| AB-04 | FAIL | `0019:332-334` invents release of a proven-unused reservation. ADR-0020 decision 7 settles only when the provider usage report matches or is within the reservation. Missing usage is not treated as a zero charge, because the encumbrance remains. See B-2. |
| AB-05 | PASS | `0019:124-128` says the local grant is not outward transmission and that provider-specific opt-in and rights remain gates. That matches "never sent to LLM providers." The local field list is HP-03. |
| AB-06 | PARTIAL | `0019:341` defers durable retention to a separate contract and does not assume a training opt-out. Provider retention, training, deletion, and subprocessors are not stated as unknown. Reports kept local is B-8. |
| AB-07 | PASS | `0019:5-9` identifies the ADR as unaccepted. `:336-342` requires owner acceptance before implementation and says a passing PoC is not live activation. Opening the pull request is not treated as acceptance. |
| AB-08 | FAIL | `0019:137-138` and `:147` use fixture IDs and forbid an invented EPS basis. FMP and Finnhub are not named. ADR-0020 decision 6 requires the user's own FMP and Finnhub data and locally retained reports. See B-8. |

## Non-blocking gaps

The 27 PARTIAL rows should be closed in the same contract revision. They are
not a second verdict. The repeated gaps are:

- The contract should cite ADR-0020 for M-01 through M-07 instead of
  leaving those items open. PR #204 is pending merge.
- Denial lists omit named paths and secret stores: `.env`, browser profiles,
  core SQLite, core cache, `~/.finrobot`, pickle, dotenv, and the OS keyring
  (IS-03, IS-05, HP-04, TF-04).
- Editor lifecycle, decimal-grammar fixtures, and symlink traversal are thinner
  than the checklist's negative controls (EN-02, EN-07, IS-04).
- Core fallback is only inert preparation and no core writes (FB-02–FB-06,
  with FB-01 already failing).
- Rights, provider retention, and UI-disconnect settlement are stated as open
  gates without the checklist's matrix or the disconnect case (AB-03, AB-06,
  RC-06).

## Source-fact errata

PR #202 also edits `docs/milestones/m10-finrobot-safety.md:261-266` and
`:475-480` at this commit. Those paragraphs correct pinned recoverable
exceptions and the secret-store fallback. This review did not re-read the pin
`2717499b8e30f242640af08c4ad9afd1113c2d45` to confirm them. They are not
adopted as application caps (RC-08). They are not a blocking finding and not
a verification of the pin.

## What this review does not do

- It does not accept ADR-0019, merge PR #202, or authorize a PoC run.
- It does not edit PR #204, ADR-0020, or the SRS amendments in that draft.
  Those decisions are cited at `2a93c7027181ba33e1011480a33732b3d2dd3bfd`.
  Pending merge, they are not the text of `SRS.md` on this branch.
- It does not set dollar amounts, a vendor, a price version, or a new weight
  formula. ADR-0020 decision 2 uses the portfolio-weight figure the
  application already computes. FC-051 is that figure.
- It does not treat a PASS row as a passed sandbox, budget, or holdings test.
- It does not re-approve ADR-0020. The owner accepted those decisions in that
  draft. This review only uses them to score #202.

## Limitations that would remain after the changes

Even a revised contract that clears the fifteen FAIL rows would not prove the
Linux image, seccomp profile, negative controls, or a billable ledger. The
ADR already says the image digest and bootstrap are missing and that the
experiment stays blocked without them (`0019:279-280`, `:297-300`). Rights to
transmit evidence, and the numeric dollar amounts on the accepted per-run and
per-day caps, are still owner inputs. This review does not supply them.
