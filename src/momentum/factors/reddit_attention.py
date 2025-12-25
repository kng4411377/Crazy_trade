"""Reddit attention momentum factor using Apewisdom."""

from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog

from src.momentum.base import MomentumFactor, FactorScore, DataProvider, ProviderCapability
from src.momentum.providers.apewisdom import ApewisdomProvider

logger = structlog.get_logger()


class RedditAttentionFactor(MomentumFactor):
    """
    Detects Reddit retail attention using Apewisdom data.
    
    Tracks stock mentions across Reddit (WSB, stocks, investing) and
    calculates momentum based on:
    - Mention volume (how much discussion)
    - Mention velocity (rate of increase)
    - Sentiment/positivity (bullish vs bearish)
    - Rank momentum (climbing the trending list)
    
    Signals:
    - High mention volume
    - Rapid increase in mentions (WSB piling in)
    - Positive sentiment
    - Climbing rank (gaining attention)
    - Meme stock breakout potential
    
    Use Cases:
    - WSB momentum plays
    - Meme stock detection
    - Retail FOMO tracking
    - Pre-market planning (9 AM update)
    - After-hours analysis (9 PM update)
    """
    
    def __init__(self, providers: List[DataProvider], config: Dict):
        super().__init__(providers, config)
        self.mention_threshold = config.get('mention_threshold', 50)  # Min mentions to score
        self.velocity_weight = config.get('velocity_weight', 0.4)
        self.volume_weight = config.get('volume_weight', 0.3)
        self.sentiment_weight = config.get('sentiment_weight', 0.3)
    
    async def calculate_score(self, symbol: str) -> Optional[FactorScore]:
        """
        Calculate Reddit attention score for a symbol.
        
        Returns:
            FactorScore with:
            - score: 0.0 to 1.0 (higher = more Reddit attention)
            - confidence: Based on mention volume
            - metadata: Reddit metrics
        """
        # Find Apewisdom provider
        apewisdom_provider = None
        for provider in self.providers:
            if isinstance(provider, ApewisdomProvider) and provider.is_available():
                apewisdom_provider = provider
                break
        
        if not apewisdom_provider:
            logger.debug(f"No Apewisdom provider available for {symbol}")
            return None
        
        try:
            # Get Reddit sentiment data
            data = await apewisdom_provider.get_stock_sentiment(symbol)
            
            if not data:
                logger.debug(f"No Apewisdom data for {symbol}")
                return None
            
            mentions = data['mentions']
            mentions_change = data['mentions_change']
            positivity = data['positivity']
            rank = data['rank']
            rank_change = data['rank_change']
            
            # Skip if below threshold
            if mentions < self.mention_threshold:
                logger.debug(f"{symbol} has only {mentions} mentions (threshold: {self.mention_threshold})")
                return None
            
            # 1. Volume score (normalized by typical WSB activity)
            # 100 mentions = low, 500 = medium, 1000+ = high
            volume_score = min(1.0, mentions / 1000.0)
            
            # 2. Velocity score (mentions change %)
            # -50% = 0.0, 0% = 0.5, +100% = 0.75, +200%+ = 1.0
            if mentions_change >= 200:
                velocity_score = 1.0
            elif mentions_change >= 100:
                velocity_score = 0.75
            elif mentions_change >= 50:
                velocity_score = 0.65
            elif mentions_change >= 0:
                velocity_score = 0.5 + (mentions_change / 200)  # 0% → 0.5, +100% → 0.75
            else:
                velocity_score = max(0.0, 0.5 + (mentions_change / 100))  # -50% → 0.0
            
            # 3. Sentiment score (positivity is 0-1 already)
            sentiment_score = positivity
            
            # Composite score (weighted average)
            score = (
                self.volume_weight * volume_score +
                self.velocity_weight * velocity_score +
                self.sentiment_weight * sentiment_score
            )
            
            # Ensure 0-1 range
            score = max(0.0, min(1.0, score))
            
            # Confidence based on mention volume
            # More mentions = more reliable signal
            if mentions >= 500:
                confidence = 0.9
            elif mentions >= 200:
                confidence = 0.8
            elif mentions >= 100:
                confidence = 0.7
            else:
                confidence = 0.6
            
            # Boost confidence if trending up
            if rank_change > 5:  # Climbing >5 spots
                confidence = min(1.0, confidence + 0.1)
            
            # Signal detection
            is_breakout = mentions_change > 100 and mentions > 200
            is_trending_up = rank_change > 0
            is_bullish = positivity > 0.6
            
            metadata = {
                'mentions': mentions,
                'mentions_change': mentions_change,
                'rank': rank,
                'rank_change': rank_change,
                'positivity': positivity,
                'volume_score': volume_score,
                'velocity_score': velocity_score,
                'sentiment_score': sentiment_score,
                'is_breakout': is_breakout,
                'is_trending_up': is_trending_up,
                'is_bullish': is_bullish
            }
            
            logger.info(
                "reddit_attention_calculated",
                symbol=symbol,
                mentions=mentions,
                change=round(mentions_change, 1),
                rank=rank,
                positivity=round(positivity, 2),
                score=round(score, 3),
                confidence=round(confidence, 3),
                breakout=is_breakout
            )
            
            return FactorScore(
                factor_name=self.name,
                symbol=symbol,
                score=score,
                confidence=confidence,
                timestamp=datetime.utcnow(),
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error calculating RedditAttentionFactor for {symbol}: {e}", exc_info=True)
            return None

