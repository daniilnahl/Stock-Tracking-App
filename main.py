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
    stock1.get_price_over_time()
    watch_list1 = Watch_list("Test")
    watch_list1.add_stock(stock1)
    watch_list1.show_stocks()
    
if __name__=="__main__":
    main()