# Opt-in EPS launcher and budget — issue #180

The owner merged #179 at `e7f4647f393f423f8ac3243c804ae82ed25e9cec`;
post-merge Foundation 39094106222 passed. The owner requested continuation and
confirmed personal non-business use with exclusive relevant Finnhub account
quota. [ADR-0016](../adr/0016-upcoming-eps-api.md) stage 2 is accepted for
[#180](https://github.com/daniilnahl/Stock-Tracking-App/issues/180). The earlier
single-symbol live smoke already proved technical calendar access at test time;
no additional live request is authorized or needed here.

## Plan and ownership

1. Master records acceptance, operating assumptions and merged API evidence.
2. `eps_impl` adds opt-in configuration/launcher flag, lazy provider-layer factory,
   API composition and app-owned budget, with deterministic tests and cold
   source/wheel checks. Existing FMP factory/defaults remain unchanged.
3. `m9_analysis` independently reviews contract, source, tests and docs.
4. Master runs final canonical verification and any required generated-asset/
   browser profiles sequentially, reviews staged hygiene and publishes one PR.
5. Exact-head CI and owner merge remain separate gates; no agent merge.

## Scope and operating assumptions

`--enable-upcoming-eps` defaults false, independent of history/dashboard flags.
Disabled composition performs no Finnhub clock/key/provider work. Enabled
composition creates one app-owned monotonic budget and a lazy service; valid
operations sample one server UTC date, reserve provider-acquisition budget, then
read only the process `FINNHUB_API_KEY` through the existing loader/validator.
The isolated #178 Windows-user-variable smoke exception is not a production
fallback. Start the launcher from a process that has inherited the variable.

ADR-0016's local budget allows 30 admitted attempts in any trailing 60 seconds,
one in flight, startup quiet time of 60 seconds and a 60-second cooldown measured
from an upstream 429 receipt. Boundary timestamps expire at age >=60. Refusal is
immediate fixed `eps_rate_limited`/429, without sleep/queue/retry. Construction
failures consume reserved attempts; cleanup releases active ownership on every
outcome. Normal API admission continues holding active work through cancellation.
This is not a shared-account coordinator. The owner must maintain exclusive
quota use and one local application instance for these operating assumptions.

The provider factory supplies native restricted HTTPS transport and exact
5.0-second/262144-byte/128-row bounds. No cache, holding mutation, EPS arithmetic,
source fallback, new live probe, dashboard form, scheduler or dependency is added.
All automated data, keys, monotonic/civil clocks and HTTP responses are synthetic.

## Verification

Independent final source/tests/probes/schema/docs review passed with no actionable
findings. Prior live success does not replace deterministic verification of the
new composition and budget. Actual checks so far:

| Command | Result |
| --- | --- |
| Focused pytest profile below | 256 passed in 53.09s, including actual source/wheel composition and cold guards. |
| Frontend `npm test` | 217 passed in 8.81s. |
| `npm run package:dashboard` and `npm run package:check` | Schema/type/build/byte-exact package checks passed in 6.90s. |
| `npm run test:browser` with installed Edge | 29 passed in 27.1s. |
| `npm run test:integration` with installed Edge | Actual source/wheel dashboard: 2 passed in 22.6s. |
| `python -m pytest tests/test_repository_hygiene.py tests/test_api_eps_composition.py::test_source_real_eps_launcher_composition_probe -q --tb=short` | 10 passed in 17.03s after the explicit synthetic-bearer rename. |
| `python -m pytest -q --tb=short` | Final full rerun: 3178 passed in 147.77s. |
| `python -m ruff check .` / `python -m mypy` / `python -m pip check` | Passed; mypy covers configured `config.py` only; no broken requirements. |

```text
python -m pytest tests/test_eps_budget.py tests/test_api_eps_composition.py tests/test_api_launcher.py tests/test_api_boundary.py tests/test_api_foundation.py tests/test_api_upcoming_eps.py tests/test_packaging.py --basetemp=.venv/eps-composition-final -q
```

Final staged hygiene passed: 9 tests in 14.46s. PR #181 exact-head Foundation
39095295435 passed all five checks; the owner merged at
`3af4db73d734453737e956819ef232c4c9197fdd`, followed by successful main Foundation
39097470838. Independent and Master review passed. No whole-M9 completion is
claimed; the dashboard and exit audit remain separate tasks.
Python 3.12.14, bundled Node 24.19.0/npm 10.8.2 and installed Edge
are unchanged. Native Windows profiles use task-local TEMP/TMP, synthetic process
keys and controlled HTTP, with no actual provider request or user state.

An initial expanded profile had 253 passes and three fixture/probe failures:
the new error schema had not yet been regenerated, and replacing the entire
environment before native TLS initialization removed Windows bootstrap variables.
The final schema is regenerated. The composition probe now bootstraps the native
event loop and TLS trust context before synthetic environment replacement, then
substitutes only the TLS-context factory and opener while retaining real native
URL/header/bounded-read/parser/service/API code and proven network denial. Cold
startup/import guards remain independently required and unchanged in purpose.
No production behavior was altered to satisfy this test-harness correction.

The initial full Python run had 3177 passes and one staged-hygiene failure in
150.70s: a literal clearly synthetic `token` variable in the probe matched the
credential rule. Renaming it to `synthetic_bearer` preserves the fixture value
and behavior while making its purpose explicit. The scanner remains unchanged;
the corrected index passed hygiene and the source probe. Full verification is
repeated rather than treating the initial run as green; the final full run passed.
