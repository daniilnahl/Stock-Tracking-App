# M7 — REST API execution plan

## Authority and current state — 2026-10-13

**Acceptance update — 2026-10-14:** the owner directly instructed **"pr merged,
continue the work"** after the explicit approval request for M7/Option A in
PR #135. Owner merge `e03d116981c8c81b7899f7202040fefb23b9065b` and reviewed
head `94bde7d268bc423b907d89429e1c5d3b76c30c41` were independently verified;
exact-head Foundation 38523342700 passed. The relevant M7 specification and
ADR-0013 Option A are accepted; M8–M10 and unresolved rights remain outside
this approval. Earlier pending statements below are dated execution snapshots.
Post-merge main Foundation 38527281579 completed successfully; #129 is resolved
and #130 is unblocked. Master owns this acceptance record; a delegated
implementation agent owns #130's minimal foundation on
`feature/130-api-foundation`. Later runtime issues await its owner merge/main CI.

The owner requested the Master Engineering Agent role and beginning M7.
`master-agent.md` contains stale M2/template placeholders; the direct M7
request selects SRS §23 M7. Analysis, bounded issues, delegated independent
contract review and proposal work are authorized. No runtime contract has
been accepted and no agent merge is authorized.

Baseline main: `5bed5d327bdbaaf75105e7bae2fc1451fef14752`, owner-merged M6
documentation #127 following accepted service/audit implementation. Baseline
[main Foundation run 38505176726](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38505176726)
was independently retrieved and is completed successfully. Existing
services satisfy reusable boundaries; no REST package/dependencies exist.
The SRS defines shared services and permits FastAPI, but no endpoints or
security/JSON/error contract. [Proposed ADR-0013](../adr/0013-local-read-only-rest-api.md)
provides reviewable Option A and alternatives. Runtime remains blocked on
explicit owner acceptance, proposal owner merge and passing required main CI.

## Newly merged specification proposal

Final base refresh found owner-merged PR #128 at
`a968df963084361e4d824d17e2c25046981514ae`; this branch fast-forwarded to it
without altering its SRS/report. SRS v1.2 still says approval PENDING. The
approved v1.1 and accepted ADRs remain authoritative. #129–134 were created
under that baseline before this refresh and are conditional planning candidates;
they do not authorize implementation under the pending SRS revision. Proposed
ADR-0013 addresses M7 D1/D2/D4, exact provenance unknowns, evolution and bounded
local operation. Owner acceptance must identify the relevant M7 specification
and Option A; M8–M10 and remaining provider/research/AI decisions stay separate.

## Live dependency view

