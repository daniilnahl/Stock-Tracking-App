#MODULE FOR RECORDING VALID TICKERS ON THE SYSTEM TO LIMIT THE AMOUNT OF REQUESTS SEND TO THE API(FREE VERSION ONLY GIVES A LIMITED AMOUNT).

import csv

#check from file
#def check_ticker():
    ##

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