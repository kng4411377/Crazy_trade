"""Momentum Intelligence Engine."""

from typing import List, Dict, Optional, Any
import asyncio
import structlog

from src.momentum.base import MomentumFactor, ProviderRegistry
from src.momentum.score import ProactiveMomentumScore, MomentumScoreRanker

logger = structlog.get_logger()


class MomentumEngine:
    """Main momentum intelligence engine."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize momentum engine.
        
        Args:
            config: Momentum layer configuration
        """
        self.config = config
        self.enabled = config.get('enabled', False)
        self.provider_registry = ProviderRegistry()
        self.factors: List[MomentumFactor] = []
        self.factor_weights = config.get('factor_weights', {})
        self.ranker = MomentumScoreRanker(
            min_score=config.get('min_score', 0.5),
            min_confidence=config.get('min_confidence', 0.4)
        )
        
        logger.info(
            "momentum_engine_initialized",
            enabled=self.enabled,
            factor_weights=self.factor_weights
        )
    
    def register_factor(self, factor: MomentumFactor):
        """Register a momentum factor.
        
        Args:
            factor: Momentum factor to register
        """
        self.factors.append(factor)
        logger.info("momentum_factor_registered", factor=factor.name)
    
    async def initialize(self) -> bool:
        """Initialize all providers and factors.
        
        Returns:
            True if initialization successful
        """
        if not self.enabled:
            logger.info("momentum_engine_disabled")
            return False
        
        logger.info("initializing_momentum_engine")
        
        # Initialize all providers
        providers = self.provider_registry.get_all()
        init_results = await asyncio.gather(
            *[p.initialize() for p in providers],
            return_exceptions=True
        )
        
        successful = sum(1 for r in init_results if r is True)
        failed = len(init_results) - successful
        
        logger.info(
            "providers_initialized",
            total=len(providers),
            successful=successful,
            failed=failed
        )
        
        if successful == 0:
            logger.error("no_providers_available_disabling_momentum")
            self.enabled = False
            return False
        
        return True
    
    async def calculate_score(self, symbol: str) -> Optional[ProactiveMomentumScore]:
        """Calculate momentum score for a symbol.
        
        Args:
            symbol: Stock or crypto symbol
            
        Returns:
            ProactiveMomentumScore or None if unable to calculate
        """
        if not self.enabled:
            return None
        
        logger.debug("calculating_momentum_score", symbol=symbol)
        
        # Calculate all factor scores in parallel
        factor_tasks = [
            factor.calculate_with_fallback(symbol)
            for factor in self.factors
            if factor.enabled
        ]
        
        factor_results = await asyncio.gather(*factor_tasks, return_exceptions=True)
        
        # Collect successful scores
        factor_scores = {}
        for factor, result in zip(self.factors, factor_results):
            if isinstance(result, Exception):
                logger.warning(
                    "factor_calculation_failed",
                    factor=factor.name,
                    symbol=symbol,
                    error=str(result)
                )
                continue
            
            if result is not None:
                factor_scores[factor.name] = result
        
        # Build composite score
        available_factors = [f.name for f in self.factors if f.enabled]
        
        score = ProactiveMomentumScore.from_factors(
            symbol=symbol,
            factor_scores=factor_scores,
            factor_weights=self.factor_weights,
            available_factors=available_factors
        )
        
        return score
    
    async def score_universe(
        self,
        symbols: List[str],
        parallel_limit: int = 10
    ) -> List[ProactiveMomentumScore]:
        """Score multiple symbols.
        
        Args:
            symbols: List of symbols to score
            parallel_limit: Max concurrent scoring operations
            
        Returns:
            List of momentum scores
        """
        if not self.enabled:
            logger.warning("momentum_engine_disabled_skipping_universe_scoring")
            return []
        
        logger.info("scoring_universe", symbol_count=len(symbols))
        
        # Use semaphore to limit concurrency
        semaphore = asyncio.Semaphore(parallel_limit)
        
        async def score_with_limit(symbol: str):
            async with semaphore:
                return await self.calculate_score(symbol)
        
        scores = await asyncio.gather(
            *[score_with_limit(s) for s in symbols],
            return_exceptions=True
        )
        
        # Filter out errors and None results
        valid_scores = [
            s for s in scores
            if s is not None and not isinstance(s, Exception)
        ]
        
        logger.info(
            "universe_scoring_complete",
            total_symbols=len(symbols),
            successful=len(valid_scores),
            failed=len(symbols) - len(valid_scores)
        )
        
        return valid_scores
    
    async def generate_watchlist(
        self,
        universe: List[str],
        max_symbols: int = 20
    ) -> List[str]:
        """Generate dynamic watchlist from universe.
        
        Args:
            universe: List of symbols to consider
            max_symbols: Maximum symbols in watchlist
            
        Returns:
            List of top momentum symbols
        """
        if not self.enabled:
            logger.warning("momentum_engine_disabled_returning_empty_watchlist")
            return []
        
        logger.info("generating_dynamic_watchlist", universe_size=len(universe))
        
        # Score all symbols
        scores = await self.score_universe(universe)
        
        # Generate watchlist
        watchlist = self.ranker.get_watchlist(scores, max_symbols=max_symbols)
        
        logger.info(
            "watchlist_generated",
            symbols=watchlist,
            count=len(watchlist)
        )
        
        return watchlist
    
    async def get_top_momentum(
        self,
        universe: List[str],
        top_n: int = 10
    ) -> List[ProactiveMomentumScore]:
        """Get top N momentum symbols.
        
        Args:
            universe: List of symbols to consider
            top_n: Number of top symbols to return
            
        Returns:
            List of top momentum scores
        """
        if not self.enabled:
            return []
        
        scores = await self.score_universe(universe)
        return self.ranker.rank(scores, top_n=top_n)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of momentum engine.
        
        Returns:
            Dict with health status
        """
        provider_health = await self.provider_registry.health_check_all()
        
        available_providers = [
            name for name, health in provider_health.items()
            if health.is_available
        ]
        
        enabled_factors = [f.name for f in self.factors if f.enabled]
        
        return {
            'enabled': self.enabled,
            'providers': {
                'total': len(provider_health),
                'available': len(available_providers),
                'unavailable': len(provider_health) - len(available_providers),
                'details': {
                    name: {
                        'available': health.is_available,
                        'last_check': health.last_check.isoformat(),
                        'error': health.error_message,
                        'rate_limited': health.rate_limited
                    }
                    for name, health in provider_health.items()
                }
            },
            'factors': {
                'total': len(self.factors),
                'enabled': len(enabled_factors),
                'names': enabled_factors
            }
        }

