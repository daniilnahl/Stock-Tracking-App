# REST foundation, saved views and stored history - issues #130-132

Accepted [ADR-0013](adr/0013-local-read-only-rest-api.md) defines the M7
contract. This foundation implements injectable transport infrastructure,
serialization and safety boundaries. It registers GET `/health`,
GET `/api/v1/openapi.json`,
GET `/api/v1/watchlists/{namespace}` and
GET `/api/v1/watchlists/{namespace}/entries/{ordinal}/history`.
Storage composition, credential loading and the production launcher remain #133.
This injected adapter starts no listener.

## Factory and extension contract

`stock_tracker.api.create_app(*, token=None, services=None)` constructs a
FastAPI instance without application configuration, credential, database,
provider or cache acquisition. A missing token permits process health;
all `/api/v1` requests fail authentication. The future production launcher
must require the operator token. Supplied tokens match
`[A-Za-z0-9_-]{32,256}`; invalid configuration raises a fixed ValueError.
The token never becomes a Pydantic response, schema example or repr field.

`ApiServices` carries a namespace-to-WatchlistService acquisition port,
an optional HistoryService and explicit historical activation/provenance
declarations. It constructs no dependency. Defaults disable history and claim
no source/cache provenance. Only an explicit FMP cache declaration qualifies
`accepted_cache_policy`; a provider name alone does not qualify it.

Data handlers call `run_data_operation(app, operation, history=False)` with a
closure containing service acquisition, invocation and explicit serialization.
Admission happens before the closure executes: at most four active operations,
one of which may be historical; excess demand immediately raises fixed
503 `api_busy`. Synchronous work runs off the event loop. Disconnect/cancellation
does not release a running worker's slot; its finally owns release. Work canceled
before execution releases exactly once and cannot acquire dependencies later.
No additional provider retries or application queue is introduced.

`api.schemas` provides typed neutral wire schemas. `watchlist_payload` and
`history_payload` in `api.serialization` copy already computed service results;
they perform no financial arithmetic, provider lookup or aggregation. Decimal
values use exact text, including exponent/scale; null, zero and unowned state
remain distinct. Snapshot amounts have unknown currency provenance and returns
are ratios. Saved display metadata remains opaque. Historical prices are raw
per-share values with unknown currency, dates are session labels and volume is
shares. Missing source/timestamps remain null. Impossible/malformed neutral
outputs fail instead of manufacturing evidence.

Later routers can reuse `error_documents()` and `PROTECTED_OPENAPI` from
`api.app` for typed fixed error examples and the `LocalBearer` security scheme.
Register only implemented routes. OpenAPI currently documents health's success
example, the actual protected schema endpoint and typed saved-view/history routes.
Its snapshot is reviewed in
`tests/fixtures/api_foundation_openapi.json`; route additions must deliberately
update that contract alongside endpoint tests.

## Access and response behavior

Request-target size is capped at 2,048 bytes of the raw path/query. The outer
ASGI boundary then requires one exact Host (`127.0.0.1:8000` or
`localhost:8000`), rejects every Origin header and authenticates `/api/v1`
before body processing or dependency acquisition. Authorization requires one
header with case-insensitive Bearer, one ASCII space and an exact valid token;
comparison uses constant-time comparison. No CORS or interactive docs exist.

Fixed routes reject all query parameters. The history handler owns exact
paired-date validation. Nonempty bodies are refused: positive/malformed/duplicate
Content-Length fails before reading; undeclared bodies stop at the first nonempty
ASGI chunk. The full body is never collected. The consumed empty request is
replayed once, then receive delegates to the actual transport so disconnects
remain observable. Unsupported methods return safe 405; unknown paths return
safe 404 without redirects. All responses use `Cache-Control: no-store`.

## Stored-entry historical requests

History selects a freshly loaded row from the same two namespace allowlist.
The ordinal contains only ASCII decimal digits and denotes a zero-based,
request-local row, preserving duplicate symbols. An absent row returns 404.
Unknown namespaces and malformed selectors are rejected before acquisition.
The handler validates the full loaded record and binds the returned HistoryView
to the exact selected Stock object; swapped namespaces, identities or malformed
neutral outputs cannot be published as another row's history.

