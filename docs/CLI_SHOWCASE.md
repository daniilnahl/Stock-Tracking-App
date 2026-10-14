# Manual CLI showcase — M6 completion

Run date: 2026-10-13 (America/Los_Angeles). Implementation:
owner-merged audit PR #125, `237c4c5f7d9825c284d706d6730bcdf9ed3510f6`.
Administrative follow-up: [#126](https://github.com/daniilnahl/Stock-Tracking-App/issues/126).

## Real-provider run

The owner explicitly requested using the configured environment key for this
manual demonstration. The running Codex process initially had neither supported
variable; the main checkout's legacy dotenv value was empty. After the owner
configured Windows `FMP_API_KEY`, its user/machine environment value was loaded
into child process memory without printing or saving it. No key was added to
source, transcripts, database or cache. Offline steps removed both key names.

The actual `menu_watchlist.app()` executed in **10 fresh Python 3.12.10 processes**,
with real stdin prompts, FMP transport/parser/policy, application services,
SQLite persistence and Rich/Matplotlib rendering. This was not CliRunner or a
fabricated successful response. A temporary launcher selected this checkout's
imports, disabled dotenv discovery, set terminal encoding/width, selected Agg
and saved the real figure instead of opening an interactive chart window. It
changed no application code and is not a supported installed entrypoint.

All working state belonged to a new temporary directory. The sample ownership
was fictional: AAPL quantity `.2500`, average cost `100.0000`. No user watchlist
or database was opened, changed or deleted. Provider data below is an observation
from this run, not a guaranteed current quote or a source of test expected values.

| Actual CLI command / input | Observed result |
| --- | --- |
| `--help`, no credentials | Exit 0; five maintained commands; no database created |
| `show-stocks`, no credentials, empty directory | Exit 0; empty table; no database created |
| `add-stock`; AAPL, `.2500`, `100.0000` | Exit 0; successful add, real lookup/profile/period requests |
| `show-stocks` in new process, no credentials | Exit 0; restored AAPL, exact `0.2500` and `100.0000`; price `341.27`, rendered unrealized return `241.27%`; database bytes unchanged |
| `add-stock`; AAPL again | Exit 0; already-exists message; database bytes unchanged |
| `refresh` | Exit 0; successful data update |
| `show-stocks` in new process, no credentials | Exit 0; refreshed values persisted, same observed quote/return |
| `graph-stock --start 2026-09-12 --end 2026-10-12`; AAPL | Exit 0; actual chart saved using real FMP raw historical observations; holdings bytes unchanged |
| `remove-stock`; AAPL, no credentials | Exit 0; row removed from temporary demo watchlist |
| `show-stocks` in new process, no credentials | Exit 0; empty final table |

Commands above are the app arguments passed by the temporary launcher; actual
process shape was `python -I -B <temporary-launcher> <arguments>`. Ordinary use
from an activated canonical checkout remains `python menu_watchlist.py <arguments>`.
The graph renders raw observations and the existing unavailable-currency/split
labels. Saving a figure replaces only the display action; no chart values or
provider behavior are substituted. This proves these operations worked with this
account at run time, not permanent endpoint entitlement or session completeness.

## Controlled failure demonstration

A separate **13-process** run used synthetic HTTP responses with external
networking disabled, while exercising actual commands, services, provider
parsing, SQLite and rendering. It added/restored AAPL with the same fictional
ownership at synthetic price 120 (20% displayed return), refreshed to 126 (26%),
rejected duplicate and invalid tickers without changing saved bytes, and rejected
a controlled profile HTTP 403 without committing partial state. A later offline
read retained the committed quote. Historical closes 101.25 and 102.5 on January
2 and 6, 2020 reached the real chart; graphing preserved holdings. Removal and
a final restart produced an empty list. These are explicitly demo prices.

## Repeating an isolated manual run

Use the canonical README environment and configure the provider key privately.
Run commands from a newly created temporary working directory with the checkout's
absolute `menu_watchlist.py` path, so cwd-relative SQLite/cache files are separate
from ordinary holdings. Do not copy a user database, legacy pickle or dotenv into
the demo directory. Start with help/empty display, then add, restart/display,
duplicate check, refresh, paired-date graph, removal and final display. Real
provider operations need the current runtime key; saved display/removal do not.
An unsupported or failed live request must be reported, not replaced with invented
prices. Live requests remain a separate manual profile; automated tests stay offline.

The saved local transcript and chart were shown in Codex. Generated demo files,
launchers and temporary databases are excluded from this repository change.
