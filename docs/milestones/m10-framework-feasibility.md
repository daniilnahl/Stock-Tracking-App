# M10 framework feasibility — issue #189

**Static assessment, 2026-10-18; proposed, not an accepted architecture decision.**
Parent: [M10 — AI Research Agents](https://github.com/daniilnahl/Stock-Tracking-App/milestone/11).
[Issue #189](https://github.com/daniilnahl/Stock-Tracking-App/issues/189)
authorizes one focused source-review session of at most 45 minutes. No upstream
code was installed, imported or executed; no model, market-data, paid, account
or private-data operation was performed. Reading public source through GitHub
and web tools is the only external acquisition in this assessment.

## Authority and local baseline

[SRS §23.10](../../SRS.md) AI1001–AI1032 are feasibility targets, not blanket
production acceptance. Accepted [ADR-0017](../adr/0017-user-criteria-taurus-discovery.md)
assigns criteria-driven discovery to Taurus; the product name does not select
TradingAgents. [ADR-0018](../adr/0018-custom-criteria-editor.md) fixes the exact
M9 descriptive envelope, not financial interpretations or an executable search.
[ADR-0005](../adr/0005-canonical-python-dependencies.md) preserves pip/pyproject
and Python 3.11/3.12. [ADR-0013](../adr/0013-local-read-only-rest-api.md) and
[ADR-0014](../adr/0014-local-read-only-dashboard.md) supply existing local access
and presentation boundaries. This document accepts none of the open M10 choices.
The attached master-agent document's M2 placeholder is not this task's scope.

Inspected local implementation and callers: [criteria preparation](../../frontend/src/features/criteria.ts),
[editor](../../frontend/src/features/StockCriteria.tsx), [app state](../../frontend/src/App.tsx),
[API factory](../../src/stock_tracker/api/app.py) and [dependency metadata](../../pyproject.toml).
Inspected associated [criteria tests](../../frontend/tests/criteria.test.ts),
[editor tests](../../frontend/tests/criteria-editor.test.tsx),
[API tests](../../tests/test_api_foundation.py) and [packaging tests](../../tests/test_packaging.py).
These define exact decimal strings/null, ordered duplicate labels, all/any,
immutable snapshots, no fetch/storage during preparation, an existing bounded
API route set, and exact installed dependency/asset checks. There is no Taurus
receiver in that inspected API surface. No public interface changes here.
Follow [TESTING.md](../TESTING.md) for actual verification; reading tests is not
running them. The prior moving-main review is [historical evidence](m7-m10-srs-review.md).

## Reproducible candidate and evidence limits

Candidate only: TauricResearch/TradingAgents commit
`e8f5503e9b86d5c2710b0c76b1f686703968c9df`, the 2026-10-16 v0.7.0 merge.
GitHub connector commit search returned that exact [commit][commit]; its pinned
[package initializer][init] declares 0.7.0. Every upstream source reference below
uses that commit. The pinned [metadata][metadata] was also read through the web
reader. The moving commits page returned an older cached September view, so it
was not used to identify the pin. Shell GitHub API access failed DNS resolution;
connector reads succeeded. A tag name is not a substitute for this immutable pin.

Facts below are static observations of the listed files. They do not establish
installed-wheel contents, a complete dependency license inventory, absence of
other side effects, runtime sandbox enforcement, performance or source rights.
No claim that this candidate is the only or best framework follows from this
bounded review. A different revision needs a fresh review.

## Compatibility and license findings

The candidate declares Python >=3.11: metadata overlaps both core runtimes, but
that does not prove its transitive dependencies resolve on either runtime.
Its broad lower bounds are not this app's exact-pin policy. These direct conflicts
alone rule out adding this version to the unchanged core environment:

| Distribution | Core exact pin | Candidate lower bound |
| --- | --- | --- |
| rich | 13.9.4 | >=14.0.0 |
| typer | 0.13.0 | >=0.21.0 |
| markdown-it-py | 3.0.0 | >=4.0 |
| typing-extensions | 4.12.2 | >=4.14.0 |

The candidate also adds LangChain model clients, LangGraph/SQLite checkpointing,
cryptography, pandas, requests, stockstats, yfinance and other packages absent
from core metadata. Its dev Ruff >=0.16 differs from core 0.8.4; do not combine
upstream dev extras with core tooling. Packaging >=24 and python-dotenv >=1
allow the corresponding core pins; no complete resolution or NumPy/pandas
compatibility claim is made. No package-manager or Python change is proposed.
Source: pinned [pyproject.toml][metadata], compared with local metadata.

The inspected [LICENSE][license] is Apache-2.0. Redistribution requires a license
copy, prominent notices in modified files, retention of pertinent source notices,
and reproduction of applicable NOTICE attribution if the distributed work
includes it (§4). Trademark permission is limited (§6); patent termination and
warranty limitations also apply. An exact root `NOTICE` lookup at this commit
returned 404. That observation does not prove a release archive/wheel, nested
component or dependency has no notice obligations. Before distributing any
selected code, inventory its actual artifact, bundled assets and every resolved
dependency; preserve required notices and record modifications. No source copied
into this app by this documentation change. Data/news/social feeds, model use,
transmission, report retention and redistribution need independent rights review
(AI1008/AI1026); an Apache code license supplies none of those permissions.

## Inspected behavior and confinement implications

| Surface and primary source | Observed fact | Consequence for a future integration |
| --- | --- | --- |
| [Initializer][init], [defaults][defaults] | Package import searches and loads `.env` and `.env.enterprise` from the working-directory ancestry; defaults read environment overrides at import. | Do not import into core or inherit the user's environment/home/working directory. Environment config is not a security boundary. |
| [Graph constructor and propagation][graph] | Constructor creates results/cache directories, constructs quick/deep model clients, memory and reflector, then compiles the graph. `create_run_state` resolves an instrument via Yahoo identity lookup; `propagate` takes one company/date, not the M9 criteria envelope. | No IO-free core factory, native criteria discovery or compatible identity mapping is established. Instantiation is not an innocuous schema check. |
| [Graph setup][setup], [analyst plan][plan] | Default market/social/news/fundamentals analysts run concurrently, with Memory Log beside them; bull/bear debate leads to Research Manager → Trader → risk debate → Portfolio Manager. Selecting fewer analysts still constructs and routes Trader/Portfolio Manager. | Neither analyst selection nor a one-round setting makes this graph research-only. Need an explicitly reviewed replacement graph or avoid this graph. |
| [Trader][trader], [Portfolio Manager][manager] | Trader requests Buy/Hold/Sell plus entry, stop and sizing; manager returns a trading rating, with structured-output/free-text paths. | These are prohibited output/action surfaces until separately decided; hiding the final rating after execution does not remove them. No brokerage/order submission API was observed in these inspected nodes. This is not a repository-wide proof that no execution surface exists. |
| [Analyst tools][tools], [router][router], [defaults][defaults] | Market offers prices/indicators/snapshot; fundamentals offers overview/statements/insiders; news offers ticker/global news, macro and prediction markets. Defaults choose Yahoo, SEC→Yahoo statements, FRED and Polymarket. Router also supports Alpha Vantage and configured fallback chains. | Existing app FMP/Finnhub entitlements/adapters are not automatically reused. Replace tools with a finite approved registry and validate arguments before dispatch; fail closed on unknown tools, redirects, URLs and vendors. |
| [Yahoo prices][prices], [Yahoo news][news] | Prices call yfinance history and round price columns to two decimals for CSV. News calls Yahoo ticker news and search, then formats publisher/link/summary text. | Do not use formatted/rounded upstream prose as exact app arithmetic or criterion evidence. Endpoint/network behavior inside third-party clients is unverified; require captured typed evidence and explicit coverage. |
| [Sentiment analyst][sentiment], [post screening][screen] | Social node prefetches news, StockTwits and Reddit outside ToolNode; a TypeSafe key enables additional HTTP post screening, with retries and a thread pool. Historical social feeds explicitly lack point-in-time archives. | ToolNode-only interception misses acquisition. No inherited keys; disable social/enrichment paths for a first PoC. Do not treat this as approved historical evidence or injection defense. |
| [Memory log][memory], [graph][graph], [settlement][settlement] | Defaults store markdown memory under `~/.tradingagents/memory/trading_memory.md`; resolved-entry cap defaults to None and pending entries are not pruned by that cap. A run settles due decisions across tickers, fetching returns/benchmarks and invoking reflection, then logs its new decision. | Hidden extra data/model work and cross-run context are incompatible with a per-request budget/privacy assumption. Remove the memory/settlement node; path overrides alone do not prevent those calls. Its financial calculations are not adopted. |
| [Graph logging][graph], [report writer][reporting], [checkpointer][checkpoint] | Results/cache default under `~/.tradingagents`; propagation writes full report/debate/trade state JSON. Explicit report saving writes markdown and normally HTML. Debug prints messages. Checkpoint defaults off; enabling uses per-ticker SQLite under cache/checkpoints; clear APIs delete rows/files. | `--no-save`, debug=False and checkpoint=False do not establish no persistence. Deny access to user files/databases, bypass state/debate dumps and checkpoint deletion, and permit only bounded sanitized summaries in a dedicated temporary run directory. |
| [CLI][cli], [updates][updates], [auth implementation][auth] | CLI exposes portfolio-file input, backtests, checkpoint clearing and login/logout. Interactive startup update logic can fetch GitHub releases/Tauric notices and cache them; it has CI/unattended/opt-out gates. Auth code has token-file, refresh/revoke HTTP and loopback sign-in paths. | Exclude CLI/auth/update modules and private portfolios from the adapter. Never reuse this app's or user's account files; upstream comments about authentication are not verified service permission. No account flow was exercised. |
| [Defaults][defaults], [graph setup][setup] | Defaults cap tool rounds at 20, recursion at 100, debate/risk rounds at 1; model max_tokens and SDK retry setting are None. Tool rounds can contain multiple calls, and parallel analysts/memory add work. | These are useful workflow controls, not hard elapsed/request/token/spend/storage guarantees. Reserve worst-case authorized spend at every call boundary before any future paid use. |

The inspected [upstream end-to-end test][upstream-test] scripts models, replaces
vendor implementations, redirects paths into tmp_path, and asserts a logged
trading decision. It also covers checkpoint resume and bounded tool loops. This
is useful evidence of injectable seams, not proof of OS isolation, no real imports,
rights, actual cost enforcement or read-only behavior. No upstream tests ran.

## Alternatives — recommendations only

| Alternative | Fit and cost | Assessment |
| --- | --- | --- |
| Direct core import/install | Four explicit pin conflicts; import-time dotenv, constructor IO and full trading workflow share core process privileges. | Reject for the unchanged core. No upgrade/unpin request is made. |
| Isolated worker/service with a small adapter | Could protect dependency resolution and permit OS-level network/filesystem controls; must remove trader/manager/memory paths, replace acquisition, validate output and prove process cleanup. A subprocess alone is not a sandbox. | Conditional research candidate only. No accepted feasibility/isolation ADR or demonstrated sandbox exists. Modification/fork maintenance and license notices must be budgeted. |
| Adapter-only owned research orchestration | Does not depend on this upstream graph; fixture-backed input/evidence/output validation can test the M9 boundary without its dependency or action surfaces. Real discovery/tools/models remain unimplemented. | Recommended first PoC proposal, because exact criteria and safety boundaries can be tested independently. It does not select a production framework or claim discovery capability. |

The stock/date analysis graph is not demonstrated to enumerate a supported
universe, preserve arbitrary M9 text semantics, verify each criterion or produce
coverage-aware candidate results. A polished report or BUY label cannot satisfy
AI1031/AI1032. No native read-only switch was found in the inspected configuration
and graph APIs. Further source audit and an authorized isolated execution test
would be necessary before claiming safe reuse of individual analysts.

## Proposed future PoC charter — not authorization to execute

Create a separate bounded issue and obtain owner approval for this charter and
its isolation/runtime plan before installing or executing upstream. Do not begin
against another agent's unmerged contract. Review/accept a feasibility ADR before
production implementation. The proposed first experiment uses adapter-only
orchestration; a later upstream-worker experiment needs its own dependency/artifact
and graph-pruning approval.

- **Time and inputs:** One engineering day maximum; one worker at a time, ten
  fixed offline cases, at most three synthetic candidate identities and twenty
  criteria per case. Preserve the exact ADR-0018 envelope, duplicate ordering,
  all/any, signed zero, trailing zeros and nullable endpoints. No changed M9 UI/API.
- **Allowed actions:** Read an explicitly supplied synthetic fixture directory;
  run owned adapter/validator code with a scripted fake model; write a sanitized
  result summary to a new disposable run directory. No upstream execution in
  this first phase. No real holdings/database, home, dotenv, account files, live
  provider/model, network, shell tools, background refresh or brokerage access.
- **Enforced ceilings:** Before any run, verify OS/network/filesystem denial;
  otherwise stop. One process, no child creation, at most five fake-model calls
  and ten fixture lookups per case, 60 seconds per case including shutdown,
  64 KiB input/64 KiB output per case, and 1 MiB total disposable output. Fake
  calls consume no real tokens and the monetary budget is zero. A supervisor
  must kill/reap a timed-out process and refuse further calls after cancellation.
- **Cases/evidence:** Exact roundtrip; unsupported financial semantics; missing
  or conflicting evidence; incomplete universe; genuine empty synthetic result;
  injection in criteria/source text; fabricated references; malformed/oversized
  model output; timeout/cancel; repeated/exhausted calls. A claimed match needs
  compatible captured fixture evidence and validator acceptance. Unsupported
  facts are withheld; no BUY/HOLD/SELL opinions or forecasts are published.
- **Acceptance artifacts:** Record fixture hashes, pin/configuration, admission
  counters, permitted evidence IDs/times, limits, sanitized status/errors, and
  denied actions. Prove zero external requests, zero writes outside the run
  directory, bounded cleanup, unchanged core behavior and no altered user data.
  Failed/partial/empty outcomes stay distinct. This tests mechanics on synthetic
  evidence, not vendor rights, search completeness or investment performance.
- **Stop conditions:** Unexpected network/file/credential access, inability to
  enforce any ceiling, surviving child/process, action/trade node invocation,
  hidden criteria relaxation, unknown metric semantics, missing licensing,
  incompatible dependencies or core regression. Preserve sanitized diagnostics;
  do not relax controls or add live access to rescue the experiment.

Approval gaps remain: source/universe and financial metric definitions; evidence
and model transmission/retention rights; framework/dependency selection and
artifact notices; actual OS sandbox and resource mechanisms; consent/privacy;
versioned execution/report/lifecycle/storage/API contracts; hard paid-call spend
reservation (unknown pricing blocks that path); opinion policy; and independent
failure/attack/cutoff audit. Existing proposed SRS/decision gates remain open.
The first PoC cannot close them or qualify M10 for release.

## Verification record

This is one new Markdown file. Local relative links and final diff require review;
canonical Python, Ruff, configured mypy, pip check and staged hygiene must be
recorded on this branch before publication. Frontend rebuild/browser execution
is not required for this documentation-only change. Historical main/PR CI does
not substitute for this branch's checks. No upstream runtime result is claimed.

[commit]: https://github.com/TauricResearch/TradingAgents/commit/e8f5503e9b86d5c2710b0c76b1f686703968c9df
[init]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tradingagents/__init__.py
[metadata]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/pyproject.toml
[license]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/LICENSE
[defaults]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tradingagents/default_config.py
[graph]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tradingagents/graph/trading_graph.py
[setup]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tradingagents/graph/setup.py
[plan]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tradingagents/graph/analyst_execution.py
[trader]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tradingagents/agents/trader/trader.py
[manager]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tradingagents/agents/managers/portfolio_manager.py
[tools]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tradingagents/agents/tools.py
[router]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tradingagents/dataflows/router.py
[prices]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tradingagents/dataflows/vendors/yahoo/market.py
[news]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tradingagents/dataflows/vendors/yahoo/news.py
[sentiment]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tradingagents/agents/analysts/sentiment_analyst.py
[screen]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tradingagents/agents/post_screen.py
[memory]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tradingagents/memory/log.py
[settlement]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tradingagents/memory/settlement.py
[reporting]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tradingagents/reporting.py
[checkpoint]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tradingagents/graph/checkpointer.py
[cli]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/cli/main.py
[updates]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/cli/updates.py
[auth]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tradingagents/llm_clients/chatgpt_auth.py
[upstream-test]: https://github.com/TauricResearch/TradingAgents/blob/e8f5503e9b86d5c2710b0c76b1f686703968c9df/tests/test_graph_end_to_end.py
