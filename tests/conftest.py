"""Shared pytest fixtures."""

import pytest
from src.config import BotConfig
from src.database import DatabaseManager


@pytest.fixture
def test_config():
    """Create a test configuration."""
    return BotConfig(
        ibkr={"host": "127.0.0.1", "port": 5000, "client_id": 12},
        mode="paper",
        watchlist=["TSLA", "NVDA", "AAPL"],
        allocation={
            "total_usd_cap": 20000,
            "per_symbol_usd": 1000,
            "per_symbol_override": {"TSLA": 1500},
            "min_cash_reserve_percent": 10,
            "allow_fractional": False,
        },
        entries={
            "type": "buy_stop",
            "buy_stop_pct_above_last": 5.0,
            "stop_limit_max_slip_pct": 1.0,
            "tif": "DAY",
            "cancel_at_close": True,
            "rearm_next_session": True,
        },
        stops={
            "trailing_stop_pct": 10.0,
            "use_trailing_limit": False,
            "trail_limit_offset_pct": 0.2,
            "tif": "GTC",
        },
        cooldowns={"after_stopout_minutes": 20},
        risk={
            "max_total_exposure_usd": 20000,
            "max_symbol_exposure_usd": 2000,
        },
    )


@pytest.fixture
def test_db():
    """Create a test database."""
    db = DatabaseManager("sqlite:///:memory:")
    db.create_tables()
    yield db
    # Cleanup handled by in-memory DB

