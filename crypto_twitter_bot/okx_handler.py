import os
import hmac
import base64
import time
import requests
from datetime import datetime, UTC

class OKXHandler:
    def __init__(self, api_key=None, api_secret=None, passphrase=None):
        self.api_key = api_key or os.getenv('OKX_API_KEY')
        self.api_secret = api_secret or os.getenv('OKX_SECRET_KEY')
        self.passphrase = passphrase or os.getenv('OKX_PASSPHRASE')
        self.base_url = "https://www.okx.com"

    def _get_timestamp(self):
        """Get ISO 8601 timestamp"""
        now = datetime.now(UTC)
        return now.isoformat("T", "milliseconds").replace("+00:00", "Z")

    def _sign(self, timestamp, method, request_path, body=''):
        message = timestamp + method + request_path + (str(body) if body else '')
        mac = hmac.new(
            bytes(self.api_secret, encoding='utf8'),
            bytes(message, encoding='utf-8'),
            digestmod='sha256'
        )
        return base64.b64encode(mac.digest()).decode()

    def _get_headers(self, method, request_path, body=''):
        timestamp = self._get_timestamp()
        return {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': self._sign(timestamp, method, request_path, body),
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }

    def get_market_data(self, pairs):
        endpoint = '/api/v5/market/tickers'
        params = {'instType': 'SPOT'}
        headers = self._get_headers('GET', endpoint)
        
        response = requests.get(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Error fetching OKX data: {response.text}")
            
        data = response.json()
        market_data = {}
        
        for ticker in data['data']:
            inst_id = ticker['instId']
            if inst_id in pairs:
                market_data[inst_id] = {
                    'price': float(ticker['last']),
                    'change_24h': float(ticker['vol24h']),
                    'volume': float(ticker['volCcy24h']),
                    'high_24h': float(ticker['high24h']),
                    'low_24h': float(ticker['low24h']),
                    'timestamp': time.time()
                }
                
                # Calculate market strength indicator
                price = float(ticker['last'])
                high = float(ticker['high24h'])
                low = float(ticker['low24h'])
                market_data[inst_id]['market_strength'] = (
                    ((price - low) / (high - low if high != low else 1)) * 100
                )
        
        return market_data

    def handle_action(self, action, context):
        """Handle Eliza action requests"""
        if action['type'] == 'fetch_prices':
            pairs = context.get('config', {}).get('data_sources', {}).get('okx', {}).get('pairs', [])
            return self.get_market_data(pairs)
        return None 