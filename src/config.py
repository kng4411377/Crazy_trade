"""Configuration management with Pydantic models."""

from __future__ import annotations

from typing import Dict, Optional, Literal, Union
from pathlib import Path
import os
import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class AlpacaConfig(BaseModel):
    """Alpaca API connection settings."""
    api_key: str
    secret_key: str
    # No other settings needed - paper/live is determined by config.mode


class AllocationConfig(BaseModel):
    """Position sizing and allocation settings."""
    total_usd_cap: float = 20000
    per_symbol_usd: float = 1000
    per_symbol_override: Dict[str, float] = Field(default_factory=dict)
    min_cash_reserve_percent: float = 10
    allow_fractional: bool = False


class EntriesConfig(BaseModel):
    """Entry order configuration."""
    type: Literal["buy_stop", "buy_stop_limit"] = "buy_stop"
    buy_stop_pct_above_last: float = 5.0
    stop_limit_max_slip_pct: float = 1.0
    entry_price_strategy: Literal["current", "sma", "opening"] = Field(
        default="current",
        description="Entry price calculation: 'current' (spot price), 'sma' (SMA of last N bars), 'opening' (today's open)"
    )
    sma_periods: int = Field(
        default=10,
        description="Number of periods for SMA calculation (only used if entry_price_strategy='sma')"
    )
    tif: str = Field(
        default="DAY",
        description="Time-in-force: DAY (cancel at close), GTC (good till cancelled), IOC, FOK, etc."
    )
    cancel_at_close: bool = True
    rearm_next_session: bool = True


class StopsConfig(BaseModel):
    """Trailing stop configuration."""
    trailing_stop_pct: float = 10.0
    use_trailing_limit: bool = False
    trail_limit_offset_pct: float = 0.2
    tif: str = Field(
        default="GTC",
        description="Time-in-force: GTC (good till cancelled), DAY (cancel at close), etc."
    )


class HoursConfig(BaseModel):
    """Market hours configuration."""
    calendar: str = "XNYS"
    allow_pre_market: bool = False
    allow_after_hours: bool = False
    skip_first_minutes: int = 5  # Skip first N minutes after open (avoid volatility)
    skip_last_minutes: int = 10  # Skip last N minutes before close (avoid volatility)


class CooldownsConfig(BaseModel):
    """Cooldown periods configuration."""
    after_stopout_minutes: int = 20


class PollingConfig(BaseModel):
    """Polling intervals configuration."""
    price_seconds: int = 10
    orders_seconds: int = 15
    keepalive_seconds: int = 300  # Keep connection alive (5 minutes default)
    event_check_seconds: int = 5  # Check for order updates/fills (Alpaca REST polling)


class RiskConfig(BaseModel):
    """Risk management settings."""
    max_total_exposure_usd: float = 20000
    max_symbol_exposure_usd: float = 2000
    max_daily_loss_pct: Optional[float] = None  # Stop trading if daily loss exceeds this %
    max_daily_loss_usd: Optional[float] = None  # Stop trading if daily loss exceeds this $
    max_concurrent_positions: Optional[int] = None  # Max number of simultaneous positions


class PersistenceConfig(BaseModel):
    """Database persistence settings."""
    db_url: str = "sqlite:///bot.db"


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"


class AlertsConfig(BaseModel):
    """Alerts configuration."""
    webhook: Optional[str] = None


