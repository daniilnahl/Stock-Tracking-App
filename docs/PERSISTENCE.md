# Persistence operations

The accepted [ADR-0009](adr/0009-persistence-contracts.md) defines M3's contracts.
Issue #70 supplies the connection boundary and initial schema. Repositories,
CLI integration and transfer/backup utilities remain separate issues. Existing
CLIs still use legacy storage until integration; initialization does not convert it.

## Location and explicit initialization

CLI composition will select `Path.cwd() / 'stock_tracker.sqlite3'`. Infrastructure
functions receive an explicit `pathlib.Path`; there is no environment override,
home fallback or automatic parent-directory creation. Local `.sqlite3` files and
their journal/WAL/shared-memory sidecars are ignored by Git.

For an explicitly selected new or empty database in an existing directory:

```python
from pathlib import Path
from stock_tracker.persistence.migrations import migrate_database

migrate_database(Path('stock_tracker.sqlite3'))
```

This is an explicit write. Tests select isolated temporary paths; agents must
not run it against real user files for verification. Failed initialization may
leave an empty version-zero file. No automatic deletion/replacement occurs.
Re-running initializes an eligible empty file or validates the current schema
without replacing data.

## One migration runner

`stock_tracker.persistence.migrations` alone owns numbered steps and
`PRAGMA user_version`. Migration 1 creates `portfolios`, `positions`, `watchlists`
and `watchlist_entries` plus version 1 in one explicit transaction. Connections
enable and verify foreign keys before transactions and use SQLite's default
five-second timeout, without retries/WAL tuning. Data inputs require bound query
parameters. Subsequent repository mappings preserve accepted text Decimal/ID values.

Version zero accepts only an empty schema. Unversioned populated files, corrupt
files and future/unknown versions fail with safe application errors. Version 1
checks complete canonical DDL: types, nullability, keys, ordinal constraints and
foreign-key cascade declarations. Case/spacing differences are accepted;
alternate DDL or extra application tables/views/triggers/indexes are unsupported.
SQLite's own internal objects are allowed. No repair/deletion is attempted.

Reads use encoded `mode=ro` URIs. An absent database under an existing parent
yields absence without creating state. Missing parents and SQLite/filesystem
failures raise fixed safe errors. Reads cannot silently upgrade old versions.
Connections close on success/failure; programming exceptions propagate.
Package/record imports perform no database IO.

## Caller-owned transactions and future upgrades

Internal `ensure_schema(connection)` and `validate_schema(connection)` require
an active transaction with enforced foreign keys and never commit caller work.
Writers use `transaction(connection, write=True)` (`BEGIN IMMEDIATE`); readers
use `transaction(connection)` (`BEGIN`) for a stable snapshot. Nesting is rejected.
Owned transactions roll back operation or commit failures. Future neutral import
must initialize and insert on the same connection/transaction rather than call
the separately committing public runner.

No upgrade beyond initial version 1 exists. Future upgrades require verified
backup, data-preservation tests and documented before/after behavior. Issue #74
owns safe neutral import and checked SQLite backup/restore to a new destination.
Until implemented, no backup utility or legacy recovery method is available.
Preserve original legacy files; never execute/deserialize them for migration.
