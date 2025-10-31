#!/usr/bin/env python3
"""
Simple REST API for remote monitoring of the trading bot.
Provides read-only access to bot status, performance, and trade data.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, jsonify, request
from src.database import DatabaseManager, FillRecord, EventRecord
from src.performance import PerformanceTracker

app = Flask(__name__)

# Database connection
DB_PATH = "sqlite:///bot.db"
db = DatabaseManager(DB_PATH)
tracker = PerformanceTracker(db)


def format_timestamp(ts):
    """Format timestamp for JSON."""
    if ts is None:
        return None
    if isinstance(ts, str):
        return ts
    return ts.strftime("%Y-%m-%d %H:%M:%S")


@app.route('/')
def index():
    """API documentation."""
    return jsonify({
        "name": "Crazy Trade Bot API",
        "version": "1.0",
        "endpoints": {
            "/health": "Health check",
            "/status": "Bot status and symbol states",
            "/performance": "Performance metrics and P&L",
            "/fills": "Recent fills (default 20)",
            "/fills?limit=N": "Recent N fills",
            "/orders": "Active orders",
            "/events": "Recent events (default 20)",
            "/events?limit=N": "Recent N events",
            "/daily": "Daily P&L (default 10 days)",
            "/daily?days=N": "Daily P&L for N days"
        }
    })


@app.route('/health')
def health():
    """Health check endpoint."""
    try:
        with db.get_session() as session:
            # Try a simple query to verify DB connection
            session.query(EventRecord).first()
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }), 500


@app.route('/status')
def status():
    """Get bot status and symbol states."""
    try:
        with db.get_session() as session:
            # Symbol states
            states = session.query(db.SymbolState).all()
            symbol_states = []
            for state in states:
                in_cooldown = state.cooldown_until_ts and state.cooldown_until_ts > datetime.utcnow()
                symbol_states.append({
                    "symbol": state.symbol,
                    "in_cooldown": in_cooldown,
                    "cooldown_until": format_timestamp(state.cooldown_until_ts),
                    "last_parent_id": state.last_parent_id,
                    "last_trail_id": state.last_trail_id
                })
            
            # Active orders count
            active_orders = db.get_active_orders(session)
            active_count = len(active_orders)
            
            # Total fills
            total_fills = session.query(FillRecord).count()
            
            # Last event
            last_event = session.query(EventRecord).order_by(EventRecord.ts.desc()).first()
            
            # Check if bot started recently
            bot_started = session.query(EventRecord).filter(
                EventRecord.event_type == 'bot_started'
            ).order_by(EventRecord.ts.desc()).first()
            
            return jsonify({
                "timestamp": datetime.utcnow().isoformat(),
                "symbols": symbol_states,
                "active_orders": active_count,
                "total_fills": total_fills,
                "last_event": {
                    "type": last_event.event_type if last_event else None,
                    "symbol": last_event.symbol if last_event else None,
                    "timestamp": format_timestamp(last_event.ts) if last_event else None
                },
                "bot_started": format_timestamp(bot_started.ts) if bot_started else None
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/performance')
def performance():
    """Get performance metrics."""
    try:
        with db.get_session() as session:
            # Get overall performance
            closed_trades = tracker.calculate_closed_trades(session)
            
            if not closed_trades:
                return jsonify({
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "No closed trades yet",
                    "total_trades": 0
                })
            
            # Calculate metrics
            winning_trades = [t for t in closed_trades if t['pnl'] > 0]
            losing_trades = [t for t in closed_trades if t['pnl'] < 0]
            
            total_pnl = sum(t['pnl'] for t in closed_trades)
            win_rate = len(winning_trades) / len(closed_trades) * 100 if closed_trades else 0
            
            gross_profit = sum(t['pnl'] for t in winning_trades)
            gross_loss = abs(sum(t['pnl'] for t in losing_trades))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
            
            # Per-symbol breakdown
            symbol_stats = {}
            for trade in closed_trades:
                symbol = trade['symbol']
                if symbol not in symbol_stats:
                    symbol_stats[symbol] = {
                        'trades': 0,
                        'pnl': 0,
                        'wins': 0,
                        'losses': 0
                    }
                symbol_stats[symbol]['trades'] += 1
                symbol_stats[symbol]['pnl'] += trade['pnl']
                if trade['pnl'] > 0:
                    symbol_stats[symbol]['wins'] += 1
                else:
                    symbol_stats[symbol]['losses'] += 1
            
            return jsonify({
                "timestamp": datetime.utcnow().isoformat(),
                "overall": {
                    "total_trades": len(closed_trades),
                    "winning_trades": len(winning_trades),
                    "losing_trades": len(losing_trades),
                    "win_rate_pct": round(win_rate, 2),
                    "total_pnl": round(total_pnl, 2),
                    "gross_profit": round(gross_profit, 2),
                    "gross_loss": round(gross_loss, 2),
                    "profit_factor": round(profit_factor, 2),
                    "avg_win": round(gross_profit / len(winning_trades), 2) if winning_trades else 0,
                    "avg_loss": round(gross_loss / len(losing_trades), 2) if losing_trades else 0
                },
                "by_symbol": symbol_stats
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/fills')
def fills():
    """Get recent fills."""
    try:
        limit = request.args.get('limit', default=20, type=int)
        limit = min(limit, 200)  # Cap at 200
        
        with db.get_session() as session:
            recent_fills = (
                session.query(FillRecord)
                .order_by(FillRecord.ts.desc())
                .limit(limit)
                .all()
            )
            
            fills_data = [{
                "timestamp": format_timestamp(fill.ts),
                "symbol": fill.symbol,
                "side": fill.side,
                "quantity": fill.qty,
                "price": round(fill.price, 2),
                "order_id": fill.order_id,
                "exec_id": fill.exec_id
            } for fill in recent_fills]
            
            return jsonify({
                "timestamp": datetime.utcnow().isoformat(),
                "count": len(fills_data),
                "fills": fills_data
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/orders')
def orders():
    """Get active orders."""
    try:
        with db.get_session() as session:
            active_orders = db.get_active_orders(session)
            
            orders_data = [{
                "order_id": order.order_id,
                "symbol": order.symbol,
                "side": order.side,
                "order_type": order.order_type,
                "quantity": order.qty,
                "status": order.status,
                "stop_price": order.stop_price,
                "limit_price": order.limit_price,
                "trailing_pct": order.trailing_pct,
                "parent_id": order.parent_id,
                "created_at": format_timestamp(order.created_at)
            } for order in active_orders]
            
            return jsonify({
                "timestamp": datetime.utcnow().isoformat(),
                "count": len(orders_data),
                "orders": orders_data
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/events')
def events():
    """Get recent events."""
    try:
        limit = request.args.get('limit', default=20, type=int)
        limit = min(limit, 200)  # Cap at 200
        
        with db.get_session() as session:
            recent_events = (
                session.query(EventRecord)
                .order_by(EventRecord.ts.desc())
                .limit(limit)
                .all()
            )
            
            events_data = [{
                "timestamp": format_timestamp(event.ts),
                "event_type": event.event_type,
                "symbol": event.symbol,
                "payload": event.payload_json
            } for event in recent_events]
            
            return jsonify({
                "timestamp": datetime.utcnow().isoformat(),
                "count": len(events_data),
                "events": events_data
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/daily')
def daily():
    """Get daily P&L."""
    try:
        days = request.args.get('days', default=10, type=int)
        days = min(days, 90)  # Cap at 90 days
        
        with db.get_session() as session:
            daily_pnl = tracker.get_daily_pnl(session, days=days)
            
            return jsonify({
                "timestamp": datetime.utcnow().isoformat(),
                "days": days,
                "count": len(daily_pnl),
                "daily_pnl": daily_pnl
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def main():
    """Run the API server."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Trading Bot API Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', default=8080, type=int, help='Port to bind to (default: 8080)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    print(f"🚀 Starting Crazy Trade Bot API Server")
    print(f"📡 Listening on http://{args.host}:{args.port}")
    print(f"📊 Endpoints available at http://localhost:{args.port}/")
    print(f"🔍 API docs at http://localhost:{args.port}/")
    print()
    print("Press Ctrl+C to stop")
    
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()

