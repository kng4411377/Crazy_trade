"""Integration tests for end-to-end scenarios."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.config import BotConfig
from src.database import DatabaseManager
from src.state_machine import SymbolStateMachine, SymbolStatus
from src.sizing import PositionSizer


@pytest.mark.integration
class TestGapUpScenario:
    """Test gap-up through stop scenario."""
    
    @pytest.mark.asyncio
    async def test_gap_up_fills_entry_creates_trailing_stop(self, test_config, test_db):
        """
        Simulate: Stock gaps up through entry stop at market open.
        Expected: Entry fills, trailing stop is active.
        """
        # Setup mocks
        mock_alpaca = Mock()
        mock_alpaca.get_positions = Mock(return_value={})
        mock_alpaca.get_open_orders = Mock(return_value=[])
        mock_alpaca.get_last_price = AsyncMock(return_value=100.0)
        
        # Mock successful entry with trailing stop
        mock_parent = Mock()
        mock_parent.order.id = 1001
        mock_parent.order.type = Mock(value="STP")  # Nested Mock for type.value
        mock_parent.order.status = Mock(value="Submitted")  # Nested Mock for status.value
        mock_parent.order.orderType = "STP"
        mock_parent.order.auxPrice = 105.0
        mock_parent.order.stop_price = 105.0
        mock_parent.order.limit_price = None
        mock_parent.order.trailing_percent = None
        
        mock_child = Mock()
        mock_child.order.id = 1002  # Use .id, not .orderId
        mock_child.order.orderType = "TRAIL"
        mock_child.order.trailingPercent = 10.0
        
        mock_alpaca.place_entry_with_trailing_stop = AsyncMock(
            return_value=(mock_parent, mock_child)
        )
        
        sizer = PositionSizer(test_config)
        sm = SymbolStateMachine("TSLA", test_config, mock_alpaca, test_db, sizer)
        
        # Initial state: no position
        status = sm.get_status()
        assert status == SymbolStatus.NO_POSITION
        
        # Process - should create entry
        await sm.process({}, 50000)
        mock_alpaca.place_entry_with_trailing_stop.assert_called_once()
        
        # Simulate entry fill - position now exists
        mock_alpaca.get_positions.return_value = {
            "TSLA": {"quantity": 10, "avg_cost": 105.0, "market_value": 1050}
        }
        
        # Simulate trailing stop exists
        mock_stop = Mock()
        mock_stop.contract.symbol = "TSLA"
        mock_stop.order.action = "SELL"
        mock_stop.order.side = Mock(value="SELL")
        mock_stop.order.type = Mock(value="trailing_stop")
        mock_stop.order.orderType = "TRAIL"
        mock_stop.order.totalQuantity = 10
        mock_stop.order.qty = 10.0
        mock_stop.order.id = 2001
        mock_alpaca.get_open_orders.return_value = [mock_stop]
        # Mock place_trailing_stop in case it's needed
        mock_alpaca.place_trailing_stop = AsyncMock(return_value=mock_stop)
        
        # Process again - should verify stop is healthy
        await sm.process({}, 50000)
        
        # Status should be POSITION_OPEN
        status = sm.get_status()
        assert status == SymbolStatus.POSITION_OPEN


@pytest.mark.integration
class TestTrailingStopScenario:
    """Test trailing stop trigger scenario."""
    
    @pytest.mark.asyncio
    async def test_trailing_stop_triggers_cooldown(self, test_config, test_db):
        """
        Simulate: Position exists, trailing stop triggers.
        Expected: Cooldown period starts, no new entries for N minutes.
        """
        mock_alpaca = Mock()
        mock_alpaca.get_positions = Mock(return_value={})
        mock_alpaca.get_open_orders = Mock(return_value=[])
        mock_alpaca.get_last_price = AsyncMock(return_value=100.0)
        mock_alpaca.place_entry_with_trailing_stop = AsyncMock(return_value=(None, None))
        
        sizer = PositionSizer(test_config)
        sm = SymbolStateMachine("TSLA", test_config, mock_alpaca, test_db, sizer)
        
        # Trigger stop-out
        sm.on_stop_out()
        
        # Status should be COOLDOWN
        status = sm.get_status()
        assert status == SymbolStatus.COOLDOWN
        
        # Try to process - should not place order
        await sm.process({}, 50000)
        mock_alpaca.place_entry_with_trailing_stop.assert_not_called()
        
        # Verify cooldown in database
        with test_db.get_session() as session:
            state = test_db.get_symbol_state(session, "TSLA")
            assert state.cooldown_until_ts is not None
            assert state.cooldown_until_ts > datetime.utcnow()


@pytest.mark.integration
class TestCooldownScenario:
    """Test cooldown behavior."""
    
    @pytest.mark.asyncio
    async def test_cooldown_prevents_entry_then_allows(self, test_config, test_db):
        """
        Simulate: After stop-out, cooldown prevents entry, then expires.
        Expected: No entry during cooldown, entry allowed after expiration.
        """
        mock_alpaca = Mock()
        mock_alpaca.get_positions = Mock(return_value={})
        mock_alpaca.get_open_orders = Mock(return_value=[])
        mock_alpaca.get_last_price = AsyncMock(return_value=100.0)
        
        mock_parent = Mock()
        mock_parent.order.id = 1001
        mock_parent.order.type = Mock(value="STP")  # Nested Mock for type.value
        mock_parent.order.status = Mock(value="Submitted")  # Nested Mock for status.value
        mock_parent.order.orderType = "STP"
        mock_parent.order.auxPrice = 105.0
        mock_parent.order.stop_price = 105.0
        mock_parent.order.limit_price = None
        mock_parent.order.trailing_percent = None
        
        mock_child = Mock()
        mock_child.order.id = 1002
        mock_child.order.type = Mock(value="TRAIL")
        mock_child.order.status = Mock(value="Submitted")
        mock_child.order.orderType = "TRAIL"
        mock_child.order.trailingPercent = 10.0
        mock_child.order.stop_price = None
        mock_child.order.limit_price = None
        mock_child.order.trailing_percent = 10.0
        
        mock_alpaca.place_entry_with_trailing_stop = AsyncMock(
            return_value=(mock_parent, mock_child)
        )
        
        sizer = PositionSizer(test_config)
        sm = SymbolStateMachine("TSLA", test_config, mock_alpaca, test_db, sizer)
        
        # Set cooldown (10 minutes remaining)
        cooldown_until = datetime.utcnow() + timedelta(minutes=10)
        with test_db.get_session() as session:
            test_db.upsert_symbol_state(session, "TSLA", cooldown_until_ts=cooldown_until)
        
        # Try to process - should not place order
        await sm.process({}, 50000)
        mock_alpaca.place_entry_with_trailing_stop.assert_not_called()
        
        # Expire cooldown
        with test_db.get_session() as session:
            past_time = datetime.utcnow() - timedelta(minutes=1)
            test_db.upsert_symbol_state(session, "TSLA", cooldown_until_ts=past_time)
        
        # Try again - should place order now
        await sm.process({}, 50000)
        mock_alpaca.place_entry_with_trailing_stop.assert_called_once()


@pytest.mark.integration
class TestDuplicateStopScenario:
    """Test duplicate stop detection and cleanup."""
    
    @pytest.mark.asyncio
    async def test_duplicate_stops_are_cancelled(self, test_config, test_db):
        """
        Simulate: Position has multiple trailing stops.
        Expected: Keeps one, cancels duplicates.
        """
        mock_alpaca = Mock()
        mock_alpaca.get_positions = Mock(return_value={
            "TSLA": {"quantity": 10, "avg_cost": 250.0, "market_value": 2500}
        })
        mock_alpaca.get_last_price = AsyncMock(return_value=100.0)
        mock_alpaca.cancel_order = AsyncMock()
        
        # Create duplicate stops
        mock_stop1 = Mock()
        mock_stop1.contract.symbol = "TSLA"
        mock_stop1.order.action = "SELL"
        mock_stop1.order.side = Mock(value="SELL")  # Add side.value
        mock_stop1.order.type = Mock(value="trailing_stop")  # Add type.value
        mock_stop1.order.orderType = "TRAIL"
        mock_stop1.order.totalQuantity = 10
        mock_stop1.order.qty = 10.0  # Add qty
        mock_stop1.order.id = 2001
        
        mock_stop2 = Mock()
        mock_stop2.contract.symbol = "TSLA"
        mock_stop2.order.action = "SELL"
        mock_stop2.order.side = Mock(value="SELL")
        mock_stop2.order.type = Mock(value="trailing_stop")
        mock_stop2.order.orderType = "TRAIL"
        mock_stop2.order.totalQuantity = 10
        mock_stop2.order.qty = 10.0
        mock_stop2.order.id = 2002
        
        mock_stop3 = Mock()
        mock_stop3.contract.symbol = "TSLA"
        mock_stop3.order.action = "SELL"
        mock_stop3.order.side = Mock(value="SELL")
        mock_stop3.order.type = Mock(value="trailing_stop")
        mock_stop3.order.orderType = "TRAIL"
        mock_stop3.order.totalQuantity = 10
        mock_stop3.order.qty = 10.0
        mock_stop3.order.id = 2003
        
        mock_alpaca.get_open_orders = Mock(return_value=[mock_stop1, mock_stop2, mock_stop3])
        
        # Mock place_trailing_stop to return AsyncMock properly
        mock_trailing_stop = Mock()
        mock_trailing_stop.order.id = 2001
        mock_alpaca.place_trailing_stop = AsyncMock(return_value=mock_trailing_stop)
        
        sizer = PositionSizer(test_config)
        sm = SymbolStateMachine("TSLA", test_config, mock_alpaca, test_db, sizer)
        
        # Process - should cancel duplicates
        await sm.process({}, 50000)
        
        # Should have cancelled 2 orders (keeping the first one)
        assert mock_alpaca.cancel_order.call_count == 2
        mock_alpaca.cancel_order.assert_any_call(mock_stop2)
        mock_alpaca.cancel_order.assert_any_call(mock_stop3)


@pytest.mark.integration
class TestRTHGatingScenario:
    """Test RTH (Regular Trading Hours) gating."""
    
    def test_orders_set_outside_rth_false(self, test_config):
        """
        Verify that orders are configured with outsideRth=False.
        This is tested in the config and order creation logic.
        """
        assert test_config.hours.allow_pre_market is False
        assert test_config.hours.allow_after_hours is False
        
        # The Alpaca client should respect market hours on all orders
        # This is verified in the order creation code


@pytest.mark.integration
class TestEODCancellation:
    """Test end-of-day order cancellation."""
    
    @pytest.mark.asyncio
    async def test_unfilled_entries_cancelled_at_close(self, test_config, test_db):
        """
        Simulate: Unfilled entry orders at end of day.
        Expected: Orders are cancelled before market close.
        """
        mock_alpaca = Mock()
        mock_alpaca.cancel_order = AsyncMock()
        
        # Mock pending entry order
        mock_entry = Mock()
        mock_entry.contract.symbol = "TSLA"
        mock_entry.order.action = "BUY"
        mock_entry.order.side = Mock(value="BUY")  # Add side.value
        mock_entry.orderStatus.status = "accepted"  # Use valid status
        mock_entry.order.id = 1001
        
        mock_alpaca.get_open_orders = Mock(return_value=[mock_entry])
        
        sizer = PositionSizer(test_config)
        sm = SymbolStateMachine("TSLA", test_config, mock_alpaca, test_db, sizer)
        
        # Cancel unfilled entries
        await sm.cancel_unfilled_entries()
        
        # Verify cancellation
        mock_alpaca.cancel_order.assert_called_once_with(mock_entry)
        
        # Verify event logged
        from src.database import EventRecord
        with test_db.get_session() as session:
            events = session.query(EventRecord).filter_by(
                event_type="entry_cancelled_eod"
            ).all()
            assert len(events) >= 1  # At least one cancellation event


@pytest.mark.integration
class TestPositionSizingIntegration:
    """Test position sizing with exposure limits."""
    
    @pytest.mark.asyncio
    async def test_sizing_respects_total_exposure_limit(self, test_config, test_db):
        """
        Simulate: Portfolio near max exposure.
        Expected: New positions rejected or sized down.
        """
        mock_alpaca = Mock()
        mock_alpaca.get_positions = Mock(return_value={})
        mock_alpaca.get_open_orders = Mock(return_value=[])
        mock_alpaca.get_last_price = AsyncMock(return_value=100.0)
        mock_alpaca.place_entry_with_trailing_stop = AsyncMock(return_value=(None, None))
        
        sizer = PositionSizer(test_config)
        
        # Already have $19,500 in positions (near $20,000 limit)
        existing_positions = {"AAPL": 10000, "MSFT": 9500}
        
        # Try to size new position
        qty = sizer.calculate_quantity("TSLA", 100.0, existing_positions, 50000)
        
        # Should be rejected (returns 0)
        assert qty == 0

