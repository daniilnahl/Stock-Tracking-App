# Milestone 0 verification record

Review date: 2026-10-03 (America/Los_Angeles).
Audited main commit: `e0bbeb1b743405a5019e11d55eaea7577aa03977` (merged PR #35).
Parent milestone: [M0 — Security & Foundation](https://github.com/daniilnahl/Stock-Tracking-App/milestone/1).
Related issues: [#12](https://github.com/daniilnahl/Stock-Tracking-App/issues/12)
and [#13](https://github.com/daniilnahl/Stock-Tracking-App/issues/13).

## Finding

The foundation implementation is present and all three
[SRS §23](../../SRS.md#milestone-0--security-and-development-foundation) exit
criteria have supporting evidence. **M0 cannot yet be reported formally
complete:** the GitHub snapshot has twelve closed foundation issues and one
open issue, #12; the milestone is open. `AGENTS.md` §10.7 requires every
required issue to be closed. The passing main runs below resolve #12's
outstanding CI evidence requirement and support its closure after review.
This documentation change does not itself close an issue or milestone.

The review preserves the approved SRS v1.1, accepted
[ADR-0005](../adr/0005-canonical-python-dependencies.md),
[agent policy](../../AGENTS.md), [testing policy](../TESTING.md), and
[financial specification](../FINANCIAL_CALCULATIONS.md). It adds no runtime,
dependency, CI, API, financial or persistence changes.

## Deliverable coverage

Issue numbers below link to the parent milestone's bounded foundation work.
Their states describe the audit snapshot, not a promise about future state.

| SRS M0 deliverable | Requirement / authority | Inspected evidence | Issue state |
| --- | --- | --- | --- |
| Rotate exposed credentials | SEC-004 | [Owner attestation](../security/issue-3-credential-rotation.md), dated 2026-10-02; external revocation is owner-confirmed. | [#3](https://github.com/daniilnahl/Stock-Tracking-App/issues/3) closed |
| Remove secrets from source | SEC-001, SEC-005 | Tracked-index credential-pattern scan; sanitized scratch script; `.env` untracked. | [#4](https://github.com/daniilnahl/Stock-Tracking-App/issues/4) closed |
| Add `.env.example` | SEC-003 | [Empty canonical template](../../.env.example); no usable key. | #4 closed; [#17](https://github.com/daniilnahl/Stock-Tracking-App/issues/17) closed |
| Update `.gitignore` | SEC-003 | [Ignore rules](../../.gitignore) cover environment overrides, both legacy pickle filenames, virtualenvs and generated artifacts. | #4 closed |
| Add configuration module | SEC-002, SEC-005; ARCH-001 boundary | [Shared loader](../../config.py) and all three runtime callers; missing/blank-key rejection and redacted diagnostics tested. | [#7](https://github.com/daniilnahl/Stock-Tracking-App/issues/7) and #17 closed |
| Standardize `pyproject.toml` | DEV-001–DEV-004 | [Project configuration](../../pyproject.toml), accepted ADR-0005, exact pins, flat-module discovery and canonical pip setup. | [#2](https://github.com/daniilnahl/Stock-Tracking-App/issues/2), [#5](https://github.com/daniilnahl/Stock-Tracking-App/issues/5), [#13](https://github.com/daniilnahl/Stock-Tracking-App/issues/13) closed |
| Add pytest | TEST-001–TEST-004 | [Test harness](../../tests/conftest.py) isolates credentials, dotenv, cwd, Matplotlib and network; collection excludes manual scratch execution. | [#6](https://github.com/daniilnahl/Stock-Tracking-App/issues/6) closed |
| Add Ruff | TEST-005 | Explicit `E4`, `E7`, `E9`, `F` baseline for Python 3.11; repository source remains in scope. | [#8](https://github.com/daniilnahl/Stock-Tracking-App/issues/8) closed |
| Add type checking when ready | DEV-001, TEST-005; SRS §23 | Strict mypy checks real `config.py`; [readiness decision](../TESTING.md#type-check-readiness-decision--issue-11) records legacy gaps and ownership. | [#11](https://github.com/daniilnahl/Stock-Tracking-App/issues/11) closed |
| Add CI | TEST-002, TEST-003, TEST-005; GH-005 checks | [Foundation workflow](../../.github/workflows/foundation.yml); all five jobs passed on main, as recorded below. | #12 open; implementation merged in [PR #34](https://github.com/daniilnahl/Stock-Tracking-App/pull/34) |
| Add PR and issue templates | GH-003, GH-004 | [Engineering task](../../.github/ISSUE_TEMPLATE/engineering_task.md) and [PR template](../../.github/pull_request_template.md) require scope, requirements, dependencies and actual verification. | [#10](https://github.com/daniilnahl/Stock-Tracking-App/issues/10) closed |
| Add `AGENTS.md` | SRS §21; GH-003, GH-004 | Tracked operating policy and approved SRS are available on main. | #2 closed |
| Add `docs/TESTING.md` | TEST-001–TEST-005 | Canonical commands, isolation, actual type scope and CI contract published. | #6, #11, #13 closed; #12 open |
| Add `docs/FINANCIAL_CALCULATIONS.md` | FIN-003–FIN-005, AN-001 | Normative v0.1 formulas, units, known-value example, open decisions and legacy discrepancies published. | [#9](https://github.com/daniilnahl/Stock-Tracking-App/issues/9) closed |

## Exit criteria evidence

| Approved exit criterion | Assessment and evidence |
| --- | --- |
| CI passes on main. | Met. [Run 37147831762](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37147831762) passed after PR #34 at `40ebf656f2017b59b31845696efc19e0e2b139bd`. [Run 37149517565](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37149517565) passed after PR #35 at the audited commit. Both are completed push runs on main; all five job conclusions were inspected. |
| No active credentials exist in source. | Supported by closed #3 owner rotation attestation, closed #4 source remediation, untracked `.env`, empty template, inspected dynamic credential loading and a passing tracked-index pattern scan. Revocation is owner-attested; scanner coverage is bounded to known literal/URL patterns, not arbitrary formats or history. No live credential test is claimed. |
| Canonical setup/test commands are documented. | Met. [README](../../README.md#canonical-setup) and [TESTING](../TESTING.md#2-canonical-commands) publish the same installation/verification block, Python 3.11/3.12 support and actual mypy scope. [PR #35](https://github.com/daniilnahl/Stock-Tracking-App/pull/35) records fresh/repeat installs on both supported runtimes; the local review below rechecks the current checkout. |

The five successful main check names are `Tests (Python 3.11)`,
`Tests (Python 3.12)`, `Ruff`, `Mypy (configuration)`, and `Credential patterns`.
Protection settings were not inspected or changed; successful check execution
does not establish that branch protection requires them.

## Code review and remaining boundaries

- `config.py` hides its key in representations, preserves process-over-dotenv
  precedence for the same name, uses absent-only `MY_API_KEY` fallback and
  rejects blank credentials before network commands. The two CLIs and scratch
  script use this boundary; configuration objects are not serialized.
- `stock.py` still stores `API_KEY`, calls provider URLs, formats financial
  values as strings and renders charts. `watch_list.py` still mixes collections
  with terminal presentation. ARCH-002, DOM-001 and numeric domain behavior
  belong to M1; the current M1 backlog includes #25–#31 and exit verification
  #33. Configuration isolation alone does not establish domain isolation.
- `utils/utility_module.py` sanitizes request diagnostics but preserves the
  legacy `None` error contract. `check_ticker` treats a `None` response as a
  successful match and caches the ticker. Provider abstraction, response/error
  semantics, timeout/retry policy and provider typing remain M2 work under
  ARCH-003 and DATA-006; no provider failure is blessed by this review.
- Both CLI modules load cwd-relative pickle files at import and persist
  `Stock.API_KEY`. M1/M3 own removing credential coupling and replacing primary
  storage under PERS-001. Verification uses isolated temporary paths; no user
  pickle or local credential file was read, deleted or migrated.
- `Stock.graph_performance` reconstructs prices from summary percentages and
  uses the current date. Genuine historical data is M4 work under DATA-003 and
  FC-060. Financial discrepancy ownership and undefined metric decisions remain
  explicit in the financial specification; M5 is blocked where definitions
  are missing. The offline M0 suite does not certify financial correctness.
- Mypy covers only `config.py`. Legacy typing remains assigned to M1/M2/M3/M6.
  Runtime `Stock` representations and saved objects are outside the bounded
  configuration redaction guarantee; domain/persistence work must address them.

These are existing later-milestone requirements, not deferred M0 deliverables.
No new architecture decision or financial convention is introduced.

## Local verification

The following checks ran in a fresh Windows Python 3.12.10 virtualenv using the
exact-pinned `.[dev]` installation. Each `python` command was invoked through
`.venv/Scripts/python.exe` from the checkout. The host's default Python 3.14
is outside the approved range; no Python version or project tooling was changed.
Initial sandbox process launches were denied; supported-runtime execution and
dependency installation succeeded after sandbox escalation.

| Command / check | Observed result |
| --- | --- |
| `python -m pip install ".[dev]"` | Passed in the fresh virtualenv. |
| `python -m pip check` | No broken requirements. |
| `python -m pytest tests/test_baseline.py tests/test_packaging.py tests/test_repository_hygiene.py -v` | 24 passed, including temporary CLI help, offline wheel build/imports, pinned dependencies and index hygiene. |
| `python -m pytest` | 83 passed. |
| `python -m ruff check .` | All checks passed. |
| `python -m mypy` | Passed for the single configured source file, `config.py`. |
| `git check-ignore -- .env .env.local watchlist.pkl daniils_stock_methodd.pkl .venv/ dist/` | All six paths ignored. |
| `git ls-files -- .env .env.example` | Only `.env.example` tracked. |
| Markdown and authority review | 46 local links/anchors resolve; README/TESTING canonical command blocks match; removing only the SRS review note reproduces the approved main SRS exactly. AGENTS, ADR-0005 and financial definitions unchanged; financial known-value example independently checked. |

The tracked-source scan includes staged documentation, including this new
record. Final patch whitespace and diff review check that only the five intended
Markdown documents change; no credentials or generated artifacts are included.

Not independently verified in this local review: Python 3.11 execution,
macOS/Linux setup walkthrough, arbitrary/historical secret formats, provider
credential validity, and repository branch-protection enforcement. Hosted main
CI verifies Python 3.11 and 3.12; PR #35 records the earlier fresh/repeat Windows
walkthrough on both. Owner-attested rotation is intentionally not replaced with
a live production request. Whole-application typing and financial/provider
correctness remain outside the documented M0 baseline.

## Completion handoff

Review the recorded passing main runs and close issue #12 once its acceptance
criteria are accepted. Then recheck all foundation issue states, required CI
and SRS exits before marking M0 complete. This branch does not merge itself,
change protections, rotate credentials, rewrite history or start M1 work.
`AGENTS.md`, the accepted ADR and normative financial definitions remain intact.
