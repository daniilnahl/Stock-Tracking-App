# M9 upcoming-EPS API contract — issue #170

**Current delivery — 2026-10-18:** this is a dated task/research record. The accepted criteria editor and EPS adapter/service/configuration/API/opt-in launcher/dashboard are now merged, and the independent audit is merged with passing main CI. Earlier pending/no-API/no-UI statements apply to their original scope or unapproved extensions. Provider research remains dated; no new entitlement, metric or live call is inferred. See [current implementation status](../CURRENT_STATUS.md).

The owner merged #169 and requested continuation. The adapter and injected
application service are delivered; public API, production date and quota
choices remain reserved by ADR-0015. [Issue #170](https://github.com/daniilnahl/Stock-Tracking-App/issues/170)
therefore prepares a concrete [ADR-0016 proposal](../adr/0016-upcoming-eps-api.md)
before runtime implementation. This is a specification proposal requiring
explicit owner acceptance, not a new runtime task or full M9 acceptance.

## Plan and traceability

1. Master verifies owner merge/main CI, inspects API/service contracts and opens
   this milestone-linked issue on `codex/m9-eps-api-contract` from main
   `1847a155d2e44f1fa82e315e060f557a421e542d`.
2. Master prepares exact endpoint, serialization, local-validation distinction,
   UTC reference-day policy, resource/admission/budget/restart choices and lazy
   opt-in activation contract. `m9_analysis` reviews independently.
3. Run canonical checks and staged hygiene, inspect diff and publish one PR.
   Owner acceptance/merge is separate; no agent merge.
4. After acceptance, decompose each implementation objective into its own issue:
   injected API; then evidence-gated production composition/budget; then separate
   minimal dashboard design/implementation. Do not assign blocked work.

The API initially takes an explicit provider symbol, avoiding an unapproved
saved-stock mapping. EPS remains precise reported non-GAAP data with unknown
currency/share basis/vintage and no arithmetic. No real credential, account,
paid data, network probe, persistence or source/default configuration is changed.

## Review and verification

Independent readiness analysis recommended the direct API path over another
offline wrapper. It identified the current query guard and shared local/upstream
ProviderRequestError category as contracts that must be addressed explicitly.
Independent full review passed after correcting the existing dashboard flag,
explicitly binding returned context to the request, and clarifying that budget
exclusivity covers the relevant account quota across all keys/clients. Master
reviewed the final staged diff. Main Foundation 38988510270 passed separately.

Canonical verification used the unchanged pinned Python 3.12.14 environment,
task-local TEMP/TMP and approved native Windows subprocess/hard-link execution.
No runtime, dependency or toolchain changed.

| Command actually executed | Result |
| --- | --- |
| `python -m pytest tests/test_baseline.py tests/test_repository_hygiene.py -q --tb=short` | 23 passed in 20.09s. |
| `python -m pytest -q --tb=short` | 3045 passed in 176.36s, including installed-wheel checks. |
| `python -m ruff check .` | Passed. |
| `python -m mypy` | Passed; configured `config.py` only. |
| `python -m pip check` | No broken requirements. |
| Relative Markdown target and staged whitespace checks | Passed. |

Final staged documentation receives another credential/hygiene scan before
commit. Exact-head hosted CI/publication is tracked on #170. No browser profile
or live account/access test ran. Local review and passing checks establish a
reviewable proposal, not acceptance or implementation of its runtime choices.

The official public terms were readable on 2026-10-16; current pricing/calendar
text fetches returned JavaScript shells. The proposal records that limitation
and preserves dated prior research. Free account existence, exact entitlement
and permitted local use remain owner evidence, not claims established by CI.
