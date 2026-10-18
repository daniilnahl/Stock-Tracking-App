# ADR-0018: User-defined stock criteria editor

## Status and authorization

**Accepted for this bounded editor, 2026-10-17.** After merging the ownership
change in [ADR-0017](0017-user-criteria-taurus-discovery.md), the owner instructed
continued work. Asked which parameters to support, the owner answered that users
may choose whatever parameters they want and customize their range values.
This authorizes [#176](https://github.com/daniilnahl/Stock-Tracking-App/issues/176)'s
custom descriptive criteria editor rather than a fixed provider-metric registry.
It does not approve evaluation of arbitrary financial metrics or agent execution.

## Representation and interpretation

Users enter a parameter name and either an inclusive numeric range or a textual
requirement. Numeric rows also require explicit unit/context text; the application
does not infer USD, percent, EPS basis, period, taxonomy or financial meaning from
the name. A label such as EPS or market cap remains a user request, not an
implemented/calculated metric or proof source data can satisfy it. Existing EPS
comparison restrictions remain intact. M10 must resolve and verify semantics
and evidence before claiming a match; user text is data, never executable agent,
URL, SQL, HTML or system instructions.

The prepared data-only envelope has exactly this shape (examples are synthetic
input illustrations, not a preset or recommended threshold):

```json
{
  "schema_version": 1,
  "kind": "user_stock_criteria",
  "match": "all",
  "criteria": [
    {
      "parameter": "Custom numeric parameter",
      "kind": "range",
      "unit": "user supplied units and period context",
      "minimum": "-0.25",
      "maximum": "1.250000000000000001"
    },
    {
      "parameter": "Custom text parameter",
      "kind": "text",
      "value": "user supplied requirement"
    }
  ]
}
```

`match` is explicitly selected as `all` or `any`, initially shown as all; no
evaluation occurs in M9. Range endpoints are exact entered plain decimal strings
or null for an omitted endpoint; at least one is required. Grammar is
`^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$`, maximum 128 characters. No exponents,
NaN/infinity, grouping, plus sign or floating-point conversion. Signed zero and
trailing fractional zeros are preserved. Validate minimum <= maximum using exact
decimal-string comparison only; this is input consistency, not financial math.

Names and units/context are nonblank strings of at most 80 characters; text
requirements are nonblank strings of at most 256 characters. Reject control
characters and malformed types without silently dropping data or normalizing
entered values. Allow duplicate parameter names in ordered rows; they may express
different periods/contexts. One to 20 rows can be prepared. No hidden thresholds,
parameter list, ranking, universe, source claims, run IDs or financial formulas.

## UI and lifecycle

Add a `Stock criteria` page to the existing local dashboard navigation and a
clear overview entry point. Reuse established pixel typography, monochrome
themes, components and accessible keyboard/mobile layout. Provide add/remove,
row type selection, minimum/maximum or text inputs, explicit match mode,
`Prepare criteria` and `Clear criteria` controls. Fields start blank.

Preparation validates, focuses the first invalid field and shows accessible
field errors. A successful action makes an immutable exact snapshot and renders
a read-only preview labeled **Prepared — Taurus search unavailable**. Subsequent
edits mark the old snapshot outdated, without mutating it or presenting it as
current. Clearing resets draft and snapshot. Browser navigation within the app
preserves tab-memory state; reload/pagehide clears it. No criteria localStorage,
sessionStorage, file, SQLite, server persistence or export/import is introduced.
Existing theme persistence remains the only browser storage setting.

The editor works without configuring an API token. Preparation, editing,
navigation and clearing perform no fetch, provider enumeration, agent call or
network operation. No search button is enabled, suggested stock fabricated or
criteria-match claim displayed. The existing recommendation and Taurus result
panels remain unavailable. No new public API/launcher contract is needed for this
local nonexecuting editor, and ADR-0016's separate proposal is not accepted here.

## Implementation and verification

Implement a pure typed preparation/validation module, accessible editor and
app-owned tab-memory state; no backend wrapper, dependency or storage migration.
Test exact large/negative/zero decimals, missing/inverted/malformed ranges,
custom names/text escaping, units, row limits, all/any mode, snapshot immutability,
staleness, navigation and reload clearing. Prove no provider/API/agent requests.
Rebuild the deliberately packaged dashboard; preserve its closed asset set/CSP.
Run frontend unit/type/build/package/browser and actual source/installed-wheel
integration profiles sequentially with canonical Python checks, staged hygiene
and independent review. No live credentials, data or model/provider calls.
