#!/usr/bin/env python3
"""
Example: Monitor bot remotely using the API

Usage:
    python examples/monitor_bot.py
    python examples/monitor_bot.py --host 192.168.1.100
"""

import requests
import argparse
import time
from datetime import datetime


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
    
    # Per symbol
    by_symbol = perf.get('by_symbol', {})
    if by_symbol:
        print(f"\n📈 BY SYMBOL")
        for symbol, stats in by_symbol.items():
            pnl = stats['pnl']
            icon = "🟢" if pnl > 0 else "🔴"
            print(f"  {icon} {symbol:6s}: ${pnl:>8.2f} ({stats['wins']}W/{stats['losses']}L)")


def monitor_continuous(api_url, interval=30):
    """Monitor bot continuously."""
    print(f"🔄 Monitoring bot at {api_url} (refresh every {interval}s)")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            status = get_status(api_url)
            print_status(status)
            
            perf = get_performance(api_url)
            print_performance(perf)
            
            print(f"\n⏳ Next update in {interval} seconds...")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n👋 Stopped monitoring")


def main():
    parser = argparse.ArgumentParser(description='Monitor trading bot via API')
    parser.add_argument('--host', default='localhost', help='API host (default: localhost)')
    parser.add_argument('--port', type=int, default=8080, help='API port (default: 8080)')
    parser.add_argument('--watch', action='store_true', help='Continuous monitoring')
    parser.add_argument('--interval', type=int, default=30, help='Update interval in seconds (default: 30)')
    
    args = parser.parse_args()
    api_url = f"http://{args.host}:{args.port}"
    
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
        monitor_continuous(api_url, args.interval)
    else:
        # Single check
        status = get_status(api_url)
        print_status(status)
        
        perf = get_performance(api_url)
        print_performance(perf)
        
        print("\n💡 Tip: Use --watch for continuous monitoring")


if __name__ == '__main__':
    main()

