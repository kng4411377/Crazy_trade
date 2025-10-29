"""Position sizing logic."""

from typing import Dict, Optional
import structlog

from src.config import BotConfig

logger = structlog.get_logger()


class PositionSizer:
    """Calculate position sizes based on dollar allocation."""

    def __init__(self, config: BotConfig):
        """Initialize position sizer with configuration."""
        self.config = config

    def calculate_quantity(
        self,
        symbol: str,
        last_price: float,
        current_positions: Optional[Dict[str, float]] = None,
        account_value: Optional[float] = None,
    ) -> int:
        """
        Calculate quantity to buy for a symbol.
        
        Args:
            symbol: Stock symbol
            last_price: Current price
            current_positions: Dict of symbol -> position value (USD)
            account_value: Total account value
            
        Returns:
            Quantity to buy (0 if constraints violated)
        """
        if last_price <= 0:
            logger.warning("invalid_price", symbol=symbol, price=last_price)
            return 0

        # Get symbol-specific allocation
        symbol_allocation = self.config.get_symbol_allocation(symbol)

        # Calculate raw quantity
        if self.config.allocation.allow_fractional:
            raw_qty = symbol_allocation / last_price
        else:
            raw_qty = int(symbol_allocation / last_price)

        if raw_qty == 0:
            logger.warning(
                "quantity_too_small",
                symbol=symbol,
                allocation=symbol_allocation,
                price=last_price,
            )
            return 0

        # Check symbol exposure limit
        position_value = raw_qty * last_price
        if position_value > self.config.risk.max_symbol_exposure_usd:
            # Scale down
            raw_qty = int(self.config.risk.max_symbol_exposure_usd / last_price)
            position_value = raw_qty * last_price
            logger.info(
                "position_scaled_down_symbol_limit",
                symbol=symbol,
                qty=raw_qty,
                value=position_value,
            )

        # Check total exposure limit
        if current_positions:
            total_exposure = sum(current_positions.values()) + position_value
            if total_exposure > self.config.risk.max_total_exposure_usd:
                logger.warning(
                    "total_exposure_limit_reached",
                    symbol=symbol,
                    total_exposure=total_exposure,
                    limit=self.config.risk.max_total_exposure_usd,
                )
                return 0

        # Check cash reserve if account value provided
        if account_value:
            min_cash_reserve = (
                account_value * self.config.allocation.min_cash_reserve_percent / 100
            )
            current_cash = account_value - sum(
                current_positions.values() if current_positions else []
            )
            
            if current_cash - position_value < min_cash_reserve:
                logger.warning(
                    "insufficient_cash_reserve",
                    symbol=symbol,
                    cash=current_cash,
                    required_reserve=min_cash_reserve,
                )
                return 0

        logger.info(
            "position_sized",
            symbol=symbol,
            qty=raw_qty,
            price=last_price,
            value=position_value,
        )

        return int(raw_qty) if not self.config.allocation.allow_fractional else raw_qty

    def check_exposure_limit(
        self, symbol: str, position_value: float, current_positions: Dict[str, float]
    ) -> bool:
        """
        Check if adding a position would violate exposure limits.
        
        Args:
            symbol: Stock symbol
            position_value: Value of new position
            current_positions: Dict of symbol -> position value
            
        Returns:
            True if within limits, False otherwise
        """
        # Check symbol limit
        if position_value > self.config.risk.max_symbol_exposure_usd:
            logger.warning(
                "symbol_exposure_limit_exceeded",
                symbol=symbol,
                value=position_value,
                limit=self.config.risk.max_symbol_exposure_usd,
            )
            return False

        # Check total limit
        total_exposure = sum(current_positions.values()) + position_value
        if total_exposure > self.config.risk.max_total_exposure_usd:
            logger.warning(
                "total_exposure_limit_exceeded",
                total_exposure=total_exposure,
                limit=self.config.risk.max_total_exposure_usd,
            )
            return False

        return True

    def get_current_exposure(self, positions: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate current exposure metrics.
        
        Args:
            positions: Dict of symbol -> position value
            
        Returns:
            Dict with exposure metrics
        """
        total = sum(positions.values())
        return {
            "total_exposure_usd": total,
            "remaining_capacity_usd": self.config.risk.max_total_exposure_usd - total,
            "utilization_pct": (total / self.config.risk.max_total_exposure_usd) * 100,
            "num_positions": len(positions),
        }

