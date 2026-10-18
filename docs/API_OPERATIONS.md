# Local REST operation — issue #133

**Current delivery — 2026-10-18:** the manual Upcoming EPS dashboard and local
opt-in acquisition described here are merged and verified. The Stock criteria
page independently prepares custom data without a request; it does not search
or evaluate metrics. See [implementation status](CURRENT_STATUS.md) for delivered
scope and deferred features. The history rights gate is independent of EPS.

## Optional packaged dashboard — issues #142/#155

Append `--dashboard` to the existing four-path invocation to serve the packaged
production React dashboard at `http://127.0.0.1:8000/`. The required process token,
four distinct paths and fixed listener settings remain unchanged. Settings accepts
the existing token into a masked memory-only field; configuration makes no request.
Explicit Watchlists reads reuse the authenticated local API. Overview counts only
the last validated saved namespace; detail re-reads its request-local row. Theme
alone persists. Saved prices/currency/freshness retain their documented limitations.
Historical acquisition remains disabled without the separate rights approval below.

Without this flag, the original API route set and rejection of every Origin
remain unchanged. Dashboard mode additionally accepts one exact matching pair:
Host `127.0.0.1:8000` with Origin `http://127.0.0.1:8000`, or Host
`localhost:8000` with Origin `http://localhost:8000`. Absent Origin remains
valid; null, duplicate, mismatched and other origins are rejected before IO.
Every API operation still requires its bearer token. There is no cross-origin
CORS permission or development proxy exception; exact same-origin headers are
accepted only in this opt-in mode. No asset embeds or substitutes the token.

Only `/` and `/dashboard-assets/hosting.css`, `hosting.js`, `stock-pixel.ttf`
and `LICENSE.txt` are public static resources. Assets accept exact GET paths
without queries or bodies; encoded aliases, directory discovery, arbitrary
files, SPA fallbacks and source maps are unavailable. Missing resources fail
with the fixed safe error contract. Static routes do not alter OpenAPI.
All dashboard-mode responses carry a restrictive CSP, framing denial,
no-referrer and nosniff. Scripts/styles/fonts are local external assets;
inline code, remote assets, framing and forms are prohibited. API no-store
responses remain unchanged. No service worker or runtime build/download exists.

