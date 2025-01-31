import pytest
import responses
from crypto_twitter_bot.crypto_twitter_bot import TwitterBot
import os

@pytest.fixture
def twitter_bot():
    """Create a Twitter bot instance"""
    return TwitterBot()

@responses.activate
def test_post_tweet_success(twitter_bot):
    """Test successful tweet posting"""
    responses.add(
        responses.POST,
        "https://api.twitter.com/2/tweets",
        json={"data": {"id": "123", "text": "Test tweet"}},
        status=200
    )
    
    twitter_bot.post_tweet("Test tweet")
    
    assert len(responses.calls) == 1
    assert responses.calls[0].request.headers["Authorization"] == f"Bearer {twitter_bot.bearer_token}"
    assert responses.calls[0].request.headers["Content-Type"] == "application/json"

@responses.activate
def test_post_tweet_error(twitter_bot):
    """Test tweet posting error handling"""
    responses.add(
        responses.POST,
        "https://api.twitter.com/2/tweets",
        json={"errors": [{"message": "Invalid request"}]},
        status=400
    )
    
    with pytest.raises(Exception):
        twitter_bot.post_tweet("Test tweet")

def test_twitter_auth_setup(mocker):
    """Test Twitter authentication setup"""
    # Mock environment variables
    mocker.patch('os.getenv', side_effect=lambda x: {
        'TWITTER_API_KEY': 'test_api_key',
        'TWITTER_API_SECRET': 'test_api_secret',
        'TWITTER_ACCESS_TOKEN': 'test_access_token',
        'TWITTER_ACCESS_TOKEN_SECRET': 'test_access_token_secret',
        'TWITTER_BEARER_TOKEN': 'test_bearer_token'
    }.get(x))
    
    twitter_bot = TwitterBot()
    assert twitter_bot.bearer_token == 'test_bearer_token' 