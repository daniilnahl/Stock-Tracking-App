import os
from dotenv import load_dotenv #needed to change python interperter to the virtual one
from stock import Stock

load_dotenv()
API_KEY = os.getenv("MY_API_KEY")



def main():
    print("Loading environment variables...")
    print("Environment variables loaded.")
    print(API_KEY)
    #WORKS NOW
    
    stock1 = Stock('AMZN', API_KEY)
    stock2 = Stock('AAPL', API_KEY)
    stock3 = Stock('AMD', API_KEY)
    
    stock1.get_stock_info()
    print(stock1)
    stock1.check_ticker()
    stock2.check_ticker()
    stock3.check_ticker()
    
if __name__=="__main__":
    main()