"""
Momentum-based watchlist filter for the trading bot.

Filters the bot's watchlist based on momentum scores, only allowing
symbols with sufficient momentum to be traded.
"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import structlog

from src.momentum.providers.yfinance_provider import YFinanceProvider
from src.momentum.providers.apewisdom import ApewisdomProvider
from src.momentum.factors.volume_anomaly import VolumeAnomalyFactor
from src.momentum.factors.reddit_attention import RedditAttentionFactor

logger = structlog.get_logger()


class MomentumFilter:
    """
    Filters symbols based on momentum scores.
    
    Usage:
        filter = MomentumFilter(config)
        await filter.initialize()
        
        # Filter watchlist
        symbols = ["AAPL", "TSLA", "GME"]
        filtered = await filter.filter_symbols(symbols)
        # Returns only symbols above momentum threshold
    """
    
    def __init__(self, config: Dict):
        """
        Initialize momentum filter.
        
        Args:
            config: momentum_config.yaml['momentum_layer']['filter'] section
        """
        self.config = config
        self.enabled = config.get('enabled', False)
        self.min_score = config.get('min_score', 0.5)
        self.volume_weight = config.get('volume_weight', 0.7)
        self.reddit_weight = config.get('reddit_weight', 0.3)
        self.cache_duration = config.get('cache_duration', 3600)  # 1 hour
        self.require_volume = config.get('require_volume', True)
        self.require_reddit = config.get('require_reddit', False)
        
        # Providers
        self.yf_provider: Optional[YFinanceProvider] = None
        self.apewisdom_provider: Optional[ApewisdomProvider] = None
        
        # Factors
        self.volume_factor: Optional[VolumeAnomalyFactor] = None
        self.reddit_factor: Optional[RedditAttentionFactor] = None
        
        # Cache
        self._score_cache: Dict[str, Dict] = {}
        self._last_filter_time: Optional[datetime] = None
        
        logger.info(
            "momentum_filter_config",
            enabled=self.enabled,
            min_score=self.min_score,
            volume_weight=self.volume_weight,
            reddit_weight=self.reddit_weight,
            require_volume=self.require_volume,
            require_reddit=self.require_reddit
        )
    
    async def initialize(self) -> bool:
        """
        Initialize providers and factors.
        
        Returns:
            True if initialization successful
        """
        if not self.enabled:
            logger.info("momentum_filter_disabled")
            return True
        
        try:
            logger.info("momentum_filter_initializing")
            
            # Initialize YFinance (always needed)
            self.yf_provider = YFinanceProvider({})
            await self.yf_provider.initialize()
            
            if not self.yf_provider.is_available():
                logger.error("momentum_filter_init_failed", reason="yfinance_unavailable")
                return False
            
            # Initialize Apewisdom (optional)
            self.apewisdom_provider = ApewisdomProvider({})
            await self.apewisdom_provider.initialize()
            
            # Create factors
            self.volume_factor = VolumeAnomalyFactor(
                [self.yf_provider],
                {'weight': self.volume_weight}
            )
            
            self.reddit_factor = RedditAttentionFactor(
                [self.apewisdom_provider],
                {
                    'weight': self.reddit_weight,
                    'min_mentions': 10,
                    'min_positivity': 0.55
                }
            )
            
            logger.info(
                "momentum_filter_initialized",
                yfinance=self.yf_provider.is_available(),
                apewisdom=self.apewisdom_provider.is_available()
            )
            
            return True
            
        except Exception as e:
            logger.error("momentum_filter_init_error", error=str(e), exc_info=True)
            return False
    
    async def filter_symbols(self, symbols: List[str]) -> List[str]:
        """
        Filter symbols by momentum score.
        
        Args:
            symbols: List of symbols to filter
        
        Returns:
            List of symbols that pass momentum filter
        """
        if not self.enabled:
            logger.debug("momentum_filter_bypassed", count=len(symbols))
            return symbols
        
        if not symbols:
            return []
        
        logger.info("momentum_filter_start", symbol_count=len(symbols))
        
        filtered_symbols = []
        filtered_out = []
        
        for symbol in symbols:
            try:
                score_data = await self._get_symbol_score(symbol)
                
                if score_data and score_data['passes_filter']:
                    filtered_symbols.append(symbol)
                    logger.info(
                        "momentum_filter_pass",
                        symbol=symbol,
                        score=score_data['composite'],
                        volume=score_data['volume_score'],
                        reddit=score_data['reddit_score']
                    )
                else:
                    filtered_out.append(symbol)
                    reason = score_data.get('filter_reason', 'below_threshold') if score_data else 'no_score'
                    logger.warning(
                        "momentum_filter_reject",
                        symbol=symbol,
                        reason=reason,
                        score=score_data.get('composite', 0) if score_data else 0
                    )
                    
            except Exception as e:
                logger.error(
                    "momentum_filter_error",
                    symbol=symbol,
                    error=str(e)
                )
                # On error, include symbol (fail-open behavior)
                if self.config.get('fail_open', True):
                    filtered_symbols.append(symbol)
                    logger.warning("momentum_filter_error_included", symbol=symbol)
        
        logger.info(
            "momentum_filter_complete",
            input_count=len(symbols),
            passed=len(filtered_symbols),
            rejected=len(filtered_out),
            filtered_out=filtered_out
        )
        
        self._last_filter_time = datetime.now()
        
        return filtered_symbols
    
    async def _get_symbol_score(self, symbol: str) -> Optional[Dict]:
        """
        Get momentum score for a symbol (with caching).
        
        Returns:
            Dict with score data and filter decision
        """
        # Check cache
        if symbol in self._score_cache:
            cached = self._score_cache[symbol]
            age = (datetime.now() - cached['timestamp']).total_seconds()
            if age < self.cache_duration:
                logger.debug("momentum_filter_cache_hit", symbol=symbol, age=age)
                return cached
        
        # Calculate fresh scores
        volume_score = None
        reddit_score = None
        
        # Get volume score (required if require_volume=True)
        if self.volume_factor:
            volume_score = await self.volume_factor.calculate_score(symbol)
        
        # Get reddit score (required if require_reddit=True)
        if self.reddit_factor and self.apewisdom_provider.is_available():
            reddit_score = await self.reddit_factor.calculate_score(symbol)
        
        # Check requirements
        if self.require_volume and not volume_score:
            result = {
                'composite': 0.0,
                'volume_score': 0.0,
                'reddit_score': 0.0,
                'passes_filter': False,
                'filter_reason': 'no_volume_data',
                'timestamp': datetime.now()
            }
            self._score_cache[symbol] = result
            return result
        
        if self.require_reddit and not reddit_score:
            result = {
                'composite': 0.0,
                'volume_score': volume_score.score if volume_score else 0.0,
                'reddit_score': 0.0,
                'passes_filter': False,
                'filter_reason': 'no_reddit_data',
                'timestamp': datetime.now()
            }
            self._score_cache[symbol] = result
            return result
        
        # Calculate composite score
        v_score = volume_score.score if volume_score else 0.0
        r_score = reddit_score.score if reddit_score else 0.0
        
        # Use MAX aggregation (like the scanner)
        composite = max(v_score, r_score) if (volume_score or reddit_score) else 0.0
        
        # Check threshold
        passes = composite >= self.min_score
        
        result = {
            'composite': composite,
            'volume_score': v_score,
            'reddit_score': r_score,
            'passes_filter': passes,
            'filter_reason': 'below_threshold' if not passes else 'passed',
            'timestamp': datetime.now(),
            'volume_data': volume_score.metadata if volume_score else None,
            'reddit_data': reddit_score.metadata if reddit_score else None
        }
        
        # Cache result
        self._score_cache[symbol] = result
        
        return result
    
    async def get_filter_stats(self) -> Dict:
        """Get statistics about filter performance."""
        return {
            'enabled': self.enabled,
            'last_filter_time': self._last_filter_time,
            'cache_size': len(self._score_cache),
            'yfinance_available': self.yf_provider.is_available() if self.yf_provider else False,
            'apewisdom_available': self.apewisdom_provider.is_available() if self.apewisdom_provider else False,
            'config': {
                'min_score': self.min_score,
                'volume_weight': self.volume_weight,
                'reddit_weight': self.reddit_weight,
                'require_volume': self.require_volume,
                'require_reddit': self.require_reddit
            }
        }
    
    async def close(self):
        """Clean up resources."""
        if self.yf_provider:
            await self.yf_provider.close()
        if self.apewisdom_provider:
            await self.apewisdom_provider.close()
        
        logger.info("momentum_filter_closed")

