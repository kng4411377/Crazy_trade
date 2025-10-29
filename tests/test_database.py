"""Tests for database operations."""

import pytest
from datetime import datetime

from src.database import DatabaseManager, SymbolState, OrderRecord, FillRecord, EventRecord


@pytest.fixture
def db():
    """Create in-memory test database."""
    db = DatabaseManager("sqlite:///:memory:")
    db.create_tables()
    return db


def test_create_tables(db):
    """Test that tables are created successfully."""
    # Should not raise any exceptions
    assert db.engine is not None
    assert db.SessionLocal is not None


def test_upsert_symbol_state(db):
    """Test inserting and updating symbol state."""
    with db.get_session() as session:
        # Insert new state
        state = db.upsert_symbol_state(session, "TSLA", last_parent_id=1001)
        assert state.symbol == "TSLA"
        assert state.last_parent_id == 1001
        
        # Update existing state
        state = db.upsert_symbol_state(session, "TSLA", last_trail_id=1002)
        assert state.last_parent_id == 1001  # Preserved
        assert state.last_trail_id == 1002  # Updated


def test_get_symbol_state(db):
    """Test retrieving symbol state."""
    with db.get_session() as session:
        # Non-existent state
        state = db.get_symbol_state(session, "NVDA")
        assert state is None
        
        # Create state
        db.upsert_symbol_state(session, "NVDA", last_parent_id=2001)
        
        # Retrieve state
        state = db.get_symbol_state(session, "NVDA")
        assert state is not None
        assert state.symbol == "NVDA"
        assert state.last_parent_id == 2001


def test_add_order(db):
    """Test adding order records."""
    with db.get_session() as session:
        order = db.add_order(
            session,
            order_id=1001,
            symbol="TSLA",
            side="BUY",
            order_type="STP",
            status="Submitted",
            qty=10,
            stop_price=105.0,
        )
        
        assert order.id is not None
        assert order.order_id == 1001
        assert order.symbol == "TSLA"
        assert order.side == "BUY"
        assert order.qty == 10


def test_update_order_status(db):
    """Test updating order status."""
    with db.get_session() as session:
        # Create order
        order = db.add_order(
            session,
            order_id=1001,
            symbol="TSLA",
            side="BUY",
            order_type="STP",
            status="Submitted",
            qty=10,
        )
        
        # Update status
        db.update_order_status(session, 1001, "Filled")
        
        # Verify
        updated_order = session.query(OrderRecord).filter(
            OrderRecord.order_id == 1001
        ).first()
        assert updated_order.status == "Filled"


def test_add_fill(db):
    """Test adding fill records."""
    with db.get_session() as session:
        fill = db.add_fill(
            session,
            exec_id="12345.01",
            symbol="TSLA",
            side="BUY",
            qty=10,
            price=252.50,
            order_id=1001,
        )
        
        assert fill.exec_id == "12345.01"
        assert fill.symbol == "TSLA"
        assert fill.qty == 10
        assert fill.price == 252.50


def test_add_event(db):
    """Test adding event records."""
    with db.get_session() as session:
        event = db.add_event(
            session,
            event_type="entry_order_placed",
            symbol="TSLA",
            payload={"order_id": 1001, "qty": 10},
        )
        
        assert event.id is not None
        assert event.event_type == "entry_order_placed"
        assert event.symbol == "TSLA"
        assert event.payload_json["order_id"] == 1001


def test_get_recent_fills(db):
    """Test retrieving recent fills."""
    with db.get_session() as session:
        # Add multiple fills
        db.add_fill(session, exec_id="1", symbol="TSLA", side="BUY", qty=10, price=250, order_id=1)
        db.add_fill(session, exec_id="2", symbol="TSLA", side="SELL", qty=10, price=260, order_id=2)
        db.add_fill(session, exec_id="3", symbol="NVDA", side="BUY", qty=5, price=500, order_id=3)
        
        # Get TSLA fills
        fills = db.get_recent_fills(session, "TSLA", limit=10)
        assert len(fills) == 2
        assert all(f.symbol == "TSLA" for f in fills)


def test_get_active_orders(db):
    """Test retrieving active orders."""
    with db.get_session() as session:
        # Add orders with different statuses
        db.add_order(session, order_id=1, symbol="TSLA", side="BUY", 
                    order_type="STP", status="Submitted", qty=10)
        db.add_order(session, order_id=2, symbol="TSLA", side="SELL", 
                    order_type="TRAIL", status="Filled", qty=10)
        db.add_order(session, order_id=3, symbol="NVDA", side="BUY", 
                    order_type="STP", status="PreSubmitted", qty=5)
        
        # Get all active orders
        active = db.get_active_orders(session)
        assert len(active) == 2  # Only Submitted and PreSubmitted
        
        # Get active for specific symbol
        active_tsla = db.get_active_orders(session, "TSLA")
        assert len(active_tsla) == 1
        assert active_tsla[0].symbol == "TSLA"


def test_cooldown_timestamp(db):
    """Test storing and retrieving cooldown timestamps."""
    with db.get_session() as session:
        future_time = datetime(2024, 12, 31, 23, 59, 59)
        
        db.upsert_symbol_state(
            session,
            "TSLA",
            cooldown_until_ts=future_time,
        )
        
        state = db.get_symbol_state(session, "TSLA")
        assert state.cooldown_until_ts == future_time


def test_case_insensitive_symbol(db):
    """Test that symbols are normalized to uppercase."""
    with db.get_session() as session:
        # Insert with lowercase
        db.upsert_symbol_state(session, "tsla", last_parent_id=1001)
        
        # Retrieve with uppercase
        state = db.get_symbol_state(session, "TSLA")
        assert state is not None
        assert state.symbol == "TSLA"

