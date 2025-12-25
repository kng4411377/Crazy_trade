"""Volume anomaly momentum factor."""

from typing import Optional, List
from datetime import datetime
import structlog

from src.momentum.base import MomentumFactor, FactorScore, DataProvider
from src.momentum.providers.alphavantage import AlphaVantageProvider
from src.momentum.providers.yfinance_provider import YFinanceProvider

logger = structlog.get_logger()


class VolumeAnomalyFactor(MomentumFactor):
    """Detects volume anomalies that indicate momentum."""
    
    def __init__(self, providers: List[DataProvider], config: dict):
        """Initialize volume anomaly factor.
        
        Args:
            providers: List of data providers (should include AlphaVantageProvider)
            config: Factor configuration
        """
        super().__init__(providers, config)
        self.rvol_threshold = config.get('rvol_threshold', 1.5)  # 50% above average
        self.volume_trend_threshold = config.get('volume_trend_threshold', 0.2)  # 20% increase
        
    async def calculate_score(self, symbol: str) -> Optional[FactorScore]:
        """Calculate volume anomaly score.
        
        Scoring logic:
        - RVOL > 1.5: Strong signal (0.7-1.0)
        - RVOL 1.2-1.5: Moderate signal (0.4-0.7)
        - RVOL < 1.2: Weak signal (0.0-0.4)
        - Volume trend increasing: Boosts score
        
        Args:
            symbol: Stock or crypto symbol
            
        Returns:
            FactorScore or None
        """
        # Find data provider (prefer YFinance, fallback to Alpha Vantage)
        data_provider = None
        for provider in self.get_available_providers():
            if isinstance(provider, YFinanceProvider):
                data_provider = provider
                break
            elif isinstance(provider, AlphaVantageProvider):
                data_provider = provider
        
        if not data_provider:
            logger.warning("no_data_provider_available", factor=self.name, symbol=symbol)
            return None
        
        # Get volume metrics
        metrics = await data_provider.calculate_volume_metrics(symbol)
        if not metrics:
            return None
        
        rvol = metrics['rvol']
        volume_trend = metrics['volume_trend']
        
        # Calculate base score from RVOL
        if rvol >= 2.0:
            base_score = 1.0
        elif rvol >= self.rvol_threshold:
            # Linear interpolation between threshold and 2.0
            base_score = 0.7 + (0.3 * ((rvol - self.rvol_threshold) / (2.0 - self.rvol_threshold)))
        elif rvol >= 1.2:
            # Linear interpolation between 1.2 and threshold
            base_score = 0.4 + (0.3 * ((rvol - 1.2) / (self.rvol_threshold - 1.2)))
        else:
            # Low volume
            base_score = max(0.0, 0.4 * (rvol / 1.2))
        
        # Adjust for volume trend
        if volume_trend > self.volume_trend_threshold:
            # Positive trend boosts score
            trend_boost = min(0.15, volume_trend * 0.5)
            score = min(1.0, base_score + trend_boost)
        elif volume_trend < -self.volume_trend_threshold:
            # Negative trend reduces score
            trend_penalty = min(0.15, abs(volume_trend) * 0.5)
            score = max(0.0, base_score - trend_penalty)
        else:
            score = base_score
        
        # Confidence based on data quality
        # Higher RVOL = higher confidence
        confidence = min(1.0, 0.5 + (rvol / 4.0))
        
        logger.info(
            "volume_anomaly_calculated",
            symbol=symbol,
            rvol=round(rvol, 2),
            volume_trend=round(volume_trend, 3),
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
                'rvol': rvol,
                'volume_trend': volume_trend,
                'current_volume': metrics['current_volume'],
                'avg_volume_20': metrics['avg_volume_20']
            }
        )

