# Local REST operation — issue #133

Use the canonical Python 3.11/3.12 `pip install ".[dev]"` setup. The accepted
[ADR-0013](adr/0013-local-read-only-rest-api.md) permits one local single-user
process. This is holdings read-only operation: no endpoint saves, refreshes,
migrates or removes holdings. Historical requests, when separately enabled,
may maintain the existing historical cache. Hosting and additional users
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
