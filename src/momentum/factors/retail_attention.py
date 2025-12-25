"""Retail Attention Factor - measures retail investor interest via Google Trends."""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from ..base import MomentumFactor, DataProvider, FactorScore

logger = logging.getLogger(__name__)


class RetailAttentionFactor(MomentumFactor):
    """
    Retail Attention Factor based on Google search trends.
    
    Measures retail investor interest and FOMO (Fear Of Missing Out) using
    Google search data. High search velocity often precedes price momentum.
    
    Scoring Logic:
    - Interest Level (0-100): How much people are searching
    - Velocity: Rate of increase in searches
    - Breakout: Sudden spike in interest (>2x average)
    
    High scores indicate:
    - Viral attention
    - Retail FOMO building
    - Potential momentum ignition
    
    Use Cases:
    - Meme stock detection
    - Retail-driven momentum
    - Breakout confirmation
    """
    
    def __init__(self, providers: List[DataProvider], config: Dict):
        super().__init__(providers, config)
        self.timeframe = config.get('timeframe', 'now 7-d')
        self.breakout_weight = config.get('breakout_weight', 0.4)
        self.velocity_weight = config.get('velocity_weight', 0.4)
        self.interest_weight = config.get('interest_weight', 0.2)
    
    async def calculate_score(self, symbol: str) -> Optional[FactorScore]:
        """
        Calculate retail attention score for a symbol.
        
        Returns:
            FactorScore with:
            - score: 0.0 to 1.0 (higher = more retail attention)
            - confidence: Based on data quality
            - metadata: Interest metrics
        """
        # Find Google Trends provider
        trends_provider = None
        for provider in self.providers:
            if provider.name == "GoogleTrendsProvider" and provider.is_available():
                trends_provider = provider
                break
        
        if not trends_provider:
            logger.debug(f"No Google Trends provider available for {symbol}")
            return None
        
        try:
            # Get search interest data
            data = await trends_provider.get_search_interest(symbol, self.timeframe)
            
            if not data:
                logger.debug(f"No Google Trends data for {symbol}")
                return None
            
            # Extract metrics
            current_interest = data.get('current_interest', 0)
            average_interest = data.get('average_interest', 0)
            velocity = data.get('velocity', 0)
            is_breakout = data.get('is_breakout', False)
            
            # Calculate component scores (0-1 scale)
            
            # 1. Interest level score (0-100 → 0-1)
            interest_score = min(current_interest / 100.0, 1.0)
            
            # 2. Velocity score (normalized)
            # Velocity can be -100 to +100, normalize to 0-1
            # Positive velocity is good, negative is bad
            velocity_normalized = (velocity + 100) / 200.0
            velocity_score = max(0, min(velocity_normalized, 1.0))
            
            # 3. Breakout score
            breakout_score = 1.0 if is_breakout else 0.0
            
            # Composite score (weighted average)
            score = (
                self.interest_weight * interest_score +
                self.velocity_weight * velocity_score +
                self.breakout_weight * breakout_score
            )
            
            # Confidence: higher when interest is significant
            # Low interest = low confidence (noisy data)
            if current_interest > 50:
                confidence = 0.9
            elif current_interest > 20:
                confidence = 0.7
            elif current_interest > 5:
                confidence = 0.5
            else:
                confidence = 0.3
            
            metadata = {
                'current_interest': current_interest,
                'average_interest': average_interest,
                'velocity': velocity,
                'is_breakout': is_breakout,
                'interest_score': interest_score,
                'velocity_score': velocity_score,
                'breakout_score': breakout_score,
            }
            
            logger.info(
                f"RetailAttention {symbol}: "
                f"score={score:.3f}, "
                f"interest={current_interest:.1f}, "
                f"velocity={velocity:.1f}, "
                f"breakout={is_breakout}"
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
            logger.error(f"Error calculating RetailAttentionFactor for {symbol}: {e}")
            return None

