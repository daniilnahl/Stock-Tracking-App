#CLASS FOR A WATCH LIST
from dataclasses import dataclass

@dataclass
class Watch_list:
    name: str
    stocks: list = None
    
    def add_stock(self, stock: object):
        self.stocks.append(stock)
        
    def remove_stock(self, stock: object):
        self.stocks.remove(stock)
    
    @property
    def get_name(self):
        return self.name
    
    @name.setter
    def change_name(self):
        new_name = input('Enter the new name of this watch list: ')  
        self.name = new_name
             
    # def show_stocks(self):