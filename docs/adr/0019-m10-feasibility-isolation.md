# ADR-0019: Proposed no-import, zero-billable M10 synthetic PoC

## Status and controlling decisions

**PROPOSED implementation contract, revised 2026-10-19.** Addresses
[#192](https://github.com/daniilnahl/Stock-Tracking-App/issues/192) and the
[#202 review](../milestones/m10-poc-review-202.md) merged in #203.
[Accepted ADR-0020](0020-m10-owner-decisions.md), merged in #204, and the amended
[SRS](../../SRS.md) control. This proposal does not reopen those decisions or
accept their implementation. Its MUST/SHALL language applies to a future accepted
experiment; publication, merge or green tests do not authorize execution.

| Authority | Accepted or recorded input | Remaining gate |
| --- | --- | --- |
| ADR-0017/0018 | M10 discovery ownership; exact nonexecuting prepared criteria | Backend implementation and supported predicate/universe contracts |
| ADR-0020 decisions 1/7 | D9 resolved: owner-configured run/day dollar caps, full run reservation before billing, provider-reported settlement | Numeric configuration, pricing/model review and implemented/audited ledger |
| ADR-0020 decision 2 | Local ticker/portfolio-weight projection only; no holdings to any LLM | Explicit projection/negative-control implementation |
| ADR-0020 decisions 3/4 | Labeled Buy/Hold/Avoid opinion; deterministic daily watchlist pick, explanation only | Selector/day-boundary details and implementation; no new ranking metric |
| ADR-0020 decision 5 | Eight canonical run statuses, including completed_empty and disabled | Proposed internal record/lifecycle below |
| ADR-0020 decision 6 | User's own FMP/Finnhub evidence under existing terms; local-only reports | Any model transmission, other source or publication rights remain blocked/unknown |
| ADR-0020 decision 8 | #197 actual-V2 Phase B retired; its numbers are not defaults | Owner-set resource profile and no-import implementation |
| #190/#191/#197/#198 | Owner-merged static findings, not runtime enforcement | This narrower synthetic contract and independent verification |

#203's checklist and review are dated assessments of head
`fcfa1648a610533664a0a18b646ce0e0f8349235`, not an acceptance of this revision.
This ADR addresses B-1 through B-9 and their partial rows below; it does not
rewrite those historical review verdicts as new test results. The earlier #199
holdings/opinion/open-D9 statements are superseded where ADR-0020 differs.
[AGENTS.md](../../AGENTS.md), [TESTING.md](../TESTING.md) and
[financial definitions](../FINANCIAL_CALCULATIONS.md) remain controlling.

## Proposed decision and core independence

Build owned Python agents/internal adapters with approved dependencies/stdlib.
FinRobot commit
[`2717499b8e30f242640af08c4ad9afd1113c2d45`](https://github.com/AI4Finance-Foundation/FinRobot/commit/2717499b8e30f242640af08c4ad9afd1113c2d45)
is reference design only. Do not install, import, dynamically load, execute,
vendor or copy FinRobot V0/V1/V2 code, instructions, skills, assets or dependencies.
TradingAgents is excluded. #197 Phase B is retired, including execution with
fake data. Reopening upstream loading requires a new owner decision.

Select a synthetic-only owned worker and supervisor-owned fake ports. Reject a
same-process worker sharing the core environment, upstream desktop/server/default
graphs, live search/model/paid brokers and a live fallback when synthetic work
fails. The real-tool/source/model allowlist is empty in this PoC.

AI stays disabled by default. Core startup/help, CLI, authenticated local API,
dashboard, M9 editor and saved holdings MUST operate with the agent package absent,
disabled, offline, limited, incompatible, invalid or failing. They must not import
agent/upstream packages, acquire agent credentials, reserve cost or dispatch work.
Core native Windows operation stays supported; native Windows agent sandboxing
is not required. The future sandbox runs on Linux, including WSL/Docker on Windows.

No public API/CLI flag, core dependency/pin, auth, UI asset, schema/migration,
financial formula or holdings write changes here. Editing/preparing/outdating/
clearing criteria, navigating or reloading stays inert and tab-memory-only under
ADR-0018, with no hidden store or request. Failure/disable cannot erase local user
reports, modify holdings/watchlists or reset budget state.

The PoC proves owned boundary mechanics only: no market discovery, investment
performance, live billing/rights or M10 completion. Owner acceptance of this ADR,
an explicit finite resource profile and the reviewed local image/bootstrap are
prerequisites, not consequences of a successful documentation PR.

## Proposed internal version-1 envelope and binding

These are internal worker/test records, not API/OpenAPI or durable public schemas.
Reject unknown versions/kinds, duplicate JSON keys, unexpected fields, invalid
types/Unicode and oversize transport bytes before launch. No repair, truncation or
dropping input. Strings/IDs are data, never code, policy, URLs or paths.

Input has exactly `schema_version: 1`, `kind: "m10_synthetic_run"`, `run_id`,
`case_id`, `criteria_snapshot`, `criteria_sha256`, `fixture_manifest_sha256`,
`limits_sha256`, `holdings_projection`, `civil_cutoff`, `binding_sha256`.
IDs are nonblank manifest-owned ASCII association tokens, never path components
or dispatch destinations; their lengths obey the owner-set transport profile.
Cases come from a finite declared manifest, not an inherited count of ten.
Each deliberately authorized session binds one immutable profile/manifest; no
automatic retry, resume, manifest expansion or new session on failure.

`criteria_snapshot` is the exact ADR-0018 prepared envelope:
`schema_version: 1`, `kind: "user_stock_criteria"`, `match: "all" | "any"`,
and ordered `criteria`. Range rows have exactly `parameter`, `kind: "range"`,
`unit`, `minimum`, `maximum`; text rows exactly `parameter`, `kind: "text"`,
`value`. Revalidate accepted 1–20 rows, nonblank/control rules, parameter/unit
80 and text 256 UTF-16-unit limits, and 128-character plain decimal endpoints.
Grammar is `-?(0|[1-9][0-9]*)([.][0-9]+)?` with full-string matching; no plus,
exponent, separators, leading zero padding, whitespace, Infinity/NaN or floats.
Null means an absent endpoint, at least one endpoint is present, and inclusive
minimum <= maximum. Preserve exact strings, signed zero, trailing zeros, Unicode,
duplicates, order and context; compare without display rounding. These existing
editor/schema limits are not #197 resource defaults. Reject unpaired surrogates
as internal transport admission, without normalizing other valid Unicode.
Do not pass this prepared envelope to draft-only `prepareCriteria`.
See [editor/callers](../../frontend/src/features/criteria.ts) and
[accepted handoff](0018-custom-criteria-editor.md).

Canonical JSON uses sorted ASCII field names, separators `,`/`:`, ASCII escaping
(`ensure_ascii=True`), no whitespace/newline, `allow_nan=False`, UTF-8 bytes.
Arrays keep order; string contents are never normalized or decimal-parsed for
serialization. Only declared integer fields use JSON numbers; bool is not int.
Hashes are lowercase hexadecimal SHA-256 of those bytes. Compute criteria hash
over the snapshot, limits hash over the complete owner-set profile, and manifest
hash over the ordered fixture IDs, byte digests, expected predicates, fake
transcripts, clocks and case specifications. Compute binding over the entire
input except `binding_sha256`; recompute before launch and publication.
A mismatch fails, never silently replaces an input. Hashing proves binding,
not truth, authenticity, rights or freshness. Later editing marks the prepared
snapshot outdated; no run silently uses the edited draft or mutates the snapshot.

Civil cutoff is fixed synthetic `2026-01-15T12:00:00Z`; every effective/publication/
receipt time is manifest-owned. Receipt is not publication. No current-date
lookup or random model output. Real Linux monotonic time enforces deadlines;
scripted monotonic clocks test exact boundaries/races, not replace the watchdog.

## Local holdings projection: tickers and accepted weights only

The worker-visible `holdings_projection` is null or an ordered bounded list of
objects with exactly `ticker` and `portfolio_weight`. Ticker is the explicit
stored symbol as a data string. Repeated tickers remain separate ordered rows.
Supervisor-only namespace/ordinal/exchange/identity bindings preserve association
and detect ambiguous candidates; they are not fields in the worker projection.
Ticker alone never resolves exchange or deduplicates positions.

Weight is null or the exact `str(Decimal)` value already computed as
`PositionAllocation.weight` under FC-051/ADR-0011, a finite nonnegative
dimensionless ratio; validate it against the supervisor's computed value.
Preserve exponent representation, significant zeros and signed zero; no float,
percentage conversion, new formula, rounding, renormalization or residual
adjustment. Reuse [analytics](../../src/stock_tracker/domain/analytics.py) and
[known-value/null/precision tests](../../tests/test_snapshot_analytics.py).
Incomplete/nonpositive total valuation leaves weights null; zero is not unknown.
Unknown/mismatched currency remains the existing domain error, not invented USD
or a guessed weight. If no accepted weight is available, do not calculate one
from saved display prices or quantities inside the adapter.

No quantity, average cost, cost basis, account/portfolio identifier, free metadata,
Stock.name, price, secret, provider object, core path or generic object crosses
this projection. The trusted fixture builder may use synthetic inputs to the
existing pure analytics calculation; only its ticker/weight projection reaches
the worker. This PoC never reads actual holdings or the user's real database.

Holdings, including ticker/weight projection and derived/disclosing descriptions,
MUST NEVER be sent to any LLM provider. There is no opt-in exception in this
contract. Check prompts, requests, evidence, opinion, errors, telemetry and logs,
not only top-level fields. Provider-bound data is a separately reviewed public
evidence projection, never the local holding object. No provider exists in this
PoC. Synthetic secrets are denied at admission without rewriting the exact stored
criteria snapshot or echoing its content. Content detection alone is not a
data-loss control.

## Evidence rights, qualification, opinion and daily suggestion

| Path | Accepted boundary / current availability |
| --- | --- |
| Evidence acquisition | Only the user's own FMP/Finnhub data under existing terms in future real operation; no other source implied. PoC uses fictional provider-shaped fixtures only, never actual account data or a live call. |
| Evidence to a model | Unverified/disabled: model-specific purpose, transmission, retention, training, deletion, subprocessors and enforceable pricing need review; no chosen model/provider or assumed training opt-out. |
| Holdings to any LLM | Prohibited, including indirect/nested disclosure; local permission is not transmission permission. |
| Report storage | Local only; owner-set diagnostic/report retention lifetime required. No cloud log, publication, redistribution or FinRobot home-directory store. |
| Other sources/publication | Unknown rights block that path. Source-code license/NOTICE is not data/model permission. |

Each fixture has a declared synthetic FMP/Finnhub source label and fake identity.
No fabricated observation is presented as actual provider evidence. Manifest
defines a finite fictional universe, explicit synthetic predicates and mandatory
evidence. These define no market universe, new financial metric or financial
comparison. Each captured record binds identity, criterion ordinal, predicate,
exact value/unit/context, effective/publication/receipt times and fixture digest.
Display references are validated `fixture:` IDs, not navigable fetched URLs.

Before row combination, require unique manifest identity, compatible/current core
inputs and every mandatory evidence item. Unknown identity, contradictory/stale
inputs or absent mandatory evidence prevents qualification even with `any`.
Unsupported units/periods/financial labels/predicates remain unverified; never
invent EPS basis, currency, ratio, valuation, forecast or FX. A relevant-looking
citation does not establish support; withhold unsupported facts.

Row states: `match`, `nonmatch`, `unverified`.
For `all`, all match qualifies, any nonmatch gives nonmatch, otherwise unverified.
For `any`, a match qualifies only after prerequisites, all nonmatch gives nonmatch,
otherwise unverified. Report every row and gap. Candidate `qualified`/`nonmatch`/
`unverified` is distinct from run status/coverage; partial validated candidates
never imply a complete search.

Optional opinion has exactly `kind: "synthetic_model_opinion"`, `synthetic: true`,
`is_qualification: false`, `label: "Research opinion, not financial advice"`,
`verdict: "Buy" | "Hold" | "Avoid"`, and `reason`. Reason is fixed reviewed
manifest text within owner-set output limits. Opinion appears only in research
output or stock suggestion of the day. No numeric price target, forecast,
unsupported factual match, suitability claim, guarantee, trade, instruction or
threshold mutation may appear in any field or nested reason. Reject violating
fake output; do not rely only on a prompt asking the worker to behave.

The stock suggestion of the day is accepted policy: one deterministic pick per
day from the user's watchlist using existing factual criteria the app computes.
Only its explanation is agent-written and follows the label/verdict rules above.
It is separate from AI1031 criteria-driven market search and sector ranking.
No new ranking metric or model-selected winner. Empty/unverified input does not
manufacture a suggestion. Selector/tie-break and day-boundary implementation
details have not been supplied here; they remain explicit implementation gates,
not a reason to describe the accepted cadence as undecided or invent a formula.
PoC uses a manifest-preselected fictional watchlist item/fixed day to test
explanation-only binding; it does not implement scheduling or claim a real pick.

## Internal records and canonical lifecycle

Output has exactly `schema_version: 1`, `kind: "m10_synthetic_result"`, `run_id`,
`case_id`, `binding_sha256`, `criteria_sha256`, `fixture_manifest_sha256`,
`limits_sha256`, `status`, `coverage`, `candidates`, `evidence`, `opinion`,
`counters`, `reason`. Status uses ONLY the accepted list:
`pending`, `running`, `completed`, `completed_empty`, `partial`, `failed`,
`cancelled`, `disabled`. No alternate status for empty success or admission.

Disabled is the same typed record with `status: "disabled"`, zero operation counters,
empty coverage/candidate/evidence lists and null opinion, and launches no worker.
Unset configuration/absent AI leaves the path disabled. A malformed enabled
request is failed with a fixed admission reason and no worker. Before validated
admission, untrusted IDs/bindings/hashes are null rather than echoed. Otherwise
records bind the admitted context; never manufacture a hash from invalid input.
Byte counters still count actual bounded observed/emitted bytes, including a
disabled or failed admission record; they are not falsely reported as zero.
Pending/running are bounded progress records, never a completed report.

Each candidate has exactly `security_id`, `qualification`, `prerequisite_gaps`,
`row_results`; each row exactly `ordinal`, `state`, `evidence_ids`, `reason`.
Evidence has exactly `evidence_id`, `security_id`, `ordinal`, `predicate_id`,
`source`, `value`, `unit`, `context`, `effective_at`, `published_at`,
`received_at`, `fixture_sha256`. Source is `synthetic_fmp` or `synthetic_finnhub`; value is
text or a declared exact decimal string, never float/arbitrary object. Ordinals
bind ADR-0018 rows; times are manifest UTC second strings. Every ID, timestamp,
digest, field type/length and collection cardinality is validated against the
manifest, accepted criteria grammar and configured byte/field limits.
Opinion is null or the exact object above. Reasons/gaps are finite safe manifest
codes except the separately bounded reviewed opinion reason.

Evidence is copied only from immutable supervisor-owned records. Worker returns
IDs, never observation replacements. Verify identity/ordinal/predicate/cutoff and
source on each reference; IDs are unique in each list. Candidate IDs are unique
universe members and each emitted candidate retains every snapshot row in order.
Coverage has exactly `universe_ids`, `attempted_ids`, `evaluated_ids`,
`unresolved_rows`, `stop_reason`; unique ordered ID sets satisfy evaluated ⊆
attempted ⊆ universe, and universe exactly matches the manifest. Unresolved rows
have exactly `security_id`, `ordinal`, `reason`, unique per security/ordinal.
Supervisor recomputes states/prerequisites/coverage from captured evidence and
counters, not worker claims. Nonempty prerequisites force unverified qualification.

Counters have exactly nonnegative integer `fake_model_attempts`,
`fixture_attempts`, `input_bytes`, `output_bytes`, owned by the supervisor.
Canonical JSON contains no raw prompt, chain-of-thought, traceback, secret or
private text. Count every frame/newline, stderr/diagnostic and final-record byte;
resolve `output_bytes`' decimal digit width before enforcing the aggregate limit.
Invalid output/unsupported fact/byte overflow fails; never silently truncate.

Pending may become running, cancelled or failed without dispatch. Running becomes
exactly one terminal completed, completed_empty, partial, failed or cancelled.
Disabled never starts; later explicit enablement is a new run, not rewriting it.
Both completed successes require full valid coverage, no unresolved rows/gaps and
successful worker cleanup. Completed has at least one qualified candidate;
completed_empty has none and may alone say bounded no candidates found.
Unresolved or interrupted coverage is partial, invalid output/invariant breach
failed, requested cancellation cancelled. First supervisor-observed trigger wins,
except failed cleanup overrides provisional success as failed infrastructure.
Validate provisional output in memory, terminate/reap/clean, then finalize exactly
once. Partial/cancelled evidence remains labeled incomplete. No terminal rewrite,
automatic retry/replay/resume or fallback search; later infrastructure diagnosis
does not convert failure into success.

## Owner-set limits and dispatch contract

No #197 numeric charter value is a default, approved cap, duration or case count.
Every applicable synthetic-resource row below requires explicit finite owner
configuration for the accepted experiment. The future live-only dollar/request/
token settings may remain explicitly unset in a synthetic profile; that keeps
billable paths disabled, without inventing amounts or blocking zero-cost mode.
Missing required synthetic settings, bool-as-number, nonfinite, negative,
malformed or inconsistent values refuse execution; no fallback values.
Structural constants such as schema
version, SHA-256 syntax and ADR-0018 grammar are distinct from resource policy.

| Resource-profile fields | Required configuration and validation |
| --- | --- |
| `run_dollar_cap`, `day_dollar_cap` | Owner-set exact dollar amounts required for any billable provider; never inferred from zero-cost mode. Missing means billable disabled. No numeric defaults. |
| `case_count_cap`, `candidate_cap`, `evidence_cap`, `holdings_row_cap` | Owner-set finite positive integers; full finite manifest must fit. The verification groups below do not prescribe a case count. |
| `fake_model_attempt_cap`, `fixture_attempt_cap`, and session aggregates | Owner-set finite nonnegative integers; preflight proves required scenarios fit, and aggregate admitted attempts fit session caps. |
| Future live request/token limits | Owner-set finite request, input/output/hidden-token and aggregate ceilings required before live use; zero real requests/tokens in this PoC. No model context size or upstream rate bucket supplies a default. |
| `case_seconds`, `session_seconds`, `cleanup_seconds` | Owner-set finite positive durations, cleanup strictly less than case/session time; total planned work/cleanup fits session deadline. |
| `input_byte_cap`, `worker_output_byte_cap`, `final_record_byte_cap`, `output_byte_cap`, session byte caps, `field_byte_cap` | Owner-set positive integers; frame/newline/log/final budgets fit aggregate output; envelope plus all replies and case totals fit their run/session caps. |
| `worker_scratch_cap`, `retained_output_cap`, `supervisor_scratch_cap`, `session_scratch_cap` | Owner-set positive byte limits; simultaneous worker allocations + retained outputs + supervisor metadata fit the session cap. |
| `concurrent_worker_cap`, `memory_cap`, `cpu_quota`, `pid_cap`, `fd_cap` | Owner-set finite positive limits compatible with the reviewed bootstrap; no unbounded workers, queues or child processes. |
| `report_retention`, `diagnostic_retention` | Owner-set finite local lifetimes; no indefinite/cloud retention. Scratch is disposable; expiration never deletes core data or unrelated/user-owned reports. |
| Real network/provider/model calls, real tokens/cost | Exactly zero for this synthetic mode by scope; this is not configured live funding or a price assumption. |

The trusted supervisor owns the profile, validates relations/worst-case serialized
sizes and binds its digest before admission. Profile input is local configuration,
not model instructions. A cap that cannot be enforced by the reviewed mechanism
refuses execution. No experiment runs until owner-set values and implementation
are reviewed; this ADR deliberately supplies no replacement numeric defaults.

Start the real session deadline before preflight. Each case deadline is min(session
deadline, case start + configured case duration), including launch and cleanup.
Last dispatch is deadline minus configured cleanup reserve; do not start a case
without that reserve. Atomically check cancellation, remaining counters/time/
space and worker slots, then increment attempts before fake dispatch. Admitted
failed/rejected attempts consume slots; no counter or time reset on retry.
A refused beyond-cap attempt never dispatches. Never admit more than configured
workers; a slot stays occupied until actual termination/reaping is proven.

Only supervisor-owned manifest-keyed scripted fake functions are capabilities,
with no URLs, commands, SDKs, shells or worker-selected destinations. Bounded
canonical JSON request/result frames use stdout; scripted replies use stdin,
newlines included in byte counts. Stderr is bounded and sanitized. Worker gets
no raw fixture store or manifest. On cancel or dispatch cutoff, stop admission,
kill/reap worker container/process group and clean only resolved owned scratch
with no symlink/traversal escape. Cleanup uses the reserved time, not extra time.
If cleanup cannot complete by deadline, fail the session, admit no more work and
do not claim the deadline/worker-slot guarantee was proven. A separately verified
runtime timeout/cleanup watchdog must handle supervisor death or preflight fails.

No unbounded container layers/runtime logs. Disable the runtime log driver,
capture bounded pipes and enforce live plus retained scratch accounting. Exceeding
a quota terminates safely, never truncates or evicts user reports to make room.

## Proposed Linux availability and denial mechanism

Use an already available Linux Docker runtime and an approved local image by
SHA-256 digest, with pull disabled. Image contains reviewed Python 3.11/3.12,
owned worker/bootstrap and synthetic denial canaries, no evidence fixture store,
manifest or user data. Trusted supervisor alone owns/hash-validates that store.
Image digest/inventory, audited libseccomp bootstrap and exact syscall profile
are future reviewed prerequisites. No image build/pull, runtime/WSL/Docker install
or system change is authorized here; absence means blocked, not improvised setup.

Require network none, read-only root, nonroot UID/GID, dropped capabilities,
no-new-privileges, no host binds/devices/namespaces/Docker socket/privileged mode.
Apply the configured memory/no-swap, CPU, PID, FD and noexec/nosuid/nodev scratch
limits with no writable home or other writable mounts. Only bounded stdin/out/err
are inherited. Fixed locale/encoding environment only; no proxy, provider,
FINROBOT, API-token, search-path or core configuration variables.
Exclude user-site/startup discovery and bytecode writes.

Before owned worker entry, irrevocable seccomp permits only reviewed interpreter,
image-file/pipe/clock operations; deny sockets, fork/vfork/clone/clone3,
execve/execveat, ptrace, mount, privilege and namespace changes. Bootstrap may
precede this filter but processes no case input/agent code first.
Trusted code also rejects pickle/arbitrary-object deserialization, eval/exec,
worker-selected dynamic imports, commands and executable prompt/tool content;
seccomp alone cannot deny in-process Python evaluation. No imported upstream
defaults such as yfinance, EDGAR, Adanos or Alpha Vantage are tools here.

Explicitly deny host/home reads and writes, .env/dotenv discovery, OS keyring,
browser profiles, API bearer/provider keys, core SQLite/history cache, legacy
pickle and ~/.finrobot secrets/sessions/logs/artifacts. These remain supervisor-
external canaries, not files mounted into the worker. Mount isolation, not a
userspace path check alone, must block ../, symlink and host-path escapes.
Deny DNS, IPv4/IPv6, loopback/proxy and child/re-exec; missing filters/quotas,
unsupported syscall architecture or failed negative control means no execution.

The PoC has no network broker. Any later accepted FMP/Finnhub broker must use
trusted fixed destinations, refuse redirects/URL userinfo and worker-supplied
hosts, and block loopback/private/link-local/metadata destinations independently
of prompt text. Defining these denials does not choose or enable that broker.

## Verification charter and remaining delivery gates

Each group needs a negative control showing the test detects the forbidden
effect using only disposable synthetic canaries/relaxed test mechanisms, never
host secrets, live network or billing. Group count is not a cap or case count;
the owner-set finite manifest/profile must cover all groups before launch.

| Verification group | Required observable result |
| --- | --- |
| Criteria grammar, range/null/all-any, controls/non-BMP/surrogates, duplicate rows | Exact immutable strings/hash/bindings; invalid grammar/types/version rejected without repair, including plus/exponent/NaN/whitespace and signed-zero/precision boundary cases |
| Editor outdating/clearing/navigation/reload and core cold startup | No request/store/credentials/cost reservation; CLI/API/dashboard/editor work with absent/disabled/incompatible/failing AI and core Windows support unchanged |
| Synthetic ticker/weight projection | Existing FC-051 exact/duplicate/zero/null/error behavior; no quantity/cost/account/namespace/ordinal fields exposed to worker |
| Per-channel secret/holdings injection | Secrets and forbidden fields absent from all channels; permitted ticker/weight projection local-only and absent from every simulated LLM payload, including nested text; exact stored snapshot never rewritten |
| Identity collision, stale/conflicting evidence, missing mandatory input with any match | Unverified candidate; optional match/false citation cannot bypass prerequisites or invent factual support |
| Empty/nonempty complete versus unresolved/interrupted/disabled | Exact eight-status list; only fully valid cleaned empty scope is completed_empty; partial text is never a completed report |
| Opinion/forecast/trade injection and preselected daily watchlist explanation | Exact label and Buy/Hold/Avoid plus reason, no numeric target/forecast/action/threshold change/model-selected winner; fixed daily selection binding, no manufactured suggestion |
| Config/counter/byte/scratch/concurrency bounds | Missing/malformed owner profile refuses; atomic cap checks, aggregate partitions and inclusive deadline boundaries hold without counter reset/truncation/retry |
| Cancel pending/in-flight, UI disconnect/stream close, deadline and supervisor crash | No new dispatch, actual worker reaping before slot reuse, cleanup before success; no completed publication or replay after failure |
| Home/.env/keyring/core DB/cache/~/.finrobot, traversal/symlink, pickle/dynamic import/socket/child attempts | Actual denials with independent canaries; no upstream code/default tool or real-data acquisition |
| Temporary core-state/report preservation | Isolated synthetic SQLite/watchlists/cache/reports and pin/asset metadata identical before/after absent/disable/failure; disabling does not delete reports; no user's DB read |
| Rights/retention and fake charge ledger | Synthetic FMP/Finnhub provenance, local-only bounded artifacts; fake-only reservation/settlement races below, no live pricing/rights claim |

D9 is resolved policy under ADR-0020, not an implemented ledger. For a future
billable path the owner configures hard per-run AND per-day dollar caps; no
amount is supplied here. Before the first billable call, atomically reserve the
FULL run's estimated maximum against both caps, across runs/restarts, accounting
for confirmed charges plus outstanding reservations. Do not substitute per-call-
only reservation. Every later dispatch must remain within that reservation and
both caps. Unknown price/version/currency/hidden-token/tool fees or unenforceable
maximum means zero billable dispatch; zero-cost mode supplies no live-dollar cap.
Day-boundary/accounting implementation must be explicit before live use.

On in-flight cancellation keep the WHOLE reservation. Local completion, timeout,
crash, UI disconnect or closing a stream does not release it or settle a run.
Release only after provider-reported usage confirms the real charge; the run
settles only when that report matches or is within the reservation. Missing,
contradictory or above-reservation usage remains unsettled and cannot authorize
another billable call. No early proven-unused release, inferred refund, automatic
replay/reset or double release. Idempotent reconciliation charges actual confirmed
usage and releases unused reservation only after that accepted settlement check.
Fake ledger fixtures cover both caps, missing/excess usage, disconnect/cancel/
restart races and duplicate reconciliation; no provider or price is selected.

Next gates: explicit owner acceptance of ADR-0019; owner-set finite resource
profile; reviewed available local image/bootstrap; then bounded validator,
Linux supervisor/fake-dispatch and independent audit issues against stable
interfaces. Production universe/predicate meanings, actual selector/day-boundary
details, provider/model transmission rights, configured live caps and audited
pricing/ledger remain implementation/activation gates. The accepted opinion,
cadence, local holdings boundary, FMP/Finnhub/local-retention rules and D9 policy
are NOT reopened. No live activation or M10 completion follows from this PoC.

For this documentation PR run relative Markdown/diff/staged hygiene and canonical
full pytest, Ruff, configured mypy and pip check. No browser build is needed.
Repository checks do not prove proposed isolation or negative controls. No PoC,
Linux runtime, upstream or real-data/model/provider operation was executed here.
