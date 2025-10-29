"""Tests for performance tracking."""

import pytest
from datetime import datetime, timedelta

from src.database import DatabaseManager
from src.performance import PerformanceTracker


@pytest.fixture
def db():
    """Create in-memory test database."""
    db = DatabaseManager("sqlite:///:memory:")
    db.create_tables()
    return db


@pytest.fixture
def tracker(db):
    """Create performance tracker."""
    return PerformanceTracker(db)


def test_calculate_closed_trades_empty(tracker, db):
    """Test with no trades."""
    with db.get_session() as session:
        trades = tracker.calculate_closed_trades(session)
        assert trades == []


def test_calculate_closed_trades_single_round_trip(tracker, db):
    """Test single buy-sell round trip."""
    with db.get_session() as session:
        # Add buy fill
        db.add_fill(
            session,
            exec_id="1",
            symbol="TSLA",
            side="BUY",
            qty=10,
            price=250.0,
            order_id=1001,
        )
        
        # Add sell fill
        db.add_fill(
            session,
            exec_id="2",
            symbol="TSLA",
            side="SELL",
            qty=10,
            price=275.0,
            order_id=1002,
        )
        
        trades = tracker.calculate_closed_trades(session)
        
        assert len(trades) == 1
        assert trades[0]['symbol'] == 'TSLA'
        assert trades[0]['entry_price'] == 250.0
        assert trades[0]['exit_price'] == 275.0
        assert trades[0]['qty'] == 10
        assert trades[0]['pnl'] == 250.0  # (275 - 250) * 10
        assert trades[0]['pnl_pct'] == pytest.approx(10.0)
        assert trades[0]['trade_type'] == 'long'


def test_calculate_closed_trades_multiple_symbols(tracker, db):
    """Test trades across multiple symbols."""
    with db.get_session() as session:
        # TSLA trade
        db.add_fill(session, exec_id="1", symbol="TSLA", side="BUY", qty=10, price=250.0, order_id=1)
        db.add_fill(session, exec_id="2", symbol="TSLA", side="SELL", qty=10, price=260.0, order_id=2)
        
        # NVDA trade
        db.add_fill(session, exec_id="3", symbol="NVDA", side="BUY", qty=5, price=500.0, order_id=3)
        db.add_fill(session, exec_id="4", symbol="NVDA", side="SELL", qty=5, price=490.0, order_id=4)
        
        trades = tracker.calculate_closed_trades(session)
        
        assert len(trades) == 2
        symbols = {t['symbol'] for t in trades}
        assert symbols == {'TSLA', 'NVDA'}
        
        # Check TSLA trade
        tsla_trade = [t for t in trades if t['symbol'] == 'TSLA'][0]
        assert tsla_trade['pnl'] == 100.0  # (260 - 250) * 10
        
        # Check NVDA trade
        nvda_trade = [t for t in trades if t['symbol'] == 'NVDA'][0]
        assert nvda_trade['pnl'] == -50.0  # (490 - 500) * 5


def test_calculate_trade_statistics(tracker, db):
    """Test trade statistics calculation."""
    with db.get_session() as session:
        # Add some winning and losing trades
        # Win 1: TSLA
        db.add_fill(session, exec_id="1", symbol="TSLA", side="BUY", qty=10, price=250.0, order_id=1)
        db.add_fill(session, exec_id="2", symbol="TSLA", side="SELL", qty=10, price=275.0, order_id=2)
        
        # Win 2: NVDA
        db.add_fill(session, exec_id="3", symbol="NVDA", side="BUY", qty=5, price=500.0, order_id=3)
        db.add_fill(session, exec_id="4", symbol="NVDA", side="SELL", qty=5, price=550.0, order_id=4)
        
        # Loss 1: AAPL
        db.add_fill(session, exec_id="5", symbol="AAPL", side="BUY", qty=20, price=150.0, order_id=5)
        db.add_fill(session, exec_id="6", symbol="AAPL", side="SELL", qty=20, price=140.0, order_id=6)
        
        stats = tracker.calculate_trade_statistics(session)
        
        assert stats['total_trades'] == 3
        assert stats['winning_trades'] == 2
        assert stats['losing_trades'] == 1
        assert stats['win_rate'] == pytest.approx(66.67, rel=0.1)
        
        # Total P&L: 250 + 250 - 200 = 300
        assert stats['total_pnl'] == 300.0
        assert stats['avg_pnl_per_trade'] == 100.0
        
        # Average win: (250 + 250) / 2 = 250
        assert stats['avg_win'] == 250.0
        
        # Average loss: -200
        assert stats['avg_loss'] == -200.0
        
        assert stats['largest_win'] == 250.0
        assert stats['largest_loss'] == -200.0


