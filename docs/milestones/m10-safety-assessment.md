# M10 safety assessment — issue #191

**Status: proposal only, 2026-10-18.** This candidate-independent, documentation-only
assessment addresses [#191](https://github.com/daniilnahl/Stock-Tracking-App/issues/191)
in [M10](https://github.com/daniilnahl/Stock-Tracking-App/milestone/11).
It does not select a framework, accept an ADR, authorize installation or external
execution, or activate Taurus. No model/provider call, credential access,
private-data inspection, upstream execution, account change or runtime
modification is part of this work. Related M10 assessments:
[criteria and candidate evidence](m10-criteria-evidence.md) and
[framework feasibility](m10-framework-feasibility.md).

## Authority and present evidence

[AGENTS.md](../../AGENTS.md), [SRS §23.10](../../SRS.md#milestone-10--ai-research-agents),
[ADR-0017](../adr/0017-user-criteria-taurus-discovery.md) and
[ADR-0018](../adr/0018-custom-criteria-editor.md) control this assessment.
ADR-0017 accepts M10 ownership of criteria-driven discovery; ADR-0018 accepts a
nonexecuting editor. Neither accepts AI execution or arbitrary metric evaluation.
AI1002/1004–1010/1016–1018/1021/1025/1026/1029 and X716–718 are assessment targets;
D9/D10/D11 and the remaining feasibility/privacy/rights contracts remain gates.
No recommendation below changes the accepted criteria envelope or financial rules.

Baseline inspected: main `3b3df5b`. Existing code establishes useful boundaries,
not an AI sandbox or proof of external usage rights:

| Inspected evidence | Existing behavior and limit |
| --- | --- |
| [API access](../../src/stock_tracker/api/access.py), [API foundation](../API_FOUNDATION.md), [API operations](../API_OPERATIONS.md) | Exact local Host, authenticated API, restricted Origin with explicit dashboard exception, no-store, fixed errors, bounded requests/responses. Current body rejection and read-only routes do not authorize a future run-creation endpoint. Worker access to loopback would bypass the intended data boundary if given local credentials. |
| [Admission](../../src/stock_tracker/api/context.py), [foundation tests](../../tests/test_api_foundation.py) | Four shared operations, separate history/EPS limits; started workers retain slots on caller cancellation. These are process-local capacity limits, not durable model spend limits. |
| [EPS budget](../../src/stock_tracker/api/eps_budget.py) | Explicit attempt accounting, startup quiet time and active lease. Does not implement LLM token/cost reservations, cross-process ownership or restart recovery. |
| [Finnhub transport](../../src/stock_tracker/providers/finnhub_transport.py), [transport tests](../../tests/test_finnhub_transport.py) | Specific HTTPS host/path/query, no redirects, bounded reads, closed responses and sanitized failures. Does not establish a general web-search allowlist or LLM transmission rights. |
| [API boundary test](../../tests/test_api_boundary.py), [cold probe](../../tests/api_foundation_probe.py), [domain isolation test](../../tests/test_domain_isolation.py), [credential tests](../../tests/test_configuration_security.py) | Offline guards and synthetic regressions exercise core isolation/redaction. They do not constrain an independently running untrusted framework at the OS boundary. |
| [Criteria module](../../frontend/src/features/criteria.ts), ADR-0018 | Exact ordered data snapshot, all/any, decimal strings and descriptive text; no request, persistence or agent execution. Valid text may still contain malicious instructions or private information. |
| [Persistence ADR](../adr/0009-persistence-contracts.md) | Existing user-data contracts remain authoritative. Research storage must not add tables or migrations to core data by implication. |

## Proposed enforcement boundaries

These controls need an accepted implementation/isolation ADR and offline proof
on the supported deployment before any activation. A subprocess, prompt warning,
Python monkeypatch or model promise alone is insufficient.

Open question for the owner, not a decision of this assessment: the README
documents native Windows setup (PowerShell virtualenv and user environment
variables) alongside macOS/Linux, and the tests include native Windows junction
and reparse-point cases. The identity boundary, refusal of inherited handles,
and DNS/proxy egress denial proposed below are not demonstrated on that Windows
deployment. Whether those controls can be enforced there, or only inside a
container or VM, is unresolved. This assessment does not choose a platform or
a sandbox mechanism.

1. **Admission and data minimization (AI1005–1008, X716–718).** Keep Taurus
   disabled by default. Require explicit initiation, exact reviewed criteria,
   approved evidence sources/use, model configuration and finite limits before
   acquiring credentials or dispatching work. Project only licensed public
   security evidence plus approved criteria; never serialize a Stock/watchlist/
   portfolio object into a prompt. Exclude holdings, quantities, costs, private
   annotations, account identifiers and local paths. Free-text criteria can
   themselves contain private data: a new reviewed outbound-data admission policy
   must block such content or obtain the separately approved exception; the
   editor's syntactic validator and general AI opt-in are insufficient. Do not
   silently rewrite criteria to remove data or claim a match after doing so.
   Private portfolio transmission requires documented purpose, provider-specific
   consent AND a separate owner-approved X716 exception before implementation.
2. **Process and filesystem (AI1002/1004/1018).** Prefer an isolated worker
   behind a small data-only adapter, subject to feasibility review. Run with an
   identity/OS boundary unable to read user databases, home/config files, .env,
   browser profiles or core cache/legacy paths; no inherited handles or broad
   environment. Give read-only approved code/evidence and a distinct bounded
   run directory only. Deny path traversal, symlink/junction/reparse escapes,
   arbitrary mount/path selection, pickle/arbitrary-object loading and child
   execution. An application path-prefix check alone is insufficient. If these
   denials cannot be enforced and demonstrated, reject that execution path.
3. **Keys and network (AI1006/1009).** A trusted credential broker owns only
   the selected provider's server-side key and injects authentication after
   validating the request. Model/framework context gets no key, core API bearer,
   unrestricted environment or credential-returning tool. Worker outbound
   networking is denied except through the broker; include DNS, proxy and
   subprocess bypasses in the denial. The broker allows reviewed HTTPS hosts,
   ports, paths, methods and typed parameters, verifies TLS, refuses redirects
   and URL userinfo, and blocks loopback, private/link-local/metadata addresses
   and DNS-rebinding destinations at connection time. No arbitrary URL from
   criteria, evidence or model output becomes a fetch. Return captured evidence
   IDs; source links are sanitized and validated separately. Broker host access
   is still subject to source-specific rights and request budgets.
4. **Tools and trading (AI1004/1009).** Construct a closed capability registry
   containing only separately approved research tools. Do not load upstream
   defaults/plugins, brokerage, order/trader/simulation routing, shell, Python,
   SQL, file access, email, webhooks, downloads, package installation or generic
   HTTP tools. Resolve typed tool names/arguments in trusted code; deny unknown
   fields, names, commands and destinations before effects. No core write port,
   database connection or local API credential crosses the adapter. A framework
   requiring these capabilities is unsuitable for this scope. No BUY/HOLD/SELL
   opinion publication while D11 remains unresolved.
5. **Untrusted evidence and output (AI1009–1011).** Criteria, pages, filings,
   summaries, tool responses and model output are data, never authority to
   change policy, tools, limits, instructions or user criteria. Delimit evidence
   and preserve provenance, but enforce privileges outside the model. Validate
   size/schema, identity/cutoff and captured references; separately check that
   evidence supports each source-dependent claim. Withhold unsupported facts;
   keep only sanitized validation failures/partial status. Escape output as text;
   no HTML/script execution or automatic remote image/link retrieval. Do not
   publish chain-of-thought. These are layered containment proposals, not a
   guarantee that prompt injection is solved. [OWASP's primary guidance](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
   (accessed 2026-10-18) describes indirect input attacks and recommends least
   privilege and treating model behavior as untrusted; those principles motivate
   the external broker.
6. **Publication and failure (AI1014/1017/1018/1021/1029).** Validate into a
   bounded staging artifact and publish a completed report atomically only after
   all mandatory gates pass. Keep partial, failed, cancelled and disabled
   outcomes distinct from no candidates found. SRS AI1015 names lifecycle states
   including `partial`/`failed`/`cancelled`; AI1032 and §23.10.4 also say
   `incomplete` (and AI1032 `disabled`) for that distinction from an empty
   search. The SRS does not pick one of those words. This assessment uses
   AI1015's `partial` for the unfinished run, and the same labels as the
   [criteria and candidate evidence proposal](m10-criteria-evidence.md).
   Diagnostics allow only non-secret IDs, safe status/error
   categories, approved model/settings identifiers, durations and counters;
   never raw prompts, exceptions, request headers, token-bearing URLs, private
   input, sensitive excerpts or indefinite conversational memory. Disabling or
   uninstalling optional AI preserves CLI/API/dashboard/criteria and user data;
   it must not trigger deletion of reports or change core dependency pins.

## Proposed budget reservation and cancellation contract

D9 is not resolved by a spend estimate or a dashboard alert. The trusted broker
must be the only billable-call path, including tool/search calls, retries,
embeddings, internal subagents and any vendor-managed continuation. Disable
hidden retries and server tools unless their complete maximum charge is bounded.

Before each call, atomically validate enablement, noncancelled run state,
monotonic deadline, approved pricing version/currency and rights; reserve all
resources against BOTH run and shared provider/account limits. Coordination
must cover every participating worker/restart; otherwise restrict execution to
one proven exclusive broker and refuse competing ownership. No numeric defaults,
exchange-rate convention or production SLO is accepted by this document.

| Resource | Required pre-call enforcement |
| --- | --- |
| Time | Finite run deadline and remaining call timeout, bounded steps/debate/retries, broker deadline and worker watchdog. No new dispatch after expiry. Wall-clock changes must not extend the run. Remote work may outlive a local timeout; its full billable maximum remains reserved. |
| Requests | Consume a finite attempt for each dispatch, including uncertain sends/retries. Bound source fan-out and graph depth; no retry may reset counters or bypass shared quota/Retry-After. |
| Tokens | Bound serialized input with a verified tokenizer or conservative proven upper bound, maximum output and every chargeable reasoning/cache/tool token category. Reserve their maxima, enforce provider output limits and bound incoming streams. Unknown hidden usage means refusal. |
| Cost | Reserve worst-case total charge for all bounded categories and fixed/tool/request fees under a reviewed price version. Use exact monetary arithmetic with conservative rounding; no floating-point under-reservation or speculative cached-input discount. Unknown prices, currency conversion, charge categories or unenforceable vendor maxima block the path. |
| Storage | Reserve finite bytes for evidence, streams, temporary files, logs, checkpoints and final artifacts under per-run AND shared disk quotas; bound reads/decompression and stop before writes exceed reservation. Existing user reports cannot be evicted to fund a new run. |
| Concurrency | Atomically acquire shared run/call/provider slots before dispatch. Retain local slots until actual execution ends; account for unresolved remote work before admitting replacement calls. Reject excess work or use a separately approved bounded queue. |

Conceptual invariant for each cost scope: **confirmed charges + outstanding
worst-case reservations <= authorized cap**. Token, request and storage ledgers
need corresponding bounds. A call receives a unique non-secret dispatch ID and
an immutable reservation record before network effects. Safe recovery must never
replay a possibly sent request automatically, refund an uncertain reservation,
or reset the ledger after a crash. Corrupt/unavailable ledger or failed clock
closes admission. If observed billing exceeds the reserved maximum, disable the
path and report a contract failure; the cap was not proven enforceable.

On verified settlement, charge actual validated usage and release only proven
unused reservation. Missing/late/contradictory usage keeps the full maximum
encumbered (or conservatively charged at that maximum) until a separately reviewed
reconciliation resolves it. An account shared with unrelated clients cannot
have an account-wide cap promised by this app without exclusive accounting or
a verified vendor hard cap; record that limitation before activation.

Cancellation atomically prevents future dispatch. If definitely unsent, release
the financial reservation once; attempt policy remains explicit. If dispatch may
have happened, try only an approved bounded vendor cancellation mechanism and
retain cost/token reservation until settlement or conservative maximum charge.
Closing a stream, UI disconnect, killed worker or reported cancellation cannot
undo an already billable request or prove remote termination. No queued task may
start later after cancellation. Worker-crash recovery follows the same rule;
ambiguous work becomes blocked/partial, never completed or silently retried.

## Rights, retention and unresolved decisions

No data/model vendor or account has been selected or assessed for entitlement
here. Public availability, source-code license, API key possession and a vendor
marketing claim do not establish transmission/retention permission. The following
is the required decision matrix, not a legal conclusion or permission grant.

| Use / boundary | Evidence required before activation | Present finding / owner decision |
| --- | --- | --- |
| Framework code | Pinned version, actual license/NOTICE and dependencies, redistribution obligations, default telemetry/tools/storage inventory | Candidate-independent; unverified. No framework selected or installed. |
| Public evidence acquisition | Dated official source terms and contract for exact endpoint/fields, automation, quota, attribution and account entitlement | Unknown; existing quote/history/EPS access does not transfer rights to discovery. No scraping authorization. |
| Sending evidence to model/tools | Both data-source permission for third-party processing and exact recipient model/tool terms, subprocessors, regions and purpose; account-specific restrictions | Unknown; transmission blocked. Local processing also needs applicable data/model permission. |
| Provider retention/training | Actual endpoint/account logging, abuse monitoring, training, deletion, backup and subprocessors policy; any required contractual opt-out | Unknown; neither zero retention nor no-training inferred. Consent cannot override unavailable source rights. |
| Local evidence/cache/checkpoints | Permitted content, TTL, attribution, encryption/access needs, size cap and deletion semantics | Unknown; separate approved research location required, no core tables or implicit reuse of history TTL. Disable framework default stores/telemetry. |
| User-owned reports | Rights to retain derived text/excerpts/citations, allowed display/export/redistribution, ownership, retention and explicit deletion policy | Unknown; no automatic cache eviction, export/publication or indefinite retention approved. Expired cache does not imply deletion of user reports. |
| Private data | Specific purpose/field allowlist, owner-approved X716 exception, provider-specific opt-in and privacy contract | Excluded. No exception sought or assumed by this assessment. |
| Budget and isolation | Accepted broker/ledger/OS enforcement ADR, exact caps/pricing and failure semantics, supported runtime feasibility evidence | D9 open; no paid run authorized. If platform cannot enforce controls, decline that path. |
| Advice and execution | Owner decision on D11 and any separately scoped specification change | Opinions remain gated; trade/broker/core mutation paths unavailable. |

Retention decisions must distinguish transient cache, failed staging artifacts,
checkpoints, sanitized diagnostic records and user-owned reports. Each needs an
explicit owner, location, bounded lifetime/bytes, access and authorized deletion
procedure, including crash leftovers/backups/vendor copies where applicable.
This assessment neither schedules cleanup nor deletes anything. Missing rights
or retention decisions block the affected feature, preserving normal local use.

## Synthetic verification plan — not executed safety tests

Implement in separately approved work with fixed offline evidence, fake billable
endpoints, controlled monotonic clocks, temporary directories/databases and
synthetic credentials only. Observe actual broker/OS denials and absence of side
effects; model refusal text alone cannot pass a case. Include negative controls
proving each test can detect a forbidden access. [TESTING.md](../TESTING.md)
remains the canonical suite contract.

| Case | Required observable result |
| --- | --- |
| Criteria/article/tool summary says ignore rules, reveal keys, relax a threshold or trade | No policy/criteria mutation, secret transmission or new capability; unverified claims withheld. |
| Criteria embeds private holdings/account text | Outbound admission refuses; no model/tool call and no raw text in diagnostics; exact local snapshot preserved. |
| Unknown tool, shell command, SQL, simulation/brokerage call, download or hidden upstream default | Denied before effect, no child process/core write/network bypass. |
| Encoded/redirecting URL, URL credentials, loopback IPv4/IPv6, private/link-local or rebinding destination | Broker refuses before unsafe connection; no credential forwarding or source fetch outside policy. |
| Worker reads .env/home/core SQLite or follows symlink/junction outside run root | OS-level denial; original bytes unchanged. Test reads and writes, not merely absent files. |
| Prompt/exception/URL contains a synthetic secret; report contains script/remote image | Secret absent from prompt/report/browser/log/export; inert escaped text and no external renderer request. |
| Forged citation, real citation that does not support claim, wrong cutoff/identity | Claim withheld; partial/validation failure distinct from no matches or verified result. |
| Concurrent calls individually fit but jointly exceed cap | Atomic admission allows only within combined cost/token/request/storage/concurrency limits. |
| Unknown or changed pricing, unbounded hidden tokens/tools, ledger or clock failure | Zero dispatch; safe actionable refusal without retry loop. |
| Stream growth, decompression bomb, runaway debate/retry or exhausted quota | Enforced byte/step/time/request/token caps; no new calls or writes beyond reservation. |
| Cancel before dispatch / during send / after send; disconnect while worker runs | Unsent dispatch prevented; uncertain/started costs retained; slots not released early; no late queued start. |
| Crash between reservation/send/receipt/settlement; duplicate retry/recovery | No duplicate billing by automatic replay, no double release and no cap reset; uncertain reservation retained. |
| Missing/late/invalid usage or reported charge beyond maximum | Hold maximum reservation; disable unprovable path, no claim cap held if exceeded. |
| Disk full, publication failure, corrupted output or worker outage | No completed report published from partial text; no core mutation; bounded diagnostic and preserved user reports. |
| AI absent/disabled/incompatible; exhausted budget | CLI, M7/M8, M9 criteria and accepted EPS paths remain usable; no optional import/config acquisition on core paths. |

Repository regression checks do not prove the proposed AI controls, vendor
rights or milestone exit.
