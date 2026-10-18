# ADR-0019: Proposed no-import, zero-billable M10 synthetic PoC

## Status and authority ledger

**PROPOSED — specification change for owner review, 2026-10-18.** This record
addresses [#192](https://github.com/daniilnahl/Stock-Tracking-App/issues/192).
Its MUST/SHALL language defines the proposed experiment only after explicit owner
acceptance. Publication, merge, tests and prior assessments do not accept this
ADR, authorize execution or enable production M10. No runtime/schema is added.

| Authority / evidence | What is settled or recorded | What remains proposed |
| --- | --- | --- |
| [ADR-0017](0017-user-criteria-taurus-discovery.md), [ADR-0018](0018-custom-criteria-editor.md) | M10 discovery ownership and exact nonexecuting descriptive criteria | Backend execution, predicates, discovery universe and qualification |
| [Merged plan](../milestones/m10-plan.md), [#198/#199 policy record](../milestones/m10-finrobot-safety.md#authority) | Owner recorded no FinRobot import/loading; Linux-only sandbox, Windows via WSL/Docker; local stored-holdings visibility; scoped research/suggestion opinions | Enforcing those policies; exact projection and opinion output boundary below |
| [#197 assessment](../milestones/m10-finrobot-feasibility.md) | Pinned static inventory; no installed/executed upstream | Its earlier actual-V2 Phase B is superseded by recorded no-import policy |
| [#190 criteria proposal](../milestones/m10-criteria-evidence.md), [#191 safety proposal](../milestones/m10-safety-assessment.md) | Reviewed input findings, not accepted executable contracts | This ADR's narrower synthetic mechanics, not their production activation |
| D9 pricing/cancellation | Pricing and uncertain in-flight charge decisions OPEN | All live/billable execution BLOCKED; future reservation discussion is not resolution |

Baseline `02815554e204d36809da62775b22a552fec8a257` contains required owner-merged
#190/#191/#197/#198 findings. Their verified merge/CI evidence is recorded by the
coordinator; an administratively open assessment issue is not a missing merge.
The owner's later policy recorded in merged #199 takes precedence over earlier
V2 execution recommendations and blanket exclusion of local holding fields.
Original owner-comment quotations were not independently verified here; this ADR
uses the merged policy record, not new quotations or inferred consent.
[AGENTS.md](../../AGENTS.md), [SRS](../../SRS.md), [financial definitions](../FINANCIAL_CALCULATIONS.md)
and [TESTING.md](../TESTING.md) remain controlling outside the proposed changes.

## Decision proposed and alternatives

Implement owned Python agents and an internal adapter using only this app's
approved dependencies/stdlib. FinRobot commit
[`2717499b8e30f242640af08c4ad9afd1113c2d45`](https://github.com/AI4Finance-Foundation/FinRobot/commit/2717499b8e30f242640af08c4ad9afd1113c2d45)
is reference design only. Do not install, import, load, execute, vendor or copy
FinRobot V0/V1/V2 code, instructions, skills, assets or dependencies. TradingAgents
is excluded. No proof that no-import implementation is impossible exists; only
such proof plus a new owner decision could reopen upstream loading. There is
no Phase B importing FinRobot under this ADR.

| Alternative | Proposed disposition |
| --- | --- |
| No-import owned synthetic agents with fixture/fake ports | SELECT for this bounded PoC; demonstrates owned boundary mechanics only |
| FinRobot package, vendored subset or extracted upstream runner | REJECT under recorded owner policy, including execution with fake data |
| Same-process worker sharing tracker environment/data | REJECT; cannot demonstrate independent filesystem/egress/process denial |
| Upstream desktop/server, live search/model or paid broker | OUT OF SCOPE and blocked, not a fallback if synthetic work fails |

The experiment is finite synthetic selection plus separately labeled fake
opinion. It proves neither market discovery nor investment performance, vendor
rights, production cost enforcement or a complete M10 product. No public API,
CLI flag, browser fetch, persistence migration, core dependency/pin change or
financial formula is authorized. Current criteria preparation remains inert.

## Proposed internal version-1 data contract

These are internal test/worker records, not public API/OpenAPI models or a
production serialization promise. Reject unknown versions/kinds, duplicate JSON
keys, unexpected fields, malformed Unicode/types and oversize bytes before any
worker starts; never repair, truncate or drop input. A rejected record is admission
failure, not an empty search. All strings are data, never code, URLs or policy.

The input object has exactly `schema_version: 1`, `kind: "m10_synthetic_run"`,
`run_id`, `case_id`, `criteria_snapshot`, `criteria_sha256`,
`fixture_manifest_sha256`, `holdings_projection`, `civil_cutoff`, `binding_sha256`.
`run_id` is `poc-01` through `poc-10`; each case has one immutable manifest ID.
IDs associate records only, not paths/commands; one invocation is one session.
A second invocation is a new deliberately authorized experiment, not auto-resume.

`criteria_snapshot` is the exact ADR-0018 prepared envelope: version/kind,
all/any and ordered range/text rows. Independently revalidate its exact keys,
1–20 rows, lengths, control restrictions, decimal grammar/inclusive ordered
bounds and null rules. Preserve all strings, signed zero, trailing zeros,
duplicates and units/context. Count text lengths as UTF-16 code units to match
the current editor, not Python code points. Reject unpaired surrogates explicitly
as new internal transport admission; do not normalize otherwise valid Unicode.
Do not pass a prepared snapshot to the existing draft-only `prepareCriteria`.

Canonicalization for this internal version is JSON with sorted ASCII field
names, separators `,` and `:`, ASCII escaping (`ensure_ascii=True`), no whitespace
or trailing newline, and `allow_nan=False`; UTF-8 encode those bytes. Arrays retain
order; strings retain contents and are never decimal-parsed for serialization.
Only declared integer fields use JSON numbers; booleans are not integers.
Hash means lowercase hexadecimal SHA-256 over those exact bytes. Compute
`criteria_sha256` over the snapshot. The manifest is a canonical ordered list of
fixture relative IDs, SHA-256 byte digests and fixed expected case specifications;
its digest binds every fixture, fake transcript, predicate, clock and coverage.
Compute `binding_sha256` over the entire input with only `binding_sha256` omitted.
Recompute all digests before launch and before publication; a mismatch fails.
Hashing binds bytes, not evidence truth, authenticity, consent or freshness.

The fixed civil cutoff is `2026-01-15T12:00:00Z` for all ten synthetic cases.
Evidence effective/publication/receipt times are fixed manifest values; receipt
never substitutes for publication. No current-date access or random model output.
The supervisor samples a real Linux monotonic clock for enforcement; test state
machines additionally inject a scripted monotonic clock to exercise exact deadline
and race boundaries. Fake time cannot replace the real worker watchdog.

## Synthetic holdings projection only

Read [WatchlistEntry/Record](../../src/stock_tracker/persistence/models.py),
[service records](../../src/stock_tracker/services/models.py),
[serialization callers](../../src/stock_tracker/api/serialization.py) and
[exact/duplicate tests](../../tests/test_api_serialization.py).
The actual holding contract is finite nonnegative Decimal quantity/cost;
`average_cost` may be null only at zero quantity. Criteria's signed grammar does
not authorize negative nonzero holdings, shorting or a new cost convention.

`holdings_projection` is null or an ordered list of at most six synthetic rows,
with exactly `namespace`, `ordinal`, `stock`, `quantity`, `average_cost`.
`stock` has exactly `symbol`, `exchange`; exchange may be null. Namespace is one
of the two existing namespaces, ordinal a nonnegative integer preserving source
position. Each `(namespace, ordinal)` occurs once; repeated symbols/identities
remain separate rows. Preserve row order. Do not invent resolved exchange or use
Stock equality to merge rows. Synthetic identifiers are manifest-owned strings.

Quantity and present cost are strings equal to `str()` of the manifest's finite
nonnegative Decimal, preserving exponent form, significant zeros and signed zero;
null is not zero. No float conversion, rounding, derived cost basis or valuation.
PoC numeric strings are bounded to 128 ASCII characters and must roundtrip exactly
through that declared representation. This projection is independent of criteria's
plain-decimal grammar. Nonzero quantity with null cost is rejected.
Omit Stock.name, current price, free metadata, portfolio/account identifiers,
annotations, settings, credentials, key objects, provider objects and core paths.

The local owner grant permits a future explicit stored-holding projection, not a
home mount, actual-database read in this PoC or arbitrary private text in criteria.
PoC fixtures are fictional and no actual holding is acquired. This ADR does not
authorize outward transmission; real provider-specific purpose/opt-in and data/
model rights remain gates. Private/secret-looking test text is refused by admission
and excluded from diagnostics. No claim that content detection solves data loss.

## Identity, evidence and candidate qualification

A case manifest stipulates a finite universe of at most three fictional security
IDs and explicit synthetic predicates. These define no financial metric or market
universe. Each captured evidence record binds `evidence_id`, `security_id`, row
ordinal, predicate ID, exact scalar/text value, units/context, effective time,
publication time, receipt time and fixture digest. No fetched URL or external ID
is required; display references are validated `fixture:` IDs, never auto-navigation.
Evidence may support only its bound identity, row, period and synthetic meaning.

Before row combination, require unique manifest identity, compatible/current core
fixture inputs and every manifest-mandatory evidence item. Unknown identity,
contradictory/stale core inputs or absent mandatory evidence blocks qualification
regardless of `any`. No production mandatory-input/freshness policy is inferred.
A fixture predicate may compare exact decimal strings numerically without changing
the original strings. Unknown financial labels/units or unresolved predicate means
unverified; do not invent semantics, currency, EPS basis, ratios or FX.

Row outcomes are `match`, `nonmatch`, `unverified`, with sanitized reason/evidence
IDs. `all`: all match qualifies; any nonmatch gives nonmatch; otherwise unverified.
`any`: at least one match qualifies only after prerequisites; all nonmatch gives
nonmatch; otherwise unverified. Report every row and gap. A real reference that
does not support the asserted claim is insufficient. Withhold unsupported facts.

Candidate state `qualified`/`nonmatch`/`unverified` is separate from run state and
coverage. A partial run can retain validated candidates without claiming a complete
search. Publish an opinion only as a separate optional `synthetic_model_opinion`
section with `synthetic: true`, `is_qualification: false`, fixed fake text and its
bound run/snapshot. Scoped research/suggestion opinion is recorded policy; no
ranking, daily scheduler, real target calculation, suitability claim or trade is
introduced. Fake opinion cannot assert an unsupported factual criterion match.

## Lifecycle and output boundary

Internal output has exactly version/kind (`1`, `m10_synthetic_result`), run/case IDs,
input `binding_sha256`, snapshot/manifest hashes, `status`, `coverage`,
`candidates`, `evidence`, `opinion`, `counters`, `reason`. Candidate/evidence entries use the
allowlists above; no arbitrary model fields/prompts/traces enter output. Output
is canonical JSON with no raw exception, private text or chain-of-thought.
Validate schema, byte limits, IDs/hashes, support and counters before publication.
Each candidate has exactly `security_id`, `qualification`, `prerequisite_gaps`,
`row_results`; each row has `ordinal`, `state`, `evidence_ids`, `reason`.
`opinion` is null or exactly `kind: "synthetic_model_opinion"`, `synthetic: true`,
`is_qualification: false`, and `text` (fixed manifest text, <=512 UTF-16 units);
its binding is inherited from the enclosing run, not a model-selected identity.
`counters` has exactly nonnegative integer `fake_model_attempts`, `fixture_attempts`,
`input_bytes`, `output_bytes`; the supervisor owns those values. Coverage has
exactly `universe_ids`, `attempted_ids`, `evaluated_ids`, `unresolved_rows`,
`stop_reason`. Reasons/gaps are finite manifest codes, not raw worker prose.
`evidence` is an ordered list of <=60 records with exactly `evidence_id`,
`security_id`, `ordinal`, `predicate_id`, `value`, `unit`, `context`, `effective_at`,
`published_at`, `received_at`, `fixture_sha256`. IDs are manifest ASCII strings
<=64 characters; ordinal is an integer 0–19; value is text <=256 UTF-16 units
(numeric value additionally uses the criteria decimal grammar/128-character cap).
Unit/context are <=80 UTF-16 units; timestamps are manifest UTC second strings;
digest is lowercase 64-character SHA-256. Candidate/row reference IDs must resolve
to these captured records and be unique within each reference list. No extra
evidence, candidate or row beyond its manifest scope is admitted.
Evidence content is copied only from supervisor-owned immutable manifest records;
the worker may return IDs, never create or replace captured observations. Supervisor
checks every referenced identity/ordinal/predicate/cutoff and fills the output list.
Coverage ID fields are unique ordered lists of <=3 manifest security IDs with
evaluated subset of attempted subset of universe; universe equals the case manifest
order/set. `unresolved_rows` is a <=60 list of exact objects `security_id`, `ordinal`,
`reason`, unique by security/ordinal and bound to a declared row. Candidate IDs are
unique universe members; every emitted candidate has exactly one row result per
snapshot ordinal, in original order. `prerequisite_gaps` is a unique list of case
manifest codes; nonempty gaps force unverified qualification. Coverage, prerequisites
and row states are recomputed by the supervisor from its fixture records/counters,
not accepted from model assertions. Completed implies evaluated equals universe,
no unresolved rows/gaps and all contracted predicates evaluated.
`output_bytes` counts the full emitted record/pipes including this counter;
supervisor serialization resolves its decimal digit width before enforcing cap.

Admission rejection/disabled means no run or worker; return bounded safe status
outside the result record. For admitted cases: `pending` → `running` → exactly
one terminal `completed`, `partial`, `failed`, `cancelled`. Cancellation of pending
work goes directly to cancelled without dispatch. No retry/resume or terminal
rewrite; immutable diagnostics may note a later infrastructure failure.
`completed` requires all case universe/predicates evaluated and successful cleanup.
Only completed with zero qualified candidates and zero unverified evaluations may
say bounded no candidates found. Unresolved evaluation/coverage or normal budget
exhaustion is partial; invalid output/invariant breach is failed; cancellation is
cancelled. If both occur, record the first supervisor-observed terminal trigger;
failed cleanup overrides any provisional success with failed infrastructure status.

Coverage carries manifest universe IDs, attempted/evaluated IDs, unresolved rows
and stop reason. A completed case may have candidates; no ranking is applied.
Supervisor validates provisional output in memory, terminates/reaps/cleans the
worker, then finalizes terminal status. Partial/cancelled validated evidence may
be retained as such; they never become a completed report. Runtime/publication
errors never write core storage or trigger discovery fallback.

## Limits, dispatch and cancellation contract

One session executes ten predeclared cases sequentially; one worker/run per case,
no concurrent workers, no additional cases or retries. Caps are inclusive:

| Resource | Per case | Whole session |
| --- | --- | --- |
| Candidates / criteria | <=3 fictional candidates; 1–20 criteria | Ten fixed manifests, no expansion |
| Fake operations | <=5 fake-model attempts; <=10 fixture lookup attempts | <=50 and <=100 respectively |
| Input / output | <=65,536 bytes each; input includes all replies, output all frames/logs/final record | <=655,360 input and <=655,360 output bytes |
| Time | <=60 real monotonic seconds including launch and cleanup | <=600 seconds including preflight and all cleanup |
| Scratch | <=256 KiB worker tmpfs; shared allocation below | <=1,048,576 live/retained scratch bytes |
| External use | 0 network/provider/model requests; 0 real tokens/currency | Same zero budget; no credentials |

Start session deadline before preflight. At each case start (before launch), set
case deadline to min(session deadline, start+60s). Last dispatch time is deadline−5s;
no new case starts with <5s remaining. Supervisor checks noncancelled state,
remaining time and counters atomically before each fake operation, increments
attempt counters before dispatch, and rejects the next attempt beyond the cap.
Rejected/failed attempts consume their admitted slot; retry does not reset it.
Only supervisor-owned manifest-keyed scripted fake functions are capabilities;
no URLs, commands, model SDKs, shell tools or worker-selected destinations.
Worker stdout sends bounded canonical JSON request/provisional-result frames;
supervisor validates binding/operation/fixture IDs, then returns scripted replies
on stdin. Each frame has a newline delimiter, counted as transport bytes. No raw
fixture store is visible to the worker. Worker frames/stderr together get 32 KiB;
the supervisor final record gets 32 KiB, jointly within 64 KiB. Initial envelope plus
all replies must fit 64 KiB; preflight checks worst-case manifest sizes before launch.

At last-dispatch time or cancellation, stop admission immediately; kill the
container/process group, reap it and remove only its owned disposable scratch.
The five reserved seconds are the cleanup window, not extra time beyond 60s.
If termination/reaping/cleanup cannot finish by deadline, session fails and admits
no more cases; do not claim an enforced deadline or release the single-worker slot
while execution may survive. Supervisor failure requires a separately verified
runtime timeout/cleanup watchdog, otherwise preflight refuses to start.

Scratch budget partitions: 256 KiB maximum worker tmpfs, 640 KiB aggregate retained
case outputs (including logs) and 128 KiB supervisor scratch/metadata = 1 MiB.
Readonly immutable code/fixture/image bytes are not scratch. No unbounded writable
runtime logs or container layers; disable runtime log driver and capture bounded
pipes. Exceeding output/space quota terminates the case with safe failure, not
silent truncation. These are live/retained bytes, not a promise about cumulative
bytes overwritten. Delete temporary case files only after verifying ownership,
resolved path and no symlink escape; never evict user reports/data to meet caps.

## Proposed Linux mechanism and availability gate

Use a trusted single-process host supervisor and an already available Linux Docker
runtime (native Linux or Linux through WSL/Docker on Windows). Require an approved
local image by SHA-256 digest, pull disabled, containing only reviewed Python
3.11/3.12, owned worker code/bootstrap and synthetic denial canaries; no evidence
fixtures or manifest. The trusted supervisor alone owns that immutable store and
validates its hashes before launch; the worker receives only bounded input/replies.
No image build/pull, runtime/WSL/Docker installation or system change is authorized
by this ADR. Image digest, inventory and bootstrap review are acceptance artifacts;
if absent, experiment remains blocked rather than using an improvised image.

Proposed container settings: network none; read-only root; nonroot UID/GID;
no host binds, devices, host namespaces, Docker socket or privileged mode;
capabilities dropped; no-new-privileges; PID limit 1; memory 128 MiB/no swap;
CPU quota 1; file-descriptor limit 32; one noexec/nosuid/nodev 256 KiB scratch tmpfs.
Input/replies use bounded stdin, output bounded pipes; home empty/read-only, no
writable /tmp (scratch is a distinct mount) or inherited FDs beyond those pipes.
Fixed allowlisted environment
only (locale/Python encoding); no proxy, provider, FINROBOT, API-token or path vars.
Python startup excludes user site/custom startup paths and bytecode writes.

Before owned worker entry, the audited bootstrap installs an irrevocable seccomp
allowlist permitting necessary interpreter/file-on-image/pipe/clock operations,
while denying socket/network calls, fork/vfork/clone/clone3, execve/execveat,
ptrace, mount and privilege/namespace operations. Bootstrap startup may precede
this filter, but processes no case input and invokes no agent code before it.
Missing libseccomp, unsupported syscall architecture, filter failure, missing
quotas/timeout control or failed negative controls means no worker execution.
Exact syscall profile/image implementation is a separately reviewed prerequisite;
this proposal does not claim those denials already work. Test host-file canaries,
DNS/IPv4/IPv6/loopback/proxy, child/re-exec and quota escapes before case dispatch.

## Verification, future paid calls and delivery gates

Each row needs a negative control showing the test would detect the forbidden
effect (e.g. a disposable relaxed test sandbox/counter implementation fails),
without ever exposing host secrets, a real network or live billing.
Each of ten fixed case manifests may contain multiple predeclared subscenarios;
all subscenarios share that case's single worker, counters, bytes and deadline.
The negative-control harness is separate, with the same zero-live-use restrictions;
it must not silently add extra experiment cases or reset their budgets.

| Fixed case | Required observable result |
| --- | --- |
| Exact envelope, duplicates, non-BMP and signed-zero bounds | Same canonical hash/row bindings; reject malformed surrogate/types/version |
| Synthetic holding duplicates, exponent/zero/null cost | Allowlist preserved; negative nonzero/null-invalid cost rejected; no metadata leak |
| Identity collision / `any` row passes but mandatory evidence missing | Unverified candidate; passing optional row does not bypass prerequisite |
| Stale/conflicting evidence / relevant-looking false citation | Unsupported fact withheld; no fabricated qualified result |
| Complete finite empty versus unresolved or interrupted scope | Only first may say no candidates; coverage/status stay distinct |
| Opinion injected into qualification / request to trade or alter threshold | Fake opinion separated; no action, criterion change or new tool |
| Exhaust fake calls/lookups and byte/space quotas | Next dispatch/write refused; no counter reset, truncation or retry loop |
| Cancel before/during operation and at 55s/60s; backward civil clock | Atomic dispatch stop, real monotonic limit, worker reaped before slot release |
| Crash before result/cleanup or supervisor/watchdog failure | No completed publication/replay; fail session if cleanup cannot be proven |
| Import/vendor attempt, home/host read, socket/DNS/child/re-exec | Actual denial, no copied FinRobot/default tools, no real data/network |

D9 remains OPEN. For any future live/billable path, a separate accepted broker
must reserve worst-case charges before every dispatch under the invariant
confirmed charges + outstanding worst-case reservations <= authorized cap,
atomically across runs/restarts. Unknown price/version/currency/hidden-token/tool
fees or unenforceable vendor maxima means zero dispatch. Uncertain sent/accepted
requests remain fully encumbered after cancel/timeout/crash; no automatic replay,
refund or budget reset. Only proven unused reservation may be released under an
accepted settlement policy. This describes a proposal, not pricing/cancellation
acceptance or an implemented ledger. This PoC tests fake counters only.

Next: explicit owner acceptance of this ADR and exact local image/bootstrap plan,
then bounded implementation issues for owned envelope/validator, Linux supervisor/
fake dispatch and independent negative-control audit against stable interfaces.
No import work is scheduled. Real discovery/universe/metric definitions, vendor
rights/provider opt-in, production holdings handling, cadence/ranking, API/UI,
durable storage/retention and live pricing need separate contracts/acceptance.
No live activation or M10 completion follows from passing this PoC.

For this documentation PR run local Markdown/diff/staged hygiene plus canonical
full pytest, Ruff, configured mypy and pip check; no browser build. Repository
checks do not prove the proposed sandbox/negative controls. No PoC, Linux runtime,
upstream or real-data/model/provider operation was executed while writing this ADR.
