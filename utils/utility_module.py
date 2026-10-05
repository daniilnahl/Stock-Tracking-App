import csv
from urllib.request import urlopen
from urllib.error import HTTPError, URLError 
import json
import logging
import certifi
from stock_tracker.exceptions import InvalidTickerError
from stock_tracker.providers import factory as provider_factory

logger = logging.getLogger(__name__)

#write to file
def write_file(valid_ticker: str):
    """
    Stores a valid ticker into a csv file.
    
    Args:
        valid_ticker (str): valid stock ticker.
    """
    with open('list_of_valid_tickers.csv', 'a', newline='', encoding='utf-8') as valid_tickers_file: #'a' appends the data being written into the file. 'w' was overwriting.
        writer = csv.writer(valid_tickers_file)
        #print(valid_ticker) records the ticker as single string 
        writer.writerow([valid_ticker])

#read from file
def read_file(valid_tickers_list: list):
    """
    Appends all valid tickers from csv file into a list.
     
    Args:
        valid_tickers_list (list): a list into which valid tickers are added to.
    """
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
        API request in python objects(dictionaries inside a list).
    """
    try: #api request template
        response = urlopen(url, cafile=certifi.where())
        data = response.read().decode("utf-8")  #reads and decodes raw response
        return json.loads(data) #parses .json into python objects
    
    #note: .reason provides reason for an error, .code provides http status code (400, 401, 403, etc).
    except HTTPError: # Error fields may contain credentials; never log them.
        logger.warning("Market-data request failed: HTTP error.")
        return None
        
    except URLError:
        logger.warning("Market-data request failed: connection error.")
        return None
    
    except json.JSONDecodeError:#when api doesn't return json. 
        logger.warning("Market-data response was not valid JSON.")
        return None
        
    except Exception: # Preserve the legacy None contract without unsafe details.
        logger.error("Market-data request failed: unexpected error.")
        return None
    
def check_ticker(ticker_symbol: str, API_KEY):
    """Resolve an exact supported identity; CSV hints are never read or changed.

    Local invalid input or a validated scoped no-match returns False. Provider
    failures propagate as safe typed errors; no failure becomes cached validity.
    """
    provider = provider_factory.create_market_data_provider(API_KEY)
    try:
        provider.resolve_symbol(ticker_symbol)
    except InvalidTickerError:
        return False
    return True
