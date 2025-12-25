"""Alpha Vantage data provider."""

import os
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import aiohttp
import structlog

from src.momentum.base import DataProvider, ProviderHealth

logger = structlog.get_logger()


class AlphaVantageProvider(DataProvider):
    """Provider for Alpha Vantage API (price, volume, technicals)."""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Alpha Vantage provider.
        
        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self.api_key = os.getenv('ALPHAVANTAGE_API_KEY', config.get('api_key'))
        self.session: Optional[aiohttp.ClientSession] = None
        self._rate_limit_remaining = 5  # Free tier: 5 per minute
        self._last_request_time = None
        self._min_request_interval = 1.0  # Minimum 1 second between requests
        
    async def initialize(self) -> bool:
        """Initialize provider and validate API key.
        
        Returns:
            True if initialization successful
        """
        if not self.api_key:
            logger.warning("alphavantage_api_key_missing")
            return False
        
        self.session = aiohttp.ClientSession()
        
        # Skip health check during init to save API calls
        # Free tier has very limited quota (25 requests/day)
        self._is_available = True
        logger.info("alphavantage_initialized", note="Health check skipped to preserve API quota")
        return True
    
    async def _rate_limit_wait(self):
        """Wait to respect rate limits (1 request per second for free tier)."""
        if self._last_request_time:
            elapsed = (datetime.utcnow() - self._last_request_time).total_seconds()
            if elapsed < self._min_request_interval:
                wait_time = self._min_request_interval - elapsed
                logger.debug("alphavantage_rate_limit_wait", wait_seconds=wait_time)
                await asyncio.sleep(wait_time)
        
        self._last_request_time = datetime.utcnow()
    
    # Alias for backwards compatibility
    async def _rate_limit_check(self):
        """Alias for _rate_limit_wait()."""
        await self._rate_limit_wait()
    
    async def health_check(self) -> ProviderHealth:
        """Check Alpha Vantage API health.
        
        Returns:
            ProviderHealth status
        """
        try:
            # Wait to respect rate limits
            await self._rate_limit_wait()
            
            # Simple quote request to test API
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': 'AAPL',
                'apikey': self.api_key
            }
            
            async with self.session.get(self.BASE_URL, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # Log the response for debugging
                    logger.debug("alphavantage_health_response", data=data)
                    
                    # Check for rate limit or error messages
                    if 'Note' in data or 'Information' in data:
                        error_msg = data.get('Note') or data.get('Information')
                        logger.warning("alphavantage_rate_limit", message=error_msg)
                        
                        # Mark as available but rate limited
                        # The provider will still work, just slowly
                        return ProviderHealth(
                            provider_name=self.name,
                            is_available=True,  # Changed to True - provider works, just rate limited
                            last_check=datetime.utcnow(),
                            error_message=f"Rate limited (will retry with delays): {error_msg[:100]}",
                            rate_limited=True
                        )
                    
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
                        error_message=f"HTTP {resp.status}"
                    )
                    
        except Exception as e:
            return ProviderHealth(
                provider_name=self.name,
                is_available=False,
                last_check=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def get_intraday_data(
        self,
        symbol: str,
        interval: str = '5min'
    ) -> Optional[Dict[str, Any]]:
        """Get intraday price data.
        
        Args:
            symbol: Stock symbol
            interval: Time interval (1min, 5min, 15min, 30min, 60min)
            
        Returns:
            Dict with intraday data or None
        """
        await self._rate_limit_check()
        
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': interval,
            'apikey': self.api_key,
            'outputsize': 'compact'  # last 100 data points
        }
        
        try:
            async with self.session.get(self.BASE_URL, params=params, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # Check for errors
                    if 'Error Message' in data:
                        logger.warning("alphavantage_error", symbol=symbol, error=data['Error Message'])
                        return None
                    
                    if 'Note' in data:
                        logger.warning("alphavantage_rate_limited", symbol=symbol)
                        self.record_error(Exception("Rate limited"))
                        return None
                    
                    time_series_key = f'Time Series ({interval})'
                    if time_series_key in data:
                        return data
                    
                    logger.warning("alphavantage_unexpected_response", symbol=symbol)
                    return None
                else:
                    logger.error("alphavantage_http_error", status=resp.status, symbol=symbol)
                    return None
                    
        except Exception as e:
            logger.error("alphavantage_request_failed", symbol=symbol, error=str(e))
            self.record_error(e)
            return None
    
    async def get_daily_data(
        self,
        symbol: str,
        outputsize: str = 'compact'
    ) -> Optional[Dict[str, Any]]:
        """Get daily price data.
        
        Args:
            symbol: Stock symbol
            outputsize: 'compact' (100 days) or 'full' (20+ years)
            
        Returns:
            Dict with daily data or None
        """
        await self._rate_limit_check()
        
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'apikey': self.api_key,
            'outputsize': outputsize
        }
        
        try:
            async with self.session.get(self.BASE_URL, params=params, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    if 'Error Message' in data or 'Note' in data:
                        return None
                    
                    if 'Time Series (Daily)' in data:
                        return data
                    
                    return None
                else:
                    return None
                    
        except Exception as e:
            logger.error("alphavantage_daily_request_failed", symbol=symbol, error=str(e))
            self.record_error(e)
            return None
    
    async def calculate_volume_metrics(self, symbol: str) -> Optional[Dict[str, float]]:
        """Calculate volume-based metrics.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict with volume metrics or None
        """
        data = await self.get_daily_data(symbol, outputsize='compact')
        if not data:
            return None
        
        try:
            time_series = data.get('Time Series (Daily)', {})
            if not time_series:
                return None
            
            # Get last 20 days of data
            dates = sorted(time_series.keys(), reverse=True)[:20]
            volumes = [float(time_series[date]['5. volume']) for date in dates]
            
            if len(volumes) < 5:
                return None
            
            # Calculate metrics
            current_volume = volumes[0]
            avg_volume_20 = sum(volumes) / len(volumes)
            rvol = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1.0
            
            # Volume trend (last 5 days vs previous 15 days)
            recent_avg = sum(volumes[:5]) / 5
            older_avg = sum(volumes[5:]) / 15 if len(volumes) > 5 else recent_avg
            volume_trend = (recent_avg / older_avg - 1.0) if older_avg > 0 else 0.0
            
            return {
                'current_volume': current_volume,
                'avg_volume_20': avg_volume_20,
                'rvol': rvol,
                'volume_trend': volume_trend
            }
            
        except Exception as e:
            logger.error("volume_metrics_calculation_failed", symbol=symbol, error=str(e))
            return None
    
    async def close(self):
        """Close provider session."""
        if self.session:
            await self.session.close()
            logger.info("alphavantage_session_closed")


# Need to import asyncio
import asyncio

