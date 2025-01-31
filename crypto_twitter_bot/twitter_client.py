import os
from loguru import logger
from elyza_os_twitter_client import TwitterClient

class TwitterHandler:
    def __init__(self):
        self.username = os.getenv("TWITTER_USERNAME")
        self.password = os.getenv("TWITTER_PASSWORD")
        self.client = None
        
    def initialize(self):
        """Initialize Twitter client"""
        try:
            if not self.client:
                self.client = TwitterClient()
                self.client.login(self.username, self.password)
                logger.info("Twitter client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twitter client: {str(e)}")
            raise
            
    def post_tweet(self, content):
        """Post a tweet using Elyza OS client"""
        try:
            if not self.client:
                self.initialize()
            
            self.client.tweet(content)
            logger.info(f"Successfully posted tweet: {content[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to post tweet: {str(e)}")
            return False
            
    def close(self):
        """Close the Twitter client session"""
        if self.client:
            try:
                self.client.logout()
                self.client = None
                logger.info("Twitter client closed successfully")
            except Exception as e:
                logger.error(f"Failed to close Twitter client: {str(e)}") 