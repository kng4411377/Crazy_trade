"""Sentiment velocity momentum factor."""

from typing import Optional, List
from datetime import datetime
import structlog

from src.momentum.base import MomentumFactor, FactorScore, DataProvider
from src.momentum.providers.stocktwits import StockTwitsProvider

logger = structlog.get_logger()


class SentimentVelocityFactor(MomentumFactor):
    """Measures social sentiment velocity and direction."""
    
    def __init__(self, providers: List[DataProvider], config: dict):
        """Initialize sentiment velocity factor.
        
        Args:
            providers: List of data providers (should include StockTwitsProvider)
            config: Factor configuration
        """
        super().__init__(providers, config)
        self.velocity_threshold = config.get('velocity_threshold', 10)  # messages/hour
        self.sentiment_threshold = config.get('sentiment_threshold', 0.6)  # bullish ratio
        
    async def calculate_score(self, symbol: str) -> Optional[FactorScore]:
        """Calculate sentiment velocity score.
        
        Scoring logic:
        - High velocity + bullish sentiment: Strong signal (0.7-1.0)
        - High velocity + neutral sentiment: Moderate signal (0.4-0.7)
        - Low velocity: Weak signal (0.0-0.4)
        - Sentiment trend increasing: Boosts score
        
        Args:
            symbol: Stock or crypto symbol
            
        Returns:
            FactorScore or None
        """
        # Find StockTwits provider
        st_provider = None
        for provider in self.get_available_providers():
            if isinstance(provider, StockTwitsProvider):
                st_provider = provider
                break
        
        if not st_provider:
            logger.warning("no_stocktwits_provider_available", factor=self.name, symbol=symbol)
            return None
        
        # Get sentiment metrics
        metrics = await st_provider.calculate_sentiment_metrics(symbol)
        if not metrics:
            return None
        
        velocity = metrics['velocity']
        sentiment_score = metrics['sentiment_score']
        sentiment_trend = metrics['sentiment_trend']
        bullish_ratio = metrics['bullish_ratio']
        
        # Calculate base score from velocity and sentiment
        if velocity >= self.velocity_threshold:
            velocity_score = min(1.0, velocity / (self.velocity_threshold * 2))
        else:
            velocity_score = velocity / self.velocity_threshold
        
        # Sentiment multiplier
        if sentiment_score >= self.sentiment_threshold:
            # Bullish sentiment boosts score
            sentiment_multiplier = 0.8 + (sentiment_score - 0.5)  # 0.8 to 1.3
        elif sentiment_score <= (1 - self.sentiment_threshold):
            # Bearish sentiment reduces score
            sentiment_multiplier = 0.3 + sentiment_score  # 0.3 to 0.8
        else:
            # Neutral sentiment
            sentiment_multiplier = 0.6 + (sentiment_score - 0.5) * 0.4
        
        base_score = velocity_score * sentiment_multiplier
        
        # Adjust for sentiment trend
        if sentiment_trend > 0.1:
            # Positive trend (getting more bullish)
            trend_boost = min(0.15, sentiment_trend)
            score = min(1.0, base_score + trend_boost)
        elif sentiment_trend < -0.1:
            # Negative trend (getting more bearish)
            trend_penalty = min(0.15, abs(sentiment_trend))
            score = max(0.0, base_score - trend_penalty)
        else:
            score = base_score
        
        # Confidence based on message volume and sentiment clarity
        message_confidence = min(1.0, metrics['total_messages'] / 20)
        sentiment_clarity = abs(sentiment_score - 0.5) * 2  # 0=neutral, 1=extreme
        confidence = (message_confidence * 0.6) + (sentiment_clarity * 0.4)
        
        logger.info(
            "sentiment_velocity_calculated",
            symbol=symbol,
            velocity=velocity,
            sentiment_score=round(sentiment_score, 3),
            bullish_ratio=round(bullish_ratio, 3),
            score=round(score, 3),
            confidence=round(confidence, 3)
        )
        
        return FactorScore(
            factor_name=self.name,
            symbol=symbol,
            score=score,
            confidence=confidence,
            timestamp=datetime.utcnow(),
            metadata={
                'velocity': velocity,
                'sentiment_score': sentiment_score,
                'sentiment_trend': sentiment_trend,
                'bullish_ratio': bullish_ratio,
                'bearish_ratio': metrics['bearish_ratio'],
                'total_messages': metrics['total_messages']
            }
        )

