# M8 — Web Dashboard execution plan

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
| [#141](https://github.com/daniilnahl/Stock-Tracking-App/issues/141) Technology/browser/capability contract | M7 implementation merged | Proposal in this PR; owner decision pending |
| [#142](https://github.com/daniilnahl/Stock-Tracking-App/issues/142) Opt-in static hosting/browser boundary | Accepted contract | Blocked |
| [#143](https://github.com/daniilnahl/Stock-Tracking-App/issues/143) Frontend scaffold/precise typed client | Accepted contract | Blocked |
| [#144](https://github.com/daniilnahl/Stock-Tracking-App/issues/144) Shared shell/themes/component guide | Scaffold/client | Blocked |
| [#145](https://github.com/daniilnahl/Stock-Tracking-App/issues/145) Both saved watchlists | Hosting, client, shell | Blocked |
| [#146](https://github.com/daniilnahl/Stock-Tracking-App/issues/146) Exact stored-row detail/raw history | Watchlists | Blocked |
| [#147](https://github.com/daniilnahl/Stock-Tracking-App/issues/147) Supported overview/settings | Watchlists, shell | Blocked |
| [#148](https://github.com/daniilnahl/Stock-Tracking-App/issues/148) Independent browser/distribution exit audit | All implementations merged | Blocked |

Assignment/review: #141 is owned by the Master for proposal and independently
reviewed by delegated `m8_analysis`; no blocking finding remains after selection
invalidation clarification. Its PR is pending publication. #142–148 are unassigned,
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
