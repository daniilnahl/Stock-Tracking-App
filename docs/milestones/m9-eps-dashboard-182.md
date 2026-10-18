# Manual upcoming-EPS dashboard — issue #182

The owner merged #181 at `3af4db73d734453737e956819ef232c4c9197fdd`;
post-merge Foundation 39097470838 passed. After the dashboard form was identified
as next, the owner instructed continuation. [ADR-0016](../adr/0016-upcoming-eps-api.md)
stage 3 accepts [#182](https://github.com/daniilnahl/Stock-Tracking-App/issues/182)'s
bounded UI using the existing API, session and approved pixel/monochrome design.

## Plan and ownership

1. Master records the narrow form/input/lifecycle/display contract.
2. `eps_impl` implements primary navigation/Overview entry, manual form/client/
   strict validation, accessible exact sourced display and tests, then rebuilds
   the same five packaged assets.
3. `m9_analysis` independently reviews contract and final source/tests/docs.
4. Run unit/type/build/package/browser and actual source/wheel integration
   sequentially; Master runs canonical Python/static/dependency/hygiene checks,
   reviews the final diff and publishes an issue-linked PR with exact-head CI.
5. Owner merge remains separate. No agent merge or full-M9 completion claim.

## Scope

The form starts with blank explicit Finnhub symbol and inclusive start/end dates.
Local validation enforces exact syntax/real dates/max92 included dates; the
server owns its UTC future cutoff. Only manual action calls the authenticated
local EPS route. No provider key field, direct vendor fetch, inferred stock/date
window, polling, retry, criteria evaluation, storage or backend change.

Decode the generated contract and verify exact request association, real date/
receipt syntax, ordered unique fiscal periods, max128 rows and fixed provenance/
unknown metadata. Preserve exact signed string values, zero and null. Show raw
non-GAAP currency-per-share observations with explicit unknown currency/share
basis/publication/fiscal-period end, vendor release labels and UTC receipt;
coverage stays not_asserted. No financial comparison or forecast-vintage claim.

Editing/clear/cancel/supersession/route departure invalidate earlier data and
prevent late publication. Route departure clears this form's draft/results;
custom-criteria app-memory retention remains unchanged. Existing session-wide
401/disconnect/page lifecycle clears remain authoritative. No frontend or
automated test reads a real key or makes another live provider call; the prior
single-symbol native smoke remains dated technical-access evidence only.

## Verification

Using the existing bundled Node 24 helper, isolated TEMP/TMP and blank provider
key environment variables:

| Command | Result |
| --- | --- |
| Frontend `npm test` | 273 passed, 7.37s; 56 new EPS cases |
| `npm run package:dashboard` then `npm run package:check` | Schema/type/build and packaged bytes passed, 5.30s |
| `npm run test:browser` with installed Edge | 31 passed, 27.6s |
| `npm run test:integration` | Actual source/wheel 2 passed, 23.4s |
| `python -m pytest -q --tb=short` | 3178 passed, 139.09s |
| `python -m ruff check .` | Passed |
| `python -m mypy` | Passed, configured `config.py` boundary |
| `python -m pip check` | Passed |
| Final staged `pytest tests/test_repository_hygiene.py -q` | 9 passed, 14.41s |
| Staged relative Markdown links / `git diff --cached --check` | Passed |

The first integration run exposed a diagnostic expectation missing the new
`eps_disabled` category. Added only that literal to the existing anchored
allowlist and reran both profiles successfully. No logging restriction was
removed. Real local default-disabled UI requests use no API mocks/provider keys.

Master inspected synthetic light 1440px and dark 320px screenshots: readable
manual controls, exact values/unknown metadata and contained horizontal table
scrolling. Screenshots stay ignored. `m9_analysis` independently passed final
source/unit/docs/browser/integration review with no actionable findings.

Exact-head CI is pending at publication. Owner merge remains
separate; this form does not complete broader M9.
