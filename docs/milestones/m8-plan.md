# M8 — Web Dashboard execution plan

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
| [#144](https://github.com/daniilnahl/Stock-Tracking-App/issues/144) Shared shell/themes/component guide | Scaffold/client merged, main CI passed | Implementation/review; frontend_plan; codex/144-shell-themes |
| [#152](https://github.com/daniilnahl/Stock-Tracking-App/issues/152) Memory-only local API connection controls | Hosting, client, shell | Blocked by #144 owner merge/main CI; extracted from #147 |
| [#145](https://github.com/daniilnahl/Stock-Tracking-App/issues/145) Both saved watchlists | Hosting, client, shell, connection #152 | Blocked |
| [#146](https://github.com/daniilnahl/Stock-Tracking-App/issues/146) Exact stored-row detail/raw history | Watchlists | Blocked |
| [#147](https://github.com/daniilnahl/Stock-Tracking-App/issues/147) Supported overview/settings | Watchlists, shell | Blocked |
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
