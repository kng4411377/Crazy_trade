"""Tests for configuration management."""

import pytest
from pathlib import Path
import tempfile
import yaml

from src.config import BotConfig, IBKRConfig, AllocationConfig


def test_config_from_dict():
    """Test creating config from dictionary."""
    config_dict = {
        "ibkr": {"host": "127.0.0.1", "port": 5000, "client_id": 12, "account": None},
        "mode": "paper",
        "watchlist": ["TSLA", "NVDA"],
        "allocation": {
            "total_usd_cap": 20000,
            "per_symbol_usd": 1000,
            "per_symbol_override": {},
            "min_cash_reserve_percent": 10,
            "allow_fractional": False,
        },
    }
    
    config = BotConfig(**config_dict)
    
    assert config.mode == "paper"
    assert config.watchlist == ["TSLA", "NVDA"]
    assert config.ibkr.port == 5000


def test_config_from_yaml():
    """Test loading config from YAML file."""
    config_data = {
        "ibkr": {"host": "127.0.0.1", "port": 5000, "client_id": 12},
        "mode": "paper",
        "watchlist": ["TSLA", "NVDA", "AAPL"],
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = f.name
    
    try:
        config = BotConfig.from_yaml(temp_path)
        assert config.mode == "paper"
        assert len(config.watchlist) == 3
        assert "TSLA" in config.watchlist
    finally:
        Path(temp_path).unlink()


def test_watchlist_normalization():
    """Test that watchlist symbols are normalized to uppercase."""
    config_dict = {
        "ibkr": {"host": "127.0.0.1", "port": 5000, "client_id": 12},
        "mode": "paper",
        "watchlist": ["tsla", "nvda", "Aapl"],
    }
    
    config = BotConfig(**config_dict)
    
    assert config.watchlist == ["TSLA", "NVDA", "AAPL"]


def test_empty_watchlist_raises_error():
    """Test that empty watchlist raises validation error."""
    config_dict = {
        "ibkr": {"host": "127.0.0.1", "port": 5000, "client_id": 12},
        "mode": "paper",
        "watchlist": [],
    }
    
    with pytest.raises(ValueError, match="at least one symbol"):
        BotConfig(**config_dict)


def test_get_symbol_allocation():
    """Test getting symbol-specific allocation."""
    config_dict = {
        "ibkr": {"host": "127.0.0.1", "port": 5000, "client_id": 12},
        "mode": "paper",
        "watchlist": ["TSLA", "NVDA"],
        "allocation": {
            "per_symbol_usd": 1000,
            "per_symbol_override": {"TSLA": 1500},
        },
    }
    
    config = BotConfig(**config_dict)
    
    assert config.get_symbol_allocation("TSLA") == 1500
    assert config.get_symbol_allocation("NVDA") == 1000
    assert config.get_symbol_allocation("tsla") == 1500  # Case insensitive

