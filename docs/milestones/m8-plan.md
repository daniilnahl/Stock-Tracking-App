# M8 — Web Dashboard execution plan

Planning started 2026-10-14 at main `26a44a7c9fcf3131d5ed56dcacc63420d192b0a9`.
The user selected M8 and requested a visual frontend demo for each completed
issue. The role document's M2/template placeholders do not select scope.

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
