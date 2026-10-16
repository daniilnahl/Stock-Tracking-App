# Stock Tracking App

A Python stock tracker with a CLI, an authenticated local REST API and a retro
pixel dashboard in monochrome light and dark themes.

## What you can do

| Interface | Supported capabilities |
|---|---|
| CLI | Add, remove, show and refresh saved stocks; graph observed raw historical closes for supported NASDAQ stocks. |
| Dashboard | Read both saved watchlists, open stored-row details, see the selected list's entry count and choose a theme. |
| Local API | Read saved watchlists and the typed OpenAPI contract; historical requests have a separate, disabled-by-default rights gate. |

The dashboard and API are read-only. Saved prices have unknown freshness and do
not establish current quotes or currency. Search/add, recommendations and Taurus
Agents are explicitly unavailable; their [follow-up scope](docs/TO-DO-LIST.md)
is documented. Live dashboard/API history remains disabled until the separate
rights requirements in [API operations](docs/API_OPERATIONS.md#historical-activation-gate)
are satisfied.

## Canonical setup

Use Git and **Python 3.11 or 3.12** (`>=3.11,<3.13`). No provider key, `.env`,
saved watchlist or frontend toolchain is needed for Python installation or help.

```bash
git clone https://github.com/daniilnahl/Stock-Tracking-App.git
cd Stock-Tracking-App
```

Create and activate a virtual environment. On Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

For Python 3.12, substitute `-3.12` or `python3.12`. After activation, install and
check the available commands:

```bash
python -m pip install .
python menu_watchlist.py --help
python -m stock_tracker.api --help
```

Installation needs package-index access. For development and tests, use the
pinned [development setup](#development-and-verification) below.

## Run the dashboard or API

Before starting, set `STOCK_TRACKER_API_TOKEN` in the process environment through
your protected secret-management mechanism. Use your own token containing
32–256 ASCII letters, digits, underscores or hyphens. Keep it out of source,
URLs, command arguments and logs. This local token is separate from an FMP key;
saved reads need no provider credential.

From the checkout, with the environment activated:

```bash
python -m stock_tracker.api --database ./stock_tracker.sqlite3 --history-cache ./stock_tracker.history-cache.json --menu-legacy ./watchlist.pkl --evaluation-legacy ./daniils_stock_methodd.pkl --dashboard
```

These four explicit paths use the CLI's working-directory locations. Choose
them deliberately; their parent directories must already exist and the files
must be distinct. A missing database can be read as empty without creating it.
Existing legacy files are protected by the transition rules linked below.

Open **http://127.0.0.1:8000/**. In Settings, enter the same token into the masked
field, then choose Watchlists and **Read saved entries**. Configuration alone
makes no request. Reloading the page or disconnecting clears credentials and
private views; only theme preference persists. Stop the server with **Ctrl+C**.

Omit `--dashboard` for API-only operation. `/health` is public;
`/api/v1/openapi.json` and saved-data routes require bearer authentication.
The listener is fixed to loopback port 8000. Default API mode rejects every
Origin header; dashboard mode accepts only its exact matching local Origin/Host
pair. See [API operations](docs/API_OPERATIONS.md) for path validation, request
contracts, startup recovery and the history gate. External hosting is outside
the accepted scope.

The wheel already contains the production dashboard. Running it requires no
Node, browser build tools, runtime build or asset download.

## CLI help and usage

Run the maintained CLI from the checkout:

```bash
python menu_watchlist.py show-stocks
python menu_watchlist.py add-stock
python menu_watchlist.py refresh
python menu_watchlist.py remove-stock
python menu_watchlist.py graph-stock --start 2020-01-01 --end 2020-01-06
```

Interactive commands prompt for their inputs. Saved display and removal work
without a provider key; add, refresh and supported history retrieval require
provider configuration. Graph dates must be supplied together or both omitted.
Charts show raw observed closes with missing sessions preserved and no inferred
currency or adjusted returns. See [CLI usage and showcase](docs/CLI_SHOWCASE.md)
and [historical cache operations](docs/HISTORICAL_CACHE.md) for detailed behavior.

The alternate Typer app in `daniils_stock_method.py` uses a separate watchlist
namespace and has no direct script entry point. Its unfinished personal
evaluation method remains unavailable. No installed CLI console script is
configured; the API uses the supported `python -m stock_tracker.api` entry point.

## Optional provider configuration

Configure your own `FMP_API_KEY` in the environment or an untracked local `.env`.
The empty [.env.example](.env.example) is a template; copy it only when `.env`
does not already exist. Never commit credentials or overwrite an existing file
during setup.

Process values override dotenv values for the same name. `FMP_API_KEY` takes
precedence over the legacy `MY_API_KEY` fallback; a present empty canonical
value fails validation. Provider keys remain server-side. API/dashboard history
has its own rights gate even when a provider key is configured.

## Saved data

The CLI uses cwd-local `stock_tracker.sqlite3`, with independent
`menu_watchlist` and `daniils_stock_method` namespaces. Numeric values preserve
Decimal precision; missing, unowned and numeric-zero states remain distinct.
The separate historical JSON cache is not holdings state.

Legacy `watchlist.pkl` and `daniils_stock_methodd.pkl` contents are never loaded
by application storage. If a legacy entry exists while its SQLite namespace is
absent, the app refuses the operation and directs you to a reviewed neutral
transition. Preserve original files. Read [CLI storage](docs/CLI_PERSISTENCE.md),
[persistence operations](docs/PERSISTENCE.md) and
[import/backup/restore](docs/PERSISTENCE_TRANSFER.md) before moving existing data.

## Development and verification

`pyproject.toml` is the canonical Python dependency file with exact runtime,
development and build pins. From the activated checkout:

```bash
python -m pip install ".[dev]"
python -m pip check
python -m pytest tests/test_baseline.py tests/test_packaging.py tests/test_repository_hygiene.py -v
python -m pytest
python -m ruff check .
python -m mypy
```

Mypy checks **config.py only**, as configured. Default pytest uses isolated
offline fixtures; `test.py` is a manual live-provider scratch script outside
collection. The Foundation workflow runs Python 3.11/3.12 tests, Ruff,
configuration Mypy and credential-pattern checks without provider secrets.
See [testing policy](docs/TESTING.md) for the full contract and scanner limits.

Frontend maintainers use the existing Node 24/npm setup and committed lockfile
described in [frontend/README.md](frontend/README.md). Run the deliberate
`npm --prefix frontend run package:dashboard` command after UI source changes,
review generated assets and check `npm --prefix frontend run package:check`
before the normal Python wheel build. Unit, fixture-browser and real source/wheel
browser profiles are separate; no development proxy bypasses the local API.

## Design and project evidence

- [Approved SRS](SRS.md) and [architecture decisions](docs/adr/).
- [Financial calculation definitions](docs/FINANCIAL_CALCULATIONS.md).
- [Dashboard component guide](frontend/COMPONENTS.md) and [M8 execution plan](docs/milestones/m8-plan.md).
- [Milestone verification records](docs/milestones/) and the [final M8 audit PR](https://github.com/daniilnahl/Stock-Tracking-App/pull/162).
- [Contribution and agent policy](AGENTS.md).

The final M8 audit and README follow-up require owner merge and passing main CI
before milestone closure. Research/AI services, mutations in the browser,
additional analytics and hosted deployment are outside the accepted dashboard
scope.

## License and acknowledgments

[MIT License](LICENSE). The project uses Financial Modeling Prep, Rich, Typer,
FastAPI and React. Bundled dashboard/font
[license notices](src/stock_tracker/api/dashboard_assets/LICENSE.txt) accompany
the distributed assets.
