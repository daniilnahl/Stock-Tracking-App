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
    stock2 = Stock('AAPL', API_KEY)
    stock3 = Stock('AMD', API_KEY)
    stock1.get_stock_info()
    stock2.get_stock_info()
    stock3.get_stock_info()
    
    watch1 = Watch_list('Test')
    watch1.add_stock(stock1)
    watch1.add_stock(stock2)
    watch1.add_stock(stock3)
    
    print(watch1.name)
    watch1.change_name()
    print(watch1.name)
    
    # print(watch1)
    # watch1.show_stocks()
    
    # stock1.check_ticker()
    # stock2.check_ticker()
    # stock3.check_ticker()
    
if __name__=="__main__":
    main()