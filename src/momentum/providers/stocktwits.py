"""StockTwits sentiment provider."""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import aiohttp
import structlog

from src.momentum.base import DataProvider, ProviderHealth

logger = structlog.get_logger()


class StockTwitsProvider(DataProvider):
    """Provider for StockTwits API (social sentiment).
    
    Supports two access modes:
    1. Direct API (currently paused for new registrations)
    2. RapidAPI marketplace (recommended - free tier available)
    """
    
    BASE_URL = "https://api.stocktwits.com/api/2"
    RAPIDAPI_BASE_URL = "https://stocktwits.p.rapidapi.com/api/2"
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize StockTwits provider.
        
        Args:
            config: Provider configuration
        """
        super().__init__(config)
        
        # RapidAPI access (recommended)
        self.rapidapi_key = os.getenv('RAPIDAPI_KEY', config.get('rapidapi_key'))
        self.use_rapidapi = os.getenv('STOCKTWITS_USE_RAPIDAPI', 'true').lower() == 'true'
        
        # Direct API access (legacy/if available)
        self.access_token = os.getenv('STOCKTWITS_ACCESS_TOKEN', config.get('access_token'))
        
        # Select appropriate base URL
        self.base_url = self.RAPIDAPI_BASE_URL if self.use_rapidapi else self.BASE_URL
        
        self.session: Optional[aiohttp.ClientSession] = None
        self._last_request_time = None
        
    async def initialize(self) -> bool:
        """Initialize provider.
        
        Returns:
            True if initialization successful
        """
        # Check if we have credentials for either access method
        has_rapidapi = bool(self.rapidapi_key)
        has_direct = bool(self.access_token)
        
        if not has_rapidapi and not has_direct:
            logger.warning(
                "stocktwits_no_credentials",
                message="No RapidAPI key or access token found. Provider disabled."
            )
            return False
        
        self.session = aiohttp.ClientSession()
        
        try:
            await self.health_check()
            self._is_available = True
            logger.info(
                "stocktwits_initialized",
                use_rapidapi=self.use_rapidapi,
                has_rapidapi=has_rapidapi,
                has_direct=has_direct
            )
            return True
        except Exception as e:
            logger.error("stocktwits_initialization_failed", error=str(e))
            return False
    
    async def health_check(self) -> ProviderHealth:
        """Check StockTwits API health.
        
        Returns:
            ProviderHealth status
        """
        try:
            # Test with a simple streams request
            url = f"{self.base_url}/streams/symbol/AAPL.json"
            headers = self._get_headers()
            
            logger.debug("stocktwits_health_check", url=url, headers={k: "***" if "key" in k.lower() else v for k, v in headers.items()})
            
            async with self.session.get(url, headers=headers, timeout=10) as resp:
                # Log response for debugging
                response_text = await resp.text()
                logger.debug("stocktwits_health_response", status=resp.status, body=response_text[:200])
                if resp.status == 200:
                    return ProviderHealth(
                        provider_name=self.name,
                        is_available=True,
                        last_check=datetime.utcnow()
                    )
                elif resp.status == 429:
                    return ProviderHealth(
                        provider_name=self.name,
                        is_available=False,
                        last_check=datetime.utcnow(),
                        error_message="Rate limited",
                        rate_limited=True
                    )
                elif resp.status == 404:
                    error_msg = f"Endpoint not found (404). URL: {url}"
                    if self.use_rapidapi:
                        error_msg += "\n⚠️  RapidAPI StockTwits endpoint may have changed. Check RapidAPI dashboard."
                    logger.error("stocktwits_404_error", url=url, use_rapidapi=self.use_rapidapi)
                    return ProviderHealth(
                        provider_name=self.name,
                        is_available=False,
                        last_check=datetime.utcnow(),
                        error_message=error_msg
                    )
                else:
                    return ProviderHealth(
                        provider_name=self.name,
                        is_available=False,
                        last_check=datetime.utcnow(),
                        error_message=f"HTTP {resp.status}: {response_text[:100]}"
                    )
                    
        except Exception as e:
            return ProviderHealth(
                provider_name=self.name,
                is_available=False,
                last_check=datetime.utcnow(),
                error_message=str(e)
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers based on auth mode.
        
        Returns:
            Headers dict
        """
        headers = {}
        
        if self.use_rapidapi and self.rapidapi_key:
            # RapidAPI authentication
            headers['X-RapidAPI-Key'] = self.rapidapi_key
            headers['X-RapidAPI-Host'] = 'stocktwits.p.rapidapi.com'
        elif self.access_token:
            # Direct API authentication
            headers['Authorization'] = f"Bearer {self.access_token}"
        
        return headers
    
    async def get_stream(
        self,
        symbol: str,
        limit: int = 30
    ) -> Optional[Dict[str, Any]]:
        """Get message stream for a symbol.
        
        Args:
            symbol: Stock symbol
            limit: Number of messages to fetch (max 30)
            
        Returns:
            Dict with stream data or None
        """
        url = f"{self.base_url}/streams/symbol/{symbol}.json"
        params = {'limit': min(limit, 30)}
        headers = self._get_headers()
        
        try:
            async with self.session.get(url, params=params, headers=headers, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
                elif resp.status == 429:
                    logger.warning("stocktwits_rate_limited", symbol=symbol)
                    self.record_error(Exception("Rate limited"))
                    return None
                else:
                    logger.warning("stocktwits_http_error", status=resp.status, symbol=symbol)
                    return None
                    
        except Exception as e:
            logger.error("stocktwits_request_failed", symbol=symbol, error=str(e))
            self.record_error(e)
            return None
    
    async def calculate_sentiment_metrics(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Calculate sentiment metrics from messages.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict with sentiment metrics or None
        """
        data = await self.get_stream(symbol, limit=30)
        if not data or 'messages' not in data:
            return None
        
        try:
            messages = data['messages']
            if not messages:
                return None
            
            # Count sentiment
            bullish = 0
            bearish = 0
            total = 0
            
            # Calculate message velocity (messages per hour)
            now = datetime.utcnow()
            recent_messages = []
            
            for msg in messages:
                total += 1
                
                # Parse timestamp
                created_at = datetime.strptime(
                    msg['created_at'],
                    '%Y-%m-%dT%H:%M:%SZ'
                )
                time_diff = (now - created_at).total_seconds() / 3600  # hours
                recent_messages.append(time_diff)
                
                # Count sentiment
                if 'entities' in msg and 'sentiment' in msg['entities']:
                    sentiment = msg['entities']['sentiment']
                    if sentiment and 'basic' in sentiment:
                        if sentiment['basic'] == 'Bullish':
                            bullish += 1
                        elif sentiment['basic'] == 'Bearish':
                            bearish += 1
            
            # Calculate metrics
            bullish_ratio = bullish / total if total > 0 else 0.5
            bearish_ratio = bearish / total if total > 0 else 0.5
            sentiment_score = (bullish_ratio - bearish_ratio + 1) / 2  # Normalize to 0-1
            
            # Message velocity (messages in last hour)
            messages_last_hour = sum(1 for t in recent_messages if t <= 1.0)
            velocity = messages_last_hour
            
            # Calculate trend (recent vs older messages sentiment)
            if len(messages) >= 10:
                recent = messages[:10]
                recent_bullish = sum(
                    1 for m in recent
                    if m.get('entities', {}).get('sentiment', {}).get('basic') == 'Bullish'
                )
                recent_sentiment = recent_bullish / 10
                
                # Compare to overall
                sentiment_trend = recent_sentiment - bullish_ratio
            else:
                sentiment_trend = 0.0
            
            return {
                'total_messages': total,
                'bullish_count': bullish,
                'bearish_count': bearish,
                'bullish_ratio': bullish_ratio,
                'sentiment_score': sentiment_score,
                'velocity': velocity,
                'sentiment_trend': sentiment_trend
            }
            
        except Exception as e:
            logger.error("sentiment_metrics_calculation_failed", symbol=symbol, error=str(e))
            return None
    
    async def close(self):
        """Close provider session."""
        if self.session:
            await self.session.close()
            logger.info("stocktwits_session_closed")

