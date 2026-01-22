"""Apewisdom provider for Reddit retail sentiment."""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from ..base import DataProvider, ProviderCapability, ProviderHealth

logger = logging.getLogger(__name__)


class ApewisdomProvider(DataProvider):
    """
    Apewisdom provider for Reddit sentiment tracking.
    
    Tracks stock mentions across Reddit (r/wallstreetbets, r/stocks, etc.)
    and provides mention volume + sentiment scores.
    
    FREE TIER:
    - Updates 2x per day (9 AM and 9 PM EST)
    - Historical data (30 days)
    - ~1000 requests/day limit
    
    Capabilities:
    - Mention volume (Reddit discussion volume)
    - Mention velocity (rate of change)
    - Sentiment/positivity score (0-1)
    - Rank tracking (position in trending list)
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key') or self._get_env_api_key()
        self.base_url = "https://apewisdom.io/api/v1.0"
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, Dict] = {}
        self._cache_duration = 3600  # Cache for 1 hour (updates are 2x/day anyway)
        self._last_request_time = 0
        self._min_request_interval = 1.0  # 1 second between requests
        
    def _get_env_api_key(self) -> Optional[str]:
        """Get API key from environment."""
        import os
        return os.getenv('APEWISDOM_API_KEY')
    
    def get_capabilities(self) -> List[ProviderCapability]:
        """Return provider capabilities."""
        return [
            ProviderCapability.SENTIMENT,  # Retail sentiment
            ProviderCapability.SOCIAL,     # Social media metrics
        ]
    
    async def initialize(self) -> bool:
        """Initialize the Apewisdom provider."""
        try:
            # Create aiohttp session
            self._session = aiohttp.ClientSession()
            
            # Test connection with a simple request
            try:
                url = f"{self.base_url}/filter/all-crypto-stocks"
                headers = self._get_headers()
                
                async with self._session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        self._is_available = True
                        self._last_health_check = datetime.now()
                        logger.info("✅ ApewisdomProvider initialized (Reddit sentiment tracking)")
                        return True
                    elif response.status == 401:
                        logger.error("❌ Apewisdom API key invalid")
                        self._is_available = False
                        return False
                    else:
                        logger.warning(f"⚠️  Apewisdom returned status {response.status}")
                        self._is_available = False
                        return False
                        
            except asyncio.TimeoutError:
                logger.error("❌ Apewisdom connection timeout")
                self._is_available = False
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize ApewisdomProvider: {e}")
            self._is_available = False
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with optional API key."""
        headers = {
            'User-Agent': 'MomentumBot/1.0',
            'Accept': 'application/json'
        }
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers
    
    async def _rate_limit_wait(self):
        """Enforce rate limiting."""
        now = asyncio.get_event_loop().time()
        time_since_last = now - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            wait_time = self._min_request_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self._last_request_time = asyncio.get_event_loop().time()
    
    def _get_cache_key(self, symbol: str, metric: str) -> str:
        """Generate cache key."""
        return f"{symbol}:{metric}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self._cache:
            return False
        
        cached = self._cache[cache_key]
        age = (datetime.now() - cached['timestamp']).total_seconds()
        return age < self._cache_duration
    
    async def get_stock_sentiment(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get Reddit sentiment for a stock symbol.
        
        Args:
            symbol: Stock symbol (e.g., "TSLA")
        
        Returns:
            {
                'mentions': int,              # Number of Reddit mentions
                'mentions_24h_ago': int,      # Mentions 24 hours ago
                'rank': int,                  # Rank in trending list
                'rank_24h_ago': int,          # Rank 24 hours ago
                'positivity': float,          # Sentiment score (0-1)
                'mentions_change': float,     # % change in mentions
                'rank_change': int,           # Change in rank
                'timestamp': datetime
            }
        """
        cache_key = self._get_cache_key(symbol, "sentiment")
        
        # Check cache
        if self._is_cache_valid(cache_key):
            logger.debug(f"Using cached Apewisdom data for {symbol}")
            return self._cache[cache_key]['data']
        
        if not self._is_available:
            return None
        
        try:
            # Rate limit
            await self._rate_limit_wait()
            
            # Fetch trending stocks (contains sentiment data)
            url = f"{self.base_url}/filter/all-crypto-stocks"
            headers = self._get_headers()
            
            async with self._session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    logger.debug(f"Apewisdom returned status {response.status} for {symbol}")
                    return None
                
                data = await response.json()
                
                # Find the symbol in results
                results = data.get('results', [])
                stock_data = None
                
                for item in results:
                    if item.get('ticker', '').upper() == symbol.upper():
                        stock_data = item
                        break
                
                if not stock_data:
                    logger.debug(f"Symbol {symbol} not found in Apewisdom trending list")
                    return None
                
                # Parse data
                mentions = stock_data.get('mentions', 0)
                mentions_24h_ago = stock_data.get('mentions_24h_ago', 0)
                rank = stock_data.get('rank', 0)
                rank_24h_ago = stock_data.get('rank_24h_ago', 0)
                positivity = stock_data.get('positivity', 0.5)  # 0-1 scale
                
                # Calculate changes
                if mentions_24h_ago > 0:
                    mentions_change = ((mentions - mentions_24h_ago) / mentions_24h_ago) * 100
                else:
                    mentions_change = 100.0 if mentions > 0 else 0.0
                
                rank_change = rank_24h_ago - rank if rank_24h_ago > 0 else 0
                
                result = {
                    'mentions': mentions,
                    'mentions_24h_ago': mentions_24h_ago,
                    'rank': rank,
                    'rank_24h_ago': rank_24h_ago,
                    'positivity': positivity,
                    'mentions_change': mentions_change,
                    'rank_change': rank_change,
                    'timestamp': datetime.now()
                }
                
                # Cache result
                self._cache[cache_key] = {
                    'data': result,
                    'timestamp': datetime.now()
                }
                
                logger.debug(
                    f"Apewisdom for {symbol}: "
                    f"mentions={mentions}, "
                    f"change={mentions_change:+.0f}%, "
                    f"rank=#{rank}, "
                    f"positivity={positivity:.2f}"
                )
                
                return result
                
        except asyncio.TimeoutError:
            logger.debug(f"Apewisdom timeout for {symbol}")
            return None
        except Exception as e:
            logger.debug(f"Apewisdom error for {symbol}: {e}")
            return None
    
    async def get_trending_stocks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all currently trending stocks on Reddit.
        
        Args:
            limit: Maximum number of stocks to return
            
        Returns:
            List of trending stocks with their Reddit metrics
        """
        if not self._is_available:
            return []
        
        try:
            await self._rate_limit_wait()
            
            url = f"{self.base_url}/filter/all-crypto-stocks"
            headers = self._get_headers()
            
            async with self._session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                results = data.get('results', [])
                
                trending = []
                for item in results[:limit]:
                    ticker = item.get('ticker', '')
                    if ticker:
                        trending.append({
                            'symbol': ticker.upper(),
                            'mentions': item.get('mentions', 0),
                            'mentions_24h_ago': item.get('mentions_24h_ago', 0),
                            'rank': item.get('rank', 0),
                            'positivity': item.get('positivity', 0.5),
                        })
                
                return trending
                
        except Exception as e:
            logger.warning(f"Failed to get trending stocks: {e}")
            return []
    
    async def health_check(self) -> ProviderHealth:
        """Check provider health."""
        if not self._is_available:
            return ProviderHealth(
                provider_name=self.name,
                is_available=False,
                last_check=datetime.now(),
                error_message="Provider not initialized"
            )
        
        try:
            # Try fetching trending list
            url = f"{self.base_url}/filter/all-crypto-stocks"
            headers = self._get_headers()
            
            async with self._session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    self._last_health_check = datetime.now()
                    return ProviderHealth(
                        provider_name=self.name,
                        is_available=True,
                        last_check=datetime.now()
                    )
                return ProviderHealth(
                    provider_name=self.name,
                    is_available=False,
                    last_check=datetime.now(),
                    error_message=f"HTTP {response.status}"
                )
                
        except Exception as e:
            logger.warning(f"ApewisdomProvider health check failed: {e}")
            return ProviderHealth(
                provider_name=self.name,
                is_available=False,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    async def close(self):
        """Clean up resources."""
        if self._session:
            await self._session.close()
        self._cache.clear()
        logger.debug("ApewisdomProvider closed")

