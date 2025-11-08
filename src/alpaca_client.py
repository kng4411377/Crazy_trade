"""Alpaca API client wrapper."""

from __future__ import annotations

from typing import Optional, Dict, Callable, List
from decimal import Decimal, ROUND_DOWN
import asyncio
import structlog
from datetime import datetime

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    StopOrderRequest,
    StopLimitOrderRequest,
    TrailingStopOrderRequest,
    GetOrdersRequest,
)
from alpaca.trading.enums import (
    OrderSide,
    TimeInForce,
    OrderType,
    QueryOrderStatus,
    OrderClass,
)
from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, CryptoLatestQuoteRequest

from src.config import BotConfig

logger = structlog.get_logger()


class AlpacaOrder:
    """Wrapper for Alpaca order to provide consistent interface."""
    
    def __init__(self, alpaca_order):
        self.order = alpaca_order
        self.contract = type('obj', (object,), {'symbol': alpaca_order.symbol})()
        self.orderStatus = type('obj', (object,), {'status': alpaca_order.status.value})()


class AlpacaClient:
    """Wrapper for Alpaca Trading API."""

    def __init__(self, config: BotConfig):
        """Initialize Alpaca client."""
        self.config = config
        self.connected = False
        
        # Initialize Alpaca clients
        self.trading_client = None
        self.data_client = None
        
        # Event handlers
        self.on_fill_callback: Optional[Callable] = None
        self.on_order_status_callback: Optional[Callable] = None
        
        # Track orders for event handling
        self.tracked_orders: Dict[str, AlpacaOrder] = {}
        self.last_order_check = datetime.min
        
        logger.info("alpaca_client_initialized")

    async def connect(self):
        """Connect to Alpaca API."""
        try:
            # Initialize trading client
            self.trading_client = TradingClient(
                api_key=self.config.alpaca.api_key,
                secret_key=self.config.alpaca.secret_key,
                paper=self.config.mode == "paper"
            )
            
            # Initialize data clients (for market data)
            self.data_client = StockHistoricalDataClient(
                api_key=self.config.alpaca.api_key,
                secret_key=self.config.alpaca.secret_key
            )
            self.crypto_data_client = CryptoHistoricalDataClient()  # No auth needed for crypto data
            
            # Test connection
            account = self.trading_client.get_account()
            self.connected = True
            
            logger.info(
                "alpaca_connected",
                account_number=account.account_number,
                status=account.status.value,
                paper_trading=self.config.mode == "paper"
            )
        except Exception as e:
            logger.error("alpaca_connection_failed", error=str(e))
            raise

    async def disconnect(self):
        """Disconnect from Alpaca (cleanup)."""
        if self.connected:
            self.trading_client = None
            self.data_client = None
            self.crypto_data_client = None
            self.connected = False
            logger.info("alpaca_disconnected")

    async def get_last_price(self, symbol: str) -> Optional[float]:
        """
        Get last traded price for a symbol (stocks or crypto).
        
        Args:
            symbol: Stock or crypto symbol (e.g., 'AAPL' or 'BTC/USD')
            
        Returns:
            Last price or None if unavailable
        """
        try:
            # Detect if symbol is crypto (contains '/')
            is_crypto = '/' in symbol or self.config.is_crypto_symbol(symbol)
            
            if is_crypto:
                # Use crypto data API
                request = CryptoLatestQuoteRequest(symbol_or_symbols=symbol)
                quotes = self.crypto_data_client.get_crypto_latest_quote(request)
                
                if symbol in quotes:
                    quote = quotes[symbol]
                    # Use mid-point of bid/ask for better pricing
                    price = (quote.bid_price + quote.ask_price) / 2.0
                    logger.debug("crypto_price_fetched", symbol=symbol, price=price)
                    return float(price)
            else:
                # Use stock data API
                request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
                quotes = self.data_client.get_stock_latest_quote(request)
                
                if symbol in quotes:
                    quote = quotes[symbol]
                    # Use mid-point of bid/ask for better pricing
                    price = (quote.bid_price + quote.ask_price) / 2.0
                    logger.debug("stock_price_fetched", symbol=symbol, price=price)
                    return float(price)
            
            logger.warning("price_unavailable", symbol=symbol, is_crypto=is_crypto)
            return None
            
        except Exception as e:
            logger.error("price_fetch_failed", symbol=symbol, error=str(e))
            logger.debug("cannot_fetch_price", symbol=symbol)
            return None

    def round_to_tick(self, price: float, tick_size: float = None) -> float:
        """
        Round price to nearest tick size.
        
        Args:
            price: Price to round
            tick_size: Tick size (default: auto-detect based on price magnitude)
            
        Returns:
            Rounded price
        """
        if tick_size is None:
            # Auto-detect tick size based on price magnitude
            if price < 0.01:  # Very small prices (like SHIB at $0.00001)
                tick_size = 0.0000001  # 7 decimal places
            elif price < 1.0:  # Small prices (like some altcoins)
                tick_size = 0.0001  # 4 decimal places
            elif price < 10.0:
                tick_size = 0.01  # 2 decimal places
            else:
                tick_size = 0.01  # Standard 2 decimal places
        
        decimal_price = Decimal(str(price))
        decimal_tick = Decimal(str(tick_size))
        return float((decimal_price / decimal_tick).quantize(1, ROUND_DOWN) * decimal_tick)

    async def place_entry_with_trailing_stop(
        self, symbol: str, qty: int, last_price: float
    ) -> tuple[Optional[AlpacaOrder], Optional[AlpacaOrder]]:
        """
        Place entry order with attached trailing stop.
        
        Note: Alpaca doesn't support bracket orders with stop entry + trailing stop.
        We'll place the entry order first, and the trailing stop will be placed
        after the entry fills (handled by the bot's fill callback).
        
        For crypto: Uses limit orders instead of stop orders (crypto doesn't support stops)
        
        Args:
            symbol: Stock or crypto symbol
            qty: Quantity to buy (fractional supported for crypto)
            last_price: Current price
            
        Returns:
            Tuple of (parent_order, None) - child order placed after fill
        """
        try:
            # Detect if symbol is crypto
            is_crypto = self.config.is_crypto_symbol(symbol)
            
            # Calculate entry price
            entry_pct = self.config.entries.buy_stop_pct_above_last
            entry_price = self.round_to_tick(last_price * (1 + entry_pct / 100))
            
            if is_crypto:
                # Crypto: Use limit order (stop orders not supported)
                # Limit order at breakout price acts similar to buy stop
                order_request = LimitOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.GTC,  # GTC for crypto (24/7)
                    limit_price=entry_price
                )
                logger.info(
                    "crypto_entry_order_type",
                    symbol=symbol,
                    order_type="limit",
                    note="Stop orders not supported for crypto, using limit order"
                )
            else:
                # Stocks: Use stop orders (standard)
                if self.config.entries.type == "buy_stop":
                    order_request = StopOrderRequest(
                        symbol=symbol,
                        qty=qty,
                        side=OrderSide.BUY,
                        time_in_force=TimeInForce.DAY,
                        stop_price=entry_price
                    )
                else:  # buy_stop_limit
                    slip_pct = self.config.entries.stop_limit_max_slip_pct
                    limit_price = self.round_to_tick(entry_price * (1 + slip_pct / 100))
                    order_request = StopLimitOrderRequest(
                        symbol=symbol,
                        qty=qty,
                        side=OrderSide.BUY,
                        time_in_force=TimeInForce.DAY,
                        stop_price=entry_price,
                        limit_price=limit_price
                    )
            
            # Submit order
            order = self.trading_client.submit_order(order_request)
            parent_wrapper = AlpacaOrder(order)
            
            # Track order for event handling
            self.tracked_orders[order.id] = parent_wrapper
            
            logger.info(
                "entry_order_placed",
                symbol=symbol,
                order_id=str(order.id),  # Convert UUID to string for clean logging
                qty=qty,
                entry_price=entry_price,
                order_type=order.type.value,
                is_crypto=is_crypto
            )
            
            # Return parent order (trailing stop will be placed after fill)
            return parent_wrapper, None
            
        except Exception as e:
            logger.error(
                "order_placement_failed",
                symbol=symbol,
                error=str(e),
            )
            return None, None

    async def place_trailing_stop(
        self, symbol: str, qty: int, current_price: float
    ) -> Optional[AlpacaOrder]:
        """
        Place standalone trailing stop (for existing position).
        
        For crypto: Uses stop-loss limit order instead (trailing stops not supported)
        
        Args:
            symbol: Stock or crypto symbol
            qty: Position quantity
            current_price: Current price (for reference)
            
        Returns:
            AlpacaOrder wrapper or None on error
        """
        try:
            # Detect if symbol is crypto
            is_crypto = self.config.is_crypto_symbol(symbol)
            
            trail_percent = self.config.stops.trailing_stop_pct
            
            if is_crypto:
                # Crypto: Use stop-loss limit order (trailing stops not supported)
                # Calculate stop price from current price
                stop_price = self.round_to_tick(current_price * (1 - trail_percent / 100))
                
                # Use limit order slightly below stop price for better execution
                limit_price = self.round_to_tick(stop_price * 0.99)  # 1% below stop
                
                order_request = LimitOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.GTC,  # GTC for crypto (24/7)
                    limit_price=stop_price  # Sell at stop price
                )
                
                logger.info(
                    "crypto_stop_loss_placed",
                    symbol=symbol,
                    qty=qty,
                    stop_price=stop_price,
                    note="Trailing stops not supported for crypto, using fixed stop-loss limit order"
                )
            else:
                # Stocks: Use trailing stop (standard)
                order_request = TrailingStopOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.GTC,
                    trail_percent=trail_percent
                )
            
            # Submit order
            order = self.trading_client.submit_order(order_request)
            wrapper = AlpacaOrder(order)
            
            # Track order
            self.tracked_orders[order.id] = wrapper
            
            logger.info(
                "exit_order_placed",
                symbol=symbol,
                order_id=str(order.id),  # Convert UUID to string for clean logging
                qty=qty,
                trail_percent=trail_percent if not is_crypto else None,
                stop_price=stop_price if is_crypto else None,
                order_type=order.type.value,
                is_crypto=is_crypto
            )
            
            return wrapper
            
        except Exception as e:
            logger.error(
                "exit_order_placement_failed",
                symbol=symbol,
                error=str(e),
            )
            return None

    async def cancel_order(self, order_wrapper: AlpacaOrder):
        """
        Cancel an order.
        
        Args:
            order_wrapper: AlpacaOrder wrapper to cancel
        """
        try:
            order_id = order_wrapper.order.id
            self.trading_client.cancel_order_by_id(order_id)
            
            # Remove from tracking
            if order_id in self.tracked_orders:
                del self.tracked_orders[order_id]
            
            logger.info("order_cancelled", order_id=order_id)
        except Exception as e:
            logger.error("order_cancel_failed", order_id=order_wrapper.order.id, error=str(e))

    def get_positions(self) -> Dict[str, dict]:
        """
        Get all current positions.
        
        Returns:
            Dict of symbol -> position info
        """
        try:
            positions_list = self.trading_client.get_all_positions()
            positions = {}
            
            for position in positions_list:
                # Safely get unrealized P&L (attribute may vary by account type)
                unrealized_pnl = 0.0
                try:
                    if hasattr(position, 'unrealized_pl') and position.unrealized_pl is not None:
                        unrealized_pnl = float(position.unrealized_pl)
                    elif hasattr(position, 'unrealized_plpc') and position.unrealized_plpc is not None:
                        market_val = float(position.market_value) if position.market_value is not None else 0.0
                        unrealized_pnl = float(position.unrealized_plpc) * market_val
                except (ValueError, TypeError) as e:
                    logger.warning("unrealized_pnl_calculation_failed", symbol=position.symbol, error=str(e))
                
                positions[position.symbol] = {
                    "quantity": float(position.qty) if position.qty is not None else 0.0,
                    "avg_cost": float(position.avg_entry_price) if position.avg_entry_price is not None else 0.0,
                    "market_value": float(position.market_value) if position.market_value is not None else 0.0,
                    "unrealized_pnl": unrealized_pnl,
                    "current_price": float(position.current_price) if position.current_price is not None else 0.0,
                }
            
            return positions
            
        except Exception as e:
            logger.error("positions_fetch_failed", error=str(e))
            return {}

    def get_open_orders(self) -> List[AlpacaOrder]:
        """
        Get all open orders.
        
        Returns:
            List of AlpacaOrder wrappers
        """
        try:
            filter_request = GetOrdersRequest(
                status=QueryOrderStatus.OPEN
            )
            orders = self.trading_client.get_orders(filter=filter_request)
            
            # Wrap orders
            wrapped_orders = [AlpacaOrder(order) for order in orders]
            
            # Update tracking
            for wrapper in wrapped_orders:
                self.tracked_orders[wrapper.order.id] = wrapper
            
            return wrapped_orders
            
        except Exception as e:
            logger.error("open_orders_fetch_failed", error=str(e))
            return []

    def get_account_value(self) -> Optional[float]:
        """
        Get total account value.
        
        Returns:
            Account equity value or None
        """
        try:
            account = self.trading_client.get_account()
            return float(account.equity)
        except Exception as e:
            logger.error("account_value_fetch_failed", error=str(e))
            return None

    async def check_for_events(self):
        """
        Check for order updates and fills.
        This simulates event-driven updates for Alpaca's REST API.
        Called periodically by the bot.
        """
        try:
            # Get recent orders
            orders = self.trading_client.get_orders(
                filter=GetOrdersRequest(status=QueryOrderStatus.CLOSED, limit=50)
            )
            
            # Check for filled orders we're tracking
            for order in orders:
                if order.id in self.tracked_orders:
                    old_wrapper = self.tracked_orders[order.id]
                    old_status = old_wrapper.order.status
                    
                    # Order status changed
                    if order.status != old_status:
                        # Update wrapper
                        new_wrapper = AlpacaOrder(order)
                        self.tracked_orders[order.id] = new_wrapper
                        
                        # Trigger order status callback
                        if self.on_order_status_callback:
                            self.on_order_status_callback(new_wrapper)
                        
                        # If filled, trigger fill callback
                        if order.status.value in ['filled', 'partially_filled']:
                            if self.on_fill_callback:
                                # Create a simple fill object
                                fill = type('obj', (object,), {
                                    'execution': type('obj', (object,), {
                                        'shares': float(order.filled_qty),
                                        'price': float(order.filled_avg_price) if order.filled_avg_price else 0,
                                        'execId': order.id,
                                    })()
                                })()
                                self.on_fill_callback(new_wrapper, fill)
                        
                        # Clean up filled/cancelled orders
                        if order.status.value in ['filled', 'canceled', 'expired', 'rejected']:
                            del self.tracked_orders[order.id]
            
        except Exception as e:
            logger.error("event_check_failed", error=str(e))

    def register_fill_callback(self, callback: Callable):
        """Register callback for fill events."""
        self.on_fill_callback = callback

    def register_order_status_callback(self, callback: Callable):
        """Register callback for order status events."""
        self.on_order_status_callback = callback

    async def keep_alive(self):
        """
        Keep-alive tickle (not needed for Alpaca REST API, but kept for compatibility).
        """
        try:
            # Just verify connection with a lightweight request
            account = self.trading_client.get_account()
            logger.debug("keepalive_ping", account_status=account.status.value)
        except Exception as e:
            logger.warning("keepalive_failed", error=str(e))

    def get_account_summary(self) -> Dict[str, float]:
        """
        Get account summary with key metrics.
        
        Returns:
            Dict with account metrics
        """
        try:
            account = self.trading_client.get_account()
            
            # Safely get unrealized P&L (attribute may vary by account type)
            unrealized_pnl = 0.0
            if hasattr(account, 'unrealized_pl'):
                unrealized_pnl = float(account.unrealized_pl)
            elif hasattr(account, 'unrealized_plpc'):
                unrealized_pnl = float(account.unrealized_plpc)
            
            # Safely calculate realized P&L
            realized_pnl = 0.0
            if hasattr(account, 'equity') and hasattr(account, 'last_equity'):
                try:
                    equity = float(account.equity) if account.equity is not None else 0.0
                    last_equity = float(account.last_equity) if account.last_equity is not None else 0.0
                    realized_pnl = equity - last_equity
                except (ValueError, TypeError) as e:
                    logger.warning("realized_pnl_calculation_failed", error=str(e))
                    realized_pnl = 0.0
            
            summary = {
                'NetLiquidation': float(account.equity) if hasattr(account, 'equity') and account.equity is not None else 0.0,
                'TotalCashValue': float(account.cash) if hasattr(account, 'cash') and account.cash is not None else 0.0,
                'GrossPositionValue': float(account.long_market_value) if hasattr(account, 'long_market_value') and account.long_market_value is not None else 0.0,
                'UnrealizedPnL': unrealized_pnl,
                'RealizedPnL': realized_pnl,
                'AvailableFunds': float(account.cash) if hasattr(account, 'cash') and account.cash is not None else 0.0,
                'BuyingPower': float(account.buying_power) if hasattr(account, 'buying_power') and account.buying_power is not None else 0.0,
            }
            
            logger.info("account_summary_fetched", summary=summary)
            return summary
            
        except Exception as e:
            logger.error("account_summary_fetch_failed", error=str(e))
            return {}

    def close_all_positions(self) -> bool:
        """
        Close all open positions at market price.
        Useful for resetting paper trading or emergency exit.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.trading_client.close_all_positions(cancel_orders=True)
            logger.info("closed_all_positions")
            return True
        except Exception as e:
            logger.error("close_all_positions_failed", error=str(e))
            return False

    def cancel_all_orders(self) -> bool:
        """
        Cancel all open orders.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.trading_client.cancel_orders()
            logger.info("cancelled_all_orders")
            return True
        except Exception as e:
            logger.error("cancel_all_orders_failed", error=str(e))
            return False

    def reset_paper_account(self) -> bool:
        """
        Reset paper trading account by closing all positions and canceling all orders.
        Only works in paper trading mode.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Close all positions (which also cancels orders)
            result = self.close_all_positions()
            
            if result:
                logger.info("paper_account_reset", 
                           message="All positions closed and orders cancelled")
            
            return result
            
        except Exception as e:
            logger.error("reset_paper_account_failed", error=str(e))
            return False

