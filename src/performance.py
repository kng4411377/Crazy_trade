"""Performance tracking and P&L analytics."""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import structlog

from ib_insync import IB
from sqlalchemy.orm import Session

from src.database import DatabaseManager, FillRecord

logger = structlog.get_logger()


class PerformanceTracker:
    """Track and analyze trading performance."""

    def __init__(self, db_manager: DatabaseManager, ibkr_client=None):
        """Initialize performance tracker."""
        self.db = db_manager
        self.ibkr = ibkr_client
        logger.info("performance_tracker_initialized")

    # Account-level P&L from IBKR

    def get_account_summary(self) -> Dict[str, float]:
        """
        Get current account summary from IBKR.
        
        Returns:
            Dict with account metrics (NetLiquidation, TotalCashValue, etc.)
        """
        if not self.ibkr or not self.ibkr.connected:
            logger.warning("ibkr_not_connected")
            return {}

        try:
            account_values = self.ibkr.ib.accountValues()
            summary = {}
            
            key_metrics = [
                'NetLiquidation',
                'TotalCashValue',
                'GrossPositionValue',
                'UnrealizedPnL',
                'RealizedPnL',
                'AvailableFunds',
                'BuyingPower',
            ]
            
            for av in account_values:
                if av.tag in key_metrics:
                    try:
                        summary[av.tag] = float(av.value)
                    except (ValueError, TypeError):
                        continue
            
            logger.info("account_summary_fetched", summary=summary)
            return summary
            
        except Exception as e:
            logger.error("failed_to_fetch_account_summary", error=str(e))
            return {}

    def get_position_pnl(self) -> Dict[str, Dict[str, float]]:
        """
        Get per-position P&L from IBKR.
        
        Returns:
            Dict of symbol -> {unrealized_pnl, realized_pnl, market_value, avg_cost}
        """
        if not self.ibkr or not self.ibkr.connected:
            logger.warning("ibkr_not_connected")
            return {}

        try:
            positions = self.ibkr.ib.positions()
            pnl_by_symbol = {}
            
            for position in positions:
                symbol = position.contract.symbol
                pnl_by_symbol[symbol] = {
                    'quantity': position.position,
                    'avg_cost': position.avgCost,
                    'market_price': getattr(position, 'marketPrice', 0),
                    'market_value': position.position * getattr(position, 'marketPrice', 0),
                    'unrealized_pnl': getattr(position, 'unrealizedPNL', 0),
                    'realized_pnl': getattr(position, 'realizedPNL', 0),
                }
            
            logger.info("position_pnl_fetched", num_positions=len(pnl_by_symbol))
            return pnl_by_symbol
            
        except Exception as e:
            logger.error("failed_to_fetch_position_pnl", error=str(e))
            return {}

    # Trade-level P&L from database

    def calculate_closed_trades(self, session: Session) -> List[Dict]:
        """
        Calculate P&L for closed trades from fill records.
        
        A closed trade is a buy followed by a sell (or vice versa).
        
        Returns:
            List of closed trade dicts with P&L
        """
        fills = session.query(FillRecord).order_by(FillRecord.ts).all()
        
        # Group fills by symbol
        fills_by_symbol = defaultdict(list)
        for fill in fills:
            fills_by_symbol[fill.symbol].append({
                'side': fill.side,
                'qty': fill.qty,
                'price': fill.price,
                'ts': fill.ts,
                'exec_id': fill.exec_id,
            })
        
        closed_trades = []
        
        # Calculate P&L for each symbol
        for symbol, symbol_fills in fills_by_symbol.items():
            position = 0
            trades = []
            current_entry = None
            
            for fill in symbol_fills:
                if fill['side'] == 'BUY':
                    if position == 0:
                        # New entry
                        current_entry = {
                            'symbol': symbol,
                            'entry_price': fill['price'],
                            'entry_qty': fill['qty'],
                            'entry_ts': fill['ts'],
                            'entry_id': fill['exec_id'],
                        }
                    position += fill['qty']
                    
                elif fill['side'] == 'SELL':
                    if current_entry and position > 0:
                        # Exit
                        exit_qty = min(fill['qty'], position)
                        pnl = (fill['price'] - current_entry['entry_price']) * exit_qty
                        pnl_pct = ((fill['price'] - current_entry['entry_price']) / 
                                   current_entry['entry_price'] * 100)
                        
                        trades.append({
                            'symbol': symbol,
                            'entry_price': current_entry['entry_price'],
                            'exit_price': fill['price'],
                            'qty': exit_qty,
                            'pnl': pnl,
                            'pnl_pct': pnl_pct,
                            'entry_ts': current_entry['entry_ts'],
                            'exit_ts': fill['ts'],
                            'duration': (fill['ts'] - current_entry['entry_ts']).total_seconds() / 3600,  # hours
                            'trade_type': 'long',
                        })
                        
                        position -= exit_qty
                        
                        if position == 0:
                            current_entry = None
            
            closed_trades.extend(trades)
        
        logger.info("closed_trades_calculated", num_trades=len(closed_trades))
        return closed_trades

    def calculate_trade_statistics(self, session: Session) -> Dict:
        """
        Calculate comprehensive trade statistics.
        
        Returns:
            Dict with win rate, avg P&L, Sharpe, max drawdown, etc.
        """
        closed_trades = self.calculate_closed_trades(session)
        
        if not closed_trades:
            return {
                'total_trades': 0,
                'message': 'No closed trades yet'
            }
        
        # Basic stats
        total_trades = len(closed_trades)
        winning_trades = [t for t in closed_trades if t['pnl'] > 0]
        losing_trades = [t for t in closed_trades if t['pnl'] < 0]
        
        wins = len(winning_trades)
        losses = len(losing_trades)
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        # P&L stats
        total_pnl = sum(t['pnl'] for t in closed_trades)
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        
        avg_win = sum(t['pnl'] for t in winning_trades) / wins if wins > 0 else 0
        avg_loss = sum(t['pnl'] for t in losing_trades) / losses if losses > 0 else 0
        
        largest_win = max((t['pnl'] for t in winning_trades), default=0)
        largest_loss = min((t['pnl'] for t in losing_trades), default=0)
        
        # Profit factor
        gross_profit = sum(t['pnl'] for t in winning_trades)
        gross_loss = abs(sum(t['pnl'] for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Average trade duration
        avg_duration = sum(t['duration'] for t in closed_trades) / total_trades if total_trades > 0 else 0
        
        # Expectancy (average profit per trade)
        expectancy = (win_rate / 100 * avg_win) - ((100 - win_rate) / 100 * abs(avg_loss))
        
        # Sharpe ratio (simplified - using trade returns)
        returns = [t['pnl_pct'] for t in closed_trades]
        avg_return = sum(returns) / len(returns) if returns else 0
        std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5 if len(returns) > 1 else 0
        sharpe = (avg_return / std_return) if std_return > 0 else 0
        
        # Max drawdown (by cumulative P&L)
        cumulative_pnl = []
        running_pnl = 0
        for trade in closed_trades:
            running_pnl += trade['pnl']
            cumulative_pnl.append(running_pnl)
        
        max_drawdown = 0
        peak = cumulative_pnl[0] if cumulative_pnl else 0
        for pnl in cumulative_pnl:
            if pnl > peak:
                peak = pnl
            drawdown = peak - pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        stats = {
            'total_trades': total_trades,
            'winning_trades': wins,
            'losing_trades': losses,
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'avg_pnl_per_trade': round(avg_pnl, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'largest_win': round(largest_win, 2),
            'largest_loss': round(largest_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'expectancy': round(expectancy, 2),
            'sharpe_ratio': round(sharpe, 2),
            'max_drawdown': round(max_drawdown, 2),
            'avg_trade_duration_hours': round(avg_duration, 2),
            'gross_profit': round(gross_profit, 2),
            'gross_loss': round(gross_loss, 2),
        }
        
        logger.info("trade_statistics_calculated", stats=stats)
        return stats

    def get_performance_by_symbol(self, session: Session) -> Dict[str, Dict]:
        """
        Get performance metrics broken down by symbol.
        
        Returns:
            Dict of symbol -> performance stats
        """
        closed_trades = self.calculate_closed_trades(session)
        
        if not closed_trades:
            return {}
        
        # Group by symbol
        trades_by_symbol = defaultdict(list)
        for trade in closed_trades:
            trades_by_symbol[trade['symbol']].append(trade)
        
        performance_by_symbol = {}
        
        for symbol, trades in trades_by_symbol.items():
            total = len(trades)
            wins = len([t for t in trades if t['pnl'] > 0])
            
            performance_by_symbol[symbol] = {
                'trades': total,
                'wins': wins,
                'losses': total - wins,
                'win_rate': round(wins / total * 100, 2) if total > 0 else 0,
                'total_pnl': round(sum(t['pnl'] for t in trades), 2),
                'avg_pnl': round(sum(t['pnl'] for t in trades) / total, 2) if total > 0 else 0,
                'best_trade': round(max(t['pnl'] for t in trades), 2),
                'worst_trade': round(min(t['pnl'] for t in trades), 2),
            }
        
        return performance_by_symbol

    def get_daily_pnl(self, session: Session, days: int = 30) -> List[Dict]:
        """
        Get daily P&L for the last N days.
        
        Returns:
            List of {date, pnl, trades} dicts
        """
        closed_trades = self.calculate_closed_trades(session)
        
        if not closed_trades:
            return []
        
        # Group by date
        pnl_by_date = defaultdict(lambda: {'pnl': 0, 'trades': 0})
        
        for trade in closed_trades:
            date = trade['exit_ts'].date()
            pnl_by_date[date]['pnl'] += trade['pnl']
            pnl_by_date[date]['trades'] += 1
        
        # Convert to list and sort
        daily_pnl = [
            {
                'date': str(date),
                'pnl': round(data['pnl'], 2),
                'trades': data['trades'],
            }
            for date, data in sorted(pnl_by_date.items())
        ]
        
        # Only last N days
        return daily_pnl[-days:]

    def generate_performance_report(self, session: Session) -> str:
        """
        Generate a comprehensive performance report.
        
        Returns:
            Formatted string report
        """
        stats = self.calculate_trade_statistics(session)
        by_symbol = self.get_performance_by_symbol(session)
        account = self.get_account_summary()
        
        lines = []
        lines.append("=" * 70)
        lines.append("PERFORMANCE REPORT")
        lines.append("=" * 70)
        lines.append("")
        
        # Account summary
        if account:
            lines.append("📊 ACCOUNT SUMMARY")
            lines.append("-" * 70)
            lines.append(f"Net Liquidation: ${account.get('NetLiquidation', 0):,.2f}")
            lines.append(f"Cash: ${account.get('TotalCashValue', 0):,.2f}")
            lines.append(f"Position Value: ${account.get('GrossPositionValue', 0):,.2f}")
            lines.append(f"Unrealized P&L: ${account.get('UnrealizedPnL', 0):,.2f}")
            lines.append(f"Realized P&L: ${account.get('RealizedPnL', 0):,.2f}")
            lines.append("")
        
        # Overall statistics
        if stats.get('total_trades', 0) > 0:
            lines.append("📈 OVERALL STATISTICS")
            lines.append("-" * 70)
            lines.append(f"Total Trades: {stats['total_trades']}")
            lines.append(f"Win Rate: {stats['win_rate']}% ({stats['winning_trades']}W / {stats['losing_trades']}L)")
            lines.append(f"Total P&L: ${stats['total_pnl']:,.2f}")
            lines.append(f"Average P&L per Trade: ${stats['avg_pnl_per_trade']:,.2f}")
            lines.append(f"Average Win: ${stats['avg_win']:,.2f}")
            lines.append(f"Average Loss: ${stats['avg_loss']:,.2f}")
            lines.append(f"Largest Win: ${stats['largest_win']:,.2f}")
            lines.append(f"Largest Loss: ${stats['largest_loss']:,.2f}")
            lines.append(f"Profit Factor: {stats['profit_factor']:.2f}")
            lines.append(f"Expectancy: ${stats['expectancy']:,.2f}")
            lines.append(f"Sharpe Ratio: {stats['sharpe_ratio']:.2f}")
            lines.append(f"Max Drawdown: ${stats['max_drawdown']:,.2f}")
            lines.append(f"Avg Trade Duration: {stats['avg_trade_duration_hours']:.2f} hours")
            lines.append("")
        
        # Performance by symbol
        if by_symbol:
            lines.append("🎯 PERFORMANCE BY SYMBOL")
            lines.append("-" * 70)
            for symbol in sorted(by_symbol.keys()):
                perf = by_symbol[symbol]
                lines.append(f"{symbol}:")
                lines.append(f"  Trades: {perf['trades']} | Win Rate: {perf['win_rate']}%")
                lines.append(f"  Total P&L: ${perf['total_pnl']:,.2f} | Avg: ${perf['avg_pnl']:,.2f}")
                lines.append(f"  Best: ${perf['best_trade']:,.2f} | Worst: ${perf['worst_trade']:,.2f}")
                lines.append("")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)

    def export_trades_to_csv(self, session: Session, filename: str = "trades.csv"):
        """
        Export closed trades to CSV file.
        
        Args:
            session: Database session
            filename: Output filename
        """
        import csv
        
        closed_trades = self.calculate_closed_trades(session)
        
        if not closed_trades:
            logger.warning("no_trades_to_export")
            return
        
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'symbol', 'entry_ts', 'exit_ts', 'duration',
                'entry_price', 'exit_price', 'qty',
                'pnl', 'pnl_pct', 'trade_type'
            ])
            writer.writeheader()
            writer.writerows(closed_trades)
        
        logger.info("trades_exported_to_csv", filename=filename, count=len(closed_trades))

