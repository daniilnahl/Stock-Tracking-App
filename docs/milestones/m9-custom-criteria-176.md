# Custom stock criteria editor — issue #176

**Current delivery — 2026-10-18:** this is a dated task/research record. The accepted criteria editor and EPS adapter/service/configuration/API/opt-in launcher/dashboard are now merged, and the independent audit is merged with passing main CI. Earlier pending/no-API/no-UI statements apply to their original scope or unapproved extensions. Provider research remains dated; no new entitlement, metric or live call is inferred. See [current implementation status](../CURRENT_STATUS.md).

Owner-merged #175 accepts M9 criteria/M10 Taurus discovery ownership. Asked
which parameters to support, the owner explicitly chose arbitrary customized
parameters and range values. [Issue #176](https://github.com/daniilnahl/Stock-Tracking-App/issues/176)
implements accepted [ADR-0018](../adr/0018-custom-criteria-editor.md)'s first
editor. It prepares descriptive user intent without source-metric evaluation,
backend/API/provider/agent calls or durable saving.

## Plan and ownership

1. Master records the custom-data contract; independent `m9_analysis` reviews.
2. `eps_impl` implements the typed validator, accessible Stock criteria page,
   app-owned tab-memory draft/snapshot and meaningful tests on
   `codex/custom-stock-criteria`, from main
   `cd9f496191b6ae39bd3da0284690647d2d2224e2`.
3. Deliberately rebuild packaged dashboard assets, then run frontend unit/type/
   build/package/browser and actual source/wheel integration profiles. Master
   runs canonical Python checks sequentially and independently reviews the diff.
4. Publish an issue-linked PR with exact-head CI; owner merge remains separate.
   No agent merge, Taurus execution or full M9 completion.

The editor allows custom parameter names, exact inclusive signed decimal ranges
with explicit user units/context, or text requirements, and explicit all/any.
Preparing freezes a data-only snapshot; edits mark it outdated. Tab navigation
preserves state, while pagehide/reload and explicit clearing reset it. No hidden
investment preset, USD assumption, forecast arithmetic or verified-match claim.

## Environment and verification

Baseline merged-main Foundation 39081793870 passed. Installed system Node is 20;
the existing bundled Node 24.19.0 meets the approved frontend runtime. Use it with
existing npm 10.8.2; canonical lockfile `npm ci --no-audit --no-fund` installed 99
packages in 30s without dependency/lockfile changes. Installed Edge is available
for headless Playwright via the existing PLAYWRIGHT_CHANNEL option; no browser
or system software is installed/altered. Python remains pinned 3.12.14.

Independent contract and final implementation review passed with no actionable
findings. The Master inspected the light desktop and dark 320px screenshots;
custom values wrap without horizontal page overflow. Validation styles are scoped
to this editor, and the page explicitly states that reload clears its contents.

| Command actually executed | Result |
| --- | --- |
| `npm test` | 217 passed in 9.35s. |
| `npm run package:dashboard` and `npm run package:check` | Schema, type, build and byte-exact package checks passed in 6.14s. |
| `npm run test:browser` with installed Edge | 29 passed in 28.6s. |
| `npm run test:integration` with installed Edge | Actual source/wheel: 2 passed in 23.5s. |
| `python -m pytest tests/test_dashboard_hosting.py tests/test_repository_hygiene.py -q --tb=short` | Focused hosting/hygiene: 41 passed in 18.40s; latest assets also covered by the final full suite. |
| `python -m pytest -q --tb=short` | 3077 passed in 170.53s. |
| `python -m ruff check .` | Passed. |
| `python -m mypy` | Passed; configured `config.py` only. |
| `python -m pip check` | No broken requirements. |
| Relative Markdown target check and `git diff --check HEAD` | Passed. |

An initial sandbox-only native junction test failure passed on approved native Windows
execution with task-local TEMP/TMP; no test or dependency was weakened.
No actual credential, holdings or model/provider request is part of this task.
Final staged hygiene passed: 9 tests in 14.91s. PR #177 exact-head Foundation
39083264222 passed all five jobs; the owner merged it at
`d17c9df61d5ffb491d264c599a5dfdfe259c4e4f`, followed by successful main Foundation
39083592809. Independent review and Master review passed. This is not whole-M9
completion; remaining contracts retain their separate gates.
