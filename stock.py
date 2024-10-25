from dataclasses import dataclass

@dataclass
class Stock:
    ticker_symbol: str
    industry: str = None
    price: float = None
    market_cap: float = None
    eps: float = None #earning per share
    pe: float = None #price to earning
    
    
