import os
import time
import schedule
from dotenv import load_dotenv
from loguru import logger
from .twitter_client import TwitterHandler
from .market_data_handler import MarketDataHandler

# Load environment variables
load_dotenv()

def post_market_update():
    """Post market update to Twitter"""
    try:
        # Initialize handlers
        market_handler = MarketDataHandler()
        twitter_handler = TwitterHandler()

        # Get market data
        market_data = market_handler.get_all_market_data()
        if not market_data:
            logger.error("Failed to fetch market data")
            return False

        # Format the message
        content = market_handler.format_market_update(market_data)
        if not content:
            logger.error("Failed to format content")
            return False

        # Post to Twitter
        success = twitter_handler.post_tweet(content)
        if not success:
            logger.error("Failed to post tweet")
            return False

        logger.info("Successfully posted market update")
        return True

    except Exception as e:
        logger.error(f"Error in post_market_update: {str(e)}")
        return False
    finally:
        # Clean up
        if 'twitter_handler' in locals():
            twitter_handler.close()

def run_bot():
    """Run the Twitter bot"""
    try:
        logger.info("Starting crypto Twitter bot...")
        
        # Schedule daily updates at 8:00 AM and 8:00 PM
        schedule.every().day.at("08:00").do(post_market_update)
        schedule.every().day.at("20:00").do(post_market_update)
        
        # Run continuously
        while True:
            schedule.run_pending()
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Shutting down bot...")
    except Exception as e:
        logger.error(f"Bot error: {str(e)}")
        raise

if __name__ == "__main__":
    run_bot() 