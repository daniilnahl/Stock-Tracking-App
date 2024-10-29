import csv

#check from file
#def check_ticker():
    ##

#write to file
def write_file(valid_ticker: str):
    with open('list_of_valid_tickers.csv', 'w', newline='', encoding='utf-8') as valid_tickers:
        writer = csv.writer(valid_tickers)
        writer.writerow(valid_ticker)#BREAKS A SINGLE TICKER INTO MULTIPLE PIECES DIVIDED BY A COMMA FIx THIS

#read from file
def read_file(valid_tickers_list: list):
    with open('list_of_valid_tickers.csv', 'r', encoding='utf-8') as valid_tickers_file:
        reader = csv.reader(valid_tickers_file)
        for valid_ticker in reader:
            valid_tickers_list.extend(valid_ticker)