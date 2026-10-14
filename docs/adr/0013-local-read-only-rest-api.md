# ADR-0013: Local holdings read-only REST API

## Status and acceptance gate

**Accepted — 2026-10-14.** After the Master requested explicit acceptance of
the relevant M7 specification and Option A in PR #135, the owner directly
instructed **"pr merged, continue the work"**. This accepts the reviewed M7
contract, including its exact local bounds, access, serialization, error and
activation choices. Independently verified owner merge:
`e03d116981c8c81b7899f7202040fefb23b9065b`, containing reviewed head
`94bde7d268bc423b907d89429e1c5d3b76c30c41`. Exact-head
[Foundation 38523342700](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38523342700)
passed. Post-merge
[main Foundation 38527281579](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38527281579)
also completed successfully; acceptance, owner-merge and main-CI prerequisites
are satisfied. #130 may begin; later issues retain their own dependency gates.
This does not accept M8–M10, unresolved provider rights or agent merges.

The original proposal and gate wording below records the reviewed decision;
it does not supersede the acceptance above. This is the concrete contract
for [#129](https://github.com/daniilnahl/Stock-Tracking-App/issues/129), in
[M7 — REST API](https://github.com/daniilnahl/Stock-Tracking-App/milestone/8).
The request to begin M7 authorizes analysis, decomposition and this proposal;
it does not settle the previously unspecified public API or architecture.
Main advanced during this task to owner-merged proposal PR #128 at
`a968df963084361e4d824d17e2c25046981514ae`. SRS v1.2 still records owner
acceptance PENDING; merge alone does not accept its new requirements. This ADR
addresses M7 decision gates D1/D2/D4 and preserves approved v1.1/ADRs.
Issues #129–134 are conditional planning candidates, not authorization to
implement the unaccepted revision. Runtime #130–133 requires explicit owner
acceptance of the relevant M7 specification and reviewed Option A,
owner merge of this proposal and passing required main CI. No agent merge.
The [M7 plan](../milestones/m7-plan.md) records dependencies and exit gates.

## Context and authority

SRS §23 M7 permits FastAPI after service/domain stabilization and requires CLI
and REST to share services. ARCH-001–005 define isolation and injection;
ARCH-006 requires an accepted ADR for material architecture choices. No
endpoint, serialization, authentication or hosted-operation contract exists.
AGENTS §§1, 10, 28 prohibit silently choosing undefined API/product semantics.
Proposed API701–724 and applicable X710–729 provide review criteria, but are
not normative until accepted. This proposal does not accept M8–M10, activate
new provider rights or resolve their research/AI decisions.

M6 is owner-merged through main `5bed5d327bdbaaf75105e7bae2fc1451fef14752`.
Accepted ADR-0012 supplies `WatchlistService`, `CurrentDataService` and
`HistoryService`, neutral immutable results and injected infrastructure ports.
ADRs 0006–0011 supply financial, identity, persistence, provider and history
rules. Existing CLI composition imports legacy facades/presentation and must
not be reused as the REST composition graph.

Inspected source: services/models, watchlists, current_data, history, protocols
and history_policy; cli/composition; persistence/models and sqlite_watchlists;
providers/factory; exceptions. Associated service, CLI boundary, persistence,
history, numeric and packaging tests establish existing behavior. Saved
watchlist prices have no freshness timestamp. A watchlist is not a Portfolio.
Current-data refresh publishes partial progress and removal preserves legacy
forward-iteration behavior; neither defines an appropriate new write contract.

## Proposed Option A

Introduce a local, single-user, authenticated **holdings read-only** REST
adapter over established watchlist views and stored-entry history. Historical
requests may write the already accepted historical cache; no endpoint saves
holdings, migrates data or reads legacy pickle contents. No new financial
metric, Portfolio CRUD, current refresh, arbitrary symbol lookup, browser UI,
hosted deployment or multi-user ownership is included. Future writes require
separate decisions about concurrency, identity and publication atomicity.

### Endpoints and request semantics

| Method/path | Contract |
|---|---|
| GET `/health` | Public process liveness only: `{"status":"ok"}`; no configuration, state, cache or provider acquisition. |
| GET `/api/v1/watchlists/{namespace}` | Authenticated `WatchlistService.load()` then `.view()`; saved observations, freshness unknown. |
| GET `/api/v1/watchlists/{namespace}/entries/{ordinal}/history` | Authenticated load, select exact row and call `HistoryService.history()` with that Stock and ordinal. |
| GET `/api/v1/openapi.json` | Authenticated, static API schema; no state/provider access. |

Only namespaces `menu_watchlist` and `daniils_stock_method` are allowed; any
other namespace returns 404 without repository access. The view response is
200 for a genuinely missing namespace, with the existing empty Watchlist
record. Existing legacy-state protection still returns an error. Ordinal is
a zero-based nonnegative integer; malformed input returns 422 and an absent
row returns 404. Ordinals are request-local selectors, not stable identifiers.
They preserve duplicate rows and must be read from a freshly loaded record.

History query parameters are either both absent or a single `start` and single
`end`, each exact `YYYY-MM-DD`. Reject duplicates, unknown query parameters,
unpaired dates and invalid calendar values with 422. Use existing injected UTC
clock/range policy, inclusive bounds, NASDAQ gate, sparse raw bars, one-hour
cache TTL, accepted maximum span/bar count and no stale fallback unchanged.
Watchlist, health and OpenAPI accept no query parameters; reject any with 422.
All endpoints accept no body; unexpected nonempty bodies return 422. Reject
declared positive Content-Length before reading, and detect undeclared/chunked
content on the first nonempty ASGI chunk without collecting the body. Tests
must prove rejection does not buffer the whole body or acquire application IO.
Other methods return safe 405 and unknown paths safe 404; no automatic redirects.

### Exact response shapes and numeric representation

Explicitly serialize neutral service results; do not expose arbitrary object
attributes or use float conversion. Financial Decimals use `str(value)` as
JSON strings, without quantization, preserving their exact value and scale.
Exponent notation from an existing Decimal remains valid. Missing values use
JSON null, not zero or formatted sentinels. Ordinals/volumes are JSON integers;
dates use ISO date strings. Ratio fields retain decimal-ratio units.

Watchlist response fields:

```text
namespace: string
name: string
observation: "saved"                 # no freshness assertion
provenance: {source: null, observed_at: null, retrieved_at: null,
             freshness: "unknown"}  # absent from the stored/service contract
entries: array of:
  ordinal: integer
  stock: {symbol: string, name: string|null, exchange: string|null}
  quantity: decimal string
  average_cost: decimal string|null  # null denotes unowned only as already defined
  current_price: decimal string|null # existing field name, saved observation
  metadata: {sector, country, currency, market_cap,
             price_1d, price_5d, price_30d, price_3m, price_6m,
             price_1y, price_3y, price_5y}: saved string|null fields
  snapshot: null or {cost_basis, market_value, unrealized_pnl,
                     unrealized_return}: decimal string|null fields
```

Metadata is copied exactly as opaque saved display text, including existing
`N/A` values; it is never recast as numeric returns or currency evidence.
The snapshot names match existing `PositionSnapshot` attributes, including
`unrealized_pnl`. Unowned rows have snapshot=null. Owned
zero inputs retain the existing snapshot/zero-denominator/missing-price rules.
Do not sum watchlist rows or infer average-cost currency from profile metadata.

History response fields: `stock` as above; `ordinal`; `start` and `end` as the
resolved requested ISO dates; `price_basis: "raw"`; `bars` as an ordered array
of `{symbol, date, open, high, low, close, adjusted_close, volume}`. Decimal
fields are strings or null according to the existing PriceBar contract;
volume is integer or null. No inferred sessions, prices or adjusted values.
JSON property order has no contract; array order does.
History additionally has `provenance: {source: "fmp"|null, observed_at: null,
retrieved_at: null, currency: null,
freshness: "accepted_cache_policy"|"unknown"}`.
Production composition declares source=fmp; injected providers without known
source use null. Only explicitly declared production cache composition may
label freshness=accepted_cache_policy; providers without that evidence use
unknown. History prices are raw per-share prices with unknown currency; volume
is shares when available. Document these units in OpenAPI. Bar dates are session
labels, not UTC timestamps. Cache receipt
time is internal and absent from HistoryView; do not stamp response time as
observation/retrieval time. Accepted cache policy is not a live-price claim.

### Proposed resource and evolution bounds

Version 1 is additive only: changed meanings/removed fields require a new
version and an accepted deprecation policy before release. No fictional future
routes are registered. Generate typed OpenAPI success/failure examples and
contract snapshots; keep serializers separate from services.

Proposed local bounds: request target at most 2,048 UTF-8 bytes; a bearer token
at most 256 ASCII characters; body refusal as above. At most four active API
data operations per process, including at most one history operation, with
immediate safe 503 `api_busy` when full and no application queue/retry. Provider
timeouts/retries stay authoritative; no API retries, background jobs or new
provider quota assumptions. At most 4 MiB of serialized success JSON: refuse
oversized responses with fixed 503 `response_too_large`, never truncate arrays
or return a misleading empty success. Encoding must stop at the limit, not
allocate an unbounded final response. These are explicit proposed safeguards,
not measured SLOs; accepting Option A accepts these bounds. Oversized request
targets return fixed 414 `request_too_large`; size/security checks precede
service acquisition. Disconnect ends delivery but admission remains held until
all associated service/provider work terminates; release in finally after work
completion, not merely socket disconnect. A blocked fake provider across a
disconnect must keep a second history request at `api_busy`. Existing atomic
cache writes still own integrity, with no holdings commits.

### Safe error contract

All non-success responses use `{"error":{"code":"...","message":"..."}}`.
Codes/messages are fixed constants, never raw exception/request serialization.
Framework validation must not echo inputs, authorization headers or context.
All responses use `Cache-Control: no-store`; no cookies or auth in URLs.

| Category | Status / code |
|---|---|
| Missing/invalid bearer | 401 / `unauthorized`, with `WWW-Authenticate: Bearer` |
| Disallowed browser Origin | 403 / `origin_forbidden` |
| Disallowed Host | 400 / `host_invalid` |
| Invalid request/domain/history range | 422 / `invalid_request` |
| Unknown namespace/absent ordinal/path | 404 / `not_found` |
| Unsupported method | 405 / `method_not_allowed` |
| Legacy transition required | 409 / `legacy_state_present` |
| InvalidTickerError from validated provider path | 422 / `invalid_ticker` |
| MarketDataUnavailableError, including inconclusive lookup | 503 / `market_data_unavailable` |
| ProviderTimeoutError (before its superclass) | 504 / `provider_timeout` |
| RateLimitError | 429 / `provider_rate_limited` |
| ProviderResponseError | 502 / `provider_response_invalid` |
| Provider unavailable/authentication/access/request or missing provider configuration | 503 / `provider_unavailable` |
| Corrupt storage/schema, persistence validation/error, cache failure, unexpected failure | 500 / `internal_error` |

Provider authentication is an upstream failure, never a client 401. Do not
forward upstream headers or add Retry-After in v1. Expected exceptions map
explicitly; unexpected exceptions fail safely, are not swallowed, and must
not log their raw message/traceback because it may contain sensitive inputs.
Safe diagnostic logging may record only the category and operation name.

### Composition, packaging and local operation

Add `stock_tracker.api` to explicit setuptools discovery. Services/domain
remain independent of FastAPI/Pydantic and continue to return neutral objects.
An injected `create_app` builds routes without IO; independent API composition
constructs services with SQLiteWatchlistRepository, existence-only legacy
ports, provider factory and UTC clock. Do not import root facades, CLI
composition, Rich, Typer or Matplotlib in the API graph.

Use the existing pip/pyproject workflow and Python 3.11/3.12. Foundation #130
must resolve and pin a compatible minimal FastAPI/Pydantic/Starlette/ASGI stack
and HTTP test client, documenting every new dependency; preserve existing
pins. Do not install broad FastAPI standard extras, introduce a lock/toolchain
or expand mypy scope. Dependency incompatibility requires review rather than
silently replacing existing pins. Exact selected versions are reviewable in
that bounded PR. FastAPI uses ASGI; see its official
[server documentation](https://fastapi.tiangolo.com/deployment/manually/) and
[dependency override testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/).

Provide `python -m stock_tracker.api` with help and a launcher fixed to
127.0.0.1:8000, one worker, no reload, no trusted proxy headers and access logs
disabled. Resolve explicit `--database`, `--history-cache`, `--menu-legacy`
and `--evaluation-legacy` paths once at launch. All four options are required;
do not implicitly locate home/cwd files or create parent directories. Help
does not read configuration or files. Require pairwise distinct resolved paths,
using Windows-aware case normalization and same-file checks for existing targets
to reject hard-link aliases. Resolve existing symlink parents/targets; refuse
unresolvable/ambiguous paths with a fixed safe configuration error. In particular
the cache must never alias a database or legacy target, including missing paths.
Launch may inspect filesystem metadata for these safety checks, but opens no
state contents and creates no SQLite/cache data. Test missing-path collisions,
existing hard links and symlink aliases with temporary inputs.
First authenticated operations follow existing IO contracts.

Require `STOCK_TRACKER_API_TOKEN` at launch, a distinct operator-supplied ASCII
token matching `[A-Za-z0-9_-]{32,256}`; reject whitespace, controls and all other
characters. No default, automatic persistence or URL form.
Configuration layer loads it from process environment only, without changing
CLI key-loading semantics. Bearer comparison uses constant-time comparison.
Authorization accepts exactly one header containing case-insensitive `Bearer`,
one ASCII space and a token matching that grammar; reject duplicate headers,
extra whitespace or other schemes with the fixed 401 response. Every `/api/v1`
operation authenticates before state/provider acquisition.
Missing token refuses launch with a fixed message. No value is printed/logged.
FMP credentials continue through existing configuration, acquired lazily only
for supported historical requests; local views need no provider credentials.

Accept only Host authorities `127.0.0.1:8000` and `localhost:8000`; reject any
Origin header (including null) in v1. No CORS middleware, credentials cookies,
proxy trust or automatic interactive docs; authenticated OpenAPI remains
available for local tools. Host/Origin rejection precedes auth and dependency
acquisition. Loopback plus bearer protects the intended local interface;
it does not claim protection from other processes running as the same user.
No server will be started against real user state during implementation.
Hosting, TLS, multi-user auth, backup/rollback and public exposure require
separate REL-003 decisions.
Owner/provider confirmation of rights for local API display and historical
cache retention is an activation gate, separate from code/contract acceptance.
Existing CLI access or an API key does not establish those rights. Implementation
and audit use only controlled fixtures; live API operation remains disabled
until the relevant D5 rights/entitlement evidence is supplied.
Concretely, production historical acquisition is disabled by default. An
explicit `--enable-history` launch flag may be used only after owner-confirmed
rights evidence is recorded in operation documentation; it is not a license
grant. Without it, the historical route returns safe 503 `history_disabled`
before state/provider/cache acquisition. Saved local views, health and schema
remain available under their access controls. Injected synthetic providers in
tests do not activate any external source or establish rights.

## Alternatives and consequences

**A — recommended:** this bounded adapter proves ARCH-005 with two shared
services, retains exact data and avoids defining new writes. It provides saved
views/history rather than fresh quotes or full Portfolio workflows.

**B — write-capable local API:** add/remove/refresh requires explicit new
request contracts, concurrency/transaction semantics and partial-failure
decisions; it expands M7 planning before runtime work can begin.

**C — hosted/multi-user API:** requires authentication/authorization, deployment,
secrets, backup/rollback and ownership specifications under REL-003; current
local SQLite/watchlist assumptions are insufficient.

## Proposed exit criteria

Both API routes execute the existing shared services; no duplicate financial,
provider or persistence policy appears in presentation. Exact Decimal/null,
row identity, safe errors/access and fixed-date raw history are audited offline
against real service/repository/cache composition in independent source and
installed-wheel processes, with proven network/legacy/outside-write guards.
Local view and all history outcomes preserve holdings/legacy bytes; fresh
cache restart and exact expiry failure retain accepted no-stale behavior.
API import/help/health require no IO, credentials or provider access. Existing
CLI/domain/provider/persistence behavior remains green. Full pytest, Ruff,
configured mypy, pip check and hygiene pass; required PRs are owner-merged,
required main CI passes and issues #129–134 close before milestone completion.
