# Historical cache operations — issue #90

The accepted ADR-0010 cache is disposable provider data, separate from holdings,
SQLite migrations, neutral transfer and database backups. This issue supplies
explicit-path storage and a historical-only decorator. Issue #91 adds the IO-free
historical factory and additive Stock.get_price_history capability. Issue #92
renders observed raw closes as unconnected markers with unknown historical
currency, range/count labels and a split-price warning. CLI selection and safe
CLI error handling remain #93. Current-data composition
still has history TTL 0.0, quote TTL 0.0 and stale fallback False.

Callers explicitly inject a repository path, UTC clock, receipt loader and
ProviderPolicy. The historical factory uses the cwd-relative
`stock_tracker.history-cache.json` sidecar and 3600-second history TTL. Exact
normalized symbol/range/raw mapping keys reuse fully validated observations;
hits preserve original receipt time and return fresh lists of immutable numeric
bars. Expiry at exactly one hour or a backwards clock misses. Zero TTL bypasses
all cache IO. Failed retrieval never returns stale data or modifies the cache.

The facade accepts keyword-only start/end dates, both or neither. Defaults span
five calendar years through the prior UTC calendar date, clamping February 29 to
February 28 where needed. An exact known NASDAQ exchange is required before
credentials, factory construction or cache access. Unsupported saved identities
raise MarketDataUnavailableError without changing holdings. Range selection uses
a monkeypatchable UTC clock; the provider-independent boundary validates raw,
nonempty, ordered in-range bars and returns a fresh list without retaining data.
It performs no quote/profile/summary refresh and stores no historical runtime
objects or bars in holdings. Current currency metadata is not historical proof.

JSON preserves Decimal text without quantization. The complete file is bounded
to 16 MiB, 32 entries, 3660 bars per entry and 4096 characters per string.
Individual oversized successful results return uncached before insertion or
eviction. Successful insertions discard expired entries, then evict the oldest
receipt timestamps with lexical key tie breaking until bounds fit.

Missing files are read misses; constructors and reads create no files. Invalid,
unsupported, unreadable files, symlinks, directories and missing parent directories
raise the fixed `Historical cache operation failed.` error before upstream
retrieval. Unknown existing contents are preserved. There is no automatic repair
or deletion command: preserve the suspect file and ask for a reviewed recovery
decision; do not treat it as holdings, execute it or unpickle it.

Writes use a uniquely owned same-directory temporary file, flush and close it,
recheck the existing target's type and full format, then atomically replace a
validated cache or absent target. Failure preserves the prior target and cleans
up only the operation's own temporary file. Atomic replacement prevents torn
reads; it promises neither power-loss durability nor protection against an
adversarial filesystem. Simultaneous writers may lose cache entries; no locks or
cross-process request suppression are promised. Holdings remain separate.
