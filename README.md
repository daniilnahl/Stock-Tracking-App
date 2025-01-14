# Stock Tracking App

## Introduction
The **Stock Tracking App** was created as a passion project driven by my interest in stocks and Python. In its current stage, the app allows the user to add, remove, and display stocks.

## Features
- Add stocks.
- Remove stocks.
- Show stocks.
- Refresh stocks' data to be up-to-date.
- Graph a stock's performance.

# Setup Instructions
## Prerequisites
- Python 3.6 or higher.
- An API key from the stock data provider (Financial Modeling Prep).

## How do I get an API key from Financial Modeling Prep?
### 1. Sign Up for an Account
- Go to the [Financial Modeling Prep website](https://site.financialmodelingprep.com/).
- Click on Sign Up in the upper-right corner of the page.
- Create a free account by providing your email, username, and password.

### 2. Access the API Key
- Once logged in, navigate to the [API Documentation](https://site.financialmodelingprep.com/developer/docs).
- Copy everything that's after the equals sign (=). Save this API key for later use.
  > ?apikey=[API_KEY]
  > | Example: ?apiKey=3fsdFSDffsjf32fsdfs42fdsf

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
python -m venv .venv
```

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
pip install -r reqs.txt
```

### 4. Copy the API key into the .env
- Open the .env file code in your editor.
- Replace **[SAMPLE API KEY]** with your actual API key.

### 5. Run the App
In the terminal type the following line to open the app menu:
```bash
py .\menu_watchlist.py --help
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

## License
This project is licensed under the MIT License.





