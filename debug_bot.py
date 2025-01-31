from crypto_twitter_bot.market_data_handler import MarketDataHandler
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_market_update():
    """Test market update formatting with both mock and real data"""
    try:
        # Initialize market data handler
        handler = MarketDataHandler()
        
        # Test with mock data
        print("\n=== Mock Market Update ===")
        mock_update = handler.debug_market_update()
        print(mock_update)
        print("========================\n")
        
        # Test with real data
        print("\n=== Real-time Market Update ===")
        real_data = handler.get_all_market_data()
        real_update = handler.format_market_update(real_data)
        print(real_update)
        print("========================\n")
        
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")

if __name__ == "__main__":
    test_market_update() 