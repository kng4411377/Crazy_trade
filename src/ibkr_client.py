"""IBKR client wrapper using ib_insync."""

from typing import Optional, Dict, Callable
from decimal import Decimal, ROUND_DOWN
import asyncio
import structlog

from ib_insync import IB, Stock, Order, Trade, OrderStatus, Execution, Fill
from ib_insync import util

from src.config import BotConfig

logger = structlog.get_logger()


class IBKRClient:
    """Wrapper for IBKR API using ib_insync."""

    def __init__(self, config: BotConfig):
        """Initialize IBKR client."""
        self.config = config
        self.ib = IB()
        self.connected = False
        self.contracts_cache: Dict[str, Stock] = {}
        
        # Event handlers
        self.on_fill_callback: Optional[Callable] = None
        self.on_order_status_callback: Optional[Callable] = None
        
        logger.info("ibkr_client_initialized")

    async def connect(self):
        """Connect to IBKR Gateway."""
        try:
            await self.ib.connectAsync(
                host=self.config.ibkr.host,
                port=self.config.ibkr.port,
                clientId=self.config.ibkr.client_id,
            )
            self.connected = True
            
            # Register event handlers
            self.ib.execDetailsEvent += self._on_execution
            self.ib.orderStatusEvent += self._on_order_status
            
            logger.info(
                "ibkr_connected",
                host=self.config.ibkr.host,
                port=self.config.ibkr.port,
                client_id=self.config.ibkr.client_id,
            )
        except Exception as e:
            logger.error("ibkr_connection_failed", error=str(e))
            raise

    async def disconnect(self):
        """Disconnect from IBKR."""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("ibkr_disconnected")

    def get_contract(self, symbol: str) -> Stock:
        """
        Get or create a contract for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Stock contract
        """
        symbol = symbol.upper()
        if symbol not in self.contracts_cache:
            contract = Stock(symbol, "SMART", "USD")
            self.contracts_cache[symbol] = contract
            logger.debug("contract_created", symbol=symbol)
        return self.contracts_cache[symbol]

    async def get_last_price(self, symbol: str) -> Optional[float]:
        """
        Get last traded price for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Last price or None if unavailable
        """
        try:
            contract = self.get_contract(symbol)
            ticker = self.ib.reqMktData(contract, "", False, False)
            await asyncio.sleep(2)  # Wait for market data
            
            price = ticker.last
            if not util.isNan(price) and price > 0:
                logger.debug("price_fetched", symbol=symbol, price=price)
                return price
            
            # Fallback to close price
            if not util.isNan(ticker.close) and ticker.close > 0:
                logger.debug("using_close_price", symbol=symbol, price=ticker.close)
                return ticker.close
            
            logger.warning("price_unavailable", symbol=symbol)
            return None
            
        except Exception as e:
            logger.error("price_fetch_failed", symbol=symbol, error=str(e))
            return None

    def round_to_tick(self, price: float, tick_size: float = 0.01) -> float:
        """
        Round price to nearest tick size.
        
        Args:
            price: Price to round
            tick_size: Tick size (default 0.01)
            
        Returns:
            Rounded price
        """
        decimal_price = Decimal(str(price))
        decimal_tick = Decimal(str(tick_size))
        return float((decimal_price / decimal_tick).quantize(1, ROUND_DOWN) * decimal_tick)

    async def place_entry_with_trailing_stop(
        self, symbol: str, qty: int, last_price: float
    ) -> tuple[Optional[Trade], Optional[Trade]]:
        """
        Place entry order (Buy Stop) with attached trailing stop.
        
        Args:
            symbol: Stock symbol
            qty: Quantity to buy
            last_price: Current price
            
        Returns:
            Tuple of (parent_trade, child_trade) or (None, None) on error
        """
        try:
            contract = self.get_contract(symbol)
            
            # Calculate stop price for entry
            stop_pct = self.config.entries.buy_stop_pct_above_last
            stop_price = self.round_to_tick(last_price * (1 + stop_pct / 100))
            
            # Create parent order (Buy Stop)
            parent = Order()
            parent.action = "BUY"
            parent.totalQuantity = qty
            parent.outsideRth = False  # RTH only
            
            if self.config.entries.type == "buy_stop":
                parent.orderType = "STP"
                parent.auxPrice = stop_price
            else:  # buy_stop_limit
                parent.orderType = "STP LMT"
                parent.auxPrice = stop_price
                slip_pct = self.config.entries.stop_limit_max_slip_pct
                parent.lmtPrice = self.round_to_tick(stop_price * (1 + slip_pct / 100))
            
            parent.tif = self.config.entries.tif
            parent.transmit = False  # Don't transmit yet
            
            # Place parent order
            parent_trade = self.ib.placeOrder(contract, parent)
            await asyncio.sleep(1)  # Wait for order ID assignment
            
            logger.info(
                "parent_order_placed",
                symbol=symbol,
                order_id=parent_trade.order.orderId,
                qty=qty,
                stop_price=stop_price,
            )
            
            # Create trailing stop child
            child = Order()
            child.action = "SELL"
            child.totalQuantity = qty
            child.orderType = "TRAIL"
            child.trailingPercent = self.config.stops.trailing_stop_pct
            child.tif = self.config.stops.tif
            child.parentId = parent_trade.order.orderId
            child.outsideRth = False
            child.transmit = True  # Transmit the entire bracket
            
            # Handle trailing limit variant
            if self.config.stops.use_trailing_limit:
                child.orderType = "TRAIL LIMIT"
                offset_pct = self.config.stops.trail_limit_offset_pct
                child.lmtPriceOffset = self.round_to_tick(last_price * offset_pct / 100)
            
            # Place child order
            child_trade = self.ib.placeOrder(contract, child)
            
            logger.info(
                "trailing_stop_placed",
                symbol=symbol,
                order_id=child_trade.order.orderId,
                parent_id=parent_trade.order.orderId,
                trailing_pct=child.trailingPercent,
            )
            
            return parent_trade, child_trade
            
        except Exception as e:
            logger.error(
                "order_placement_failed",
                symbol=symbol,
                error=str(e),
            )
            return None, None

    async def place_trailing_stop(
        self, symbol: str, qty: int, current_price: float
    ) -> Optional[Trade]:
        """
        Place standalone trailing stop (for existing position).
        
        Args:
            symbol: Stock symbol
            qty: Position quantity
            current_price: Current price (for limit offset calculation)
            
        Returns:
            Trade object or None on error
        """
        try:
            contract = self.get_contract(symbol)
            
            order = Order()
            order.action = "SELL"
            order.totalQuantity = qty
            order.orderType = "TRAIL"
            order.trailingPercent = self.config.stops.trailing_stop_pct
            order.tif = self.config.stops.tif
            order.outsideRth = False
            
            if self.config.stops.use_trailing_limit:
                order.orderType = "TRAIL LIMIT"
                offset_pct = self.config.stops.trail_limit_offset_pct
                order.lmtPriceOffset = self.round_to_tick(current_price * offset_pct / 100)
            
            trade = self.ib.placeOrder(contract, order)
            
            logger.info(
                "standalone_trailing_stop_placed",
                symbol=symbol,
                order_id=trade.order.orderId,
                qty=qty,
                trailing_pct=order.trailingPercent,
            )
            
            return trade
            
        except Exception as e:
            logger.error(
                "trailing_stop_placement_failed",
                symbol=symbol,
                error=str(e),
            )
            return None

    async def cancel_order(self, trade: Trade):
        """
        Cancel an order.
        
        Args:
            trade: Trade object to cancel
        """
        try:
            self.ib.cancelOrder(trade.order)
            logger.info("order_cancelled", order_id=trade.order.orderId)
        except Exception as e:
            logger.error("order_cancel_failed", order_id=trade.order.orderId, error=str(e))

    def get_positions(self) -> Dict[str, dict]:
        """
        Get all current positions.
        
        Returns:
            Dict of symbol -> position info
        """
        positions = {}
        for position in self.ib.positions():
            symbol = position.contract.symbol
            positions[symbol] = {
                "quantity": position.position,
                "avg_cost": position.avgCost,
                "market_value": position.position * position.marketPrice
                if hasattr(position, "marketPrice")
                else 0,
            }
        return positions

    def get_open_orders(self) -> list[Trade]:
        """
        Get all open orders.
        
        Returns:
            List of Trade objects
        """
        return self.ib.openTrades()

    def get_account_value(self) -> Optional[float]:
        """
        Get total account value.
        
        Returns:
            Account value or None
        """
        try:
            account_values = self.ib.accountValues()
            for av in account_values:
                if av.tag == "NetLiquidation":
                    return float(av.value)
            return None
        except Exception as e:
            logger.error("account_value_fetch_failed", error=str(e))
            return None

    # Event handlers

    def _on_execution(self, trade: Trade, fill: Fill):
        """Handle execution events."""
        logger.info(
            "execution_received",
            symbol=trade.contract.symbol,
            side=trade.order.action,
            qty=fill.execution.shares,
            price=fill.execution.price,
            order_id=trade.order.orderId,
        )
        
        if self.on_fill_callback:
            self.on_fill_callback(trade, fill)

    def _on_order_status(self, trade: Trade):
        """Handle order status events."""
        logger.info(
            "order_status_update",
            symbol=trade.contract.symbol,
            order_id=trade.order.orderId,
            status=trade.orderStatus.status,
        )
        
        if self.on_order_status_callback:
            self.on_order_status_callback(trade)

    def register_fill_callback(self, callback: Callable):
        """Register callback for fill events."""
        self.on_fill_callback = callback

    def register_order_status_callback(self, callback: Callable):
        """Register callback for order status events."""
        self.on_order_status_callback = callback

