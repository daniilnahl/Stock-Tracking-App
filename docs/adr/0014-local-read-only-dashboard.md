# ADR-0014: Local read-only dashboard

## Status

**Proposed — owner acceptance required.** Prepared 2026-10-14 in response to
the request to start M8. This request authorizes planning; it does not select
previously unresolved D3 architecture. SRS §23.8/UI801–829 remains proposed.
ADR-0013 accepts M7 only. This proposal does not modify that acceptance.

## Decision requested: Option A

Accept SRS §23.8 within this explicitly read-only capability subset and the
applicable cross-milestone requirements. Approve the following D3 decisions:

- React, TypeScript and Vite under `frontend/`; npm and a single committed
  `package-lock.json`. Preserve Python 3.11/3.12 and pip/pyproject unchanged.
  Select and document supported Node LTS and exact dependency pins in the
  scaffold PR after checking official support/security documentation; no
  system installation is authorized by this ADR.
- Vitest, React Testing Library and a separate Playwright browser test profile.
  Default Python tests remain independent of browsers and internet access.
- One typed API layer and native request state/coalescing/cancellation. No
  overlapping state libraries. Generate types from the reviewed M7 schema;
  runtime validation rejects incompatible data before publishing a view.
- Light monochrome default, dark alternative, semantic CSS tokens, tabular
  numbers, explicit text/sign gain/loss, WCAG 2.2 AA target and reduced motion.
  Persist only theme preference locally. No copied reference artwork.

### Browser security and distribution

M7 currently rejects every Origin header. Do not weaken that default. Add an
explicit opt-in dashboard composition/launcher option, separately tested from
default API operation, serving a locally built bundle at the existing fixed
loopback listener. Never start a second public listener or use wildcard CORS.

Dashboard mode accepts absent Origin for authenticated nonbrowser clients and
only exact matching same-origin browser requests: Host `127.0.0.1:8000` pairs
with Origin `http://127.0.0.1:8000`; Host `localhost:8000` pairs with Origin
`http://localhost:8000`. Refuse null, duplicates, mismatches and all other
origins before dependency acquisition. Default M7 mode keeps refusing every
Origin. No development proxy strips an Origin to bypass this boundary.

Public static routes serve only packaged, allowlisted build assets. Path
traversal, arbitrary file serving, source maps, application state, credentials
and token substitution are prohibited. Retain safe error/log behavior and
no-store API responses. Apply a restrictive same-origin CSP (no inline script,
remote assets or framing) and no-referrer policy. No service worker.

The operator enters the existing local API bearer token into a masked control.
It stays only in page memory and Authorization headers; never persist it,
bundle it, put it in a URL, log it or capture it in a demo. Reload/disconnect
clears token and all private response state; disconnect aborts requests and
invalidates pending results. Authentication failure clears private views.
Provider credentials remain server-side. This local trust model does not
protect against another process under the same OS user or browser extensions.

Use production-built assets for integration demos, not a separate-port Vite
server. Component development may use schema fixtures with a conspicuous demo
label and no real data/token. Build/distribution checks must verify the wheel
contains intended assets and that API-only installation/help remains usable
without frontend build tools. No automatic build/download during Python import.

### Day-one capabilities

| View | Supported behavior |
|---|---|
| Overview | Entry counts and saved observation status only |
| Watchlists | Both M7 namespaces, preserved order and duplicate rows |
| Stored-row detail | Existing saved fields and snapshot values with unknown currency/freshness labels |
| History | Existing exact stored-row M7 endpoint, paired dates, sparse raw bars and accessible data table |
| Settings | Theme and memory-only local API connection |

No add/remove/current market refresh, arbitrary-symbol lookup, verified company
profile, aggregate financial analytics, research, AI or hosted operation.
Reload means reread saved data, never fetch current quotes. UI820 is satisfied
only for operations supported by M7; unsupported operations are omitted.
UI821 does not authorize new backend capabilities. UI822 permits omission.
Live history remains disabled pending the separate ADR-0013 rights gate.

Keep exact Decimal strings for display/storage; do not pass them through
JavaScript Number. JSON volume can reach signed 64-bit maximum: decode it
losslessly before native JSON parsing can round it. Test maximum volume and
high precision decimals. Any chart-only numeric projection must be finite,
documented as approximate, and accompanied by the exact-value table; never
calculate new financial metrics. Missing values and zero stay distinct.

Namespace plus ordinal selects a request-local row, not a stable identity.
Reload the list before opening detail; discard detail on list reload, namespace
change or disconnect. If the selected ordinal disappears or its Stock changes,
clear selection and require a new choice; do not silently select a shifted row.
Before publishing history, verify its Stock/ordinal against the current request
selection and generation. Identical duplicate rows still have no stable identity
across separate requests; label detail as the returned request-local selection.
Render all external text as text. Never infer USD,
freshness, adjusted returns, contiguous sessions or provenance from opaque
metadata. Failure/offline/loading/empty/unsupported/success states are explicit;
failed reload cannot relabel old observations current.

## Alternatives

1. Option A above: a scoped extension of M7 access and static composition with
   default API behavior preserved. Recommended for one local application.
2. Separate frontend origin: requires another reviewed CORS/access/distribution
   contract and listener; no present requirement justifies the added surface.
3. Postpone M8: leaves M7 unchanged and defers frontend toolchain decisions.

## Acceptance and verification gates

Owner explicitly accepts scoped M8 requirements and Option A; proposal is
owner-merged and required main CI passes before runtime issues begin. Agent
merges remain prohibited. Each implementation issue has one branch/PR and a
visual demo using isolated synthetic state, labeled as such. Independent review
covers API boundary regression, precise numbers, cancellation, themes, keyboard,
responsive layouts, accessible names/contrast and clean installed distribution.
No milestone completion until required issues close, PRs are owner-merged and
exit evidence/main CI pass. An illustrative preview is not a working frontend.
