import os
from dotenv import load_dotenv #needed to change python interperter to the virtual one
from stock import Stock
from watch_list import Watch_list
import rich

load_dotenv()
API_KEY = os.getenv("MY_API_KEY")



def main():
    print("Loading environment variables...")
    print("Environment variables loaded.")
    #print(API_KEY)
    #WORKS NOW
    
    stock1 = Stock('AMZN', API_KEY)
    stock1.get_stock_info()
    print(stock1)
    stock1.get_realtime_price()
    print(stock1)    
   
    
if __name__=="__main__":
    main()