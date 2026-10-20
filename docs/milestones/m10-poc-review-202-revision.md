# Re-review of revised PR #202 — issue #205

**Status: documentation review, 2026-10-20. Not owner acceptance, not a
sandbox or budget result, and not an edit to the proposed contract.**
This file re-scores
[PR #202](https://github.com/daniilnahl/Stock-Tracking-App/pull/202) for
[#205](https://github.com/daniilnahl/Stock-Tracking-App/issues/205).
The reviewed tree is commit
[`9e29e5468c34a91636ca717c87f8d6d5b445febb`](https://github.com/daniilnahl/Stock-Tracking-App/commit/9e29e5468c34a91636ca717c87f8d6d5b445febb)
on `codex/192-no-import-poc-contract`, confirmed equal to that pull request's
head. The contract under review is
[`docs/adr/0019-m10-feasibility-isolation.md` at that commit](https://github.com/daniilnahl/Stock-Tracking-App/blob/9e29e5468c34a91636ca717c87f8d6d5b445febb/docs/adr/0019-m10-feasibility-isolation.md).
Line numbers below are that file unless another path is named.

The comparison baseline is the merged review
[m10-poc-review-202.md](m10-poc-review-202.md) of head
`fcfa1648a610533664a0a18b646ce0e0f8349235`, and the row definitions in
[m10-poc-review-checklist.md](m10-poc-review-checklist.md). Accepted
[ADR-0020](../adr/0020-m10-owner-decisions.md) controls. This branch does not
edit ADR-0019, `SRS.md`, `docs/CURRENT_STATUS.md`, `docs/milestones/m10-plan.md`,
`docs/milestones/m10-finrobot-safety.md`, or the historical review. It does
not comment on PR #202, accept ADR-0019, or reopen ADR-0020.

## Overall verdict

**PASS with limitations.**

The revision records the accepted ADR-0020 rules that the earlier head
contradicted. All nine blocking findings and all fifteen former FAIL rows are
addressed in the proposed contract. Twenty-five of the twenty-seven former
PARTIAL rows are addressed. Two documentation rows remain actionable: the
draft scope still does not state the Taurus product label (SA-03), and the
range comparison sentence still does not say exact decimal-string comparison
(EN-02). Neither row contradicts ADR-0020, and neither restores a former FAIL.

This is a reading of the text at `9e29e54`. It is not evidence that a sandbox,
a budget ledger, or a negative control has run. Owner acceptance of ADR-0019
remains pending. This review does not accept that ADR, choose a numeric cap,
or re-approve ADR-0020.

## Counts

| Set | Addressed | Still actionable |
| --- | --- | --- |
| Blocking findings B-1–B-9 | 9 | 0 |
| Former FAIL rows (15) | 15 | 0 |
| Former PARTIAL rows (27) | 25 | 2 |
| Former PASS rows checked for regression (39) | 39 still hold | 0 regressed |

The two still-actionable rows are SA-03 and EN-02, listed below with current
file and line.

## Blocking findings

| ID | Result | Current evidence at `9e29e54` |
| --- | --- | --- |
| B-1 | ADDRESSED | `:16` records D9 resolved: owner-configured run and day dollar caps, full run reservation, provider-reported settlement. `:281` and `:384-392` require both caps, with no numeric default, and reserve the full run maximum against both before the first billable call. `:394-401` keeps the whole reservation on in-flight cancel and forbids an early proven-unused release. |
| B-2 | ADDRESSED | `:396-401` settles a run only when the provider usage report matches or is within the reservation. Missing, contradictory, or above-reservation usage stays unsettled and cannot authorize another billable call. Unused reservation is released only after that accepted settlement check. |
| B-3 | ADDRESSED | `:77` refuses an inherited case count of ten. `:269-296` says no #197 charter number is a default, duration, or case count, and that every applicable synthetic-resource row needs an explicit finite owner value. No 60-second, five-dispatch, 64 KiB, 1 MiB, 128 MiB, PID, FD, or 512-unit figure is supplied. `:91-92` says the editor limits are not resource defaults. |
| B-4 | ADDRESSED | `:118-122` exposes exactly `ticker` and `portfolio_weight`. Namespace, ordinal, exchange, and identity bindings stay supervisor-only. `:125-135` takes weight from `PositionAllocation.weight` under FC-051/ADR-0011 and forbids a new formula. `:137-138` excludes quantity, average cost, cost basis, and account identifiers. |
| B-5 | ADDRESSED | `:184-191` requires the label "Research opinion, not financial advice", a verdict of Buy, Hold, or Avoid, and a reason. The same sentences forbid a numeric price target, a forecast, a trade, and a threshold change, including inside a nested reason. |
| B-6 | ADDRESSED | `:193-202` records one deterministic watchlist pick per day from criteria the application already computes. Only the explanation is agent-written. No new ranking metric. Selector, tie-break, and day-boundary details stay implementation gates. The PoC uses a preselected fictional item and does not claim a real pick. |
| B-7 | ADDRESSED | `:209-211` lists only `pending`, `running`, `completed`, `completed_empty`, `partial`, `failed`, `cancelled`, and `disabled`. `:213-215` and `:253-258` put `disabled` and `completed_empty` on that same record. |
| B-8 | ADDRESSED | `:156` and `:162` limit evidence to the user's own FMP and Finnhub data, with fictional fixtures in the PoC. `:159` keeps reports local and requires an owner-set retention lifetime. `:227` labels synthetic evidence `synthetic_fmp` or `synthetic_finnhub`. |
| B-9 | ADDRESSED | `:47-50` requires core startup, CLI, authenticated local API, dashboard, M9 editor, and saved holdings to keep working when the agent package is absent, disabled, offline, limited, incompatible, invalid, or failing, without importing it or reserving cost. `:372` is the matching negative-control group. |

## Former FAIL rows

| Row | Result | Current evidence at `9e29e54` |
| --- | --- | --- |
| FQ-03 | ADDRESSED | `:184-188` requires the research-opinion label, Buy/Hold/Avoid, and a reason, and limits that object to research output or the stock suggestion of the day. See B-5. |
| FQ-04 | ADDRESSED | `:188-191` forbids a numeric price target and a forecast in any field or nested reason, and rejects violating fake output. See B-5. |
| FQ-05 | ADDRESSED | `:193-200` records the deterministic daily watchlist rule and refuses a new ranking metric or a model-selected winner. See B-6. |
| FQ-06 | ADDRESSED | `:209-215` and `:256-258` use the eight statuses, including `completed_empty` for a bounded empty result. See B-7. |
| HP-01 | ADDRESSED | `:143-145` forbids sending holdings, including the ticker and weight projection, to any LLM, with no opt-in. `:137-138` drops quantity and cost basis. See B-4. |
| HP-03 | ADDRESSED | `:118-135` projects ticker and the existing portfolio weight only. See B-4. |
| RC-01 | ADDRESSED | `:281-289` names per-run and per-day dollar caps and the other resource rows as owner-set, with no numeric defaults. See B-3. |
| RC-03 | ADDRESSED | `:16` and `:384-386` record D9 as resolved policy and leave the amounts unset. See B-1. |
| RC-04 | ADDRESSED | `:394-397` keeps the whole in-flight reservation until provider-reported usage confirms the real charge. See B-1. |
| ZB-05 | ADDRESSED | `:269` and `:296` reject the #197 charter numbers as defaults and supply none in their place. See B-3. |
| PS-07 | ADDRESSED | `:209-211` and `:256-260` distinguish `completed_empty`, `partial`, `failed`, `cancelled`, and `disabled`. See B-7. |
| FB-01 | ADDRESSED | `:47-50` lists the core surfaces and the absent, disabled, offline, limited, incompatible, invalid, and failing cases. See B-9. |
| AB-02 | ADDRESSED | `:394-401` replaces proven-unused release with provider-reported settlement of the whole reservation. See B-1 and B-2. |
| AB-04 | ADDRESSED | `:396-399` refuses to treat missing usage, local completion, or an inferred unused amount as settlement. See B-2. |
| AB-08 | ADDRESSED | `:156-159` and `:227` name the user's FMP and Finnhub data and local report retention. See B-8. |

## Former PARTIAL rows

| Row | Result | Current evidence at `9e29e54` |
| --- | --- | --- |
| SA-03 | STILL ACTIONABLE | `:34-40` keeps FinRobot reference-only and excludes TradingAgents. The draft scope section does not state that Taurus remains the product label. The word does not appear in this ADR. [ADR-0017](../adr/0017-user-criteria-taurus-discovery.md) still carries the label, and `:15` cites that ADR for discovery ownership. The checklist pass condition asks for all three facts together in the draft scope. |
| EN-02 | STILL ACTIONABLE | `:87-90` preserves exact strings, signed zero, and trailing zeros, and forbids plus, exponent, leading-zero padding, whitespace, Infinity, NaN, and floats. `:371` covers plus, exponent, NaN, whitespace, and signed-zero/precision cases. `:89-91` then says to compare minimum and maximum "without display rounding." [ADR-0018](../adr/0018-custom-criteria-editor.md) lines 54–55 require exact decimal-string comparison only. The citation at `:95-96` identifies that handoff; the revalidation sentence does not use it. |
| EN-03 | ADDRESSED | `:85-92` keeps the 1–20 row and 80/256/128 editor limits and says they are not #197 resource defaults. `:269-276` requires owner-set resource values and refuses fallback numbers. |
| EN-07 | ADDRESSED | `:55-57` keeps editor actions tab-memory-only, with no hidden store or request. `:108-109` marks a later edit outdated and forbids silent use of the edited draft. |
| IS-01 | ADDRESSED | `:51-52` keeps core native Windows support and says native Windows agent sandboxing is not required. The sandbox is Linux, including WSL/Docker on Windows. |
| IS-03 | ADDRESSED | `:349-351` names `.env`/dotenv, the OS keyring, browser profiles, API bearer and provider keys, core SQLite, the history cache, and `~/.finrobot`. `:380` requires canaries for those paths. |
| IS-04 | ADDRESSED | `:352-353` requires mount isolation, not a userspace path check alone, to block `../`, symlink, and host-path escapes. `:380` includes traversal and symlink attempts. |
| IS-05 | ADDRESSED | `:341-346` denies fork, clone, and execve, and rejects pickle, arbitrary-object deserialization, `eval`/`exec`, and worker-selected dynamic imports. `:380` tests pickle, dynamic import, and a child process. |
| IS-07 | ADDRESSED | `:357-360` requires a later FMP/Finnhub broker to refuse redirects, URL userinfo, and worker-supplied hosts, and to block loopback, private, link-local, and metadata destinations. Defining that denial does not enable the broker. |
| IS-10 | ADDRESSED | `:289` requires owner-set finite local report and diagnostic lifetimes and forbids cloud retention. `:351` names `~/.finrobot` as a denied non-product store. Expiration cannot delete core data or unrelated user reports. |
| HP-04 | ADDRESSED | `:148-150` denies synthetic secrets at admission and says content detection is not a data-loss control. `:349-351` names the secret paths. `:374` requires those secrets to be absent from every channel and every simulated LLM payload. |
| HP-05 | ADDRESSED | `:148-149` denies a secret without rewriting the exact stored criteria snapshot. `:374` requires that snapshot to stay unrewritten and the secret to stay out of prompt, log, and payload channels. |
| HP-06 | ADDRESSED | `:141` says this PoC never reads actual holdings or the user's real database. `:381` requires an isolated synthetic SQLite image to be identical before and after. |
| RC-06 | ADDRESSED | `:394-395` says local completion, timeout, crash, UI disconnect, and closing a stream do not release the reservation or settle the run. `:379` tests UI disconnect and stream close. |
| RC-07 | ADDRESSED | `:79` and `:263-264` forbid automatic retry, replay, and resume. `:399-400` forbids replay, reset, and a double release. The concrete ceiling that used to sit under this row is gone; see B-3. |
| PS-03 | ADDRESSED | `:159` and `:289` require an owner-set diagnostic and report retention lifetime. `:248` keeps raw prompts out of the canonical record. |
| PS-05 | ADDRESSED | `:248-249` excludes raw prompts, chain-of-thought, tracebacks, secrets, and private text. `:374` is the per-channel synthetic-secret control. |
| FB-02 | ADDRESSED | `:47` says AI stays disabled by default. `:213-215` gives unset configuration and an absent package a disabled record and no worker. `:372` requires cold startup with no cost reservation or dispatch. |
| FB-03 | ADDRESSED | `:49-50` forbids the core surfaces from importing agent or upstream packages or acquiring agent credentials. `:372` is the cold-startup control. |
| FB-04 | ADDRESSED | `:57-58` says failure cannot modify holdings or watchlists or reset the budget. `:263` forbids automatic retry. `:381` compares core bytes before and after failure. |
| FB-05 | ADDRESSED | `:54` authorizes no core pin change. `:57-58` says disablement cannot erase local user reports. `:381` includes pin and asset metadata and report preservation. |
| FB-06 | ADDRESSED | `:55-57` names editing, preparing, outdating, clearing, navigating, and reloading as inert and request-free. `:372` attaches the no-request result to those editor actions. |
| TF-02 | ADDRESSED | `:381` specifies an isolated synthetic SQLite database for the preservation cases and forbids reading the user's database. |
| TF-04 | ADDRESSED | `:349` denies `.env`/dotenv discovery and the OS keyring. `:380` requires those canaries. |
| AB-01 | ADDRESSED | `:16`, `:281`, and `:384-386` state per-run and per-day dollar caps with no amount and no numeric default. Dollar amounts stay unset. See B-1 and B-3. |
| AB-03 | ADDRESSED | `:154-160` is a rights table. Evidence-to-model status is unverified. A source license or NOTICE is not data or model permission. |
| AB-06 | ADDRESSED | `:157` leaves model retention, training, deletion, subprocessors, and pricing unverified, and assumes no training opt-out. Local report retention is `:159`. |

## Former PASS rows

None of the thirty-nine PASS rows from the `fcfa1648` review regressed.
Current anchors:

| Row | Still holds at `9e29e54` |
| --- | --- |
| SA-01 | `:37-38` forbids install, import, dynamic load, execute, vendor, and copy. `:380` requires a denial canary. The diff adds no dependency file. |
| SA-02 | `:35-40` keeps the pin reference-only and requires a new owner decision before any load. |
| SA-04 | `:5-11` is **PROPOSED**. Publication, merge, or green tests do not authorize execution. `:405` still requires explicit owner acceptance. |
| SA-05 | `:34` and `:54-55` keep approved dependencies and authorize no core pin change. Image Python 3.11/3.12 at `:325` is the sandbox image. `pyproject.toml` is outside the diff. |
| SA-06 | `:54-55`, `:165`, and `:197` add no financial formula, market universe, or ranking metric. |
| SA-07 | `:70` keeps strings as data. `:188-190` forbids a trade, an instruction, and a threshold change. `:364-366` requires the forbidden effect itself to fail the control. |
| SA-08 | `:414-417` says repository checks do not prove isolation or the negative controls, and that no PoC was executed. |
| EN-01 | `:81-86` binds `criteria_snapshot` to the ADR-0018 envelope. `:68-70` rejects unexpected fields and forbids repair. `m10_synthetic_run` at `:72` is the wrapper. |
| EN-04 | `:55-57` keeps preparation inert. `:82` stores `all` or `any`. `:94` does not pass the prepared envelope through `prepareCriteria`. |
| EN-05 | `:90-91` preserves duplicates, order, and context. `:224` and `:238` keep row order. |
| EN-06 | `:68-69` rejects unknown versions without dropping the rest of the record. `:92-93` rejects unpaired surrogates without normalizing other Unicode. |
| FQ-01 | `:170-175` requires bound identity and mandatory evidence, leaves unknown labels unverified, and withholds a false citation. `:375` is the control. |
| FQ-02 | `:184-185` sets `is_qualification: false` on the opinion object. `:177-182` keeps candidate qualification distinct from run status. |
| FQ-07 | `:175` withholds unsupported facts. `:182` says partial candidates are not a complete search. `:189-190` forbids a criterion change. |
| IS-02 | `:329-330` blocks the experiment when the reviewed image is absent. `:355` refuses execution when a negative control fails. |
| IS-06 | `:332` sets network none. `:341` and `:354` deny sockets, DNS, IPv4, IPv6, loopback, and proxy. No permitted host is selected. |
| IS-08 | `:45` leaves the real-tool allowlist empty. `:347` names yfinance, EDGAR, Adanos, and Alpha Vantage as excluded. |
| IS-09 | `:54-58` and `:189` introduce no trade and no holdings write. |
| HP-02 | `:118-122` is an explicit field list. It is not a home mount and not a serialized portfolio object. |
| HP-07 | `:143-145` and `:158` forbid holdings transmission to any LLM, including indirect disclosure, with no opt-in. |
| RC-02 | `:390-391` gives unknown price, version, currency, hidden fees, or an unenforceable maximum zero billable dispatches. That is a refusal, not a price of zero. |
| RC-05 | `:253` can cancel pending work without dispatch. `:311-313` stops admission and reaps the worker. The charge outcome is now B-1 rather than an open question. |
| RC-08 | `:284` says no upstream rate bucket or model context size is a default. `docs/milestones/m10-finrobot-safety.md:274` at this commit still says the library default is not an accepted cap. The 120/min buckets at `:285-287` of that safety file remain a description of pinned code. |
| ZB-01 | `:42-45` and `:290` keep this mode synthetic, with zero real network, provider, model, token, and currency use. |
| ZB-02 | `:141` reads no actual holdings database. `:290` and `:366` forbid live billing and host secrets. |
| ZB-03 | `:60-63` and `:416-417` say a documentation result does not prove cost enforcement or authorize live activation. |
| ZB-04 | `:21` and `:39-40` retire #197 Phase B, including fake-data execution, and schedule no import. |
| ZB-06 | `:44-45` rejects a live fallback. `:355` stops when a negative control fails. The ADR remains proposed at `:5`. |
| PS-01 | `:167-168` binds fixture identity, digest, and the three timestamps. Display references stay `fixture:` IDs. `:67` keeps the records internal. |
| PS-02 | `:174-175` withholds a relevant-looking citation that does not support the claim. |
| PS-04 | `:111-112` fixes `2026-01-15T12:00:00Z` and says receipt is not publication. |
| PS-06 | `:256-258` requires full coverage and successful cleanup for both completed statuses. `:263` keeps partial and cancelled evidence labeled incomplete. |
| PS-08 | `:67` and `:54` keep the records internal and add no public API, schema, or migration. |
| TF-01 | `:111-114` fixes the civil cutoff, forbids a current-date lookup, and separates scripted clocks from the real monotonic watchdog. |
| TF-03 | `:332`, `:341`, and `:354` deny the network and socket calls. `:366` forbids a live network in the controls. |
| TF-05 | `:364-366` requires each negative control to detect the forbidden effect, using disposable canaries only. |
| TF-06 | `:414-417` says pytest, Ruff, mypy, and pip check do not prove the sandbox, and that no provider operation was run. |
| AB-05 | `:143-145` separates the local projection from provider transmission. |
| AB-07 | `:5-11` and `:405-412` keep the ADR unaccepted. Opening or merging the pull request is not acceptance. `:412` says this PoC is not live activation or M10 completion. |

HP-07 and AB-05 are stronger than the earlier pass: the transmission ban now
says there is no opt-in exception. IS-08 now names the pinned default tools.
SA-05 still does not change the application pin.

## Policy checks requested by #205

Exact criteria. `:81-96` copies the ADR-0018 envelope: schema version 1, kind
`user_stock_criteria`, match `all` or `any`, and ordered range or text rows.
The grammar, 128-character plain decimals, 1–20 rows, and the 80/256 UTF-16
limits are restated. `:94` does not hand that prepared envelope to draft-only
`prepareCriteria`. The comparison sentence is the EN-02 remainder above.

Holdings. `:118-150` allows tickers and accepted portfolio weights only.
Weight is the existing FC-051 figure, or null when no accepted weight exists.
Nothing in that projection, and no derived description of it, may be sent to
any LLM. The prohibition is unconditional in this contract.

Opinion. `:184-191` is the label, the Buy, Hold, or Avoid verdict, a reason,
and a ban on numeric price targets and forecasts.

Daily suggestion. `:193-202` is one deterministic pick per day from the user's
watchlist, using factual criteria the application already computes. The agent
writes only the explanation. Empty input does not manufacture a suggestion.
The selector and the day boundary are not invented here.

Statuses. `:209-211` is the canonical eight. `:258` reserves "no candidates
found" for `completed_empty`. `:213-215` uses `disabled` when the path is not
active.

Limits. `:269-296` requires owner-set finite values and states that this ADR
supplies no replacement numeric defaults. Missing dollar caps disable billable
paths without inventing an amount. `:290` keeps this PoC at zero real
requests, tokens, and cost.

Reservation and settlement. `:384-403` reserves the full estimated run maximum
against both the per-run and per-day caps before the first billable call.
Settlement happens only when the provider usage report matches or is within
that reservation. A finished local task, a crash, a disconnect, or a missing
usage report does not settle it.

Evidence and retention. `:154-160` limits evidence to the user's own FMP and
Finnhub data under existing terms and keeps reports on the machine. Other
sources and publication rights stay unknown and block that path. The PoC
itself uses fictional fixtures, not live calls.

Core fallback and negative controls. `:47-58` and the groups at `:369-382`
specify the core-survival rule and a negative control for each listed group.
`:364-366` says those controls have to detect the forbidden effect. `:416-417`
says they were not executed for this pull request.

The shared paragraphs added beside the ADR, in `SRS.md`, `docs/CURRENT_STATUS.md`,
`docs/adr/0017-user-criteria-taurus-discovery.md`, and `docs/milestones/m10-plan.md`
at this same commit, point at ADR-0020 and leave acceptance, configuration,
and isolation as separate gates. They do not reopen a resolved decision and
they do not choose a number. This review does not edit those files.

## Historical text that is not a new contract finding

`docs/milestones/m10-finrobot-safety.md:468-474` at this commit still says D9
is open and that an in-flight charge is part of that open decision. That
paragraph is the earlier #198/#199 gap list. The revision's only safety-file
edits are the recoverable-exception erratum at `:261-266` and the secret-store
erratum at `:475`. `:27-28` of the revised ADR says those earlier open-D9
statements are superseded where ADR-0020 differs. They are not scored again
as contract policy.

## What remains unproven

The sandbox, image digest, seccomp profile, budget ledger, and negative
controls are specified and unexecuted. `:328-330` and `:414-417` say the same.
A green documentation diff is not a PoC run. Owner acceptance of ADR-0019 has
not been given.

## Remaining gates

Implementation:

- bounded validator, Linux supervisor, and fake dispatch against the internal records
- selector, tie-break, and day-boundary behavior for the daily suggestion, without a new ranking metric
- day-boundary accounting for the per-day dollar cap
- audited pricing and ledger, including the fake-ledger races at `:402-403` before any live use
- production universe and predicate meanings

Configuration:

- explicit owner acceptance of ADR-0019
- an owner-set finite resource profile, including the per-run and per-day dollar amounts, with no default supplied by this review
- a reviewed local image digest, libseccomp bootstrap, and syscall profile

Rights:

- model purpose, transmission, retention, training, deletion, subprocessors, and pricing remain unverified, so evidence-to-model stays disabled
- any source other than the user's own FMP and Finnhub data, and any publication or redistribution of reports, stays blocked
- a future FMP/Finnhub network broker is specified only as a denial list and is not chosen or enabled

Zero-cost synthetic mode stays first. Billable paths stay disabled until the
dollar caps are configured. No live activation follows from this review.

## Recheck of `3196111` — 2026-10-20

Codex pushed
[`31961118859620e0425294e66e179e02466149c2`](https://github.com/daniilnahl/Stock-Tracking-App/commit/31961118859620e0425294e66e179e02466149c2)
on `codex/192-no-import-poc-contract` after the review above. That commit is
the current head of
[PR #202](https://github.com/daniilnahl/Stock-Tracking-App/pull/202). Git
records the author as daniilnahl. This review did not edit that branch.
The contract at that head is
[`docs/adr/0019-m10-feasibility-isolation.md`](https://github.com/daniilnahl/Stock-Tracking-App/blob/31961118859620e0425294e66e179e02466149c2/docs/adr/0019-m10-feasibility-isolation.md).

The diff from `9e29e54` to `3196111` is one file, three insertions and one
deletion. No other checklist sentence changed. Former lines 1–33 keep the
same numbers. Former lines 34–90 move down by one. Former line 91 is now
lines 92–93. Former lines 92–417 move down by two. The earlier sections of
this file remain the record for `9e29e54`.

| Row | Result at `3196111` | Who | Evidence |
| --- | --- | --- | --- |
| SA-03 | ADDRESSED | Codex | `:34-41`. Taurus remains the product label under ADR-0017. FinRobot stays reference-only at `:36-39`. TradingAgents stays excluded at `:40`. The three facts are in the draft scope section. The label is not equated with importing FinRobot. |
| EN-02 | ADDRESSED | Codex | `:88-93`. Endpoints stay exact strings, signed zero and trailing zeros are preserved, and minimum <= maximum uses exact decimal-string comparison only, per ADR-0018, with no float conversion or rounded comparison. `:373` still requires plus, exponent, NaN, whitespace, and signed-zero/precision cases to fail. |

No regression against the other 79 checklist rows, ADR-0020, or ADR-0018.
The diff does not reopen an accepted decision and does not introduce a
numeric cap. Per-run and per-day caps remain owner-set with no numeric
default (`:283`, `:298`). Proven-unused release stays forbidden (`:401`).

**Final verdict: PASS with limitations.**

SA-03 and EN-02 are no longer actionable. Every former FAIL and PARTIAL row
is addressed at `3196111`. The thirty-nine former PASS rows still hold, at
the line offset above. The limitations that remain are the ones already
recorded: this is a documentation reading, not owner acceptance of ADR-0019,
and the sandbox, budget ledger, and negative controls have not run. Current
locations of that limit are `:330-332` and `:416-419`. The implementation,
configuration, and rights gates in the previous section still apply, with
the same two-line offset for any `9e29e54` citation from line 92 onward.
