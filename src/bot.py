"""Main bot orchestrator."""

import asyncio
from datetime import datetime
from typing import Dict, Optional, List
import signal
import sys
import structlog
import yaml
from pathlib import Path

from alpaca.trading.enums import OrderType

from src.config import BotConfig
from src.database import DatabaseManager
from src.alpaca_client import AlpacaClient, AlpacaOrder
from src.market_hours import MarketHoursChecker
from src.sizing import PositionSizer
from src.state_machine import SymbolStateMachine
from src.performance import PerformanceTracker

logger = structlog.get_logger()


class TradingBot:
    """Main trading bot orchestrator."""

    def __init__(self, config: BotConfig):
        """Initialize trading bot."""
        self.config = config
        self.running = False
        
        # Initialize components
        self.db = DatabaseManager(config.persistence.db_url)
        self.db.create_tables()
        
        self.alpaca = AlpacaClient(config)
        self.market_hours = MarketHoursChecker(
            config.hours.calendar,
            config.hours.allow_pre_market,
            config.hours.allow_after_hours,
            config.hours.skip_first_minutes,
            config.hours.skip_last_minutes,
        )
        self.sizer = PositionSizer(config)
        
        # State machines for each symbol (stocks + crypto)
        self.state_machines: Dict[str, SymbolStateMachine] = {}
        all_symbols = config.get_all_symbols()
        for symbol in all_symbols:
            self.state_machines[symbol] = SymbolStateMachine(
                symbol, config, self.alpaca, self.db, self.sizer
            )
        
        # Momentum filter (hybrid integration)
        self.momentum_filter = None
        self.momentum_filter_config = self._load_momentum_filter_config()
        self.dynamic_watchlist_config = self._load_dynamic_watchlist_config()
        self.dynamic_watchlist_manager = None
        self.active_symbols: List[str] = all_symbols  # Will be filtered at start()
        
        # Performance tracker
        self.performance = PerformanceTracker(self.db, self.alpaca)
        
        # Register event handlers
        self.alpaca.register_fill_callback(self._on_fill)
        self.alpaca.register_order_status_callback(self._on_order_status)
        
        # Track last event check time
        self.last_event_check = datetime.min
        
        # Track last operation times
        self.last_price_check = datetime.min
        self.last_order_check = datetime.min
        self.last_eod_cancel = None
        self.last_snapshot_date = None
        self.last_keepalive = datetime.min
        
        logger.info(
            "trading_bot_initialized",
            mode=config.mode,
            stock_watchlist=config.watchlist,
            crypto_watchlist=config.crypto_watchlist,
            num_stocks=len(config.watchlist),
            num_crypto=len(config.crypto_watchlist),
            total_symbols=len(all_symbols),
        )

    async def start(self):
        """Start the trading bot."""
        logger.info("starting_trading_bot")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Connect to Alpaca
        await self.alpaca.connect()
        
        # Initialize and apply momentum filter
        await self._initialize_momentum_filter()
        
        # Initialize dynamic watchlist (if enabled)
        await self._initialize_dynamic_watchlist()
        
        self.running = True
        
        # Log initial state
        dw_enabled = self.dynamic_watchlist_config.get('enabled', False) if self.dynamic_watchlist_config else False
        with self.db.get_session() as session:
            self.db.add_event(
                session,
                event_type="bot_started",
                payload={
                    "mode": self.config.mode,
                    "stock_watchlist": self.config.watchlist,
                    "crypto_watchlist": self.config.crypto_watchlist,
                    "active_symbols": self.active_symbols,
                    "momentum_filter_enabled": self.momentum_filter_config.get('enabled', False) if self.momentum_filter_config else False,
                    "dynamic_watchlist_enabled": dw_enabled,
                },
            )
        
        # Main event loop
        try:
            await self._run_loop()
        except Exception as e:
            logger.error("bot_error", error=str(e), exc_info=True)
            raise
        finally:
            await self.stop()

    async def stop(self):
        """Stop the trading bot."""
        logger.info("stopping_trading_bot")
        self.running = False
        
        await self.alpaca.disconnect()
        
        # Clean up momentum filter
        if self.momentum_filter:
            try:
                await self.momentum_filter.close()
            except Exception as e:
                logger.error("momentum_filter_close_error", error=str(e))
        
        # Clean up dynamic watchlist manager
        if self.dynamic_watchlist_manager:
            try:
                await self.dynamic_watchlist_manager.close()
            except Exception as e:
                logger.error("dynamic_watchlist_close_error", error=str(e))
        
        with self.db.get_session() as session:
            self.db.add_event(session, event_type="bot_stopped")
        
        logger.info("trading_bot_stopped")

    def _load_momentum_filter_config(self) -> Optional[Dict]:
        """Load momentum filter configuration from config.yaml."""
        try:
            # Try main config.yaml first (unified config)
            config_path = Path("config.yaml")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                # Check for unified config structure (momentum.filter)
                filter_config = config.get('momentum', {}).get('filter', {})
                if filter_config:
                    logger.info(
                        "momentum_filter_config_loaded",
                        source="config.yaml",
                        enabled=filter_config.get('enabled', False),
                        min_score=filter_config.get('min_score', 0),
                    )
                    return filter_config
            
            # Fallback: Try legacy momentum_config.yaml
            legacy_path = Path("momentum_config.yaml")
            if legacy_path.exists():
                with open(legacy_path, 'r') as f:
                    momentum_config = yaml.safe_load(f)
                
                filter_config = momentum_config.get('momentum_layer', {}).get('filter', {})
                if filter_config:
                    logger.info(
                        "momentum_filter_config_loaded",
                        source="momentum_config.yaml (legacy)",
                        enabled=filter_config.get('enabled', False),
                        min_score=filter_config.get('min_score', 0),
                    )
                    return filter_config
            
            logger.info("momentum_filter_config_not_found")
            return None
            
        except Exception as e:
            logger.error("momentum_filter_config_load_error", error=str(e))
            return None
    
    def _load_dynamic_watchlist_config(self) -> Optional[Dict]:
        """Load dynamic watchlist configuration from config.yaml."""
        try:
            # Try main config.yaml first (unified config)
            config_path = Path("config.yaml")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                # Check for unified config structure (momentum.dynamic_watchlist)
                dw_config = config.get('momentum', {}).get('dynamic_watchlist', {})
                if dw_config:
                    logger.info(
                        "dynamic_watchlist_config_loaded",
                        source="config.yaml",
                        enabled=dw_config.get('enabled', False),
                        max_positions=dw_config.get('max_positions', 5),
                        update_interval=dw_config.get('update_interval', 3600),
                    )
                    return dw_config
            
            # Fallback: Try legacy momentum_config.yaml
            legacy_path = Path("momentum_config.yaml")
            if legacy_path.exists():
                with open(legacy_path, 'r') as f:
                    momentum_config = yaml.safe_load(f)
                
                dw_config = momentum_config.get('momentum_layer', {}).get('dynamic_watchlist', {})
                if dw_config:
                    logger.info(
                        "dynamic_watchlist_config_loaded",
                        source="momentum_config.yaml (legacy)",
                        enabled=dw_config.get('enabled', False),
                        max_positions=dw_config.get('max_positions', 5),
                        update_interval=dw_config.get('update_interval', 3600),
                    )
                    return dw_config
            
            logger.info("dynamic_watchlist_config_not_found")
            return None
            
        except Exception as e:
            logger.error("dynamic_watchlist_config_load_error", error=str(e))
            return None
    
    async def _initialize_momentum_filter(self):
        """Initialize momentum filter and apply to watchlist."""
        if not self.momentum_filter_config or not self.momentum_filter_config.get('enabled', False):
            logger.info("momentum_filter_disabled", active_symbols=len(self.active_symbols))
            return
        
        try:
            # Import here to avoid circular dependency
            from src.momentum.filter import MomentumFilter
            
            logger.info("momentum_filter_initializing")
            
            # Create filter
            self.momentum_filter = MomentumFilter(self.momentum_filter_config)
            
            # Initialize (async)
            success = await self.momentum_filter.initialize()
            
            if not success:
                logger.error("momentum_filter_init_failed")
                self.momentum_filter = None
                return
            
            # Filter stocks only (keep crypto untouched)
            stock_symbols = self.config.watchlist
            crypto_symbols = self.config.crypto_watchlist
            
            if stock_symbols:
                logger.info("momentum_filter_applying", stock_count=len(stock_symbols))
                
                filtered_stocks = await self.momentum_filter.filter_symbols(stock_symbols)
                
                # Update active symbols
                self.active_symbols = filtered_stocks + crypto_symbols
                
                filtered_out = [s for s in stock_symbols if s not in filtered_stocks]
                
                logger.info(
                    "momentum_filter_applied",
                    original_stocks=len(stock_symbols),
                    filtered_stocks=len(filtered_stocks),
                    crypto_count=len(crypto_symbols),
                    total_active=len(self.active_symbols),
                    filtered_out=filtered_out
                )
                
                # Log to database
                with self.db.get_session() as session:
                    self.db.add_event(
                        session,
                        event_type="momentum_filter_applied",
                        payload={
                            "original_stocks": stock_symbols,
                            "filtered_stocks": filtered_stocks,
                            "filtered_out": filtered_out,
                            "filter_config": self.momentum_filter_config
                        }
                    )
            else:
                logger.info("momentum_filter_no_stocks")
                
        except ImportError as e:
            logger.error("momentum_filter_import_error", error=str(e))
            self.momentum_filter = None
        except Exception as e:
            logger.error("momentum_filter_error", error=str(e), exc_info=True)
            self.momentum_filter = None
    
    async def _initialize_dynamic_watchlist(self):
        """Initialize dynamic watchlist manager for auto-discovery."""
        if not self.dynamic_watchlist_config or not self.dynamic_watchlist_config.get('enabled', False):
            logger.info("dynamic_watchlist_disabled")
            return
        
        try:
            # Import here to avoid circular dependency
            from src.momentum.dynamic_watchlist import DynamicWatchlistManager
            
            logger.info("dynamic_watchlist_initializing")
            
            # Create manager with bot config for position limits
            self.dynamic_watchlist_manager = DynamicWatchlistManager(
                self.dynamic_watchlist_config,
                bot_config=self.config
            )
            
            # Get current positions for context
            positions = await self.alpaca.get_positions()
            current_positions = {p.symbol: float(p.market_value) for p in positions}
            account = await self.alpaca.get_account()
            account_value = float(account.equity)
            
            # Initialize (this runs first scan if scan_at_start=True)
            success = await self.dynamic_watchlist_manager.initialize()
            
            if not success:
                logger.error("dynamic_watchlist_init_failed")
                self.dynamic_watchlist_manager = None
                return
            
            # Run initial scan with position context
            await self.dynamic_watchlist_manager.scan_and_update(
                current_positions=current_positions,
                account_value=account_value
            )
            
            # Get the dynamic watchlist and merge with active symbols
            dynamic_symbols = self.dynamic_watchlist_manager.get_watchlist()
            
            # Merge: active_symbols + dynamic (remove duplicates)
            combined = list(self.active_symbols)
            for symbol in dynamic_symbols:
                if symbol not in combined:
                    combined.append(symbol)
            
            # Respect max positions from dynamic watchlist config
            max_watchlist = self.dynamic_watchlist_config.get('max_watchlist_size', 20)
            self.active_symbols = combined[:max_watchlist]
            
            # Create state machines for any new symbols
            for symbol in self.active_symbols:
                if symbol not in self.state_machines:
                    self.state_machines[symbol] = SymbolStateMachine(
                        symbol, self.config, self.alpaca, self.db, self.sizer
                    )
            
            # Start background scanning
            await self.dynamic_watchlist_manager.start_background_scanning()
            
            logger.info(
                "dynamic_watchlist_initialized",
                dynamic_symbols=dynamic_symbols,
                active_symbols=self.active_symbols,
                total=len(self.active_symbols)
            )
            
            # Log to database
            with self.db.get_session() as session:
                self.db.add_event(
                    session,
                    event_type="dynamic_watchlist_initialized",
                    payload={
                        "dynamic_symbols": dynamic_symbols,
                        "active_symbols": self.active_symbols,
                        "config": self.dynamic_watchlist_config
                    }
                )
                
        except ImportError as e:
            logger.error("dynamic_watchlist_import_error", error=str(e))
            self.dynamic_watchlist_manager = None
        except Exception as e:
            logger.error("dynamic_watchlist_error", error=str(e), exc_info=True)
            self.dynamic_watchlist_manager = None

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("shutdown_signal_received", signal=signum)
        self.running = False

    async def _run_loop(self):
        """Main event loop."""
        logger.info("entering_main_loop")
        
        while self.running:
            try:
                # Check if we're in acceptable trading window (for stocks)
                # This excludes first/last minutes if configured
                in_trading_window = self.market_hours.is_in_trading_window()
                has_crypto = len(self.config.crypto_watchlist) > 0
                
                # Process crypto always (24/7) or stocks during trading window
                if in_trading_window or has_crypto:
                    await self._process_trading_logic(in_rth=in_trading_window)
                else:
                    logger.debug("outside_trading_window_no_crypto")
                    # Keep connection alive even when market is closed
                    await self._keepalive_tick()
                    await asyncio.sleep(60)  # Check every minute when market is closed
                    continue
                
                # Handle end-of-day cancellations
                await self._handle_eod_cancellations()
                
                # Take daily performance snapshot
                await self._take_daily_snapshot()
                
                # Check for order events (Alpaca REST polling)
                await self._check_order_events()
                
                # Keep-alive ping to prevent connection timeout
                await self._keepalive_tick()
                
                # Sleep based on polling interval
                await asyncio.sleep(self.config.polling.orders_seconds)
                
            except Exception as e:
                logger.error("loop_iteration_error", error=str(e), exc_info=True)
                await asyncio.sleep(10)  # Brief pause on error
        
        logger.info("exiting_main_loop")

    async def _process_trading_logic(self, in_rth: bool = True):
        """Process trading logic for all symbols.
        
        Args:
            in_rth: Whether we're in regular trading hours (affects stock trading)
        """
        # Check daily drawdown limit (circuit breaker)
        if not self._check_daily_drawdown_ok():
            logger.warning("daily_drawdown_limit_breached_skipping_new_entries")
            return
        
        # Get current positions and account value
        positions = self.alpaca.get_positions()
        account_value = self.alpaca.get_account_value()
        
        # Calculate current exposures
        position_values = {
            symbol: pos["market_value"] 
            for symbol, pos in positions.items()
        }
        
        exposure_metrics = self.sizer.get_current_exposure(position_values)
        logger.debug("exposure_metrics", **exposure_metrics)
        
        # Check if we can add new positions
        can_add_position = self._check_position_limit_ok(positions)
        
        # Process each ACTIVE symbol (filtered by momentum)
        for symbol in self.active_symbols:
            sm = self.state_machines.get(symbol)
            if not sm:
                continue  # Symbol not in state machines
            
            try:
                # Skip stocks if market is closed
                is_crypto = self.config.is_crypto_symbol(symbol)
                if not is_crypto and not in_rth:
                    logger.debug("skipping_stock_outside_rth", symbol=symbol)
                    continue
                
                # Check if we're at position limit before allowing new entries
                if not can_add_position and symbol not in positions:
                    logger.debug("skipping_new_entry_at_position_limit", symbol=symbol)
                    continue
                
                await sm.process(position_values, account_value)
            except Exception as e:
                logger.error(
                    "symbol_processing_error",
                    symbol=symbol,
                    error=str(e),
                    exc_info=True,
                )

    async def _handle_eod_cancellations(self):
        """Handle end-of-day order cancellations (stocks only, not crypto)."""
        if not self.config.entries.cancel_at_close:
            return
        
        # Check if we're near market close (within 15 minutes)
        seconds_to_close = self.market_hours.seconds_until_market_close()
        
        if 0 < seconds_to_close <= 900:  # 15 minutes
            # Check if we've already done this today
            today = datetime.utcnow().date()
            if self.last_eod_cancel != today:
                logger.info("cancelling_unfilled_stock_entries_eod")
                
                # Only cancel stock orders, not crypto (crypto trades 24/7)
                for symbol, sm in self.state_machines.items():
                    if not self.config.is_crypto_symbol(symbol):
                        await sm.cancel_unfilled_entries()
                
                self.last_eod_cancel = today
                
                with self.db.get_session() as session:
                    self.db.add_event(
                        session,
                        event_type="eod_stock_cancellations_completed",
                    )

    async def _check_order_events(self):
        """Check for order updates and fills (Alpaca REST polling)."""
        now = datetime.utcnow()
        
        # Check for events based on configured interval
        interval = self.config.polling.event_check_seconds
        if (now - self.last_event_check).total_seconds() >= interval:
            await self.alpaca.check_for_events()
            self.last_event_check = now

    async def _keepalive_tick(self):
        """Send periodic keep-alive to Alpaca to prevent timeout."""
        now = datetime.utcnow()
        
        # Send keep-alive based on configured interval
        interval = self.config.polling.keepalive_seconds
        if (now - self.last_keepalive).total_seconds() >= interval:
            await self.alpaca.keep_alive()
            self.last_keepalive = now

    async def _take_daily_snapshot(self):
        """Take daily performance snapshot."""
        today = datetime.utcnow().date()
        
        # Only snapshot once per day
        if self.last_snapshot_date == today:
            return
        
        try:
            # Get account summary
            account_summary = self.performance.get_account_summary()
            positions = self.alpaca.get_positions()
            
            if not account_summary:
                return
            
            with self.db.get_session() as session:
                # Get trade count for today
                from src.database import FillRecord
                today_start = datetime.combine(today, datetime.min.time())
                trades_today = (
                    session.query(FillRecord)
                    .filter(FillRecord.ts >= today_start)
                    .count()
                )
                
                # Save snapshot
                self.db.add_performance_snapshot(
                    session,
                    date=datetime.utcnow(),
                    account_value=account_summary.get('NetLiquidation'),
                    cash_value=account_summary.get('TotalCashValue'),
                    position_value=account_summary.get('GrossPositionValue'),
                    unrealized_pnl=account_summary.get('UnrealizedPnL'),
                    realized_pnl=account_summary.get('RealizedPnL'),
                    num_positions=len(positions),
                    num_trades=trades_today,
                )
            
            self.last_snapshot_date = today
            logger.info("daily_snapshot_saved", date=today)
            
        except Exception as e:
            logger.error("failed_to_save_snapshot", error=str(e))

    def _check_daily_drawdown_ok(self) -> bool:
        """
        Check if daily drawdown limits are within acceptable range.
        
        Circuit breaker: Stops new entries if daily loss exceeds threshold.
        
        Returns:
            True if ok to trade, False if limit breached
        """
        # If no limits configured, always allow
        if (self.config.risk.max_daily_loss_pct is None and 
            self.config.risk.max_daily_loss_usd is None):
            return True
        
        # Get today's P&L
        try:
            account_summary = self.performance.get_account_summary()
            if not account_summary:
                # Can't get account data, allow trading (fail open)
                return True
            
            # Calculate today's P&L
            # Note: This is a simplified version - you might want to track daily starting balance
            daily_pnl = account_summary.get('DailyPnL', 0)  # If Alpaca provides this
            # Fallback: use unrealized + realized PnL (approximate)
            if daily_pnl == 0:
                daily_pnl = (account_summary.get('UnrealizedPnL', 0) + 
                            account_summary.get('RealizedPnL', 0))
            
            account_value = account_summary.get('NetLiquidation', 0)
            
            # Check percentage limit
            if self.config.risk.max_daily_loss_pct is not None and account_value > 0:
                daily_loss_pct = (daily_pnl / account_value) * 100
                if daily_loss_pct < -self.config.risk.max_daily_loss_pct:
                    logger.error(
                        "daily_loss_pct_limit_breached",
                        daily_loss_pct=daily_loss_pct,
                        limit=self.config.risk.max_daily_loss_pct,
                        daily_pnl=daily_pnl,
                        alert="CIRCUIT BREAKER: Stopping new entries"
                    )
                    return False
            
            # Check dollar limit
            if self.config.risk.max_daily_loss_usd is not None:
                if daily_pnl < -self.config.risk.max_daily_loss_usd:
                    logger.error(
                        "daily_loss_usd_limit_breached",
                        daily_pnl=daily_pnl,
                        limit=self.config.risk.max_daily_loss_usd,
                        alert="CIRCUIT BREAKER: Stopping new entries"
                    )
                    return False
            
            return True
            
        except Exception as e:
            logger.error("failed_to_check_daily_drawdown", error=str(e))
            return True  # Fail open - allow trading if can't check
    
    def _check_position_limit_ok(self, positions: dict) -> bool:
        """
        Check if we're within concurrent position limits.
        
        Args:
            positions: Current positions dict
            
        Returns:
            True if ok to add new position, False if limit reached
        """
        if self.config.risk.max_concurrent_positions is None:
            return True
        
        current_count = len(positions)
        if current_count >= self.config.risk.max_concurrent_positions:
            logger.warning(
                "max_concurrent_positions_reached",
                current=current_count,
                limit=self.config.risk.max_concurrent_positions
            )
            return False
        
        return True

    async def _place_trailing_stop_with_retry(self, symbol: str, qty: int, entry_price: float):
        """
        Place trailing stop with retry logic to ensure it gets placed.
        
        This is critical - if the trailing stop doesn't get placed, the position has no protection!
        
        Args:
            symbol: Symbol to place trailing stop for
            qty: Position quantity
            entry_price: Entry fill price
        """
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    "placing_trailing_stop_attempt",
                    symbol=symbol,
                    qty=qty,
                    attempt=attempt,
                    max_retries=max_retries
                )
                
                # Place the trailing stop
                success = await self.state_machines[symbol].place_trailing_stop_after_entry(qty, entry_price)
                
                if success is not False:  # None or True means success
                    logger.info(
                        "trailing_stop_placed_successfully",
                        symbol=symbol,
                        qty=qty,
                        attempt=attempt
                    )
                    return True
                else:
                    logger.warning(
                        "trailing_stop_placement_returned_false",
                        symbol=symbol,
                        attempt=attempt
                    )
                    
            except Exception as e:
                logger.error(
                    "trailing_stop_placement_attempt_failed",
                    symbol=symbol,
                    qty=qty,
                    attempt=attempt,
                    error=str(e),
                    exc_info=True
                )
            
            # Wait before retry (unless it's the last attempt)
            if attempt < max_retries:
                logger.info("waiting_before_retry", symbol=symbol, delay_seconds=retry_delay)
                await asyncio.sleep(retry_delay)
        
        # All retries failed - log critical error
        logger.critical(
            "trailing_stop_placement_failed_all_retries",
            symbol=symbol,
            qty=qty,
            max_retries=max_retries,
            alert="POSITION WITHOUT PROTECTION!"
        )
        
        # Record critical event
        with self.db.get_session() as session:
            self.db.add_event(
                session,
                event_type="trailing_stop_placement_failed",
                symbol=symbol,
                payload={
                    "qty": qty,
                    "entry_price": entry_price,
                    "max_retries": max_retries,
                    "alert": "Position opened without trailing stop protection!"
                }
            )
        
        return False

    def _on_fill(self, order_wrapper: AlpacaOrder, fill):
        """Handle fill events."""
        symbol = order_wrapper.contract.symbol
        exec_id = str(fill.execution.execId)  # Convert to string for consistency
        
        order = order_wrapper.order
        side = order.side.value.upper()
        order_id = str(order.id)        
        logger.info(
            "fill_received",
            symbol=symbol,
            side=side,
            qty=fill.execution.shares,
            price=fill.execution.price,
            order_id=order_id,
            exec_id=exec_id,
        )
        
        # Record fill in database (will skip if duplicate)
        with self.db.get_session() as session:
            # Check if fill already exists before processing
            if self.db.fill_exists(session, exec_id):
                logger.debug("fill_already_processed", exec_id=exec_id, symbol=symbol)
                return
            
            self.db.add_fill(
                session,
                exec_id=exec_id,
                symbol=symbol,
                side=side,
                qty=fill.execution.shares,
                price=fill.execution.price,
                order_id=order_id,
            )
            
            self.db.add_event(
                session,
                event_type="fill",
                symbol=symbol,
                payload={
                    "exec_id": exec_id,
                    "side": side,
                    "qty": fill.execution.shares,
                    "price": fill.execution.price,
                    "order_id": order_id,
                },
            )
        
        # If this is a SELL fill of a trailing stop, enter cooldown
        if side == "SELL" and order.type == OrderType.TRAILING_STOP:
            logger.info("stopout_detected", symbol=symbol)
            if symbol in self.state_machines:
                self.state_machines[symbol].on_stop_out()
        
        # If this is a BUY fill from a tracked order, place trailing stop IMMEDIATELY
        # Skip for untracked/historical fills (they already have trailing stops or were stopped out)
        if side == "BUY" and symbol in self.state_machines:
            is_tracked = getattr(order_wrapper, 'is_tracked', True)
            if is_tracked:
                # IMPORTANT: Place trailing stop immediately (synchronously)
                # Don't use create_task to avoid delays/failures going unnoticed
                try:
                    # Schedule immediate placement (will run on next event loop iteration)
                    asyncio.ensure_future(
                        self._place_trailing_stop_with_retry(
                            symbol, 
                            int(fill.execution.shares),
                            fill.execution.price
                        )
                    )
                    logger.info("trailing_stop_placement_scheduled", symbol=symbol)
                except Exception as e:
                    logger.error("failed_to_schedule_trailing_stop", symbol=symbol, error=str(e))
            else:
                logger.debug("skipping_trailing_stop_for_historical_fill", symbol=symbol, order_id=order_id)

    def _on_order_status(self, order_wrapper: AlpacaOrder):
        """Handle order status updates."""
        symbol = order_wrapper.contract.symbol
        order_id = str(order_wrapper.order.id)
        status = order_wrapper.orderStatus.status
        
        logger.debug(
            "order_status_update",
            symbol=symbol,
            order_id=order_id,
            status=status,
        )
        
        # Update order status in database
        with self.db.get_session() as session:
            self.db.update_order_status(session, order_id, status)
            
            # Log significant status changes
            if status in ["filled", "canceled", "cancelled", "expired", "rejected"]:
                self.db.add_event(
                    session,
                    event_type=f"order_{status}",
                    symbol=symbol,
                    payload={
                        "order_id": order_id,
                        "status": status,
                    },
                )


async def main(config_path: str = "config.yaml"):
    """Main entry point."""
    import logging
    
    # Setup structured logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    logging.basicConfig(level=logging.INFO)
    
    # Load configuration
    try:
        config = BotConfig.from_yaml(config_path)
        logger.info("configuration_loaded", config_path=config_path)
    except Exception as e:
        logger.error("failed_to_load_config", error=str(e))
        sys.exit(1)
    
    # Create and start bot
    bot = TradingBot(config)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("keyboard_interrupt_received")
    except Exception as e:
        logger.error("bot_failed", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

