"""Main bot orchestrator."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
import signal
import sys
import structlog

from ib_insync import Trade, Fill, util

from src.config import BotConfig
from src.database import DatabaseManager
from src.ibkr_client import IBKRClient
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
        
        self.ibkr = IBKRClient(config)
        self.market_hours = MarketHoursChecker(
            config.hours.calendar,
            config.hours.allow_pre_market,
            config.hours.allow_after_hours,
        )
        self.sizer = PositionSizer(config)
        
        # State machines for each symbol
        self.state_machines: Dict[str, SymbolStateMachine] = {}
        for symbol in config.watchlist:
            self.state_machines[symbol] = SymbolStateMachine(
                symbol, config, self.ibkr, self.db, self.sizer
            )
        
        # Performance tracker
        self.performance = PerformanceTracker(self.db, self.ibkr)
        
        # Register event handlers
        self.ibkr.register_fill_callback(self._on_fill)
        self.ibkr.register_order_status_callback(self._on_order_status)
        
        # Track last operation times
        self.last_price_check = datetime.min
        self.last_order_check = datetime.min
        self.last_eod_cancel = None
        self.last_snapshot_date = None
        
        logger.info(
            "trading_bot_initialized",
            mode=config.mode,
            watchlist=config.watchlist,
            num_symbols=len(config.watchlist),
        )

    async def start(self):
        """Start the trading bot."""
        logger.info("starting_trading_bot")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Connect to IBKR
        await self.ibkr.connect()
        
        self.running = True
        
        # Log initial state
        with self.db.get_session() as session:
            self.db.add_event(
                session,
                event_type="bot_started",
                payload={
                    "mode": self.config.mode,
                    "watchlist": self.config.watchlist,
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
        
        await self.ibkr.disconnect()
        
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
                # Check if we're in trading hours
                in_rth = self.market_hours.is_regular_trading_hours()
                
                if in_rth:
                    await self._process_trading_logic()
                else:
                    logger.debug("outside_trading_hours")
                    await asyncio.sleep(60)  # Check every minute when market is closed
                    continue
                
                # Handle end-of-day cancellations
                await self._handle_eod_cancellations()
                
                # Take daily performance snapshot
                await self._take_daily_snapshot()
                
                # Sleep based on polling interval
                await asyncio.sleep(self.config.polling.orders_seconds)
                
            except Exception as e:
                logger.error("loop_iteration_error", error=str(e), exc_info=True)
                await asyncio.sleep(10)  # Brief pause on error
        
        logger.info("exiting_main_loop")

    async def _process_trading_logic(self):
        """Process trading logic for all symbols."""
        # Get current positions and account value
        positions = self.ibkr.get_positions()
        account_value = self.ibkr.get_account_value()
        
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
                await sm.process(position_values, account_value)
            except Exception as e:
                logger.error(
                    "symbol_processing_error",
                    symbol=symbol,
                    error=str(e),
                    exc_info=True,
                )

    async def _handle_eod_cancellations(self):
        """Handle end-of-day order cancellations."""
        if not self.config.entries.cancel_at_close:
            return
        
        # Check if we're near market close (within 15 minutes)
        seconds_to_close = self.market_hours.seconds_until_market_close()
        
        if 0 < seconds_to_close <= 900:  # 15 minutes
            # Check if we've already done this today
            today = datetime.utcnow().date()
            if self.last_eod_cancel != today:
                logger.info("cancelling_unfilled_entries_eod")
                
                for symbol, sm in self.state_machines.items():
                    await sm.cancel_unfilled_entries()
                
                self.last_eod_cancel = today
                
                with self.db.get_session() as session:
                    self.db.add_event(
                        session,
                        event_type="eod_cancellations_completed",
                    )

    async def _take_daily_snapshot(self):
        """Take daily performance snapshot."""
        today = datetime.utcnow().date()
        
        # Only snapshot once per day
        if self.last_snapshot_date == today:
            return
        
        try:
            # Get account summary
            account_summary = self.performance.get_account_summary()
            positions = self.ibkr.get_positions()
            
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

    def _on_fill(self, trade: Trade, fill: Fill):
        """Handle fill events."""
        symbol = trade.contract.symbol
        exec_id = fill.execution.execId
        
        logger.info(
            "fill_received",
            symbol=symbol,
            side=trade.order.action,
            qty=fill.execution.shares,
            price=fill.execution.price,
            order_id=trade.order.orderId,
            exec_id=exec_id,
        )
        
        # Record fill in database
        with self.db.get_session() as session:
            self.db.add_fill(
                session,
                exec_id=exec_id,
                symbol=symbol,
                side=trade.order.action,
                qty=fill.execution.shares,
                price=fill.execution.price,
                order_id=trade.order.orderId,
            )
            
            self.db.add_event(
                session,
                event_type="fill",
                symbol=symbol,
                payload={
                    "exec_id": exec_id,
                    "side": trade.order.action,
                    "qty": fill.execution.shares,
                    "price": fill.execution.price,
                    "order_id": trade.order.orderId,
                },
            )
        
        # If this is a SELL fill of a trailing stop, enter cooldown
        if trade.order.action == "SELL" and "TRAIL" in trade.order.orderType:
            logger.info("stopout_detected", symbol=symbol)
            if symbol in self.state_machines:
                self.state_machines[symbol].on_stop_out()

    def _on_order_status(self, trade: Trade):
        """Handle order status updates."""
        symbol = trade.contract.symbol
        order_id = trade.order.orderId
        status = trade.orderStatus.status
        
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
            if status in ["Filled", "Cancelled", "Inactive"]:
                self.db.add_event(
                    session,
                    event_type=f"order_{status.lower()}",
                    symbol=symbol,
                    payload={
                        "order_id": order_id,
                        "status": status,
                    },
                )


async def main(config_path: str = "config.yaml"):
    """Main entry point."""
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
    
    import logging
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

