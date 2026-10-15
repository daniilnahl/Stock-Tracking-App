# Dashboard client foundation — issue #143

Implements the accepted read-only ADR-0014/UI801–802, UI810–811,
UI816–817, UI824 and UI826 foundation. The owner accepted the revised
all-text pixel design and scoped ADR after PR #149; root #142 records that
acceptance. This branch deliberately retains its independent #149 base.

The small React page is a **synthetic client foundation demo**, with no API
calls, token entry, real holdings or production sample prices. Full shell,
themes, watchlists, settings and browser/distribution audit are #144–148.
No backend/API contract, Python dependency, CI workflow or rights gate changes.

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
Production serving/allowlisting/distribution is owned by #142/#148. Never
serve real API operations through a separate-port frontend development server.

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
Do not put it in a URL, DOM, storage, log, fixture capture or build asset.
Use only synthetic credentials in tests. Token-entry UI is reserved for #147.

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
Identical duplicates have no stable cross-request identity: later features must
label details as a returned request-local selection, not a permanent holding ID.

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
keyboard activation, exact displayed strings, safe error/clear behavior, no
private API request and the unsupported-parser warning. Screenshots are in
ignored test-results. This is bounded foundation evidence, not a full WCAG,
theme, production API or installed-wheel browser audit.

## Font

`src/stock-pixel.ttf` copies the project's original Stock Pixel font unchanged.
Its original glyph source and deterministic generator are maintained at
`../docs/previews/assets/`; license is the repository root LICENSE.
No third-party artwork/font or CDN is used. All demonstration text and controls
use real scalable text with this local font and a monospace fallback. Glyphs
cover this demo's ASCII; unimplemented localization is not certified.

## Implementation verification

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
