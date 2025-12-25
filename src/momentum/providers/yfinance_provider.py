"""Yahoo Finance data provider."""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import structlog

try:
    import yfinance as yf
except ImportError:
    yf = None

from src.momentum.base import DataProvider, ProviderHealth

logger = structlog.get_logger()


class YFinanceProvider(DataProvider):
    """Provider for Yahoo Finance data (free, unlimited)."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Yahoo Finance provider.
        
        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self._cache = {}  # Simple cache to avoid duplicate requests
        self._cache_ttl = 300  # 5 minutes
        
    async def initialize(self) -> bool:
        """Initialize provider.
        
        Returns:
            True if initialization successful
        """
        if yf is None:
            logger.error("yfinance_not_installed", 
                        message="Install with: pip install yfinance")
            return False
        
        # Test with a simple query
        try:
            await self.health_check()
            self._is_available = True
            logger.info("yfinance_initialized", note="No API key required, unlimited requests!")
            return True
        except Exception as e:
            logger.error("yfinance_initialization_failed", error=str(e))
            return False
    
    async def health_check(self) -> ProviderHealth:
        """Check Yahoo Finance API health.
        
        Returns:
            ProviderHealth status
        """
        try:
            # Test with a simple ticker fetch
            # Run in executor since yfinance is synchronous
            ticker = await asyncio.get_event_loop().run_in_executor(
                None, yf.Ticker, "AAPL"
            )
            
            # Try to get some data
            info = await asyncio.get_event_loop().run_in_executor(
                None, lambda: ticker.info
            )
            
            if info and 'symbol' in info:
                return ProviderHealth(
                    provider_name=self.name,
                    is_available=True,
                    last_check=datetime.utcnow()
                )
            else:
                return ProviderHealth(
                    provider_name=self.name,
                    is_available=False,
                    last_check=datetime.utcnow(),
                    error_message="Failed to fetch test data"
                )
                
        except Exception as e:
            return ProviderHealth(
                provider_name=self.name,
                is_available=False,
                last_check=datetime.utcnow(),
                error_message=str(e)
            )
    
    def _get_cache_key(self, symbol: str, data_type: str) -> str:
        """Generate cache key."""
        return f"{symbol}:{data_type}:{datetime.utcnow().strftime('%Y%m%d%H%M')}"
    
    def _get_cached(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if fresh."""
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if (datetime.utcnow() - timestamp).total_seconds() < self._cache_ttl:
                return data
        return None
    
    def _set_cached(self, cache_key: str, data: Any):
        """Store data in cache."""
        self._cache[cache_key] = (data, datetime.utcnow())
    
    async def get_daily_data(
        self,
        symbol: str,
        days: int = 30
    ) -> Optional[Dict[str, Any]]:
        """Get daily historical data.
        
        Args:
            symbol: Stock symbol
            days: Number of days of history
            
        Returns:
            Dict with daily data or None
        """
        cache_key = self._get_cache_key(symbol, f"daily_{days}")
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            # Create ticker
            ticker = await asyncio.get_event_loop().run_in_executor(
                None, yf.Ticker, symbol
            )
            
            # Get historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            hist = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: ticker.history(start=start_date, end=end_date)
            )
            
            if hist.empty:
                logger.warning("yfinance_no_data", symbol=symbol)
                return None
            
            # Convert to dict format
            result = {
                'symbol': symbol,
                'history': hist.to_dict('index')
            }
            
            self._set_cached(cache_key, result)
            logger.debug("yfinance_daily_data_fetched", symbol=symbol, days=len(hist))
            return result
            
        except Exception as e:
            logger.error("yfinance_request_failed", symbol=symbol, error=str(e))
            self.record_error(e)
            return None
    
    async def calculate_volume_metrics(self, symbol: str) -> Optional[Dict[str, float]]:
        """Calculate volume-based metrics.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict with volume metrics or None
        """
        data = await self.get_daily_data(symbol, days=30)
        if not data or 'history' not in data:
            return None
        
        try:
            history = data['history']
            
            # Get last 20 days of data
            dates = sorted(history.keys(), reverse=True)[:20]
            if len(dates) < 5:
                logger.warning("yfinance_insufficient_data", symbol=symbol, days=len(dates))
                return None
            
            volumes = [history[date]['Volume'] for date in dates]
            
            # Calculate metrics
            current_volume = volumes[0]
            avg_volume_20 = sum(volumes) / len(volumes)
            rvol = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1.0
            
            # Volume trend (last 5 days vs previous 15 days)
            recent_avg = sum(volumes[:5]) / 5
            older_avg = sum(volumes[5:]) / 15 if len(volumes) > 5 else recent_avg
            volume_trend = (recent_avg / older_avg - 1.0) if older_avg > 0 else 0.0
            
            result = {
                'current_volume': current_volume,
                'avg_volume_20': avg_volume_20,
                'rvol': rvol,
                'volume_trend': volume_trend
            }
            
            logger.debug("yfinance_volume_metrics", symbol=symbol, rvol=rvol)
            return result
            
        except Exception as e:
            logger.error("yfinance_volume_metrics_failed", symbol=symbol, error=str(e))
            return None
    
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current quote for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict with quote data or None
        """
        cache_key = self._get_cache_key(symbol, "quote")
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            ticker = await asyncio.get_event_loop().run_in_executor(
                None, yf.Ticker, symbol
            )
            
            # Get current info
            info = await asyncio.get_event_loop().run_in_executor(
                None, lambda: ticker.info
            )
            
            if not info:
                return None
            
            # Extract relevant quote data
            result = {
                'symbol': symbol,
                'price': info.get('currentPrice') or info.get('regularMarketPrice'),
                'volume': info.get('volume') or info.get('regularMarketVolume'),
                'previous_close': info.get('previousClose') or info.get('regularMarketPreviousClose'),
                'open': info.get('open') or info.get('regularMarketOpen'),
                'high': info.get('dayHigh') or info.get('regularMarketDayHigh'),
                'low': info.get('dayLow') or info.get('regularMarketDayLow'),
            }
            
            self._set_cached(cache_key, result)
            return result
            
        except Exception as e:
            logger.error("yfinance_quote_failed", symbol=symbol, error=str(e))
            self.record_error(e)
            return None
    
    async def close(self):
        """Close provider (cleanup cache)."""
        self._cache.clear()
        logger.info("yfinance_provider_closed")

