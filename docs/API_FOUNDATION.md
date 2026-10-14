# REST foundation — issue #130

Accepted [ADR-0013](adr/0013-local-read-only-rest-api.md) defines the M7
contract. This foundation implements injectable transport infrastructure,
serialization and safety boundaries. It registers only GET `/health` and
GET `/api/v1/openapi.json`. No watchlist/history route, storage composition,
credential loading, production launcher or externally accessible listener is
introduced. Those are dependent #131–133 tasks.

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

Later handlers call `run_data_operation(app, operation, history=False)` with a
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
example and the actual protected schema endpoint. Its snapshot is reviewed in
`tests/fixtures/api_foundation_openapi.json`; route additions must deliberately
update that contract alongside endpoint tests.

## Access and response behavior

Request-target size is capped at 2,048 bytes of the raw path/query. The outer
ASGI boundary then requires one exact Host (`127.0.0.1:8000` or
`localhost:8000`), rejects every Origin header and authenticates `/api/v1`
before body processing or dependency acquisition. Authorization requires one
header with case-insensitive Bearer, one ASCII space and an exact valid token;
comparison uses constant-time comparison. No CORS or interactive docs exist.

Fixed routes reject all query parameters. Future history handlers own exact
paired-date validation. Nonempty bodies are refused: positive/malformed/duplicate
Content-Length fails before reading; undeclared bodies stop at the first nonempty
ASGI chunk. The full body is never collected. The consumed empty request is
replayed once, then receive delegates to the actual transport so disconnects
remain observable. Unsupported methods return safe 405; unknown paths return
safe 404 without redirects. All responses use `Cache-Control: no-store`.

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