Query parameters are either absent or exactly one `start` and one `end`, each
an exact `YYYY-MM-DD` calendar date. Duplicate, unknown, unpaired, empty or invalid
dates return fixed 422. For example, the injected endpoint accepts
`/api/v1/watchlists/menu_watchlist/entries/0/history?start=2020-01-02&end=2020-01-06`.
The existing HistoryService owns UTC defaults, inclusive range limits, NASDAQ
identity validation and sparse raw-bar validation. No API retry or additional
clock resolution changes those policies. Raw OHLC values retain exact Decimal
strings; adjusted_close is null, and integer volume zero differs from null.

Default `ApiServices.history_enabled=False` returns fixed 503 `history_disabled`
before watchlist/provider/cache acquisition. Explicit synthetic injection can
enable deterministic tests; it does not grant external display/cache rights.
Future production activation remains the documented #133 operator gate. The
history route uses the shared one-history admission slot; cancellation or a
closed ASGI client cannot release it while provider work continues. Responses
declare only explicitly injected source/cache provenance, with unknown currency
and timestamps left null. Fresh-cache restart and exact one-hour expiry use
the existing cache policy with no stale fallback and leave holdings/legacy bytes
unchanged. Cache composition remains outside the API adapter graph.

All failures use `{ "error": { "code": "...", "message": "..." } }` with
constant messages. No request input, raw exception, URL, path, traceback,
credential or upstream header is serialized/logged. Provider authentication is
an upstream 503, not a client 401. Composition must translate its ConfigurationError
to `ApiFailure("provider_unavailable")`, avoiding a configuration-loader import
in presentation. Unexpected failures use fixed internal_error and safe category
logging. API authentication failures include `WWW-Authenticate: Bearer`.

`BoundedJSONResponse` stops at 4 MiB, returning 503 `response_too_large` rather
than truncating. It escapes saved strings in small slices and never constructs
an unbounded final JSON response. Financial floats and arbitrary objects are
rejected. Limits are accepted safeguards, not measured SLOs. Actual provider
timeouts/retries/cache semantics remain their adapters' responsibility.

## Dependencies and compatibility

`pyproject.toml` remains the only dependency definition and canonical installation
is `python -m pip install ".[dev]"`. Every existing pin is preserved.
No standard extras, telemetry package, multipart parser, second lockfile,
new runtime or type-check scope is introduced.

| New runtime package | Pin / purpose |
|---|---|
| FastAPI | 0.141.0; versioned injectable ASGI presentation. 0.142+ adds a mandatory OpenTelemetry dependency outside this minimal scope. |
| Pydantic / pydantic_core | 2.11.10 / 2.33.2; typed schema generation, preserving typing_extensions 4.12.2. Pydantic 2.12 requires a newer typing_extensions pin. |
| Starlette | 1.8.0; underlying ASGI routing/responses. |
| Uvicorn / h11 | 0.54.0 / 0.16.0; minimal server dependency for later approved local launch, without extras. |
| AnyIO / idna | 4.13.0 / 3.20; compatible ASGI concurrency and IDNA dependencies. |
| typing-inspection | 0.4.2; typing metadata, compatible with typing_extensions 4.12.2. |
| annotated-doc / annotated-types | 0.0.5 / 0.8.0; framework documentation/type metadata. |
| HTTPX / httpcore (dev only) | 0.28.1 / 1.0.9; in-process ASGI tests, no live listener. |

