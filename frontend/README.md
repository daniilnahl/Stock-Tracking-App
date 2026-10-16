# Local packaged dashboard — issues #143–147/#152/#155

Implements the accepted read-only ADR-0014 client foundation and shared
monochrome shell: UI801–809, UI810–815, UI816–818, UI820–821, UI824–826, UI828 and X718 within
their bounded foundation scope. The owner accepted the revised all-text pixel
design and scoped ADR after PR #149; owner-merged #142 records acceptance.

The shared shell has typed Overview/Watchlists/Settings routes, a working
local light/dark theme preference and masked memory-only local API configuration.
Configuration does not verify authentication or make a request. Watchlists
supports explicit read/reload of both saved namespaces through that same session;
saved observations never claim live-price freshness. Stored-row detail re-reads
before selection, with explicit sparse raw history and an exact-value table.
Overview counts only the current validated saved namespace (#147). The deliberately
packaged dashboard and real source/wheel launcher integration are #155; the final
independent milestone audit remains #148.
The #143 **synthetic client
foundation demo** is preserved separately at `#client-foundation`. See the
[component guide](COMPONENTS.md) for inputs, navigation and theme contracts.
No backend/API contract, dependency, CI workflow or rights gate changes in #144–146/#152.

## Reproduce

Use installed Node **24 LTS, at least 24.19.0 and below 25**, and npm
**10.8.2** (tested; compatible npm 10/11 allowed). No system software is
installed by these commands. Node20 is EOL and is intentionally rejected.
There is one npm package manager and one committed package-lock.json.

```text
cd frontend
npm ci
npm run schema:check
npm run typecheck
npm test
npm run build
```

No development API proxy or automatic Python import/build/download exists.
The `dist` directory is local build output, not a committed artifact.
Production serving/allowlisting/distribution is implemented by #142/#155. Never
serve real API operations through a separate-port frontend development server.

## Deliberate Python distribution — issue #155

From `frontend`, run `npm ci`, `npm run package:dashboard`, then
`npm run package:check` before the normal Python wheel build. The package command
runs schema/type/Vite build and a separate explicit bridge; no Python install,
import, help or launcher path invokes it. Review and commit the five generated
files under `src/stock_tracker/api/dashboard_assets/`. Installed/API-only users
need neither Node/npm nor browser tools. Python's existing exact package-data and
route allowlists remain unchanged: `/` plus `/dashboard-assets/hosting.js`,
`hosting.css`, `stock-pixel.ttf`, `LICENSE.txt`. No directory mount, manifest
discovery, chunks, maps, dev source, fallback path or credential substitution.

Vite uses stable flat names and `/dashboard-assets/` as its base. The bridge
validates the exact input/output sets, external asset references, original font
and pinned production licenses before writes. It rejects unexpected files and
dependency drift; `--check` compares exact bytes without modifying package files.
`LICENSE.txt` combines project/original-font MIT text with local React19.3.1,
ReactDOM19.3.1, scheduler0.28.0 and emitted Vite8.3.4 modulepreload-helper core MIT
notices; Vite's dev-tool bundled notices are excluded. LF attributes pin the HTML input
and all packaged text; an actual isolated autocrlf checkout test protects Windows
byte parity. Build again and check rather than accepting line-ending normalization
or automatically discovering changed filenames. No dependency or lockfile changes.

## Actual launcher/installed-wheel browser integration — issue #155

After deliberate packaging, set `PLAYWRIGHT_CHANNEL=msedge` for installed Edge and
run `npm run test:integration`. It uses the existing canonical `.venv` Python
(override only via `STOCK_TRACKER_TEST_PYTHON` when necessary), builds/installs a wheel
offline into an ignored task-local target, and verifies source then wheel using
the real production launcher/composition at fixed `127.0.0.1:8000`. An occupied
port fails without stopping its listener; cleanup terminates only the owned child.
History rights remain disabled. Temporary real SQLite has explicitly synthetic
duplicate/null/zero/precise rows in both namespaces; no real DB or provider is used.
No `page.route` API mocks or test server replaces actual application requests.

The profile verifies exact source/wheel served bytes, closed routes, unchanged CSP,
actual local font, authenticated saved/detail/overview flows and safe disabled
history. SQLite hashes remain unchanged and cache/legacy paths stay absent.
Credentials are randomly generated at runtime and passed only through the child
environment and a test-context one-shot binding into the transient masked field.
No production hook is added. Field/DOM/output/path diagnostics use booleans; raw
child output is never dumped. Only theme persists. Traces, videos and automatic
screenshots are off. The integration config also sets Playwright1.64.1's recognized
`PLAYWRIGHT_NO_COPY_PROMPT` switch (`lib/index.js:_takePageSnapshot`) to suppress
automatic failure ARIA snapshots. Screenshots require an absent password field,
no token in DOM and conspicuous synthetic/no-live-data/rights-not-activated labels.
They remain in ignored `frontend/test-results/integration/`.

A deliberate negative diagnostic probe is opt-in: set
`STOCK_TRACKER_DIAGNOSTIC_PROBE=1` and run `npm run test:integration -- --project=source
--grep="explicit negative privacy"`. Expected exit is1 with a fixed boolean failure;
inspect artifacts for absence of trace/video/screenshots and `# Page snapshot`.
The masked probe value is generated inside the page and never returned. Unset
the probe flag before the normal passing integration command. This tests the
diagnostic control; it does not weaken application assertions or hide failures.

Direct runtime dependencies are only React/ReactDOM. Vite and its official
React plugin build TSX; TypeScript checks contracts; Vitest executes offline
unit/component tests; RTL/DOM/jsdom test accessible components. Playwright is
a separately invoked browser profile. No router, state library, JSON/Decimal
library, styling framework, additional linter or formatter is introduced.
Exact pins and transitive integrity hashes are in package.json/package-lock.json.
Registry engines and React/Vite/RTL peer ranges were checked before pinning.

Official compatibility/support references checked 2026-10-14:
[Node LTS/EOL](https://nodejs.org/en/about/eol),
[Node releases](https://github.com/nodejs/Release/blob/main/README.md),
[Vite](https://vite.dev/guide/),
[Vitest](https://main.vitest.dev/guide/),
[React versions](https://react.dev/versions),
[RTL](https://testing-library.com/docs/react-testing-library/intro/),
[jsdom engines](https://github.com/jsdom/jsdom/blob/main/package.json),
[Playwright](https://playwright.dev/docs/intro).

## Schema and exact numbers

`npm run generate` derives readonly contracts, runtime schemas and fixed
error/status/message contracts from the reviewed M7 snapshot at
`../tests/fixtures/api_foundation_openapi.json`. `schema:check` compares the
entire deterministic result and source hash, normalizing CRLF/LF for portable checks. Review schema changes rather
than regenerating blindly. The dependency-free generator supports only the
schema keywords actually used by M7 and fails on unknown constructs.

**Browser prerequisite:** native JSON.parse reviver `context.source` support
is required. The client probes this before retaining a credential and before
any private request; unsupported browsers receive a visible fixed failure.
There is no lossy parser fallback, polyfill, source rewrite or browser Number
conversion for Decimal/volume. [Normative parsing specification](https://tc39.es/ecma262/multipage/structured-data.html#sec-json.parse).

Every JSON numeric primitive is replaced by an internal original-lexeme
wrapper. Runtime schema validation accepts only original unsigned canonical
integer lexemes for integer fields, rejects wrong JSON types and overflow,
and returns volume as bigint. The generated int64 maximum comes from the
original schema lexeme `9223372036854775807`, never a rounded JS literal.
Ordinals alone become Number after proving they are safe nonnegative integers.
Decimal fields remain exact strings including scale/exponents. No new metric,
rounding or chart projection is performed. Zero and null remain distinct.
Objects/arrays are strictly validated and frozen before publication. Additional
checks bind namespace/ordered ordinals and history Stock/ordinal/date range/
ordered sparse bars. Unknown currency, freshness and provenance stay unknown.
This validates the approved wire contract without duplicating domain arithmetic.

## Native client lifecycle

`ApiClient` exposes connect/disconnect, immutable getSnapshot/subscribe,
loadWatchlist, selectRow and loadHistory. Features consume this single layer.
`connect` accepts only the existing API token grammar and exact fixed local
origins; the token remains in a private field and Authorization headers.
Outside its transient masked entry field, do not put it in DOM text/attributes,
React state, a URL, storage, log, fixture capture or build asset.
Use only synthetic credentials in tests. The #152 Settings control configures
this same client in memory without an implicit verification/read request.

Requests are relative same-origin GETs with no-store, omitted cookies,
redirect rejection and no-referrer. Responses are bounded to M7's 4MiB limit,
UTF-8 decoded strictly, then validated. HTTP401 immediately disconnects and
clears every private view even if its body is malformed. Other API errors
must match generated fixed status/code/message triples; raw errors and server
text never become diagnostics. There is no automatic retry or stale fallback.

Identical pending requests share one transport. Each consumer can cancel;
the transport aborts when its last consumer leaves. Disconnect, reconnect,
namespace changes, list reload and history-range supersession abort obsolete
work and suppress ignored late results using controller/session/selection
checks. A failed reload removes old values instead of declaring them current.

selectRow always re-reads the list and compares its exact Stock fields/ordinal
to the requested row. Missing/changed rows clear selection and require a new
choice. Selection objects belong only to that client/list revision; history
refuses copied/stale selections. A list reload always discards detail/history.
Identical duplicates have no stable cross-request identity: detail labels the
returned request-local selection, never a permanent holding ID. `clearSelection`
only invalidates selection/history and aborts their work; it retains the configured
connection and saved list. The feature aborts its pending selection read separately.

## Memory-only connection controls — issue #152

App creates one client and subscribes through useSyncExternalStore; session
context shares that exact client/snapshot across routes. The production entry
point has no injected client or global session handle; the optional App factory
is an isolated unit-test seam. The existing client's internal `connected` state
means configured, not authenticated. UI labels it **Configured** and explains
that configuration alone does not verify authentication. A completed protected
saved read is reported in Watchlists; configuration sends no verification or
implicit read request and does not become a permanent authentication claim.

Settings uses an uncontrolled native password input: no credential React state,
echo, URL, storage, export, bundle substitution or logging. Each submission passes
the whole password-field value directly to the strict client and immediately clears the DOM
field, including failed attempts. Native validation/truncation does not silently
truncate an overlength value or trim padding. Normal native password-field
normalization still applies. Only fixed ClientError diagnostics appear.
Retries require a new explicit entry. Replacement resets the old client session
and aborts/invalidates obsolete work under the existing client contract.

Disconnect clears the field/error/session and focuses the empty input. External
disconnect/authentication failure clears replacement drafts before painting the
disconnected state. Navigating away discards an unsubmitted draft while keeping
the page session; pagehide, cached-page restoration and App unmount disconnect.
Reload starts with a new empty client and field. Only theme persists. Browser
extensions/password managers and other same-user processes remain outside this
local trust boundary, as documented by ADR-0014.

The #152 lifecycle tests inject controlled client reads to verify
abort/generation/401 clearing through the shared session. Its connection controls
still make no read or authentication probe. Browser connection checks configure,
replace, disconnect and reload without private reads.
Synthetic credentials are generated at runtime, with browser generation entirely
inside the page rather than credential-bearing Playwright arguments. Password
empty checks and sensitive diagnostic assertions report booleans; recordings are
off. Manual demo screenshots are taken only after the field is verified empty.

## Saved watchlists — issue #145

Watchlists offers only `menu_watchlist` and `daniils_stock_method`. Read and
Reload are explicit saved GET operations: no automatic request on configuration,
navigation or namespace selection, quote acquisition or holdings mutation.
Reload clears the prior table while pending; failed/offline/incompatible reads
never restore stale rows. Cancel and namespace/route changes abort this view's
consumer; existing client generation/controller checks suppress late responses.
Disconnect/replacement/page lifecycle and HTTP401 clear private state. Data
remains only in the shared memory snapshot, with no local persistence.

Rows retain response order and use namespace plus response-local ordinal as
their React key. Visible ordinals distinguish identical duplicate rows without
claiming cross-request identity. Quantity, average cost and saved price display
exact Decimal strings, including scale/exponents, without numeric conversion.
Null average cost denotes unowned; explicit zero cost/quantity remains owned.
Null saved price is unavailable, never zero. Costs/prices are per share with
unknown currency. Source, times and freshness remain unknown even when opaque
saved metadata contains a currency-like label. No snapshot metrics, arithmetic,
totals, sorting or new API contract is introduced by the watchlist table.
Stored-row detail/history is isolated in #146 below.

Safe disconnected, unsupported, loading, cancelled, empty, success, network,
schema, legacy-state and authentication failures preserve usable explicit
recovery. Cancellation restores keyboard focus to Read. Component tests cover
these states and ignored late transport results. Separate browser checks
intercept only the two existing same-origin saved paths with synthetic payloads;
captures contain a conspicuous test-inserted synthetic/no-live-data banner.
No sample figures or browser-test mode ships in production assets.

## Stored-row detail and raw history — issue #146

Each visible ordinal has an Open detail action. It calls `selectRow` to re-read
the namespace and compare the expected exact Stock identity before publishing
the returned row. Missing/changed associations clear detail and require a new
choice; identical duplicates retain only response-local identity. Close, list
reload, namespace change and route unmount clear selection/history and abort
pending consumers. Disconnect/replacement/401 retain the client-wide clearing
contract. Cancellation/close/retry keep a stable keyboard focus target.

Detail displays saved inputs, opaque metadata and existing API snapshot values
without arithmetic or rounding. Monetary units explicitly have unknown currency;
unrealized return remains the API's dimensionless decimal ratio, never multiplied
into percentage points. Null/unowned/owned-zero and unavailable-return distinctions
remain explicit. Saved metadata is text, not a verified company profile or evidence
of currency, freshness, returns or source.

History requires an explicit read with both ISO dates or neither; default requests
display the API's returned inclusive range. Sparse raw OHLC strings, null adjusted
close, and exact bigint volume are shown in a named scrollable table. Session dates
are labels, not observation times. Declared source/cache-policy provenance is shown
without claiming live freshness; currency and observation/retrieval times stay unknown.
The safe `history_disabled` response explains the closed rights gate. No UI control
activates historical acquisition, changes server settings or grants provider rights.

The chart is an explicitly approximate scatter plot of returned close observations.
It draws no connecting lines or invented sessions. Its isolated disposable projection
uses browser Number only for chart geometry, with finite checks, nonzero-underflow
refusal and safe single/flat observations. Overflow/unsafe geometry omits the chart
while retaining exact values. These numbers never feed display values, storage or
financial metrics. Endpoint dates remain normal-size pixel HTML outside SVG; axes
and points use the theme text color. The precise table is always the numeric source.

Component tests cover fresh association, snapshot units/nulls, paired dates, disabled,
incompatible/offline/401 states, safe cancellation and late-result suppression. The
separate browser profile intercepts existing same-origin endpoints only, uses runtime
synthetic credentials, and inserts conspicuous synthetic/no-live-data labels into
focused detail/history/chart captures. There is no production fixture mode or new
dependency, API, provider activation, Python, CI or hosting change.

## Separate browser demonstration

```text
npm run build
npm run test:browser
```

The browser binaries must already be available for the installed Playwright
version, or deliberately provisioned in a local test cache by the operator.
For installed Edge, set `PLAYWRIGHT_CHANNEL=msedge` before the browser command.
The separate profile starts a loopback-only **test fixture**, serving only the
built index/JS/CSS/font on 127.0.0.1:8000 under a restrictive CSP. It fails if
the port is already in use; it never attaches to an existing user's server.
It has no API/backend, token, proxy or provider. It is not production hosting.
Default Python tests and npm unit/component tests do not start this fixture,
require a browser or access the network.

The profile verifies desktop/phone layouts, actual local pixel-font loading,
keyboard activation, exact displayed strings, safe error/clear behavior,
no implicit private API request and the unsupported-parser warning. Explicit
watchlist workflows use intercepted synthetic responses only. Screenshots are in
ignored test-results. This is bounded foundation evidence, not a full WCAG,
theme, production API or installed-wheel browser audit.

## Font

`src/stock-pixel.ttf` copies the project's original Stock Pixel font unchanged.
Its original glyph source and deterministic generator are maintained at
`../docs/previews/assets/`; license is the repository root LICENSE.
No third-party artwork/font or CDN is used. All demonstration text and controls
use real scalable text with this local font and a monospace fallback. Glyphs
cover this demo's ASCII; unimplemented localization is not certified.

## Issue #143 implementation verification (historical record)

Using Node24.19.0/npm10.8.2: schema drift/typecheck/production build pass;
Offline clean npm ci from the task-local cache passes (99 packages, audit zero);
64 deterministic frontend tests pass. Separate installed-Edge Playwright
profile: 3 passed, including 1440px/390px layouts and unsupported parsing.
Both production-asset screenshots were visually inspected.

Canonical Python3.12.14 commands ran against this checkout's source using the
existing approved environment without changing it: targeted API serialization,
watchlist/history, packaging and hygiene checks 111 passed (48.23s); full pytest
2762 passed (113.96s); Ruff, configured mypy (config.py) and pip check passed.
No live API/provider/user data was accessed. Required remote CI and owner
merge remain separate gates; this is not milestone completion.

## Issue #144 implementation verification — 2026-10-15

Existing Node24.19.0/npm10.8.2, unchanged lockfile: offline clean npm ci passed
(99 packages, audit zero); schema drift/typecheck/production build passed;
84 deterministic frontend tests passed. The separate installed-Edge browser
profile passed 11 checks, preserving the client foundation checks and adding
light/dark desktop/tablet/phone, keyboard navigation/back/skip, persistent theme,
blocked storage, local font, overflow and computed contrast/reduced-motion checks.
Light desktop and dark phone production-asset captures were visually inspected.

Canonical Python3.12.14: targeted dashboard hosting/packaging/hygiene 42 passed
in 65.49s; full pytest 2794 passed in 125.65s; Ruff, configured mypy (config.py)
and pip check passed. Sandbox startup limitations required approved native
execution for browser and Python subprocess checks. No real credentials,
provider, saved holdings or user database was used. Staged hygiene, independent
review, remote CI and owner merge remain separate gates. No full WCAG or M8
completion claim is made.

## Issue #152 implementation verification — 2026-10-15

Existing Node24.19.0/npm10.8.2 and unchanged dependencies/lockfile: final schema
drift/typecheck/production build passed; 102 deterministic frontend tests passed
in 2.66s; separate installed-Edge browser profile passed 15 checks in 12.2s.
Configured/disconnected desktop-light and phone-dark captures contain empty
password fields, no real credential or private observations, and were visually
inspected. Controls make no authentication verification/read request.

Canonical Python3.12.14: initial focused run had 41 passes and one existing
installed-wheel M6 audit failure when a cold Matplotlib font scan emitted
`Matplotlib is building the font cache; this may take a moment.` The installed
library emits this warning if enumeration exceeds five seconds. No Python,
cache policy or quiet-output assertion was changed. The unchanged isolated test
then passed in 60.73s; sequential targeted dashboard-hosting/packaging/hygiene
rerun passed 42 in 70.06s; full pytest passed 2794 in 176.56s. Ruff, configured
mypy (config.py) and pip check passed. This records the observed Windows timing
failure rather than hiding it or weakening verification.

No backend, Python dependency, CI, rights gate or user state changed. Staged
hygiene, independent review, remote CI and owner merge remain separate gates;
this does not establish M8 completion or live backend authentication.

## Issue #145 implementation verification — 2026-10-15

Existing Node24.19.0/npm10.8.2 with unchanged dependencies/lockfile: final schema
drift/typecheck/production build passed; 117 deterministic frontend tests passed
in 5.50s; separate installed-Edge browser profile passed 19 checks in 18.2s.
Browser coverage includes explicit namespace reads, duplicate/exact/null/zero
display, horizontal keyboard access, cancellation focus, retry focus, failed
reload recovery and shared-session 401 clearing. Captures of Menu desktop-light
and both namespaces on phone-dark show conspicuous synthetic/no-live-data labels
and contain no password field, real token or private holdings.

Canonical Python3.12.14: focused hosting/packaging/hygiene command passed 42 in
76.43s; full pytest passed 2794 in 175.69s. Ruff, configured mypy (config.py)
and pip check passed. Browser and Python suites ran sequentially. No backend,
Python/dependency, CI, distribution or user-state changes were required. Staged
hygiene, remote CI and owner merge remain separate gates; these checks do not
certify live API operation, full WCAG compliance or M8 completion.

## Issue #146 implementation verification — 2026-10-15

Existing Node24.19.0/npm10.8.2 and unchanged dependencies/lockfile: final schema
drift/typecheck/production build passed; 149 deterministic frontend tests passed
in 8.53s. Separate installed-Edge profile passed 25 checks in 22.3s, including
fresh duplicate association, exact Decimal/int64 history, paired-date refusal,
disabled rights, 401 clearing, keyboard cancellation/focus and phone overflow
for long untrusted symbols. The reproduced heading overflow was fixed with a
scoped wrapping rule; no client identity policy or API contract changed.

Canonical Python3.12.14: `python -m pytest tests/test_api_serialization.py
tests/test_api_watchlists.py tests/test_api_history.py tests/test_dashboard_hosting.py
tests/test_packaging.py tests/test_repository_hygiene.py -v` passed 142 in 74.02s;
full pytest passed 2794 in 158.43s. Ruff, configured mypy (config.py) and pip
check passed. Browser and Python suites ran sequentially under the shared
verification slot. No real API/provider/user database or production token was used.

Focused desktop/phone history/chart and disabled-state captures contain conspicuous
synthetic/no-live-data/rights-not-activated labels. The phone table's right-scroll
capture exposes exact max/zero/null volume; all password fields are absent.
Actual focused desktop history, phone chart and disabled phone captures were
visually inspected. No dependency, Python, CI, hosting or rights activation changed.
Root staged hygiene, remote CI, owner merge and combined distribution/M8 audit
remain separate gates; this is not certification of live entitlement or full WCAG.

## Issue #155 implementation verification — 2026-10-16

Existing Node24.19.0/npm10.8.2 and unchanged dependencies/lockfile: schema drift,
typecheck, production build and deliberate package bridge passed. Final frontend
suite passed 164 in 7.01s; existing separate installed-Edge browser regression
profile passed 27 in 26.4s. Actual source and offline-installed-wheel integration
profile passed 2 in 15.7s, using the production launcher/composition, temporary
synthetic SQLite, real same-origin API requests and disabled history rights.
Both distributions served exactly the reviewed asset bytes under unchanged CSP,
loaded the local font, retained read-only database bytes, and created no cache or
legacy files. Final byte check passed; repeated deliberate builds produced
identical SHA256 hashes for all five packaged resources, including font and
React/ReactDOM/scheduler/Vite-core notices. Scoped LF attributes and a real Git
checkout regression protect Windows asset bytes.

The bridge junction-refusal fixture initially encountered sandbox EPERM; the
unchanged test passed under approved native execution. The integration-only
controlled diagnostic probe deliberately failed with its fixed boolean assertion;
its retained error context contained no page/ARIA snapshot, screenshot, video or
trace. The normal source/wheel profile then passed separately. All final demo
captures show synthetic/no-live-data/rights-not-activated labels and contain no
password fields or real credentials. Source desktop and wheel phone captures
were visually inspected.

Canonical Python3.12.14: `python -m pytest tests/test_dashboard_hosting.py
tests/test_api_foundation.py tests/test_api_boundary.py tests/test_api_launcher.py
tests/test_packaging.py tests/test_repository_hygiene.py -v` passed 197 in 76.52s;
full `python -m pytest` passed 2795 in 157.12s. `python -m ruff check .`, configured
`python -m mypy` (config.py), `python -m pip check` and `git diff --check` passed.
Heavy suites ran sequentially, with no environment/dependency/CI/security-contract
change. Independent review found no unresolved findings. Root staged hygiene,
remote CI, owner merge and the remaining M8 audit are separate gates.
