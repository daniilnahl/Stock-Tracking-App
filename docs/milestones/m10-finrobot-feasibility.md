# M10 FinRobot component and adapter feasibility — issue #197

**Static assessment, 2026-10-18; proposal, not runtime acceptance.**
[Issue #197](https://github.com/daniilnahl/Stock-Tracking-App/issues/197) belongs to
[M10 — AI Research Agents](https://github.com/daniilnahl/Stock-Tracking-App/milestone/11).
The owner selected FinRobot and excluded TradingAgents. This review recommends a
specific FinRobot component for the next contract review; it does not reopen the
framework choice or replace it with an invented agent stack.

## Authority, scope and evidence

Baseline: main `a3723255b15d36f8f5c57f10310f281c5cbb8bb5`.
[AGENTS.md](../../AGENTS.md), [SRS §23.10](../../SRS.md#milestone-10--ai-research-agents),
[ADR-0017](../adr/0017-user-criteria-taurus-discovery.md),
[ADR-0018](../adr/0018-custom-criteria-editor.md),
[ADR-0005](../adr/0005-canonical-python-dependencies.md),
[financial definitions](../FINANCIAL_CALCULATIONS.md) and
[testing policy](../TESTING.md) control this work. AI1001–1032 are the review
targets, not blanket production acceptance. Undefined valuation, FX, forecasts,
EPS comparisons or selection/ranking semantics are not adopted from upstream.

The owner's Linux-only sandbox decision is already recorded in the
[merged M10 plan](m10-plan.md#what-remains-of-m10): on Windows, agents run through
WSL or Docker; native Windows sandboxing is not required. Linux, WSL or Docker
availability is not proof of host-filesystem, process or network confinement.
This assessment requires that proof later without reopening the OS choice.

Inspected local [dependency metadata](../../pyproject.toml),
[criteria implementation](../../frontend/src/features/criteria.ts), its
[editor caller](../../frontend/src/features/StockCriteria.tsx),
[criteria tests](../../frontend/tests/criteria.test.ts),
[API factory](../../src/stock_tracker/api/app.py),
[API tests](../../tests/test_api_foundation.py) and
[packaging tests](../../tests/test_packaging.py). Criteria preparation preserves
ordered duplicate labels, all/any and exact decimal strings/null without a
request; the inspected API route set has no Taurus receiver. Installed core
pins and packaged resources have strict tests. No public interface changes here.

This is one focused source-review session, bounded to 45 minutes, using the
prior preliminary inspection as input and rechecking the immutable manifests,
license/NOTICE/trademark and relevant callable sources. No upstream installation,
import, execution, credential/private-data access, account operation, scraping,
model/provider/paid call or Linux sandbox experiment occurred. Public source
reads are the only external acquisition. #198 owns the independent safety
assessment; #192 will define the proposed shared execution contract. Neither
unmerged output is an input to this report.

Source pin: [AI4Finance-Foundation/FinRobot commit][commit]
`2717499b8e30f242640af08c4ad9afd1113c2d45` (2026-09-28), verified by GitHub
connector commit lookup and pinned file reads. The pinned V2 manifest was also
read through the web reader. This is a source-review pin, not an accepted build
artifact or dependency lock. Sources below are immutable at that commit; claims
are limited to inspected paths, not every file or release artifact.

## Generations, packages and actual compatibility

| Generation / source | Observed entry point and metadata | Fit for this task |
| --- | --- | --- |
| V0 AutoGen: [root setup][setup], [requirements][v0requirements], [workflow][v0workflow] | Root distribution `FinRobot` 0.1.5 maps import `finrobot` to `finrobot_autogen/finrobot`; also discovers `finrobot_equity` packages. Python `>=3.10,<3.12`. AutoGen assistant/user-proxy workflows default to code execution in `coding`, with `use_docker=False`; chat enters a disk-cache context. | Reject root installation for the proposed adapter. Python 3.12 is excluded, direct core conflicts exist, and host-code execution is outside research-only scope. |
| V1 equity: [requirements][v1requirements], [launcher][v1launcher], [guide][v1readme] | Separate web/report application; launcher calls `finrobot_equity.web_app.main:app`. Requirements include OpenAI/Agents SDK, NumPy <2, report/PDF/web/database dependencies. Python 3.9+ is a requirements comment, not a proven support declaration. | No need to adopt a second web app or report pipeline. Its NumPy range conflicts with core. Guide examples generate forecasts/files and can regenerate model text; not a criteria receiver. |
| V2 backend: [manifest][v2manifest], [initializer][v2init], [SDK][sdk] | Nested `finrobot_desktop/` distribution `finrobot` 2.0.0 declares Python >=3.11, Hatchling, PydanticAI and CLI `finrobot.cli:cli`; initializer lazily exports `FinRobot`/`PipelineResult`. | Recommend reviewing only the Python backend pipeline/executor seams below in an isolated worker. No React/Tauri shell, upstream server, full pipeline or backtest extra is accepted. |

Distribution names `FinRobot` and `finrobot` normalize to the same package name;
both generations also occupy import `finrobot`. They must not be mixed in one
environment. A root Git installation follows root setup, not the nested V2
project. A future approved artifact must explicitly identify the V2 subdirectory,
commit, included package files and hashes; a bare package name/version is not
sufficient to identify it. This report neither checks current PyPI artifacts nor
assumes they match the source tree. Root setup's broad exception on requirements
loading can produce empty requirements when that read fails, another reason to
inspect the actual artifact rather than infer its dependency metadata.

Actual direct conflicts, compared with current core metadata:

| Generation | Upstream constraint | Core pin | Result |
| --- | --- | --- | --- |
| V0 | numpy==1.26.4 | numpy==2.2.0 | Incompatible |
| V0 | starlette==0.37.2 | starlette==1.8.0 | Incompatible |
| V0 | typing_extensions==4.9.0 | typing_extensions==4.12.2 | Incompatible |
| V1 | numpy>=1.24.0,<2.0.0 | numpy==2.2.0 | Incompatible |
| V2 | fastapi>=0.115; uvicorn>=0.34 | fastapi==0.141.0; uvicorn==0.54.0 | Direct ranges permit pins |
| V2 | click>=8.1; matplotlib>=3.8 | click==8.1.7; matplotlib==3.10.0 | Direct ranges permit pins |

These are different findings from the excluded TradingAgents report. V2 does
not declare its own direct Rich/Typer/markdown-it/typing_extensions conflicts.
Its additional dependencies include `pydantic-ai>=1.70.0`, pydantic-settings,
aiosqlite, yfinance, PyYAML, Jinja2, rank-bm25, keyring, edgartools and ddgs.
Distribution/import names can differ, e.g. edgartools is imported as `edgar`;
absence of the same import spelling from core is not a dependency analysis.

V2 Python metadata overlaps core-supported 3.11/3.12; this is not proven runtime
support or resolution. Direct overlap does not establish compatibility of
PydanticAI's transitive Pydantic/httpx/model SDK requirements with core pins, nor
that every dependency version permits both Python runtimes. No resolver, build,
install, wheel import, Linux runtime or upstream test ran. A worker-specific
reviewed resolution/artifact inventory is required before Phase B. Preserve
core Python `>=3.11,<3.13`, pip and exact pyproject pins; upstream Hatchling/uv
examples do not authorize changing this app's backend or package manager.

## License and distribution obligations

The inspected [root LICENSE][license] is Apache-2.0. Its redistribution conditions
include license copy, prominent notices in modified files, pertinent source
notices, and applicable NOTICE attribution. The actual [NOTICE][notice] identifies
AI4Finance attribution and trademarks and requires retaining that file on
redistribution. [Trademark policy][trademark] permits truthful reference to the
software but prohibits misleading official/endorsed derivative branding and use
of the mark as a derivative product name. This assessment makes no branding
change or claim of endorsement.

V2 [skill attribution][attribution] identifies conversion of Anthropic financial
playbooks under MIT. Do not automatically bundle/load all skills: inventory any
selected skill's original license, revision, notices and contents first. Root
NOTICE lists some third parties; it is not a complete dependency/license bill of
materials. Verify exact worker artifact, bundled assets and resolved transitive
licenses/NOTICE obligations before redistribution. No upstream code or assets
are copied by this change. Source license permission does not establish market
data, news, search, model transmission, retention, report or redistribution
rights. Those remain activation gates.

## Callable seams and effects observed in V2

| Pinned source / seam | Inspected behavior | Adapter implication |
| --- | --- | --- |
| [SDK][sdk] `FinRobot.__init__`, `_ensure_deps`, `_run_pipeline` | Constructor resolves settings and validates model config. First pipeline call loads skills if present, builds default provider/cache dependencies and all five subagents. `_run_pipeline` validates a ticker and invokes a registered pipeline; sync calls own a persistent event loop. | SDK is an informative facade, not an accepted no-effect entry point. Avoid using it unchanged for a fixture-only experiment; default settings can create home/cache directories before a pipeline executes. Ensure async resources close. |
| [Registry][registry], [agent factory][agents] | Registered pipelines include research/comps/DCF/LBO/DDM/earnings/IC memo. Five subagents load Markdown instructions and share the configured model; the data agent gets `query_financial_data`. | Do not invoke registry defaults or automatically register new future pipelines. Review explicit instructions/tools/callable list. Financial operators/ratings are not approved app definitions. |
| [Protocols][protocols], [runner][runner], [dependencies][deps] | `PipelineStep` accepts an executor/validator; default executor calls `agent.run(prompt, deps=deps)`. `FinRobotDeps` accepts a data layer and optional skill/artifact/coverage stores and run semaphore. Runner uses steps, validation/retry and optional artifact builder/store. | These are plausible narrow injection seams for a separately authorized pinned FinRobot test using fake executor/model/data and no stores. Runtime/import graph and hidden effects still need proof. No inheritance from whole SDK/default provider graph is necessary in principle. |
| [Data factory][datafactory] | Yahoo plus news aggregation always registered; FMP/Finnhub/Adanos are key-dependent, SEC depends on valid identity, optional Alpha Vantage enriches news. Builds a SQLite data cache. | No-key is not no-network. Replace acquisition with a fixture-only data port; existing app credentials/rights/adapters are not automatically shared. |
| [Orchestrator][orchestrator] | Lead agent includes DuckDuckGo search; financial-data, report-history, coverage and backtest tools are broader than a single research step. | Exclude lead/default tool registration from first PoC. No generic web, history/coverage/private-store access or backtest tool. |
| [Settings][config], [paths][paths], [secret store][secrets] | Normal user settings drop environment/dotenv sources; infrastructure overrides and HTTP proxy inheritance remain. Model defaults empty. Cache-path resolution can create `~/.finrobot`/logs. Paths include artifact/run/cache databases and settings. Keychain storage has plaintext-file fallback. Default file logging is enabled. | Construct explicit isolated settings/paths and no secrets; deny access to real home/config, inherited proxy/account state and core data. Empty model alone does not confine other effects. |
| [Authentication][auth] | Capability middleware is a no-op without configured token; SSE can carry token in query. | Retain this app's authenticated local API; do not adopt upstream browser/server posture or token URL scheme. |
| [Runner][runner], [protocols][protocols], [research pipeline][research] | Default three retries/backoff and character compaction; default executor has no explicit usage-limit argument. Research SEC timeout explicitly cannot stop the underlying thread. | Not proof of hard spend/token/deadline/cancellation enforcement. Control every dispatch outside the model and reap workers before releasing capacity. Hiding retries does not bound billable work. |
| [BackTrader adapter][backtest] | Optional simulation includes buy/close, dynamic strategy loading and threaded execution. | Exclude simulation/strategy loading. No live brokerage submission observed in these inspected seams; this is not a repository-wide absence proof. |

The [upstream progress tests][upstreamtests] inject fake executors/agents and
check start/end/retry events. They support the existence of callable seams,
not Linux confinement, real dependency compatibility, citation support or hard
resource guarantees. They were read, not run. Upstream field validation and
numeric auditing cannot replace this app's financial/evidence rules.

## Stock analysis versus criteria discovery

The inspected SDK/pipeline entry takes a ticker; M9 provides a version-1 ordered
criteria description. A ticker syntax check does not establish canonical stock
identity, an approved search universe, exhaustive search, field meaning, financial
comparability or a criterion match. DuckDuckGo search/peer analysis/coverage tools
are not evidence of a compliant arbitrary-criteria search. No ADR-0018 receiver
or AI1031/1032 discovery guarantee is established by these inspected paths.

A future trusted adapter must retain the exact snapshot and revalidate it before
execution. Names/text are untrusted data, never commands, URLs or permission to
choose new financial semantics. Preserve signed zero, trailing zeros, null
endpoints, row order/duplicates and explicit all/any; resolve meaning and evidence
under accepted contracts. Neither model inference nor upstream computed values
may silently normalize/relax thresholds or fill unknown evidence. Unknown units,
period/basis, source rights or universe coverage must prevent unsupported claims.
Distinguish empty complete synthetic results from incomplete/failed/disabled
search. Production discovery requires separate source/universe and qualification
contracts; this static assessment supplies none.

## Integration alternatives and recommendation

| Approach | Assessment |
| --- | --- |
| Direct core install/import | Reject as first approach. V0/V1 have explicit conflicts; V2 direct overlap is insufficient proof, and upstream stores/network/defaults would share core privileges. No core upgrades or API changes proposed. |
| Isolated Linux FinRobot worker behind small adapter | Recommended target: selected V2 Python runner/step/executor seams with explicit data/model ports, no default SDK/provider/server/tool graph. Protects core dependencies in principle; approved package assembly, actual transitive resolution and OS controls remain prerequisites. A process/container alone proves none of them. |
| Owned adapter-only experiment | Recommended Phase A to establish exact data admission, deterministic status/evidence validation and limits using synthetic ports. Proves mechanics only; it cannot establish FinRobot runtime integration and is not a substitute production agent stack. |

## Proposed two-phase synthetic PoC charter

This is a concrete proposal for #192 review, not its ADR, a shared runtime schema,
an approved sandbox mechanism or authorization to execute either phase here.
The Linux-only platform decision is settled; exact packaging, resource enforcement,
WSL/Docker host-mount/egress policy and fake-call injection still require reviewed
implementation and proof. No native Windows sandbox investigation is needed.

**Phase A — owned adapter mechanics, no upstream import:** one engineering day
maximum, ten fixed offline cases, at most three synthetic candidate identities,
and ADR-0018's existing one-to-twenty criteria limit. Use fixture-only data and
scripted fake model ports; validate unchanged input, evidence association and
safe outcome handling. Success means only that the owned boundary works.

**Phase B — actual pinned V2 component execution, separately authorized:** after
accepted #192 scope, reviewed V2 packaging/transitive pins, exact component and
fake-call seams, and demonstrated Linux denial/limits, execute only the selected
FinRobot runner/steps with an injected fake executor/model/data port. Do not call
unmodified SDK initialization, default registry pipelines, provider factory,
lead agent, server, secret store, valuation/backtest operators or default skills.
Any unavoidable import-time dependency/effect must be documented and reviewed
before execution; stop rather than expanding the allowlist during the run.
This phase must establish actual pinned FinRobot call counts, resource cleanup,
output validation and unchanged core behavior; Phase A results cannot substitute.
No live model/provider or paid call is part of either proposed phase.

Proposed common bounds and evidence, pending the execution contract:

- One run/worker at a time, ten cases maximum per phase; 60 seconds per case
  including cleanup, at most five fake-model dispatches and ten fixture lookups.
  Maximum 64 KiB input and 64 KiB output per case; 1 MiB total scratch output.
  Monetary budget zero; no real tokens, keys or account access. Input limits
  must fail visibly, never truncate or rewrite the user's accepted snapshot.
- Read-only selected code/fixtures, fresh bounded scratch directory, no real
  home/core SQLite/cache, no inherited credentials/handles, no child execution,
  and no networking including DNS/proxy/loopback. Linux OS denial/resource proof
  must precede worker execution; WSL/Docker must not expose unrestricted host
  mounts or sockets. Concrete mechanisms belong to the safety/execution review.
- Cases: exact decimal/null/order roundtrip; all/any; unknown metric/context;
  incompatible/missing/conflicting evidence; partial universe versus actual
  empty synthetic result; malicious criteria/source text; fabricated citation;
  malformed/oversized output; exhausted calls/retries; cancel/timeout/crash.
  No claimed match without compatible captured fixture evidence. Unsupported
  facts withheld; no opinions, forecasts or fabricated winner published.
- Record fixture hashes, upstream/component/artifact pins, explicit settings,
  permitted evidence IDs/cutoffs, dispatch counters, actual denials, bounded
  status/errors and resource cleanup. No raw prompts, debate logs, secret text
  or chain-of-thought. Prove no external request or out-of-directory write,
  no surviving worker, no changed user data and working core paths with AI absent.
- Stop on unexpected imports/effects, attempted network/file/credential access,
  unbounded chargeable path, surviving process/thread, inability to enforce a
  ceiling, criteria mutation, unsupported financial interpretation, license gap
  or core regression. Preserve sanitized diagnostics; do not rescue the run by
  enabling providers, weakening limits or installing another framework.

Still unresolved: accepted exact V2 artifact/subset and maintenance strategy;
worker dependency resolution/build licenses; actual Linux enforcement and host
boundary; permitted discovery universe/tools and source/model rights; financial
field meanings; private-input admission; output/API/lifecycle/storage/retention
contracts; hard pre-call spend reservation and uncertain cancellation settlement;
opinion policy; independent evidence/attack/cutoff audit and rollout acceptance.
Owner platform/framework selection settles direction, not these contracts.

## Verification record and limits

Changed only this Markdown report. Link/reference and diff self-review are
required before handoff; canonical full Python, Ruff, configured mypy, pip check
and staged hygiene remain required before publication under TESTING.md. Historical
main/other-PR checks are not results for this branch. No frontend rebuild/browser
profile is needed for documentation alone. Passing repository checks will not
prove FinRobot runtime, Linux sandbox, paid budget enforcement or M10 completion.

[commit]: https://github.com/AI4Finance-Foundation/FinRobot/commit/2717499b8e30f242640af08c4ad9afd1113c2d45
[setup]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/setup.py
[v0requirements]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_autogen/requirements.txt
[v0workflow]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_autogen/finrobot/agents/workflow.py
[v1requirements]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_equity/requirements.txt
[v1launcher]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_equity/run_web_app.py
[v1readme]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_equity/README.md
[v2manifest]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/pyproject.toml
[v2init]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/__init__.py
[sdk]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/sdk.py
[license]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/LICENSE
[notice]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/NOTICE
[trademark]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/TRADEMARK_POLICY.md
[attribution]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/skills/ATTRIBUTION.md
[registry]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/pipelines/registry.py
[agents]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/agents/factory.py
[protocols]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/pipelines/protocols.py
[runner]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/pipelines/runner.py
[deps]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/deps.py
[datafactory]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/data/factory.py
[orchestrator]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/orchestrator.py
[config]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/config.py
[paths]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/paths.py
[secrets]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/secret_store.py
[auth]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/auth.py
[research]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/pipelines/equity_research.py
[backtest]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/backtest/backtrader_adapter.py
[upstreamtests]: https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/tests/unit/test_streaming.py
