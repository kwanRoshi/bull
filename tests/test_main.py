import pytest
import json
import time
import schedule
from unittest.mock import patch, MagicMock
from crypto_twitter_bot.crypto_twitter_bot import TwitterBot, AIHandler, post_market_update, run_bot
import os

@pytest.fixture
def mock_config():
    return {
        'prompts': {
            'market_analysis': 'Analyze this data: {{data}}',
            'technical_analysis': 'Technical analysis of: {{data}}'
        },
        'data_sources': {
            'okx': {
                'pairs': ['BTC-USDT', 'ETH-USDT']
            }
        }
    }

@pytest.fixture
def mock_market_data():
    return {
        'BTC-USDT': {
            'price': 50000.0,
            'market_strength': 65.5
        }
    }

def test_post_market_update_success(mocker, mock_config, mock_market_data):
    """Test successful market update posting"""
    # Mock config file
    mocker.patch('builtins.open', mocker.mock_open(read_data=json.dumps(mock_config)))
    
    # Mock OKX handler
    mock_okx = mocker.MagicMock()
    mock_okx.get_market_data.return_value = mock_market_data
    mocker.patch('crypto_twitter_bot.crypto_twitter_bot.OKXHandler', return_value=mock_okx)
    
    # Mock AI handler
    mock_ai = mocker.MagicMock()
    mock_ai.generate_content_claude.return_value = "Claude analysis"
    mock_ai.generate_content_openai.return_value = "GPT-4 analysis"
    mocker.patch('crypto_twitter_bot.crypto_twitter_bot.AIHandler', return_value=mock_ai)
    
    # Mock Twitter bot
    mock_twitter = mocker.MagicMock()
    mocker.patch('crypto_twitter_bot.crypto_twitter_bot.TwitterBot', return_value=mock_twitter)
    
    # Mock random choice to test both AI paths
    with patch('random.choice', return_value=True):
        post_market_update()
        mock_ai.generate_content_claude.assert_called_once()
    
    with patch('random.choice', return_value=False):
        post_market_update()
        mock_ai.generate_content_openai.assert_called_once()

def test_post_market_update_okx_error(mocker, mock_config):
    """Test error handling when OKX data fetch fails"""
    mocker.patch('builtins.open', mocker.mock_open(read_data=json.dumps(mock_config)))
    mock_okx = mocker.MagicMock()
    mock_okx.get_market_data.side_effect = Exception("OKX API error")
    mocker.patch('crypto_twitter_bot.crypto_twitter_bot.OKXHandler', return_value=mock_okx)
    
    post_market_update()  # Should log error but not raise exception

def test_post_market_update_ai_error(mocker, mock_config, mock_market_data):
    """Test error handling when AI content generation fails"""
    mocker.patch('builtins.open', mocker.mock_open(read_data=json.dumps(mock_config)))
    mocker.patch('crypto_twitter_bot.crypto_twitter_bot.OKXHandler').return_value.get_market_data.return_value = mock_market_data
    
    mock_ai = mocker.MagicMock()
    mock_ai.generate_content_claude.side_effect = Exception("Claude API error")
    mocker.patch('crypto_twitter_bot.crypto_twitter_bot.AIHandler', return_value=mock_ai)
    
    post_market_update()  # Should log error but not raise exception

def test_post_market_update_twitter_error(mocker, mock_config, mock_market_data):
    """Test error handling when Twitter post fails"""
    mocker.patch('builtins.open', mocker.mock_open(read_data=json.dumps(mock_config)))
    mocker.patch('crypto_twitter_bot.crypto_twitter_bot.OKXHandler').return_value.get_market_data.return_value = mock_market_data
    mocker.patch('crypto_twitter_bot.crypto_twitter_bot.AIHandler').return_value.generate_content_claude.return_value = "Test content"
    
    mock_twitter = mocker.MagicMock()
    mock_twitter.post_tweet.side_effect = Exception("Twitter API error")
    mocker.patch('crypto_twitter_bot.crypto_twitter_bot.TwitterBot', return_value=mock_twitter)
    
    post_market_update()  # Should log error but not raise exception

@pytest.mark.timeout(2)  # Timeout after 2 seconds to prevent infinite loop
def test_run_bot(mocker):
    """Test bot scheduling and running"""
    mock_schedule = mocker.MagicMock()
    mocker.patch('schedule.every', return_value=mock_schedule)
    
    # Mock time.sleep to break the infinite loop
    mock_sleep = mocker.MagicMock(side_effect=KeyboardInterrupt)
    mocker.patch('time.sleep', mock_sleep)
    
    # Run bot and verify scheduling
    try:
        run_bot()
    except KeyboardInterrupt:
        pass
    
    schedule.every.assert_called_once_with(4)
    mock_schedule.hours.do.assert_called_once_with(post_market_update)
    mock_sleep.assert_called_once_with(60)

def test_ai_handler_initialization(mocker):
    """Test AI handler initialization and functionality"""
    # Mock config file
    mocker.patch('builtins.open', mocker.mock_open(read_data=json.dumps({
        'prompts': {
            'market_analysis': 'test prompt',
            'technical_analysis': 'test prompt'
        }
    })))
    
    # Mock environment variables
    mocker.patch('os.getenv', side_effect=lambda x: {
        'ANTHROPIC_API_KEY': 'test_api_key',
        'OPENAI_API_KEY': 'test_api_key'
    }.get(x))
    
    # Create handler
    handler = AIHandler()
    
    # Test that prompts are loaded
    assert 'market_analysis' in handler.prompts
    assert 'technical_analysis' in handler.prompts
    assert handler.prompts['market_analysis'] == 'test prompt'
    assert handler.prompts['technical_analysis'] == 'test prompt'
    
    # Test that clients are initialized when needed
    mock_response = type('Response', (), {'content': "Test content"})()
    mocker.patch.object(handler, '_get_anthropic').return_value.messages.create.return_value = mock_response
    
    content = handler.generate_content_claude({'test': 'data'})
    assert content == "Test content"
    
    mock_response = type('Response', (), {
        'choices': [
            type('Choice', (), {'message': type('Message', (), {'content': "Test content"})()})()
        ]
    })()
    mocker.patch.object(handler, '_get_openai').return_value.chat.completions.create.return_value = mock_response
    
    content = handler.generate_content_openai({'test': 'data'})
    assert content == "Test content"

def test_ai_handler_client_initialization_error(mocker):
    """Test AI handler client initialization with missing API keys"""
    # Mock config file
    mocker.patch('builtins.open', mocker.mock_open(read_data=json.dumps({
        'prompts': {
            'market_analysis': 'test prompt',
            'technical_analysis': 'test prompt'
        }
    })))
    
    # Mock environment variables to return None for API keys
    mocker.patch('os.getenv', return_value=None)
    
    # Create handler
    handler = AIHandler()
    
    # Test client initialization with missing API keys
    with pytest.raises(Exception):
        handler._get_anthropic()
    
    with pytest.raises(Exception):
        handler._get_openai()

def test_run_bot_keyboard_interrupt(mocker):
    """Test bot graceful shutdown on keyboard interrupt"""
    mock_schedule = mocker.MagicMock()
    mocker.patch('schedule.every', return_value=mock_schedule)
    
    # Mock schedule.run_pending to raise KeyboardInterrupt
    mocker.patch('schedule.run_pending', side_effect=KeyboardInterrupt)
    
    # Run bot and verify it handles the interrupt
    with pytest.raises(KeyboardInterrupt):
        run_bot()
    
    schedule.every.assert_called_once_with(4)
    mock_schedule.hours.do.assert_called_once_with(post_market_update) 