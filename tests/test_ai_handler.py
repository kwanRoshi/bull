import pytest
import json
from crypto_twitter_bot.crypto_twitter_bot import AIHandler
import os

@pytest.fixture
def ai_handler(mocker):
    """Create a mock AI handler"""
    # Mock environment variables
    mocker.patch('os.getenv', side_effect=lambda x: {
        'ANTHROPIC_API_KEY': 'test_api_key',
        'OPENAI_API_KEY': 'test_api_key'
    }.get(x))
    
    # Mock config file
    mocker.patch('builtins.open', mocker.mock_open(read_data=json.dumps({
        'prompts': {
            'market_analysis': 'Analyze this data: {{data}}',
            'technical_analysis': 'Technical analysis of: {{data}}'
        }
    })))
    
    # Create mock clients
    mock_anthropic = mocker.MagicMock()
    mock_anthropic.messages = mocker.MagicMock()
    mock_anthropic.messages.create = mocker.MagicMock()
    
    mock_openai = mocker.MagicMock()
    mock_openai.chat = mocker.MagicMock()
    mock_openai.chat.completions = mocker.MagicMock()
    mock_openai.chat.completions.create = mocker.MagicMock()
    
    # Mock client constructors
    mocker.patch('anthropic.Anthropic', return_value=mock_anthropic)
    mocker.patch('openai.OpenAI', return_value=mock_openai)
    
    # Create handler and replace clients
    handler = AIHandler()
    handler.anthropic = mock_anthropic
    handler.openai = mock_openai
    
    return handler

@pytest.fixture
def mock_market_data():
    """Sample market data for testing"""
    return {
        'BTC-USDT': {
            'price': 50000.0,
            'change_24h': 1000.0,
            'volume': 50000000.0,
            'high_24h': 51000.0,
            'low_24h': 49000.0,
            'market_strength': 50.0
        }
    }

def test_generate_content_claude(ai_handler, mock_market_data):
    """Test Claude content generation"""
    mock_response = type('Response', (), {'content': "Generated content from Claude"})()
    ai_handler.anthropic.messages.create.return_value = mock_response
    
    content = ai_handler.generate_content_claude(mock_market_data)
    assert content == "Generated content from Claude"
    
    # Verify correct prompt formatting
    ai_handler.anthropic.messages.create.assert_called_once()
    call_args = ai_handler.anthropic.messages.create.call_args[1]
    assert isinstance(call_args['messages'], list)
    assert call_args['messages'][0]['content'].startswith('Analyze this data:')

def test_generate_content_openai(ai_handler, mock_market_data):
    """Test OpenAI content generation"""
    mock_response = type('Response', (), {
        'choices': [
            type('Choice', (), {'message': type('Message', (), {'content': "Generated content from GPT-4"})()})()
        ]
    })()
    
    ai_handler.openai.chat.completions.create.return_value = mock_response
    
    content = ai_handler.generate_content_openai(mock_market_data)
    assert content == "Generated content from GPT-4"
    
    # Verify correct prompt formatting
    ai_handler.openai.chat.completions.create.assert_called_once()
    call_args = ai_handler.openai.chat.completions.create.call_args[1]
    assert isinstance(call_args['messages'], list)
    assert call_args['messages'][0]['content'].startswith('Technical analysis of:') 