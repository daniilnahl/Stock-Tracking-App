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
    
    stock = Stock('AMZN', API_KEY)
    print(stock)
    stock.get_stock_info()
    print(stock)
    
if __name__=="__main__":
    main()