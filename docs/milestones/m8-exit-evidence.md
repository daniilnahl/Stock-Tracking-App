# M8 independent exit audit — issue #148

**Current delivery — 2026-10-18:** audit #148 and README follow-up are owner-merged (#162/#163); all M8 issues are closed. The in-progress notices and three-route matrix below are dated M8 evidence. The current dashboard has five routes after M9 criteria/EPS delivery. M8's administrative milestone remains open. See [current status](../CURRENT_STATUS.md).

## Status and accepted scope

Audit in progress on `codex/148-m8-exit-audit`, based on owner-merged #155 / PR159
at `4474c44322a58c7d8fa98e7c63e8f044030127ef`. The Master independently verified
post-merge main Foundation38944336927 passed all five jobs. ADR-0014 accepts the
local read-only dashboard and original all-text pixel design; ADR-0013's historical
rights gate remains closed. This document does **not** declare M8 complete.
Audit PR publication, exact-head required CI, independent review, owner merge,
post-merge main CI and final issue/milestone closure remain separate gates.

The audit engineer previously reviewed but did not implement the feature PRs.
The Master assigned another reviewer to examine this audit's tests and evidence.
No new backend contract, dependency, CI workflow, metric or provider activation.

## Requirement and evidence matrix

| Accepted requirements | Evidence and limits |
|---|---|
| UI801–804 | Pinned React/TypeScript/Vite; typed three-route inventory, App-owned session, reusable primitives. Unit shell/route tests and actual source/wheel keyboard navigation, h1 focus and skip link retaining hash. |
| UI805–809 | Shared semantic monochrome tokens and local Stock Pixel font. Existing browser computed contrast, tabular/units/exact text and theme persistence tests; actual installed source/wheel light/dark at1440/820/390/320, named scrollable saved table, keyboard scrolling. No supported sorting/filtering operation is invented. |
| UI810–811 | Actual launcher→M7→shared services→temporary SQLite reads in both namespaces; counts include duplicates only in loaded successful namespace. Existing state/client tests cover loading/empty/failure/offline/cancel/unsupported/401 and no stale fallback. |
| UI812–814 | Independent actual-launcher viewport/theme matrix, keyboard focus/scrolling, Overview user text spacing with 200% root text, Watchlists200% text access, forced-colors focus/shadow and reduced-motion checks. Existing browser phone/detail overflow and reduced-motion regressions remain required. Bounds and manual exclusions below. |
| UI815 | Original local font source/license; bundled project/font, React, ReactDOM, scheduler and emitted Vite-helper core MIT notices. Exact asset and license source/wheel tests. No copied reference art. |
| UI816–818 / X718 | Central validated lossless API client; App-owned memory-only token/session; theme-only persistence. Existing coalescing/generation/cancel and controlled401 tests prove clearing already-loaded private views. Actual real-server401 rejects a fresh wrong-token session with empty private views; loaded-page reload and explicit disconnect clear loaded counts/token without automatic API reads. |
| UI819–821 | Supported current-namespace entry count and saved observations/detail with unknown freshness/currency; request-local fresh row selection. Controlled existing history tests preserve sparse dates, exact OHLC/bigint and approximate finite chart-only projection. Actual launcher only exercises disabled history503; no rights activation or live entitlement claim. |
| UI822–823 | Analytics route omitted; exact two future panels explicitly unavailable. Search/add explains unsupported operation and fixed TO-DO LIST link; no mutation or research/agent requests. |
| UI824 | React text rendering, fixed safe errors, no arbitrary redirects/URLs; hostile-string/client/browser tests. Real integration checks no external requests, private token in DOM/assets/logs, password-free labeled captures and theme-only storage. |
| UI825 | COMPONENTS.md documents all nine primitives; this audit corrects stale Overview table/count wording to match #147. |
| UI826–828 | Existing unit/schema/build, separate fixture browser and actual source/wheel profiles; deliberate fixed five-file distribution and byte check. Default API-only cold import/help needs no Node/build/asset reads. Custom themes/cloud sync remain deferred. |
| UI829 | This independent audit and evidence, with independent review and owner/CI closure gates still pending. No illustrative preview substitutes for installed operation. |

## Reproduced findings and bounded corrections

The new actual-launcher audit failed at820px with 200% text plus prescribed
spacing: the header's NAV/link/theme button overflowed the viewport. The failure
reported element tag/class shapes only, without private text or credentials.
Adding `flex-wrap: wrap` to the existing header fixes its single-row constraint.
The regression remains strict. Assets were regenerated through the existing
deliberate package bridge; no CSP/security or design token changed. Source and
installed-wheel checks passed after the correction. Normal desktop/tablet/phone
light/dark checks also remain required. No unrelated redesign was introduced.

Adding the320 CSSpx cases independently exposed the namespace SettingsField grid
allowing its native select's intrinsic width to expand the label/select/hint past
the viewport. An explicit `grid-template-columns: minmax(0, 1fr)` keeps that track
within its parent without hiding overflow or changing the control's semantics.
Both normal theme/viewport and text-override regressions remain strict. This is
the audit's only other production change; generated CSS is updated deliberately.

