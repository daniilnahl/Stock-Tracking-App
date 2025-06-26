from stock import Stock 

def main():
    test = Stock("AMD", "PIfzeXPMBKiGExOA9JdZSCfwu8264HK9")
    # forward pe -
    # industry pe - FOUND
    # PEG - 
    # Price/FCF -
    # Net profit margin 5y avg -
    # PS - 
    # ROIC - FOUND
    # 5y revenue cagr - FOUND
    # 5y fcf cagr - NOT FOUND (api doesnt provide historic fcf values).
    # 3y eps growth - FOUND
    # debt/equity -
    # economic moat - 
    # management quality -


    test.get_stock_info()   
    # industry pe - https://financialmodelingprep.com/stable/industry-pe-snapshot?date=2024-02-01&apikey=PIfzeXPMBKiGExOA9JdZSCfwu8264HK9

    # ROIC (also gives mcap) - https://financialmodelingprep.com/stable/key-metrics?symbol=AAPL&apikey=PIfzeXPMBKiGExOA9JdZSCfwu8264HK9
    # EPS 4 years growth 
        # get estimate eps from 4 years in future - https://financialmodelingprep.com/stable/analyst-estimates?symbol=AAPL&period=annual&page=0&limit=10&apikey=PIfzeXPMBKiGExOA9JdZSCfwu8264HK9  
        # get current eps - https://financialmodelingprep.com/stable/earnings-calendar?apikey=PIfzeXPMBKiGExOA9JdZSCfwu8264HK9
        # calcuate cagr 


    # 5 year revenue cagr - https://financialmodelingprep.com/stable/financial-growth?symbol=AAPL&apikey=PIfzeXPMBKiGExOA9JdZSCfwu8264HK9

if __name__ == "__main__":
    main()