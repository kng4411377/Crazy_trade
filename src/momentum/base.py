"""Base classes for momentum layer providers and factors."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import structlog

logger = structlog.get_logger()


class ProviderCapability(Enum):
    """Capabilities that a data provider can offer."""
    PRICE = "price"              # Historical/current price data
    VOLUME = "volume"            # Volume data
    OPTIONS = "options"          # Options flow and data
    SENTIMENT = "sentiment"      # Social sentiment
    TECHNICALS = "technicals"    # Technical indicators
    FUNDAMENTALS = "fundamentals"  # Fundamental data
    SHORT_INTEREST = "short_interest"  # Short selling data
    DARK_POOL = "dark_pool"      # Dark pool data
    GAMMA = "gamma"              # Gamma exposure data


@dataclass
class ProviderHealth:
    """Health status of a data provider."""
    provider_name: str
    is_available: bool
    last_check: datetime
    error_message: Optional[str] = None
    rate_limited: bool = False


class DataProvider(ABC):
    """Base class for all data providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize provider with configuration.
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config
        self.name = self.__class__.__name__
        self._is_available = False
        self._last_health_check = None
        self._error_count = 0
        self._max_errors = 3
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize provider connection and validate credentials.
        
        Returns:
            True if initialization successful
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        """Check provider health and availability.
        
        Returns:
            ProviderHealth status object
        """
        pass
    
    def is_available(self) -> bool:
        """Check if provider is currently available.
        
        Returns:
            True if provider can be used
        """
        return self._is_available and self._error_count < self._max_errors
    
    def record_error(self, error: Exception):
        """Record an error for this provider.
        
        Args:
            error: Exception that occurred
        """
        self._error_count += 1
        logger.warning(
            "provider_error",
            provider=self.name,
            error=str(error),
            error_count=self._error_count,
            max_errors=self._max_errors
        )
        
        if self._error_count >= self._max_errors:
            self._is_available = False
            logger.error(
                "provider_disabled",
                provider=self.name,
                reason="max_errors_exceeded"
            )
    
    def reset_error_count(self):
        """Reset error counter after successful operation."""
        if self._error_count > 0:
            logger.info("provider_errors_cleared", provider=self.name)
        self._error_count = 0


@dataclass
class FactorScore:
    """Score from a single momentum factor."""
    factor_name: str
    symbol: str
    score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    timestamp: datetime
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        """Validate score ranges."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be 0-1, got {self.score}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0-1, got {self.confidence}")


class MomentumFactor(ABC):
    """Base class for momentum scoring factors."""
    
    def __init__(self, providers: List[DataProvider], config: Dict[str, Any]):
        """Initialize factor with data providers.
        
        Args:
            providers: List of data providers this factor can use
            config: Factor-specific configuration
        """
        self.providers = providers
        self.config = config
        self.name = self.__class__.__name__
        self.weight = config.get('weight', 1.0)
        self.enabled = config.get('enabled', True)
        
    @abstractmethod
    async def calculate_score(self, symbol: str) -> Optional[FactorScore]:
        """Calculate momentum score for a symbol.
        
        Args:
            symbol: Stock or crypto symbol
            
        Returns:
            FactorScore or None if unable to calculate
        """
        pass
    
    def get_available_providers(self) -> List[DataProvider]:
        """Get list of available providers for this factor.
        
        Returns:
            List of available providers
        """
        return [p for p in self.providers if p.is_available()]
    
    async def calculate_with_fallback(self, symbol: str) -> Optional[FactorScore]:
        """Calculate score with provider fallback logic.
        
        Tries each provider in priority order until one succeeds.
        
        Args:
            symbol: Stock or crypto symbol
            
        Returns:
            FactorScore or None if all providers failed
        """
        if not self.enabled:
            logger.debug("factor_disabled", factor=self.name, symbol=symbol)
            return None
        
        available_providers = self.get_available_providers()
        
        if not available_providers:
            logger.warning(
                "no_providers_available",
                factor=self.name,
                symbol=symbol,
                total_providers=len(self.providers)
            )
            return None
        
        for provider in available_providers:
            try:
                score = await self.calculate_score(symbol)
                if score is not None:
                    provider.reset_error_count()
                    return score
            except Exception as e:
                provider.record_error(e)
                logger.warning(
                    "provider_failed_trying_next",
                    factor=self.name,
                    provider=provider.name,
                    symbol=symbol,
                    error=str(e)
                )
                continue
        
        logger.error(
            "all_providers_failed",
            factor=self.name,
            symbol=symbol,
            providers_tried=len(available_providers)
        )
        return None


class ProviderRegistry:
    """Registry for managing data providers."""
    
    def __init__(self):
        """Initialize empty provider registry."""
        self._providers: Dict[str, DataProvider] = {}
        
    def register(self, provider: DataProvider):
        """Register a provider.
        
        Args:
            provider: Provider instance to register
        """
        self._providers[provider.name] = provider
        logger.info("provider_registered", provider=provider.name)
    
    def get(self, name: str) -> Optional[DataProvider]:
        """Get provider by name.
        
        Args:
            name: Provider name
            
        Returns:
            Provider instance or None
        """
        return self._providers.get(name)
    
    def get_all(self) -> List[DataProvider]:
        """Get all registered providers.
        
        Returns:
            List of all providers
        """
        return list(self._providers.values())
    
    def get_available(self) -> List[DataProvider]:
        """Get all available providers.
        
        Returns:
            List of available providers
        """
        return [p for p in self._providers.values() if p.is_available()]
    
    async def health_check_all(self) -> Dict[str, ProviderHealth]:
        """Run health checks on all providers.
        
        Returns:
            Dict mapping provider name to health status
        """
        results = {}
        for provider in self._providers.values():
            try:
                health = await provider.health_check()
                results[provider.name] = health
            except Exception as e:
                results[provider.name] = ProviderHealth(
                    provider_name=provider.name,
                    is_available=False,
                    last_check=datetime.utcnow(),
                    error_message=str(e)
                )
        return results

