# M9 — Automated Stock Research planning

## Current API contract proposal — 2026-10-16

PR #169 is owner-merged at `1847a155d2e44f1fa82e315e060f557a421e542d`;
post-merge [Foundation 38988510270](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38988510270)
passed. The injected EPS service is delivered. The next meaningful step is
[#170](https://github.com/daniilnahl/Stock-Tracking-App/issues/170), a concrete
[opt-in EPS API/composition proposal](../adr/0016-upcoming-eps-api.md). It is
**proposed**, with no runtime change or live acquisition authorized. Master owns
the proposal; `m9_analysis` independently reviews. Its conditional delivery order
is injected API, evidence-gated composition/budget, then a separately reviewed
minimal dashboard form. No further offline wrapper is proposed.

## Previous service continuation — 2026-10-16

Planning PR #165 and the scoped EPS implementation PR #167 are owner-merged.
Main `74f787554e3cd7c7083738347a83c887e1a1c5d0` passed
[Foundation 38987281100](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38987281100).
The selected Finnhub Free upcoming-release observation contract is accepted
under [ADR-0015](../adr/0015-finnhub-upcoming-eps.md) and EPS-001–004; its adapter,
strict transport and offline tests are implemented. This supersedes the initial
investigation-only statements below for that narrow capability.

After the owner's instruction to continue, [#168](https://github.com/daniilnahl/Stock-Tracking-App/issues/168)
adds an explicitly injected application service with one intended research-date
sample, immutable request context and validated raw observations. See
[the bounded task record](m9-eps-service-168.md). `eps_impl` owns source/tests;
Master owns contracts, verification and publication; `m9_analysis` independently
reviews. No default/live acquisition, identity mapping, API/UI, arithmetic,
quota policy or persistence is authorized. Broader M9 remains proposed and its
other decision gates remain open. The following initial plan is dated history,
not a claim that the merged adapter is still unimplemented.

## Initial planning status — 2026-10-16

Planning started for [#164](https://github.com/daniilnahl/Stock-Tracking-App/issues/164)
in [M9, milestone 10](https://github.com/daniilnahl/Stock-Tracking-App/milestone/10).
The owner requested the master engineering role and work on **M9**. The role
document's M2/template values do not select this task's scope. The Master owns
planning and review; delegated `m9_analysis` independently inspected readiness.

SRS §23.9/RSH901–940 remains **proposed**. This planning request does not settle
the explicit decisions in §23.7.0/§23.11. No implementation issue, runtime code,
financial definition, connector activation or new dependency is introduced.
The [decision brief](m9-decisions.md) records the human inputs needed next.
Do not mark the SRS or an ADR accepted from this plan, CI or a PR merge alone.

**Source research update — 2026-10-16:** the owner selected FMP first, then
FINVIZ enrichment, and requested native-metric gap research. The
[provider coverage report](m9-provider-coverage.md) records official-source
findings and conditional routing: documented FMP capabilities stay with FMP;
FINVIZ is considered for verified native/semantic gaps only. This resolves source
priority, not authenticated schemas, actual entitlement, metrics or activation.

The owner subsequently reported **no subscription**. FINVIZ activation is
deferred; FMP free-tier feasibility is the next source-contract task, with exact
endpoint/symbol/use rights still unverified. Do not assume a free key, start a
trial, buy access or substitute scraping. This narrows available delivery
options but does not approve a new preset or resolve M9 exit criteria.

**EPS feasibility:** the owner's subsequent Finnhub free-tier request is recorded
in [the EPS report](m9-finnhub-eps.md). Recent quarterly actual/estimate observations
are a candidate; forward estimate series are Premium. Keep this investigation
inside planning #164 until field semantics, access and provider extension are
accepted. No implementation agent is assigned to a blocked connector task.

Baseline is owner-merged main `4d7720446ab299344ec98b1a28169143d7a9202a`.
PR #162's final M8 audit is merged at `9a6a41449d1f483b7e2218eabc8db1867e05d497`;
README PR #163 is merged at baseline. GitHub reports both post-merge Foundation
runs successful: [38954764226](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38954764226)
and [38955087073](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38955087073).
M8 has zero open issues but its milestone remains open. These facts establish
delivery prerequisites, not a new claim of administrative M8 closure or M9 acceptance.

## Repository readiness

| Existing capability | Reuse and M9 gap |
| --- | --- |
| [Provider protocols](../../src/stock_tracker/providers/protocols.py), [models](../../src/stock_tracker/providers/models.py) | Lookup, quote, profile, reported period changes and raw history are available. No universe/fundamentals/news/screen interface, FINVIZ adapter or provider-stable identity exists. Nullable dates remain unknown. Profile sector/market cap are not a dated taxonomy or field-level research evidence registry. |
| [Application services](../../src/stock_tracker/services/) | Watchlist/current/history orchestration is injected and reusable. History accepts exact NASDAQ only; preserve callable contracts and ordered row/namespace behavior. There is no research service or job lifecycle. |
| [Financial definitions](../FINANCIAL_CALCULATIONS.md) | Approved position/snapshot calculations exist. No valuation screen, attractiveness score, ranking, technical indicator or research default threshold is defined. Provider summary percentages cannot manufacture history. |
| [SQLite runner](../../src/stock_tracker/persistence/migrations.py) | Version 1 rejects extra tables. Research state needs an accepted storage/retention/backup contract using the single migration mechanism where applicable. Never append unapproved tables or expire user reports by inference. |
| [API](../../src/stock_tracker/api/) and [dashboard](../../frontend/) | Accepted local read-only views, exact serialization, authentication and opt-in same-origin hosting can be reused. Research command/job routes and server-side criteria settings require a new reviewed contract; unavailable M9/M10 panels stay unavailable. |
| [Transport](../../src/stock_tracker/providers/transport.py), [history cache](../../src/stock_tracker/providers/history_cache.py) | Accepted bounded transport, immediate 429 failure and history TTL/no-stale behavior remain authoritative. No cross-process research budget or per-class freshness policy exists. |

Relevant regression evidence is in `tests/test_provider_models.py`,
`test_provider_protocols.py`, `test_current_data_service.py`, `test_history_service.py`,
`test_sqlite_migrations.py`, the API tests and frontend unit/browser profiles.
Read these tests and all downstream callers before changing their interfaces.
No existing quote/profile or saved metadata is automatically sufficient for
dated, comparable, rights-cleared research qualification.

## Planning work and execution state

| Issue / objective | Status | Dependency | Assigned agent / PR / review |
| --- | --- | --- | --- |
| [#164](https://github.com/daniilnahl/Stock-Tracking-App/issues/164): readiness, decision brief and conditional dependency plan | Planning documents reviewed and locally verified; owner product decisions pending | Current request authorizes planning | Master; `m9_analysis` independent review passed; publication/current PR tracked on #164 |
| #166: Finnhub Free upcoming-release EPS contract/adapter | Owner-merged; post-merge CI passed | Narrow owner-selected reported-data scope | `eps_impl`; PR #167; independent review passed |
| #168: injected upcoming-EPS application service | Owner-merged #169; main CI passed | #166 merged; ADR-0015 service addendum | `eps_impl`; complete independent review passed; 3045 full tests passed |
| #170: opt-in EPS API/composition contract | Proposal in review; runtime blocked on acceptance | #168 merged; account/use evidence gates live composition | Master; `m9_analysis` independent review |
| Provider/field/use rights contract for live activation | Candidate planning task | Owner source/entitlement evidence; dated official documentation review | Unassigned; no live activation issue or PR |
| First screen/universe/taxonomy/daily selection contract | Candidate planning task | Owner product choices and normative financial definitions | Unassigned; no implementation issue or PR |
| Research storage/jobs/API contract | Candidate planning task | Accepted scope and evidence/screen contracts | Unassigned; no implementation issue or PR |

These are separate bounded contract objectives, not one issue to implement the
milestone. Open their planning issues as needed; do not open implementation issues
until specification and relevant decisions are accepted. Then create detailed
issues using AGENTS §10.3, one issue/branch/worktree/implementation agent/PR per
objective, with explicit SRS IDs, tests and predecessor gates. No agent merge.

## Conditional implementation sequence

This table is a dependency proposal, not approved API/schema or implementation
authorization. Final decomposition follows accepted contracts, not this inventory.

| Bounded objective | Requirements | Blocking contracts / implementation |
| --- | --- | --- |
| Typed research identities and observations | RSH906–908, RSH913, X712–715 | Scope; identity/field/provenance/availability contract |
| Research snapshot/run repository | RSH912, RSH923, RSH931 | Observation models; storage/version/retention/backup contract |
| Approved source field acquisition | RSH901–905, RSH911 | Observation/provider contract; actual per-field/use rights and endpoint schema |
| Comparability, freshness and conflict evaluation | RSH907–910, RSH917–918, RSH926 | Field registry, dated fixtures, acquisition, freshness/precedence decisions |
| Shared provider quotas/coalescing | RSH911, X720, X723 | Verified enabled-plan limits, concurrency ownership and accepted retry changes |
| First deterministic screen | RSH914–918, RSH921–926 | Approved preset/math/universe/rank; complete validated observation snapshot |
| Sector result grouping | RSH919, RSH925 | Screen; approved dated taxonomy/unmapped policy/result bounds |
| Daily selection and no-candidate outcome | RSH920, RSH923 | Screen; approved calendar/date/cutoff/rank/tie-break/revision contract |
| Durable manual runs/cancellation | RSH929, RSH931–933 | Repository, screen, quota and job lifecycle contracts |
| Safe watchlist association/change detection | RSH924, RSH927–928 | Stable identities/runs; canonical dedup and prior/current evidence policy |
| Opt-in schedules/restart recovery | RSH930–932, RSH936 | Durable runs; timezone/frequency/missed-run policy and typed settings |
| Versioned research routes | RSH935, X710, X718 | Stable services; accepted authorization/async/cancellation/settings contract |
| Research UI and settings | RSH934, RSH936–937 | M8 delivery; approved API; source/coverage/error/cancellation UX |
| Independent M9 exit audit | RSH938–940 | Required implementations owner-merged; exact-head/main CI and all decision gates |

FINVIZ is optional and separately gated. Do not let it silently substitute
differently defined fields or block permitted FMP-only operation when approved
rules allow it. Scraping, external notifications, hosted listeners, export/PDF,
paid AI and M10 remain separate approval scopes. Do not infer those permissions
from M9 acceptance. Keep M10 at milestone level until M9 contracts stabilize.

## Verification and exit plan

Use [TESTING.md](../TESTING.md): targeted tests, full pytest, Ruff, configured
mypy (`config.py` only), pip check and staged hygiene. Keep source/wheel isolation,
exact Decimal/null/zero behavior, clock injection, mocked providers and temporary
storage. Browser suites remain separate from default Python tests.

Future research tests must cover reproducible ordering, future-evidence rejection,
dated sector membership, incompatible periods/currencies, missing/stale/conflict
exclusions, zero versus unavailable, holidays/no-candidate, per-provider quotas,
duplicate association without holdings mutation, cancellation, crash recovery,
partial publication and opt-in schedules. These are prospective requirements,
not tests introduced or passed by this documentation task.

M9 exit requires every approved RSH requirement mapped to evidence; permitted
reproducible sector screens and sources; qualified daily/no-candidate outcomes;
safe opt-in durable watchlist research; prior dated runs; independent review;
required issue closure, owner merges and passing CI. No milestone completion
claim is possible while its specification/decision gates remain unresolved.

## Current verification

Independent read-only readiness analysis completed with no runtime edits or
provider calls. Latest merged main/PR and CI state was inspected through GitHub.
Independent review of both planning documents by `m9_analysis` passed with no
actionable finding. The Master reviewed the final scope and staged diff.

A new ignored worktree environment uses bundled Python **3.12.14** and unchanged
canonical `python -m pip install ".[dev]"` pins. Initial sandbox ensurepip failed;
the same setup succeeded using task-local TEMP/TMP and approved native execution.
No supported version, dependency or system software changed. GitHub connector
issue creation returned 403; authorized Git credentials held in memory supplied
the REST fallback. No credential values were printed or written to artifacts.

| Command actually executed | Result |
| --- | --- |
| `python -m pytest tests/test_baseline.py tests/test_packaging.py tests/test_repository_hygiene.py -q --tb=short` | 25 passed in 75.22s; planning documents staged. |
| `python -m pytest -q --tb=short` | 2795 passed in 158.70s. |
| `python -m ruff check .` | Passed. |
| `python -m mypy` | Passed; configured `config.py` only. |
| `python -m pip check` | No broken requirements. |
| Relative Markdown target existence check | Passed for both new documents. |
| `git diff --cached --check` | Passed. |

Native Windows subprocess/hard-link verification used approved execution;
application tests retained their offline fixtures and isolated storage.
No frontend/browser profile was rerun because this task changes documentation
only. M9 runtime, provider entitlement and milestone exit are not verified:
contracts/owner evidence are pending and no research implementation exists.
Hosted PR CI remains a separate publication gate; #164 tracks its current state.
Past M8 results do not substitute for this branch's checks.
