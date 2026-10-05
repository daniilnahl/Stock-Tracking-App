# ADR-0009: M3 persistence contracts and safe legacy transition

## Status

**Accepted, 2026-10-05.** The owner stated **"Option A approved and PR merged"**
in the Codex milestone chat, accepting Option A at exact reviewed commit
`8e525177c7443fc92e1afc6b42e573ad3a3c43b2`, including the legacy filename/behavior
extension. The [Master's acceptance record](https://github.com/daniilnahl/Stock-Tracking-App/issues/68#issuecomment-5999983033)
faithfully records that human instruction; it is not separately human-authored
GitHub acceptance. Owner-merged [PR #77](https://github.com/daniilnahl/Stock-Tracking-App/pull/77)
is on main at `48944f98938639628cfe216d4d0bc6883f0f5f26`; all five required checks
passed in [Foundation run 37351164698](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37351164698).
This documentation-only proposal addresses [issue #68](https://github.com/daniilnahl/Stock-Tracking-App/issues/68)
in [M3 — Persistence](https://github.com/daniilnahl/Stock-Tracking-App/milestone/4).
The original proposal wording below preserves the exact accepted contract.
#68 is closed; runtime implementation remains separately scoped #69–75 work.
Acceptance does not authorize agent merges, certify restart persistence, or
authorize execution of migration against real user files.

The governing sources are SRS §§5, 6, 8, 9, 12 and 23; ADRs 0005–0008;
AGENTS.md; TESTING.md; and FC-001–004, FC-110 and missing-data rules.
The [M3 plan](../milestones/m3-plan.md) maps dependent implementation issues.

## Context

Both root CLIs load cwd-relative pickle files at import and overwrite them on
successful add/remove/refresh. They store separate Watch_list collections:
watchlist.pkl and daniils_stock_methodd.pkl. A Watch_list is not a Portfolio.
ADR-0006 preserves ordered duplicates and distinguishes an unowned entry
(quantity zero, cost sentinel '-') from a Position with numeric zero inputs.
Domain Portfolio has ordered Positions and an optional integer id. No accepted
schema, repository interface, migration runner or backup policy exists.

The SRS already selects SQLite and prohibits pickle as primary long-term storage.
PERS-008 and ARCH-006 require decisions before the first schema. This proposal
preserves model semantics and existing commands while replacing their storage.

## Proposed decision: boundaries and location

Use standard-library sqlite3, with stock_tracker.persistence containing models,
protocols, sqlite repositories, migrations and transfer utilities. Compatibility
mapping stays outside domain. Add that package to existing explicit setuptools
discovery. Keep pip, Python 3.11/3.12, dependency pins, configured mypy scope and
existing root modules. Domain imports no persistence/configuration/UI modules.

Repository constructors accept a pathlib.Path and perform no IO. CLI composition
selects Path.cwd() / 'stock_tracker.sqlite3', resolved once per process. No new
environment variable, implicit home-directory fallback or provider dependency.
Tests and transfer utilities always receive explicit temporary paths.

Read operations on a missing file return absence/empty collections without
creating a file or directory. CLI help and empty local display perform no write.
A first successful write initializes the schema. Existing files must be opened
without accidental create-on-read; malformed or unsupported databases raise a
safe error, never become an empty replacement. A missing parent directory fails
explicitly; application code does not silently create directory trees.

The CLI collections use independent namespaces 'menu_watchlist' and
'daniils_stock_method'; their mutable display name is not their storage key.
Keep Watch_list and Portfolio distinct. No watchlist entry implicitly creates a
Portfolio or Position. Store real domain Portfolios separately for later callers.

### Legacy behavior extension requiring express approval

Maintained CLIs stop calling pickle.load/dump, including at import. Their new
WATCHLIST_FILE points to the shared SQLite filename; namespaces keep state
independent. Existing command names, prompts, validation, display and provider
call sequence remain. Existing pickle files are never opened, deleted or rewritten.

If a namespace is absent and its corresponding legacy filename exists, refuse
the load/write with LegacyStatePresentError and guidance to preserve the original
file and use the documented manual neutral-data transition. Do not silently show
an empty replacement and permit its save. An existing namespace is authoritative
after an explicit neutral import; the untouched old file does not block it.
Only existence is inspected; existence must not trigger deserialization.
Help remains usable without loading state; #73 must move load behind command
execution and preserve the testable root load_watchlist/save_watchlist surface.
When no legacy file exists, a genuinely new namespace may start empty.

This expressly extends ADR-0006's M1 filename and pickle-IO preservation. Root
Stock.__getstate__/__setstate__ and trusted synthetic compatibility tests may
remain; they are not application storage or a migration utility.

## Exact records and repository interfaces

Proposed frozen records in persistence.models:

```python
@dataclass(frozen=True)
class WatchlistEntry:
    stock: Stock  # stock_tracker.domain.Stock
    quantity: Decimal
    average_cost: Decimal | None
    current_price: Decimal | None
    sector: str | None
    country: str | None
    currency: str | None
    market_cap: str | None
    price_1d: str | None
    price_5d: str | None
    price_30d: str | None
    price_3m: str | None
    price_6m: str | None
    price_1y: str | None
    price_3y: str | None
    price_5y: str | None

@dataclass(frozen=True)
class WatchlistRecord:
    namespace: str
    name: str
    entries: tuple[WatchlistEntry, ...]

class PortfolioRepository(Protocol):
    def create(self, portfolio: Portfolio) -> Portfolio: ...
    def get(self, portfolio_id: int) -> Portfolio | None: ...
    def list(self) -> list[Portfolio]: ...
    def save(self, portfolio: Portfolio) -> None: ...
    def delete(self, portfolio_id: int) -> bool: ...

class WatchlistRepository(Protocol):
    def get(self, namespace: str) -> WatchlistRecord | None: ...
    def list(self) -> list[WatchlistRecord]: ...
    def save(self, record: WatchlistRecord) -> None: ...
```

Concrete constructors are SQLitePortfolioRepository(path: Path) and
SQLiteWatchlistRepository(path: Path). Each operation owns/closes its connection;
no persistent global client or destructor lifecycle. list returns fresh records:
Portfolios ordered by numeric id, watchlists by exact namespace; entries retain
ordinal order. No references to a mutable caller list are retained.
Each get/list reads schema, parent and child rows in one explicit read transaction
and SQLite snapshot; separate uncoordinated SELECTs must not combine pre-save
names with post-save entries. A malformed row rejects the whole requested result,
including list, rather than returning a partial collection.

Validate complete candidates before database writes, including mutated Portfolio
lists. Names/namespaces are nonblank strings without surrounding whitespace.
Identity follows domain Stock exactly, without case/exchange normalization.
Decimals must be actual finite nonnegative Decimal objects. Optional average_cost
is absent only when quantity is zero: absence denotes unowned state; numeric
zero denotes a Position. current_price=None denotes unavailable; Decimal(0)
remains a valid quote and is never substituted for absence.
Legacy metadata fields are string or None; they are display records outside
domain, not numeric inputs. Empty text and literal display sentinels may remain
in these metadata fields. Identity None/'N/A' mapping stays at the facade boundary.

Map records to root Stock with current runtime configuration, never saved keys.
Recompute snapshots/returns; do not store total_return. Retain saved last-observed
quote and display metadata for offline display without fetching or claiming
freshness. Missing price restores as None; unowned average cost restores as '-'.
No market-cap reverse parsing, cache TTL, FX or financial metric is introduced.

### IDs, uniqueness and deletion

Portfolio id is stored as canonical decimal integer TEXT, preserving explicit
Python integers including zero/negative values rather than imposing SQLite's
signed-64-bit identity range. Bool is invalid. create with an explicit unused id
preserves it; a collision fails, never updates. create with id=None allocates
max(0, all existing positive ids) + 1 inside BEGIN IMMEDIATE. Deleted ids may be
reused by this algorithm; ids are local record identities, not permanent external
identifiers. Return a fresh Portfolio with the assigned id; never mutate caller.
save requires a non-None existing id and atomically replaces its name/positions;
missing id raises PersistenceNotFoundError. delete returns False for absence,
otherwise removes only that explicitly identified aggregate and its children.
Avoid Python 3.11's decimal str(int)/int(text) digit-limit boundary: encode an
integer with format(Decimal(value), 'f') and decode validated canonical integer
text with int(Decimal(text)), using exact constructors without quantization or
global Decimal/interpreter-limit changes. Validate text grammar before decoding.
Tests include an id exceeding 4,300 digits and exact restart/allocation behavior.
Malformed saved ids raise PersistenceDataError; invalid supplied ids raise
PersistenceValidationError, never expose a conversion ValueError. Neutral transfer
retains its separate 4,096-character string cap and cannot transfer every ID that
the repository supports; this limit is explicit and does not truncate values.

Portfolio names need not be unique. Namespaces are unique exact strings, case
sensitive; watchlist save creates/replaces only that exact namespace atomically.
Security symbols/exchanges are never globally unique database keys. Ordinal keys
retain repeated known identities and independent unresolved identities. There is
no watchlist deletion API in M3; CLI removal replaces its explicitly edited entry
collection. No automatic pruning of legacy files, portfolios or other namespaces.

## Schema version 1 and one migration mechanism

SQL below fixes schema shape; all variable data use bound query parameters.
Field repetition in watchlist_entries is deliberate compatibility storage.

```sql
CREATE TABLE portfolios (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL
);
CREATE TABLE positions (
    portfolio_id TEXT NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    symbol TEXT NOT NULL,
    name TEXT,
    exchange TEXT,
    quantity TEXT NOT NULL,
    average_cost TEXT NOT NULL,
    PRIMARY KEY (portfolio_id, ordinal)
);
CREATE TABLE watchlists (
    namespace TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL
);
CREATE TABLE watchlist_entries (
    namespace TEXT NOT NULL REFERENCES watchlists(namespace) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    symbol TEXT NOT NULL,
    name TEXT,
    exchange TEXT,
    quantity TEXT NOT NULL,
    average_cost TEXT,
    current_price TEXT,
    sector TEXT,
    country TEXT,
    currency TEXT,
    market_cap TEXT,
    price_1d TEXT,
    price_5d TEXT,
    price_30d TEXT,
    price_3m TEXT,
    price_6m TEXT,
    price_1y TEXT,
    price_3y TEXT,
    price_5y TEXT,
    PRIMARY KEY (namespace, ordinal)
);
```

Enable and verify PRAGMA foreign_keys=ON on every connection before a transaction.
Store Decimal via str(value), preserving exponent/trailing-zero precision without
quantization or arithmetic. Decode through Decimal and validate finite/sign rules.
TEXT affinity prevents REAL coercion. Optional values use SQL NULL. Ordinals must
be contiguous from zero on read; reject malformed stored rows rather than skip
them or expose a partial aggregate. Validate ids/names/identity/metadata on read.

Only stock_tracker.persistence.migrations owns numbered schema upgrades and
PRAGMA user_version. Proposed function: migrate_database(path: Path) -> None.
Version zero is eligible only for a new/empty database with no user tables;
refuse an unversioned populated file. Migration 1 creates the four tables and
sets user_version=1 in one explicit transaction. Do not use executescript in a
way that implicitly commits an already active transaction. Roll back schema and
version on failure. Version 1 validates expected schema before use; future or
unknown versions fail without modification. Reads of old noncurrent versions
report SchemaVersionError; upgrades are explicit or part of a validated write.
Version-1 validation checks exact application table/column names, declared types,
nullability, primary keys, ordinal constraints and foreign-key targets/cascade
actions against this schema. A version number and matching table names alone
are insufficient. Internal SQLite tables may exist; extra application tables or
weakened constraints are an unsupported schema, not silently adopted.

Future migrations must preserve data, have before/after tests and document their
backup requirement. There is one runner and no parallel ORM/Alembic framework.
Aggregate replacement, ID allocation and multi-record import use BEGIN IMMEDIATE
and commit/rollback as one transaction; failed writes never publish partial data.
Use sqlite3's default five-second lock timeout, no retry loop/WAL tuning in M3.
State is last-successful-save when multiple callers replace the same aggregate;
optimistic concurrency is not introduced. This local single-user limitation is
explicit, not a hosted-service concurrency promise.

## Errors and CLI handling

Add no-argument StockTrackerError subclasses with fixed safe messages:

| Error | Meaning / message |
| --- | --- |
| PersistenceError | SQLite/filesystem failure: 'Local storage operation failed.' |
| PersistenceValidationError | Invalid write/import candidate: 'Local storage input is invalid.' |
| PersistenceDataError | Invalid stored data: 'Local storage data is invalid.' |
| PersistenceConflictError | Explicit create/import collision: 'Local storage record already exists.' |
| PersistenceNotFoundError | Required update target absent: 'Local storage record was not found.' |
| SchemaVersionError | Unsupported/malformed schema: 'Local storage schema is unsupported.' |
| LegacyStatePresentError | Absent namespace with legacy file: 'Legacy state requires an explicit safe transition before saving.' |

The specialized classes subclass PersistenceError. Validate bool/type inputs
before SQLite bindings. Translate sqlite3.Error and relevant OSError at the
boundary using safe exceptions from None; do not echo paths, raw SQL, values or
tracebacks in normal logs/output. Unexpected programming exceptions propagate.
Root CLI renders safe errors and exits nonzero, with no success message before
commit. Do not swallow infrastructure errors or claim writes succeeded. Provider
failure semantics and partial in-memory refresh behavior remain; committed state
is unchanged on provider failure. No cross-process compare-and-swap is promised.

## Neutral legacy transition: no pickle reader

The supported path is manual reconstruction of reviewed holdings/metadata into
a neutral UTF-8 JSON file, followed by explicit import. Preserve original legacy
files as backups. Do not provide instructions to execute/unpickle old files,
general or restricted Unpickler, class imports from payloads, or automatic
conversion. Reconstruction may require the owner to recover information from
independently trusted records; this proposal cannot recover inaccessible pickle
contents or certify missing data. No test touches real legacy files.

Proposed utilities, not a new public Typer command:

```python
def import_neutral_state(source: Path, destination: Path) -> None: ...
def backup_database(source: Path, destination: Path) -> None: ...
def restore_database(source: Path, destination: Path) -> None: ...
```

Format has exactly keys format, version, portfolios, watchlists; format is
'stock-tracker-neutral', version is integer 1 excluding bool. portfolios is an
array of objects with exactly id, name, positions. id is null for allocation or
a canonical integer string (e.g. '0', '-7', '12'; no plus/leading zeros/-0).
positions is an array of objects with exactly stock, quantity, average_cost;
stock has exactly symbol, name, exchange, using domain validation and null optional
fields. Decimal fields are strings; no JSON numeric ownership. watchlists is an
array of objects with exactly namespace, name, entries. Each entry has exactly
the WatchlistEntry field names above; stock uses the same object shape and all
optional fields are explicitly present as string or null. Identity must already
be reviewed/clean; the importer performs no provider resolution or inference.

Decimal strings follow signed decimal syntax with optional fraction/exponent;
reject whitespace, underscores, decorated money/percent, NaN/Infinity and bool.
Parse exactly, then apply finite/nonnegative and optional ownership constraints.
Reject duplicate JSON object keys, unknown/missing fields and nonstandard JSON
constants. Reject duplicate explicit portfolio ids or namespaces in the payload.
Preserve entry order/duplicates; do not merge or silently repair holdings.

Import resource limits: at most 10 MiB UTF-8 bytes, 10,000 aggregate records,
100,000 total entries, 64 nested levels, and 4,096 characters per string. Reject
violations before writing; these are transfer limits, not domain quantization or
repository field truncation. No partial import, overflow rounding or permissive
fallback. Tests include limits, malformed input and safe diagnostic behavior.

Read/parse/validate the full payload first. Under one BEGIN IMMEDIATE transaction,
initialize a new destination if needed, check all collisions, allocate None ids
after reserving payload explicit ids, and insert every aggregate. Any existing
explicit id/namespace causes failure with no replacement; payloads may add
distinct aggregates to a valid destination. On failure an existing destination's
committed contents/schema remain unchanged. If creating a new file fails, report
it; do not claim filesystem atomicity or automatically delete a file as recovery.
Initialization calls the migration runner's internal version-1 steps on this same
connection and transaction; it must not call a separately committing public
migrate_database operation before the import. Schema/user_version and imported
rows therefore commit or roll back together.
Insert via transaction-aware internal mapping/write helpers on that connection,
never public repository create/save methods that own another connection.
An empty newly created file may remain and must be handled through the documented
empty-version-zero migration rule. Source JSON and legacy files are untouched.

## Backup and restore

backup_database opens an existing valid schema read-only and uses
sqlite3.Connection.backup into a new destination exclusively reserved by this
operation. Reject source=destination or an existing destination; do not overwrite.
For every transfer, check resolved path and existing file identity (including
hard-link aliases) before destination initialization/reservation; aliases must
never let writes change the source. Neutral source/destination alias fails too.
The API obtains a SQLite-consistent snapshot, including active journal state,
without relying on filesystem copy. Validate schema, PRAGMA integrity_check and
foreign_key_check on the completed snapshot; close every connection. On failure,
report an unusable destination; never suggest restoring it and do not delete an
unrelated existing file. Backups contain holdings/metadata, never credentials.
Also validate every persisted record through the same repository decoder,
including Decimal/sign, identity, optional ownership and contiguous ordinals;
SQL integrity checks alone do not certify valid application state.
The owner selects access-controlled storage/retention; M3 promises no encryption
or scheduled backups. A verified backup is required before an explicit upgrade
of an existing database; initial version-1 creation needs none.

restore_database uses the same checked backup procedure from a supported verified
backup to a new destination. It does not replace an active database or auto-upgrade
the backup. Stop application processes, verify the new destination offline, then
the owner may select an empty new directory, restore to its stock_tracker.sqlite3
file and launch the existing CLI with that directory as cwd. The prior directory
and database remain untouched. In-place overwrite, deletion and automatic relocation
are outside this proposal; approval here authorizes no destructive user action.

## Alternatives and approval consequences

Recommended option A accepts this entire contract: cwd-relative one database,
independent watchlists and Portfolios, exact text Decimals/ids, numbered stdlib
migrations and manual neutral transition. It minimizes dependency/runtime churn
and preserves offline metadata; manual reconstruction may be costly and files
remain scoped to cwd. Stored records do not introduce hosted concurrency control.

Option B uses an OS user-data directory with an explicit configuration override.
This improves cwd independence but needs an exact cross-platform location and
test isolation/relocation contract before delegation; do not infer one.

Option C includes an automated legacy extraction utility. This requires a separate
approved security design, supported-format evidence and explicit trusted-source
handling; unrestricted pickle execution is not an acceptable default. It may
recover more data but is not authorized by accepting A.

The owner may amend any proposed field/contract, but #69–74 stay blocked until
the resulting concrete ADR is accepted. A response accepting A must expressly
authorize replacement of legacy CLI filenames/automatic pickle loading, the
existence-only refusal policy, manual recovery limitations, local allocation and
delete semantics, neutral transfer limits, migration and backup/restore contracts.
No financial quantization, domain model redesign, new CLI CRUD commands, cache,
transaction ledger, architecture framework or system installation is selected.

## Required evidence before M3 completion

Temporary-database tests cover create/read/update/delete, IDs/collisions, ordered
duplicates, optional ownership and metadata, FK/cascade, rollback, migrations,
future-version/corruption rejection, safe transfer limits and backup/restore.
Both root CLIs retain precision, provider-failure/no-match behavior and offline
display under restart tests. Help/read do not create state; legacy existence
refuses unsafe empty overwrite. Source and installed-wheel subprocesses deny
network/pickle application IO and prove actual Portfolio plus both watchlist
restart state. Run canonical pytest/Ruff/configured mypy and main required CI.
Human merges, issue closure and evidence against every SRS exit criterion remain
required; this proposal alone satisfies no runtime requirement.
