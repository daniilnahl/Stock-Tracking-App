# Independent M8 exit audit — issue #148

This is the historical M8 audit reproduction guide. Current scope as of
2026-10-18 also includes the shipped criteria editor and manual upcoming EPS,
with separate contracts/evidence in the
[accepted M9 scope audit](../docs/milestones/m9-exit-audit-184.md). Original M8
results do not establish coverage of those later features.

Run the canonical pinned setup from README.md. Use an isolated Python3.12
environment with `pip install ".[dev]"`; no additional tool/dependency is needed.
The heavy profiles below must run sequentially, using installed Edge and an
unoccupied loopback8000. No user listener is stopped.

```text
npm run build
npm run package:check
npm test
npm run test:browser
npm run test:integration
```

Set `PLAYWRIGHT_CHANNEL=msedge` and `STOCK_TRACKER_TEST_PYTHON` to the audit venv
Python for integration. Set task-local TEMP/TMP where native Windows permissions
require it. Run canonical full Python pytest, Ruff, configured mypy and pip check
in that same fresh environment; default pytest never requires browser/Node.

`integration/exit-audit.ts` extends the existing real source/installed-wheel
launcher workflow, without API interception or duplicated server setup. It adds
eight normal viewport/theme combinations (1440/820/390/320px), keyboard navigation/focus/skip/scroll,
local font checks, Overview user text spacing plus200% root text, Watchlists
access at200% text, forced-colors/reduced-motion and real reload/401 clearing.
It found header wrapping and320px native-select grid sizing defects; the two
narrow CSS declarations keep the regressions strict without hiding overflow.
Only the original fixed five packaged assets ship. Regenerate deliberately with
`npm run package:dashboard` after source UI changes, then review byte drift.

Explicit wheel captures are labeled synthetic/no-live-data/rights-not-activated,
contain no password controls or process token in DOM, and stay under ignored
`test-results/integration`. Automatic trace/video/screenshot/ARIA diagnostics are
disabled by the existing integration profile. Source/wheel database hashes stay
unchanged and history/EPS acquisition remain disabled. The current integration
profile also covers criteria without an API connection and the real EPS form's
disabled response. Controlled chart/EPS success is verified by synthetic fixture
tests rather than live provider activation.

The complete requirement matrix, recorded command results, findings and delivery
evidence are in [M8 evidence](../docs/milestones/m8-exit-evidence.md). Media
emulation/CSSOM are bounded checks, not full screen-reader, native zoom or cross-
browser accessibility certification. The original #148 audit deliberately left
the root README unchanged; subsequent documentation reconciliation is separate.
