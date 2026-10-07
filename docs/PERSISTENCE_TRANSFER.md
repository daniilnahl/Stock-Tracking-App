# Safe neutral transition and SQLite backup/restore

**M3 complete, 2026-10-06.** [Completion evidence](milestones/m3-exit-evidence.md)
records source/installed-wheel neutral import, checked backup/new-destination
restore and fresh Portfolio/CLI reads, with original state preserved.

The utilities in `stock_tracker.persistence.transfer` implement accepted
ADR-0009 for local reviewed data. They are Python functions, not new CLI commands.
Never run them against real user files as part of automated tests.

## Manual reconstruction

Preserve original `watchlist.pkl` and `daniils_stock_methodd.pkl` files unchanged.
The supported transition does not read, execute or deserialize either file.
There is no pickle extraction/conversion utility. Reconstruct holdings and display
metadata manually from independently trusted records, review identities and
quantities, and write a neutral UTF-8 JSON document. Information available only
inside an inaccessible legacy file may be unrecoverable through this procedure;
missing holdings/metadata are not inferred, silently filled, or certified.

The exact top-level keys are `format`, `version`, `portfolios`, `watchlists`.
`format` is `stock-tracker-neutral`, `version` is integer `1` (never boolean),
and both collections are arrays. A minimal valid document is:

```json
{
  "format": "stock-tracker-neutral",
  "version": 1,
  "portfolios": [
    {
      "id": null,
      "name": "Reviewed portfolio",
      "positions": [
        {
          "stock": {"symbol": "ABC", "name": "Example", "exchange": "NASDAQ"},
          "quantity": "0.2500",
          "average_cost": "100.0000"
        }
      ]
    }
  ],
  "watchlists": [
    {
      "namespace": "menu_watchlist",
      "name": "Reviewed watchlist",
      "entries": [
        {
          "stock": {"symbol": "ABC", "name": null, "exchange": null},
          "quantity": "0",
          "average_cost": null,
          "current_price": null,
          "sector": null,
          "country": null,
          "currency": null,
          "market_cap": null,
          "price_1d": null,
          "price_5d": null,
          "price_30d": null,
          "price_3m": null,
          "price_6m": null,
          "price_1y": null,
          "price_3y": null,
          "price_5y": null
        }
      ]
    },
    {"namespace": "daniils_stock_method", "name": "Other reviewed list", "entries": []}
  ]
}
```

Every object must contain exactly its illustrated keys. Stock identity uses exact
symbol/name/exchange with optional `null` name/exchange; identities must already
be reviewed. Names/namespaces are nonblank with no surrounding whitespace.
No provider lookup or exchange normalization occurs. IDs are `null` for local
allocation or canonical integer strings such as `0`, `-7`, `12`; plus signs,
leading zeros and `-0` are invalid. Explicit IDs, including negative/zero IDs,
are inserted before allocating `null` IDs above all existing positive IDs.

Ownership and quotes use plain signed decimal strings with optional fraction or
exponent, requiring finite nonnegative values. Whitespace, underscores, money
symbols, percent decorations, NaN/Infinity, JSON numbers and booleans are invalid.
Exact Decimal values, exponent/trailing-zero precision and entry order/duplicates
remain intact; optional plus signs/leading zeros in decimal input are represented
through `str(Decimal(value))`, rather than preserved as raw JSON spelling. Optional
watchlist average cost is `null` only for zero quantity (unowned); numeric `0`
cost represents ownership. Nullable quote remains different from valid zero.
All metadata fields are explicitly present as string or `null`; empty strings
and display sentinels may remain metadata. Stored quote/metadata are last-observed
state with no freshness claim. Do not include runtime keys, configurations,
clients, derived returns or arbitrary class/object fields.

Input limits are at most 10 MiB UTF-8 bytes, 10,000 aggregate records, 100,000
total positions/watchlist entries, 64 nested object/array levels and 4,096
characters in each string (including keys). Duplicate object keys, duplicate
explicit IDs/namespaces, unknown/missing fields and nonstandard JSON constants
are refused. Strings must be representable as UTF-8. These are transfer limits;
repository-supported IDs/strings beyond them cannot be transferred through this
format and are never truncated.

Use explicit reviewed paths:

```python
from pathlib import Path
from stock_tracker.persistence.transfer import import_neutral_state

import_neutral_state(Path("reviewed-neutral.json"), Path("stock_tracker.sqlite3"))
```

The importer validates the entire source before opening or writing the destination
database, validates an
existing destination, then initializes/adds all records in one transaction.
Any existing explicit ID or namespace is a collision; it never replaces or
merges existing records. A collision or failed write leaves existing committed
schema/rows unchanged. JSON source and legacy files stay untouched. A failed
first write may leave an empty version-zero file; the standard migration rule
can initialize an empty file later. No automatic deletion/recovery is performed.
An imported namespace is authoritative for the included CLI integration;
its preserved legacy file does not block that namespace.

## Backup and restore

```python
from pathlib import Path
from stock_tracker.persistence.transfer import backup_database, restore_database

backup_database(Path("stock_tracker.sqlite3"), Path("new-backup.sqlite3"))
restore_database(Path("new-backup.sqlite3"), Path("new-directory/stock_tracker.sqlite3"))
```

Choose a new destination file in an existing directory. Existing destinations,
including dangling symlink directory entries, are refused. Resolved-path and
existing-file identities reject same-file, symlink and hardlink aliases before
writes. Exclusive file reservation prevents overwriting a file created after the
initial check; the SQLite destination is opened in existing-file mode. The reserved
file identity is checked around opening to refuse detected path replacement. This is
local single-user operation, not a guarantee against hostile filesystem changes.

Backup uses SQLite's backup API from one read-only validated snapshot, including
committed state held in active journals/WAL; copying the bare database bytes is
insufficient. Schema, SQLite integrity, foreign keys and every Portfolio/watchlist
record are validated on the source snapshot and resulting copy. Unsupported
versions, corrupt ownership/identity/metadata/ordinals or missing source fail
safely. Restore performs the same checked copy without upgrade or replacement.
Connections close on success/failure. Failed copying/verification may leave the
newly reserved file unusable; preserve the source, do not treat that destination
as a verified backup, and choose another new destination for a later attempt.
No existing/source file is deleted or overwritten as recovery.

Before selecting restored state, stop application processes. Create/select an
empty new directory yourself, restore to its new `stock_tracker.sqlite3`, verify
it offline, then launch the existing application with that directory as cwd.
SQLite CLI integration is included. Keep the old directory/database untouched.
Never replace an active database in place. The owner chooses access-controlled
backup storage and retention; no encryption, scheduling or automatic relocation
is promised. A verified backup is required before a future explicit upgrade of
an existing database; current schema version 1 is not upgraded by these utilities.

Run `python -m pytest tests/test_persistence_transfer.py tests/test_packaging.py -v`.
Tests use fictional neutral/opaque legacy fixtures and temporary SQLite only,
including exact limits, aliases, collisions, partial rollback, active WAL,
concurrent consistent snapshot, complete record validation and copy failures.
Installed-wheel smoke imports/copies/restores temporary state with transport
guards. [CLI storage](CLI_PERSISTENCE.md) describes merged #73 behavior;
[M3 audit evidence](milestones/m3-exit-evidence.md) records combined source/wheel
restart through neutral import, backup and restoration and completed closure gates.
