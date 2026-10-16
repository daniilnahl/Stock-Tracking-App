# Shared dashboard components — issues #144/#146

The local all-text Stock Pixel font, semantic CSS tokens, square controls and
hard shadows apply to every component. Light is the default; the centrally
registered dark theme overrides only palette tokens. CSS remains the single
source of color/spacing/type/focus/radius/motion values. Add a reviewed theme
ID in `src/themes/theme.ts` and its token overrides in `src/styles.css` together.
No per-feature brand colors, font CDN, images of text or decorative flicker.

| Component | Inputs and behavior |
| --- | --- |
| `Button` | Native button attributes, children and optional className. Defaults to type button; pass type submit only for an approved form. Native disabled, labels and handlers remain intact. Use ordinary next-action labels or stable toggle labels with an accurate pressed state. |
| `PageLayout` | title, description, children, optional headingRef. Owns the only main and h1. The shell owns route titles/focus; feature modules provide content rather than another page shell. |
| `Navigation` | current RouteId or null. Reads only the typed central inventory. The three primary items remain Overview, Watchlists and Settings. Active page uses aria-current plus a double underline; all links remain keyboard accessible. |
| `DataTable<Row>` | caption, readonly columns (id/header/render/optional numeric), readonly rows, rowKey and emptyMessage. Native caption/th/scope semantics; exact text is preserved. A named focusable overflow region and visible horizontal-scroll hint preserve phone access. Caller provides namespace/request-local ordinal keys for actual watchlist rows; never deduplicate by symbol. |
| `Chart` | title and optional children. Owns a semantic figure/caption; without children shows explicit unavailability. The history feature supplies finite approximate sparse-point geometry, provenance limits and an accompanying exact-value DataTable. The primitive calculates no financial values. |
| `EmptyState` | title and message rendered as text in a status region. State why data is empty/disconnected/unsupported; do not fabricate values or present unavailable data as zero. |
| `ErrorState` | A safe ClientError from the central client; optional onRetry. Announces the fixed safe message and renders a retry button only when the caller supplies a supported operation. Never pass raw provider exceptions or server text. |
| `FilterPanel` | title and children. Native fieldset/legend grouping. Include only filters supported by a real feature; the shell does not invent filtering behavior. |
| `SettingsField` | label, hint, render callback receiving id and aria-describedby. Attach both attributes to the supplied native input/select. Generated IDs associate labels/descriptions without cloning or HTML injection. |

For example, a presentation-only select:

```tsx
<SettingsField label="Theme" hint="Only this preference is saved locally.">
  {attributes => <select {...attributes} value={theme} onChange={onChange}>
    <option value="light">Monochrome light</option>
    <option value="dark">Monochrome dark</option>
  </select>}
</SettingsField>
```

`DataTable` render callbacks return React text/elements. Do not use
dangerouslySetInnerHTML, inject external HTML, convert Decimal strings to
Number or format unknown currency as USD. Present gains/losses with text and
signs as well as any future semantic colors. No new metric/sorting/filtering
policy is defined by these generic primitives.

The shell shows truthful session/status limits; Watchlists displays explicit
saved-read results and their safe lifecycle states. Exact research
and agent placeholder titles remain above the three status cards; their labels
do not enable a service. Search/add toggles an explanation and a fixed safe
GitHub source-document link. It issues no request and offers no save operation.
The guide components are verified through isolated synthetic tests. There is
no publicly enabled component playground or demo-price stock list. Stored-row
history is an explicit protected workflow with the server rights gate preserved.
The #143 synthetic client check remains separate at
`#client-foundation`, omitted from the three primary navigation items.

## Route and theme contracts

`src/app/routes.ts` defines RouteId, fixed hashes, labels, page titles and the
navigation flag. Hash routing requires no server fallback or router dependency.
Initial/empty hashes select Overview; unknown hashes display a safe unavailable
page without echoing or following their content. Real route changes update the
document title and focus the page heading. Browser back/forward remains native.
The skip link prevents hash routing and focuses the existing main instead.

Only `stock-tracker.theme` (`light` or `dark`) is persisted. Invalid/missing
preferences default to light, irrespective of the system's color preference.
Blocked reads/writes keep a usable page theme and announce that persistence
is unavailable. Only localStorage events can sync the preference across tabs;
sessionStorage/other keys are ignored. No token/private response or route is
persisted. Appearance controls do not claim to configure any server behavior.

Issue #152 adds a separate masked connection form, backed by one App-owned client
and shared memory snapshot. The native password field is uncontrolled; the whole
password-field draft is transferred to strict client validation and cleared on every submit,
disconnect, route unmount and pagehide. No trim/truncation or stored React value
is used. Context changes to disconnected clear replacement drafts before paint.
`connected` in the client means configured only: the control explains that
configuration alone does not verify authentication, and sends no verification/read request.
Protected views use this same client and its safe lifecycle rather
than creating a second session. App unmount/reload or pagehide/restoration clears
the session; only theme can survive. See the README's #152 privacy/test contract.

Issue #145 composes the existing SettingsField, Button, DataTable, EmptyState
and ErrorState primitives on Watchlists. Its exact namespace selector is local
UI state; only explicit Read/Reload calls the shared client. Ordered duplicate
rows expose response-local ordinals and exact Decimal strings. Cancellation
restores focus to Read. Overview keeps its reserved panels and shows only the
current validated namespace's duplicate-inclusive count and observation limits;
it does not duplicate holdings rows or combine namespace counts. Search/add stays a truthful
unsupported disclosure. The README records read/error/precision boundaries.

Issue #146 adds fresh-row detail to Watchlists, using native disclosure for
opaque saved metadata and definition lists for exact inputs/snapshot values.
It adds a grouped paired-date history form and exact sparse OHLC/volume table.
Chart children contain points only for returned dates; geometry is approximate,
and unsafe projections leave the exact table available. Date labels use ordinary
pixel HTML rather than tiny SVG text; axes/points use the high-contrast text token.
Feature styles live in `src/features/stored-row.css`, using existing theme tokens.
Closing detail clears selection/history and focuses the namespace control;
history cancellation focuses Read, and retry focuses Start date before replacing
the transient retry button. All protected operations use the shared client.

## Verification boundaries

`npm test` covers route inventory, single-main/h1/current-page/focus/skip
semantics, approved placeholder order, disclosure safety, exact text/duplicate
rows and escaped external strings, empty/error/group/field/chart semantics,
theme defaults/persistence/invalid preferences/storage failures/cross-tab area
isolation, and the unchanged precise-client tests.

The separate installed-Edge browser profile exercises production assets under
the existing loopback fixture/CSP. It covers light/dark desktop/tablet/phone,
keyboard skip/navigation/back/settings, local-font loading, overflow regions,
literal Decimal/int64 display, blocked storage and reduced motion. It calculates
contrast from actual computed palette tokens: body/muted text at least 4.5:1
and focus/control borders at least 3:1 against both backgrounds/surfaces.
These bounded checks do not certify a full screen-reader audit, every possible
content length, a production service-backed workflow or the M8 exit criteria.
