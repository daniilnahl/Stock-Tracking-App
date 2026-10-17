# M9 injected upcoming-EPS service — issue #168

[Issue #168](https://github.com/daniilnahl/Stock-Tracking-App/issues/168) follows
owner-merged #166/#167 and the owner's instruction to continue. The accepted
contract is [ADR-0015's service addendum](../adr/0015-finnhub-upcoming-eps.md),
SRS's scoped EPS record and [EPS-001–004](../FINANCIAL_CALCULATIONS.md).
Broader M9 decisions remain proposed.

## Bounded plan and ownership

1. Master records the service contract and creates the milestone-linked issue.
2. `eps_impl` implements additive service/view and deterministic source/wheel
   tests on `codex/m9-eps-service`, from merged main
   `74f787554e3cd7c7083738347a83c887e1a1c5d0`.
3. `m9_analysis` independently reviews the full diff; Master runs canonical
   verification, inspects staged changes and publishes an issue-linked PR.
4. Required hosted checks and owner merge remain separate. No agent merge.

The service acquires an injected provider only after validating explicit symbol,
date bounds and one sampled intended research date. It returns immutable request
context plus unchanged validated observations, without accepting an arbitrary
analysis-date override. Source/accounting/unknown metadata, association, period
uniqueness and deterministic ordering are validated at the application boundary.
No financial arithmetic, timezone default, live credential/configuration,
API/CLI/UI, saved-stock mapping, quota policy, cache or persistence is added.

## Verification and remaining gates

**Merge update:** PR #169 is owner-merged at
`1847a155d2e44f1fa82e315e060f557a421e542d`; post-merge
[Foundation 38988510270](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38988510270)
passed. The local execution narrative below predates publication. The next task
is [#170's API proposal](../adr/0016-upcoming-eps-api.md), pending acceptance.

Use synthetic providers and fixed date suppliers for meaningful admission,
failure, precision, provenance and source/installed-wheel isolation checks.
Run targeted tests, full pytest, Ruff, configured mypy, pip check, staged hygiene
and final diff review. No browser profile is needed for this backend-only task.
Baseline merged-main Foundation 38987281100 passed. Independent contract/docs
and complete source/test reviews passed with no unresolved findings. Initial
targeted service/Finnhub/history verification passed 308 cases in 5.31s. The first
full run had 3,040 passes and one architecture-check failure in 174.47s: the static
checker knew the older neutral model/protocol modules but not the new EPS types.
ADR-0012 explicitly permits neutral provider models/protocols. The correction
registered the exact two EPS type imports and extended controls rejecting concrete
Finnhub/transport imports, broad EPS-module imports and unknown EPS types. General
provider admission remains unchanged. Independent review of the correction passed.

The unchanged pinned environment uses Python 3.12.14. Task-local TEMP/TMP and
approved native Windows execution support subprocess/hard-link checks. All
application/provider data remain synthetic and offline; no toolchain changed.

| Command actually executed | Result |
| --- | --- |
| Service/Finnhub/history targeted tests | 308 passed in 5.31s. |
| Service/architecture/service-boundary/history targeted repair tests | 176 passed in 4.87s. |
| `python -m pytest -q --tb=short` after correction | 3045 passed in 174.86s, including installed-wheel probes. |
| `python -m ruff check .` after correction | Passed. |
| `python -m mypy` | Passed; configured `config.py` only. |
| `python -m pip check` | No broken requirements. |
| Relative Markdown targets / staged diff whitespace | Passed. |

Master reviewed the staged source, probes, fixtures and documentation. The full
suite includes staged credential/hygiene checks; final documentation staging is
scanned again before commit. Local implementation and verification are complete.
PR publication, exact-head hosted CI and owner merge are tracked on #168; no
agent merge or full M9 completion is claimed.

Future live wiring requires verified access/permitted use, a trusted date
supplier with an explicit calendar convention, identity mapping if saved stocks
are used, and cross-request quota ownership. No test result resolves those gates
or demonstrates complete future-market coverage or historical forecast vintage.
