# Stock Tracking App

## Introduction
The **Stock Tracking App** was created as a passion project driven by my interest in stocks and Python. The app allows the user to track stocks.

## Features
- Add stocks.
- Remove stocks.
- Show stocks.
- Refresh stocks' data to be up-to-date.
- Graph a stock's performance.

The existing chart is approximate; real historical charting remains M4 work.
The unfinished personal evaluation method is unavailable. This foundation
does not certify financial analytics or production readiness.

## Canonical setup

Use Git and **Python 3.11 or 3.12** (`>=3.11,<3.13` in `pyproject.toml`).
No provider key, `.env` or saved watchlist is needed for installation, tests or
help in a fresh checkout. Installation needs package-index access; automated
verification blocks market-provider transport and isolates temporary state.

```bash
git clone https://github.com/daniilnahl/Stock-Tracking-App.git
cd Stock-Tracking-App
```

Create and activate a fresh virtual environment. On Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

For Python 3.12, substitute `-3.12` or `python3.12` in the creation command.
Use `python` after activation so all commands use that environment.

From the checkout, install the application and pinned development tools, then
run the canonical checks from [docs/TESTING.md](docs/TESTING.md):

```bash
python -m pip install ".[dev]"
python -m pip check
python -m pytest tests/test_baseline.py tests/test_packaging.py tests/test_repository_hygiene.py -v
python -m pytest
python -m ruff check .
python -m mypy
```

The targeted checks verify both Typer help surfaces in empty temporary working
directories, offline wheel packaging, dependency pins, Git ignore behavior and
redacted tracked-source credential patterns. Full pytest collects only `tests/`;
`test.py` is a manual live-provider scratch script, outside collection.

`pyproject.toml` is the single master dependency file. Runtime, development,
transitive and build-backend versions use exact pins; there is no separately
maintained `reqs.txt` or second lockfile. Repeat
`python -m pip install ".[dev]"` and the checks in the same environment to verify
that installed dependency versions stay pinned. Repeat the fresh environment
walkthrough on each supported Python version when changing pins. Pins provide
version resolution, not artifact hashes or byte-identical builds across platforms.
Runtime-only installation uses `python -m pip install .`.

Optional wheel build, using the installed pinned backend:

```bash
python -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist
```

The wheel includes five flat modules (`stock`, `watch_list`, `menu_watchlist`,
`daniils_stock_method`, `config`) and `utils.utility_module`. It excludes tests,
scratch scripts, CSV data and local state. CLI usage still requires the checkout.

