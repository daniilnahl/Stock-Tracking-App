# Stock Tracking App

## Introduction
The **Stock Tracking App** was created as a passion project driven by my interest in stocks and Python. The app allows the user to track stocks.

## Features
- Add stocks.
- Remove stocks.
- Show stocks.
- Refresh stocks' data to be up-to-date.
- Graph a stock's performance.

# Setup Instructions
## Prerequisites
- Python 3.11 or 3.12 (declared in `pyproject.toml`).
- An API key from the stock data provider (Financial Modeling Prep).

## How do I get an API key from Financial Modeling Prep?
### 1. Sign Up for an Account
- Go to the [Financial Modeling Prep website](https://site.financialmodelingprep.com/).
- Click on Sign Up in the upper-right corner of the page.
- Create a free account by providing your email, username, and password.

### 2. Access the API Key
- Once logged in, navigate to the [API Documentation](https://site.financialmodelingprep.com/developer/docs).
- Copy your API key and save it locally as `MY_API_KEY` using the setup below.

## How to download or clone the Project?
### Option 1: Download the ZIP File
- Visit the project repository on GitHub.
- Click the green Code button at the top-right corner of the repository page.
- Select **Download ZIP**.
- Extract the downloaded ZIP file to your desired location.

### Option 2: Clone the Repository
To clone the project using Git, follow these steps:
- Copy the repository URL from the Code button (e.g., https://github.com/username/repository.git).
- Open your terminal or command prompt and navigate to the directory where you want to store the project.
- Run the following command (put the link you copied instead):
```bash
git clone https://github.com/username/repository.git
```
- Navigate into the project directory:
```bash
cd repository
```

## How to start the Application?
### 1. Create a Virtual Environment
To ensure your project dependencies are isolated, create a virtual environment:
```bash
python3.11 -m venv .venv
```

On Windows, use `py -3.11 -m venv .venv`. Python 3.12 is also supported.

### 2. Activate the Virtual Environment
On Windows:
```bash
.venv\Scripts\activate
```
On macOS/Linux:
```bash
source .venv/bin/activate
```
Once activated, your terminal prompt should show (venv) indicating the virtual environment is active.

### 3. Install Dependencies
Install the required Python packages by running:
```bash
python -m pip install .
```

`pyproject.toml` is the master dependency file and pins the application and
transitive dependencies. The former `reqs.txt` is no longer needed. Run the
CLI commands below from the repository checkout; its CSV and watchlist files
currently use paths relative to the working directory.

### 4. Configure MY_API_KEY locally
- Copy `.env.example` to `.env` (do not overwrite an existing local `.env`).
- Set `MY_API_KEY` to your own API key in `.env`, or set the environment variable.
- The template intentionally leaves the value empty. Keep `.env` and local
  overrides out of Git; never paste credentials into source or examples.

### 5. Run the App
In the terminal type the following line to open the app menu:
```bash
py .\menu_watchlist.py --help
```
or 
```bash
py menu_watchlist.py --help
```

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
records the dependency migration and approval. Testing policy and financial
calculation documentation listed in the SRS remain separate M0 deliverables.

`test.py` is a developer scratch script that makes live API calls only when
run explicitly. It is separate from the offline repository hygiene checks:

```bash
python -m unittest discover -s tests -v
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
The known unfinished watchlist method and canonical testing policy are tracked
in issue #6; lint configuration and legacy lint cleanup remain separate M0 work.
No mypy configuration exists yet.

## License
This project is licensed under the MIT License.





