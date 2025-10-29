"""Per-symbol state machine logic."""

from datetime import datetime, timedelta
from typing import Optional, Dict
from enum import Enum
import structlog

from ib_insync import Trade

from src.config import BotConfig
from src.database import DatabaseManager, SymbolState
from src.ibkr_client import IBKRClient
from src.sizing import PositionSizer

logger = structlog.get_logger()


class SymbolStatus(Enum):
    """Symbol trading status."""
    NO_POSITION = "no_position"
    ENTRY_PENDING = "entry_pending"
    POSITION_OPEN = "position_open"
    COOLDOWN = "cooldown"
    HALT = "halt"


class SymbolStateMachine:
    """Manage state transitions for a single symbol."""

    def __init__(
        self,
        symbol: str,
        config: BotConfig,
        ibkr_client: IBKRClient,
        db_manager: DatabaseManager,
        sizer: PositionSizer,
    ):
        """Initialize state machine for a symbol."""
        self.symbol = symbol.upper()
        self.config = config
        self.ibkr = ibkr_client
        self.db = db_manager
        self.sizer = sizer
        
        logger.info("state_machine_initialized", symbol=self.symbol)

    def get_status(self) -> SymbolStatus:
        """
        Determine current status of the symbol.
        
        Returns:
            Current SymbolStatus
        """
        # Check cooldown
        with self.db.get_session() as session:
            state = self.db.get_symbol_state(session, self.symbol)
            if state and state.cooldown_until_ts:
                if datetime.utcnow() < state.cooldown_until_ts:
                    return SymbolStatus.COOLDOWN

        # Check position
        positions = self.ibkr.get_positions()
        if self.symbol in positions and positions[self.symbol]["quantity"] > 0:
            return SymbolStatus.POSITION_OPEN

        # Check pending entry orders
        open_orders = self.ibkr.get_open_orders()
        for trade in open_orders:
            if (
                trade.contract.symbol == self.symbol
                and trade.order.action == "BUY"
                and trade.orderStatus.status in ["Submitted", "PreSubmitted"]
            ):
                return SymbolStatus.ENTRY_PENDING

        return SymbolStatus.NO_POSITION

    async def process(self, current_positions: Dict[str, float], account_value: Optional[float]):
        """
        Process state machine logic for this symbol.
        
        Args:
            current_positions: Dict of symbol -> position value for exposure checking
            account_value: Total account value
        """
        status = self.get_status()
        logger.debug("processing_symbol", symbol=self.symbol, status=status.value)

        if status == SymbolStatus.NO_POSITION:
            await self._handle_no_position(current_positions, account_value)
        elif status == SymbolStatus.ENTRY_PENDING:
            await self._handle_entry_pending()
        elif status == SymbolStatus.POSITION_OPEN:
            await self._handle_position_open()
        elif status == SymbolStatus.COOLDOWN:
            await self._handle_cooldown()

    async def _handle_no_position(
        self, current_positions: Dict[str, float], account_value: Optional[float]
    ):
        """Handle NO_POSITION state - create entry order if conditions met."""
        # Check if we should re-arm
        with self.db.get_session() as session:
            state = self.db.get_symbol_state(session, self.symbol)
            
            # Get last price
            last_price = await self.ibkr.get_last_price(self.symbol)
            if not last_price:
                logger.warning("cannot_fetch_price", symbol=self.symbol)
                return

            # Calculate position size
            qty = self.sizer.calculate_quantity(
                self.symbol, last_price, current_positions, account_value
            )
            
            if qty == 0:
                logger.info("skipping_entry_zero_qty", symbol=self.symbol)
                return

            # Place entry with trailing stop
            parent_trade, child_trade = await self.ibkr.place_entry_with_trailing_stop(
                self.symbol, qty, last_price
            )
            
            if parent_trade and child_trade:
                # Update state
                self.db.upsert_symbol_state(
                    session,
                    self.symbol,
                    last_parent_id=parent_trade.order.orderId,
                    last_trail_id=child_trade.order.orderId,
                )
                
                # Record orders in DB
                self.db.add_order(
                    session,
                    order_id=parent_trade.order.orderId,
                    symbol=self.symbol,
                    side="BUY",
                    order_type=parent_trade.order.orderType,
                    status="Submitted",
                    qty=qty,
                    stop_price=parent_trade.order.auxPrice,
                    limit_price=getattr(parent_trade.order, "lmtPrice", None),
                    trailing_pct=None,
                    parent_id=None,
                )
                
                self.db.add_order(
                    session,
                    order_id=child_trade.order.orderId,
                    symbol=self.symbol,
                    side="SELL",
                    order_type=child_trade.order.orderType,
                    status="Submitted",
                    qty=qty,
                    stop_price=None,
                    limit_price=None,
                    trailing_pct=child_trade.order.trailingPercent,
                    parent_id=parent_trade.order.orderId,
                )
                
                self.db.add_event(
                    session,
                    event_type="entry_order_placed",
                    symbol=self.symbol,
                    payload={
                        "parent_id": parent_trade.order.orderId,
                        "child_id": child_trade.order.orderId,
                        "qty": qty,
                        "last_price": last_price,
                    },
                )

    async def _handle_entry_pending(self):
        """Handle ENTRY_PENDING state - monitor entry order."""
        # Entry orders are DAY orders, so they'll auto-cancel at close
        # We just need to monitor fills (handled by event handlers)
        logger.debug("entry_pending", symbol=self.symbol)

    async def _handle_position_open(self):
        """Handle POSITION_OPEN state - ensure trailing stop exists and is healthy."""
        positions = self.ibkr.get_positions()
        position = positions.get(self.symbol)
        
        if not position:
            logger.warning("position_disappeared", symbol=self.symbol)
            return

        position_qty = int(position["quantity"])
        
        # Check for existing trailing stop
        open_orders = self.ibkr.get_open_orders()
        trailing_stops = [
            trade
            for trade in open_orders
            if trade.contract.symbol == self.symbol
            and trade.order.action == "SELL"
            and "TRAIL" in trade.order.orderType
        ]
        
        if not trailing_stops:
            # Missing trailing stop - create one
            logger.warning("missing_trailing_stop", symbol=self.symbol)
            last_price = await self.ibkr.get_last_price(self.symbol)
            if last_price:
                trade = await self.ibkr.place_trailing_stop(
                    self.symbol, position_qty, last_price
                )
                if trade:
                    with self.db.get_session() as session:
                        self.db.upsert_symbol_state(
                            session,
                            self.symbol,
                            last_trail_id=trade.order.orderId,
                        )
                        self.db.add_event(
                            session,
                            event_type="trailing_stop_recreated",
                            symbol=self.symbol,
                            payload={"order_id": trade.order.orderId, "qty": position_qty},
                        )
        elif len(trailing_stops) > 1:
            # Multiple stops - cancel duplicates (keep the first one)
            logger.warning("duplicate_trailing_stops", symbol=self.symbol, count=len(trailing_stops))
            for trade in trailing_stops[1:]:
                await self.ibkr.cancel_order(trade)
                with self.db.get_session() as session:
                    self.db.add_event(
                        session,
                        event_type="duplicate_stop_cancelled",
                        symbol=self.symbol,
                        payload={"order_id": trade.order.orderId},
                    )
        else:
            # Verify quantity matches
            stop_trade = trailing_stops[0]
            stop_qty = int(stop_trade.order.totalQuantity)
            
            if stop_qty != position_qty:
                logger.warning(
                    "stop_qty_mismatch",
                    symbol=self.symbol,
                    position_qty=position_qty,
                    stop_qty=stop_qty,
                )
                # Cancel and recreate
                await self.ibkr.cancel_order(stop_trade)
                last_price = await self.ibkr.get_last_price(self.symbol)
                if last_price:
                    trade = await self.ibkr.place_trailing_stop(
                        self.symbol, position_qty, last_price
                    )
                    if trade:
                        with self.db.get_session() as session:
                            self.db.upsert_symbol_state(
                                session,
                                self.symbol,
                                last_trail_id=trade.order.orderId,
                            )
                            self.db.add_event(
                                session,
                                event_type="trailing_stop_adjusted",
                                symbol=self.symbol,
                                payload={
                                    "old_qty": stop_qty,
                                    "new_qty": position_qty,
                                    "order_id": trade.order.orderId,
                                },
                            )

    async def _handle_cooldown(self):
        """Handle COOLDOWN state - wait for cooldown to expire."""
        with self.db.get_session() as session:
            state = self.db.get_symbol_state(session, self.symbol)
            if state and state.cooldown_until_ts:
                remaining = (state.cooldown_until_ts - datetime.utcnow()).total_seconds()
                logger.debug(
                    "in_cooldown",
                    symbol=self.symbol,
                    remaining_seconds=int(remaining),
                )

    def on_stop_out(self):
        """Handle stop-out event - enter cooldown period."""
        cooldown_minutes = self.config.cooldowns.after_stopout_minutes
        cooldown_until = datetime.utcnow() + timedelta(minutes=cooldown_minutes)
        
        with self.db.get_session() as session:
            self.db.upsert_symbol_state(
                session,
                self.symbol,
                cooldown_until_ts=cooldown_until,
            )
            self.db.add_event(
                session,
                event_type="stopout_cooldown_started",
                symbol=self.symbol,
                payload={
                    "cooldown_minutes": cooldown_minutes,
                    "cooldown_until": cooldown_until.isoformat(),
                },
            )
        
        logger.info(
            "stopout_cooldown_started",
            symbol=self.symbol,
            cooldown_minutes=cooldown_minutes,
        )

    async def cancel_unfilled_entries(self):
        """Cancel unfilled entry orders (e.g., at end of day)."""
        open_orders = self.ibkr.get_open_orders()
        for trade in open_orders:
            if (
                trade.contract.symbol == self.symbol
                and trade.order.action == "BUY"
                and trade.orderStatus.status in ["Submitted", "PreSubmitted"]
            ):
                await self.ibkr.cancel_order(trade)
                with self.db.get_session() as session:
                    self.db.add_event(
                        session,
                        event_type="entry_cancelled_eod",
                        symbol=self.symbol,
                        payload={"order_id": trade.order.orderId},
                    )
                logger.info("entry_cancelled_eod", symbol=self.symbol, order_id=trade.order.orderId)

