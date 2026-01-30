"""
Technical Indicators Calculator.

Calculates RSI, MACD, Bollinger Bands, VWAP, OBV, ATR, and other indicators
for use in AI analysis. Uses config switches so only enabled indicators
are computed (saves CPU on low-power hardware).
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog

try:
    import pandas as pd
    import numpy as np
except ImportError:
    pd = None
    np = None

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    import pandas_ta as ta
except ImportError:
    ta = None

logger = structlog.get_logger()


@dataclass
class IndicatorResult:
    """Result of indicator calculation for a symbol."""
    symbol: str
    timestamp: datetime
    price: float

    # RSI
    rsi: Optional[float] = None

    # MACD
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None

    # Bollinger Bands
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_percent: Optional[float] = None  # Where price is in band (0-1)

    # SMAs
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None

    # Volume
    volume: Optional[int] = None
    volume_sma: Optional[float] = None
    relative_volume: Optional[float] = None

    # VWAP (intraday / period context)
    vwap: Optional[float] = None
    vwap_above: Optional[bool] = None  # True if price > VWAP

    # OBV (volume flow)
    obv: Optional[float] = None

    # ATR (volatility)
    atr: Optional[float] = None

    # Price action
    price_change_1d: Optional[float] = None
    price_change_5d: Optional[float] = None
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'price': round(self.price, 2) if self.price else None,
            'rsi': round(self.rsi, 2) if self.rsi else None,
            'macd': round(self.macd, 4) if self.macd else None,
            'macd_signal': round(self.macd_signal, 4) if self.macd_signal else None,
            'macd_histogram': round(self.macd_histogram, 4) if self.macd_histogram else None,
            'bb_upper': round(self.bb_upper, 2) if self.bb_upper else None,
            'bb_middle': round(self.bb_middle, 2) if self.bb_middle else None,
            'bb_lower': round(self.bb_lower, 2) if self.bb_lower else None,
            'bb_percent': round(self.bb_percent, 2) if self.bb_percent else None,
            'sma_20': round(self.sma_20, 2) if self.sma_20 else None,
            'sma_50': round(self.sma_50, 2) if self.sma_50 else None,
            'sma_200': round(self.sma_200, 2) if self.sma_200 else None,
            'volume': self.volume,
            'volume_sma': round(self.volume_sma, 0) if self.volume_sma else None,
            'relative_volume': round(self.relative_volume, 2) if self.relative_volume else None,
            'price_change_1d': round(self.price_change_1d, 2) if self.price_change_1d else None,
            'price_change_5d': round(self.price_change_5d, 2) if self.price_change_5d else None,
        }
        if self.vwap is not None:
            d['vwap'] = round(self.vwap, 2)
            d['vwap_above'] = self.vwap_above
        if self.obv is not None:
            d['obv'] = round(self.obv, 0)
        if self.atr is not None:
            d['atr'] = round(self.atr, 4)
        return d

    def to_summary(self) -> str:
        """Generate human-readable summary for AI prompt (only includes enabled indicators)."""
        lines = [f"{self.symbol}: ${self.price:.2f}"]

        if self.rsi is not None:
            rsi_status = "oversold" if self.rsi < 30 else "overbought" if self.rsi > 70 else "neutral"
            lines.append(f"  RSI: {self.rsi:.1f} ({rsi_status})")

        if self.macd is not None and self.macd_signal is not None:
            macd_status = "bullish" if self.macd > self.macd_signal else "bearish"
            lines.append(f"  MACD: {self.macd:.4f} vs Signal {self.macd_signal:.4f} ({macd_status})")

        if self.bb_percent is not None:
            bb_status = "near upper" if self.bb_percent > 0.8 else "near lower" if self.bb_percent < 0.2 else "middle"
            lines.append(f"  Bollinger: {self.bb_percent:.0%} ({bb_status})")

        if self.vwap_above is not None:
            lines.append(f"  Price vs VWAP: {'Above' if self.vwap_above else 'Below'}")

        if self.atr is not None:
            lines.append(f"  Volatility (ATR): {self.atr:.2f}")

        if self.obv is not None:
            lines.append(f"  OBV: {self.obv:,.0f}")

        if self.relative_volume is not None:
            vol_status = "high" if self.relative_volume > 1.5 else "low" if self.relative_volume < 0.5 else "normal"
            lines.append(f"  Volume: {self.relative_volume:.1f}x average ({vol_status})")

        if self.price_change_1d is not None:
            lines.append(f"  1D Change: {self.price_change_1d:+.2f}%")

        return "\n".join(lines)


class TechnicalIndicators:
    """
    Calculate technical indicators for symbols.
    
    Uses pandas/numpy for calculations, yfinance for data.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize indicator calculator.

        Args:
            config: gemini.indicators config section
        """
        self.config = config or {}
        self._override: Dict[str, Any] = {}  # Runtime override (e.g. low_power_mode)
        self._cache: Dict[str, IndicatorResult] = {}
        self._cache_ttl = 60  # Cache for 1 minute
        self._cache_times: Dict[str, datetime] = {}

    def set_override(self, override: Optional[Dict[str, Any]]) -> None:
        """
        Set runtime override for indicator switches (e.g. low_power_mode).
        Override wins over config. Pass None to clear.
        """
        self._override = override if override else {}
        if self._override:
            self.clear_cache()  # Recompute with new effective config

    def _get_effective_config(self) -> Dict[str, Any]:
        """Merge config with override (override wins). Deep merge for nested dicts."""
        import copy
        effective = copy.deepcopy(self.config)
        for key, value in self._override.items():
            if isinstance(value, dict) and isinstance(effective.get(key), dict):
                effective[key] = {**effective[key], **value}
            else:
                effective[key] = value
        return effective
        
        # Check dependencies
        if pd is None or np is None:
            logger.error("pandas/numpy not installed - indicators will not work")
        if yf is None:
            logger.error("yfinance not installed - cannot fetch price data")
    
    def _min_required_bars(self) -> int:
        """Minimum number of candles needed for all enabled indicators (saves CPU)."""
        cfg = self._get_effective_config()
        min_bars = 30  # baseline
        if cfg.get('rsi', {}).get('enabled', True):
            min_bars = max(min_bars, cfg.get('rsi', {}).get('period', 14) + 5)
        if cfg.get('macd', {}).get('enabled', True):
            slow = cfg.get('macd', {}).get('slow_period', 26)
            signal = cfg.get('macd', {}).get('signal_period', 9)
            min_bars = max(min_bars, slow + signal + 5)
        if cfg.get('bollinger', {}).get('enabled', True):
            min_bars = max(min_bars, cfg.get('bollinger', {}).get('period', 20) + 5)
        if cfg.get('sma', {}).get('enabled', True):
            periods = cfg.get('sma', {}).get('periods', [20, 50, 200])
            if periods:
                min_bars = max(min_bars, max(periods) + 5)
        if cfg.get('atr', {}).get('enabled', False):
            min_bars = max(min_bars, cfg.get('atr', {}).get('period', 14) * 2 + 5)
        if cfg.get('vwap', {}).get('enabled', False) or cfg.get('obv', {}).get('enabled', False):
            min_bars = max(min_bars, 50)
        return min_bars

    async def calculate_for_symbol(self, symbol: str, bars: Optional[int] = None) -> Optional[IndicatorResult]:
        """
        Calculate only enabled indicators for a symbol (config switches).
        Fetches minimum required bars to save CPU.
        """
        # Check cache
        if symbol in self._cache:
            cache_time = self._cache_times.get(symbol)
            if cache_time and (datetime.now() - cache_time).total_seconds() < self._cache_ttl:
                logger.debug("indicators_cache_hit", symbol=symbol)
                return self._cache[symbol]

        required_bars = max(bars or 100, self._min_required_bars())

        try:
            df = await self._fetch_price_data(symbol, required_bars)
            if df is None or len(df) < 30:
                logger.warning("insufficient_data_for_indicators", symbol=symbol, bars=len(df) if df is not None else 0)
                return None

            current_price = float(df['Close'].iloc[-1])
            current_volume = int(df['Volume'].iloc[-1]) if 'Volume' in df.columns else None

            result = IndicatorResult(
                symbol=symbol,
                timestamp=datetime.now(),
                price=current_price,
                volume=current_volume
            )

            cfg = self._get_effective_config()

            # RSI (only if enabled)
            if cfg.get('rsi', {}).get('enabled', True):
                period = cfg.get('rsi', {}).get('period', 14)
                result.rsi = self._calculate_rsi(df['Close'], period)

            # MACD (only if enabled)
            if cfg.get('macd', {}).get('enabled', True):
                macd_config = cfg.get('macd', {})
                macd, signal, hist = self._calculate_macd(
                    df['Close'],
                    macd_config.get('fast_period', 12),
                    macd_config.get('slow_period', 26),
                    macd_config.get('signal_period', 9)
                )
                result.macd = macd
                result.macd_signal = signal
                result.macd_histogram = hist

            # Bollinger (only if enabled)
            if cfg.get('bollinger', {}).get('enabled', True):
                bb_config = cfg.get('bollinger', {})
                upper, middle, lower = self._calculate_bollinger(
                    df['Close'],
                    bb_config.get('period', 20),
                    bb_config.get('std_dev', 2)
                )
                result.bb_upper = upper
                result.bb_middle = middle
                result.bb_lower = lower
                if upper and lower and upper != lower:
                    result.bb_percent = (current_price - lower) / (upper - lower)

            # SMAs (only if enabled)
            if cfg.get('sma', {}).get('enabled', True):
                periods = cfg.get('sma', {}).get('periods', [20, 50, 200])
                if 20 in periods:
                    result.sma_20 = self._calculate_sma(df['Close'], 20)
                if 50 in periods:
                    result.sma_50 = self._calculate_sma(df['Close'], 50)
                if 200 in periods and len(df) >= 200:
                    result.sma_200 = self._calculate_sma(df['Close'], 200)

            # Volume (only if enabled)
            if cfg.get('volume', {}).get('enabled', True) and 'Volume' in df.columns:
                result.volume_sma = self._calculate_sma(df['Volume'], 20)
                if result.volume_sma and result.volume_sma > 0:
                    result.relative_volume = current_volume / result.volume_sma

            # VWAP (only if enabled)
            if cfg.get('vwap', {}).get('enabled', False) and 'Volume' in df.columns:
                vwap_val = self._calculate_vwap(df)
                if vwap_val is not None:
                    result.vwap = vwap_val
                    result.vwap_above = current_price > vwap_val

            # OBV (only if enabled)
            if cfg.get('obv', {}).get('enabled', False) and 'Volume' in df.columns:
                result.obv = self._calculate_obv(df)

            # ATR (only if enabled)
            if cfg.get('atr', {}).get('enabled', False):
                period = cfg.get('atr', {}).get('period', 14)
                result.atr = self._calculate_atr(df, period)

            # Price changes (lightweight)
            if len(df) >= 2:
                result.price_change_1d = ((current_price / float(df['Close'].iloc[-2])) - 1) * 100
            if len(df) >= 6:
                result.price_change_5d = ((current_price / float(df['Close'].iloc[-6])) - 1) * 100

            self._cache[symbol] = result
            self._cache_times[symbol] = datetime.now()

            logger.debug(
                "indicators_calculated",
                symbol=symbol,
                price=current_price,
                rsi=result.rsi,
                atr=result.atr
            )

            return result

        except Exception as e:
            logger.error("indicator_calculation_failed", symbol=symbol, error=str(e))
            return None
    
    async def calculate_for_symbols(self, symbols: List[str]) -> Dict[str, IndicatorResult]:
        """
        Calculate indicators for multiple symbols.
        
        Args:
            symbols: List of symbols
            
        Returns:
            Dict mapping symbol to IndicatorResult
        """
        results = {}
        
        for symbol in symbols:
            result = await self.calculate_for_symbol(symbol)
            if result:
                results[symbol] = result
        
        return results
    
    async def _fetch_price_data(self, symbol: str, bars: int) -> Optional[pd.DataFrame]:
        """Fetch historical price data using yfinance."""
        if yf is None:
            return None
        
        try:
            # Convert crypto format if needed (BTC/USD -> BTC-USD)
            yf_symbol = symbol.replace('/', '-')
            
            # Fetch data in executor (yfinance is synchronous)
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, yf_symbol)
            
            # Get historical data
            df = await loop.run_in_executor(
                None,
                lambda: ticker.history(period="1y", interval="1d")
            )
            
            if df.empty:
                return None
            
            return df.tail(bars)
            
        except Exception as e:
            logger.debug("price_data_fetch_failed", symbol=symbol, error=str(e))
            return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> Optional[float]:
        """Calculate RSI (Relative Strength Index)."""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
        except Exception:
            return None
    
    def _calculate_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> tuple:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        try:
            ema_fast = prices.ewm(span=fast, adjust=False).mean()
            ema_slow = prices.ewm(span=slow, adjust=False).mean()
            
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            histogram = macd_line - signal_line
            
            return (
                float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None,
                float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else None,
                float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else None
            )
        except Exception:
            return None, None, None
    
    def _calculate_bollinger(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2
    ) -> tuple:
        """Calculate Bollinger Bands."""
        try:
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            
            upper = sma + (std * std_dev)
            lower = sma - (std * std_dev)
            
            return (
                float(upper.iloc[-1]) if not pd.isna(upper.iloc[-1]) else None,
                float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else None,
                float(lower.iloc[-1]) if not pd.isna(lower.iloc[-1]) else None
            )
        except Exception:
            return None, None, None
    
    def _calculate_sma(self, series: pd.Series, period: int) -> Optional[float]:
        """Calculate Simple Moving Average (vectorized)."""
        try:
            if len(series) < period:
                return None
            sma = series.rolling(window=period).mean()
            return float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else None
        except Exception:
            return None

    def _calculate_vwap(self, df: pd.DataFrame) -> Optional[float]:
        """VWAP: volume-weighted average price (intraday/period context). Vectorized."""
        if pd is None or df is None or len(df) < 2:
            return None
        try:
            if ta is not None and 'High' in df.columns and 'Low' in df.columns and 'Volume' in df.columns:
                s = ta.vwap(df['High'], df['Low'], df['Close'], df['Volume'])
                if s is not None and len(s) > 0 and not pd.isna(s.iloc[-1]):
                    return float(s.iloc[-1])
            # Fallback: vectorized VWAP = sum(typical_price * volume) / sum(volume)
            typical = (df['High'] + df['Low'] + df['Close']) / 3.0
            cum_tpv = (typical * df['Volume']).cumsum()
            cum_vol = df['Volume'].cumsum()
            vwap_series = cum_tpv / cum_vol.replace(0, np.nan)
            if vwap_series.iloc[-1] and not pd.isna(vwap_series.iloc[-1]):
                return float(vwap_series.iloc[-1])
            return None
        except Exception:
            return None

    def _calculate_obv(self, df: pd.DataFrame) -> Optional[float]:
        """On-Balance Volume (volume flow). Vectorized."""
        if pd is None or df is None or len(df) < 2 or 'Volume' not in df.columns:
            return None
        try:
            if ta is not None:
                s = ta.obv(df['Close'], df['Volume'])
                if s is not None and len(s) > 0 and not pd.isna(s.iloc[-1]):
                    return float(s.iloc[-1])
            # Fallback: OBV = cumsum(sign(close.diff()) * volume)
            direction = np.sign(df['Close'].diff().fillna(0))
            obv = (direction * df['Volume']).cumsum()
            return float(obv.iloc[-1]) if not pd.isna(obv.iloc[-1]) else None
        except Exception:
            return None

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> Optional[float]:
        """ATR (Average True Range) for volatility. Vectorized."""
        if pd is None or df is None or len(df) < period + 1:
            return None
        try:
            if ta is not None and 'High' in df.columns and 'Low' in df.columns:
                s = ta.atr(df['High'], df['Low'], df['Close'], length=period)
                if s is not None and len(s) > 0 and not pd.isna(s.iloc[-1]):
                    return float(s.iloc[-1])
            # Fallback: TR = max(H-L, |H-prev_C|, |L-prev_C|), ATR = EMA(TR, period)
            high, low, close = df['High'], df['Low'], df['Close']
            prev_close = close.shift(1)
            tr = pd.concat([
                high - low,
                (high - prev_close).abs(),
                (low - prev_close).abs()
            ], axis=1).max(axis=1)
            atr = tr.ewm(span=period, adjust=False).mean()
            return float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else None
        except Exception:
            return None

    def clear_cache(self):
        """Clear the indicator cache."""
        self._cache.clear()
        self._cache_times.clear()