Ruff checks application code, tests and the scratch script using `E4`, `E7`,
`E9` and `F`. Mypy runs in strict mode on **`config.py` only**, using the file
scope in `pyproject.toml`; do not run `mypy src/` because no `src/` tree exists.
The [readiness decision](docs/TESTING.md#type-check-readiness-decision--issue-11)
assigns remaining domain, provider, persistence and CLI typing to M1/M2/M3/M6.

## CLI help and usage

In a fresh checkout, before creating local credentials or watchlist files:

```bash
python menu_watchlist.py --help
```

This prints the existing commands: `add-stock`, `remove-stock`, `show-stocks`,
`refresh` and `graph-stock`. Run a command from the checkout using
`python menu_watchlist.py <command>`; add/remove commands prompt for input.
`add-stock` and `refresh` require a provider credential before network work.
Help and saved-data commands do not require a key. The alternate Typer app in
`daniils_stock_method.py` is covered by the offline help tests; it has no script
entry point. The unfinished evaluation method raises `NotImplementedError`.

**Existing-state caveat:** both CLI modules load cwd-relative pickle state at
import, including when displaying help (`watchlist.pkl` or
`daniils_stock_methodd.pkl`). Pickle can execute code; never load an untrusted
file. For verification of an existing installation, use the isolated tests
above or a separate fresh checkout, rather than importing the CLI in a user-data
directory. Do not inspect, delete, migrate or overwrite saved user files as part
of setup. Legacy `Stock.API_KEY` values can also be stored in these files;
removing credential coupling and replacing pickle are M1/M3 work. CSV paths
are also relative to the working directory.

## Optional provider configuration

Obtain your own key through [Financial Modeling Prep](https://site.financialmodelingprep.com/developer/docs).
Keep it outside source control in the process environment, or copy the empty
[.env.example](.env.example) to a local `.env` **only if `.env` does not exist**.
On PowerShell:

```powershell
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
```

On macOS/Linux:

```bash
[ -e .env ] || cp .env.example .env
```

Edit only the local file to set `FMP_API_KEY`. `.env` and local overrides are
ignored by Git; `.env.example` deliberately contains an empty value. Never
paste a credential into source, tests, command examples, logs or PR text.

[config.py](config.py) loads optional dotenv configuration. Process environment
values override dotenv values of the same name. `FMP_API_KEY` wins across
sources; the legacy `MY_API_KEY` fallback applies only when `FMP_API_KEY` is
absent from both. A present but empty/whitespace canonical value fails validation
and does not fall back. Remove the empty canonical variable if using the legacy
name. Missing or blank credentials stop `add-stock`, `refresh` and explicit
scratch-script requests before network work. Diagnostics omit credential values
and request URLs.

Previously exposed keys are covered by the
[owner rotation attestation](docs/security/issue-3-credential-rotation.md).
This is owner-confirmed revocation/replacement, not an agent live-key test.
Tracked-source scanning covers known literal credential and URL patterns with
redacted findings; it does not certify arbitrary secret formats or Git history.

## Contributing and foundation status

Read the approved [SRS](SRS.md), [agent operating policy](AGENTS.md),
[testing policy](docs/TESTING.md), [financial calculation specification](docs/FINANCIAL_CALCULATIONS.md)
and [accepted dependency ADR](docs/adr/0005-canonical-python-dependencies.md).
Implement a bounded issue on a task branch, run required checks, review the diff
and open a PR using the repository templates. Do not merge automatically.

The [Foundation workflow](.github/workflows/foundation.yml) runs pytest on
Python 3.11 and 3.12, Ruff, configuration mypy and credential-pattern checks
on PRs and pushes to `main`, using the same pinned installation without provider
secrets. The [CI contract](docs/TESTING.md#foundation-actions-workflow--issue-12)
lists exact check names, scanner limitations and owner-only protection setup.

[Issue #13](https://github.com/daniilnahl/Stock-Tracking-App/issues/13) and its PR
record the SRS §23 requirement/issue checklist and sanitized exit evidence.
[M0](https://github.com/daniilnahl/Stock-Tracking-App/milestone/1) stays open while
required issues remain open. Passing setup checks alone do not close the
milestone: all required issues, successful CI on `main` after an authorized
merge, source security evidence and canonical documentation must be accounted for.

## Acknowledgments 
- ### Financial Modeling Prep API
  #### This app utilizes the Financial Modeling Prep API for retrieving stock data.
  #### You can learn more about the API at https://financialmodelingprep.com/developer/docs/.
- ### RICH Library
  #### The app uses the RICH API for creating beautiful tables and enhancing the CLI interface.
  #### More information can be found at https://rich.readthedocs.io/.
- ### Typer Library
  #### The app is built using the Typer API to handle CLI commands.
  #### You can check out Typer at https://typer.tiangolo.com/.
  #### Citation: Ramírez, S. Typer [Computer software]. https://github.com/fastapi/typer.
  
## Contributing
Feel free to contribute by creating issues or submitting pull requests to enhance the app.

Read [AGENTS.md](AGENTS.md) and the approved [SRS.md](SRS.md) before implementing
an issue. The [foundation decision](docs/adr/0005-canonical-python-dependencies.md)
records the dependency migration and approval. [Testing policy](docs/TESTING.md)
defines the offline suite; financial calculation documentation remains a
separate M0 deliverable.

`test.py` is a developer scratch script that makes live API calls only when
run explicitly. Pytest collects only automated tests under `tests/`:

```bash
python -m pytest
```

These checks verify credential patterns with redacted diagnostics and Git ignore
rules. They do not certify that arbitrary secrets or historical commits are clean.

### Development installation and packaging checks

Use a fresh virtual environment as described above with Python 3.11 or 3.12.
Install the application and development tools together:

```bash
python -m pip install ".[dev]"
python -m pip check
python -m pytest tests/test_packaging.py -v
python -m pytest
python -m ruff check .
python -m mypy
python -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist
```

Repeat this workflow on each supported Python version. A second
`python -m pip install ".[dev]"` must preserve the installed dependency versions.
Runtime, development, transitive and build-backend versions are pinned in
`pyproject.toml`; update those pins together. This provides version-pinned
resolution, not byte-identical or hash-verified artifacts across platforms.
Installation and packaging checks need package-index access but no API key,
`.env`, user database or market-data request.

The wheel contains the four existing application modules and `utils`; scratch
scripts, tests, CSV data and local state are excluded. Existing CLI scripts must
still run from the checkout. Packaging smoke checks import only `stock` and
`utils.utility_module` with transport blocked, without instantiating a stock.
The unfinished watchlist evaluation method explicitly raises `NotImplementedError`.
The offline baseline verifies both CLI help surfaces without keys or saved state.

Ruff's baseline is configured in `pyproject.toml` for Python 3.11 with explicit
`E4`, `E7`, `E9` and `F` rules (import/statement errors, syntax errors and
Pyflakes). Run `python -m ruff check .` from the checkout to check application
code, automated tests and the sanitized scratch script. See the
[testing policy](docs/TESTING.md) for rule rationale and coverage.
Mypy is configured in strict mode for the maintained `config.py` boundary.
Run `python -m mypy` from the checkout; it uses the explicit file scope in
`pyproject.toml`. The [type-check readiness decision](docs/TESTING.md#type-check-readiness-decision--issue-11)
records the concrete legacy gaps and milestone ownership for expanding coverage.
This baseline does not certify legacy domain, provider, persistence or CLI types.

## Continuous integration

The Foundation workflow runs pytest on Python 3.11 and 3.12, Ruff, the configured
mypy scope, and a redacted credential-pattern scan on pull requests and pushes
to `main`. It installs the same pinned `.[dev]` environment and needs no FMP
credentials. See the [CI contract](docs/TESTING.md#foundation-actions-workflow--issue-12)
for exact check names, scanner limits, failure probes, and owner-only protection
setup. A passing PR run must be followed by a passing `main` run after an
owner-authorized merge before issue #12 can close.

## License
This project is licensed under the MIT License.
