"""
Dynamic Watchlist Manager - Auto-discover and manage trending stocks.

Periodically scans for momentum signals and updates the active watchlist,
respecting position limits and account constraints.
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Set
import structlog

# File written by bot for API to read (same dir as api_server.py when cwd is project root)
WATCHLIST_STATE_FILE = "dynamic_watchlist.json"

from src.momentum.providers.yfinance_provider import YFinanceProvider
from src.momentum.providers.apewisdom import ApewisdomProvider
from src.momentum.factors.volume_anomaly import VolumeAnomalyFactor
from src.momentum.factors.reddit_attention import RedditAttentionFactor

logger = structlog.get_logger()


class DynamicWatchlistManager:
    """
    Manages a dynamic watchlist based on momentum signals.
    
    Features:
    - Auto-discovers trending stocks from Reddit/WSB
    - Scores stocks and filters by momentum threshold
    - Respects position limits (max positions, account value)
    - Periodic re-scanning to catch new opportunities
    - Removes stocks that lose momentum
    """
    
    def __init__(self, config: Dict, bot_config=None):
        """
        Initialize dynamic watchlist manager.
        
        Args:
            config: momentum_config.yaml['momentum_layer']['dynamic_watchlist']
            bot_config: Main bot config (for position limits)
        """
        self.config = config
        self.bot_config = bot_config
        self.enabled = config.get('enabled', False)
        
        # Scan settings
        self.update_interval = config.get('update_interval', 3600)
        self.scan_at_start = config.get('scan_at_start', True)
        
        # Discovery sources
        self.use_reddit_trending = config.get('use_reddit_trending', True)
        self.use_volume_movers = config.get('use_volume_movers', True)
        self.use_config_watchlist = config.get('use_config_watchlist', True)
        
        # Position limits
        self.max_positions = config.get('max_positions', 5)
        self.max_watchlist_size = config.get('max_watchlist_size', 20)
        
        # Scoring thresholds
        self.min_score_to_add = config.get('min_score_to_add', 0.5)
        self.min_score_to_keep = config.get('min_score_to_keep', 0.3)
        
        # Stock filters
        self.min_price = config.get('min_price', 5.0)
        self.max_price = config.get('max_price', 1000.0)
        self.min_volume = config.get('min_volume', 500000)
        self.exclude_otc = config.get('exclude_otc', True)
        
        # Always include / blacklist
        self.always_include = set(config.get('always_include', []))
        self.blacklist = set(config.get('blacklist', []))
        
        # Universe to scan
        self.universe = config.get('universe', [])
        
        # Providers and factors
        self.yf_provider: Optional[YFinanceProvider] = None
        self.apewisdom_provider: Optional[ApewisdomProvider] = None
        self.volume_factor: Optional[VolumeAnomalyFactor] = None
        self.reddit_factor: Optional[RedditAttentionFactor] = None
        
        # State
        self.active_watchlist: List[str] = []
        self.symbol_scores: Dict[str, Dict] = {}
        self.last_scan_time: Optional[datetime] = None
        self._initialized = False
        self._scan_task: Optional[asyncio.Task] = None
        
        logger.info(
            "dynamic_watchlist_manager_created",
            enabled=self.enabled,
            max_positions=self.max_positions,
            max_watchlist_size=self.max_watchlist_size,
            update_interval=self.update_interval
        )
    
    async def initialize(self) -> bool:
        """Initialize providers and factors."""
        if not self.enabled:
            logger.info("dynamic_watchlist_disabled")
            return True
        
        try:
            logger.info("dynamic_watchlist_initializing")
            
            # Initialize YFinance
            self.yf_provider = YFinanceProvider({})
            await self.yf_provider.initialize()
            
            if not self.yf_provider.is_available():
                logger.error("dynamic_watchlist_yfinance_unavailable")
                return False
            
            # Initialize Apewisdom
            self.apewisdom_provider = ApewisdomProvider({})
            await self.apewisdom_provider.initialize()
            
            # Create factors
            self.volume_factor = VolumeAnomalyFactor(
                [self.yf_provider],
                {'weight': 0.5}
            )
            
            self.reddit_factor = RedditAttentionFactor(
                [self.apewisdom_provider],
                {'weight': 0.5, 'mention_threshold': 10}
            )
            
            self._initialized = True
            
            logger.info(
                "dynamic_watchlist_initialized",
                yfinance=self.yf_provider.is_available(),
                apewisdom=self.apewisdom_provider.is_available()
            )
            
            # Run initial scan if configured
            if self.scan_at_start:
                await self.scan_and_update()
            
            return True
            
        except Exception as e:
            logger.error("dynamic_watchlist_init_error", error=str(e), exc_info=True)
            return False
    
    async def start_background_scanning(self):
        """Start background task for periodic scanning."""
        if not self.enabled or not self._initialized:
            return
        
        async def scan_loop():
            while True:
                try:
                    await asyncio.sleep(self.update_interval)
                    await self.scan_and_update()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("dynamic_watchlist_scan_error", error=str(e))
                    await asyncio.sleep(60)  # Wait a minute before retry
        
        self._scan_task = asyncio.create_task(scan_loop())
        logger.info("dynamic_watchlist_background_scanning_started", interval=self.update_interval)
    
    async def stop_background_scanning(self):
        """Stop background scanning task."""
        if self._scan_task:
            self._scan_task.cancel()
            try:
                await self._scan_task
            except asyncio.CancelledError:
                pass
            self._scan_task = None
            logger.info("dynamic_watchlist_background_scanning_stopped")
    
    async def scan_and_update(
        self,
        current_positions: Optional[Dict[str, float]] = None,
        account_value: Optional[float] = None
    ) -> List[str]:
        """
        Scan for momentum and update watchlist.
        
        Args:
            current_positions: Dict of symbol -> position value (USD)
            account_value: Total account value
            
        Returns:
            Updated active watchlist
        """
        if not self._initialized:
            logger.warning("dynamic_watchlist_not_initialized")
            return self.active_watchlist
        
        logger.info("dynamic_watchlist_scan_starting")
        
        # Step 1: Build universe to scan
        universe = await self._build_universe()
        logger.info("dynamic_watchlist_universe_built", size=len(universe))
        
        # Step 2: Score all symbols
        scored_symbols = await self._score_universe(universe)
        logger.info("dynamic_watchlist_scored", count=len(scored_symbols))
        
        # Step 3: Filter and rank
        ranked = self._filter_and_rank(scored_symbols, current_positions, account_value)
        
        # Step 4: Update active watchlist
        old_watchlist = set(self.active_watchlist)
        new_watchlist = [s['symbol'] for s in ranked[:self.max_watchlist_size]]
        
        # Always include specified symbols
        for symbol in self.always_include:
            if symbol not in new_watchlist and symbol not in self.blacklist:
                new_watchlist.append(symbol)
        
        self.active_watchlist = new_watchlist
        self.last_scan_time = datetime.now()
        
        # Log changes
        added = set(new_watchlist) - old_watchlist
        removed = old_watchlist - set(new_watchlist)
        
        logger.info(
            "dynamic_watchlist_updated",
            watchlist=new_watchlist,
            added=list(added),
            removed=list(removed),
            total=len(new_watchlist)
        )
        self._persist_watchlist()
        return self.active_watchlist

    def _persist_watchlist(self) -> None:
        """Write current watchlist to a JSON file so the API can serve GET /watchlist."""
        try:
            path = Path.cwd() / WATCHLIST_STATE_FILE
            data = {
                "symbols": self.active_watchlist,
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "source": "dynamic",
            }
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            logger.debug("dynamic_watchlist_persisted", path=str(path), count=len(self.active_watchlist))
        except Exception as e:
            logger.warning("dynamic_watchlist_persist_failed", error=str(e))
    
    async def _build_universe(self) -> List[str]:
        """Build the universe of symbols to scan."""
        universe = set()
        
        # Add configured universe
        universe.update(self.universe)
        
        # Add Reddit trending stocks
        if self.use_reddit_trending and self.apewisdom_provider and self.apewisdom_provider.is_available():
            try:
                trending = await self.apewisdom_provider.get_trending_stocks(limit=30)
                for stock in trending:
                    symbol = stock.get('symbol', '')
                    if symbol:
                        universe.add(symbol)
                logger.debug("dynamic_watchlist_reddit_trending_added", count=len(trending))
            except Exception as e:
                logger.warning("dynamic_watchlist_reddit_fetch_error", error=str(e))
        
        # Remove blacklisted symbols
        universe -= self.blacklist
        
        return list(universe)
    
    async def _score_universe(self, universe: List[str]) -> List[Dict]:
        """Score all symbols in the universe."""
        scored = []
        
        for symbol in universe:
            try:
                # Get scores
                volume_score = await self.volume_factor.calculate_score(symbol)
                reddit_score = None
                if self.apewisdom_provider and self.apewisdom_provider.is_available():
                    reddit_score = await self.reddit_factor.calculate_score(symbol)
                
                # Calculate composite
                v_score = volume_score.score if volume_score else 0.0
                r_score = reddit_score.score if reddit_score else 0.0
                
                # Use MAX to catch any strong signal
                composite = max(v_score, r_score)
                
                if composite > 0:
                    scored.append({
                        'symbol': symbol,
                        'composite': composite,
                        'volume_score': v_score,
                        'reddit_score': r_score,
                        'volume_data': volume_score.metadata if volume_score else None,
                        'reddit_data': reddit_score.metadata if reddit_score else None
                    })
                    
                    # Cache score
                    self.symbol_scores[symbol] = {
                        'composite': composite,
                        'volume_score': v_score,
                        'reddit_score': r_score,
                        'timestamp': datetime.now()
                    }
                    
            except Exception as e:
                logger.debug("dynamic_watchlist_score_error", symbol=symbol, error=str(e))
        
        return scored
    
    def _filter_and_rank(
        self,
        scored_symbols: List[Dict],
        current_positions: Optional[Dict[str, float]] = None,
        account_value: Optional[float] = None
    ) -> List[Dict]:
        """Filter by thresholds and rank by score."""
        
        # Filter by minimum score
        filtered = [s for s in scored_symbols if s['composite'] >= self.min_score_to_add]
        
        # Sort by composite score (highest first)
        filtered.sort(key=lambda x: x['composite'], reverse=True)
        
        # Respect max positions
        max_new_positions = self.max_positions
        if current_positions:
            current_count = len(current_positions)
            max_new_positions = max(0, self.max_positions - current_count)
        
        # Limit to available slots + buffer for watchlist
        # Allow more in watchlist than max_positions to have options
        buffer = min(10, self.max_watchlist_size - self.max_positions)
        max_symbols = max_new_positions + buffer
        
        return filtered[:max_symbols]
    
    def get_watchlist(self) -> List[str]:
        """Get current active watchlist."""
        return self.active_watchlist.copy()
    
    def get_symbol_score(self, symbol: str) -> Optional[Dict]:
        """Get cached score for a symbol."""
        return self.symbol_scores.get(symbol)
    
    def should_trade_symbol(
        self,
        symbol: str,
        current_positions: Optional[Dict[str, float]] = None
    ) -> bool:
        """
        Check if we should trade a symbol based on momentum and limits.
        
        Args:
            symbol: Stock symbol
            current_positions: Current open positions
            
        Returns:
            True if symbol should be traded
        """
        # Check blacklist
        if symbol in self.blacklist:
            logger.debug("dynamic_watchlist_symbol_blacklisted", symbol=symbol)
            return False
        
        # Check if in active watchlist (or always include)
        if symbol not in self.active_watchlist and symbol not in self.always_include:
            logger.debug("dynamic_watchlist_symbol_not_in_watchlist", symbol=symbol)
            return False
        
        # Check position count
        if current_positions:
            if len(current_positions) >= self.max_positions:
                logger.debug(
                    "dynamic_watchlist_max_positions_reached",
                    symbol=symbol,
                    current=len(current_positions),
                    max=self.max_positions
                )
                return False
            
            # Already have position in this symbol
            if symbol in current_positions:
                return True  # Can still manage existing position
        
        # Check momentum score
        score_data = self.symbol_scores.get(symbol)
        if score_data:
            if score_data['composite'] < self.min_score_to_keep:
                logger.debug(
                    "dynamic_watchlist_low_momentum",
                    symbol=symbol,
                    score=score_data['composite'],
                    threshold=self.min_score_to_keep
                )
                return False
        
        return True
    
    def add_symbol(self, symbol: str) -> bool:
        """Manually add a symbol to watchlist."""
        if symbol in self.blacklist:
            return False
        
        if symbol not in self.active_watchlist:
            self.active_watchlist.append(symbol)
            logger.info("dynamic_watchlist_symbol_added", symbol=symbol)
        return True
    
    def remove_symbol(self, symbol: str) -> bool:
        """Remove a symbol from watchlist."""
        if symbol in self.active_watchlist:
            self.active_watchlist.remove(symbol)
            logger.info("dynamic_watchlist_symbol_removed", symbol=symbol)
            return True
        return False
    
    def get_stats(self) -> Dict:
        """Get statistics about the dynamic watchlist."""
        return {
            'enabled': self.enabled,
            'initialized': self._initialized,
            'watchlist_size': len(self.active_watchlist),
            'max_positions': self.max_positions,
            'max_watchlist_size': self.max_watchlist_size,
            'last_scan': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'update_interval': self.update_interval,
            'scored_symbols': len(self.symbol_scores),
            'watchlist': self.active_watchlist,
            'always_include': list(self.always_include),
            'blacklist': list(self.blacklist)
        }
    
    async def close(self):
        """Clean up resources."""
        await self.stop_background_scanning()
        
        if self.yf_provider:
            await self.yf_provider.close()
        if self.apewisdom_provider:
            await self.apewisdom_provider.close()
        
        logger.info("dynamic_watchlist_closed")
