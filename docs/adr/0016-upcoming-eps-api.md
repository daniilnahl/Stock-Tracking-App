# ADR-0016: Opt-in local upcoming-EPS API

## Status and decision requested

**Partially accepted — stage 1, 2026-10-17.** After owner-merging #177, the owner
explicitly approved Option A and requested online testing: "Yes approved but
test it online. We need to ensure the API calls actually work".
[#178](https://github.com/daniilnahl/Stock-Tracking-App/issues/178) implements the
injected API adapter and separately verifies one live single-symbol request.
The production flag/composition/budget and dashboard form remain later tasks;
their access/use and account-budget gates are preserved. No broad M9/M10
acceptance follows.

The isolated live smoke test uses the real restricted transport, adapter,
service and injected API in memory, with explicit UTC reference date and one
future window for a public symbol. The owner authorizes reading the existing
Finnhub environment credential solely for this test. If the running process has
not inherited the Windows user variable, pass that value into the test process
only; do not change saved environment settings or the process-only production
loader. Never print/store the key, response body or observations; record only
safe status, parsing and counts. Make no retries, market scan, persistence or
holdings access. The live profile is manual and excluded from pytest/CI; its
success establishes technical access at test time, not completeness, permitted
production use or account-wide quota ownership.

The original proposal follows for traceability. This is the concrete proposal for
[#170](https://github.com/daniilnahl/Stock-Tracking-App/issues/170), prepared after
the owner merged #169 and instructed continued work. Main
`1847a155d2e44f1fa82e315e060f557a421e542d` passed
[Foundation 38988510270](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/38988510270).
The original document changed no runtime behavior; the explicit acceptance above
authorizes stage 1's runtime change.

Accepting Option A below would authorize the exact injected API implementation
and tests. Production composition additionally requires the account/use evidence
below; authenticated live probes require a separate explicit instruction. A
merge alone without acceptance of this proposal is not activation permission.
No broader M9 screen, formula, storage/job architecture or M10 is accepted.

## Context and inspected boundaries

[ADR-0015](0015-finnhub-upcoming-eps.md) and EPS-001–004 supply exact Finnhub
calendar observations and `UpcomingEpsService`, with one injected research-date
sample, immutable request context and no historical override. #166/#168 are
merged. Their acceptance explicitly excludes public routes, default/live wiring,
production date selection and account-quota policy.

[ADR-0013](0013-local-read-only-rest-api.md) supplies authenticated local GET
routes, bounded JSON, fixed errors and admission held until workers terminate.
[ADR-0014](0014-local-read-only-dashboard.md) supplies the opt-in local dashboard boundary.
These are reused without authorizing general research commands or writes.
AGENTS §§1, 7 and 28 require owner review of undefined product/API behavior.

Inspected `api/app.py`, `access.py`, `context.py`, `errors.py`, `serialization.py`,
`configuration.py`, `composition.py`, `services/eps.py`, provider adapter/transport,
and corresponding API/service/packaging tests. The existing query guard permits
queries only on `/history`; a new route needs an exact additional exception.
The service and upstream adapter both currently use `ProviderRequestError` for
different failures; mapping all of that class to HTTP 422 would be incorrect.

## Proposed Option A — one explicit provider-symbol request

Add authenticated GET `/api/v1/research/upcoming-eps` to the existing loopback,
single-user API, disabled by default. It uses explicit Finnhub symbols, with no
lookup, saved-row/Stock association, exchange inference or watchlist changes.
API enablement is independent of history and dashboard enablement.

| Input | Proposed exact contract |
| --- | --- |
| Query keys | Exactly one each of `provider_symbol`, `start`, `end`; all required. Reject unknown/duplicate/empty keys and malformed percent/UTF-8 encoding. No analysis-date, source, account key or international switch. |
| Provider symbol | ASCII `^[A-Z0-9][A-Z0-9.-]{0,31}$`, case-sensitive; no trimming or uppercasing. This intentionally narrower HTTP grammar is not a globally unique identity or proof Finnhub supports the symbol. |
| Dates | Exact `YYYY-MM-DD` real calendar dates; inclusive `start <= end`, at most 92 included dates (`(end-start).days <= 91`). No default window. |
| Research date | One server-owned UTC calendar date sampled by the injected date supplier. Require `analysis_date < start`. No client override. |
| Body/method | No body under the existing streaming refusal; GET only, no redirects. |

The UTC reference day is an explicit application policy. Compare vendor date
labels as calendar dates; do not convert their undocumented timezone, infer an
event instant or call them UTC timestamps. Excluding the entire reference day
preserves the conservative same-day exclusion. Retrieval timestamps remain UTC
receipt times, never forecast publication/vintage. The 92-date span is a local
resource limit; it is not a guarantee of a future horizon or complete coverage.
The start may be farther in the future; an empty response remains inconclusive.

Retain all existing bearer, exact Host/Origin, target-size, request-body,
no-store/CSP and error protections. Only this exact route gains query admission;
do not grant a `/research` prefix or suffix exemption. Auth/access and local
syntax/span rejection happen before date, service, budget or provider acquisition.
After valid syntax, disabled acquisition returns `eps_disabled` before the date
supplier, key/environment, provider or account-budget access. The service rejects
a past/same-day start before provider acquisition.

## Exact response projection

Return a typed JSON object with only these fields. Decimal values are strings
using the existing exact serializer, including zero/negative values; null stays
null. Dates are ISO calendar dates; `retrieved_at` is RFC 3339 UTC with `Z`,
preserving any nonzero microsecond precision without rounding.

```json
{
  "provider": "finnhub",
  "provider_symbol": "TEST",
  "start": "2026-10-17",
  "end": "2026-11-16",
  "analysis_date": "2026-10-16",
  "date_convention": "utc-reference-day/vendor-date-labels",
  "observation_kind": "upcoming_release_eps_estimate",
  "coverage": "not_asserted",
  "observations": [{
    "symbol": "TEST",
    "fiscal_year": 2026,
    "fiscal_quarter": 3,
    "release_date": "2026-10-20",
    "release_session": "amc",
    "estimate": "1.250000000000000001",
    "retrieved_at": "2026-10-16T20:00:00Z",
    "provider": "finnhub",
    "source": "earnings_calendar",
    "source_field": "epsEstimate",
    "accounting_basis": "non-GAAP",
    "units": "currency-per-share",
    "currency": null,
    "share_basis": null,
    "published_at": null,
    "fiscal_period_end": null
  }]
}
```

An empty successful tuple produces `observations: []` with the same request
context. It means only that no observations were returned, not no company,
invalid ticker, zero EPS, complete coverage or no upcoming earnings. No cache
freshness, financial comparison, estimate confidence or forecast accuracy claim
is introduced. Revalidate the view before projection and require its symbol,
start and end to equal the parsed request's provider_symbol, start and end.
A structurally valid view for a different request fails with existing
`internal_error`/500, without echoing supplied values; never publish it under 200.
Do not serialize arbitrary dataclasses, raw provider bodies or credentials. Update authenticated static
OpenAPI and its exact schema fixtures without activating dependencies.

## Errors, bounds and execution ownership

Add safe `UpcomingEpsInputError(ProviderRequestError)` for local service symbol,
date and future-range admission. Catch it before its base class and map it to
existing `invalid_request`/422. Invalid injected research-date values are server
dependency failures (`ProviderUnavailableError`/503), not caller blame. Upstream
`ProviderRequestError` remains `provider_unavailable`/503. Preserve existing
callers catching the base category; no global remapping of provider failures.

| Situation | Result |
| --- | --- |
| Disabled | New fixed `eps_disabled`, HTTP 503, message `Upcoming EPS acquisition is disabled.` |
| Missing/invalid process key or denied provider access/auth | Existing `provider_unavailable`, 503; no secret/raw exception. |
| Local EPS budget/cooldown refusal | New fixed `eps_rate_limited`, 429, message `Upcoming EPS request budget is unavailable.` |
| Upstream 429 | Existing `provider_rate_limited`, 429; no retry; engage shared 60-second EPS cooldown. |
| Timeout / malformed upstream / other provider failures | Existing 504 / 502 / safe category mappings, unchanged. |
| Shared or EPS active-operation capacity exhausted | Existing `api_busy`, 503. |

Keep the shared four active-data-operation limit and history's existing one.
Add one active EPS operation, held through actual worker termination, including
disconnect/cancellation. A canceled queued worker acquires no dependencies;
active work cannot release its slot early. No request queue, background retry,
fallback, coalescing or automatic polling is introduced.

Proposed native provider bounds: **5.0 seconds** timeout, **262,144 bytes** maximum
response and **128 rows**. Pass the same byte bound to adapter and native
transport. These are application safety choices, not advertised provider limits.
Retain the existing **4 MiB** final JSON limit and existing request-target bound.
Reject over-limit provider responses without publishing partial observations.

## Budget and credential composition

Own one EPS budget per application instance, using an injected monotonic clock
and lock, shared across all EPS requests and failed attempts. Permit at most
**30 admitted EPS attempts in any trailing 60 seconds**, with one in flight.
At startup refuse EPS attempts for **60 seconds**; on upstream 429 refuse new
attempts for **60 seconds** from receipt. Refuse immediately rather than sleep;
boundary timestamps expire at `age >= 60`. Count a reserved provider-acquisition
attempt even if construction fails. Failed admission consumes no attempt. No
refund/retry is given for errors or cancellation after reservation.

This conservative local budget is not an account-wide limiter. Production uses
one local worker and requires exclusive use of the relevant Finnhub account
quota by this application, including all keys and clients, with no simultaneous
second instance/external consumer. A distinct key alone does not establish a
distinct account budget. Startup quiet time bounds restart
bursts from this application; it cannot coordinate unknown external clients or
prove vendor quota/access. Shared-key or multi-worker use requires a separately
accepted coordinator and remains unsupported. No budget/data table or cache is
added. The startup delay is visible as the fixed local budget error, never a
health failure or automatic sleep.

Propose launch flag `--enable-upcoming-eps`, default false, independent of
`--enable-history` and the existing `--dashboard` flag. When disabled, never inspect a
Finnhub key. When explicitly enabled and an admitted valid operation needs a
provider, read **FINNHUB_API_KEY** from the process environment only; no dotenv,
FMP-key fallback, command-line key, browser storage or query credential. Validate
it at the lazy composition boundary and inject it into the accepted adapter.
Keep credentials out of repr, pickle, logs, errors and configuration exports.
Health, static assets, OpenAPI, disabled and rejected requests remain free of
key/provider acquisition. Existing FMP paths and defaults stay unchanged.

## Access/use evidence and activation gate

The owner reported no paid subscription and subsequently reported obtaining a
Finnhub key (#172). Calendar entitlement and permitted production use remain
unverified. Do not request a key in chat, create an account, purchase access or
scrape. Only the explicit one-request smoke authorization above permits a live
probe in #178; it does not unlock production composition.
The owner must confirm a usable Free account exists, intended local personal
non-business use, and exclusive relevant account-budget ownership before live
composition is enabled.
Account-specific permission or restrictions take precedence; unknown permitted
use keeps production acquisition disabled. No automatic probe runs on startup.

[Finnhub's official terms](https://finnhub.io/terms-of-service), read 2026-10-16,
restrict personal plans to qualifying personal use and restrict sharing data or
derived results without written permission. A loopback API is not by itself
evidence of permitted use. The terms also describe separate account limits and
an additional per-second cap; our local budget is not an entitlement guarantee.
This proposal stores no EPS records and authorizes no redistribution/export.

[Official pricing](https://finnhub.io/pricing) and
[calendar documentation](https://finnhub.io/docs/api/earnings-calendar) returned
JavaScript shells in this round's text fetch. Earlier rendered findings remain
dated in ADR-0015 and [the feasibility report](../milestones/m9-finnhub-eps.md).
Do not treat this text fetch as refreshed schema/plan verification or infer new
rights. A separately authorized, credential-safe single-symbol smoke test may
later verify access, but technical success cannot establish use rights.

## Conditional delivery sequence and verification

1. **Injected API adapter:** after explicit acceptance, implement typed schema,
   exact route/query gate, disabled dependency, service-error distinction,
   serialization and EPS/shared admission. Offline fakes only; no production
   connector. Test all request/error/value/provenance/cancellation boundaries,
   unchanged other routes and cold source/installed-wheel health/schema behavior.
2. **Gated local composition/budget:** after step 1 merge/CI and account/use
   evidence, implement the accepted flag/process key/UTC supplier/budget/provider
   bounds. Deterministic monotonic/civil clocks, injected native HTTP fixtures and
   source/wheel launcher checks; no tests need live credentials or a listener.
3. **Minimal dashboard EPS form:** after stable route/composition, prepare a
   separate reviewed UI task. Explicit provider-symbol/date form and manual
   request, precise raw non-GAAP/provenance/unknown/empty/error presentation; no
   auto-polling, mapping to saved holdings, growth/PEG, screening or daily pick.
   UI design/acceptance is separate from acceptance of this API proposal.

Each implementation objective needs its own milestone-linked issue/branch/PR
and acceptance criteria before work starts. This conditional inventory creates
no blocked implementation assignments. Run canonical targeted/full Python,
Ruff, configured mypy, pip check, staged hygiene and independent review per task;
browser tests only for the later UI. Passing proposal CI, merging it or approving
an API cannot establish a live account, use rights or full M9 completion.
