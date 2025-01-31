import logging
from crypto_twitter_bot.market_data_handler import MarketDataHandler
import json

def main():
    logging.basicConfig(level=logging.DEBUG)
    handler = MarketDataHandler()
    
    print('\n=== Testing Real-time Token Updates ===')
    market_data = handler.get_all_market_data()
    
    if market_data:
        print('\nCurrent Market Data:')
        for token, data in market_data.items():
            print(f"\n{token}:")
            print(f"  Price: ${data.get('price', 'N/A')}")
            print(f"  24h Change: {data.get('change_24h', 'N/A')}%")
            print(f"  Volume: {data.get('volume', 'N/A')} BTC")
    else:
        print("Failed to fetch real market data")

if __name__ == "__main__":
    main()