def test_get_performance_by_symbol(tracker, db):
    """Test per-symbol performance breakdown."""
    with db.get_session() as session:
        # TSLA: 2 wins
        db.add_fill(session, exec_id="1", symbol="TSLA", side="BUY", qty=10, price=250.0, order_id=1)
        db.add_fill(session, exec_id="2", symbol="TSLA", side="SELL", qty=10, price=260.0, order_id=2)
        db.add_fill(session, exec_id="3", symbol="TSLA", side="BUY", qty=10, price=250.0, order_id=3)
        db.add_fill(session, exec_id="4", symbol="TSLA", side="SELL", qty=10, price=265.0, order_id=4)
        
        # NVDA: 1 loss
        db.add_fill(session, exec_id="5", symbol="NVDA", side="BUY", qty=5, price=500.0, order_id=5)
        db.add_fill(session, exec_id="6", symbol="NVDA", side="SELL", qty=5, price=480.0, order_id=6)
        
        by_symbol = tracker.get_performance_by_symbol(session)
        
        assert 'TSLA' in by_symbol
        assert 'NVDA' in by_symbol
        
        # TSLA stats
        tsla = by_symbol['TSLA']
        assert tsla['trades'] == 2
        assert tsla['wins'] == 2
        assert tsla['losses'] == 0
        assert tsla['win_rate'] == 100.0
        assert tsla['total_pnl'] == 250.0  # 100 + 150
        
        # NVDA stats
        nvda = by_symbol['NVDA']
        assert nvda['trades'] == 1
        assert nvda['wins'] == 0
        assert nvda['losses'] == 1
        assert nvda['win_rate'] == 0.0
        assert nvda['total_pnl'] == -100.0


def test_get_daily_pnl(tracker, db):
    """Test daily P&L aggregation."""
    with db.get_session() as session:
        # Trades on different days
        today = datetime.utcnow()
        yesterday = today - timedelta(days=1)
        
        # Yesterday's trade
        db.add_fill(session, exec_id="1", symbol="TSLA", side="BUY", qty=10, price=250.0, order_id=1)
        fill = db.add_fill(session, exec_id="2", symbol="TSLA", side="SELL", qty=10, price=260.0, order_id=2)
        fill.ts = yesterday
        session.commit()
        
        # Today's trade
        db.add_fill(session, exec_id="3", symbol="NVDA", side="BUY", qty=5, price=500.0, order_id=3)
        db.add_fill(session, exec_id="4", symbol="NVDA", side="SELL", qty=5, price=550.0, order_id=4)
        
        daily = tracker.get_daily_pnl(session, days=30)
        
        assert len(daily) == 2
        
        # Check that we have entries for both days
        dates = {d['date'] for d in daily}
        assert len(dates) == 2


def test_calculate_statistics_no_trades(tracker, db):
    """Test statistics with no trades."""
    with db.get_session() as session:
        stats = tracker.calculate_trade_statistics(session)
        assert stats['total_trades'] == 0
        assert 'message' in stats


def test_profit_factor(tracker, db):
    """Test profit factor calculation."""
    with db.get_session() as session:
        # Wins totaling $500
        db.add_fill(session, exec_id="1", symbol="TSLA", side="BUY", qty=10, price=100.0, order_id=1)
        db.add_fill(session, exec_id="2", symbol="TSLA", side="SELL", qty=10, price=130.0, order_id=2)
        
        db.add_fill(session, exec_id="3", symbol="NVDA", side="BUY", qty=10, price=100.0, order_id=3)
        db.add_fill(session, exec_id="4", symbol="NVDA", side="SELL", qty=10, price=120.0, order_id=4)
        
        # Loss totaling $250
        db.add_fill(session, exec_id="5", symbol="AAPL", side="BUY", qty=10, price=100.0, order_id=5)
        db.add_fill(session, exec_id="6", symbol="AAPL", side="SELL", qty=10, price=75.0, order_id=6)
        
        stats = tracker.calculate_trade_statistics(session)
        
        # Profit factor = gross_profit / gross_loss = 500 / 250 = 2.0
        assert stats['profit_factor'] == 2.0


def test_export_trades_to_csv(tracker, db, tmp_path):
    """Test CSV export."""
    import csv
    
    with db.get_session() as session:
        # Add a trade
        db.add_fill(session, exec_id="1", symbol="TSLA", side="BUY", qty=10, price=250.0, order_id=1)
        db.add_fill(session, exec_id="2", symbol="TSLA", side="SELL", qty=10, price=275.0, order_id=2)
        
        # Export
        csv_file = tmp_path / "test_trades.csv"
        tracker.export_trades_to_csv(session, str(csv_file))
        
        # Verify file exists and has content
        assert csv_file.exists()
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 1
            assert rows[0]['symbol'] == 'TSLA'
            assert float(rows[0]['pnl']) == 250.0


def test_performance_snapshot(db):
    """Test performance snapshot storage."""
    with db.get_session() as session:
        snapshot = db.add_performance_snapshot(
            session,
            date=datetime.utcnow(),
            account_value=50000.0,
            cash_value=20000.0,
            position_value=30000.0,
            unrealized_pnl=1000.0,
            realized_pnl=500.0,
            num_positions=3,
            num_trades=5,
        )
        
        assert snapshot.id is not None
        assert snapshot.account_value == 50000.0
        
        # Retrieve latest
        latest = db.get_latest_snapshot(session)
        assert latest.id == snapshot.id

