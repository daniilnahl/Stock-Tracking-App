# M7 — REST API execution plan

## Authority and current state — 2026-10-13

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
| [#129](https://github.com/daniilnahl/Stock-Tracking-App/issues/129) | REST contract/acceptance | M6 merged | Proposal submitted; Master; independent read-only agent review | [PR #135](https://github.com/daniilnahl/Stock-Tracking-App/pull/135); owner acceptance outstanding |
| [#130](https://github.com/daniilnahl/Stock-Tracking-App/issues/130) | Lazy app factory, JSON/error/access foundation | #129 acceptance, owner merge/main CI | Blocked; unassigned | None |
| [#131](https://github.com/daniilnahl/Stock-Tracking-App/issues/131) | Saved watchlist views | #130 owner merge/main CI | Blocked; unassigned | None |
| [#132](https://github.com/daniilnahl/Stock-Tracking-App/issues/132) | Stored-row raw history | #130/#131 owner merge/main CI | Blocked; unassigned | None |
| [#133](https://github.com/daniilnahl/Stock-Tracking-App/issues/133) | Local composition/launch/operation | #130–132 owner merge/main CI | Blocked; unassigned | None |
| [#134](https://github.com/daniilnahl/Stock-Tracking-App/issues/134) | Independent source/wheel exit audit | #130–133 owner merge/main CI | Blocked; unassigned | None |

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

## Completion gate

Check every accepted ADR exit against combined evidence; required issues closed,
required implementation/audit PRs owner-merged and main CI green. Capture actual
results and remaining decisions in an exit-evidence document. Never close M7
to conceal outstanding contracts or runtime work. M8 remains future scope.
