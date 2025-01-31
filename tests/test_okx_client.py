import pytest
import responses
import json
from unittest.mock import patch
from crypto_twitter_bot.okx_handler import OKXHandler
from datetime import datetime, UTC

@pytest.fixture
def okx_client(mocker):
    """Create a mock OKX client"""
    mocker.patch('os.getenv', side_effect=lambda x: {
        'OKX_API_KEY': 'test_api_key',
        'OKX_SECRET_KEY': 'test_secret_key',
        'OKX_PASSPHRASE': 'test_passphrase'
    }.get(x))
    return OKXHandler()

@pytest.fixture
def mock_okx_response():
    """Mock OKX API response data"""
    return {
        'code': '0',
        'data': [
            {
                'instId': 'BTC-USDT',
                'last': '50000',
                'vol24h': '1000',
                'volCcy24h': '50000000',
                'high24h': '51000',
                'low24h': '49000'
            },
            {
                'instId': 'ETH-USDT',
                'last': '3000',
                'vol24h': '2000',
                'volCcy24h': '6000000',
                'high24h': '3100',
                'low24h': '2900'
            }
        ]
    }

def test_get_timestamp(okx_client):
    """Test timestamp generation"""
    mock_datetime = datetime(2024, 1, 30, 12, 0, 0, tzinfo=UTC)
    with patch('crypto_twitter_bot.okx_handler.datetime') as mock_dt:
        mock_dt.now.return_value = mock_datetime
        mock_dt.UTC = UTC
        result = okx_client._get_timestamp()
        assert result == "2024-01-30T12:00:00.000Z"

def test_sign(okx_client):
    """Test signature generation"""
    timestamp = "2024-01-30T12:00:00.000Z"
    method = "GET"
    request_path = "/api/v5/market/tickers"
    signature = okx_client._sign(timestamp, method, request_path)
    assert isinstance(signature, str)
    assert len(signature) > 0

@responses.activate
def test_get_market_data_success(okx_client, mock_okx_response):
    """Test successful market data retrieval"""
    responses.add(
        responses.GET,
        f"{okx_client.base_url}/api/v5/market/tickers",
        json=mock_okx_response,
        status=200
    )

    market_data = okx_client.get_market_data(['BTC-USDT', 'ETH-USDT'])
    
    assert 'BTC-USDT' in market_data
    assert 'ETH-USDT' in market_data
    assert market_data['BTC-USDT']['price'] == 50000.0
    assert 'market_strength' in market_data['BTC-USDT']

@responses.activate
def test_get_market_data_error(okx_client):
    """Test market data retrieval error handling"""
    responses.add(
        responses.GET,
        f"{okx_client.base_url}/api/v5/market/tickers",
        json={'code': '1', 'msg': 'Error'},
        status=400
    )

    with pytest.raises(Exception) as exc_info:
        okx_client.get_market_data(['BTC-USDT'])
    assert "Error fetching OKX data" in str(exc_info.value)

def test_market_strength_calculation(okx_client, mock_okx_response):
    """Test market strength indicator calculation"""
    # Price at midpoint between high and low
    data = {
        'last': '50000',
        'high24h': '51000',
        'low24h': '49000'
    }
    
    price = float(data['last'])
    high = float(data['high24h'])
    low = float(data['low24h'])
    
    strength = ((price - low) / (high - low)) * 100
    assert strength == 50.0  # Should be 50% when price is at midpoint 

def test_handle_action_fetch_prices(okx_client, mock_okx_response):
    """Test handling of fetch_prices action"""
    context = {
        'config': {
            'data_sources': {
                'okx': {
                    'pairs': ['BTC-USDT', 'ETH-USDT']
                }
            }
        }
    }
    
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            f"{okx_client.base_url}/api/v5/market/tickers",
            json=mock_okx_response,
            status=200
        )
        
        result = okx_client.handle_action({'type': 'fetch_prices'}, context)
        assert result is not None
        assert 'BTC-USDT' in result
        assert 'ETH-USDT' in result

def test_handle_action_unknown(okx_client):
    """Test handling of unknown action type"""
    result = okx_client.handle_action({'type': 'unknown'}, {})
    assert result is None

def test_market_data_edge_cases(okx_client):
    """Test market data calculation with edge cases"""
    response_data = {
        'code': '0',
        'data': [
            {
                'instId': 'BTC-USDT',
                'last': '50000',
                'vol24h': '1000',
                'volCcy24h': '50000000',
                'high24h': '50000',  # Same as current price
                'low24h': '50000'    # Same as current price
            }
        ]
    }
    
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            f"{okx_client.base_url}/api/v5/market/tickers",
            json=response_data,
            status=200
        )
        
        result = okx_client.get_market_data(['BTC-USDT'])
        # When high == low, market_strength should be 0.0 since (price - low) / 1 = 0
        assert result['BTC-USDT']['market_strength'] == 0.0 