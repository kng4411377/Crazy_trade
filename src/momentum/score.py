"""Proactive momentum scoring system."""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import structlog

from src.momentum.base import FactorScore

logger = structlog.get_logger()


@dataclass
class ProactiveMomentumScore:
    """Composite momentum score for a symbol."""
    
    symbol: str
    composite_score: float  # 0.0 to 1.0 (weighted average of factors)
    confidence: float  # 0.0 to 1.0 (based on number of contributing factors)
    timestamp: datetime
    
    # Individual factor scores
    factor_scores: Dict[str, FactorScore]
    
    # Metadata
    factors_used: int
    factors_available: int
    missing_factors: List[str]
    
    def __post_init__(self):
        """Validate score ranges."""
        if not 0.0 <= self.composite_score <= 1.0:
            raise ValueError(f"Composite score must be 0-1, got {self.composite_score}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0-1, got {self.confidence}")
    
    @classmethod
    def from_factors(
        cls,
        symbol: str,
        factor_scores: Dict[str, FactorScore],
        factor_weights: Dict[str, float],
        available_factors: List[str]
    ) -> "ProactiveMomentumScore":
        """Create composite score from individual factor scores.
        
        Args:
            symbol: Symbol being scored
            factor_scores: Dict of factor_name -> FactorScore
            factor_weights: Dict of factor_name -> weight
            available_factors: List of all available factor names
            
        Returns:
            ProactiveMomentumScore
        """
        if not factor_scores:
            # No factors available - return zero score
            return cls(
                symbol=symbol,
                composite_score=0.0,
                confidence=0.0,
                timestamp=datetime.utcnow(),
                factor_scores={},
                factors_used=0,
                factors_available=len(available_factors),
                missing_factors=available_factors
            )
        
        # Calculate weighted composite score
        total_weight = 0.0
        weighted_sum = 0.0
        confidence_sum = 0.0
        
        for factor_name, score in factor_scores.items():
            weight = factor_weights.get(factor_name, 1.0)
            weighted_sum += score.score * weight
            total_weight += weight
            confidence_sum += score.confidence
        
        # Normalize
        composite_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Confidence based on:
        # 1. Average confidence of contributing factors
        # 2. Percentage of available factors that contributed
        avg_factor_confidence = confidence_sum / len(factor_scores)
        factor_coverage = len(factor_scores) / len(available_factors)
        confidence = (avg_factor_confidence * 0.6) + (factor_coverage * 0.4)
        
        # Find missing factors
        missing = [f for f in available_factors if f not in factor_scores]
        
        logger.info(
            "momentum_score_calculated",
            symbol=symbol,
            composite_score=round(composite_score, 3),
            confidence=round(confidence, 3),
            factors_used=len(factor_scores),
            factors_available=len(available_factors),
            missing_factors=missing
        )
        
        return cls(
            symbol=symbol,
            composite_score=composite_score,
            confidence=confidence,
            timestamp=datetime.utcnow(),
            factor_scores=factor_scores,
            factors_used=len(factor_scores),
            factors_available=len(available_factors),
            missing_factors=missing
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API/logging.
        
        Returns:
            Dictionary representation
        """
        return {
            'symbol': self.symbol,
            'composite_score': round(self.composite_score, 3),
            'confidence': round(self.confidence, 3),
            'timestamp': self.timestamp.isoformat(),
            'factors_used': self.factors_used,
            'factors_available': self.factors_available,
            'missing_factors': self.missing_factors,
            'factor_scores': {
                name: {
                    'score': round(score.score, 3),
                    'confidence': round(score.confidence, 3),
                    'metadata': score.metadata
                }
                for name, score in self.factor_scores.items()
            }
        }
    
    def is_strong_signal(self, threshold: float = 0.7) -> bool:
        """Check if this is a strong momentum signal.
        
        Args:
            threshold: Minimum composite score to be considered strong
            
        Returns:
            True if strong signal
        """
        return self.composite_score >= threshold and self.confidence >= 0.5
    
    def is_reliable(self, min_factors: int = 2, min_confidence: float = 0.5) -> bool:
        """Check if score is reliable.
        
        Args:
            min_factors: Minimum number of factors needed
            min_confidence: Minimum confidence needed
            
        Returns:
            True if reliable
        """
        return self.factors_used >= min_factors and self.confidence >= min_confidence


class MomentumScoreRanker:
    """Ranks symbols by momentum score."""
    
    def __init__(self, min_score: float = 0.5, min_confidence: float = 0.4):
        """Initialize ranker.
        
        Args:
            min_score: Minimum composite score for ranking
            min_confidence: Minimum confidence for ranking
        """
        self.min_score = min_score
        self.min_confidence = min_confidence
    
    def rank(
        self,
        scores: List[ProactiveMomentumScore],
        top_n: Optional[int] = None
    ) -> List[ProactiveMomentumScore]:
        """Rank symbols by momentum score.
        
        Args:
            scores: List of momentum scores
            top_n: Return only top N symbols (None = all)
            
        Returns:
            List of scores sorted by composite score (descending)
        """
        # Filter by minimum thresholds
        filtered = [
            s for s in scores
            if s.composite_score >= self.min_score
            and s.confidence >= self.min_confidence
        ]
        
        # Sort by composite score (descending)
        ranked = sorted(
            filtered,
            key=lambda s: (s.composite_score, s.confidence),
            reverse=True
        )
        
        if top_n is not None:
            ranked = ranked[:top_n]
        
        logger.info(
            "momentum_ranking_complete",
            total_symbols=len(scores),
            qualified_symbols=len(filtered),
            top_n=top_n,
            returned=len(ranked)
        )
        
        return ranked
    
    def get_watchlist(
        self,
        scores: List[ProactiveMomentumScore],
        max_symbols: int = 20
    ) -> List[str]:
        """Generate dynamic watchlist from scores.
        
        Args:
            scores: List of momentum scores
            max_symbols: Maximum symbols in watchlist
            
        Returns:
            List of symbol names
        """
        ranked = self.rank(scores, top_n=max_symbols)
        return [score.symbol for score in ranked]

