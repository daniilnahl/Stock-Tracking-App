# M10 FinRobot safety applicability — issue #198

**Status: proposal only, 2026-10-18.** This is a static, source-backed map for
[#198](https://github.com/daniilnahl/Stock-Tracking-App/issues/198) in
[M10](https://github.com/daniilnahl/Stock-Tracking-App/milestone/11). It does
not install, import, or execute FinRobot. It does not make a model, provider,
or paid call, accept an ADR, authorize a PoC, or change this application's
API or dashboard. Nothing below is an accepted runtime contract.

The general controls in
[the #191/#194 assessment](m10-safety-assessment.md) remain proposals. That
document has since been merged; merging the proposal does not make its broker,
ledger, or OS denials exist in this repository. This review only maps pinned
FinRobot surfaces onto those proposals. [#197](https://github.com/daniilnahl/Stock-Tracking-App/issues/197)
owns component, dependency, and license inventory. This file does not.

## Authority

[AGENTS.md](../../AGENTS.md), [SRS §23.10](../../SRS.md#milestone-10--ai-research-agents)
(AI1001–AI1032 as review targets), accepted
[ADR-0017](../adr/0017-user-criteria-taurus-discovery.md) and
[ADR-0018](../adr/0018-custom-criteria-editor.md), and the existing financial
restrictions govern the review. ADR-0017 assigns criteria-driven discovery to
M10. ADR-0018 accepts a nonexecuting editor whose prepared envelope is data,
not instructions. Neither accepts FinRobot execution, a tool allowlist, or a
financial formula.

Owner decisions of 2026-10-18 that this review uses, and does not reopen:

- FinRobot is the selected framework direction. TauricResearch/TradingAgents is excluded.
- The M10 agent sandbox is Linux-only. On Windows it runs through WSL or Docker. Native Windows sandboxing is not required.

D9 (hard spend reservation) and D11 (BUY/HOLD/SELL text) stay open. X716 still
excludes private holdings unless a separate exception is approved. No exception
is requested here.

## Pin and generations inspected

Source pin:
[`2717499b8e30f242640af08c4ad9afd1113c2d45`](https://github.com/AI4Finance-Foundation/FinRobot/commit/2717499b8e30f242640af08c4ad9afd1113c2d45)
(2026-09-28, `docs: lead with decision intelligence and the four-part principle`).
This is a read-only review pin, not an installation pin or an accepted artifact.
The tree was read over the network. No package was installed and no module was imported.

Three generations are present and were inspected. "Inspected" means the Python
execution, credential, network, and storage surfaces below were read. The
desktop TypeScript/Tauri UI was not adopted and was not reviewed component by
component. Vendored `SKILL.md` bodies were not copied.

| Generation | Tree | Distribution name | What was read |
| --- | --- | --- | --- |
| V0 AutoGen | `finrobot_autogen/` | Root [`setup.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/setup.py) installs this tree as import name `finrobot` (distribution `FinRobot` 0.1.5, Python `>=3.10,<3.12`) and also installs `finrobot_equity`. | Agents, tool registration, code/file tools, provider helpers, JSON-to-environment key loading. |
| V1 equity | `finrobot_equity/` | Same root `setup.py` (`finrobot_equity` and `finrobot_equity.*`). | Report pipeline, config-file keys, web app, subprocess runner, cookie sessions, SQLite. |
| V2 desktop/backend | `finrobot_desktop/finrobot/` | [`finrobot_desktop/pyproject.toml`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/pyproject.toml) names the package `finrobot` 2.0.0, Python `>=3.11`. Root `setup.py` does not install this tree. | Orchestrator tools, pipelines, providers, secrets, server/auth, SDK/CLI, backtest, skills, artifacts, transcripts. |

The root [`NOTICE`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/NOTICE)
states Apache-2.0 and that "FinRobot" and "AI4Finance" are trademarks of
AI4Finance Foundation. Derivative naming, logos, and redistribution must follow
its trademark policy, and redistributions must retain the NOTICE. That is a
source fact about the pinned file. It is not permission to transmit market data,
call a model, or inherit this application's API keys. Component and data/model
obligations remain with #197.

Importing the name `finrobot` is ambiguous: V0 and V2 both claim it, and only
V0 is what the root installer provides. A later adapter must not resolve that
clash by installing either distribution into this application's environment.

## How to read this document

| Label | Meaning |
| --- | --- |
| Source fact | Behavior read at the pin. It describes FinRobot, not this application. |
| Proposed control | A containment rule this review recommends. It is not implemented here and is not accepted by merging #194. |
| Unverified | Not demonstrated. Upstream comments, prompt text, and this review are not enforcement evidence. |

This repository has no FinRobot adapter, worker, or interceptor. Every
"interception today" cell below is therefore "none".

## Source facts

### Tool and code execution

V0 registers tools onto an AutoGen user proxy and runs chats with code
execution enabled. [`workflow.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_autogen/finrobot/agents/workflow.py)
defaults `code_execution_config` to `work_dir: coding` and `use_docker: False`,
with `human_input_mode="NEVER"` and `max_consecutive_auto_reply=10`.
[`coding.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_autogen/finrobot/functional/coding.py)
executes a caller-supplied cell through `IPython.get_ipython().run_cell`, and
reads, creates, and rewrites files under the relative `coding/` directory with
no path normalization. [`toolkits.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_autogen/finrobot/toolkits.py)
can register an arbitrary callable or every public method of a class.
[`agent_library.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_autogen/finrobot/agents/agent_library.py)
ships market and investor agents whose default toolkits include Finnhub,
yfinance, FMP, SEC-report retrieval, image display, and PDF report building.
`SingleAssistant.chat` enters AutoGen `Cache.disk()`; the cache location is
AutoGen's, not pinned in this tree.

V1's web task runner starts a child with `subprocess.Popen`, copies
`os.environ` into that child, and passes a config file path
([`web_app/main.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_equity/web_app/main.py)).
The request model accepts `fmp_api_key` and `openai_api_key` fields. Report
scripts then read keys from an INI file
([`common_utils.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_equity/core/src/modules/common_utils.py)).

V2 does not ship an `exec`/`eval` tool in the lead agent. It does ship a closed
tool set that is registered unconditionally in
[`create_lead_agent`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/orchestrator.py):

| Tool | Effect read at the pin |
| --- | --- |
| `duckduckgo_search_tool(max_results=8)` | Keyless web search, registered as a PydanticAI common tool. |
| `query_financial_data` | Model-chosen ticker and `DataType`, then `DataLayer.fetch` / `fetch_canonical`. |
| `ask_filings` | SEC 10-K question answering via `run_qa`. |
| `query_coverage_universe` | Reads the user's FinRobot watchlist; `refresh=True` live-fetches every name. |
| `find_reports` / `diff_reports` | Read artifacts already stored for this FinRobot user. |
| `run_monte_carlo` | Seeds a DCF from live data and returns a fair-value distribution plus an upside/downside sentence. |
| `run_backtest` | Runs a BackTrader SMA crossover and returns performance statistics. |
| `activate_skill` | Returns methodology text for a model-chosen skill id. |
| `run_equity_research`, `run_comps_analysis`, `run_dcf_valuation`, `run_lbo_analysis`, `run_ddm_valuation`, `run_earnings_analysis`, `run_ic_memo` | Each executes a multi-step pipeline. Descriptions in [`registry.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/pipelines/registry.py) tell the model to use them for research, valuation, LBO, and invest/pass memos. |

The data sub-agent receives only `query_financial_data`
([`factory.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/agents/factory.py)).
Other roles have no tools in that factory. The lead agent still has the full
set above. Invalid tool arguments are returned as strings or raised as
`ModelRetry` so the model can try again. That is a conversation retry, not an
authorization check.

Skills are Markdown. [`loader.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/skills/loader.py)
uses `yaml.safe_load` and stores the body as `full_content`.
[`render_pipeline_methodology`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/skills/pipeline_methodology.py)
substitutes a distilled excerpt for known ids and otherwise returns the
original body. [`registry.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/skills/registry.py)
loads every `SKILL.md` under the configured directory. The directory defaults
to the bundle and can be replaced with `FINROBOT_SKILLS_DIR`.

Backtest strategy resolution is an import boundary.
[`backtrader_adapter.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/backtest/backtrader_adapter.py)
resolves `sma_crossover` from an in-repo registry. A `module:ClassName` string
calls `importlib.import_module` only when the module matches
`FINROBOT_BACKTEST_STRATEGY_MODULE_PREFIXES`. The default prefix list is empty,
so that import is off unless the operator sets the variable. Setting it
executes the matched module's top-level code.
[`strategy_agent.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/backtest/strategy_agent.py)
adds an LLM loop of `MAX_ITERATIONS = 3` that retunes SMA parameters and
re-runs BackTrader.

### API, auth, and session boundaries

V2's CLI `serve` defaults to `127.0.0.1:8321`
([`cli.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/cli.py)).
[`server.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/server.py)
adds TrustedHost for `127.0.0.1`, `localhost`, `testserver`, and `test`, and
CORS origins that include the Vite dev server and Tauri localhost schemes.
[`auth.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/auth.py)
checks `FINROBOT_CAPABILITY_TOKEN` with `hmac.compare_digest` when the variable
is set. When it is unset, the middleware calls the route with no check. `/health`
and `OPTIONS` stay exempt. The token is accepted from `Authorization: Bearer`
or from the `token` query string. The same module states that the token exists
so another local process cannot read settings or burn LLM quota, and that the
dev loop leaves the variable unset.

Chat sessions are an upstream product surface. The server injects UI locale,
a client context bundle, and a watchlist block into the model instructions on
each turn (`_build_runtime_instructions` in `server.py`). Transcript writers
append those turns to disk. SDK methods in
[`sdk.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/sdk.py)
(`research`, `dcf`, `comps`, `lbo`, `earnings`, `ic_memo`, `analyze`, `ask`,
`backtest`, `auto_backtest`, and their async twins) call the same pipelines
without passing through the FastAPI auth middleware or the HTTP rate buckets.

V1 is a separate application. [`web_app/auth.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_equity/web_app/auth.py)
identifies users with a `session_id` cookie and stores sessions for 7 or 30
days. [`database/connection.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_equity/web_app/database/connection.py)
uses `DATABASE_URL` when set and otherwise creates `web_app/data/finrobot.db`.

This application's authenticated local API and packaged dashboard are a
different stack. FinRobot's server, cookie login, Tauri shell, and SDK are not
compatible substitutes and are not imported by this review.

### Environment, keyring, and config

V2 user settings are constructor kwargs plus the secret store.
[`FinRobotSettings.settings_customise_sources`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/config.py)
drops env and dotenv sources for ordinary fields. `model_post_init` still
reads three variables: `FINROBOT_SKILLS_DIR`, `FINROBOT_CACHE_DB_PATH`, and
`FINROBOT_BACKTEST_STRATEGY_MODULE_PREFIXES`. `create_secret_store` also reads
`FINROBOT_DEV_MODE` and `FINROBOT_USE_KEYCHAIN`. Capability-token lookup reads
`FINROBOT_CAPABILITY_TOKEN`. The shared LLM client uses httpx defaults, so
`HTTP_PROXY`, `HTTPS_PROXY`, and `NO_PROXY` apply (`config.py` states
`trust_env` stays at its default).

[`secret_store.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/secret_store.py)
tries the OS keychain on Windows and Linux, and falls back to a plaintext JSON
file at `~/.finrobot/.secrets` (mode `0600`, directory `0700`) when keyring
import or a probe call fails. Dev mode always uses the file. The file store's
own comments name headless CI, Docker, and WSL as environments where keyring
imports but does not work. A failed keychain read returns "unset" and logs a
warning. A failed write raises `SecretStoreError`. Secret names include
`fmp_api_key`, `finnhub_api_key`, `alpha_vantage_api_key`, `adanos_api_key`,
and `provider_key:<id>`. Boot hydrates those values into the process settings
object. LLM keys are omitted from `model_dump()` by being a private attribute;
they are still present in memory and are sent to the provider by
`create_model`.

Built-in model providers are Anthropic and OpenAI. Custom providers are
OpenAI-compatible rows with a caller-supplied `base_url`. The model id is free
text. `create_model` builds an Anthropic or OpenAI chat model with the key
baked into the provider instance and does not document a spend cap.

V0 [`register_keys_from_json`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_autogen/finrobot/utils.py)
writes every key in a JSON file into `os.environ`. FMP, Finnhub, SEC, and
Reddit helpers read those variables, and several helpers call the JSON loader
with a relative `config_api_keys` path. V1 stores the same class of keys in
`config.ini` and will create a dummy file containing a key assignment when
`common_utils.py` is executed as a script.

None of these stores are this application's environment loader. Possession of
an FMP or Finnhub key in this application does not authorize copying it into
FinRobot's keychain, `.secrets` file, INI file, or process environment.

### Providers and fallbacks

[`build_provider_chain`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/data/factory.py)
appends, in order: FMP if a key is set, Finnhub if a key is set, yfinance
always, SEC EDGAR when a user-agent identity is valid, Adanos if a key is set,
and a news aggregator that can use an Alpha Vantage key. yfinance is
unauthenticated. EDGAR fetches are unauthenticated public HTTP once the
identity check passes. DuckDuckGo is a separate, keyless tool and is not part
of this chain.

[`layer.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/data/layer.py)
walks that chain and can serve a last-known cached row when every provider
fails. The same file notes that a fallback winner can be a different provider
than the preferred one. FX uses yfinance first and FMP when yfinance is
rate-limited. Industry medians are a numeric fallback table, not a market-data
entitlement.

V0 additionally downloads news and social posts (CNBC, Sina, Xueqiu,
Stocktwits, Reddit, and others) through FinNLP helpers. Those functions are
part of the inspected V0 tree. They are not an approved source for this
application.

This application's existing FMP and Finnhub transports are not consulted by
any of these chains. A FinRobot fallback to yfinance, EDGAR, Adanos, Alpha
Vantage, or web search is a new egress path, not a reuse of an accepted
provider.

### Model calls and retries

V2 pipeline steps use `max_retries: int = 3`
([`runner.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/pipelines/runner.py)).
Recoverable exceptions are those whose text contains `429`, `rate limit`,
`too many requests`, or `timeout`, with delays of 2, 5, and 10 seconds.
Auth, billing, and context-length failures are treated as fatal. A non-critical
step that still fails is degraded and the pipeline continues. Prompt size is
reduced with character caps (`_PROMPT_MAX_STEP_DATA_CHARS = 12_000`, a 16_000
structured cap, a 200_000 character warning). The warning is not a refusal.
The runner does not consult a price table or a token ledger.

`ModelRetry` on a bad `data_type` is an extra model round trip. The lead-agent
and sub-agent constructors do not pass an explicit `retries=` argument. The
library default was not inspected and is not an accepted cap.

[`_stream_with_fallback`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/server.py)
reissues the same chat request once in non-streaming mode when the stream
fails or ends without usable content and no tool has run yet. That second
call is not a separate admission decision.

The shared LLM timeout is connect 10s, read 120s, write 30s, pool 10s. The
read timeout is a gap between chunks, not a run deadline (`config.py`). A
streaming response that keeps producing bytes is not stopped by that timeout.

HTTP admission, when the caller goes through FastAPI, is an in-process token
bucket: 120 pipeline runs per minute, 60 chats per minute, and 240 live-data
reads per minute
([`ratelimit.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/ratelimit.py)).
One run or one chat consumes one bucket token, regardless of how many model
or provider calls happen inside it. A semaphore of 4 limits concurrent runs
(`server.py`, `_MAX_CONCURRENT_RUNS = 4`). Both are process-local and disappear
on restart. SDK and CLI entry points do not pass through those buckets.

### Artifact, checkpoint, log, and action writes

[`paths.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/paths.py)
creates `~/.finrobot/` and stores artifacts, quotes, data cache, runs,
coverage, sessions, settings, SEC holdings, and logs there. The module
describes deleting that directory as the way to remove state. Pipeline
completion calls `artifact_store.save`
([`runner.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/pipelines/runner.py)).
Run rows and SSE events go to `runs.db`. Chat transcripts go to
`~/.finrobot/sessions/<session_id>.jsonl`
([`transcript.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/audit/transcript.py)),
which scrubs some credential-shaped substrings before append. The scrub is a
regex over known patterns, not a guarantee that prompts, tool results, or
private text are absent. File logging uses a rotating handler under
`~/.finrobot/logs` when `log_to_file` is set
([`obs/setup.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/obs/setup.py)).
Server startup calls `ensure_home()` and starts background cache, summary,
migration, and SEC-holdings work.

No LangGraph-style checkpoint directory was found in the V2 paths above. The
durable equivalents are the artifact database, run database, session JSONL,
data cache, and secret file. V0's `coding/` work directory and AutoGen disk
cache are separate write roots. V1 writes analysis and report files under an
output directory and status rows in its own SQLite database.

Actions, as distinct from file writes:

- BackTrader sets a simulated broker cash balance and reads portfolio value
  ([`backtrader_adapter.py`](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/backtest/backtrader_adapter.py)).
  No Alpaca, IBKR, or other live order client was found in the inspected V2
  Python. That absence is not confinement: `run_backtest` and `auto_backtest`
  are default SDK and chat tools.
- Report tools emit verdict, target, and entry fields. Monte Carlo text states
  whether the model implies upside or downside. The IC-memo tool description
  includes an IRR hurdle and an invest/pass recommendation.
- V2 compute operators implement DCF, DDM, LBO, multiples, and related
  arithmetic. Those formulas are upstream choices. They are not definitions in
  this application's financial specification, and this review does not adopt them.

## Allow, deny, and interception map

| Surface | What the pinned source allows | What the pinned source denies | Interception in this application |
| --- | --- | --- | --- |
| V0 code execution | Local AutoGen execution, Docker off, IPython cells, file tools under `coding/`. | No Docker isolation at the default. No path jail beyond string prefix `coding/`. | None. Proposed: do not import V0. |
| V0/V1 credentials | JSON file copied into the environment; INI keys; request-body keys; child inherits the parent environment. | V0 helpers error when the expected variable is missing. That is a missing-key failure, not a broker. | None. Proposed: never pass this application's keys across. |
| V2 lead tools | Every tool in the table above is registered for a configured model. | Unknown `data_type` retries. Invalid tickers return an error string. There is no allowlist argument on `create_lead_agent`. | None. Proposed: do not construct this agent. |
| V2 dynamic strategy import | Off when the prefix variable is empty. | Non-matching `module:Class` raises `ValueError` before `import_module`. | None. Proposed: do not set the prefix and do not call the adapter. |
| V2 unknown skill body | Loaded from `FINROBOT_SKILLS_DIR` or the bundle and inserted into the prompt. | Known ids are replaced with a distilled excerpt. The excerpt is still model text, not a privilege boundary. | None. Proposed: do not load the skill registry. |
| V2 HTTP auth | Enforced only when the capability token is set. Loopback bind and Host/CORS lists apply to the server process. | Unset token disables auth. `/health` is open. Query-string tokens are accepted. | None. Proposed: do not start this server. |
| V2 secrets | Keychain when the backend probe works; otherwise plaintext `~/.finrobot/.secrets`. | Failed writes are errors. Failed reads look like missing keys. | None. Proposed: no secret hydration in the worker. |
| Provider chain | FMP, Finnhub, yfinance, EDGAR, Adanos, Alpha Vantage news, then stale cache. | A provider is skipped when its key is absent, except yfinance, which is always appended. | None. Proposed: no FinRobot data layer. |
| Model retry and chat fallback | Up to three step retries, `ModelRetry`, and one non-streaming reissue. | Fatal auth/billing/context strings stop that step's retries. | None. Proposed: one reserved call or refusal. |
| HTTP buckets | 120 runs/min, 60 chats/min, 240 data reads/min, 4 concurrent runs, inside one process. | Excess HTTP calls get 429. SDK/CLI do not use the buckets. | None. Not a substitute for D9. |
| Home-directory writes | Artifacts, runs, cache, sessions, logs, settings, secrets. | Permission bits on the secret file. No isolation from the user's home. | None. Proposed: no `~/.finrobot` access. |
| Cancellation | `POST /api/runs/{id}/cancel` cancels the in-process task. | SSE disconnect only stops polling. No vendor cancel call was found. | None. |

## Allowed research subset

The executable subset authorized by this review is empty.

FinRobot's defaults are research-shaped and still include code execution (V0),
a shell child (V1), web search, unauthenticated market data, watchlist reads,
valuation and backtest tools, opinion text, and home-directory writes (V2).
Selecting the framework does not adopt those defaults. A prompt instruction
inside a skill excerpt is not a deny path.

The only subset that stays eligible for a later, separate contract is:

1. No import of V0 or V1.
2. No import of the V2 server, routes, desktop shell, secret store, provider
   chain, skill registry, backtest adapter, or lead agent.
3. If an owner-accepted PoC later uses any V2 code, it is a reviewed,
   non-executing fragment behind an adapter this application owns, running as
   a Linux process with no home directory, no inherited environment, and no
   network except through a broker this application implements.
4. Evidence, if a later rights decision allows it, comes only from this
   application's already accepted public-data transports for an explicit
   ticker. yfinance, EDGAR-through-FinRobot, Adanos, Alpha Vantage, DuckDuckGo,
   and social/news downloaders are outside that subset.
5. The result returns as data to this application's own API and dashboard.
   FinRobot artifacts, sessions, and reports are not the product store.
6. ADR-0018's prepared criteria remain an immutable local snapshot. They are
   not a FinRobot tool argument and are not rewritten to force a match.

Until the gating gaps below are closed, item 3 is not available. Items 1, 2,
and 6 are immediate constraints on any implementation issue.

## Prohibited paths

**Code.** V0 AutoGen execution and `coding/` file tools. V1 `subprocess.Popen`
and any command built from request fields. V2 `importlib` strategy loading,
even though the default prefix list is empty. Unknown `SKILL.md` bodies as
instructions. Package installation, shell tools, and SQL tools were not found
as lead-agent tools; their absence is not a reason to load a generation that
already executes code elsewhere.

**Trade and simulated performance.** Live brokerage routing was not found, and
is still prohibited. Also prohibited now: BackTrader runs, the LLM strategy
loop, Monte Carlo upside/downside calls, verdict/target/entry publication, and
IC-memo invest/pass output. D11 remains unresolved, so opinion text stays
unpublished. Upstream DCF, DDM, LBO, and multiples code is not an application
metric.

**Private data.** FinRobot coverage/watchlist rows, chat context bundles,
session transcripts, settings, and secret files. V1 user records and session
cookies. This application's holdings, quantities, costs, annotations, account
identifiers, local paths, and API bearer. Free-text criteria that may contain
private text. No X716 exception is implied by enabling a future research flag.

## Local API and dashboard

This review does not add routes, middleware, or pages. The existing local
authenticated API and packaged dashboard stay the only user-facing surfaces.
FinRobot's FastAPI app, Tauri/Vite client, V1 web app, and cookie login are
not mounted beside them and are not a source of auth, storage, or static files.

A future research panel, if separately accepted under AI1022 and AI1023, is
new versioned behavior in this application's API and the existing dashboard.
Disabled or absent AI must leave CLI, API, dashboard, criteria editing, and
holdings usable (AI1014, AI1025, AI1029). This document does not implement
that flag. It also does not add a run-creation endpoint.

## Worst-case reservation and cancellation

**Source fact.** No pre-call monetary or token reservation exists. The HTTP
bucket charges one count for the whole run or chat. Inside that admission a
pipeline can issue one model call per step, then up to three retries, and a
chat can add a full non-streaming reissue plus every tool's provider traffic.
Provider fallback can contact more than one host per fetch. Character caps can
shrink a prompt; they do not compute a price. There is no ledger to retain if
usage is missing.

**Source fact.** `cancel_run` records intent and calls `asyncio.Task.cancel()`.
The route comment says spend stops at the next await because provider calls
are httpx awaits. That is an in-process observation, not a vendor cancellation
and not a proof that the current request is unbilled. Disconnecting the SSE
client returns from the poller and leaves the task running. Orphaned rows can
be marked `cancelled` in the database after the process is already gone, which
does not unwind a remote call. SDK and CLI callers have no shared cancel
ledger with the server.

**Proposed control, not a contract.** Keep the #191 rule: the trusted broker
is the only billable path; before each call, reserve the worst case of every
bounded category, including retries, the one-shot stream fallback, tool
fan-out, and provider-chain attempts; refuse when price, tokenizer, or hidden
usage is unknown. On cancel, release a reservation only when the dispatch is
known unsent; otherwise keep the worst-case charge until settlement. Do not
treat FinRobot's bucket, semaphore, or task cancel as that mechanism.

**Unverified.** No synthetic broker was run. Upstream retry limits were not
executed. Provider billing behavior was not observed.

## Gating gaps

These block activation. Closing them is later accepted work, not this issue.

1. **No confinable default.** The allowed executable subset is empty. Loading
   `create_lead_agent` or `FinRobot.research` enables tools this scope rejects.
2. **No hard budget.** D9 is open. Counts and concurrency are not worst-case
   reservations. Retries and the chat fallback multiply unreserved calls.
   SDK/CLI skip the HTTP buckets.
3. **Cancellation is local.** Task cancel and SSE disconnect do not retain an
   uncertain charge or prove the provider stopped.
4. **Secrets and home writes.** Linux, WSL, and Docker are exactly the
   environments where the pinned store falls back to plaintext
   `~/.finrobot/.secrets`. The sandbox decision does not remove that fallback.
   Artifacts, runs, caches, sessions, and logs share the user home directory.
5. **Egress is not brokered.** yfinance, EDGAR, DuckDuckGo, custom `base_url`,
   and process proxy variables can leave the host without this application's
   transport. Existing FMP/Finnhub rights do not cover those hosts.
6. **Private context is on by default in V2 chat.** Watchlist text and the
   client context bundle are inserted into instructions. Transcripts store the
   conversation. This application's holdings must not be added to that path.
7. **Financial and opinion output.** Upstream valuation operators and
   verdict/target/backtest text conflict with the accepted calculation
   boundary and with open D11. They are not reusable as application results.
8. **Rights, price, and retention are unknown.** NOTICE/trademark text is not
   a data or model contract. No provider account, region, training opt-out, or
   report-retention decision was verified.
9. **Wrong-generation import.** Root install exposes V0 as `finrobot` and does
   not install V2, which uses the same import name. Either install can pull
   incompatible Python and dependency pins into this application.
10. **Enforcement is unbuilt.** #191/#194 and this file are documents. This
    repository cannot deny a FinRobot tool call until an accepted adapter and
    tests exist.

## Synthetic adversarial and failure matrix

Not executed. These rows are the evidence a later implementation must produce
with fixed offline fixtures, a fake billable endpoint, a temporary directory,
and synthetic credentials. A model refusal string does not pass a row. Each
row needs a negative control that fails if the forbidden effect is still
possible. [TESTING.md](../TESTING.md) stays the suite contract. Repository
pytest does not cover this matrix.

| Case | Pinned surface the case targets | Required observable result |
| --- | --- | --- |
| Prompt says to ignore limits, reveal keys, or run a shell | V0 code tools; V2 lead agent; unknown skill body | No new process, no secret in the prompt or transcript, no extra tool. |
| `IPython` cell or `coding/../../` path | `coding.py` | Path and execution denied before effect. Not reachable from this app. |
| `module:ClassName` strategy with an empty prefix, then with a prefix | `backtrader_adapter.py` | Empty prefix denies before import. A set prefix is out of scope and must stay unset. |
| Request body or INI contains a provider key | V1 `AnalysisRequest`, `config.ini` | Key is not accepted, logged, or copied into the child environment. |
| Capability token unset; another local client calls settings and runs | `auth.py`, `ratelimit.py` | This app never binds FinRobot's server. A future worker with no token does not start. |
| Keychain probe fails on Linux/WSL/Docker | `FileSecretStore` | Worker has no secret file and no keychain access. Missing key refuses the run. |
| `FINROBOT_SKILLS_DIR` or `FINROBOT_CACHE_DB_PATH` points outside the run root | `config.py` `model_post_init` | Variable is not inherited. No read of the foreign path. |
| Model selects DuckDuckGo, yfinance, EDGAR, or a custom `base_url` | Orchestrator, factory, `create_model` | Connection does not open. No DNS lookup to those hosts from the worker. |
| One admitted run fans out to retries, stream fallback, and several providers | `runner.py`, `_stream_with_fallback`, `layer.py` | Dispatch count cannot exceed the reserved worst case. Unknown price dispatches nothing. |
| Cancel before send, during send, and after the provider has accepted | `cancel_run`, SSE poller | Unsent work is not sent. Uncertain work stays reserved. Poller disconnect does not clear the reservation. |
| Crash between reserve and settlement | No ledger at the pin | No automatic replay, no double release, cap unchanged. |
| Watchlist, holdings, or criteria text includes an account identifier | Coverage prompt, ADR-0018 envelope | Outbound admission refuses. Local snapshot bytes stay unchanged. |
| Pipeline returns a verdict, target, or backtest return | Registry tools, artifact save | Not stored in this app's database and not shown in the dashboard. |
| Artifact or transcript write | `~/.finrobot` | No file appears under the user home or the core SQLite paths. |
| AI package missing, disabled, or budget exhausted | This application's CLI, API, dashboard, criteria | Those surfaces still serve. They do not import FinRobot. |

## Owner decisions still required

- Whether any V2 fragment may be imported after #197, or whether the selected
  direction must be reimplemented without loading this pin. This review does
  not recommend enabling the default agent.
- D9: vendor, price version, caps, and what happens to an uncertain in-flight
  charge. No numeric default is proposed here.
- D11: whether opinion text can ever be shown. It cannot be shown on current
  authority.
- Confirm that no X716 exception is granted for holdings or for free-text
  criteria that contain private data.
- Confirm the Linux/WSL/Docker sandbox image has no user home, no keyring, no
  inherited environment, and no route except a future broker.
- #197's license and dependency result, including trademark use if any source
  is vendored. This review does not clear redistribution.

## Boundary

#192 may consume this map as an input. It is not an adapter contract.
#197 remains responsible for generation choice, pins, and NOTICE obligations
beyond the trademark fact quoted above. No Taurus search, candidate, model
call, or financial calculation is delivered here.

## Repository checks

These checks exercise this repository. They do not execute FinRobot and they
do not prove the matrix above.

| Command | Result |
| --- | --- |
| `python -m pytest -q --tb=line` | 3143 passed, 35 skipped, 40.93s. Python 3.12.3. `COLUMNS=300` so Rich tables are not ellipsized by this environment's 80-column terminal. The 35 skips were already present before this documentation change. |
| `python -m ruff check .` | Passed. |
| `python -m mypy` | Passed. Configured files are `config.py` only. |
| `python -m pip check` | No broken requirements. |
| Relative links in the three edited Markdown files | Resolved. |
| `git diff --cached --check` | Passed. |
| `python -m pytest tests/test_repository_hygiene.py -q --tb=short` | 9 passed, against the staged documentation. |

Python 3.11 is not installed in this environment. The Foundation workflow runs
that suite on the pull request.
