# M2 market-provider exit evidence


**Subsequent M3 update (2026-10-06):** [M3 completion evidence](m3-exit-evidence.md) records
closed milestone 4 and all nine required issues. Maintained CLIs now restore
SQLite state lazily, without application pickle IO or persisted runtime keys;
legacy files are preserved for manual reviewed neutral reconstruction. References
below to unsafe pickle, credential-bearing state or future M3 work describe the
original dated snapshot, not current behavior. Historical acceptance, verification
and external credential-rotation attribution remain unchanged.


## Completion review — 2026-10-05

**M2 is implemented and achieved under AGENTS.md §10.7.** The
[final issue #56 completion report](https://github.com/daniilnahl/Stock-Tracking-App/issues/56#issuecomment-5999403521)
records no remaining M2 blocker. All ten required issues (#47, #48, #50–56 and
#66) are closed after human merges of PR #57–65 and #67. At this completion
snapshot, [milestone 3](https://github.com/daniilnahl/Stock-Tracking-App/milestone/3)
is closed at 100%, with zero open and 20 closed items (issues and PRs).

Completed implementation main is `5eccf3b24edbe03a6f01e86b9dfcffb80a1ad0c7`,
the human merge of [PR #67](https://github.com/daniilnahl/Stock-Tracking-App/pull/67).
Its exact reviewed implementation head is
`a73b66135c3b85b1a68800407a4d5ed525bbd793`. The
[exact-head PR Foundation run 37345838578](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37345838578)
and [post-merge main run 37346059176](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37346059176)
both passed **Tests (Python 3.11), Tests (Python 3.12), Ruff, Mypy (configuration)
and Credential patterns**. The final closing audit passed **301 focused cases**;
fresh main verification passed **1,334 full pytest cases**, Ruff and configured
mypy for **one source file (`config.py`)**. These completed implementation checks
are separate from this later documentation-only branch's pending PR/CI.

| SRS §23 M2 deliverable / exit | Result and evidence | Issue / human-merged PR |
| --- | --- | --- |
| Create MarketDataProvider | PASS: provider/history protocols, pure contract/source/wheel probes | #47 / #57; #48 / #58 |
| Implement FMP adapter | PASS: all four capabilities, precise parser/status/request-count matrices | #50 / #59; #51 / #60; #52 / #61; #53 / #62; #54 / #63 |
| Add typed provider models | PASS: immutable Decimal/nullable/UTC models and safe typed errors | #48 / #58 |
| Define timeout/retry/rate-limit policy | PASS: accepted ADR-0007 values, explicit factory and deterministic transport tests | #47 / #57; #50 / #59 |
| Fix ticker validation | PASS: exact NASDAQ identities; ADR-0008 scoped no-match rejection; real wrapper/both CLI preservation tests; failures remain distinct | #54 / #63; #55 / #64; #66 / #67 |
| Add mocked provider tests | PASS: offline adapter/facade/domain/CLI/error/security/source/wheel checks | #48/#50–55/#66 implementation PRs; #56 / #65 |
| Application code no longer calls FMP directly | PASS: maintained callers delegate; controlled static violations, bounded legacy-helper exception, installed-wheel guards and exact request counts | #55 / #64; #56 / #65 |

The full historical issue/PR and requirement/test maps remain below; the current
final rows are **#56 / PR #65: closed after final exit review** and
**#66 / PR #67: closed after human merge and passing main CI**. ADR-0008 replaces
the earlier definitive unknown evidence gate only for scoped product invalidity.
A completed schema-valid NASDAQ no-match rejects a new candidate without adding
or saving; existing holdings remain intact. Malformed/duplicate identities,
authentication/access/request/HTTP 404/rate-limit/timeout/outage errors retain
their categories. Incomplete/truncated-search false negatives are an accepted
limitation; no global nonexistence or API completeness is asserted.

M3 persistence/pickle replacement, M4 genuine historical retrieval/corporate
actions/synthetic-chart removal, M5 analytics and M6 broader CLI work remain
later-milestone work outside M2; no required M2 deliverable is deferred.
Historical interfaces are not implemented retrieval; configured mypy
does not cover the whole application. No live key, account entitlement, search
completeness or branch-protection enforcement was verified by this completion audit.

## Historical #66 implementation update — 2026-10-05

The following dated snapshots describe the then-pending state. They are
superseded by the completion review above and preserved for traceability.

The owner later instructed rejection/reporting of a stock not found through the
FMP API. Approved [#66](https://github.com/daniilnahl/Stock-Tracking-App/issues/66),
accepted [ADR-0008](../adr/0008-scoped-ticker-rejection.md) and SRS DATA-006 now
record scoped product invalidity: a completed schema-valid successful NASDAQ
search with no exact supported match rejects the new candidate as invalid.
This supersedes the historical definitive unknown evidence gate below; it
accepts incomplete/truncated-search false negatives without asserting global
nonexistence or completeness. Malformed/duplicate identities and provider
failures retain their categories; no existing holdings are deleted.

PR [#65](https://github.com/daniilnahl/Stock-Tracking-App/pull/65) human merge
included the verification portion of #56 on main
`22cc27c2c009231428c935fabaa352d52eabbcc0`. The Master verified all five checks
in [main Foundation run 37264563909](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37264563909).
#66's task branch adds actual-adapter wrapper/CLI no-match regressions in
test_fmp_lookup.py and test_cli_ownership.py, with saved-byte/ordered-holding
preservation and no downstream request or candidate construction. Its PR,
exact-head CI, human merge and subsequent main CI remain pending. Final #56/M2
exit review remains required; neither issue nor milestone is closed here.

Local #66 canonical verification passed 1,334 full pytest cases, 142 focused
lookup/wrapper/CLI/factory cases, Ruff and configured mypy (config.py only).
These local results do not substitute for exact-head PR or post-merge main CI.

## Historical verification snapshot before #66

Snapshot: **2026-10-04; incomplete**. This records the unblocked verification
portion of [#56](https://github.com/daniilnahl/Stock-Tracking-App/issues/56), not
issue or milestone completion. DATA-006's definitive network unknown-instrument
classification remains unsatisfied. The verification changes' PR publication,
exact-head CI, human merge and subsequent main CI are pending.

## Authority and observed main state

The owner accepted ADR-0007 exactly at
`cf909dfc6c9766c440b1aeaf408d10c1f112e6a4` by saying **"I approve A"** in the
Codex milestone chat on 2026-10-04, retaining the DATA-006 blocker. The
[acceptance record](https://github.com/daniilnahl/Stock-Tracking-App/pull/57#issuecomment-5982448860)
is the Master's faithful record of that human instruction, not an independently
authored human GitHub approval. SRS, ADR-0005/0006/0007 and the financial/testing
specifications remain authoritative. No requirement or policy changes here.

The Master verified #47/#48/#50–55 closed and PR #57–64 human merged.
Local Git confirms the latest implementation head
`bf71b8f81de137a32240d0f3b5cb88e14b235336` is included in verified main
`2de8ce2069e7a85a9d5cf46f0a770065b7c8a7f0` after PR #64. The
[completed main push Foundation run 37262947445](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37262947445)
passed **Tests (Python 3.11), Tests (Python 3.12), Ruff, Mypy (configuration)
and Credential patterns**. That run verifies the merged implementation; it
does not verify this later verification branch. No agent merge is authorized.

| Issue | Delivered concern | Human-merged PR |
| --- | --- | --- |
| #47 | Accepted contracts and explicit reliability values | [#57](https://github.com/daniilnahl/Stock-Tracking-App/pull/57) |
| #48 | Immutable typed models, provider/history protocols, safe errors, packaging | [#58](https://github.com/daniilnahl/Stock-Tracking-App/pull/58) |
| #50 | Injectable HTTP, precise JSON, retry/budget/status/credential boundary | [#59](https://github.com/daniilnahl/Stock-Tracking-App/pull/59) |
| #51 | Stable quote parsing | [#60](https://github.com/daniilnahl/Stock-Tracking-App/pull/60) |
| #52 | Stable company-profile parsing | [#61](https://github.com/daniilnahl/Stock-Tracking-App/pull/61) |
| #53 | Stable period-change parsing in percentage points | [#62](https://github.com/daniilnahl/Stock-Tracking-App/pull/62) |
| #54 | Exact scoped lookup, CSV bypass, minimal approved factory | [#63](https://github.com/daniilnahl/Stock-Tracking-App/pull/63) |
| #55 | Facade, both CLI flows and scratch caller delegate through providers | [#64](https://github.com/daniilnahl/Stock-Tracking-App/pull/64) |
| #56 | Boundary controls, installed-wheel integration and this evidence | Open; verification PR pending; DATA-006 blocked |

## Requirement and automated evidence map

| Requirement / M2 deliverable | Source and meaningful tests | Assessment |
| --- | --- | --- |
| ARCH-001/002/003/006; provider protocol and isolated domain | providers/protocols.py, models.py; test_provider_models.py, test_provider_protocols.py, test_provider_errors.py, provider_contract_probe.py, test_domain_isolation.py, domain_isolation_probe.py | Typed interfaces; separate history capability; pure models/domain guards in source and installed wheel |
| DATA-001/002/007; FMP quote/profile/period adapter | providers/fmp.py; test_fmp_quotes.py, test_fmp_profiles.py, test_fmp_period_changes.py | Exact one-row identities, strict required fields, Decimal precision, nullable values versus zero; UTC receipt times; only verified quote Unix timestamp supplies as_of |
| DATA-008; currency boundary | compatibility/stock_operations.py; test_provider_integration.py | Known currency/exchange conflicts reject publication and invalidate price; absent metadata preserves known values; no USD default or FX |
| DATA-009–011, SRS §11/18, SEC-002/005, ERR-001/002 | providers/transport.py, fmp.py, factory.py; test_fmp_transport.py, test_provider_factory_validation.py | Approved explicit production policy; transient-only retry, bounded admission budget/jitter, 429 policy, closure, redirect rejection and safe errors/logs |
| DATA-006, ERR-001–003; ticker validation | providers/fmp.py, utility check_ticker; test_fmp_lookup.py, test_provider_factory_validation.py, test_baseline.py | Local invalid input versus inconclusive scoped identity versus unavailable data/infrastructure errors; CSV reads/writes denied; definitive network unknown remains blocked |
| FIN-001/002/003, DOM-002; facade and ownership compatibility | compatibility/stock_operations.py, both CLI modules; test_provider_integration.py, test_stock_facade.py, test_cli_ownership.py | Real domain arithmetic under typed/provider HTTP fakes; candidate publication, price/summary invalidation, holdings/order/metadata preservation, explicit-null success and failed-operation no-save |
| ARCH-003, PERF-001; no direct application FMP calls | test_market_provider_boundary.py; provider_integration_probe.py via test_packaging.py | Controlled violation regressions and actual installed provider/facade operation request counts; retained generic helper unused by maintained callers |
| TEST-001–005, SEC-005; deterministic/security/package evidence | conftest.py, test_packaging.py, test_repository_hygiene.py; all provider tests above | Offline fixed-clock fixtures, injected transport/jitter, isolated user state, credential-safe representation/pickle/errors and exact wheel contents; configured mypy covers config.py only |

The accepted production factory supplies 10-second per-attempt timeout,
30-second admission budget, at most two attempts, retry statuses
408/500/502/503/504, no automatic 429 retry, 0.5-second base and 2-second cap
for full-jitter backoff, zero quote/history TTLs and no stale fallback. The
admission budget checks before retries/sleep; it is not a hard wall-time bound
for urllib's blocking socket operations. No cache or extra application retry
layer has been introduced.

The static boundary test scans runtime Python for FMP URL literals, selected
distinctive payload-key subscripts/get calls (including price/symbol heuristics),
ordinary HTTP imports/calls, concrete fmp/transport imports in callers and
aliased calls to the retained generic helper. Controlled synthetic violations
prove enforcement. The utility exception permits only existing generic imports
and urlopen/certifi.where calls inside get_jsonparsed_data, not new caller HTTP,
FMP URLs or selected schema reads. This is a bounded literal/import/call
regression detector, not proof against dynamic obfuscation, arbitrary parsing,
every HTTP library or every generic metadata mapping.

The installed-wheel probe starts in a fresh `python -I` process with its own
network/TLS/CA guards before application imports and checks those guards deny
cached-module and bound-socket paths. Real factory construction, FMP parsing,
all four capabilities, check_ticker and the real Stock/domain facade execute
under one controlled HTTP boundary and UTC clock. Exact route counts exclude
hidden lookup/profile/quote requests. Exercised application module files must
originate in the installed target; utils namespace target precedence is checked
even when the canonical environment adds another installed namespace directory.
Representations and trusted synthetic pickle state exclude the synthetic key.
Separate fresh domain/pure-provider probes retain stronger import/IO isolation.

## Local verification and publication gates

Canonical Python is the existing `.venv` Python 3.11.9, with pinned dependencies;
Windows Store base launch requires sandbox escalation. No replacement toolchain,
live credentials, real user files, new dependency, runtime feature or CI change
is part of this verification portion.

Local full pytest passed **1,326 tests** on Python 3.11.9; focused boundary,
packaging, domain-isolation and provider-integration verification passed **159
tests**. Ruff passed; configured mypy passed for its one source file. Staged
hygiene results will be recorded in this task's PR after execution. Current verification
PR and exact-head CI are pending; subsequent owner merge/main CI are also
pending. Earlier successful main CI must not be relabeled as this branch's CI.

## Remaining DATA-006 decision and exit blocker

The Master reinspected the official [Stable search-symbol page](https://site.financialmodelingprep.com/developer/docs/stable/search-symbol),
[documentation index](https://site.financialmodelingprep.com/developer/docs) and
[quickstart](https://site.financialmodelingprep.com/developer/docs/quickstart)
on 2026-10-04. Those inspected public pages describe the search route, limit,
exchange and authentication; they do not establish exhaustive results, exact
match ordering or an authoritative global unknown-instrument signal. This is
limited evidence from those pages, not a claim that every provider document or
account entitlement was inspected. No live key or account was tested.

An empty result, fewer than 100 rows, a full 100-row result, exchange mismatch
or HTTP 404 does not prove a globally invalid ticker. The accepted implementation
raises InstrumentLookupInconclusiveError when no exact supported NASDAQ identity
is found; provider/authentication/rate-limit/timeout/malformed failures retain
their categories. Local invalid syntax alone can return False from check_ticker.
Closing #54 delivered this conservative contract; it did not satisfy definitive
network unknown classification or waive #56's exit blocker.

A further human decision must be recorded before #56/M2 can close:

- **A — retain the evidence gate (recommended):** keep current safe inconclusive
  behavior until authoritative provider evidence supports definitive network
  unknown classification. The gate remains open meanwhile.
- **B — explicitly approve a narrower DATA-006 interpretation:** treat supported
  NASDAQ no-exact-match/inconclusive classification as sufficient, accepting
  false-negative risk from incomplete or truncated search. This would never
  assert global invalidity or translate infrastructure failure into invalidity.
  B is a proposal only, unapproved; it requires a further accepted contract/SRS
  interpretation record and follow-up before issue/milestone closure.

Neither option is implemented or approved by this evidence document. The earlier
"I approve A" accepted ADR-0007's proposal and retained this blocker; it does not
approve either newly described exit decision. **#56 and M2 remain incomplete.**

M3 persistence/pickle replacement, M4 genuine history/corporate-action semantics
and synthetic-chart removal, M5 analytics and M6 broader CLI/service changes
remain outside this record. Historical protocol availability is not retrieval
implementation; period percentage points are not historical bars or ratios.
