# Finnhub environment configuration — issue #172

**Current delivery — 2026-10-18:** this is a dated task/research record. The accepted criteria editor and EPS adapter/service/configuration/API/opt-in launcher/dashboard are now merged, and the independent audit is merged with passing main CI. Earlier pending/no-API/no-UI statements apply to their original scope or unapproved extensions. Provider research remains dated; no new entitlement, metric or live call is inferred. See [current implementation status](../CURRENT_STATUS.md).

The owner's 2026-10-17 instruction explicitly requests reading a newly obtained
Finnhub key from Windows environment variables like FMP. The bounded task is
[#172](https://github.com/daniilnahl/Stock-Tracking-App/issues/172), under
SRS SEC-001–005 and [ADR-0015's configuration addendum](../adr/0015-finnhub-upcoming-eps.md).
This does not accept the broader proposed ADR-0016 API/date/quota contract.

Master owns contract/docs, full verification and publication. `eps_impl` owns
the minimal `config.py` functions and synthetic offline tests on
`codex/finnhub-env-key`, based on merged main
`756943fc8466d34b4e9b44e2bcf5253073ec6dbe`. Independent `m9_analysis` reviews
the complete diff before publication. No agent merge or live credential use.

The explicit Finnhub loader reads only current-process `FINNHUB_API_KEY`, reuses
the existing secret-hidden configuration value and does not call dotenv. A safe
validator rejects missing/malformed header values before explicit adapter use.
FMP loading, legacy fallback and default application wiring remain unchanged.
Windows persistent environment changes require restarting the parent app and
terminal; README also gives a current-session secure prompt and injection example.

## Verification

Independent complete source/test/docs review passed with no unresolved findings.
Master reviewed the final staged diff. The unchanged pinned environment uses
Python 3.12.14 with task-local TEMP/TMP and approved native Windows execution.
Merged baseline Foundation 38997844773 passed separately.

| Command actually executed | Result |
| --- | --- |
| New/FMP configuration, security and Finnhub targeted tests | 244 passed in 11.84s. |
| Configuration tests after global Finnhub environment isolation | 91 passed in 3.25s. |
| `python -m pytest -q --tb=short` | 3077 passed in 144.34s, including installed-wheel checks. |
| `python -m ruff check .` | Passed. |
| `python -m mypy` | Passed; configured `config.py`, including both new functions. |
| `python -m pip check` | No broken requirements. |
| Relative Markdown targets / staged whitespace | Passed. |

The full suite includes staged hygiene; final documentation staging is scanned
again before commit. Exact-head hosted CI/publication is tracked on #172, with
owner merge remaining separate. No agent merge or broad M9 completion is claimed.
No actual key is read, displayed, stored or used; all fixtures are synthetic.
Live account access, permitted use and public API/launcher activation remain
outside this task. Obtaining a key does not resolve those remaining gates.
