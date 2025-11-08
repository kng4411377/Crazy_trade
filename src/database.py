"""Database models and session management."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import structlog

Base = declarative_base()
logger = structlog.get_logger()


class SymbolState(Base):
    """Track per-symbol state including cooldowns."""
    __tablename__ = "state"

    symbol = Column(String, primary_key=True, index=True)
    cooldown_until_ts = Column(DateTime, nullable=True)
    last_parent_id = Column(String, nullable=True)  # Changed to String for UUID support
    last_trail_id = Column(String, nullable=True)   # Changed to String for UUID support
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OrderRecord(Base):
    """Track all orders placed by the bot."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, unique=True, index=True)  # Changed to String for UUID support
    symbol = Column(String, index=True, nullable=False)
    side = Column(String, nullable=False)  # BUY/SELL
    order_type = Column(String, nullable=False)  # STP, TRAIL, etc.
    status = Column(String, nullable=False)  # Submitted, Filled, Cancelled, etc.
    qty = Column(Float, nullable=False)
    stop_price = Column(Float, nullable=True)
    limit_price = Column(Float, nullable=True)
    trailing_pct = Column(Float, nullable=True)
    parent_id = Column(String, nullable=True)  # Changed to String for UUID support
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FillRecord(Base):
    """Track all executions/fills."""
    __tablename__ = "fills"

    exec_id = Column(String, primary_key=True)
    symbol = Column(String, index=True, nullable=False)
    side = Column(String, nullable=False)
    qty = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    order_id = Column(String, index=True, nullable=False)  # Changed to String for UUID support
    ts = Column(DateTime, default=datetime.utcnow, index=True)


class EventRecord(Base):
    """Generic event log for auditing."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, index=True, nullable=True)
    event_type = Column(String, index=True, nullable=False)
    payload_json = Column(JSON, nullable=True)
    ts = Column(DateTime, default=datetime.utcnow, index=True)


class PerformanceSnapshot(Base):
    """Daily performance snapshot."""
    __tablename__ = "performance_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, index=True, nullable=False)
    account_value = Column(Float, nullable=True)
    cash_value = Column(Float, nullable=True)
    position_value = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, nullable=True)
    realized_pnl = Column(Float, nullable=True)
    daily_pnl = Column(Float, nullable=True)
    num_positions = Column(Integer, nullable=True)
    num_trades = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DatabaseManager:
    """Manage database connections and operations."""

    def __init__(self, db_url: str):
        """Initialize database manager."""
        self.db_url = db_url
        
        # Use StaticPool for SQLite to avoid threading issues
        if db_url.startswith("sqlite"):
            self.engine = create_engine(
                db_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            self.engine = create_engine(db_url)
        
        self.SessionLocal = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=self.engine
        )
        
        logger.info("database_manager_initialized", db_url=db_url)

    def create_tables(self):
        """Create all tables."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("database_tables_created")

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    # Convenience methods for common operations

    def get_symbol_state(self, session: Session, symbol: str) -> Optional[SymbolState]:
        """Get state for a symbol."""
        return session.query(SymbolState).filter(SymbolState.symbol == symbol.upper()).first()

    def upsert_symbol_state(self, session: Session, symbol: str, **kwargs):
        """Insert or update symbol state."""
        state = self.get_symbol_state(session, symbol)
        if state:
            for key, value in kwargs.items():
                setattr(state, key, value)
        else:
            state = SymbolState(symbol=symbol.upper(), **kwargs)
            session.add(state)
        session.commit()
        return state

    def add_order(self, session: Session, **kwargs) -> OrderRecord:
        """Add an order record."""
        order = OrderRecord(**kwargs)
        session.add(order)
        session.commit()
        return order

    def update_order_status(self, session: Session, order_id: int, status: str):
        """Update order status."""
        order = session.query(OrderRecord).filter(OrderRecord.order_id == order_id).first()
        if order:
            order.status = status
            order.updated_at = datetime.utcnow()
            session.commit()

    def add_fill(self, session: Session, **kwargs) -> FillRecord:
        """Add a fill record."""
        fill = FillRecord(**kwargs)
        session.add(fill)
        session.commit()
        return fill

    def add_event(self, session: Session, event_type: str, symbol: Optional[str] = None, 
                  payload: Optional[dict] = None) -> EventRecord:
        """Add an event record."""
        event = EventRecord(
            symbol=symbol.upper() if symbol else None,
            event_type=event_type,
            payload_json=payload
        )
        session.add(event)
        session.commit()
        return event

    def get_recent_fills(self, session: Session, symbol: str, limit: int = 10) -> list[FillRecord]:
        """Get recent fills for a symbol."""
        return (
            session.query(FillRecord)
            .filter(FillRecord.symbol == symbol.upper())
            .order_by(FillRecord.ts.desc())
            .limit(limit)
            .all()
        )

    def get_active_orders(self, session: Session, symbol: Optional[str] = None) -> list[OrderRecord]:
        """Get active orders (not filled/cancelled)."""
        query = session.query(OrderRecord).filter(
            OrderRecord.status.in_(["Submitted", "PreSubmitted", "PendingSubmit"])
        )
        if symbol:
            query = query.filter(OrderRecord.symbol == symbol.upper())
        return query.all()

    def add_performance_snapshot(self, session: Session, **kwargs) -> PerformanceSnapshot:
        """Add a performance snapshot."""
        snapshot = PerformanceSnapshot(**kwargs)
        session.add(snapshot)
        session.commit()
        return snapshot

    def get_latest_snapshot(self, session: Session) -> Optional[PerformanceSnapshot]:
        """Get the most recent performance snapshot."""
        return (
            session.query(PerformanceSnapshot)
            .order_by(PerformanceSnapshot.date.desc())
            .first()
        )

