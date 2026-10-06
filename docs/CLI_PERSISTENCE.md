# Existing CLI storage

Both maintained entrypoints retain their existing commands, prompts and provider
flows. They select `Path.cwd() / 'stock_tracker.sqlite3'` once when imported and
store independent namespaces: `menu_watchlist` and `daniils_stock_method`.
Changing the working directory later in the process does not move its storage.
Names, ordered entries, duplicate identities, exact ownership inputs, last
observed quotes and display metadata persist. Saved quotes support offline
display and do not imply freshness. Portfolios remain separate records.

Percentage display metadata may contain empty or nonnumeric text. Empty/missing
values and the existing dash/N/A sentinels display as `-`. Other nonnumeric
metadata displays literally, with Rich markup escaped and no percentage suffix
or numeric color classification. Numeric percentage strings retain their exact
text and existing colors. This presentation behavior does not change saved
metadata, holdings, or database state.

Importing an entrypoint creates an empty in-memory `current_watchlist`; it does
not load application state. Root and subcommand help never load storage or
require a provider key. Command execution loads state lazily. Existing
`load_watchlist()` returns a fresh offline watchlist; `save_watchlist(watchlist)`
commits only that entrypoint's namespace. Restored facades bind the currently
configured runtime key, which is never persisted. Local display needs no key;
add/refresh retain their existing key requirement.

The public in-memory `current_watchlist` object stays available for existing
callers. Lazy restoration updates that object in place. Explicitly supplied
nonempty in-memory state and its object references are retained; callers may
use `load_watchlist()` to request fresh persisted state explicitly. State is
last-successful-save, without cross-process conflict detection.

An absent database/namespace starts empty without creating storage when its
legacy filename is absent. The legacy names are `watchlist.pkl` and
`daniils_stock_methodd.pkl`. When the namespace is absent and the corresponding
legacy directory entry exists, loading/saving refuses with a safe error and
guidance to preserve the original file and use manual neutral reconstruction.
Only directory-entry existence is inspected, including dangling symlinks;
contents and link targets are never read. An existing SQLite namespace is
authoritative even when the original legacy file remains. Application code
never deserializes, overwrites, renames or deletes those files.

Storage errors exit commands nonzero using fixed safe messages. Add/refresh
success is reported after commit. Invalid, aborted or provider-failed commands
preserve committed storage; accepted partial in-memory refresh behavior remains.
Corrupt/unsupported state fails explicitly without an empty fallback. All
verification uses temporary paths, never real user files.

The accepted [persistence ADR](adr/0009-persistence-contracts.md) defines the
manual transition and backup contracts. [Persistence operations](PERSISTENCE.md)
documents the runner/repositories and separately scoped transfer utilities.
These CLI changes introduce no new public command or automatic legacy converter.
