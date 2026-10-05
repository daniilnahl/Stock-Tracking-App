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
`daniils_stock_method`, `config`), `utils.utility_module`, and the
`stock_tracker.domain` and `stock_tracker.compatibility` packages. It excludes
tests, scratch scripts, CSV data and local state. CLI usage still requires the checkout.

Ruff checks application code, tests and the scratch script using `E4`, `E7`,
`E9` and `F`. Mypy runs in strict mode on **`config.py` only**, using the file
scope in `pyproject.toml`; `mypy src/` is not the configured verification command.
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
of setup. New facade state excludes runtime credentials; historical saved keys
are ignored when restoring state and current configuration supplies the runtime
binding. This does not migrate real user files or make pickle safe. Replacing
pickle remains M3 work. Explicit legacy CSV helpers use paths relative to the
working directory. Ticker validation does not read or change CSV hints: it
requires a unique exact NASDAQ provider match each time. A completed valid
search without that match reports the new candidate as invalid and rejects it
without adding or saving; existing holdings stay unchanged. This scoped rule
can reject real instruments when search is incomplete or truncated and does
not claim global nonexistence. Provider failures remain separate errors.
Both CLIs render safe provider/configuration failures with exit code 1 and do
not save a failed add or refresh. A failed profile/quote invalidates the current
price in memory while preserving known metadata and holdings; a failed summary
invalidates all summary fields. Earlier entries may already have refreshed when
a later entry fails, but the saved file stays unchanged. Explicit null prices
are successful missing data, with unavailable return values rather than zero.

## Domain boundary and M1 status

The installed `stock_tracker.domain` package exposes immutable security identity
and ownership, a Portfolio with an owned Position list, and pure Decimal position
snapshots. It imports and runs independently of credentials, HTTP, databases and
terminal/chart libraries. Root `stock.Stock` is a compatibility facade; existing
CLI commands retain their names and ownership prompts preserve decimal text.
Snapshot inputs use one currency; missing quotes and undefined zero-basis returns
stay distinct from zero. Advanced metrics and transaction conventions remain
blocked by the financial specification.

M1 is achieved as of 2026-10-04: owner-merged
[PR #46](https://github.com/daniilnahl/Stock-Tracking-App/pull/46) includes the
reviewed implementation on `main` at `788d3c4`; all nine required M1 issues
are closed and the [post-merge Foundation run](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37214866386)
passed all five checks. The [M1 completion review](docs/milestones/m1-exit-evidence.md#completion-review--2026-10-04)
records source, tests, issue/PR reconciliation and local verification.
GitHub's milestone container remains open with zero open issues at the review.
Safe structured storage, real historical charts and CLI V2 remain later milestones.

## Market data layer and M2 status

M2 is implemented and achieved as of 2026-10-05 on `main` at
`5eccf3b24edbe03a6f01e86b9dfcffb80a1ad0c7`. It supplies immutable typed provider
models/interfaces, FMP quote/profile/period/identity operations, approved HTTP
timeout/retry/rate-limit behavior, scoped ticker rejection and offline mocked
verification. Maintained application paths delegate through the provider boundary;
successful no-match rejects only a new candidate, while provider failures stay
distinct and existing holdings remain untouched.

All ten required M2 issues are closed after human merges of PR #57–65 and #67.
The [post-merge Foundation run](https://github.com/daniilnahl/Stock-Tracking-App/actions/runs/37346059176)
passed all five checks; the [completion evidence](docs/milestones/m2-exit-evidence.md#completion-review--2026-10-05)
records the six deliverables, boundary exit criterion and final review.
[M2](https://github.com/daniilnahl/Stock-Tracking-App/milestone/3) is closed at
100%, with zero open and 20 closed items. This does not implement persistence,
genuine historical retrieval/charts, FX or broader exchange support.

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

The [M0 verification record](docs/milestones/m0-verification.md) consolidates
the SRS §23 deliverable checklist, code review and sanitized exit evidence.
At the 2026-10-03 review of `e0bbeb1`, all three technical exit criteria have
supporting evidence, including a successful Foundation run on `main` after
PR #35 merged. All thirteen foundation issues are closed; CI
[issue #12](https://github.com/daniilnahl/Stock-Tracking-App/issues/12) was
implemented in [PR #34](https://github.com/daniilnahl/Stock-Tracking-App/pull/34)
and its completed state was reconciled after owner confirmation.
[M0](https://github.com/daniilnahl/Stock-Tracking-App/milestone/1)
is complete under `AGENTS.md` §10.7.
The foundation does not complete the later domain, provider, persistence or
financial milestones.

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

## License
This project is licensed under the MIT License.
