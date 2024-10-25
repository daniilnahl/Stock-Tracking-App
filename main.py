import os
from dotenv import load_dotenv #needed to change python interperter to the virtual one
import stock

load_dotenv()
API_KEY = os.getenv("MY_API_KEY")



def main():
    print("Loading environment variables...")
    print("Environment variables loaded.")
    
    
    
    print(API_KEY)
    
    
if __name__=="__main__":
    main()