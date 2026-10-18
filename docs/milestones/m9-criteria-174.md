# M9 criteria / M10 discovery scope change — issue #174

The owner's 2026-10-17 instruction is the product authorization for
[#174](https://github.com/daniilnahl/Stock-Tracking-App/issues/174) and
[ADR-0017](../adr/0017-user-criteria-taurus-discovery.md). M9 will let the user
configure stock criteria; M10 Taurus agents will search for candidates using
those criteria. M9 does not implement an API-based market screener or supply a
daily suggested-stock winner. Existing permitted known-stock data calls remain.

This task updates the SRS's ownership/criteria/exit rules, the milestone plan,
decision brief and frontend prerequisite checklist. It changes no runtime UI,
API, agent, provider, storage, financial formula or dependency. Parameter/schema/
storage details and M10 execution contracts need their own bounded follow-ups;
do not invent them or ask for duplicate approval of this ownership decision.

Master owns specification/planning on `codex/m9-criteria-m10-discovery` from
owner-merged main `ef1da71` (#173). `m9_analysis` independently reviews the full
diff for residual M9 candidate-search gates, fabricated acceptance and accidental
agent activation. Canonical source/installed-wheel checks and staged hygiene
precede publication; owner merge remains separate, with no agent merge.

## Verification

Independent complete review passed after removing residual M9 candidate/ranking
records, aligning the next M9 decision with criteria rather than search-universe
selection, and making framework-specific license review conditional on actual
component selection. Master reviewed the final staged diff.

Canonical checks used the unchanged pinned Python 3.12.14 environment, task-local
TEMP/TMP and approved native Windows subprocess/hard-link execution.

| Command actually executed | Result |
| --- | --- |
| `python -m pytest tests/test_baseline.py tests/test_repository_hygiene.py -q --tb=short` | 23 passed in 20.65s. |
| `python -m pytest -q --tb=short` | 3077 passed in 147.87s, including installed-wheel checks. |
| `python -m ruff check .` | Passed. |
| `python -m mypy` | Passed; configured `config.py` only. |
| `python -m pip check` | No broken requirements. |
| Relative Markdown target and staged whitespace checks | Passed. |

The full suite includes staged hygiene; final documentation staging receives a
separate scan before commit. Exact-head hosted CI/publication is tracked on #174.
No browser profile, live stock search or Taurus/model run is part of this change;
no runtime criteria capability is claimed. Owner merge remains separate.
