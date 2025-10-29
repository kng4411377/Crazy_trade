"""Configuration management with Pydantic models."""

from typing import Dict, Optional, Literal
from pathlib import Path
import yaml
from pydantic import BaseModel, Field, field_validator


class IBKRConfig(BaseModel):
    """IBKR connection settings."""
    host: str = "127.0.0.1"
    port: int = 5000
    client_id: int = 12
    account: Optional[str] = None


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
    tif: str = "DAY"
    cancel_at_close: bool = True
    rearm_next_session: bool = True


class StopsConfig(BaseModel):
    """Trailing stop configuration."""
    trailing_stop_pct: float = 10.0
    use_trailing_limit: bool = False
    trail_limit_offset_pct: float = 0.2
    tif: str = "GTC"


class HoursConfig(BaseModel):
    """Market hours configuration."""
    calendar: str = "XNYS"
    allow_pre_market: bool = False
    allow_after_hours: bool = False


class CooldownsConfig(BaseModel):
    """Cooldown periods configuration."""
    after_stopout_minutes: int = 20


class PollingConfig(BaseModel):
    """Polling intervals configuration."""
    price_seconds: int = 10
    orders_seconds: int = 15


class RiskConfig(BaseModel):
    """Risk management settings."""
    max_total_exposure_usd: float = 20000
    max_symbol_exposure_usd: float = 2000


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
    ibkr: IBKRConfig
    mode: Literal["paper", "live"] = "paper"
    watchlist: list[str] = Field(default_factory=list)
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
        """Ensure watchlist has at least one symbol."""
        if not v:
            raise ValueError("Watchlist must contain at least one symbol")
        return [s.upper() for s in v]

    @classmethod
    def from_yaml(cls, path: str | Path) -> "BotConfig":
        """Load configuration from YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        
        return cls(**data)

    def get_symbol_allocation(self, symbol: str) -> float:
        """Get allocation for a specific symbol."""
        return self.allocation.per_symbol_override.get(
            symbol.upper(), 
            self.allocation.per_symbol_usd
        )

