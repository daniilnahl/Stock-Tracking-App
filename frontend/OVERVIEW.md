# Supported overview — issue #147

The Overview reads the existing App-owned client snapshot. It creates no client,
collects no credential, calls no API and stores no additional preference. Theme
and connection controls continue to use the unchanged #144/#152 implementations.

The three status cards show the session's configuration state, supported entry
count and unknown observation freshness. Count evidence requires a connected
session and a validated successful watchlist whose namespace matches the client
snapshot. The count is the returned array length, including ordered duplicate
rows, for that namespace only. An empty successful list gives zero. Idle,
loading, failed, cancelled, disconnected, unsupported or mismatched state gives
Unavailable, never an invented zero or a retained previous count.

The existing Saved observations rectangle names the loaded namespace and saved
list name, with scope and unknown source/time/currency/freshness labels. It links
to Watchlists for explicit reads and holds no duplicate holdings table. Saved
names are React text. Observation labels never claim live quotes or derive
currency/age from opaque metadata. There is no sum across namespaces, portfolio
valuation, return, risk calculation, analytics route or extra endpoint.

The exact two future-feature panels remain above the same three cards.
Search/add keeps its explanation and fixed source-document link; no request or
save action is enabled. Recommendation/agent services and live history remain
unavailable under their separate acceptance and rights gates.

## Contracts and files

- `src/features/OverviewSummary.tsx`: one shared success-evidence gate and the
  three cards, using existing palette/type/spacing/accessibility tokens.
- `src/features/ShellPages.tsx`: Overview wiring and the existing panel's scope
  text/navigation. Settings and SearchDisclosure behavior remain unchanged.
- `tests/overview.test.tsx`: both namespaces, duplicate-inclusive count, known
  empty zero, precise scope, unsafe-name escaping, unavailable/reset states,
  pending cancellation and no automatic fetch/storage.
- `browser/overview.spec.ts`: separate installed-Edge production-asset fixture
  checks for light desktop and dark phone, manual reads, scope switching,
  duplicate count, empty zero, disconnect clearing and no navigation fetches.

Legacy shell tests now check Overview's panel/navigation rather than an empty
holdings table. Real Watchlists horizontal scrolling remains covered by #145.
The theme-notice tests target their named notices, because the supported count
adds a separate polite status region.

## Verification and demo boundaries

Use the existing pinned frontend toolchain and separate browser profile from
README.md. No dependency, lockfile, Python/API/hosting or CI change is required.
`npm test` and `npm run build` include the new tests and schema/type checks.
Canonical Python tests still verify unchanged source/installed-wheel behavior.

Browser tests intercept only the existing API read routes with labeled isolated
synthetic responses. Credentials are generated inside the page and cleared from
the masked control before leaving Settings; captures contain no credential
field. Trace, video and automatic failure screenshots remain disabled. The demo
banner explicitly identifies synthetic data. No live API/provider/user state,
financial evidence, installed dashboard integration or full WCAG/M8 completion
is inferred from this bounded demonstration. Distribution remains #155/#148.

## Implementation verification — 2026-10-15

Using the existing pinned Node 24 runtime/npm and unchanged dependency set:

- `npm test`: 124 unit/component tests passed, including seven overview cases.
- `npm run build`: schema drift check, TypeScript and production build passed.
- `PLAYWRIGHT_CHANNEL=msedge npm run test:browser`: 21 checks passed in 19.0s.
  Production-asset light desktop (1440px) and dark phone (390px) captures were
  visually inspected. They show a clearly labeled synthetic duplicate-inclusive
  count of three, the approved two panels/three cards/panel shape, local pixel
  text and no credential field. Long saved-list names also passed overflow checks.

Using the existing approved Python 3.12.14 interpreter, with the secondary
checkout as working directory and the existing isolated temporary directory:

- `python -m pytest tests/test_dashboard_hosting.py tests/test_packaging.py tests/test_repository_hygiene.py -q`:
  42 passed in 73.25s.
- `python -m pytest -q`: 2,794 passed in 162.91s.
- `python -m ruff check .`, configured `python -m mypy` (config.py only),
  `python -m pip check` and `git diff --check` passed.

Native execution was authorized for the assigned managed worktree, Windows
control sockets, temporary fixtures and installed-Edge profile; application
network/data-isolation guards stayed active. Python/browser checks ran
sequentially. No environment mapping, supported version, dependency, server
contract, provider activation or real user state changed. Required staged
credential inspection, independent review, remote CI and owner merge remain
separate gates. This is not the final installed-dashboard/M8 exit audit.
