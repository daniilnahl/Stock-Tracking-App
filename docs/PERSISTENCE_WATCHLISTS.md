# SQLite watchlist repository and facade mapping — issue #72

`stock_tracker.persistence.sqlite_watchlists.SQLiteWatchlistRepository(path)`
implements the accepted watchlist protocol using the single ADR-0009 schema and
migration mechanism. Construction performs no IO. `get(namespace)` returns a
fresh complete record or `None`; `list()` orders records by exact namespace;
`save(record)` creates or atomically replaces only that namespace. Namespaces
are case sensitive and independent of mutable display names. Entry order and
duplicates remain intact; no Portfolio or Position row is created implicitly.

Each operation owns and closes a connection. Reads validate schema and decode
parents/entries in one explicit snapshot. Writes validate the complete candidate
before opening SQLite, then initialize/validate schema and replace the aggregate
inside `BEGIN IMMEDIATE`. Failure rolls back schema/version/rows together.
Decimal strings preserve exponent and trailing zero precision; nullable cost
means unowned only at zero quantity, while numeric zero cost retains ownership.
Nullable quote remains distinct from a valid zero quote. Malformed saved rows,
noncontiguous ordinals and orphan entries reject the complete requested result.
Missing-file reads create no state; missing-parent paths fail safely. Strings
must be representable as UTF-8 for SQLite binding; no normalization or lossy
conversion is performed. Five-second SQLite lock timeout and last-successful-save
semantics remain those accepted in ADR-0009; no optimistic concurrency is added.

Explicit facade functions live in
`stock_tracker.compatibility.watchlist_persistence`:

```python
record = watchlist_to_record(watchlist, "menu_watchlist")
repository.save(record)
restored = record_to_watchlist(repository.get("menu_watchlist"), runtime_key)
```

Callers must handle an absent record before restoring. Restoration requires the
current runtime key argument, which may be `None`; it does not load configuration
or request market data. Identity `None`/`N/A` is mapped to domain `None` at the
facade boundary. Missing price restores as `None`, unowned cost as `-`, and
snapshots/returns are recomputed from authoritative inputs. Runtime keys, clients,
configuration and derived returns never enter persisted records. Display metadata
remains exact string/None without reverse parsing or freshness claims.

Run `python -m pytest tests/test_sqlite_watchlists.py tests/test_packaging.py -v`.
Tests use fictional inputs and isolated temporary SQLite files, check full input
validation/rollback/corruption/independent namespaces, and restore real facades
offline. Coordinated concurrent writes prove reads retain matching parent/entry
snapshots. Wheel smoke builds/installs offline and verifies both new modules and
real restored precision/returns from the installed package. No real database,
legacy file, provider credential, or live transport is used.

This change supplies reusable storage/mapping only. Existing CLI storage wiring,
legacy refusal/neutral transition, backup/restore and complete milestone restart
verification remain issues #73–75. No CLI command/contract, domain formula,
dependency, schema or public record/protocol contract changes here.
