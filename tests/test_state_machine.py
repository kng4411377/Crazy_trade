"""Tests for symbol state machine."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.config import BotConfig
from src.database import DatabaseManager
from src.state_machine import SymbolStateMachine, SymbolStatus


@pytest.fixture
def config():
    """Create test configuration."""
    return BotConfig(
        alpaca={"api_key": "test_key", "secret_key": "test_secret"},
        mode="paper",
        watchlist=["TSLA"],
        cooldowns={"after_stopout_minutes": 20},
    )


@pytest.fixture
def db_manager():
    """Create test database manager."""
    db = DatabaseManager("sqlite:///:memory:")
    db.create_tables()
    return db


@pytest.fixture
def mock_alpaca_client():
    """Create mock Alpaca client."""
    client = Mock()
    client.get_positions = Mock(return_value={})
    client.get_open_orders = Mock(return_value=[])
    client.get_last_price = AsyncMock(return_value=100.0)
    client.place_entry_with_trailing_stop = AsyncMock(return_value=(None, None))
    client.place_trailing_stop = AsyncMock(return_value=None)
    client.cancel_order = AsyncMock()
    return client


@pytest.fixture
def mock_sizer():
    """Create mock position sizer."""
    sizer = Mock()
    sizer.calculate_quantity = Mock(return_value=10)
    return sizer


@pytest.fixture
def state_machine(config, mock_alpaca_client, db_manager, mock_sizer):
    """Create state machine for testing."""
    return SymbolStateMachine(
        "TSLA",
        config,
        mock_alpaca_client,
        db_manager,
        mock_sizer,
    )


def test_state_machine_initialization(state_machine):
    """Test state machine initialization."""
    assert state_machine.symbol == "TSLA"
    assert state_machine.config is not None


def test_get_status_no_position(state_machine, mock_alpaca_client):
    """Test status detection when no position exists."""
    mock_alpaca_client.get_positions.return_value = {}
    mock_alpaca_client.get_open_orders.return_value = []
    
    status = state_machine.get_status()
    assert status == SymbolStatus.NO_POSITION


def test_get_status_position_open(state_machine, mock_alpaca_client):
    """Test status detection when position is open."""
    mock_alpaca_client.get_positions.return_value = {
        "TSLA": {"quantity": 10, "avg_cost": 250.0, "market_value": 2500}
    }
    
    status = state_machine.get_status()
    assert status == SymbolStatus.POSITION_OPEN


def test_get_status_entry_pending(state_machine, mock_alpaca_client):
    """Test status detection when entry order is pending."""
    mock_order = Mock()
    mock_order.contract.symbol = "TSLA"
    mock_order.order.action = "BUY"
    mock_order.orderStatus.status = "Submitted"
    
    mock_alpaca_client.get_positions.return_value = {}
    mock_alpaca_client.get_open_orders.return_value = [mock_order]
    
    status = state_machine.get_status()
    assert status == SymbolStatus.ENTRY_PENDING


def test_get_status_cooldown(state_machine, db_manager):
    """Test status detection when in cooldown."""
    # Set cooldown until future time
    future_time = datetime.utcnow() + timedelta(minutes=10)
    with db_manager.get_session() as session:
        db_manager.upsert_symbol_state(
            session,
            "TSLA",
            cooldown_until_ts=future_time,
        )
    
    status = state_machine.get_status()
    assert status == SymbolStatus.COOLDOWN


def test_get_status_cooldown_expired(state_machine, db_manager, mock_alpaca_client):
    """Test status when cooldown has expired."""
    # Set cooldown to past time
    past_time = datetime.utcnow() - timedelta(minutes=10)
    with db_manager.get_session() as session:
        db_manager.upsert_symbol_state(
            session,
            "TSLA",
            cooldown_until_ts=past_time,
        )
    
    mock_alpaca_client.get_positions.return_value = {}
    mock_alpaca_client.get_open_orders.return_value = []
    
    status = state_machine.get_status()
    assert status == SymbolStatus.NO_POSITION  # Cooldown expired


@pytest.mark.asyncio
async def test_handle_no_position_places_order(state_machine, mock_alpaca_client):
    """Test that NO_POSITION state places entry order."""
    # Mock successful order placement
    mock_parent = Mock()
    mock_parent.order.orderId = 1001
    mock_parent.order.orderType = "STP"
    mock_parent.order.auxPrice = 105.0
    
    mock_child = Mock()
    mock_child.order.orderId = 1002
    mock_child.order.orderType = "TRAIL"
    mock_child.order.trailingPercent = 10.0
    
    mock_alpaca_client.place_entry_with_trailing_stop.return_value = (mock_parent, mock_child)
    
    await state_machine.process({}, 50000)
    
    # Verify order was placed
    mock_alpaca_client.place_entry_with_trailing_stop.assert_called_once()


@pytest.mark.asyncio
async def test_handle_position_open_missing_stop(state_machine, mock_alpaca_client):
    """Test that missing trailing stop is recreated."""
    # Position exists but no trailing stop
    mock_alpaca_client.get_positions.return_value = {
        "TSLA": {"quantity": 10, "avg_cost": 250.0, "market_value": 2500}
    }
    mock_alpaca_client.get_open_orders.return_value = []
    
    mock_trade = Mock()
    mock_trade.order.orderId = 2001
    mock_alpaca_client.place_trailing_stop.return_value = mock_trade
    
    await state_machine.process({}, 50000)
    
    # Verify trailing stop was created
    mock_alpaca_client.place_trailing_stop.assert_called_once_with("TSLA", 10, 100.0)


@pytest.mark.asyncio
async def test_handle_position_open_duplicate_stops(state_machine, mock_alpaca_client):
    """Test that duplicate trailing stops are cancelled."""
    # Position with multiple trailing stops
    mock_alpaca_client.get_positions.return_value = {
        "TSLA": {"quantity": 10, "avg_cost": 250.0, "market_value": 2500}
    }
    
    mock_stop1 = Mock()
    mock_stop1.contract.symbol = "TSLA"
    mock_stop1.order.action = "SELL"
    mock_stop1.order.orderType = "TRAIL"
    mock_stop1.order.totalQuantity = 10
    
    mock_stop2 = Mock()
    mock_stop2.contract.symbol = "TSLA"
    mock_stop2.order.action = "SELL"
    mock_stop2.order.orderType = "TRAIL"
    mock_stop2.order.totalQuantity = 10
    
    mock_alpaca_client.get_open_orders.return_value = [mock_stop1, mock_stop2]
    
    await state_machine.process({}, 50000)
    
    # Verify duplicate was cancelled (should cancel the second one)
    mock_alpaca_client.cancel_order.assert_called_once_with(mock_stop2)


@pytest.mark.asyncio
async def test_handle_position_open_qty_mismatch(state_machine, mock_alpaca_client):
    """Test that stop with wrong quantity is replaced."""
    # Position with 10 shares but stop for 5 shares
    mock_alpaca_client.get_positions.return_value = {
        "TSLA": {"quantity": 10, "avg_cost": 250.0, "market_value": 2500}
    }
    
    mock_stop = Mock()
    mock_stop.contract.symbol = "TSLA"
    mock_stop.order.action = "SELL"
    mock_stop.order.orderType = "TRAIL"
    mock_stop.order.totalQuantity = 5  # Wrong quantity
    
    mock_alpaca_client.get_open_orders.return_value = [mock_stop]
    
    mock_new_trade = Mock()
    mock_new_trade.order.orderId = 3001
    mock_alpaca_client.place_trailing_stop.return_value = mock_new_trade
    
    await state_machine.process({}, 50000)
    
    # Verify old stop was cancelled and new one created
    mock_alpaca_client.cancel_order.assert_called_once_with(mock_stop)
    mock_alpaca_client.place_trailing_stop.assert_called_once_with("TSLA", 10, 100.0)


def test_on_stop_out_enters_cooldown(state_machine, db_manager, config):
    """Test that stop-out triggers cooldown period."""
    state_machine.on_stop_out()
    
    # Check that cooldown was set
    with db_manager.get_session() as session:
        state = db_manager.get_symbol_state(session, "TSLA")
        assert state is not None
        assert state.cooldown_until_ts is not None
        
        # Cooldown should be ~20 minutes in the future
        cooldown_delta = state.cooldown_until_ts - datetime.utcnow()
        assert cooldown_delta.total_seconds() > 19 * 60  # At least 19 minutes
        assert cooldown_delta.total_seconds() < 21 * 60  # At most 21 minutes


@pytest.mark.asyncio
async def test_cancel_unfilled_entries(state_machine, mock_alpaca_client):
    """Test cancelling unfilled entry orders."""
    # Create mock pending entry order
    mock_entry = Mock()
    mock_entry.contract.symbol = "TSLA"
    mock_entry.order.action = "BUY"
    mock_entry.orderStatus.status = "Submitted"
    mock_entry.order.orderId = 1001
    
    mock_alpaca_client.get_open_orders.return_value = [mock_entry]
    
    await state_machine.cancel_unfilled_entries()
    
    # Verify order was cancelled
    mock_alpaca_client.cancel_order.assert_called_once_with(mock_entry)


@pytest.mark.asyncio
async def test_cooldown_prevents_new_entry(state_machine, db_manager, mock_alpaca_client):
    """Test that cooldown prevents creating new entry orders."""
    # Set active cooldown
    future_time = datetime.utcnow() + timedelta(minutes=10)
    with db_manager.get_session() as session:
        db_manager.upsert_symbol_state(
            session,
            "TSLA",
            cooldown_until_ts=future_time,
        )
    
    # Try to process (should not place order)
    await state_machine.process({}, 50000)
    
    # Verify no order was placed
    mock_alpaca_client.place_entry_with_trailing_stop.assert_not_called()