One post-grid-fix43-case hosting/packaging/hygiene run had42 passes and one
pre-existing installed M6 probe failure: Matplotlib emitted its cold-font-cache
warning into stderr, violating the probe's strict empty-output assertion.
The installed `font_manager.py` schedules this warning after5s; the probe uses
an isolated fresh MPLCONFIGDIR. Asset byte checks and dashboard/API/cold probes
already passed before that later M6 assertion. No code, timer, cache, logging or
assertion was changed to conceal it. The unchanged affected-case retry and
subsequent verification outcomes are recorded below. The unchanged affected case
passed1 in52.42s, then the unchanged related43 cases passed in71.05s.

## Reproduction and environment

An isolated ignored `frontend/.cache/m8-audit-venv` uses the already installed
Python3.12.14 and canonical `python -m pip install ".[dev]"` with existing exact
pins. No system software or alternative package manager. Initial sandbox venv
ensurepip failed; the unchanged command succeeded with task-local TEMP/TMP and
approved native execution. Native Windows control sockets/hard links and Edge
require approved execution; application/provider guards remain active.

Existing Node24.19.0/npm10.8.2 and installed Edge run the pinned frontend tooling.
Set TEMP/TMP to the task's `.venv/tmp`, `PLAYWRIGHT_CHANNEL=msedge`, and
`STOCK_TRACKER_TEST_PYTHON` to the fresh environment's Python before integration.
Heavy suites run sequentially. See the [audit guide](../../frontend/AUDIT.md).

## Verification — 2026-10-16

These commands ran in the fresh audit environment; prior implementation results
in other documents are not substituted for this audit's runs.

| Command | Result |
|---|---|
| `python -m pytest tests/test_dashboard_hosting.py tests/test_api_foundation.py tests/test_api_boundary.py tests/test_api_launcher.py tests/test_api_serialization.py tests/test_api_watchlists.py tests/test_api_history.py tests/test_packaging.py tests/test_repository_hygiene.py -q` |297 passed in84.96s. |
| `python -m pytest -q` |2795 passed in159.73s after header correction; before final CSS-only grid correction. |
| `python -m pytest tests/test_dashboard_hosting.py tests/test_packaging.py tests/test_repository_hygiene.py -q` |Final-grid source/wheel/cold/security coverage43 passed in71.05s, after the unchanged cold-font-warning retry described above. |
| `python -m ruff check .` |Passed. |
| `python -m mypy` |Passed; configured scope remains one source file, config.py. |
| `python -m pip check` |No broken requirements. |
| `npm run build` |Schema drift, TypeScript and production Vite build passed after both narrow fixes. |
| `npm run package:check` |Final five-resource byte check passed after320px correction. |
| `npm test` |Final164 deterministic tests passed in7.69s. |
| `npm run test:browser` |Final27 separate Edge fixture checks passed in25.4s, including precise successful-history/cancellation/contrast regressions. |
| `npm run test:integration` |Final2 real source/wheel workflows passed in23.0s; each covers eight viewport/theme combinations plus overrides, rights-disabled history, reload, real401 refusal and loaded-state disconnect. |
| `git diff --check` |Passed; staged hygiene and remote checks remain Master-owned gates. |

The final artifact-only label adjustment also passed TypeScript. No additional
production changes followed the final grid build. All heavy runs were serial.
Staged hygiene and exact-head hosted CI remain Master-owned later gates.

## Demonstration and limitations

The actual installed-wheel launcher produces labeled synthetic overview demos
at1440/820/390/320 in both themes. A temporary SQLite database preserves exact ordered
duplicates, unowned/owned-zero and precise decimals. API routes are not mocked;
history stays disabled and no provider is acquired. Database hash remains fixed;
history cache and legacy paths remain absent. Each capture checks no password
field and no process token in DOM. Traces, videos, automatic screenshots and
automatic failure ARIA snapshots remain disabled; no real credential/user data.

The final light1440, dark320 and820px200%-text installed-wheel images were
visually inspected. They show one conspicuous disclosure, real selectable pixel
text, preserved placeholder/card structure and wrapped keyboard-accessible header.
The viewport-only200% image moves only the test disclosure above the header after
strict assertions; it labels CSS text sizing distinctly from native browser zoom.
All final images are in ignored `.venv/issue148-demos/` for Master preservation;
no generated screenshot or runtime state is committed.

CSSOM property changes emulate user text overrides under the **unchanged CSP**.
Spacing (line1.5, letter.12em, word.16em, paragraph2em) is tested on current Overview
nodes; root text is200% and remains enlarged when navigating to Watchlists. This
does not claim native browser toolbar zoom, every text length or assistive tool.
Forced colors/reduced motion use Edge media emulation. Tests verify semantic names,
status/focus/contrast behavior; no full manual screen-reader certification was
performed. Firefox/Safari, OS-specific native high-contrast settings and actual
browser zoom remain unverified. These limits do not authorize hiding failing tests
or claiming universal WCAG conformance. Live historical rights, hosted operation,
mutations/research/AI/new metrics remain outside accepted M8 scope.
