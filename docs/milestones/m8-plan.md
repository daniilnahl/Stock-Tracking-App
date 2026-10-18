# M8 — Web Dashboard execution plan

**Current delivery — 2026-10-18:** the final audit (#162) and README follow-up (#163) are owner-merged and all M8 issues are closed. Assignments below are dated execution history. The administrative milestone remains open; the dashboard has since gained accepted M9 criteria/EPS pages. See [current status](../CURRENT_STATUS.md).

## Final audit and README follow-up — 2026-10-16

The owner confirmed PR #159 merged and requested the final push, followed by
streamlining the main README. PR #159 is verified owner-merged at
`4474c44322a58c7d8fa98e7c63e8f044030127ef`, containing reviewed packaging head
`71fab3f5e1d3560f0b0db354b9d9b4cf50210eee`. Exact-head Foundation `38943862172`
and combined main Foundation `38944336927` passed all five jobs. #155 is closed.

#148 is delegated to `m8_review`, independent of the frontend implementation,
on `codex/148-m8-exit-audit` from that main. It owns bounded actual source/wheel
browser audit checks, clean-install verification and requirement/exit evidence.
The Master owns this plan/publication; another agent and the Master independently
review the audit change. No production feature, dependency, CI, rights or hosting
expansion is authorized. Heavy native suites remain serialized. Demonstrations
must use labeled synthetic state with no credential-bearing artifacts. Full
WCAG certification or untested browser/screen-reader coverage must not be claimed.

#160 records the owner's README follow-up. Its edits begin after the audit work
is verified and will be a separate bounded documentation PR. It preserves the
canonical setup anchor, current command/security/data contracts and links to
historical evidence while removing stale milestone narratives. Neither audit
readiness nor README cleanup closes M8 before required owner merges/main CI.

The audit reproduced two bounded layout defects: header overflow with enlarged
Overview text/spacing and a namespace select grid overflowing at 320px. Header
wrapping and a zero-minimum grid track preserve the approved pixel themes and
native controls. Strict real-launcher regressions and deliberate packaged CSS
checks cover these fixes. Evidence scopes text overrides/media emulation and
distinguishes actual fresh-session 401 from controlled nonempty-state clearing.
No API, privacy, financial or provider-rights behavior changes.

Final audit verification: fresh Python environment canonical install; targeted
297 and full 2795 passed. The final CSS-only grid correction was followed by
43 hosting/packaging/hygiene passes, with the pre-existing cold Matplotlib
warning and unchanged successful retry explicitly recorded (follow-up #161).
Final frontend 164, fixture browser 27 and real source/wheel workflows 2 passed;
each actual workflow covers eight viewport/theme combinations plus bounded
text/media/session checks. Schema/type/build/package byte check, Ruff, configured
mypy and pip check passed. Independent source/test/evidence review found no
actionable issue. Master inspected the actual installed-wheel labeled 200% CSS
text capture; normal viewport and narrow phone captures are also available.
Staged hygiene, exact-head hosted CI and owner merge remain publication gates.

## Production distribution — 2026-10-15

The owner instructed **“Pr merged continue the work”**. PR #157 is verified
owner-merged at `bcd83f4909abebe4d1b3ed6345f13e433dc1791e`; PR #158 at
`15f73b14a36c8db60c0a40d117eda391acf5cc00`. The combined main Foundation
`38845989101` passed all five jobs. Issues #146 and #147 are closed by their
owner merges. Their exact-head checks and independent reviews also passed;
synthetic frontend demos were delivered for both.

#155 is delegated to `frontend_plan` on `codex/155-dashboard-distribution`
from that combined main in the primary worktree. The Master owns this plan
and publication; `m8_review` will independently review the implementation.
The scope is a deliberate reproducible build-to-package step, reviewed closed
static routes, source/installed-wheel asset parity and actual launcher/browser
integration over isolated synthetic SQLite. No broad static mount, runtime
discovery, Python import-time Node/build/download, new dependency, CI change,
endpoint, financial behavior or live rights activation is included. Heavy
native suites are serialized. All credential-bearing artifacts are prohibited;
visual demos use labeled synthetic state with masked controls absent.

#148 remains blocked until #155 is reviewed, owner-merged and main CI passes.
M8 is not complete; earlier sections retain their dated implementation history.

### #155 implementation and review

The deliberate frontend package bridge now builds stable flat files for the
existing five Python routes, refusing extra files/maps/chunks and linked output
directories. It checks the original font and bundles project/font and pinned
React/ReactDOM/scheduler and Vite runtime-helper MIT notices. A no-write check detects exact byte drift;
scoped LF attributes and an actual autocrlf checkout regression preserve Windows
bytes. The existing Python static allowlist/package data, CSP, Origin/Host,
authentication and no-store controls remain unchanged. Python startup, import,
help and installation never invoke the frontend toolchain.

The separate actual-launcher browser profile runs source and an offline-installed
wheel over temporary synthetic SQLite without API mocks. Both verify every asset
byte, local font/CSP, authenticated saved namespaces/duplicates/exact values,
detail, overview and HTTP503 disabled history. Database hashes remain unchanged;
cache and legacy paths remain absent. Only the owned child is terminated and an
occupied port is refused. Runtime random credentials are absent from captured
DOM, fields and diagnostics; automatic trace/video/screenshots and failure ARIA
snapshots are disabled. An explicit negative probe verified that failure output
contains no such artifacts. It is separate from passing application checks.

Master inspected the actual synthetic desktop overview and installed-wheel
dark-phone overview/disabled-history captures, with readable pixel text and
unavailable panels preserved. Frontend tests 164, schema/type/build and package
byte check, existing browser regressions 27 and final source/wheel integration 2
passed. Repeated production builds produced identical hashes for all five assets.
Final targeted Python verification passed 197 in 76.52s; the original full-suite
session completed successfully with 2795 passed in 157.12s and was recovered after
an account-usage interruption, without a duplicate full run. Independent final
source/test/docs review, including the Vite helper notice, found no actionable
issue. Ruff, configured mypy (config.py), pip check and the final package byte
check passed. Staged hygiene, hosted CI and owner merge remain publication gates.

## Detail/history and overview — 2026-10-15

The owner instructed **“pr merged, continue the work”**. PR #156 is verified
owner-merged at `481c7609d34720f5819d0c001b98f2ee6de92e30`, containing reviewed
watchlists head `291688906f8841fe6554159a3973820fc2742733`. Exact-head Foundation
`38812823965` and post-merge main Foundation `38813607165` passed all five jobs.
#145 is closed through its owner merge, with visual demos of both namespaces.

#146 is delegated to `frontend_plan` on `codex/146-stored-row-history` in the
primary task worktree. #147 is delegated to `m8_analysis` on
`codex/147-supported-overview` in the clean reused managed `m8-api-client`
worktree. Both start from `481c760`. Independent review is assigned to
`m8_review` and the Master. Ownership is non-overlapping: #146 owns Watchlists,
detail/history/chart and any minimal client selection-invalidation helper;
#147 owns Overview and reads the existing session without changing it. The
SearchDisclosure contract stays stable. Shared docs are #146/Master-owned;
#147 documents its feature separately. Heavy Python/browser checks are serialized
to avoid port and native-font-cache contention.

#146 must re-read and validate the exact namespace/ordinal/Stock before detail,
discard obsolete selections/history, retain exact raw values and bigint volume,
and label checked finite chart projections as approximate beside the exact table.
Live history rights remain disabled. #147 counts only the explicitly named
successful loaded namespace, including duplicates; unavailable data is not zero
and no global total or automatic request is invented. It reuses the existing
theme/connection lifecycle and preserves the unavailable future panels.
Neither issue changes backend endpoints, dependencies, CI, hosting, financial
formulas or rights activation. #155 waits for both owner merges/main CI before
the actual asset/launcher/wheel bridge; #148 remains the independent exit audit.

### #146/#147 implementation and review

#146 opens detail only through a fresh exact namespace/ordinal/Stock selection.
Close, list reload, namespace/route change and disconnect clear obsolete detail
and history, with a minimal additive client invalidation helper. Existing saved
inputs/snapshots remain exact, with unknown currency and explicit decimal-ratio
return units. Raw history uses paired dates, sparse returned points, an exact
OHLC/bigint-volume table and separately checked finite approximate coordinates.
Unsafe projection hides only the chart; history rights remain server-gated.
HTML date labels retain readable pixel text on phones and axes use contrasting
theme text tokens. No financial formula, adjusted return or session is invented.

#147 derives duplicate-inclusive counts solely from the named current successful
watchlist snapshot. Known empty is zero; loading, failure, cancellation,
disconnect/replacement and unsupported/inconsistent state are unavailable.
It creates no client, credential state, storage or request. The two unavailable
future panels, three cards and Saved observations rectangle remain; that last
panel now contains truthful scope/provenance/navigation instead of an obsolete
empty holdings table. Scoped wrapping handles untrusted long saved-list names.

Independent `m8_review` reviewed both issues' source, unit/browser code and
feature documentation with no remaining actionable finding. Actual browser and
canonical checks plus Master visual inspection remain issue-specific release
gates; no standalone fixture is claimed to satisfy installed integration.

#147 final verification passed in its isolated worktree: 124 frontend tests,
schema drift/TypeScript/production build, 21 installed-Edge browser checks,
targeted Python 42 and full pytest 2794, Ruff, configured mypy (config.py), pip
check and final staged hygiene 9. Master inspected actual labeled synthetic
light desktop/dark phone captures and confirmed the approved panel structure.
PR #157 publishes head `579f620605275eda6840c41b278efb9646c2cc67` independently
of #146. Exact-head Foundation `38845080867` passed all five jobs;
`MASTER-REVIEW-PASSED` is recorded in the PR because its authenticated author
cannot approve its own PR. Owner merge remains required; no control is bypassed.

#146 final verification passed: 149 frontend tests, schema drift/TypeScript/
production build and 25 installed-Edge browser checks; targeted serialization/
watchlist/history/hosting/packaging/hygiene 142 and full pytest 2794; Ruff,
configured mypy (config.py) and pip check. The long-symbol phone overflow case
was reproduced and fixed through scoped heading wrapping, without changing
client policy or backend behavior. Master inspected focused synthetic desktop
history, phone chart and disabled-history captures; exact data remains accessible
by table scrolling and live history rights remain off. No unresolved independent
source/test/documentation finding remains. Final staged hygiene, exact-head
hosted CI and owner merge remain separate gates for this branch.

## Saved watchlists — 2026-10-15

The owner instructed **“pr merged, continue the work”**. PR #154 is verified
owner-merged at `502c1feacf1dd98f0d4251c30832509f2f1be7ee`, containing reviewed
connection head `e2c2ae764378386521e5b654a8a8ae0cad1d9fee`. Exact-head Foundation
`38809385901` and post-merge main Foundation `38810779189` passed all five jobs.
#152 is closed through the owner merge, with its actual frontend demo delivered.

#145 is delegated to `frontend_plan` on `codex/145-saved-watchlists` from combined
main `502c1fe`. It reuses the single memory-only session and existing API client
for both saved namespaces, preserving request-local ordinals, duplicate order,
exact Decimal text and distinct unowned/zero/missing states. Prices retain
unknown currency/freshness labels; opaque metadata is not provenance. Reads and
reloads reread saved observations, never request current market quotes.
Independent review is assigned to `m8_analysis`. No endpoint, calculation,
mutation, detail/history, aggregate overview, dependency, backend, CI or hosting
change is included. #146/#147 remain blocked until #145 owner merge/main CI.
#155 separately integrates the completed production frontend into the Python
package/launcher after those views merge; #148 independently audits that actual
installed integration. The current Python host still serves its readiness
assets, so a standalone frontend fixture is not claimed to complete UI827.
This decomposes already accepted distribution work rather than expanding its
architecture or hiding implementation inside the final audit. Earlier snapshots follow.

### #145 implementation and review

The Watchlists route now uses the shared client for explicit saved reads,
reloads, cancellation and retry. Selecting a namespace or configuring a token
makes no request. Tables preserve response order/duplicates and show the actual
request-local ordinal, exact quantity/cost/price strings, ownership and distinct
unavailable states. Average-cost null follows the accepted unowned contract;
owned zero quantity/cost remains numeric. Currency/source/times/freshness remain
unknown; saved metadata never establishes provenance. No totals or new metrics
are calculated. Snapshot namespace and request cancellation gate all rendering.

Review refinements keep namespace text in the pixel font, display ordinals,
restore stable keyboard focus after Cancel/retry, distinguish user cancellation
from session resets, and bind browser fixture labels to each held request.
Shared header/settings copy describes configuration without falsely claiming
that successful saved reads are unverified or that no observations were loaded.
Overview keeps its approved layout and directs reads to Watchlists; aggregate
overview integration remains #147. Browser captures use a conspicuous test-only
synthetic banner, with no fixture mode or sample holdings in production code.

Independent `m8_analysis` and Master source/test review found no unresolved
runtime or test issue. Master visually inspected actual production-asset Menu
desktop and right-scrolled dark-phone saved-price captures: synthetic labeling,
pixel typography, separate duplicate rows and horizontal data access are visible.
These controlled responses are not live data or final installed integration.
Canonical Python 3.12.14 verification passed: targeted hosting/packaging/hygiene
42 tests and full pytest 2794 tests, with unchanged quiet packaging probes.
Final frontend verification passed: schema drift/TypeScript/production build,
117 unit/component tests and 19 separate installed-Edge browser checks. Ruff,
configured mypy (config.py) and pip check passed. Suites ran sequentially in
the existing approved environments with native-process sandbox escalation.
Master additionally inspected the Method dark-phone capture, confirming both
namespace demos are present. No real credentials, holdings, user database or
provider traffic was used. Final staged hygiene, exact-head hosted CI and owner
merge remain separate gates; successor implementation is still blocked.

## Connection prerequisite — 2026-10-15

The owner instructed **“pr merged, continue the work”**. PR #153 is verified
owner-merged at `bd11a0c85209ee487d1287fb17712fa5f1f4da35`, containing reviewed
shell head `e4b9e089406b277eaaef483ccf2fbe30d5bea85f`. Exact-head Foundation
`38737993534` and post-merge main Foundation `38806969664` passed all five jobs.
#144 is closed through its owner merge; production-asset visual demos were
delivered. No agent merge occurred.

#152 is delegated to `frontend_plan` on `codex/152-memory-only-connection`,
based on main `bd11a0c`. One App-owned client/snapshot will drive a masked
Settings input, configuration/disconnect state and private-state invalidation.
Only theme persists. Configuring a token makes no request and cannot establish
verified authentication; protected reads remain #145 work. Route changes keep
the shared client but discard unsubmitted input; reload/disconnect/page exit
discard credentials/private state. No watchlist rendering, metrics, endpoint,
hosting, dependency, backend or CI changes are included.

#145 waits for #152's owner merge/main CI. #146/#147 wait for saved watchlists;
#148 remains the final integrated/distribution audit. The earlier snapshots
below retain implementation and review history.

### #152 implementation and review

One stable App-owned `ApiClient` and `useSyncExternalStore` snapshot now drive
the Settings controls and configuration labels across routes. The native masked
field is uncontrolled; submission validates its complete value without trimming
or truncation, clears the field, and sends no request. Only the theme persists.
Replacement/disconnect/reload/page exit and external authentication-reset paths
discard private state and drafts through the existing client lifecycle.
The interface explicitly states that configured credentials are not verified
authentication; saved-data rendering/reads remain #145 work.

Independent `m8_analysis` reviewed source and regression coverage. Review repairs
removed native truncation, cleared replacement drafts on external disconnect/401,
kept fixed errors useful, prevented credential values in test diagnostics and
clarified the isolated synthetic demo's status. No unresolved runtime finding
remains. Master visually inspected actual production-asset light desktop
configured and dark phone disconnected captures, with empty credential fields.
These isolated no-API browser captures do not establish installed-dashboard
integration, live authentication or milestone completion.

Final frontend verification passed: schema drift/TypeScript/production build,
102 deterministic unit/component tests and 15 separate installed-Edge browser
checks. Browser trace/video/automatic screenshots are explicitly disabled;
manual captures happen only after boolean empty-field checks. Test credentials
are generated at runtime, with credential-sensitive failure diagnostics limited
to booleans/counts. A pre-existing installed M6 packaging probe first failed on
Matplotlib's font-cache warning (emitted after five seconds of fresh font
enumeration); the unchanged isolated test passed on rerun. No probe assertion,
cache isolation, Python source or dependency was changed to obtain that result.

Canonical Python 3.12.14 final verification: targeted hosting/packaging/hygiene
42 passed; full pytest 2794 passed; Ruff, configured mypy (config.py) and pip
check passed. Existing pinned Node 24.19.0/npm 10.8.2 and Python environments
were reused without dependency changes. Windows native browser/process checks
required approved sandbox escalation. Final staged hygiene, exact-head hosted
CI and owner merge remain separate gates before successor implementation.

## Continuation — 2026-10-15

The owner instructed **“prs merged, continue the work”**. Independently verified
PR #151 merge `1d0328c326561c7db30dfcc2bf241d0df060773a` contains reviewed
client head `63cb4d624ae9a8f35ef4ec6813b0fed5edfa3753`; PR #150 merge
`a2de2695f25b6d4c47c07af3ac91b9f1f4efac1b` contains reviewed hosting head
`d2f396b832e8c5fb662b10e4e87f33142d86ea47` and the client merge. Post-merge
main Foundation `38735781899` and `38735810019` passed all five jobs. Required
issues #142/#143 are closed through owner merges, with their actual visual
demos delivered in chat. There is no agent merge or scope expansion.

Issue #144 is now delegated to `frontend_plan` on
`codex/144-shell-themes`, based on combined main `a2de2695`. It owns the shared
typed navigation/layout, reusable presentation primitives, original pixel
typography, semantic monochrome tokens, accessible persistent local theme and
component guide. It does not fetch data or add credential entry, new metrics or
backend functionality. The synthetic #143 demonstration remains a separate
utility route. Main navigation retains Overview/Watchlists/Settings and the
approved unavailable future panels/search explanation.

#152 extracts memory-only connection controls from #147 to remove a dependency
cycle: #145 needs a connection, while #147 needs #145's saved-entry counts.
#152 waits for #144's owner merge and main CI; #145 then waits for #152.
#147 reuses the existing theme/connection lifecycle and adds supported overview
counts/status only after #145. #146 waits for watchlists; #148 audits the
completed integrated dashboard. This changes issue ordering, not approved
product or API scope. A real browser demonstration is required for each issue.
The dated execution snapshots below are retained as traceability history.

### #144 implementation and review

Shared frontend shell supplies three typed primary routes, one main/heading,
keyboard skip/route focus and browser history; local light/dark theme persistence
with blocked-storage and cross-tab area handling; reusable semantic primitives
and `frontend/COMPONENTS.md`. All actual text uses the original local pixel font.
The approved unavailable panels and search disclosure are preserved. No API
request, token entry, backend/CI/dependency change or financial metric is added.

Independent `m8_analysis` reviewed the final source, guide and browser checks
with no unresolved finding. Master review corrected storage-area isolation,
theme action-button semantics and a visible horizontal-scroll hint. Actual
production-asset Edge captures at 1440/768/390 pixels in both themes were made;
Master visually inspected the light desktop and dark phone captures. This
isolated no-API fixture is not the final packaged dashboard integration.

Local verification: pinned offline npm ci (99 packages, audit zero), schema
drift/type/production build, 84 frontend tests and 11 installed-Edge browser
checks passed. Python 3.12.14 canonical environment: targeted hosting/packaging/
hygiene 42 passed; full pytest 2794 passed; Ruff, configured mypy (config.py)
and pip check passed. Windows native browser/async process checks required the
approved sandbox escalation; no application/provider network was used.
Exact-head hosted checks and owner merge remain separate gates.

## Acceptance update — 2026-10-14

The owner's **“approved continue work”** accepts revised ADR-0014 Option A and
the scoped M8 requirements/design. Owner merge of PR #149 is independently
verified at `dd7e9d52cb596f608bdb70c534407ae60d461be2`, containing reviewed head
`edeced0fe1d63ff3cf4a758b1f8e1d0ee72fe673`. Exact-head Foundation `38690737794`
passed all five checks. Post-merge main Foundation `38691698230` also passed
all five checks; runtime #142/#143 are unblocked. The Master
owns this acceptance record; delegated `m8_analysis` is implementing #142 on
`codex/142-local-dashboard-hosting`. Independent #143 is assigned to delegated
`frontend_plan` on `codex/143-frontend-api-client` in managed worktree
`m8-api-client`, based on the same owner-merged contract. It owns only frontend
scaffold/client contracts and a labeled synthetic client demo; it does not alter
#142's API/runtime graph. Other implementation issues retain their
predecessor gates. The earlier proposal snapshots below are review history.

Approved design: original local pixel font for all actual text, same monochrome
light/dark themes, two unavailable layout panels and an explanatory search/add
entry point linked to the backend/frontend checklist. No write, research/AI or
live-provider activation is implied. No agent merge is authorized.

Planning started 2026-10-14 at main `26a44a7c9fcf3131d5ed56dcacc63420d192b0a9`.
The user selected M8 and requested a visual frontend demo for each completed
issue. The role document's M2/template placeholders do not select scope.
Following review of PR #149, the owner requested retro pixel text and UI while
preserving the established theme. The preview and ADR now specify pixel display
headings, readable monospace data, square controls and hard shadows within the
same monochrome light/dark tokens. No runtime feature or financial rule changes.

SRS §23.8 is proposed and D3 unresolved. [ADR-0014](../adr/0014-local-read-only-dashboard.md)
provides a concrete acceptance choice. No runtime implementation is authorized
until its owner acceptance/merge and main CI gates pass. The existing M7 API
supports saved watchlist reads and stored-row raw history, refuses every Origin,
and has no mutations or fetched portfolio summary service.

Parent: [M8 milestone 9](https://github.com/daniilnahl/Stock-Tracking-App/milestone/9).

| Objective | Dependencies | Status |
|---|---|---|
| [#141](https://github.com/daniilnahl/Stock-Tracking-App/issues/141) Technology/browser/capability contract | Owner merge and main CI verified | Closed completed; PR #149 merged |
| [#142](https://github.com/daniilnahl/Stock-Tracking-App/issues/142) Opt-in static hosting/browser boundary | Accepted contract | Closed completed; owner merged PR #150; main CI passed |
| [#143](https://github.com/daniilnahl/Stock-Tracking-App/issues/143) Frontend scaffold/precise typed client | Accepted contract | Closed completed; owner merged PR #151; main CI passed |
| [#144](https://github.com/daniilnahl/Stock-Tracking-App/issues/144) Shared shell/themes/component guide | Scaffold/client merged, main CI passed | Closed completed; owner merged PR #153; main CI passed |
| [#152](https://github.com/daniilnahl/Stock-Tracking-App/issues/152) Memory-only local API connection controls | Hosting, client, shell merged; main CI passed | Closed completed; owner merged PR #154; main CI passed |
| [#145](https://github.com/daniilnahl/Stock-Tracking-App/issues/145) Both saved watchlists | Hosting, client, shell, connection #152 merged; main CI passed | Closed completed; owner merged PR #156; main CI passed |
| [#146](https://github.com/daniilnahl/Stock-Tracking-App/issues/146) Exact stored-row detail/raw history | Watchlists merged; main CI passed | In progress; frontend_plan; codex/146-stored-row-history |
| [#147](https://github.com/daniilnahl/Stock-Tracking-App/issues/147) Supported overview/settings | Watchlists and shell merged; main CI passed | In progress; m8_analysis; codex/147-supported-overview |
| [#155](https://github.com/daniilnahl/Stock-Tracking-App/issues/155) Package dashboard assets and actual local-launcher integration | Completed views #145/#146/#147 | Blocked; required bridge before exit audit |
| [#148](https://github.com/daniilnahl/Stock-Tracking-App/issues/148) Independent browser/distribution exit audit | All implementations merged | Blocked |

Assignment/review: #141 is owned by the Master for proposal and independently
reviewed by delegated `m8_analysis`; no blocking finding remains after selection
invalidation clarification. PR #149 is owner-merged. At the original proposal snapshot #142–148 were unassigned,
have no implementation PR or review, and are blocked by the acceptance and
predecessor gates in the table. No issue is claimed complete.

One issue/branch/implementation agent/PR per objective. Hosting and client may
proceed independently only after approval of their stable contract. The Master
owns planning and independent review; delegated implementation must read
AGENTS.md and relevant SRS/ADRs/tests/callers. No agent merges.

## Demo and verification contract

Every completed implementation issue includes an actual browser demonstration
of its changed frontend behavior, with screenshots or a viewable local demo.
Use explicit isolated synthetic data and conspicuous labeling; no real holdings,
provider credentials, local API token or private paths in captures. State which
behaviors are exercised and which remain unsupported. The contract issue uses
an [illustrative design preview](../previews/m8-dashboard.html), clearly separate
from implementation or live data. Do not call an issue complete before its
acceptance criteria and required checks pass.

Follow docs/TESTING.md: canonical Python install, targeted tests, full pytest,
Ruff, configured mypy and pip check. After approval, add frontend type/build,
unit/component/schema and separately invoked browser checks. Audit lossless
volume/Decimal handling, both namespaces/duplicates, unknown provenance,
authentication/Origin/static traversal, disconnection/cancellation, actual
history disabled/error/success states, theme persistence and accessibility.

## Initial analysis and limitations

Independent delegated read-only analysis confirmed the capability and browser
access gaps. No financial logic, persistence, API runtime or dependency changed.
The GitHub connector cannot create milestones and rejected issue writes with
403; existing authenticated Git credentials provide the authorized GitHub REST
fallback without printing credentials. Browser tool initialization timed out.
The available `python`/`py` runtime reports Python 3.14 only, outside the approved
3.11/3.12 range. Do not run canonical checks under an unsupported runtime or
change the supported version. Record unavailable verification until a supported
environment is available. This documentation proposal is not M8 completion.

Actual proposal checks: preview JavaScript parsed successfully with Node;
preview disclosure/accessibility-marker checks passed; independent read-only
proposal review passed after the two traceability/selection clarifications.
Canonical pytest/Ruff/mypy/pip check and actual browser/theme rendering were
not verified: supported Python was unavailable and browser initialization timed
out. No check is claimed from those unavailable tools. Full runtime verification
and screenshot demonstrations remain required for implementation issues.

Retro design revision checks: Node controlled-DOM execution verified original
vector glyph output for every heading, preserved accessible text, decorative
glyph hiding and both theme-toggle states. `git diff --check` passed. This
verifies script behavior only; browser rendering, contrast and responsive
accessibility are not certified by the controlled DOM. No Playwright package
is installed in this checkout; no dependency was added for this preview.
Independent static review confirmed palette/scope/accessibility-text retention
and identified the preview's SVG lettering as an images-of-text concern for
production. ADR now requires actual text with a local pixel font in production;
this illustrative rendering does not certify WCAG AA.

## All-text pixel and placeholder revision

The owner requested pixel styling for **all** text, an obvious stock search/add
entry point plus a backend/frontend gap checklist, and two rectangles above
the three status cards titled “Recommend stock of the day” and “Taurus Agents
Menu”. The preview now uses the local original Stock Pixel TrueType font for
all real HTML text, including tables, body copy and controls; the earlier SVG
heading renderer is removed. Original glyph source, a deterministic Node-only
generator and license notes accompany the required font asset. Existing
monochrome light/dark theme tokens remain unchanged.

Both requested panels are visibly unavailable placeholders. Search / add stock
only toggles an explanation and a link to [TO-DO LIST](../TO-DO-LIST.md). The
checklist identifies actual existing CLI/shared-service behavior, missing HTTP
lookup/mutation support, backend approval/contracts/concurrency/security/tests
and frontend request/commit/error states. No backend or future agent/research
functionality is implemented or implied.

Current verification supersedes the earlier SVG checks: Node controlled-DOM
checks pass for theme toggles and search disclosure expand/collapse; static
checks verify every preview text character has a pixel glyph, the global font,
both exact titles/order/unavailable labels and local links. Font rebuild hashes
match; TrueType cmap/table/checksum checks pass; Windows private-font loading
recognizes Stock Pixel without installation. An isolated headless Edge desktop
capture at 1440×1900 was visually inspected and confirms the local pixel font,
panel order and visible search/add control. No real data or credentials were
used. Independent static review found no blocker after clarifying uncertain
post-commit outcomes. Canonical Python checks remain unavailable as previously
recorded; no production functionality or full accessibility audit is claimed.

A second isolated Edge test copy programmatically activated dark mode and
expanded search/add. Its capture with content constrained to 390px was visually
inspected: navigation/text/panels wrap and status cards stack; the data table
retains its intentional horizontal scroll region. Edge's minimum headless window
width exceeded the requested 390px, so the check used a 500px capture with an
explicit 390px body rather than claiming true mobile-device emulation. Test
copies/profiles/captures remain outside the repository. Actual browser rendering
is now verified for these bounded previews, superseding the earlier timeout;
full browser E2E, screen-reader/contrast auditing and canonical Python checks
remain outside this revision's verification.

## PR #149 CI repair — binary credential scanning

Foundation run `38689231682` failed Credential patterns and both Python jobs
at the same `UnicodeDecodeError`: the scanner decoded the newly tracked
`stock-pixel.ttf` as strict UTF-8. Both Python runs otherwise passed 2725 cases
with 35 platform-specific skips; Ruff/configured mypy passed.

The repair scans staged blob contents using loss-preserving `surrogateescape`,
retaining strict decoding for other Git output. Binary assets are not skipped;
ASCII credential patterns still match. An isolated staged-binary regression
covers clean bytes, synthetic assignment/URL findings and an unstaged cleanup
that cannot conceal staged findings. No workflow, dependencies, font, preview,
application runtime or financial behavior changes. Independent review passed.

The bundled runtime discovery supplied Python 3.12.14, superseding the earlier
local-runtime limitation. A worktree `.venv` uses the canonical pinned
`pip install ".[dev]"`. Initial sandbox TEMP/DNS restrictions were resolved by
an ignored worktree TEMP and approved network installation; no system software
or supported-version change. One unittest attempt without the worktree TEMP
failed on sandbox temporary-directory permissions; no assertion was weakened.

Actual canonical verification: `python -m pytest tests/test_repository_hygiene.py
-v` **9 passed in 12.72s**; full `python -m pytest` **2762 passed in 111.52s**;
Ruff passed; configured mypy passed (one source file, `config.py`); `pip check`
passed. Full tests used approved native temporary hard-link access and isolated
test state, no live credentials/provider or real user database. Final hosted CI
must pass on the pushed repair; no milestone/issue completion is inferred.

## Local hosting implementation — issue #142

The accepted contract now has an opt-in `--dashboard` launcher/configuration
path. Exact packaged static GET routes serve a clearly labeled pixel-styled
hosting foundation using external local CSS/script/font/license. Matching local
Origin/Host pairs are accepted only in opt-in mode; API authentication, safe
failures and the default M7 access/schema contracts remain intact. Rejected
paths/methods/query/body/origins cannot acquire assets or application state.
Restrictive CSP, no-referrer, nosniff and framing denial apply in dashboard mode.
No current/historical data requests, credential entry or persistent preference
exist on this foundation page; those remain subsequent frontend issues.

Independent Master review checked the actual source, tests, callers, fixed
package-data list, source/installed-wheel resource serving and cold no-IO probes.
Manual real-launcher verification used four isolated temporary paths and an
unprinted synthetic token: root/assets returned successfully; matching Origin
passed, foreign Origin failed, unauthenticated API failed, encoded asset aliases
failed and no holdings/cache/legacy state was created. Headless Edge rendered
the actual loopback-served page with the local pixel font; the screenshot is a
chat artifact, not a committed diagnostic file. Demo process was stopped.

Python 3.12.14 targeted dashboard/foundation/launcher/packaging verification:
**186 passed in 39.63s**. Full canonical pytest: **2794 passed in 121.32s**.
Ruff/configured mypy (`config.py` only)/pip check/diff check passed. Native Windows
control-socket and hard-link execution required approved sandbox escalation;
application network guards remained active. The first wheel probe correctly
emitted safe rejection logs; the final probe captures and asserts exact safe
category messages rather than suppressing failures. No unresolved review
finding, dependency addition or CLI/financial/persistence behavior change.

Implementation PR publication/hosted CI/owner merge remain separate gates.
The live readiness demo verifies #142 hosting only, not M8 completion.
