#!/usr/bin/env python3
"""
Example: Monitor bot remotely using the API

Usage:
    python examples/monitor_bot.py
    python examples/monitor_bot.py --host 192.168.1.100
    python examples/monitor_bot.py --watch --show-orders --show-fills
"""

import requests
import argparse
import time
import sys
from datetime import datetime
from typing import Optional, Dict, List


def get_status(api_url):
    """Get bot status."""
    try:
        response = requests.get(f"{api_url}/status", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ Error fetching status: {e}")
        return None


def get_performance(api_url):
    """Get performance metrics."""
    try:
        response = requests.get(f"{api_url}/performance", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ Error fetching performance: {e}")
        return None


def get_orders(api_url, status='active', limit=10):
    """Get orders."""
    try:
        params = {'status': status}
        if limit and status != 'active':
            params['limit'] = limit
        response = requests.get(f"{api_url}/orders", params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ Error fetching orders: {e}")
        return None


def get_fills(api_url, limit=10):
    """Get recent fills."""
    try:
        response = requests.get(f"{api_url}/fills?limit={limit}", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ Error fetching fills: {e}")
        return None


def get_daily_pnl(api_url, days=7):
    """Get daily P&L."""
    try:
        response = requests.get(f"{api_url}/daily?days={days}", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ Error fetching daily P&L: {e}")
        return None


def print_status(status):
    """Print formatted status."""
    if not status:
        return
    
    print("\n" + "="*60)
    print("BOT STATUS")
    print("="*60)
    
    # Summary
    print(f"⏰ Last check: {datetime.now().strftime('%H:%M:%S')}")
    print(f"📋 Active orders: {status.get('active_orders', 0)}")
    print(f"💰 Total fills: {status.get('total_fills', 0)}")
    
    # Last event
    last_event = status.get('last_event', {})
    if last_event.get('type'):
        print(f"📝 Last event: {last_event['type']} ({last_event.get('symbol', 'N/A')})")
    
    # Symbols
    print(f"\n📊 SYMBOLS ({len(status.get('symbols', []))})")
    for sym in status.get('symbols', []):
        status_icon = "🔴" if sym['in_cooldown'] else "🟢"
        cooldown = sym['cooldown_until'] or "None"
        print(f"  {status_icon} {sym['symbol']:6s} - Cooldown: {cooldown}")


def print_performance(perf):
    """Print formatted performance."""
    if not perf:
        return
    
    overall = perf.get('overall')
    if not overall:
        print("\n💡 No trades yet")
        return
    
    print("\n" + "="*60)
    print("PERFORMANCE")
    print("="*60)
    
    # Overall stats
    win_rate = overall.get('win_rate_pct', 0)
    total_pnl = overall.get('total_pnl', 0)
    pnl_icon = "🟢" if total_pnl > 0 else "🔴"
    
    print(f"📊 Total trades: {overall.get('total_trades', 0)}")
    print(f"🎯 Win rate: {win_rate:.1f}%")
    print(f"{pnl_icon} Total P&L: ${total_pnl:,.2f}")
    print(f"📈 Profit factor: {overall.get('profit_factor', 0):.2f}")
    
    # Show average win/loss
    if overall.get('wins', 0) > 0:
        avg_win = overall.get('total_wins', 0) / overall['wins']
        print(f"💰 Avg win: ${avg_win:.2f}")
    if overall.get('losses', 0) > 0:
        avg_loss = overall.get('total_losses', 0) / overall['losses']
        print(f"💸 Avg loss: ${avg_loss:.2f}")
    
    # Per symbol
    by_symbol = perf.get('by_symbol', {})
    if by_symbol:
        print(f"\n📈 BY SYMBOL")
        for symbol, stats in by_symbol.items():
            pnl = stats['pnl']
            icon = "🟢" if pnl > 0 else "🔴"
            wr = stats.get('win_rate', 0)
            print(f"  {icon} {symbol:6s}: ${pnl:>8.2f} ({stats['wins']}W/{stats['losses']}L) WR:{wr:.0f}%")


def print_orders(orders_data, show_all=False):
    """Print formatted orders."""
    if not orders_data:
        return
    
    orders = orders_data.get('orders', [])
    if not orders:
        print("\n📋 No active orders")
        return
    
    status_filter = orders_data.get('status_filter', 'active')
    print("\n" + "="*60)
    print(f"ORDERS ({status_filter.upper()})")
    print("="*60)
    
    for order in orders[:10 if not show_all else None]:  # Limit to 10 unless show_all
        symbol = order['symbol']
        side = order['side']
        order_type = order['order_type']
        qty = order['quantity']
        status = order['status']
        
        # Color code by side
        side_icon = "🟢" if side == "BUY" else "🔴"
        
        # Format price info
        price_info = ""
        if order.get('stop_price'):
            price_info = f"@ ${order['stop_price']:.2f}"
        elif order.get('limit_price'):
            price_info = f"@ ${order['limit_price']:.2f}"
        elif order.get('trailing_pct'):
            price_info = f"trail {order['trailing_pct']:.1f}%"
        
        print(f"  {side_icon} {symbol:6s} {side:4s} {qty:>3.0f} {order_type:8s} {price_info:15s} [{status}]")


def print_fills(fills_data):
    """Print recent fills."""
    if not fills_data:
        return
    
    fills = fills_data.get('fills', [])
    if not fills:
        print("\n💰 No recent fills")
        return
    
    print("\n" + "="*60)
    print("RECENT FILLS")
    print("="*60)
    
    for fill in fills[:10]:  # Show last 10
        symbol = fill['symbol']
        side = fill['side']
        qty = fill['quantity']
        price = fill['price']
        timestamp = fill.get('timestamp', '')[:19]  # Truncate timestamp
        
        side_icon = "🟢" if side == "BUY" else "🔴"
        print(f"  {side_icon} {symbol:6s} {side:4s} {qty:>6.1f} @ ${price:>7.2f}  {timestamp}")


def print_daily_pnl(daily_data, days=7):
    """Print daily P&L chart."""
    if not daily_data:
        return
    
    daily = daily_data.get('daily', [])
    if not daily:
        return
    
    print("\n" + "="*60)
    print(f"DAILY P&L (Last {days} days)")
    print("="*60)
    
    for day in daily[:days]:
        date = day['date'][:10]  # Just the date part
        pnl = day['pnl']
        trades = day.get('num_trades', 0)
        
        # Create simple bar chart
        bar_length = int(abs(pnl) / 50)  # Scale: 1 char per $50
        bar_length = min(bar_length, 30)  # Cap at 30 chars
        
        if pnl > 0:
            bar = "🟢" + "█" * bar_length
            print(f"  {date}: ${pnl:>8.2f} {bar} ({trades} trades)")
        elif pnl < 0:
            bar = "🔴" + "█" * bar_length
            print(f"  {date}: ${pnl:>8.2f} {bar} ({trades} trades)")
        else:
            print(f"  {date}: ${pnl:>8.2f} - ({trades} trades)")


def clear_screen():
    """Clear terminal screen."""
    sys.stdout.write('\033[2J\033[H')
    sys.stdout.flush()


def monitor_continuous(api_url, interval=30, show_orders=False, show_fills=False, show_daily=False, clear=True):
    """Monitor bot continuously."""
    print(f"🔄 Monitoring bot at {api_url} (refresh every {interval}s)")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            if clear:
                clear_screen()
            
            status = get_status(api_url)
            print_status(status)
            
            if show_orders:
                orders = get_orders(api_url)
                print_orders(orders)
            
            if show_fills:
                fills = get_fills(api_url, limit=10)
                print_fills(fills)
            
            perf = get_performance(api_url)
            print_performance(perf)
            
            if show_daily:
                daily = get_daily_pnl(api_url, days=7)
                print_daily_pnl(daily, days=7)
            
            print(f"\n⏳ Next update in {interval} seconds... (Ctrl+C to stop)")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n👋 Stopped monitoring")


def main():
    parser = argparse.ArgumentParser(
        description='Monitor trading bot via API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python examples/monitor_bot.py                          # Single status check
  python examples/monitor_bot.py --watch                  # Continuous monitoring
  python examples/monitor_bot.py --watch --show-orders    # Show active orders
  python examples/monitor_bot.py --watch --show-fills     # Show recent fills
  python examples/monitor_bot.py --watch --show-daily     # Show daily P&L chart
  python examples/monitor_bot.py --watch --show-all       # Show everything
  python examples/monitor_bot.py --host 192.168.1.100 --watch  # Monitor remote bot
        """
    )
    parser.add_argument('--host', default='localhost', help='API host (default: localhost)')
    parser.add_argument('--port', type=int, default=8080, help='API port (default: 8080)')
    parser.add_argument('--watch', action='store_true', help='Continuous monitoring mode')
    parser.add_argument('--interval', type=int, default=30, help='Update interval in seconds (default: 30)')
    parser.add_argument('--show-orders', action='store_true', help='Show active orders')
    parser.add_argument('--show-fills', action='store_true', help='Show recent fills')
    parser.add_argument('--show-daily', action='store_true', help='Show daily P&L chart')
    parser.add_argument('--show-all', action='store_true', help='Show all information')
    parser.add_argument('--no-clear', action='store_true', help='Don\'t clear screen between updates')
    
    args = parser.parse_args()
    api_url = f"http://{args.host}:{args.port}"
    
    # If show-all, enable all display options
    if args.show_all:
        args.show_orders = True
        args.show_fills = True
        args.show_daily = True
    
    # Check if API is reachable
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API not healthy at {api_url}")
            print("Make sure the API server is running: ./run_api.sh")
            return
    except requests.RequestException:
        print(f"❌ Cannot reach API at {api_url}")
        print("Make sure the API server is running: ./run_api.sh")
        return
    
    print(f"✅ Connected to {api_url}")
    
    if args.watch:
        monitor_continuous(
            api_url, 
            args.interval,
            show_orders=args.show_orders,
            show_fills=args.show_fills,
            show_daily=args.show_daily,
            clear=not args.no_clear
        )
    else:
        # Single check
        status = get_status(api_url)
        print_status(status)
        
        if args.show_orders:
            orders = get_orders(api_url)
            print_orders(orders)
        
        if args.show_fills:
            fills = get_fills(api_url, limit=10)
            print_fills(fills)
        
        perf = get_performance(api_url)
        print_performance(perf)
        
        if args.show_daily:
            daily = get_daily_pnl(api_url, days=7)
            print_daily_pnl(daily, days=7)
        
        print("\n💡 Tip: Use --watch for continuous monitoring")
        print("💡 Tip: Use --show-all to see everything")


if __name__ == '__main__':
    main()

