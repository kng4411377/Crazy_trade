"""Tests for configuration management."""

import pytest
from pathlib import Path
import tempfile
import yaml

from src.config import BotConfig, AlpacaConfig, AllocationConfig


def test_config_from_dict():
    """Test creating config from dictionary."""
    config_dict = {
        "alpaca": {"api_key": "test_key", "secret_key": "test_secret"},
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
    assert config.alpaca.api_key == "test_key"


def test_config_from_yaml():
    """Test loading config from YAML file."""
    config_data = {
        "alpaca": {"api_key": "test_key", "secret_key": "test_secret"},
        "mode": "paper",
        "watchlist": ["TSLA", "NVDA", "AAPL"],
    }
    
    # Create both config and secrets files
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = f.name
    
    # Create a temporary secrets file in the same directory
    secrets_path = Path(temp_path).parent / "secrets.yaml"
    secrets_data = {
        "alpaca": {
            "api_key": "secret_test_key",
            "secret_key": "secret_test_secret"
        }
    }
    
    try:
        with open(secrets_path, 'w') as sf:
            yaml.dump(secrets_data, sf)
        
        config = BotConfig.from_yaml(temp_path)
        assert config.mode == "paper"
        assert len(config.watchlist) == 3
        assert "TSLA" in config.watchlist
    finally:
        Path(temp_path).unlink()
        if secrets_path.exists():
            secrets_path.unlink()


def test_watchlist_normalization():
    """Test that watchlist symbols are normalized to uppercase."""
    config_dict = {
        "alpaca": {"api_key": "test_key", "secret_key": "test_secret"},
        "mode": "paper",
        "watchlist": ["tsla", "nvda", "Aapl"],
    }
    
    config = BotConfig(**config_dict)
    
    assert config.watchlist == ["TSLA", "NVDA", "AAPL"]


def test_empty_watchlist_raises_error():
    """Test that empty watchlist raises validation error."""
    config_dict = {
        "alpaca": {"api_key": "test_key", "secret_key": "test_secret"},
        "mode": "paper",
        "watchlist": [],
    }
    
    with pytest.raises(ValueError, match="at least one symbol"):
        BotConfig(**config_dict)


def test_get_symbol_allocation():
    """Test getting symbol-specific allocation."""
    config_dict = {
        "alpaca": {"api_key": "test_key", "secret_key": "test_secret"},
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

