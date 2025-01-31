import os
import requests
import time
from datetime import datetime, timedelta
from loguru import logger

class MarketDataHandler:
    def __init__(self):
        self.session = requests.Session()
        # Add headers to avoid API blocks
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
        
    def get_unisat_data(self, token):
        """Get data from Unisat API for BRC20 tokens"""
        try:
            # Get BRC20 token data from Unisat
            url = "https://open-api.unisat.io/v1/indexer/brc20/ticker"
            params = {
                'ticker': token.lower()
            }
            headers = {
                'Authorization': f'Bearer {os.getenv("UNISAT_API_KEY", "")}'
            }
            response = self.session.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') == 0 and data.get('data'):
                token_data = data['data']
                return {
                    'price': float(token_data['latestPrice']),
                    'volume': float(token_data['volume24h']),
                    'change_24h': float(token_data['priceChange24h'])
                }
            
            # Fallback to OKX for ORDI
            if token.lower() == 'ordi':
                return self.get_okx_data('ORDI')
            return None
        except Exception as e:
            logger.error(f"Error fetching Unisat data for {token}: {str(e)}")
            # Fallback to OKX for ORDI
            if token.lower() == 'ordi':
                try:
                    return self.get_okx_data('ORDI')
                except Exception as e2:
                    logger.error(f"Error fetching ORDI data from fallback: {str(e2)}")
            return None

    def get_okx_data(self, symbol):
        """Get data from OKX API"""
        try:
            # Get ticker data
            url = "https://www.okx.com/api/v5/market/ticker"
            params = {
                'instId': f"{symbol}-USDT"
            }
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            logger.debug(f"OKX ticker response for {symbol}: {data}")
            
            if data['code'] == '0' and data['data']:
                ticker = data['data'][0]
                price = float(ticker['last'])
                volume_usdt = float(ticker['volCcy24h'])
                btc_price = self.get_btc_price()
                
                logger.debug(f"OKX {symbol} price: {price}, volume: {volume_usdt}, btc_price: {btc_price}")
                
                # Get 24h price change
                url_candle = "https://www.okx.com/api/v5/market/candles"
                params_candle = {
                    'instId': f"{symbol}-USDT",
                    'bar': '1D',
                    'limit': '2'
                }
                response_candle = self.session.get(url_candle, params=params_candle)
                response_candle.raise_for_status()
                candle_data = response_candle.json()
                
                logger.debug(f"OKX candle response for {symbol}: {candle_data}")
                
                if candle_data['code'] == '0' and len(candle_data['data']) >= 2:
                    current_price = float(candle_data['data'][0][4])
                    prev_price = float(candle_data['data'][1][4])
                    price_change = ((current_price - prev_price) / prev_price) * 100
                    logger.debug(f"OKX {symbol} price change calculation: current={current_price}, prev={prev_price}, change={price_change}%")
                else:
                    price_change = 0
                    logger.warning(f"Could not calculate price change for {symbol}, using 0")
                
                return {
                    'price': price,
                    'volume': volume_usdt / btc_price if btc_price else 0,
                    'change_24h': price_change
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching OKX data for {symbol}: {str(e)}")
            return None

    def get_magiceden_data(self, token):
        """Get data from Magic Eden API for Runes"""
        try:
            # Try OKX first for DOGS
            if token.lower() == 'dogs':
                okx_data = self.get_okx_data('DOGS')
                if okx_data:
                    return okx_data

            # Fallback to Magic Eden API
            url = "https://api-mainnet.magiceden.dev/v2/ord/btc/runes/stats"
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Find the token in the list
            token_data = next((item for item in data if item['symbol'].lower() == token.lower()), None)
            if token_data:
                btc_price = self.get_btc_price()
                volume_btc = float(token_data.get('volume24h', 0))
                
                return {
                    'price': float(token_data['floorPrice']),
                    'volume': volume_btc,
                    'change_24h': float(token_data.get('change24h', 0))
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching Magic Eden data for {token}: {str(e)}")
            return None

    def get_coingecko_id(self, coin_id):
        """Get correct CoinGecko ID using search API"""
        try:
            # First check our known mappings
            coin_id_map = {
                'stamp': 'stamp',  # We'll try to find the correct ID
                'ordi': 'ordinals',
                'dogs': 'doginals',
                'ckb': 'nervos-network',
                'fb': 'friendtech'
            }
            
            mapped_id = coin_id_map.get(coin_id.lower())
            if mapped_id:
                return mapped_id
                
            # If not in our map, try to search
            url = "https://pro-api.coingecko.com/api/v3/search"
            headers = {
                'x-cg-pro-api-key': 'CG-zNWWNicxnjMZYsB1TwFhWrdb'
            }
            params = {
                'query': coin_id
            }
            
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and 'coins' in data and len(data['coins']) > 0:
                # Find exact match first
                for coin in data['coins']:
                    if coin['symbol'].lower() == coin_id.lower():
                        return coin['id']
                # If no exact match, return first result
                return data['coins'][0]['id']
                
            return coin_id  # Return original if nothing found
            
        except Exception as e:
            logger.error(f"Error searching CoinGecko ID for {coin_id}: {str(e)}")
            return coin_id

    def get_coingecko_data(self, coin_id):
        """Get data from CoinGecko API with proper error handling"""
        try:
            # Get the correct CoinGecko ID
            cg_id = self.get_coingecko_id(coin_id)
            
            # Try Pro API first with coins endpoint
            url = f"https://pro-api.coingecko.com/api/v3/coins/{cg_id}"
            headers = {
                'x-cg-pro-api-key': 'CG-zNWWNicxnjMZYsB1TwFhWrdb'
            }
            params = {
                'localization': 'false',
                'tickers': 'false',
                'community_data': 'false',
                'developer_data': 'false',
                'sparkline': 'false'
            }
            
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            
            # Check if we got rate limited or other error
            if response.status_code in [429, 403]:
                logger.warning(f"Rate limited or auth error from CoinGecko Pro API: {response.status_code}")
                raise requests.exceptions.RequestException("Rate limited")
            elif response.status_code == 404:
                logger.warning(f"Token {cg_id} not found in CoinGecko Pro API")
                raise requests.exceptions.RequestException("Token not found")
                
            response.raise_for_status()
            data = response.json()
            
            if data and isinstance(data, dict):
                btc_price = self.get_btc_price()
                
                # Extract data with proper error handling
                try:
                    market_data = data.get('market_data', {})
                    price = float(market_data.get('current_price', {}).get('usd', 0) or 0)
                    volume = float(market_data.get('total_volume', {}).get('usd', 0) or 0)
                    change = float(market_data.get('price_change_percentage_24h', 0) or 0)
                    
                    # Basic validation
                    if price <= 0 or volume <= 0:
                        logger.warning(f"Invalid price or volume from CoinGecko for {cg_id}")
                        return None
                        
                    return {
                        'price': price,
                        'volume': volume / btc_price if btc_price else 0,
                        'change_24h': change
                    }
                except (ValueError, TypeError, KeyError) as e:
                    logger.error(f"Error parsing CoinGecko data values for {cg_id}: {str(e)}")
                    return None
            
            logger.warning(f"Invalid response format from CoinGecko for {cg_id}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed to CoinGecko Pro API for {cg_id}: {str(e)}")
            # Fallback to free API
            try:
                url = f"https://api.coingecko.com/api/v3/coins/{cg_id}"
                params = {
                    'localization': 'false',
                    'tickers': 'false',
                    'community_data': 'false',
                    'developer_data': 'false',
                    'sparkline': 'false'
                }
                response = self.session.get(url, params=params, timeout=5)
                response.raise_for_status()
                data = response.json()
                
                if data and isinstance(data, dict):
                    btc_price = self.get_btc_price()
                    market_data = data.get('market_data', {})
                    
                    price = float(market_data.get('current_price', {}).get('usd', 0) or 0)
                    volume = float(market_data.get('total_volume', {}).get('usd', 0) or 0)
                    change = float(market_data.get('price_change_percentage_24h', 0) or 0)
                    
                    if price <= 0 or volume <= 0:
                        return None
                        
                    return {
                        'price': price,
                        'volume': volume / btc_price if btc_price else 0,
                        'change_24h': change
                    }
            except Exception as e2:
                logger.error(f"Fallback to free API also failed for {cg_id}: {str(e2)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching CoinGecko data for {cg_id}: {str(e)}")
            return None

    def get_gateio_data(self, symbol):
        """Get data from Gate.io API"""
        try:
            # Map symbols to Gate.io trading pairs
            pair_map = {
                'STAMP': ['STAMP_USDT', 'STAMP_BTC'],  # Try both USDT and BTC pairs
                'ORDI': ['ORDI_USDT', 'ORDI_BTC'],
                'DOGS': ['DOGS_USDT', 'DOGS_BTC'],
                'CKB': ['CKB_USDT'],
                'FB': ['FB_USDT']
            }
            
            # Get the correct trading pairs
            currency_pairs = pair_map.get(symbol.upper(), [])
            if not currency_pairs:
                return None
            
            btc_price = self.get_btc_price()
            if not btc_price:
                logger.error("Failed to get BTC price for conversion")
                return None

            for currency_pair in currency_pairs:
                try:
                    # First try to get ticker data
                    url = "https://api.gateio.ws/api/v4/spot/tickers"
                    params = {
                        'currency_pair': currency_pair
                    }
                    headers = {
                        'Accept': 'application/json',
                        'User-Agent': 'Mozilla/5.0'
                    }
                    response = self.session.get(url, params=params, headers=headers, timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data and isinstance(data, list) and len(data) > 0:
                            ticker = data[0]
                            
                            try:
                                price = float(ticker['last'])
                                volume = float(ticker['quote_volume'])
                                change = float(ticker['change_percentage'])
                                
                                # Convert BTC prices to USD if needed
                                if currency_pair.endswith('_BTC'):
                                    price = price * btc_price
                                    volume = volume * btc_price
                                
                                if price > 0 and volume > 0:
                                    return {
                                        'price': price,
                                        'volume': volume / btc_price,  # Convert volume to BTC
                                        'change_24h': change
                                    }
                            except (ValueError, TypeError, KeyError) as e:
                                logger.error(f"Error parsing Gate.io ticker data for {currency_pair}: {str(e)}")
                                continue
                    
                    # If ticker fails, try candlestick data
                    url = "https://api.gateio.ws/api/v4/spot/candlesticks"
                    params = {
                        'currency_pair': currency_pair,
                        'interval': '1d',
                        'limit': 2
                    }
                    response = self.session.get(url, params=params, headers=headers, timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data and isinstance(data, list) and len(data) >= 2:
                            try:
                                current = data[0]
                                previous = data[1]
                                
                                price = float(current[2])  # Close price
                                volume = float(current[6])  # Quote volume
                                prev_price = float(previous[2])
                                change = ((price - prev_price) / prev_price) * 100
                                
                                # Convert BTC prices to USD if needed
                                if currency_pair.endswith('_BTC'):
                                    price = price * btc_price
                                    volume = volume * btc_price
                                
                                if price > 0 and volume > 0:
                                    return {
                                        'price': price,
                                        'volume': volume / btc_price,  # Convert volume to BTC
                                        'change_24h': change
                                    }
                            except (ValueError, TypeError, IndexError) as e:
                                logger.error(f"Error parsing Gate.io candlestick data for {currency_pair}: {str(e)}")
                                continue
                except Exception as e:
                    logger.error(f"Error fetching Gate.io data for {currency_pair}: {str(e)}")
                    continue
            
            # If all pairs fail, try market stats as last resort
            url = "https://api.gateio.ws/api/v4/spot/markets"
            response = self.session.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                for currency_pair in currency_pairs:
                    market_data = next((item for item in data if item.get('id') == currency_pair), None)
                    if market_data:
                        try:
                            price = float(market_data.get('last', 0))
                            volume = float(market_data.get('quote_volume', 0))
                            change = float(market_data.get('change_percentage', 0))
                            
                            # Convert BTC prices to USD if needed
                            if currency_pair.endswith('_BTC'):
                                price = price * btc_price
                                volume = volume * btc_price
                            
                            if price > 0 and volume > 0:
                                return {
                                    'price': price,
                                    'volume': volume / btc_price,  # Convert volume to BTC
                                    'change_24h': change
                                }
                        except (ValueError, TypeError) as e:
                            logger.error(f"Error parsing Gate.io market data for {currency_pair}: {str(e)}")
                            continue
            
            return None
        except Exception as e:
            logger.error(f"Error fetching Gate.io data for {symbol}: {str(e)}")
            return None

    def get_stamp_data(self):
        """Get data for STAMP token from Kucoin API"""
        try:
            url = "https://api.kucoin.com/api/v1/market/stats"
            params = {'symbol': 'STAMP-USDT'}
            response = self.session.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == '200000' and data.get('data'):
                    market_data = data['data']
                    try:
                        price = float(market_data.get('last', 0))
                        volume = float(market_data.get('volValue', 0))
                        change = float(market_data.get('changeRate', 0)) * 100
                        btc_price = self.get_btc_price()
                        
                        if price > 0 and volume > 0 and btc_price:
                            return {
                                'price': price,
                                'volume': volume / btc_price,
                                'change_24h': change
                            }
                    except (ValueError, TypeError) as e:
                        logger.error(f"Data parsing error from Kucoin: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error fetching STAMP data from Kucoin: {str(e)}")
            try:
                # Fallback to mock data for testing
                mock_data = self.get_mock_data()
                return mock_data.get('stamp', None)
            except Exception as e:
                logger.error(f"Error getting mock data for STAMP: {str(e)}")
                return None

    def get_binance_data(self, symbol):
        """Get data from Binance API"""
        try:
            # Get 24h ticker data
            url = "https://api.binance.com/api/v3/ticker/24hr"
            params = {
                'symbol': f"{symbol}USDT"
            }
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data:
                btc_price = self.get_btc_price()
                volume_usdt = float(data['quoteVolume'])
                
                return {
                    'price': float(data['lastPrice']),
                    'volume': volume_usdt / btc_price if btc_price else 0,
                    'change_24h': float(data['priceChangePercent'])
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching Binance data for {symbol}: {str(e)}")
            return None

    def get_btc_price(self):
        """Get current BTC price in USD from OKX"""
        try:
            url = "https://www.okx.com/api/v5/market/ticker"
            params = {'instId': 'BTC-USDT'}
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if data['code'] == '0' and data['data']:
                return float(data['data'][0]['last'])
            return None
        except Exception as e:
            logger.error(f"Error fetching BTC price from OKX: {str(e)}")
            return None

    def get_cat20_data(self, token):
        """Get data from UniSat CAT Market API"""
        try:
            # Get CAT20 market data
            endpoints = [
                "https://open-api.unisat.io/v2/market/cat/ticker",
                "https://open-api.unisat.io/v2/market/cat/stats",
                "https://open-api.unisat.io/v2/market/cat-dex/stats"
            ]
            
            headers = {
                'Authorization': f'Bearer {os.getenv("UNISAT_API_KEY", "")}',
                'Accept': 'application/json'
            }
            
            all_data = []
            btc_price = self.get_btc_price()
            
            for url in endpoints:
                try:
                    params = {'tick': token.lower()} if 'cat-dex' in url else {}
                    response = self.session.get(url, headers=headers, params=params, timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('code') == 0 and data.get('data'):
                            market_data = data['data']
                            try:
                                # Find token in the market data
                                token_data = None
                                if isinstance(market_data, list):
                                    token_data = next((item for item in market_data if 
                                        item.get('tick', '').lower() == token.lower() or 
                                        item.get('ticker', '').lower() == token.lower()), None)
                                else:
                                    token_data = market_data
                                
                                if token_data:
                                    # Try different field names
                                    price_fields = ['price', 'lastPrice', 'last', 'currentPrice']
                                    volume_fields = ['volume24h', 'volume', 'dailyVolume', 'vol24h']
                                    change_fields = ['priceChangePercent', 'priceChange24h', 'change24h', 'change']
                                    
                                    price = 0
                                    volume = 0
                                    change = 0
                                    
                                    for field in price_fields:
                                        if token_data.get(field):
                                            try:
                                                price = float(token_data[field])
                                                break
                                            except (ValueError, TypeError):
                                                continue
                                                
                                    for field in volume_fields:
                                        if token_data.get(field):
                                            try:
                                                volume = float(token_data[field])
                                                break
                                            except (ValueError, TypeError):
                                                continue
                                                
                                    for field in change_fields:
                                        if token_data.get(field):
                                            try:
                                                change = float(token_data[field])
                                                break
                                            except (ValueError, TypeError):
                                                continue
                                    
                                    if price > 0 and volume > 0:
                                        all_data.append({
                                            'price': price,
                                            'volume': volume / btc_price if btc_price else 0,
                                            'change_24h': change
                                        })
                            except (ValueError, TypeError) as e:
                                logger.error(f"Data parsing error from {url}: {str(e)}")
                except Exception as e:
                    logger.error(f"Error fetching data from {url}: {str(e)}")
                    continue
            
            # If we have multiple data points, aggregate them
            if len(all_data) > 0:
                # Calculate median values to avoid outliers
                prices = [d['price'] for d in all_data if d['price'] > 0]
                volumes = [d['volume'] for d in all_data if d['volume'] > 0]
                changes = [d['change_24h'] for d in all_data if abs(d['change_24h']) <= 100]
                
                if prices and volumes:
                    return {
                        'price': sorted(prices)[len(prices)//2],  # Median price
                        'volume': sum(volumes) / len(volumes),    # Average volume
                        'change_24h': sum(changes) / len(changes) if changes else 0  # Average change
                    }
                elif len(all_data) > 0:
                    # If we don't have all metrics, use the first available complete data
                    return next((d for d in all_data if d['price'] > 0 and d['volume'] > 0), all_data[0])
                    
        except Exception as e:
            logger.error(f"Error fetching CAT20 data for {token}: {str(e)}")
        return None

    def get_fb_data(self):
        """Get data for FB token from Gate.io API"""
        try:
            url = "https://api.gateio.ws/api/v4/spot/tickers"
            params = {'currency_pair': 'FB_USDT'}
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0:
                    ticker = data[0]
                    try:
                        price = float(ticker['last'])
                        volume = float(ticker['quote_volume'])
                        change = float(ticker['change_percentage'])
                        btc_price = self.get_btc_price()
                        
                        if price > 0 and volume > 0 and btc_price:
                            return {
                                'price': price,
                                'volume': volume / btc_price,
                                'change_24h': change
                            }
                    except (ValueError, TypeError) as e:
                        logger.error(f"Data parsing error from Gate.io: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error fetching FB data from Gate.io: {str(e)}")
            try:
                mock_data = self.get_mock_data()
                return mock_data.get('fb', None)
            except Exception as e:
                logger.error(f"Error getting mock data for FB: {str(e)}")
                return None

    def get_all_market_data(self):
        """Get market data for all tracked assets"""
        market_data = {}
        
        # Get DOGS data from OKX
        dogs_data = self.get_okx_data('DOGS')
        if dogs_data:
            market_data['dogs'] = {
                'protocol': 'Runes',
                **dogs_data
            }
            
        # Get STAMP data from Kucoin
        stamp_data = self.get_stamp_data()
        if stamp_data:
            market_data['stamp'] = {
                'protocol': 'SRC20',
                **stamp_data
            }
            
        # Get ORDI data from OKX
        ordi_data = self.get_okx_data('ORDI')
        if ordi_data:
            market_data['ordi'] = {
                'protocol': 'BRC20',
                **ordi_data
            }
            
        # Get FB data from Binance
        fb_data = self.get_fb_data()
        if fb_data:
            market_data['fb'] = {
                'protocol': 'FB',
                **fb_data
            }
            
        # Get CKB data from Gate.io
        try:
            url = "https://api.gateio.ws/api/v4/spot/tickers"
            params = {'currency_pair': 'CKB_USDT'}
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list):
                    for ticker in data:
                        if ticker.get('currency_pair') == 'CKB_USDT':
                            try:
                                price = float(ticker['last'])
                                volume = float(ticker['quote_volume'])
                                change = float(ticker['change_percentage'])
                                btc_price = self.get_btc_price()
                                
                                if price > 0 and volume > 0 and btc_price:
                                    market_data['ckb'] = {
                                        'protocol': 'CKB',
                                        'price': price,
                                        'volume': volume / btc_price,
                                        'change_24h': change
                                    }
                                    break
                            except (ValueError, TypeError) as e:
                                logger.error(f"Data parsing error from Gate.io for CKB: {str(e)}")
        except Exception as e:
            logger.error(f"Error fetching CKB data from Gate.io: {str(e)}")
            
        # Calculate overall market trend
        changes = [data['change_24h'] for data in market_data.values() if data]
        market_data['overall_trend'] = 'up' if sum(changes) > 0 else 'down'
            
        return market_data

    def format_market_update(self, market_data):
        """Format market data into a tweet"""
        trend_word = "上升" if market_data.get('overall_trend') == 'up' else "下降"
        message = f"今日比特币生态市值整体{trend_word}，\n\n"

        # Sort assets by volume
        sorted_assets = sorted(
            [(k, v) for k, v in market_data.items() if k != 'overall_trend' and v and v.get('price', 0) > 0],
            key=lambda x: x[1]['volume'] if x[1].get('volume', 0) > 0 else 0,
            reverse=True
        )

        for symbol, data in sorted_assets:
            change = data['change_24h']
            change_symbol = "上升" if change > 0 else "下降"
            
            # Format price based on its value
            price = data['price']
            if price < 0.001:
                price_str = f"{price:.6f}"
            elif price < 0.01:
                price_str = f"{price:.5f}"
            elif price < 0.1:
                price_str = f"{price:.4f}"
            elif price < 1:
                price_str = f"{price:.3f}"
            elif price < 100:
                price_str = f"{price:.2f}"
            else:
                price_str = f"{price:.1f}"
            
            message += f"{data['protocol']}协议的${symbol}成交量{data['volume']:.2f}比特币，"
            message += f"单价{price_str}美金，"
            message += f"比昨日{change_symbol}{abs(change):.1f}%；\n"

        return message.strip()

    def get_mock_data(self):
        """Generate mock market data for testing"""
        mock_data = {
            'dogs': {
                'protocol': 'Runes',
                'price': 0.82,
                'volume': 0.55,
                'change_24h': 35.5
            },
            'stamp': {
                'protocol': 'SRC20',
                'price': 0.48,
                'volume': 0.22,
                'change_24h': -15.3
            },
            'ordi': {
                'protocol': 'BRC20',
                'price': 152.45,
                'volume': 1.25,
                'change_24h': 5.8
            },
            'fb': {
                'protocol': 'FB',
                'price': 0.31,
                'volume': 2.35,
                'change_24h': 8.2
            },
            'ckb': {
                'protocol': 'CKB',
                'price': 0.022,
                'volume': 1.85,
                'change_24h': -2.1
            }
        }
        
        # Calculate overall market trend
        changes = [data['change_24h'] for data in mock_data.values()]
        mock_data['overall_trend'] = 'up' if sum(changes) > 0 else 'down'
        
        return mock_data

    def debug_market_update(self):
        """Generate and format a mock market update for testing"""
        mock_data = self.get_mock_data()
        return self.format_market_update(mock_data)                                                                                                                                                    