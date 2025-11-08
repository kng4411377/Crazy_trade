"""Main bot orchestrator."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
import signal
import sys
import structlog

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
        )
        self.sizer = PositionSizer(config)
        
        # State machines for each symbol (stocks + crypto)
        self.state_machines: Dict[str, SymbolStateMachine] = {}
        all_symbols = config.get_all_symbols()
        for symbol in all_symbols:
            self.state_machines[symbol] = SymbolStateMachine(
                symbol, config, self.alpaca, self.db, self.sizer
            )
        
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
        
        self.running = True
        
        # Log initial state
        with self.db.get_session() as session:
            self.db.add_event(
                session,
                event_type="bot_started",
                payload={
                    "mode": self.config.mode,
                    "stock_watchlist": self.config.watchlist,
                    "crypto_watchlist": self.config.crypto_watchlist,
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
        
        with self.db.get_session() as session:
            self.db.add_event(session, event_type="bot_stopped")
        
        logger.info("trading_bot_stopped")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("shutdown_signal_received", signal=signum)
        self.running = False

    async def _run_loop(self):
        """Main event loop."""
        logger.info("entering_main_loop")
        
        while self.running:
            try:
                # Check if we're in trading hours (for stocks)
                in_rth = self.market_hours.is_regular_trading_hours()
                has_crypto = len(self.config.crypto_watchlist) > 0
                
                # Process crypto always (24/7) or stocks during market hours
                if in_rth or has_crypto:
                    await self._process_trading_logic(in_rth=in_rth)
                else:
                    logger.debug("outside_trading_hours_no_crypto")
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
        
        # Process each symbol
        for symbol, sm in self.state_machines.items():
            try:
                # Skip stocks if market is closed
                is_crypto = self.config.is_crypto_symbol(symbol)
                if not is_crypto and not in_rth:
                    logger.debug("skipping_stock_outside_rth", symbol=symbol)
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

    def _on_fill(self, order_wrapper: AlpacaOrder, fill):
        """Handle fill events."""
        symbol = order_wrapper.contract.symbol
        exec_id = fill.execution.execId
        
        order = order_wrapper.order
        side = order.side.value.upper()
        order_id = order.id
        
        logger.info(
            "fill_received",
            symbol=symbol,
            side=side,
            qty=fill.execution.shares,
            price=fill.execution.price,
            order_id=order_id,
            exec_id=exec_id,
        )
        
        # Record fill in database
        with self.db.get_session() as session:
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
        
        # If this is a BUY fill, place trailing stop
        if side == "BUY" and symbol in self.state_machines:
            asyncio.create_task(self.state_machines[symbol].place_trailing_stop_after_entry(
                int(fill.execution.shares),
                fill.execution.price
            ))

    def _on_order_status(self, order_wrapper: AlpacaOrder):
        """Handle order status updates."""
        symbol = order_wrapper.contract.symbol
        order_id = order_wrapper.order.id
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