The wheel includes an explicit asset list. Python install/import/help does not
require Node or read assets; resource reads occur only on valid static GETs.
The original font is distributed with the repository MIT license. `LICENSE.txt`
also includes the bundled React19.3.1, ReactDOM19.3.1, scheduler0.28.0 and emitted
Vite8.3.4 modulepreload-helper core MIT notices (not Vite's dev-tool bundled notices).
Editable font glyphs/generator remain in `docs/previews/assets/`. Deliberate asset
generation and source/installed-wheel browser verification are documented in
[frontend/README.md](../frontend/README.md). Runtime startup does not discover assets,
run Node or download/build anything. Installed users need no frontend toolchain.

The following original M7 operation instructions describe default API mode;
the opt-in Origin/static exception above applies only with `--dashboard`.

Use the canonical Python 3.11/3.12 `pip install ".[dev]"` setup. The accepted
[ADR-0013](adr/0013-local-read-only-rest-api.md) permits one local single-user
process. This is holdings read-only operation: no endpoint saves, refreshes,
migrates or removes holdings. Historical requests, when separately enabled,
may maintain the existing historical cache. External hosting and additional users
require separate approval. M7 completion still requires the #134 combined audit.

## Configuration and start

Run `python -m stock_tracker.api --help` without a token or data configuration.
Help uses static text and reads no application environment, locale files,
terminal settings, database, provider configuration or cache. The supported
options use a separate argument value (`--database FILE`); there are no option
abbreviations, argument files, token arguments or arbitrary server flags.

Before starting, supply a distinct operator-generated secret through the
process environment as `STOCK_TRACKER_API_TOKEN`. It must contain 32–256 ASCII
letters, digits, underscores or hyphens, with no whitespace. Use a suitably
random token from your protected secret-management mechanism; never paste it
into documentation, URLs or screenshots. This local access token is distinct
from your provider credential. The API token is never loaded from `.env`,
given a default, persisted, printed, logged or included in configuration repr.
Changing it requires restarting the process.

All four file arguments are required. For example, in PowerShell after setting
the token in the process environment:

```powershell
python -m stock_tracker.api --database C:\LocalState\stock_tracker.sqlite3 --history-cache C:\LocalState\history-cache.json --menu-legacy C:\LocalState\watchlist.pkl --evaluation-legacy C:\LocalState\daniils_stock_methodd.pkl
```

Choose paths deliberately; the example is not an implicit default. Relative
paths resolve once against the launch working directory. The launcher creates
no parent directory and opens no state contents or SQLite/cache file. It may
inspect metadata to resolve existing symlink parents/targets and reject file
aliases. All four paths must be distinct after native case normalization and
existing same-file checks, including hard links. Missing-path collisions,
dangling symlinks/junctions, loops, file-as-parent paths, directories as file targets and
inaccessible metadata are refused with one safe configuration message. Native
Windows drive-relative, device/extended-namespace, reserved, stream and trimmed
dot/space spellings are refused as ambiguous. Resolution does not create a
missing path. Keep the selected locations stable while the process runs;
metadata validation is a launch check, not a filesystem sandbox.

The server configuration is fixed: **127.0.0.1:8000**, one worker, no reload,
no trusted proxy headers and no access logs. It offers no interactive docs or
CORS. Generic server diagnostics are restricted; launch failures use fixed
messages rather than raw exceptions, paths or supplied values. Never expose
this listener through a reverse proxy or port forwarding under this contract.

## Local requests and stop

Public `GET http://127.0.0.1:8000/health` returns `{"status":"ok"}` for process
liveness. It does not certify state validity, provider readiness or entitlement.
Authenticated `GET /api/v1/openapi.json` provides the typed static contract.
Local clients must send exactly one `Authorization: Bearer <local token>` header
for every `/api/v1` request, never a query token. Only Host `127.0.0.1:8000` or
`localhost:8000` is accepted, and every Origin header is refused, including null.
These checks precede dependency acquisition. Responses use `Cache-Control: no-store`.
Loopback plus bearer does not protect against another process under your user.

Saved routes are `/api/v1/watchlists/menu_watchlist` and
`/api/v1/watchlists/daniils_stock_method`. They use the existing WatchlistService
and temporary per-operation SQLite connections. Saved values, ordered duplicate
rows and namespace identity are preserved; prices have unknown freshness and
saved metadata does not establish currency. A missing database in an existing
parent returns an empty view without creating it. Missing parents, corrupt or
future-schema state fail safely. The corresponding legacy path is checked only
for existence when a namespace is absent; its contents are never read or
deserialized. Preserve legacy data and follow the existing neutral transition
guide when `legacy_state_present` is returned. Existing structured namespaces
remain authoritative. No backup, schema or migration policy changes here.

Stop the foreground process with **Ctrl+C** and allow active work to finish.
Restart using the same explicit paths and a protected token. A failed start
does not replace holdings/cache or create directories. Check all four path
arguments, filesystem permissions, token grammar and whether another process
already occupies port 8000. Do not delete state to fix a configuration error.

## Historical activation gate

**Current rights evidence: not supplied. Live historical API operation is not
activated or verified by this task.** Code acceptance, a provider key, prior CLI
access and offline fixtures do not establish API display or cache-retention
rights. Before using `--enable-history`, the owner must record relevant official
subscription/entitlement evidence, local display permission, cache storage and
retention limits, attribution, automation/rate limits and applicable restrictions
in this operation record (or a linked owner-approved record). If unsupported or
uncertain, keep history disabled; saved local views remain available.

Only after that prerequisite, explicitly append `--enable-history`. This flag
is a capability switch, not a license grant. Without it, the stored-history route
returns 503 `history_disabled` before acquiring holdings, provider or cache.
Enabled requests freshly load the selected namespace/ordinal, then the shared
HistoryService validates the exact saved Stock, NASDAQ scope and dates before
provider acquisition. Unknown rows and invalid ranges cannot trigger credentials.
Local views require no provider key, even when the flag is enabled.

Only supported enabled history lazily invokes existing `config.load_configuration`
and `providers.factory.create_historical_market_data_provider`, with the explicit
resolved cache path. Existing FMP process/dotenv semantics remain unchanged;
configuration/key failures map to fixed 503 `provider_unavailable`, not client
401. UTC defaults, raw Decimal OHLC, sparse sessions, one-hour cache policy,
bounded retries and no stale fallback remain authoritative. Production responses
declare source `fmp` and freshness `accepted_cache_policy`; timestamps and
currency remain unknown. The flag changes no holdings, financial formula or
external provider policy. See [API contract details](API_FOUNDATION.md) for
exact strings/nulls, dates, units, errors and resource bounds.

## Upcoming EPS — opt-in local acquisition, issues #178/#180

[ADR-0016](adr/0016-upcoming-eps-api.md) stage 1 adds authenticated
`GET /api/v1/research/upcoming-eps?provider_symbol=TEST&start=2026-10-19&end=2027-01-18`.
This synthetic request illustrates syntax, not a current-date preset. Supply
exactly one explicit case-sensitive provider symbol and each ISO calendar date;
the inclusive window is at most 92 dates and must begin after the service's
injected UTC reference day. No symbol lookup or saved-holdings association occurs.

The launcher keeps EPS disabled by default and returns fixed 503 `eps_disabled`
after input validation, without looking up a key or contacting Finnhub. To opt
in, append `--enable-upcoming-eps` to the existing four-path launch command.
This flag is independent of `--dashboard` and `--enable-history`; it does not
enable history. With `--dashboard`, use the **Upcoming EPS** page after configuring
the existing local connection in Settings. Enter an explicit provider symbol and
start/end dates, then submit manually; no request runs just by opening the page.
Editing, clear, cancel or leaving this route removes earlier results. Neither
the form nor its results are stored across reload. Manual requests require the
local API bearer token. An embedding caller may independently inject
`ApiServices(upcoming_eps=service, upcoming_eps_enabled=True)` into `create_app`.

The owner confirmed personal non-business research and exclusive use of the
relevant Finnhub account quota. Maintain those conditions and run only one
instance: the local budget does not coordinate other keys, apps or machines.
The prior live smoke established calendar access at that time; it is not a
guarantee of future access or a separate permission grant.

Start from a terminal whose **process environment** contains `FINNHUB_API_KEY`.
If the Windows user variable was added after the terminal/app started, restart
the launching process so it inherits the new value. Production does not read
the Windows user registry directly, invoke dotenv or fall back to FMP keys.
Do not put the Finnhub key in a query, command-line argument or browser field.
The local bearer and provider key have separate roles.

Enabled startup performs no Finnhub call or key validation. One server-owned
UTC reference day is sampled for each locally valid operation. After its
future-date check and budget admission, lazy composition loads/validates the
process key and builds the restricted native provider with a 5.0-second timeout,
262144-byte response bound and 128-row bound. Missing/invalid credentials return
fixed 503 `provider_unavailable`; health/schema remain available.

For the first 60 seconds after enabled app creation, valid EPS requests return
fixed 429 `eps_rate_limited`, immediately. Thereafter the app permits at most
30 provider-acquisition attempts in a trailing 60 seconds and one in flight.
Key validation/construction failures still count; cancellation does not refund
an attempt. An upstream 429 returns `provider_rate_limited` and starts another
60-second local cooldown at receipt. A timestamp expires when age reaches 60
seconds. There is no sleep, request queue, retry, polling, cache or stale fallback.
Restart creates a fresh budget with the startup quiet period again. Existing
shared/EPS active-operation capacity refusals remain 503 `api_busy`.

Successful responses preserve reported non-GAAP EPS as exact decimal strings
or null, fiscal quarter/year, release date/session and UTC receipt time.
Currency, share basis, publication time and fiscal-period end remain unknown.
Coverage is `not_asserted`; an empty list establishes no completeness or absence
of upcoming earnings. No EPS growth, comparison or ranking is calculated.
Invalid local input is 422; upstream access failures are safe 503 categories,
with existing rate-limit/timeout/malformed-response categories preserved. EPS
has one active-operation slot inside the API's shared four-operation capacity.

The owner-authorized isolated live test passed through the actual native Finnhub
transport/service/injected API; see [dated evidence](milestones/m9-eps-api-178.md).
That smoke was separate from production activation and automatic tests.
The accepted #180 composition uses only deterministic mocked HTTP in tests;
see [launcher/budget evidence](milestones/m9-eps-composition-180.md).

## Offline verification limits

Launcher tests replace `uvicorn.run` and never start a real listener. Real
temporary SQLite/service tests and typed fake provider factories establish lazy
acquisition, path safety, safe errors and unchanged bytes. Cold source/wheel
help imports use independently proven guards; launch configuration separately
permits only synthetic token lookup and metadata validation before no-IO
health/schema/disabled-route serving guards. The foundation's narrow framework
code-metadata/tuning exceptions remain disclosed. Windows tests attempt real
symlinks; unavailable creation privilege uses equivalent synthetic metadata/
resolution fixtures, without changing OS settings. Existing hard-link checks
run against real temporary files. Native Windows junction tests also verify
missing-target alias resolution and refusal of dangling reparse-point parents;
synthetic non-symlink metadata independently covers that refusal branch.
These tests do not establish live entitlement,
historical completeness or milestone completion.
