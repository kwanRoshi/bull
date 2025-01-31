import logging
from crypto_twitter_bot.market_data_handler import MarketDataHandler

def main():
    logging.basicConfig(level=logging.DEBUG)
    handler = MarketDataHandler()
    
    print('\nTesting with mock data:')
    print(handler.debug_market_update())
    
    print('\nTesting with real data:')
    market_data = handler.get_all_market_data()
    if market_data:
        print(handler.format_market_update(market_data))
    else:
        print("Failed to fetch real market data")

if __name__ == "__main__":
    main()
