"""Tests for API server endpoints."""

import pytest
import json
from datetime import datetime, timedelta

from src.database import DatabaseManager, OrderRecord, FillRecord, EventRecord, SymbolState


@pytest.fixture
def api_db():
    """Create in-memory test database for API tests."""
    db = DatabaseManager("sqlite:///:memory:")
    db.create_tables()
    return db


@pytest.fixture
def api_client(api_db):
    """Create Flask test client."""
    # Import here to avoid loading the module-level db
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # Import api_server and override the db
    import api_server
    api_server.db = api_db
    api_server.tracker = api_server.PerformanceTracker(api_db)
    
    api_server.app.config['TESTING'] = True
    with api_server.app.test_client() as client:
        yield client


def test_health_endpoint(api_client):
    """Test /health endpoint."""
    response = api_client.get('/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'timestamp' in data
    assert data['database'] == 'connected'


def test_index_endpoint(api_client):
    """Test / endpoint returns API documentation."""
    response = api_client.get('/')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['name'] == 'Crazy Trade Bot API'
    assert 'endpoints' in data
    assert '/health' in data['endpoints']
    assert '/status' in data['endpoints']
    assert '/orders' in data['endpoints']


def test_tickle_endpoint(api_client):
    """Test /v1/api/tickle keep-alive endpoint."""
    response = api_client.post('/v1/api/tickle', 
                               data=json.dumps({}),
                               content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert 'timestamp' in data


def test_status_endpoint(api_client, api_db):
    """Test /status endpoint."""
    # Add some test data
    with api_db.get_session() as session:
        api_db.upsert_symbol_state(session, "TSLA", last_parent_id=1001)
        api_db.add_order(
            session,
            order_id=1001,
            symbol="TSLA",
            side="BUY",
            order_type="STP",
            status="Submitted",
            qty=10,
        )
        api_db.add_event(
            session,
            event_type="bot_started",
            symbol=None,
            payload={}
        )
    
    response = api_client.get('/status')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'timestamp' in data
    assert 'symbols' in data
    assert len(data['symbols']) == 1
    assert data['symbols'][0]['symbol'] == 'TSLA'
    assert data['active_orders'] == 1
    assert data['last_event']['type'] == 'bot_started'


def test_orders_endpoint_default(api_client, api_db):
    """Test /orders endpoint with default parameters (active only)."""
    with api_db.get_session() as session:
        # Add various orders
        api_db.add_order(session, order_id=1, symbol="TSLA", side="BUY",
                        order_type="STP", status="Submitted", qty=10)
        api_db.add_order(session, order_id=2, symbol="NVDA", side="BUY",
                        order_type="STP", status="PreSubmitted", qty=5)
        api_db.add_order(session, order_id=3, symbol="TSLA", side="SELL",
                        order_type="TRAIL", status="Filled", qty=10)
        api_db.add_order(session, order_id=4, symbol="AAPL", side="BUY",
                        order_type="STP", status="Cancelled", qty=20)
    
    response = api_client.get('/orders')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['count'] == 2  # Only Submitted and PreSubmitted
    assert data['status_filter'] == 'active'
    assert all(o['status'] in ['Submitted', 'PreSubmitted', 'PendingSubmit'] 
               for o in data['orders'])


def test_orders_endpoint_all_with_limit(api_client, api_db):
    """Test /orders endpoint with status=all and limit."""
    with api_db.get_session() as session:
        # Add many orders
        for i in range(1, 51):
            status = 'Filled' if i % 2 == 0 else 'Submitted'
            api_db.add_order(
                session,
                order_id=i,
                symbol="TSLA",
                side="BUY",
                order_type="STP",
                status=status,
                qty=10
            )
    
    response = api_client.get('/orders?status=all&limit=20')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['count'] == 20  # Limited to 20
    assert data['status_filter'] == 'all'
    # Should be sorted by created_at desc (most recent first)
    assert data['orders'][0]['order_id'] > data['orders'][-1]['order_id']


def test_orders_endpoint_filtered_by_status(api_client, api_db):
    """Test /orders endpoint filtered by specific status."""
    with api_db.get_session() as session:
        # Add orders with different statuses
        for i in range(1, 11):
            if i <= 3:
                status = 'Filled'
            elif i <= 6:
                status = 'Cancelled'
            else:
                status = 'Submitted'
            
            api_db.add_order(
                session,
                order_id=i,
                symbol="TSLA",
                side="BUY",
                order_type="STP",
                status=status,
                qty=10
            )
    
    # Test Filled orders
    response = api_client.get('/orders?status=Filled&limit=10')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['count'] == 3
    assert all(o['status'] == 'Filled' for o in data['orders'])
    
    # Test Cancelled orders
    response = api_client.get('/orders?status=Cancelled&limit=10')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['count'] == 3
    assert all(o['status'] == 'Cancelled' for o in data['orders'])


def test_orders_endpoint_limit_cap(api_client, api_db):
    """Test that /orders endpoint respects 200 limit cap."""
    with api_db.get_session() as session:
        # Add 250 orders
        for i in range(1, 251):
            api_db.add_order(
                session,
                order_id=i,
                symbol="TSLA",
                side="BUY",
                order_type="STP",
                status="Filled",
                qty=10
            )
    
    # Request 500 but should be capped at 200
    response = api_client.get('/orders?status=all&limit=500')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['count'] == 200  # Capped at 200


def test_fills_endpoint(api_client, api_db):
    """Test /fills endpoint."""
    with api_db.get_session() as session:
        # Add test fills
        for i in range(1, 6):
            api_db.add_fill(
                session,
                exec_id=f"exec_{i}",
                symbol="TSLA",
                side="BUY",
                qty=10,
                price=250.0 + i,
                order_id=i
            )
    
    response = api_client.get('/fills?limit=5')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['count'] == 5
    assert 'fills' in data


def test_events_endpoint(api_client, api_db):
    """Test /events endpoint."""
    with api_db.get_session() as session:
        # Add test events
        api_db.add_event(session, "bot_started", None, {})
        api_db.add_event(session, "entry_order_placed", "TSLA", {"order_id": 1})
    
    response = api_client.get('/events?limit=10')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['count'] == 2
    assert 'events' in data


def test_performance_endpoint_no_trades(api_client):
    """Test /performance endpoint with no trades."""
    response = api_client.get('/performance')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'message' in data or 'overall' in data


def test_daily_endpoint(api_client, api_db):
    """Test /daily endpoint."""
    response = api_client.get('/daily?days=7')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'timestamp' in data
    assert 'days' in data
    assert 'daily_pnl' in data


def test_reset_endpoint(api_client):
    """Test /reset endpoint returns instructions."""
    response = api_client.post('/reset')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'message' in data
    assert 'instructions' in data


def test_close_all_endpoint(api_client):
    """Test /admin/close_all endpoint returns instructions."""
    response = api_client.post('/admin/close_all')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'message' in data
    assert 'instructions' in data


def test_orders_response_fields(api_client, api_db):
    """Test that /orders response includes all required fields."""
    with api_db.get_session() as session:
        api_db.add_order(
            session,
            order_id=1001,
            symbol="TSLA",
            side="BUY",
            order_type="STP",
            status="Submitted",
            qty=10,
            stop_price=250.0,
            limit_price=None,
            trailing_pct=None,
            parent_id=None
        )
    
    response = api_client.get('/orders')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert len(data['orders']) == 1
    
    order = data['orders'][0]
    required_fields = [
        'order_id', 'symbol', 'side', 'order_type', 'quantity',
        'status', 'stop_price', 'limit_price', 'trailing_pct',
        'parent_id', 'created_at'
    ]
    for field in required_fields:
        assert field in order, f"Missing required field: {field}"
    
    assert order['order_id'] == 1001
    assert order['symbol'] == 'TSLA'
    assert order['quantity'] == 10


def test_invalid_endpoint(api_client):
    """Test that invalid endpoints return 404."""
    response = api_client.get('/invalid_endpoint')
    assert response.status_code == 404

