# ADR-0008: Reject unmatched candidates in the supported ticker scope

## Status

**Accepted, 2026-10-04 (Codex chat local date).** The repository owner instructed:
"introduce functionality where ... through the financial modeling API the stock
... is not found, the stock is discarded and reported as invalid." The Master
recorded that direct human instruction in approved [issue #66](https://github.com/daniilnahl/Stock-Tracking-App/issues/66),
which explicitly identifies this DATA-006 specification interpretation change.
This later instruction supersedes the earlier decision to retain definitive
network unknown evidence as an M2 exit blocker for this scoped product behavior.
Acceptance authorizes the bounded implementation, not agent merges or milestone
closure. Human merge, exact-head/main CI and final #56 exit verification remain
required.

## Context

ADR-0007 reserves InvalidTickerError for local invalid input and classifies a
successful search without an exact supported identity as inconclusive. Its
public documentation evidence does not establish exhaustive search results or
exact-match ordering. The owner now chooses rejection as a product rule despite
that limitation. No new claim about the provider's completeness is made.

## Decision

- Keep normalized input, Stable search-symbol query, limit=100 and NASDAQ scope.
  Validate the successful response's entire array and every identity/metadata
  field before deciding. A unique exact normalized symbol and exact NASDAQ
  exchange succeeds; duplicate exact identities or malformed rows remain
  ProviderResponseError, even if another row matches or no row matches.
- A completed HTTP 200, schema-valid search with no exact supported match raises
  InvalidTickerError. This includes empty arrays, unrelated/substring results,
  exchange mismatch and a full-limit array without a match. It means invalid
  for this application's supported lookup, not globally nonexistent.
- check_ticker retains its two arguments and returns False for InvalidTickerError
  from either local syntax or this scoped no-match decision. It never reads or
  writes CSV, trusts cached positives, or stores a negative cache.
- Both existing CLI add flows report invalid ticker and return before creating
  the candidate, fetching profile/period data, prompting for holdings, adding
  or saving. Preserve their existing exit behavior. "Discard" means rejection
  of the new candidate, never deletion or modification of existing holdings or
  persisted user data. Refresh and explicit removal behavior do not change.
- Authentication/access/request failures, HTTP 404, rate limiting, timeout,
  outages, malformed JSON/schema and programming errors retain their existing
  categories. Empty quote/profile/period responses remain unavailable data.
  No infrastructure failure becomes invalidity.
- Keep the exported InstrumentLookupInconclusiveError for compatibility and
  other provider implementations; FMP's completed valid no-match search no
  longer emits it. Keep fixed safe error messages and all public signatures.

This supersedes only ADR-0007's successful no-match classification, local-only
InvalidTickerError meaning, corresponding wrapper/caller wording and the
definitive unknown evidence gate as applied to this product rule. Its numeric,
time, reliability, credential, metadata, CSV, history and architecture contracts
remain accepted unchanged. SRS DATA-006 records this scoped interpretation.

## Consequences and verification

Incomplete or truncated search, missing exact-match ordering guarantees and
the NASDAQ-only scope can reject a real instrument. This is an explicit accepted
false-negative risk and application limitation, not verified API completeness,
global truth or broader exchange support. A user may retry; no negative cache
prevents reconsideration.

Tests must exercise real adapter parsing under synthetic HTTP for exact/no-match
and every malformed/failure category; real wrapper no-match must return False.
Both CLI add flows must preserve existing ordered holdings and trusted saved
bytes while making only the lookup request and reporting invalidity. Existing
financial, provider, wheel, boundary and hygiene checks remain required. #66's
human merge/main CI and final #56 review precede any M2 completion claim.
