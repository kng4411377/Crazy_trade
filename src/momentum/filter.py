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
from src.momentum.factors.news_sentiment import NewsSentimentFactor

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
            config: Full momentum section (filter + factors) or legacy filter-only section
        """
        filter_cfg = config.get('filter', config)
        factors_cfg = config.get('factors', {})
        self.config = filter_cfg
        self.enabled = filter_cfg.get('enabled', False)
        self.min_score = filter_cfg.get('min_score', 0.5)
        self.volume_weight = filter_cfg.get('volume_weight', 0.7)
        self.reddit_weight = filter_cfg.get('reddit_weight', 0.3)
        self.news_weight = filter_cfg.get('news_weight', 0.3)
        self.cache_duration = filter_cfg.get('cache_duration', 3600)  # 1 hour
        self.require_volume = filter_cfg.get('require_volume', True)
        self.require_reddit = filter_cfg.get('require_reddit', False)
        self.require_news = filter_cfg.get('require_news', False)
        self.use_news_sentiment = factors_cfg.get('news_sentiment', {}).get('enabled', False)
        self.use_reddit_attention = factors_cfg.get('reddit_attention', {}).get('enabled', False)
        if not self.use_news_sentiment and not self.use_reddit_attention:
            self.use_news_sentiment = True  # default to news when both absent (replaced reddit)
        self._factors_cfg = factors_cfg
        
        # Providers
        self.yf_provider: Optional[YFinanceProvider] = None
        self.apewisdom_provider: Optional[ApewisdomProvider] = None
        
        # Factors
        self.volume_factor: Optional[VolumeAnomalyFactor] = None
        self.reddit_factor: Optional[RedditAttentionFactor] = None
        self.news_factor: Optional[NewsSentimentFactor] = None
        
        # Cache
        self._score_cache: Dict[str, Dict] = {}
        self._last_filter_time: Optional[datetime] = None
        
        logger.info(
            "momentum_filter_config",
            enabled=self.enabled,
            min_score=self.min_score,
            volume_weight=self.volume_weight,
            reddit_weight=self.reddit_weight,
            news_weight=self.news_weight,
            use_news_sentiment=self.use_news_sentiment,
            use_reddit_attention=self.use_reddit_attention,
            require_volume=self.require_volume,
            require_reddit=self.require_reddit,
            require_news=self.require_news
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
            
            if self.use_reddit_attention:
                self.apewisdom_provider = ApewisdomProvider({})
                await self.apewisdom_provider.initialize()
            
            # Create factors
            self.volume_factor = VolumeAnomalyFactor(
                [self.yf_provider],
                {'weight': self.volume_weight}
            )
            
            if self.use_news_sentiment:
                news_cfg = dict(self._factors_cfg.get('news_sentiment', {'weight': self.news_weight, 'top_headlines': 3}))
                news_cfg.setdefault('weight', self.news_weight)
                news_cfg.setdefault('enabled', True)
                self.news_factor = NewsSentimentFactor([], news_cfg)
            if self.use_reddit_attention and self.apewisdom_provider:
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
                apewisdom=self.apewisdom_provider.is_available() if self.apewisdom_provider else False,
                news_sentiment=self.use_news_sentiment
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
        news_score = None
        
        # Get volume score (required if require_volume=True)
        if self.volume_factor:
            volume_score = await self.volume_factor.calculate_score(symbol)
        
        # Get reddit score (required if require_reddit=True)
        if self.reddit_factor and self.apewisdom_provider and self.apewisdom_provider.is_available():
            reddit_score = await self.reddit_factor.calculate_score(symbol)
        
        # Get news score (when news_sentiment factor enabled)
        if self.news_factor:
            news_score = await self.news_factor.calculate_score(symbol)
        
        # Check requirements
        if self.require_volume and not volume_score:
            result = {
                'composite': 0.0,
                'volume_score': 0.0,
                'reddit_score': 0.0,
                'news_score': 0.0,
                'passes_filter': False,
                'filter_reason': 'no_volume_data',
                'timestamp': datetime.now()
            }
            self._score_cache[symbol] = result
            return result
        
        if self.require_reddit and not reddit_score and self.use_reddit_attention:
            result = {
                'composite': 0.0,
                'volume_score': volume_score.score if volume_score else 0.0,
                'reddit_score': 0.0,
                'news_score': 0.0,
                'passes_filter': False,
                'filter_reason': 'no_reddit_data',
                'timestamp': datetime.now()
            }
            self._score_cache[symbol] = result
            return result
        
        if self.require_news and not news_score and self.use_news_sentiment:
            result = {
                'composite': 0.0,
                'volume_score': volume_score.score if volume_score else 0.0,
                'reddit_score': 0.0,
                'news_score': 0.0,
                'passes_filter': False,
                'filter_reason': 'no_news_data',
                'timestamp': datetime.now()
            }
            self._score_cache[symbol] = result
            return result
        
        # Calculate composite score (volume, reddit, or news)
        v_score = volume_score.score if volume_score else 0.0
        r_score = reddit_score.score if reddit_score else 0.0
        n_score = news_score.score if news_score else 0.0
        composite = max(v_score, r_score, n_score) if (volume_score or reddit_score or news_score) else 0.0
        
        # Check threshold
        passes = composite >= self.min_score
        
        result = {
            'composite': composite,
            'volume_score': v_score,
            'reddit_score': r_score,
            'news_score': n_score,
            'passes_filter': passes,
            'filter_reason': 'below_threshold' if not passes else 'passed',
            'timestamp': datetime.now(),
            'volume_data': volume_score.metadata if volume_score else None,
            'reddit_data': reddit_score.metadata if reddit_score else None,
            'news_data': news_score.metadata if news_score else None
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
            'news_sentiment': self.use_news_sentiment,
            'config': {
                'min_score': self.min_score,
                'volume_weight': self.volume_weight,
                'reddit_weight': self.reddit_weight,
                'news_weight': self.news_weight,
                'require_volume': self.require_volume,
                'require_reddit': self.require_reddit,
                'require_news': self.require_news
            }
        }
    
    async def close(self):
        """Clean up resources."""
        if self.yf_provider:
            await self.yf_provider.close()
        if self.apewisdom_provider:
            await self.apewisdom_provider.close()
        self.news_factor = None
        logger.info("momentum_filter_closed")