class BotConfig(BaseModel):
    """Main bot configuration."""
    alpaca: AlpacaConfig
    mode: Literal["paper", "live"] = "paper"
    watchlist: list[str] = Field(default_factory=list)
    crypto_watchlist: list[str] = Field(default_factory=list)  # NEW: Crypto symbols
    allocation: AllocationConfig = Field(default_factory=AllocationConfig)
    entries: EntriesConfig = Field(default_factory=EntriesConfig)
    stops: StopsConfig = Field(default_factory=StopsConfig)
    hours: HoursConfig = Field(default_factory=HoursConfig)
    cooldowns: CooldownsConfig = Field(default_factory=CooldownsConfig)
    polling: PollingConfig = Field(default_factory=PollingConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    persistence: PersistenceConfig = Field(default_factory=PersistenceConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    alerts: AlertsConfig = Field(default_factory=AlertsConfig)

    @field_validator("watchlist")
    @classmethod
    def validate_watchlist(cls, v):
        """Normalize stock watchlist to uppercase."""
        if v is None:
            return []
        return [s.upper() for s in v]
    
    @field_validator("crypto_watchlist")
    @classmethod
    def validate_crypto_watchlist(cls, v):
        """Normalize crypto watchlist to uppercase with /USD suffix if needed."""
        if v is None:
            return []
        normalized = []
        for symbol in v:
            symbol = symbol.upper()
            # Add /USD suffix if not present (Alpaca format)
            if '/' not in symbol:
                symbol = f"{symbol}/USD"
            normalized.append(symbol)
        return normalized

    @model_validator(mode="after")
    def require_at_least_one_symbol(self):
        """Require at least one symbol in watchlist or crypto_watchlist."""
        if not (self.watchlist or self.crypto_watchlist):
            raise ValueError("at least one symbol required in watchlist or crypto_watchlist")
        return self
    
    def get_all_symbols(self) -> list[str]:
        """Get combined list of all symbols (stocks + crypto)."""
        return self.watchlist + self.crypto_watchlist
    
    def is_crypto_symbol(self, symbol: str) -> bool:
        """Check if a symbol is crypto."""
        symbol = symbol.upper()
        return symbol in self.crypto_watchlist or '/' in symbol

    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "BotConfig":
        """
        Load configuration from YAML file.
        
        This method loads both config.yaml and secrets.yaml:
        - config.yaml: Main configuration (safe to commit)
        - secrets.yaml: API keys and secrets (in .gitignore)
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        # Load main config
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        if data is None:
            data = {}

        # Single config: derive top-level crypto_watchlist from crypto section when enabled
        if "crypto_watchlist" not in data:
            crypto_section = data.get("crypto") or {}
            if crypto_section.get("enabled") and crypto_section.get("watchlist"):
                data["crypto_watchlist"] = crypto_section.get("watchlist", [])
            else:
                data["crypto_watchlist"] = []

        # Load secrets from secrets.yaml (single file for all API keys and optional env)
        secrets_path = path.parent / "secrets.yaml"
        if secrets_path.exists():
            with open(secrets_path, "r") as f:
                secrets = yaml.safe_load(f)
            if secrets is None:
                secrets = {}

            # Merge secrets into config data
            if "alpaca" in secrets:
                data["alpaca"] = secrets["alpaca"]

            # Optional: export env section to os.environ (for momentum/other code using os.getenv)
            env_section = secrets.get("env")
            if isinstance(env_section, dict):
                for k, v in env_section.items():
                    if k and v is not None and str(v).strip():
                        os.environ.setdefault(k, str(v).strip())
        else:
            # If no secrets.yaml, check for .env or environment variables
            if "ALPACA_API_KEY" in os.environ and "ALPACA_SECRET_KEY" in os.environ:
                data["alpaca"] = {
                    "api_key": os.environ["ALPACA_API_KEY"],
                    "secret_key": os.environ["ALPACA_SECRET_KEY"]
                }
            else:
                raise FileNotFoundError(
                    f"secrets.yaml not found at {secrets_path}\n"
                    "Please create it from secrets.yaml.example:\n"
                    "  cp secrets.yaml.example secrets.yaml\n"
                    "  # Then edit secrets.yaml with your API keys"
                )
        
        return cls(**data)

    def get_symbol_allocation(self, symbol: str) -> float:
        """Get allocation for a specific symbol."""
        return self.allocation.per_symbol_override.get(
            symbol.upper(), 
            self.allocation.per_symbol_usd
        )