All issues belong to [M7 milestone 8](https://github.com/daniilnahl/Stock-Tracking-App/milestone/8).

| Issue | Objective | Dependencies | Status / assigned work | PR / review |
|---|---|---|---|---|
| [#129](https://github.com/daniilnahl/Stock-Tracking-App/issues/129) | REST contract/acceptance | M6 merged | Accepted; owner merge and PR/main CI passed | [PR #135](https://github.com/daniilnahl/Stock-Tracking-App/pull/135), merged |
| [#130](https://github.com/daniilnahl/Stock-Tracking-App/issues/130) | Lazy app factory, JSON/error/access foundation | #129 resolved | Closed; owner merge and PR/main CI passed | [PR #136](https://github.com/daniilnahl/Stock-Tracking-App/pull/136), merged |
| [#131](https://github.com/daniilnahl/Stock-Tracking-App/issues/131) | Saved watchlist views | #130 resolved | Closed; owner merge and PR/main CI passed | [PR #137](https://github.com/daniilnahl/Stock-Tracking-App/pull/137), merged |
| [#132](https://github.com/daniilnahl/Stock-Tracking-App/issues/132) | Stored-row raw history | #130/#131 resolved | Closed; owner merge and PR/main CI passed | [PR #138](https://github.com/daniilnahl/Stock-Tracking-App/pull/138), merged |
| [#133](https://github.com/daniilnahl/Stock-Tracking-App/issues/133) | Local composition/launch/operation | #130–132 resolved | Closed; owner merge and PR/main CI passed | [PR #139](https://github.com/daniilnahl/Stock-Tracking-App/pull/139), merged |
| [#134](https://github.com/daniilnahl/Stock-Tracking-App/issues/134) | Independent source/wheel exit audit | #130–133 resolved | Implemented; canonical checks and independent review passed; hosted CI pending at submission | [PR #140](https://github.com/daniilnahl/Stock-Tracking-App/pull/140), open |

One issue, branch and PR per objective. Delegate runtime only after contracts
and dependency gates pass. Stable factory/serializers precede route work;
composition and combined audit follow. Issue creation/proposal CI never imply
contract acceptance. All issues stay open until their acceptance gates pass.

## Requirement and test mapping

| Requirements | Implementation / verification |
|---|---|
| SRS M7, ARCH-001–006 | Accepted ADR; shared services; cold API/service boundary probes with negative controls; no CLI/facade UI graph |
| FIN-001–005, FC-001–004 / approved position metrics | Exact Decimal wire tests; zero/null/unowned and known-value snapshots; no new formulas |
| DATA-003/006/007, PERF-001/002 | Fixed UTC/range and exact raw bar/error matrices; existing retries/cache reuse/expiry/no-stale policy |
| PERS-005/007, ADR-0009 | Isolated temp SQLite, both namespaces, ordered duplicate rows, missing/legacy/corrupt/schema refusal, unchanged holdings bytes |
| SEC-002/005, ERR-001/002 | Auth/Host/Origin before acquisition, no input echo/raw diagnostics, separate API/provider credentials, fixed envelopes |
| DEV-001–004, TEST-001–005, GH-003–005 | Canonical pinned setup, full tests/Ruff/configured mypy/pip check, source/wheel installation, scoped PR/main CI |

Runtime tests use fake transports, fixed clocks and isolated state. No live
credentials, network, current prices or real databases. History may update only
the explicit temporary cache. The final combined audit must prove its denial
guards before executing real application paths, preserve CLI tests and document
limits (saved freshness unknown, sparse raw history, local single user).

## Proposal verification record

Independent delegated read-only review checked service/model/config/provider
contracts. Findings repaired before submission: path alias protection, exact
Bearer token grammar, fixed-route query rejection and bounded body refusal.
No runtime feature or milestone exit is claimed. Initial virtual-environment ensurepip failed because sandbox TEMP
was unwritable; selecting a worktree-local ignored temporary directory repaired
it. Canonical installation initially failed at pinned setuptools resolution due
to sandbox DNS; approved elevated canonical pip installation then succeeded
in the worktree virtual environment, using supported Python 3.12.14. No system
software, runtime requirement or dependency configuration changed.

Actual Python 3.12.14 proposal checks: targeted baseline/packaging/hygiene
**24 passed in 103.08s**; Ruff passed; configured mypy passed (**config.py only,
one source file**); pip check passed. Initial sandbox full pytest: **2504 passed,
3 failed in 210.92s**, all at temporary `os.link` fixture creation denied by
Windows sandbox. With approved temporary hard-link access, persistence transfer
passed **83 in 3.34s** and full pytest passed **2507 in 118.02s**. No source/test
or valid assertion changed. Staged hygiene passed **8 in 13.11s** before final
proposal reconciliation and **8 in 12.51s** afterward; final Ruff/configured
mypy/pip check also passed. Final delegated review clarified admission retention
until disconnected provider work terminates and unknown injected cache
provenance. [PR #135](https://github.com/daniilnahl/Stock-Tracking-App/pull/135)
was created through the signed-in GitHub website and attached to this chat.
Required hosted CI, owner acceptance and owner merge remain outstanding at
submission. #129 stays open; downstream runtime issues remain blocked.

## Foundation implementation — issue #130, 2026-10-14

The delegated implementation supplies `stock_tracker.api` with an injected
factory registering only health and authenticated OpenAPI, typed neutral wire
schemas/serializers, fixed error envelopes, exact Host/Origin/Bearer ordering,
bounded bodies/responses and reusable admission. Source and installed-wheel
probes prove application IO isolation with documented code-loading exceptions.
Existing pins/Python/tooling, services, financial arithmetic, CLI behavior and
SQLite schema remain unchanged. No data routes, launcher or production
configuration are included. See [foundation details](../API_FOUNDATION.md).

Independent Master/read-only agent review repaired malformed snapshot output
and cancellation-before-worker-start admission leakage; each has regression
coverage. The reviewer independently reproduced the cancellation fix, raw ASGI
access/body/refusal cases and final cold-source probe, then returned PASS with
no actionable findings. No review conclusion is product acceptance or a merge.
Final Master audit additionally found the token in Starlette middleware keyword
argument repr. A private middleware-factory closure removes that diagnostic
exposure; regression and independent correct/wrong/missing-token probes pass.
Canonical final reinstall refreshed the completed API package; isolated installed
import/factory execution passed from site-packages.

Canonical Python 3.12.14 results (commands actually executed):

- `python -m pytest tests/test_api_foundation.py tests/test_api_serialization.py tests/test_api_boundary.py tests/test_packaging.py -q`: initial **85 passed in 46.78s**; final repr-repair **86 passed in 47.19s**.
- `python -m pytest -q`: initial **2590 passed in 124.20s**; final repr-repair/reinstall **2591 passed in 126.12s**.
- Final fixture-only token indirection: cold-source boundary **1 passed in 1.20s**; no runtime behavior change.
- `python -m ruff check .`, `python -m mypy` (**config.py only**), `python -m pip check`: passed.
- Final staged `python -m pytest tests/test_repository_hygiene.py -q`: **8 passed in 13.61s**.
- Whitespace/scope/staged-secret/generated-artifact review: passed; only intended source, tests, JSON contract fixture and documentation staged.

Native Windows event-loop control sockets and temporary hard-link tests required
approved filesystem/socket access; actual application execution retained offline
guards. Every old/new exact pin resolved in a Python 3.11 Windows-wheel dry run;
local 3.11 execution was unavailable and remains a required hosted CI check.
PR #136 was created through the signed-in website and attached to this chat.
Hosted PR/main CI, owner merge and #130 closure remain pending. #131–134 stay
blocked on their respective preceding owner merges/main CI; M7 is incomplete.

## Saved-view continuation — issue #131, 2026-10-14

The owner instructed "pr merged, continue the work" after PR #136. Verified
owner merge `1994ecea7fa22762d88de1d56b867dcda455a9e3`, reviewed head
`3e3fff68edbd4f622f7e55108d9dab521a64e23a`, five successful PR Foundation
checks (run 38530351856) and successful main Foundation 38619991215.
Issue #130 is closed; #131 may begin on `feature/131-saved-watchlist-api`.
The merge preceded the final local token-repr repair. Preserve that minimal
security prerequisite and regression in this branch (commit `3d3405e`);
the original merged-head results were 85 targeted and 2590 full tests.
The later 86/2591 results above include that locally reviewed repair, rather
than the merged head. The PR evidence was corrected to distinguish them.

Plan: delegate the saved-view route over existing load/view/serialization and
admission, verify both namespaces and unchanged temporary holdings/legacy bytes,
update real typed OpenAPI and guarded source/wheel evidence, independently review,
then publish one bounded issue PR. No history route, launcher, dependency,
financial formula or persistence schema changes. #132–134 await their respective
owner merges/main CI. M7 remains incomplete.

Implementation delegates only the allowlisted saved-view route to existing
`WatchlistService.load()`/`view()`, serializer and admission. Response namespace
must match the request; malformed/swapped dependencies fail safely. Typed actual
OpenAPI includes the route and restores its specific integer ordinal minimum
from FastAPI's `0.0` to exact `0`; the financial encoder still rejects floats.
Temporary SQLite reads preserve bytes across success/absence/corrupt/future
schema outcomes, and legacy checks never read pickle contents. Cold source/wheel
probes execute both namespaces with unchanged proven infrastructure denial guards.

Final canonical Python 3.12.14 checks actually run:

- API/source/wheel focused suite: **107 passed in 41.81s**.
- Final fixture/staged-hygiene/packaging suite: **31 passed in 41.91s**.
- `python -m pytest -q`: **2612 passed in 96.82s**.
- Ruff, configured mypy (**config.py only**), pip check and diff check: passed.
- Independent review: **PASS**; **104 API tests in 2.46s**, **2 packaging tests in 39.04s**, cold-source isolation and separate mismatch/malformed/absent dependency probes passed.

Recovery evidence: initial typed OpenAPI float-bound failures were repaired only
in schema metadata. Initial full run had **2 failed / 2610 passed in 120.11s**:
the staged scanner treated a synthetic domain Stock's second positional name as
the legacy credential pattern, and an unchanged packaging assertion saw transient
Matplotlib font-cache stderr. Named fixture arguments repaired the scanner match;
focused packaging and the final full run passed without changing its assertion.
No guard, financial encoding rule, hygiene check or valid expectation was weakened.
Hosted CI and owner merge remain required before #132 begins.

Published [PR #137](https://github.com/daniilnahl/Stock-Tracking-App/pull/137)
through the signed-in GitHub website and attached it to this chat. Final staged
hygiene passed **8 in 8.41s**; Master scope/whitespace/secret review and final
Ruff/configured mypy/pip check passed before commit/push. No agent merge.

## Stored-entry history continuation — issue #132, 2026-10-14

The owner instructed "merged, continue the work" after PR #137. Verified owner
merge `090a6aafa5576802efa379b46c3a2721bfe350d1`, reviewed final head
`e75c7632acd4182a09eb0eb494d47b45692af056`, five successful exact-head PR
Foundation checks (38622318673) and five successful main checks (38626243824).
Issue #131 is closed; #132 is unblocked on `feature/132-stored-entry-history-api`.
The implementation agent analyzed only while main CI was pending and began
editing after all dependency checks passed. A separate read-only agent reviews
contracts, isolation, precision, row association and read/cache integrity.

Plan: add only the accepted stored-row history route using existing load/history
services, raw serializer and history admission; validate transport selectors and
dates, preserve disabled activation before IO, exact integer schema bounds,
unknown provenance and fixed safe errors. Verify duplicate identity, UTC/range/
NASDAQ policy, temporary holdings/legacy bytes, cache restart/exact expiry/no
stale fallback, actual disconnect retention and guarded source/wheel execution.
No production launcher, dependency, persistence schema, provider policy, financial
formula or CLI changes. #133–134 retain their owner-merge/main-CI gates. M7 remains
incomplete; live provider rights and activation remain separate.

Implemented only that route with strict namespace/ASCII ordinal and paired ISO
query validation through the framework request interface. Full loaded records
and exact selected Stock identity are revalidated before publication; defaults,
NASDAQ scope, ranges and raw bars remain owned by HistoryService. Disabled
history refuses before state/provider/cache acquisition. Typed OpenAPI has four
unique input parameters and exact approved integer ordinal/volume bounds;
financial floats remain forbidden. Closed-client and cancellation tests retain
history admission until the actual worker terminates. Existing guarded source
and installed-wheel probes execute real services with synthetic provider ports;
separate temporary SQLite/cache tests prove restart, exact expiry, no stale
fallback and unchanged holdings/legacy bytes.

Final canonical Python 3.12.14 results actually executed:

- `python -m pytest tests/test_api_history.py -q`: **63 passed in 2.23s**.
- Five API paths (history, foundation, boundary, serialization, saved views): **168 passed in 4.90s**.
- Those paths plus the authoritative market-provider boundary: **181 passed in 5.21s**.
- `python -m pytest -q`: **2675 passed in 104.61s**, including fresh source/wheel probes.
- Ruff, configured mypy (**config.py only**), pip check and diff check: passed.
- Independent review: **PASS**; separately proved 13 invalid query cases refuse before acquisition and two plain/encoded valid queries preserve exact row/zero/null values under network denial.

Initial full run: **1 failed / 2674 passed in 114.72s**. The existing architecture
check rejected a direct `urllib.parse` import. Replacing it with the framework
query interface retained strict raw-segment/date/duplicate validation and passed
the unchanged boundary check and adversarial probes. No test, guard, policy or
assertion was weakened. Staged hygiene, hosted CI and owner merge remain required
before #133 begins. M7 remains incomplete.

Published [PR #138](https://github.com/daniilnahl/Stock-Tracking-App/pull/138)
through the signed-in GitHub website and attached it to this chat. Final staged
hygiene passed **8 in 8.16s**; Master scope/whitespace/secret review and final
Ruff/configured mypy/pip check passed before commit/push. No agent merge.

## Local operation continuation — issue #133, 2026-10-14

The owner instructed "pr merged, continue the work" after PR #138. Verified
owner merge `f5c91da49f5e774381420b772ad475cc36055da0`, reviewed head
`20541993d4f4bf2bea74843ed585c76564564837`, successful exact-head Foundation
38628310335 and successful main Foundation 38631256087. Issue #132 is closed;
#133 is unblocked on `feature/133-local-api-launcher`. The implementation agent
performed analysis only while main CI was pending and began after it passed.
A separate read-only agent reviews path aliases, token safety, lazy composition,
launcher bounds and source/wheel evidence.

Plan: implement independent configuration/composition and the fixed loopback
launcher. Require four explicit pairwise distinct paths with metadata-only
startup validation and an environment-only operator token. Help/import/health
remain IO-free; saved views never acquire provider credentials/cache. Enabled
history reuses the existing lazy configuration/provider factory and UTC service
policy. Document the separate owner-confirmed rights precondition for the opt-in
flag; no rights were supplied and no live provider/listener/user state is used.
Verify safe failures, aliases, rejected access, temporary state and source/wheel
packaging. No dependency, schema, financial or CLI changes. #134 retains its owner
merge/main-CI gate; M7 is incomplete.

Implemented independent API configuration/composition and the module launcher.
Configuration requires a valid process-only token and four explicit distinct
paths, rejects native aliases and unresolved symlink/reparse entries using
metadata only, and issues immutable validated configuration without repeated
resolution during composition. The server runner is fixed to loopback port
8000, one worker, no reload/proxy trust/access logs. Shared services retain
lazy infrastructure acquisition and accepted UTC/provider/cache policies.
Static help avoids locale/terminal configuration reads. Operations docs record
the unsupplied rights gate and disabled-by-default historical capability.

Final focused verification after the junction repair passed **255 in 46.84s**
across all API tests and source/installed-wheel packaging. Independent review
passed with no remaining findings; its actual native Windows junction and
synthetic reparse regressions passed **2 in 0.69s**. Staged-index hygiene passed
**8 in 9.70s**. Master independently inspected source, tests, probes and docs;
Ruff, configured mypy (**config.py only**), pip check and diff check passed.
Earlier review repairs covered unchecked configuration construction, ambiguous
Windows path spellings, cold-help guard placement, startup metadata/token-only
guard evidence and dangling junction parents. No guard or policy was weakened.
Final canonical Python 3.12.14 `python -m pytest -q` passed **2760 in 111.81s**
with no skips or failures, including fresh source/installed-wheel checks.
Hosted CI remains pending at submission. No live listener, provider call, real
credential or user state was used. #134 remains gated on owner merge and passing
main CI; M7 remains incomplete.

Published [PR #139](https://github.com/daniilnahl/Stock-Tracking-App/pull/139)
through the signed-in GitHub website and attached it to this chat. Final staged
hygiene passed **8 in 8.43s** before the implementation commit. This publication
record changes documentation only. Final-revision hosted CI and Master review
are recorded on the PR; no agent merge.

## Combined audit continuation — issue #134, 2026-10-14

The owner instructed "merged, continue the work" after PR #139. Verified owner
merge `65efe21f5d6432e0e4e19d29f76d30d66b1c00be`, reviewed final head
`101315b69bdc5d7455c6c04d8930a9895b1ad192`, successful exact-head Foundation
38659586967 and successful main Foundation 38668340633, each with all five
checks. Issue #133 is closed. #134 is unblocked on
`test/134-rest-api-exit-audit`, based on that owner merge. The delegated audit
agent performed analysis only while main CI was pending; a separate read-only
agent reviews audit coverage, guard evidence and requirement traceability.

Plan: add one combined offline probe for source and installed-wheel processes,
using the real local API configuration/composition, shared services, SQLite,
provider factory/parser and historical cache. Replace only the external HTTP
seam and clocks with controlled fixtures. Prove network, legacy-content and
outside-write guards before executing application paths. Verify both namespaces,
ordered duplicates, precise numbers/nulls, safe errors/access, cache restart,
exact expiry/no stale fallback, and unchanged holdings/legacy bytes. Reuse the
existing wheel build and canonical verification commands. Record exit evidence
and limits without claiming milestone completion before this audit PR's owner
merge, main CI and issue closure. No runtime feature, dependency, schema,
financial, CLI, rights or hosting changes; no live operation or user state.

Implemented only a standalone combined audit, its source wrapper, reuse of the
existing installed-wheel build, testing instructions and requirement/exit
evidence. Production API configuration/composition, service calculations,
provider factory/transport/FMP parser, SQLite and JSON cache remain real. The
external opener and clocks are controlled. Distinct namespace/duplicate markers,
exact raw numbers/nulls, 3599-second restart reuse, exact 3600-second expiry,
accepted provider retries and unchanged holdings/legacy/cache-failure bytes are
asserted under proven Python IO guards. A denial ledger prevents safe HTTP
errors from hiding forbidden IO. Bootstrap, TLS/code reads and fixture-only
legacy opener exceptions are disclosed in [exit evidence](m7-exit-evidence.md).

Focused M7/API/source-wheel verification passed **256 in 49.33s**. Independent
read-only review passed with no remaining findings; its separate source audit
passed **1 in 3.29s**. Initial staged-index hygiene passed **8 in 9.22s**. Master
inspected the diff and independently ran Ruff, configured mypy (**config.py
only**) and pip check successfully. Final canonical Python 3.12.14 full pytest
passed **2761 in 122.98s**. Hosted CI is pending at submission; no milestone
completion is claimed. #134's own owner merge, passing main CI and closure
remain required.

Published [PR #140](https://github.com/daniilnahl/Stock-Tracking-App/pull/140)
through the signed-in GitHub website and attached it to this chat. Final staged
hygiene passed **8 in 8.80s**; Master diff/secret/artifact review and canonical
static checks passed before commit/push. This publication record changes docs
only; final-revision hosted CI and Master review are recorded on the PR.
No agent merge and no premature milestone completion.

## Completion gate

Check every accepted ADR exit against combined evidence; required issues closed,
required implementation/audit PRs owner-merged and main CI green. Capture actual
results and remaining decisions in an exit-evidence document. Never close M7
to conceal outstanding contracts or runtime work. M8 remains future scope.
