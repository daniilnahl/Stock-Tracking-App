# M7–M10 proposed SRS: conflict and decision report

**Status: PARTIALLY ACCEPTED — M7 under ADR-0013; remaining decisions pending.** Prepared 2026-10-13
(America/Los_Angeles); repository observations continued on 2026-10-14 UTC.
**Scoped acceptance update — 2026-10-14:** the owner's direct **"pr merged,
continue the work"** followed the explicit request to accept relevant M7
specification and Option A in PR #135. Independently verified owner merge
e03d116 contains reviewed head 94bde7d. This resolves D1/D2/D4 only for
accepted ADR-0013's local holdings read-only scope. M8–M10, provider rights,
research/AI, external hosting and other open gates remain proposed/blocked.
Earlier pending statements are original proposal snapshots, not a revocation
of the scoped acceptance recorded here and in SRS/ADR-0013.
This is a documentation proposal only. No milestone implementation, implementation
issues, new ADR acceptance, provider activation, subscription, paid model run,
deployment or agent merge is authorized or performed.

## Proposed change and authoritative baseline

[SRS §23](../../SRS.md#milestone-7--rest-api) expands M7/M8 and adds M9
Automated Stock Research and M10 AI Research Agents. All 143 supplied IDs are
retained: X710–729, API701–724, UI801–829, RSH901–940 and AI1001–1030.
Requirements are condensed for integration; illustrative schemas/routes/module
groups remain nonbinding. Proposed decisions are not marked accepted.
The header identifies v1.2 as proposed while retaining the v1.1 approval record.
§4 exclusions, M0–M6, §§24–27, accepted ADRs, financial rules, testing policy,
runtime, dependency pins and public interfaces are unchanged.

Baseline: owner-merged main `5bed5d327bdbaaf75105e7bae2fc1451fef14752`,
PR #127 M6 completion documentation.
The first fetch saw `926171e`; live recheck showed #125 merged at `237c4c5`
and main [Foundation run 38500809992](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38500809992)
successful. #127 then merged while this review was running; the clean proposal
branch was fast-forwarded before edits. No M6 audit changes were copied from
the initial checkout's task branch. The latest read confirms #127 post-merge
[Foundation run 38505176726](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38505176726)
successful at `5bed5d3`, M6 milestone 7 closed with zero open items and all
required #112–118 closed. No M7–M10 milestone containers were present. M1's
administrative container remains open with zero open items; it is unrelated to
this proposal and was not changed.

Reviewed sources: AGENTS.md; complete SRS; ADR-0005–0012 (especially accepted
0011/0012); FINANCIAL_CALCULATIONS.md; TESTING.md; pyproject.toml; Foundation
workflow and PR template; M5/M6 plans and exit evidence; service/provider/domain/
persistence contracts and corresponding snapshot, watchlist, current-data,
history, CLI and packaging tests. Current M6 services are reusable Python
services, not an installed new CLI command tree or an HTTP client contract.

## Repository conflicts and gaps requiring decisions

At the original proposal snapshot all decisions below were **OPEN**. The
scoped acceptance above now resolves D1/D2/D4 only for ADR-0013 Option A;
other decisions and broader interpretations remain open. Recommendations and proposed clarifications
in the SRS are reviewable choices, not owner approval or accepted ADRs.

| Gate / priority | Evidence and conflict | Owner decision / blocking scope |
| --- | --- | --- |
| D11 / P0 — advice boundary | SRS §4 excludes advice/prediction/trading. RSH920/922 and upstream BUY/HOLD/SELL under AI1019 can blur that boundary. An informational label alone does not settle it. | Explicitly accept §23's proposed narrow research interpretation or approve a separate §4 amendment. Decide whether directional model opinions may be displayed at all. Block recommendation/opinion behavior pending acceptance. |
| D1 / P0 — deployment/security | REL-003 has no hosted identity/isolation policy. Loopback and CORS alone do not protect local mutations from hostile origins, CSRF or DNS rebinding. | Local-first single-user recommended; approve host/origin/access-token or equivalent mutation protection, trusted clients and authentication lifecycle. Hosted/multi-user, external listeners and backup/deployment remain separate approval. |
| D2 / P1 — API contract | ARCH-005/ADR-0012 require shared Python services; current CLI has no requirement to call HTTP. Existing numeric records are exact Decimal. | Review FastAPI/Pydantic, version prefix, decimal encoding, date/null/error schemas, namespace/row addressing, write concurrency and disconnect acknowledgement. Preserve CLI partial in-memory invalidation and atomic persistence; no new route or HTTP-client CLI mandate. |
| D3 / P2 — frontend/toolchain/design | Current core uses canonical pip, pinned Python 3.11/3.12; no accepted frontend setup. M8 moves optional React/Next.js toward a proposed Vite default. | Approve technology/design/distribution ADR, one frontend dependency mechanism and generated API types without replacing core tooling. Approve monochrome themes/accessibility; no copied Fly Guy assets. |
| D4 / P0 — actual capabilities | `WatchlistService`, `CurrentDataService`, `HistoryService` exist. `portfolio_snapshot` is pure, with explicit caller currency inputs; no fetched aggregate application service or stored cost currency. `WatchlistView` contains saved numeric prices/opaque metadata, not complete observation provenance. | Inventory day-one operations. Default candidate: supported watchlist/current/history only. Omit/mark unsupported aggregates until independently approved currency acquisition/service contract exists. Saved sector/currency/percentage strings cannot become verified financial evidence. |
| D5 / P0 — provider rights | Official FINVIZ API is verified, but no owner subscription/field entitlement or contractual display/retention/export/LLM permission was supplied. FMP explicitly publishes a display/redistribution licensing gate. | Provider/field/use rights matrix with dated official contract evidence and owner-confirmed entitlement. Unknown rights block activation; do not infer local use is automatically permitted. No scraping/paid subscription authorized. |
| D6 / P0 — finance/screens | FIN-004/005, AN-001, FC scope/§§15–19 and RSH915 block invented metrics. No approved first preset, thresholds, ranking/weights, fundamentals registry or sector taxonomy. Current accepted lookup/history scope is exact NASDAQ, not all US exchanges. | Approve dated universe/identity/taxonomy, field semantics and first screen (formula, units, accounting period, missing/zero/conflict policy, rounding and known values). Wider exchanges or provider-stable IDs need accepted extension without rewriting legacy identities. |
| D7 / P1 — daily selection | Neither market calendar/date policy nor ranking/tie-break for Stock of the Day exists. FC-070 zero prior-price rule remains undefined; raw M4 history proves neither adjusted returns nor complete sessions. | Approve eligibility, date/timezone/calendar, analysis cutoff, rank/tie-break, revision and no-candidate contracts. No technical indicator/return inferred from raw chart or summary percentages. |
| D8 / P1 — jobs/storage | Strict SQLite v1 rejects extra tables (ADR-0009/0010). No durable research scheduler or cross-process quota coordination exists. AGENTS forbids implied deletion of user data. | Approve job states/idempotence/concurrency/restart/missed-run policy, source freshness, storage location and retention/backup/migration using the existing migration runner. Automatic expiry applies only to explicitly designated cache-owned data; reports/user data need explicit deletion policy. External notifications/always-on hosting separate. |
| D9 / P0 — AI feasibility/privacy/cost | Current upstream metadata conflicts with core pins. A subprocess does not alone constrain filesystem/network/tool use. Vendor reporting may arrive after billable work; cancellation cannot refund an in-flight call. | Authorize bounded isolated spike separately, then accept version/adapter/environment/graph/tool/egress/storage/privacy ADR. Public evidence only by default; no holdings upload from general AI opt-in. Approve enforceable worst-case per-call reservations and failure policy; unknown prices/unbounded calls disable vendor/path. |
| D10 / P0 — evidence/report rights | API access, Apache source license and marketing examples of AI workflows do not establish rights for third-party model input or report retention/publication. | Disable unverified export/cloud-model transmission. Approve each data/vendor/purpose/retention use; capture sanitized references rather than token-bearing source URLs. |

Additional contract gaps are included in those gates:

- **Metadata versus provenance (D2/D4/D6):** `HistoryView` exposes bars/date range,
  not provider receipt time or historical currency. Provider `HistoryObservation`
  has receipt time internally; profile/period `as_of` can be None; persisted
  `WatchlistEntry` lacks observation timestamps. API709 must expose known/unknown
  metadata honestly. Rich M9 provenance needs an approved service/model extension,
  not a serializer stamping current time as observation time.
- **ISO currency and identity (D2/D6):** ADR-0011 permits exact nonblank currency
  labels without ISO normalization, while X714 proposes ISO codes for new data.
  Preserve existing validation; decide explicit new mapping/unknown behavior.
  ADR-0006 unknown-exchange equality uses object identity; do not replace it with
  ticker deduplication. ADR-0008 scoped no-match rejection remains authoritative.
- **Freshness/retry (D2/D8):** ADR-0010 history TTL is 3600 seconds, quote TTL is
  zero, expired history never falls back. ADR-0007 returns 429 immediately without
  retry. X726/RSH910/911 do not silently change these policies. Any stale-history
  view or new account-wide retry coordinator needs distinct accepted semantics.
- **Research completion (D8):** A partial run may be inspectable but cannot be a
  successfully completed/qualified snapshot. Define degraded evidence eligibility
  rather than relaxing screen thresholds. Define backup/rollback honestly rather
  than assuming a destructive down-migration is necessary or permitted.
- **AI verification (D9/D11):** Citations must both exist and support claims;
  references alone are insufficient. Agent “risk”/“technical” names do not approve
  undefined indicators, app risk metrics or predictions. Identical inputs/config
  must be auditable; identical stochastic output is not promised. Upstream text
  and logs must be sanitized and cannot replace M9 classifications.
- **X718 privacy wording (D1/D9/D10):** The supplied blanket ban on holdings in
  browser bundles could be read as banning an authorized holdings view. The
  proposal distinguishes authorized local display/payloads from public bundles,
  logs/screenshots/exports; this clarification still requires owner review.

Undefined financial work remains blocked: ranking/scoring/weights/default
thresholds; valuation/fundamental ratio definitions and reporting periods;
momentum/technical indicators; daily zero-denominator and calendar conventions;
historical cash-flow return, benchmark alignment, risk/annualization, dividends,
held splits and FX. Existing FC-020/030/040/041/050/051/091 and accepted M5 snapshot
clarification remain unchanged. No formula or financial test expectation is
introduced by this proposal.

## External verification and rights limits

Primary sources checked during this review (2026-10-14 UTC / 2026-10-13 local).
These are technical observations, **not** contractual permission or account proof.

| Source | Verified observation | Still unverified / blocked |
| --- | --- | --- |
| [FINVIZ API announcement, 2026-10-07](https://finviz.com/blog/our-upgraded-api-higher-limits-clearer-data-and-more-ways-to-connect/) and [Elite](https://finviz.com/elite) | Official API/export workflow exists. Announcement describes account-shared rolling limits and 429 Retry-After. | Actual owner plan/token, endpoint schema/fields, historical vintages, retention, display/export and LLM rights. Marketing is insufficient; limits must be reverified on activation. |
| [FINVIZ robots](https://finviz.com/robots.txt) | Generic crawler policy disallows screener queries and several export paths including screener API CSV. | Robots is not a license or substitute for authenticated official API terms. It does not imply authenticated contractual API use is forbidden or permitted. No scraping performed. |
| [FMP pricing/licensing notice](https://site.financialmodelingprep.com/pricing-plans) | Published notice requires a specific agreement for display/redistribution. Plans differ in coverage/limits. | Owner agreement and field-level local display/storage/report/LLM rights; no live entitlement tested and no assumption existing CLI licenses new use. |
| [TradingAgents metadata](https://github.com/TauricResearch/TradingAgents/blob/main/pyproject.toml), [README](https://github.com/TauricResearch/TradingAgents) and [license](https://github.com/TauricResearch/TradingAgents/blob/main/LICENSE) | Moving main declares Python >=3.11 and Apache-2.0; dependency bounds conflict with core (`rich>=14` vs 13.9.4, `typer>=0.21` vs 0.13.0, `markdown-it-py>=4` vs 3.0.0, `typing-extensions>=4.14` vs 4.12.2). README describes trader/portfolio roles and saved reports/memory. | No tag/commit accepted or installed, no dependency resolution/worker sandbox proven. Review actual release NOTICE/transitive/data/model licenses, default network/storage and read-only feasibility in an authorized spike. |

## Review and verification record

Independent reviewer `srs_independent_review` performed a read-only review of
the draft against the supplied addendum, approved baseline, AGENTS, accepted
ADRs, finance/testing contracts, service models/callers and regression assertions.
It confirmed unchanged approved body through M6 and §§24–27, all 143 unique IDs,
preserved architecture/CLI/numeric/provider policies and explicit owner gates.
No other substantive addendum requirement was lost by condensation.

One P1 finding: AI1010's “reject or mark unsupported claims” could allow
publication of unsupported factual claims. Corrected to withhold them from
published reports; sanitized validation failures/partial diagnostics remain
possible. Two P2 findings: qualify the DEV-003-only statement as historical
v1.1 wording (corrected), and replace the review-record placeholder (this record).
The reviewer read the corrected files again and returned **PASS**, with no
remaining findings. Reviewer conclusion: suitable for owner review;
this technical finding is **not** product acceptance or permission to implement.
The reviewer did not run tests or independently reverify external rights.

Local structural check passed: normalized exact comparison preserves §§1–M6
and §§24–27 against `5bed5d3`; all expected IDs occur once, and relative document
links resolve. `git diff --check` passed after removing whitespace in the newly
changed header. Only SRS.md and this report are staged; no secrets or generated
artifacts were found in the diff review.

Canonical repository environment was recreated using existing Python **3.12.10**
and unchanged `python -m pip install ".[dev]"` pins. The initial global runtime
lacked pytest; no unsupported Python 3.14 test run or new toolchain was used.
No system software or M7–M10 dependency was installed.

| Command actually run with `.venv/Scripts/python.exe` | Result |
| --- | --- |
| `python -m pytest tests/test_baseline.py tests/test_packaging.py tests/test_repository_hygiene.py -q --tb=short` | 24 passed in 63.94s; documentation staged |
| `python -m pytest -q --tb=short` | 2507 passed in 126.90s |
| `python -m ruff check .` | Passed |
| `python -m mypy` | Passed; configured `config.py` only |
| `python -m pip check` | Passed |

Not verified locally: Python 3.11 (only supported 3.12 was used), future M7–M10
runtime/exit behavior (unimplemented), account/provider licensing (not supplied),
upstream worker compatibility/security and paid LLM behavior (no authorized spike
or paid calls). Baseline implementation CI is M6 evidence only. This proposal's
hosted CI is reported separately on its PR; green tests do not accept the SRS.

No implementation issues or milestone containers are created. After owner
acceptance, address current milestone ADRs and precise contracts first; only then
create bounded dependency-ordered implementation issues. Keep later milestones
at coarse planning depth. Do not change this acceptance record to Approved from
green tests, a PR merge alone or an agent review.
