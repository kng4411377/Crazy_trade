"""Tests for position sizing."""

import pytest

from src.config import BotConfig
from src.sizing import PositionSizer


@pytest.fixture
def config():
    """Create test configuration."""
    return BotConfig(
        alpaca={"api_key": "test_key", "secret_key": "test_secret"},
        mode="paper",
        watchlist=["TSLA", "NVDA"],
        allocation={
            "total_usd_cap": 20000,
            "per_symbol_usd": 1000,
            "per_symbol_override": {"TSLA": 1500},
            "min_cash_reserve_percent": 10,
            "allow_fractional": False,
        },
        risk={
            "max_total_exposure_usd": 20000,
            "max_symbol_exposure_usd": 2000,
        },
    )


def test_calculate_quantity_basic(config):
    """Test basic quantity calculation."""
    sizer = PositionSizer(config)
    
    # NVDA at $500/share with $1000 allocation = 2 shares
    qty = sizer.calculate_quantity("NVDA", 500.0, {}, 50000)
    assert qty == 2


def test_calculate_quantity_with_override(config):
    """Test quantity calculation with symbol override."""
    sizer = PositionSizer(config)
    
    # TSLA at $250/share with $1500 allocation (override) = 6 shares
    qty = sizer.calculate_quantity("TSLA", 250.0, {}, 50000)
    assert qty == 6


def test_calculate_quantity_too_small(config):
    """Test that high-priced stocks return zero qty when allocation too small."""
    sizer = PositionSizer(config)
    
    # Stock at $2000/share with $1000 allocation = 0 shares
    qty = sizer.calculate_quantity("NVDA", 2000.0, {}, 50000)
    assert qty == 0


def test_symbol_exposure_limit(config):
    """Test that symbol exposure limit is enforced."""
    sizer = PositionSizer(config)
    
    # Stock at $100/share, would normally buy 10 shares = $1000
    # But symbol limit is $2000, so should scale down if needed
    qty = sizer.calculate_quantity("NVDA", 100.0, {}, 50000)
    assert qty == 10  # Within limit
    
    # Stock at $100/share, would normally buy 15 shares = $1500
    # But if we try with override for more allocation
    config.allocation.per_symbol_override["NVDA"] = 3000  # Above $2000 limit
    qty = sizer.calculate_quantity("NVDA", 100.0, {}, 50000)
    assert qty <= 20  # Limited by max_symbol_exposure_usd ($2000)


def test_total_exposure_limit(config):
    """Test that total exposure limit is enforced."""
    sizer = PositionSizer(config)
    
    # Already have $19,500 in positions
    current_positions = {"AAPL": 19500}
    
    # Try to add $1000 position (would exceed $20,000 limit)
    qty = sizer.calculate_quantity("NVDA", 100.0, current_positions, 50000)
    assert qty == 0  # Rejected due to total exposure


def test_cash_reserve_requirement(config):
    """Test cash reserve requirement."""
    sizer = PositionSizer(config)
    
    # Account value $10,000, need to keep 10% = $1,000 in cash
    # Current positions = $8,000, so cash = $2,000
    # Can use up to $1,000 (leaving $1,000 reserve)
    current_positions = {"AAPL": 8000}
    
    # Try to buy $1500 worth (would violate cash reserve)
    qty = sizer.calculate_quantity("NVDA", 150.0, current_positions, 10000)
    # Should be limited or rejected
    assert qty == 0 or qty * 150.0 <= 1000


def test_fractional_shares_allowed(config):
    """Test fractional share handling when enabled."""
    config.allocation.allow_fractional = True
    sizer = PositionSizer(config)
    
    # $1000 allocation / $333 per share = ~3.003 shares
    qty = sizer.calculate_quantity("NVDA", 333.0, {}, 50000)
    assert qty > 3.0
    assert qty < 3.1


def test_check_exposure_limit(config):
    """Test exposure limit checking."""
    sizer = PositionSizer(config)
    
    # Within limits
    assert sizer.check_exposure_limit("NVDA", 1000, {"AAPL": 5000}) is True
    
    # Exceeds symbol limit
    assert sizer.check_exposure_limit("NVDA", 2500, {}) is False
    
    # Exceeds total limit
    assert sizer.check_exposure_limit("NVDA", 1000, {"AAPL": 19500}) is False


def test_get_current_exposure(config):
    """Test exposure metrics calculation."""
    sizer = PositionSizer(config)
    
    positions = {"AAPL": 5000, "MSFT": 3000, "GOOGL": 2000}
    metrics = sizer.get_current_exposure(positions)
    
    assert metrics["total_exposure_usd"] == 10000
    assert metrics["remaining_capacity_usd"] == 10000
    assert metrics["utilization_pct"] == 50.0
    assert metrics["num_positions"] == 3