Official [FastAPI metadata](https://pypi.org/pypi/fastapi/0.141.0/json),
[Pydantic metadata](https://pypi.org/pypi/pydantic/2.11.10/json),
[Starlette metadata](https://pypi.org/pypi/starlette/1.8.0/json) and
[AnyIO metadata](https://pypi.org/pypi/anyio/4.13.0/json) establish declared
Python/dependency ranges; installation and tests establish actual local behavior.
All exact project/development pins resolved successfully in a Python 3.11
Windows-wheel dry run. Python 3.12.14 canonical installation and focused tests
ran locally. Python 3.11 runtime execution remains a required Foundation CI
check; the local host has no supported 3.11 interpreter.

## Offline verification and limits

Run the focused command in the canonical environment:

```bash
python -m pytest tests/test_api_foundation.py tests/test_api_serialization.py tests/test_api_boundary.py tests/test_packaging.py -v
```

HTTPX uses in-process ASGI transport. Raw ASGI tests prove duplicate-header,
auth/Host/Origin order, bounded body inspection, exact size boundaries, fixed
errors, admission/cancellation and actual disconnect delivery. Real neutral
services supply independent known-value serialization fixtures. Existing
provider/domain/CLI/persistence tests remain required.

Cold source/installed-wheel subprocesses deny configuration/UI/concrete
infrastructure imports, ordinary file IO, SQL, network, pickle, credential
environment access and output. Negative controls prove denial before actual
API imports/operations, including ordinary temporary data disguised as
`fake.dist-info/METADATA`. The pinned framework remains cold too.

Code-loading exceptions are explicit: stdlib timezone/sysconfig and native
Windows event-loop control sockets bootstrap before guards; Pydantic's exact
PYDANTIC_DISABLE_PLUGINS and PYDANTIC_VALIDATE_CORE_SCHEMAS tuning lookups are
represented as defaults only for their specific framework callers; distribution
METADATA/entry_points.txt reads are limited to immediate canonical site-package
metadata directories and the explicit installed application root. Application
credential/environment and ordinary data IO remain denied. This establishes
application IO-free construction, not a claim that Python framework imports
never consult code metadata or framework tuning settings.

Tests on Windows may need permission for native event-loop control sockets and
the existing temporary hard-link fixtures. The module-owned loop bootstraps
before the existing per-test transport guard, then actual API execution keeps
that guard active. Tests explicitly verify denied connect/getaddrinfo afterward;
no policy replacement or application listener is used. Production plugin loaders
are unmodified. These tests certify neither live provider rights/entitlement
nor a complete M7 runtime. Historical activation remains separately gated.

## Saved watchlist requests — issue #131

GET `/api/v1/watchlists/menu_watchlist` and
GET `/api/v1/watchlists/daniils_stock_method` require the local bearer token
and accept no query or body. The route acquires the explicitly injected
WatchlistService only after access checks and admission, calls `load()` then
`view()`, and projects its neutral result with `watchlist_payload`. The result
must match the requested namespace. No provider key, provider or cache is
acquired; no holdings are saved or refreshed. Other namespaces return safe
404 `not_found` without service acquisition. Stored-entry history is documented
in the section above and remains disabled by default.

A genuinely absent namespace returns 200 with the existing `Watchlist` empty
record without creating a database. An absent namespace with its legacy entry
present returns 409 `legacy_state_present`; only existence is inspected, never
pickle contents. Existing structured namespaces remain authoritative even when
legacy entries exist. Corrupt data and unsupported schema return fixed 500
`internal_error`, retaining the original files. Unconfigured service injection
also fails safely; production configuration is not supplied by this issue.

Rows retain order, duplicate tickers, exchange distinctions and request-local
zero-based ordinals. Unowned rows use null average cost/snapshot; numeric zero
remains numeric text. Existing Position snapshots retain the service's formulas,
with returns expressed as ratios. Saved current prices
are observations of unknown freshness. Opaque saved currency/display metadata
does not establish price or cost currency. No aggregate, timestamps or source
evidence is invented. The OpenAPI success example is a genuinely empty view;
the contract tests also exercise precise fractional, loss, zero and missing
values through real temporary SQLite repositories and source/wheel processes.

FastAPI's generated OpenAPI model represents the integer ordinal minimum as
`0.0`; the schema adapter restores that specific accepted bound to integer `0`.
This adjustment applies only to schema metadata. Financial payload floats remain
unsupported by the bounded encoder; Decimal service observations stay exact text.
