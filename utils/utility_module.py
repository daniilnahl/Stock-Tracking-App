import csv
from urllib.request import urlopen
from urllib.error import HTTPError, URLError 
import json
import certifi

#write to file
def write_file(valid_ticker: str):
    with open('list_of_valid_tickers.csv', 'a', newline='', encoding='utf-8') as valid_tickers_file: #'a' appends the data being written into the file. 'w' was overwriting.
        writer = csv.writer(valid_tickers_file)
        #print(valid_ticker) records the ticker as single string 
        writer.writerow([valid_ticker])

#read from file
def read_file(valid_tickers_list: list):
    with open('list_of_valid_tickers.csv', 'r', newline='', encoding='utf-8') as valid_tickers_file:
        reader = csv.reader(valid_tickers_file)
        for valid_ticker in reader:
            valid_tickers_list.append(valid_ticker)
            
#processes API request
def get_jsonparsed_data(url):
    """
    Processes the .json file that gets returned from an API request.
    Args:
    url: url address for a specific API request.
    Returns:
    API request in a format of a dictionary inside a list.
    """
    try:
        response = urlopen(url, cafile=certifi.where())
        data = response.read().decode("utf-8")
        return json.loads(data)
    #.reason provides reason for an error, .code provides http status code (400, 401, 403, etc).
    except HTTPError as error:
        print(f"HTTP Error: {error.code} - {error.reason}") 
        return None
        
    except URLError as error:
        print(f"URL Error: {error.reason}")
        return None
    
    except json.JSONDecodeError:
        print("Error decoding JSON. The response may not be valid JSON.")
        return None
        
    except Exception as error:
        print(f"An unexpected error occurred: {error}")
        return None
    
def check_ticker(ticker_symbol: str, API_KEY):
    """
    Checks if a stock ticker is real. If real and wasn't on local file stores to local file to preserve limited amount of API requests and returns true. 
    If not on file and can't be found through API returns false.
    Args:
    ticker_symbol: stock ticker thats getting checked.
    API_KEY: API key to get a succseful response from the FTM server.
    """
    valid_tickers_list = []
    read_file(valid_tickers_list)
        
    #checks if the ticker symbol is found on file(valid_tickers_list)
    found_ticker = any(ticker_symbol == valid_ticker[0] for valid_ticker in valid_tickers_list)
        
    #if ticker found return true
    if found_ticker:
        return True
    else: #checks if provided ticker is valid using API
        url = (f"https://financialmodelingprep.com/api/v3/search-ticker?query={ticker_symbol}&limit=10&exchange=NASDAQ&apikey={API_KEY}")
        data = get_jsonparsed_data(url)

        # Check the API response
        if data == []:  #empty list means ticker wasn't found
            return False
        else:
            write_file(ticker_symbol)
            return True    
                