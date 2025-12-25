"""Google Trends provider for retail attention metrics."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from ..base import DataProvider, ProviderCapability

logger = logging.getLogger(__name__)


class GoogleTrendsProvider(DataProvider):
    """
    Google Trends provider using pytrends.
    
    Provides retail attention metrics based on Google search interest.
    NO API KEY REQUIRED - completely free!
    
    Capabilities:
    - Search interest trends (0-100 scale)
    - Interest velocity (rate of change)
    - Breakout detection
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.pytrends = None
        self._last_request_time = 0
        self._min_request_interval = 5.0  # Base delay: 5 seconds
        self._current_delay = 5.0  # Adaptive delay (increases on rate limit)
        self._max_delay = 30.0  # Max delay cap
        self._cache: Dict[str, Dict] = {}
        self._cache_duration = 300  # Cache for 5 minutes
        self._max_retries = 3  # Retry failed requests
        self._consecutive_failures = 0  # Track failures for adaptive backoff
        
    def get_capabilities(self) -> List[ProviderCapability]:
        """Return provider capabilities."""
        return [
            ProviderCapability.SENTIMENT,  # Retail sentiment proxy
            ProviderCapability.TECHNICALS,  # Trend analysis
        ]
    
    async def initialize(self) -> bool:
        """Initialize the Google Trends client."""
        try:
            # Import pytrends
            from pytrends.request import TrendReq
            
            # Initialize client with minimal parameters (compatible with all versions)
            self.pytrends = TrendReq(
                hl='en-US',
                tz=360  # US timezone
            )
            
            self._is_available = True
            self._last_health_check = datetime.now()
            logger.info("✅ GoogleTrendsProvider initialized (FREE, NO API KEY!)")
            return True
            
        except ImportError:
            logger.warning(
                "⚠️  pytrends not installed. Install with: pip install pytrends"
            )
            self._is_available = False
            self._error_message = "pytrends library not installed"
            return False
        except Exception as e:
            logger.error(f"❌ Failed to initialize GoogleTrendsProvider: {e}")
            self._is_available = False
            self._error_message = str(e)
            return False
    
    async def _rate_limit_wait(self):
        """Enforce adaptive rate limiting with exponential backoff."""
        now = asyncio.get_event_loop().time()
        time_since_last = now - self._last_request_time
        
        # Use current adaptive delay (increases after rate limits)
        if time_since_last < self._current_delay:
            wait_time = self._current_delay - time_since_last
            logger.debug(f"Google Trends rate limit: waiting {wait_time:.1f}s (adaptive delay: {self._current_delay:.1f}s)")
            await asyncio.sleep(wait_time)
        
        self._last_request_time = asyncio.get_event_loop().time()
    
    def _on_success(self):
        """Called after successful request - gradually reduce delay."""
        self._consecutive_failures = 0
        # Gradually reduce delay back to minimum (by 10% each success)
        if self._current_delay > self._min_request_interval:
            self._current_delay = max(
                self._min_request_interval,
                self._current_delay * 0.9
            )
            logger.debug(f"Google Trends: Reduced delay to {self._current_delay:.1f}s")
    
    def _on_rate_limit(self):
        """Called when rate limited - increase delay exponentially."""
        self._consecutive_failures += 1
        old_delay = self._current_delay
        # Exponential backoff: double the delay, capped at max
        self._current_delay = min(self._max_delay, self._current_delay * 2)
        logger.warning(
            f"Google Trends rate limited! Increasing delay: {old_delay:.1f}s → {self._current_delay:.1f}s "
            f"(failures: {self._consecutive_failures})"
        )
    
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
    
    async def get_search_interest(
        self,
        symbol: str,
        timeframe: str = 'now 7-d'
    ) -> Optional[Dict[str, Any]]:
        """
        Get Google search interest for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., "TSLA")
            timeframe: Time range (e.g., 'now 7-d', 'now 1-d', 'today 1-m')
        
        Returns:
            {
                'interest_over_time': pandas.DataFrame with interest scores (0-100),
                'current_interest': float (0-100),
                'average_interest': float (0-100),
                'velocity': float (rate of change),
                'is_breakout': bool (interest > 2x average)
            }
        """
        cache_key = self._get_cache_key(symbol, f"interest_{timeframe}")
        
        # Check cache
        if self._is_cache_valid(cache_key):
            logger.debug(f"Using cached Google Trends data for {symbol}")
            return self._cache[cache_key]['data']
        
        if not self._is_available:
            return None
        
        # Retry logic with exponential backoff
        for attempt in range(self._max_retries):
            try:
                # Rate limit
                await self._rate_limit_wait()
                
                # Build search query - try multiple variations
                queries = [
                    f"{symbol} stock",
                    symbol,
                ]
                
                # Build payload and get data (synchronous call in executor)
                loop = asyncio.get_event_loop()
                interest_df = await loop.run_in_executor(
                    None,
                    self._fetch_trends,
                    queries,
                    timeframe
                )
                
                if interest_df is None or interest_df.empty:
                    logger.debug(f"No Google Trends data for {symbol}")
                    return None
                
                # Calculate metrics
                # Take the max interest across all query variations
                interest_values = interest_df.max(axis=1).values
                
                if len(interest_values) == 0:
                    return None
                
                current_interest = float(interest_values[-1])
                average_interest = float(interest_values.mean())
                
                # Calculate velocity (slope of recent trend)
                if len(interest_values) >= 2:
                    velocity = float(interest_values[-1] - interest_values[0])
                else:
                    velocity = 0.0
                
                # Detect breakout (current > 2x average)
                is_breakout = current_interest > (2.0 * average_interest) if average_interest > 0 else False
                
                result = {
                    'interest_over_time': interest_df,
                    'current_interest': current_interest,
                    'average_interest': average_interest,
                    'velocity': velocity,
                    'is_breakout': is_breakout,
                    'timestamp': datetime.now()
                }
                
                # Cache result
                self._cache[cache_key] = {
                    'data': result,
                    'timestamp': datetime.now()
                }
                
                # Success! Reduce delay
                self._on_success()
                
                logger.debug(
                    f"Google Trends for {symbol}: "
                    f"interest={current_interest:.1f}, "
                    f"velocity={velocity:.1f}, "
                    f"breakout={is_breakout}"
                )
                
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if it's a rate limit error (429 or similar)
                is_rate_limit = (
                    '429' in error_msg or
                    'rate limit' in error_msg or
                    'too many requests' in error_msg or
                    'quota' in error_msg
                )
                
                if is_rate_limit:
                    self._on_rate_limit()
                    
                    if attempt < self._max_retries - 1:
                        retry_delay = self._current_delay * (attempt + 1)  # Increase delay each retry
                        logger.warning(
                            f"Google Trends rate limited for {symbol}, "
                            f"retry {attempt + 1}/{self._max_retries} in {retry_delay:.1f}s"
                        )
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        logger.warning(
                            f"Google Trends rate limited for {symbol} after {self._max_retries} retries, giving up"
                        )
                        return None
                else:
                    # Non-rate-limit error, don't retry
                    logger.debug(f"Google Trends error for {symbol}: {e}")
                    import traceback
                    logger.debug(f"Traceback: {traceback.format_exc()}")
                    return None
        
        return None
    
    def _fetch_trends(self, queries: List[str], timeframe: str):
        """Fetch trends data (synchronous, for executor)."""
        try:
            logger.debug(f"Fetching trends for queries: {queries}, timeframe: {timeframe}")
            self.pytrends.build_payload(queries, timeframe=timeframe)
            result = self.pytrends.interest_over_time()
            logger.debug(f"Trends result type: {type(result)}, empty: {result.empty if hasattr(result, 'empty') else 'N/A'}")
            return result
        except Exception as e:
            logger.warning(f"Trends fetch error: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None
    
    async def health_check(self) -> bool:
        """Check provider health with a simple query."""
        if not self._is_available:
            return False
        
        try:
            # Try a simple query for a popular stock
            result = await self.get_search_interest("AAPL", timeframe='now 7-d')
            
            if result is not None:
                self._last_health_check = datetime.now()
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"GoogleTrendsProvider health check failed: {e}")
            return False
    
    async def close(self):
        """Clean up resources."""
        self.pytrends = None
        self._cache.clear()
        logger.debug("GoogleTrendsProvider closed")

