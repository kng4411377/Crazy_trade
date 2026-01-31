"""
Gemini AI Analyzer - Batched trade signal analysis.

Sends batched prompts to Google's Gemini API (1 call per minute limit).
Provides trade signals with confidence scores for both stocks and crypto.
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import structlog

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from src.analysis.indicators import TechnicalIndicators, IndicatorResult

logger = structlog.get_logger()


@dataclass
class TradeSignal:
    """AI-generated trade signal for a symbol."""
    symbol: str
    timestamp: datetime
    
    # Signal
    action: str  # "BUY", "SELL", "HOLD", "WATCH"
    confidence: float  # 0.0 to 1.0
    
    # Context
    strategy: str  # "Wheel Strategy", "Day Trading", etc.
    reasoning: str
    
    # Price targets (optional)
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Risk assessment
    risk_level: str = "medium"  # "low", "medium", "high"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'action': self.action,
            'confidence': self.confidence,
            'strategy': self.strategy,
            'reasoning': self.reasoning,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'risk_level': self.risk_level
        }


class GeminiAnalyzer:
    """
    Gemini-powered trade signal analyzer.
    
    Features:
    - Batches all tickers into single API call (respects rate limits)
    - Calculates technical indicators locally
    - Supports different strategies for stocks vs crypto
    - Returns structured trade signals with confidence scores
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Gemini analyzer.
        
        Args:
            config: gemini section from config.yaml
        """
        self.config = config
        self.enabled = config.get('enabled', False)
        
        # API settings
        self.model_name = config.get('model', 'gemini-2.0-flash')
        self.call_interval = config.get('call_interval_seconds', 60)
        self.timeout = config.get('timeout_seconds', 30)
        
        # Data source toggles
        self.enable_stocks = config.get('enable_stocks', True)
        self.enable_crypto = config.get('enable_crypto', True)
        self.enable_news_analysis = config.get('enable_news_analysis', True)
        self.enable_tavily_fallback = config.get('enable_tavily_fallback', False)
        self._last_tavily_call_ts: Optional[datetime] = None
        self.tavily_interval_seconds = config.get('tavily_interval_seconds', 60)
        
        # Crypto watchlist (static)
        self.crypto_watchlist = config.get('crypto_watchlist', ['BTC/USD', 'ETH/USD', 'SOL/USD'])
        
        # Strategies
        self.strategies = config.get('strategies', {
            'stocks': 'Wheel Strategy',
            'crypto': 'Day Trading'
        })
        
        # Thresholds
        self.min_confidence = config.get('min_confidence', 0.6)
        
        # Prompt settings
        self.prompt_style = config.get('prompt_style', 'concise')
        self.include_price_history = config.get('include_price_history', True)
        
        # Logging
        self.log_prompts = config.get('log_prompts', False)
        self.log_responses = config.get('log_responses', True)
        
        # Technical indicators calculator
        self.indicators = TechnicalIndicators(config.get('indicators', {}))

        # Runtime override (e.g. low_power_mode from health_status.json)
        self._indicator_override: Optional[Dict[str, Any]] = None

        # State
        self._last_call_time: Optional[datetime] = None
        self._model = None
        self._initialized = False
        
        logger.info(
            "gemini_analyzer_created",
            enabled=self.enabled,
            model=self.model_name,
            enable_stocks=self.enable_stocks,
            enable_crypto=self.enable_crypto
        )
    
    async def initialize(self) -> bool:
        """
        Initialize the Gemini API client.
        
        Returns:
            True if successful
        """
        if not self.enabled:
            logger.info("gemini_analyzer_disabled")
            return True
        
        if genai is None:
            logger.error("google-generativeai package not installed")
            return False
        
        try:
            # Get API key from multiple sources (in order of priority)
            api_key = None
            
            # 1. Environment variable
            api_key = os.getenv('GEMINI_API_KEY')
            
            # 2. .env file
            if not api_key:
                try:
                    from dotenv import load_dotenv
                    load_dotenv()
                    api_key = os.getenv('GEMINI_API_KEY')
                except ImportError:
                    pass
            
            # 3. secrets.yaml
            if not api_key:
                try:
                    import yaml
                    with open('secrets.yaml', 'r') as f:
                        secrets = yaml.safe_load(f)
                    api_key = secrets.get('gemini', {}).get('api_key')
                except Exception:
                    pass
            
            if not api_key:
                logger.error("GEMINI_API_KEY not found in environment, .env, or secrets.yaml")
                return False
            
            # Configure Gemini
            genai.configure(api_key=api_key)
            
            # Initialize model
            self._model = genai.GenerativeModel(self.model_name)
            
            # Test connection with a simple prompt
            try:
                response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self._model.generate_content("Say 'OK' if you're ready.")
                    ),
                    timeout=10
                )
                
                if response and response.text:
                    self._initialized = True
                    logger.info("gemini_analyzer_initialized", model=self.model_name)
                    return True
                    
            except asyncio.TimeoutError:
                logger.error("gemini_initialization_timeout")
                return False
                
        except Exception as e:
            logger.error("gemini_initialization_failed", error=str(e))
            return False
        
        return False

    def set_indicator_override(self, override: Optional[Dict[str, Any]]) -> None:
        """
        Set runtime override for indicator config (e.g. low_power_mode).
        When set, only RSI runs; VWAP, OBV, ATR (and optionally MACD, Bollinger, SMA, volume) are disabled.
        Pass None to clear and use config.yaml again.
        """
        self._indicator_override = override
        self.indicators.set_override(override)

    async def analyze(
        self,
        stock_symbols: Optional[List[str]] = None,
        crypto_symbols: Optional[List[str]] = None,
        stock_market_open: bool = True,
    ) -> Dict[str, TradeSignal]:
        """
        Analyze symbols and return trade signals.
        
        Batches all symbols into a single API call.
        
        Args:
            stock_symbols: List of stock symbols (uses dynamic watchlist)
            crypto_symbols: List of crypto symbols (uses static list if None)
            stock_market_open: If False, Tavily fallback is skipped for stocks (only cryptos).
            
        Returns:
            Dict mapping symbol to TradeSignal
        """
        if not self.enabled or not self._initialized:
            return {}
        
        # Rate limiting
        if not await self._check_rate_limit():
            logger.debug("gemini_rate_limited")
            return {}
        
        signals = {}
        
        try:
            # Collect symbols to analyze
            all_symbols = []
            symbol_strategies = {}
            
            if self.enable_stocks and stock_symbols:
                for symbol in stock_symbols:
                    all_symbols.append(symbol)
                    symbol_strategies[symbol] = self.strategies.get('stocks', 'Wheel Strategy')
            
            if self.enable_crypto:
                crypto_list = crypto_symbols or self.crypto_watchlist
                for symbol in crypto_list:
                    all_symbols.append(symbol)
                    symbol_strategies[symbol] = self.strategies.get('crypto', 'Day Trading')
            
            if not all_symbols:
                logger.debug("no_symbols_to_analyze")
                return {}
            
            logger.info("gemini_analysis_starting", symbol_count=len(all_symbols))
            
            # Calculate indicators for all symbols
            indicator_results = await self.indicators.calculate_for_symbols(all_symbols)
            
            if not indicator_results:
                logger.warning("no_indicators_calculated")
                return {}
            
            # Fetch news cluster per symbol when enabled (sync call in executor; avoid timeouts)
            symbol_news_cluster: Dict[str, str] = {}
            if self.enable_news_analysis:
                from src.analysis.news_fetcher import get_news_cluster
                loop = asyncio.get_event_loop()
                for sym in all_symbols:
                    cluster = await loop.run_in_executor(None, lambda s=sym: get_news_cluster(s))
                    symbol_news_cluster[sym] = cluster
            
            # Build prompt
            prompt = self._build_prompt(indicator_results, symbol_strategies, symbol_news_cluster)
            
            if self.log_prompts:
                logger.debug("gemini_prompt", prompt=prompt[:500])
            
            # Call Gemini API
            response = await self._call_gemini(prompt)
            
            if not response:
                return {}
            
            # Parse response (all signals; we filter by min_confidence after Tavily step)
            all_signals = self._parse_response(response, symbol_strategies, include_all=True)
            
            # Tavily fallback only when Yahoo (yfinance) has NO news for that symbol.
            # - Stocks: only when stock market is open (no Tavily for stocks off-hours).
            # - Rate limit: at most 1 Tavily call per tavily_interval_seconds (default 60).
            if self.enable_tavily_fallback and all_signals:
                from src.analysis.tavily_research import get_tavily_context
                from src.analysis.news_fetcher import NO_NEWS_PLACEHOLDER
                loop = asyncio.get_event_loop()
                now = datetime.now()
                for sym, sig in list(all_signals.items()):
                    no_news = (symbol_news_cluster.get(sym) or "").strip() == NO_NEWS_PLACEHOLDER
                    if not no_news:
                        continue
                    is_crypto = "/" in sym
                    if not is_crypto and not stock_market_open:
                        logger.debug("tavily_skipped_stock_off_hours", symbol=sym)
                        continue
                    if self._last_tavily_call_ts is not None:
                        elapsed = (now - self._last_tavily_call_ts).total_seconds()
                        if elapsed < self.tavily_interval_seconds:
                            logger.debug("tavily_rate_limited", symbol=sym, elapsed=elapsed, interval=self.tavily_interval_seconds)
                            continue
                    try:
                        summary = await loop.run_in_executor(None, lambda s=sym: get_tavily_context(s))
                        self._last_tavily_call_ts = datetime.now()
                        if not summary:
                            continue
                        logger.info("Tavily Context", symbol=sym, tavily_context=summary[:500])
                        confirmed = await self._confirm_signal_with_tavily(sym, sig, summary, symbol_strategies.get(sym, "General"))
                        if confirmed:
                            all_signals[sym] = confirmed
                    except Exception as e:
                        logger.debug("tavily_fallback_error", symbol=sym, error=str(e))
            
            # Return only signals at or above min_confidence
            signals = {s: all_signals[s] for s in all_signals if all_signals[s].confidence >= self.min_confidence}
            
            logger.info(
                "gemini_analysis_complete",
                symbols_analyzed=len(indicator_results),
                signals_generated=len(signals)
            )
            
            return signals
            
        except Exception as e:
            logger.error("gemini_analysis_failed", error=str(e), exc_info=True)
            return {}
    
    async def _check_rate_limit(self) -> bool:
        """Check if we can make an API call (rate limiting)."""
        if self._last_call_time is None:
            return True
        
        elapsed = (datetime.now() - self._last_call_time).total_seconds()
        if elapsed < self.call_interval:
            return False
        
        return True
    
    def _build_prompt(
        self,
        indicators: Dict[str, IndicatorResult],
        strategies: Dict[str, str],
        symbol_news_cluster: Optional[Dict[str, str]] = None,
    ) -> str:
        """Build the batched analysis prompt."""
        if symbol_news_cluster is None:
            symbol_news_cluster = {}

        # Group by strategy
        strategy_groups = {}
        for symbol, result in indicators.items():
            strategy = strategies.get(symbol, 'General')
            if strategy not in strategy_groups:
                strategy_groups[strategy] = []
            strategy_groups[strategy].append(result)

        # System instruction: use News Context to validate technicals
        prompt_parts = [
            "You are a professional trading analyst. Analyze the following securities and provide trade signals.",
            "",
            "Use the News Context to validate the technical indicators. If technicals say BUY but news is overwhelmingly negative (e.g., bankruptcy, fraud, recall), override with HOLD or SELL.",
            "",
            "For each security, provide:",
            "1. ACTION: BUY, SELL, HOLD, or WATCH",
            "2. CONFIDENCE: 0.0 to 1.0 (how confident in the signal)",
            "3. REASONING: Brief explanation (1-2 sentences)",
            "4. RISK_LEVEL: low, medium, or high",
            "",
            "Respond in JSON format:",
            '{"signals": [{"symbol": "AAPL", "action": "BUY", "confidence": 0.75, "reasoning": "...", "risk_level": "medium"}, ...]}',
            "",
        ]

        for strategy, results in strategy_groups.items():
            prompt_parts.append(f"=== {strategy.upper()} ===")
            prompt_parts.append(f"Strategy Context: {strategy}")
            prompt_parts.append("")

            for result in results:
                prompt_parts.append(result.to_summary())
                news_context = symbol_news_cluster.get(result.symbol, "No recent news")
                prompt_parts.append("News Context: " + news_context)
                prompt_parts.append("")

        prompt_parts.append("Analyze all securities above and return JSON with signals for each.")

        return "\n".join(prompt_parts)
    
    async def _call_gemini(self, prompt: str) -> Optional[str]:
        """Make the API call to Gemini."""
        if not self._model:
            return None
        
        try:
            self._last_call_time = datetime.now()
            
            # Call in executor (synchronous SDK)
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._model.generate_content(prompt)
                ),
                timeout=self.timeout
            )
            
            if response and response.text:
                if self.log_responses:
                    logger.info("gemini_response_received", length=len(response.text))
                return response.text
            
            return None
            
        except asyncio.TimeoutError:
            logger.error("gemini_api_timeout")
            return None
        except Exception as e:
            logger.error("gemini_api_error", error=str(e))
            return None
    
    def _parse_response(
        self,
        response: str,
        strategies: Dict[str, str],
        include_all: bool = False,
    ) -> Dict[str, TradeSignal]:
        """Parse Gemini's JSON response into TradeSignals."""
        signals = {}
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning("no_json_in_response")
                return {}
            
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            for signal_data in data.get('signals', []):
                symbol = signal_data.get('symbol')
                if not symbol:
                    continue
                
                signal = TradeSignal(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    action=signal_data.get('action', 'HOLD').upper(),
                    confidence=float(signal_data.get('confidence', 0.5)),
                    strategy=strategies.get(symbol, 'Unknown'),
                    reasoning=signal_data.get('reasoning', ''),
                    risk_level=signal_data.get('risk_level', 'medium'),
                    entry_price=signal_data.get('entry_price'),
                    stop_loss=signal_data.get('stop_loss'),
                    take_profit=signal_data.get('take_profit')
                )
                
                if include_all or signal.confidence >= self.min_confidence:
                    signals[symbol] = signal
                    logger.debug(
                        "signal_parsed",
                        symbol=symbol,
                        action=signal.action,
                        confidence=signal.confidence
                    )
                else:
                    logger.debug(
                        "signal_below_threshold",
                        symbol=symbol,
                        confidence=signal.confidence,
                        threshold=self.min_confidence
                    )
            
        except json.JSONDecodeError as e:
            logger.error("json_parse_error", error=str(e), response_preview=response[:200])
        except Exception as e:
            logger.error("response_parse_error", error=str(e))
        
        return signals

    async def _confirm_signal_with_tavily(
        self,
        symbol: str,
        original: TradeSignal,
        tavily_summary: str,
        strategy: str,
    ) -> Optional[TradeSignal]:
        """
        Second Gemini call: confirm or override trade decision using Tavily context.
        Returns updated TradeSignal or None to keep original.
        """
        prompt = (
            "You are a trading analyst. Use the following Tavily research to confirm or override the original trade decision.\n\n"
            f"Tavily Context: {tavily_summary}\n\n"
            f"Original signal for {symbol}: {original.action} with confidence {original.confidence:.2f}. "
            f"Reasoning: {original.reasoning[:150]}\n\n"
            "If the research strongly contradicts the original (e.g., SEC investigation, fraud, recall), override with HOLD or SELL. "
            "Otherwise confirm the original action.\n\n"
            "Respond in JSON only: {\"action\": \"BUY\"|\"SELL\"|\"HOLD\"|\"WATCH\", \"confidence\": 0.0-1.0, \"reasoning\": \"brief reason\"}"
        )
        try:
            response = await self._call_gemini(prompt)
            if not response:
                return None
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start == -1 or json_end == 0:
                return None
            data = json.loads(response[json_start:json_end])
            action = (data.get("action") or original.action).upper()
            if action not in ("BUY", "SELL", "HOLD", "WATCH"):
                action = original.action
            confidence = float(data.get("confidence", original.confidence))
            reasoning = data.get("reasoning") or original.reasoning
            return TradeSignal(
                symbol=symbol,
                timestamp=datetime.now(),
                action=action,
                confidence=max(0.0, min(1.0, confidence)),
                strategy=strategy,
                reasoning=reasoning[:500],
                risk_level=original.risk_level,
                entry_price=original.entry_price,
                stop_loss=original.stop_loss,
                take_profit=original.take_profit,
            )
        except Exception as e:
            logger.debug("tavily_confirm_parse_error", symbol=symbol, error=str(e))
            return None
    
    def get_actionable_signals(
        self,
        signals: Dict[str, TradeSignal],
        action_filter: Optional[List[str]] = None
    ) -> List[TradeSignal]:
        """
        Get signals that are actionable (high confidence, specific action).
        
        Args:
            signals: Dict of signals from analyze()
            action_filter: Only return these actions (e.g., ["BUY", "SELL"])
            
        Returns:
            List of actionable signals sorted by confidence
        """
        action_filter = action_filter or ["BUY", "SELL"]
        
        actionable = [
            s for s in signals.values()
            if s.action in action_filter and s.confidence >= self.min_confidence
        ]
        
        # Sort by confidence (highest first)
        actionable.sort(key=lambda x: x.confidence, reverse=True)
        
        return actionable
    
    async def close(self):
        """Clean up resources."""
        self._model = None
        self._initialized = False
        self.indicators.clear_cache()
        logger.info("gemini_analyzer_closed")
