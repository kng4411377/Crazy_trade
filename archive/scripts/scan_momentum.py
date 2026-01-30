#!/usr/bin/env python3
"""
Dynamic Momentum Scanner - Discover and score trending stocks.

Combines:
1. Trending stock discovery (from exchanges, no OTC)
2. Config watchlist
3. Multi-factor momentum scoring
4. Top-N ranking
"""

import asyncio
import sys
from pathlib import Path
import yaml

# Add project root to path (script lives in archive/scripts/)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.momentum.discovery import TrendingStockDiscovery
from src.momentum.providers.yfinance_provider import YFinanceProvider
from src.momentum.providers.apewisdom import ApewisdomProvider
from src.momentum.factors.volume_anomaly import VolumeAnomalyFactor
from src.momentum.factors.reddit_attention import RedditAttentionFactor


async def load_config_watchlist(config_path: str = "config.yaml") -> list:
    """Load watchlist from config.yaml."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        watchlist = config.get('watchlist', [])
        print(f"✅ Loaded {len(watchlist)} symbols from {config_path}")
        return watchlist
    except Exception as e:
        print(f"⚠️  Could not load config watchlist: {e}")
        return []


async def discover_and_score(
    discovery_limit: int = 30,
    score_limit: int = 10,
    use_config_watchlist: bool = True,
    volume_weight: float = 0.5,
    retail_weight: float = 0.5,
    aggregation_mode: str = "weighted"
):
    """
    Discover trending stocks and score them.
    
    Args:
        discovery_limit: Max stocks to discover
        score_limit: Top N to return
        use_config_watchlist: Include config.yaml watchlist
        volume_weight: Weight for volume anomaly
        retail_weight: Weight for reddit attention
        aggregation_mode: 'weighted' (avg) or 'max' (catch strong signals in any factor)
    """
    print("\n" + "="*80)
    print("🚀 DYNAMIC MOMENTUM SCANNER")
    print("="*80)
    print(f"Discovery: Top {discovery_limit} trending stocks")
    print(f"Config Watchlist: {'Enabled' if use_config_watchlist else 'Disabled'}")
    print(f"Aggregation: {aggregation_mode.upper()} ({'Catches any strong signal' if aggregation_mode == 'max' else 'Weighted average'})")
    print(f"Weights: Volume {volume_weight:.0%} | Reddit {retail_weight:.0%}")
    print("="*80)
    
    # Step 1: Discover trending stocks
    print("\n📡 Step 1: Discovering Trending Stocks...")
    print("-"*80)
    
    discovery = TrendingStockDiscovery()
    trending = await discovery.discover_trending(max_symbols=discovery_limit)
    print(f"✅ Discovered {len(trending)} trending stocks")
    
    # Step 2: Load config watchlist
    universe = list(trending)  # Start with discovered stocks
    
    if use_config_watchlist:
        print("\n📋 Step 2: Loading Config Watchlist...")
        print("-"*80)
        config_symbols = await load_config_watchlist()
        
        if config_symbols:
            # Merge with trending (remove duplicates)
            for symbol in config_symbols:
                if symbol not in universe:
                    universe.append(symbol)
            print(f"✅ Combined universe: {len(universe)} symbols")
        else:
            print("⚠️  No config watchlist found, using trending only")
    
    print(f"\n🎯 Universe: {', '.join(universe[:20])}")
    if len(universe) > 20:
        print(f"           ... and {len(universe) - 20} more")
    
    # Step 3: Initialize providers
    print("\n⚙️  Step 3: Initializing Momentum Providers...")
    print("-"*80)
    
    yf_provider = YFinanceProvider({})
    apewisdom_provider = ApewisdomProvider({})
    
    await yf_provider.initialize()
    await apewisdom_provider.initialize()
    
    print(f"✅ YFinance: {'Available' if yf_provider.is_available() else 'Unavailable'}")
    print(f"✅ Apewisdom (Reddit): {'Available' if apewisdom_provider.is_available() else 'Unavailable'}")
    
    if not yf_provider.is_available():
        print("❌ YFinance unavailable - cannot continue")
        return
    
    # Show what's actually trending on Reddit
    if apewisdom_provider.is_available():
        print("\n🦍 Currently Trending on Reddit (Top 20):")
        print("-"*80)
        trending_reddit = await apewisdom_provider.get_trending_stocks(limit=20)
        if trending_reddit:
            print(f"{'Rank':<6}{'Symbol':<8}{'Mentions':<12}{'24h Ago':<12}{'Positivity'}")
            print("-"*80)
            for stock in trending_reddit:
                print(f"{stock['rank']:<6}{stock['symbol']:<8}{stock['mentions']:<12,}"
                      f"{stock['mentions_24h_ago']:<12,}{stock['positivity']:.2f}")
            
            # Add trending Reddit stocks to universe
            reddit_symbols = [s['symbol'] for s in trending_reddit]
            for symbol in reddit_symbols:
                if symbol not in universe:
                    universe.append(symbol)
            print(f"\n✅ Added {len(reddit_symbols)} Reddit trending stocks to universe")
        else:
            print("   No trending stocks found (API may be down)")
    else:
        print("\n⚠️  Apewisdom unavailable - Reddit scores will be 0")
    
    # Step 4: Create factors
    volume_factor = VolumeAnomalyFactor([yf_provider], {'weight': volume_weight})
    reddit_factor = RedditAttentionFactor([apewisdom_provider], {
        'weight': retail_weight,
        'mention_threshold': 10,  # Fixed: was 'min_mentions'
    })
    
    # Step 5: Score all symbols
    print(f"\n📊 Step 4: Scoring {len(universe)} Symbols...")
    print("-"*80)
    print("(This may take a few minutes...)")
    print()
    
    scored_symbols = []
    
    for i, symbol in enumerate(universe, 1):
        try:
            # Get scores
            volume_score = await volume_factor.calculate_score(symbol)
            reddit_score = await reddit_factor.calculate_score(symbol) if apewisdom_provider.is_available() else None
            
            if volume_score:
                # Calculate composite based on aggregation mode
                if reddit_score:
                    if aggregation_mode == "max":
                        # MAX mode: Catch stocks strong in ANY factor
                        composite = max(volume_score.score, reddit_score.score)
                    else:
                        # WEIGHTED mode: Need both factors for high score
                        composite = (
                            volume_weight * volume_score.score +
                            retail_weight * reddit_score.score
                        )
                    
                    signals = []
                    if volume_score.score > 0.7:
                        signals.append("🔥 High Volume")
                    if reddit_score.score > 0.7:
                        signals.append("🦍 High Reddit Buzz")
                    if reddit_score.metadata and reddit_score.metadata.get('rank') and reddit_score.metadata['rank'] <= 10:
                        signals.append("💥 Top 10 on WSB")
                else:
                    composite = volume_score.score
                    signals = []
                    if volume_score.score > 0.7:
                        signals.append("🔥 High Volume")
                
                scored_symbols.append({
                    'symbol': symbol,
                    'composite': composite,
                    'volume_score': volume_score.score if volume_score else 0,
                    'reddit_score': reddit_score.score if reddit_score else 0,
                    'rvol': volume_score.metadata.get('rvol', 0) if volume_score else 0,
                    'reddit_mentions': reddit_score.metadata.get('mentions', 0) if reddit_score and reddit_score.metadata else 0,
                    'reddit_rank': reddit_score.metadata.get('rank', 0) if reddit_score and reddit_score.metadata else 0,
                    'signals': signals
                })
                
                print(f"  {i:3}/{len(universe)} {symbol:6} - Composite: {composite:.3f} {' '.join(signals)}")
            
        except Exception as e:
            print(f"  {i:3}/{len(universe)} {symbol:6} - Error: {e}")
    
    # Step 6: Multiple ranking views to catch different momentum phases
    print("\n" + "="*80)
    print(f"🎯 MULTI-PHASE MOMENTUM ANALYSIS")
    print("="*80)
    
    # View 1: Early Reddit Signals (Reddit buzz without volume yet)
    print("\n🦍 EARLY SIGNALS - Reddit Buzz (Pre-Volume)")
    print("-"*80)
    reddit_only = [s for s in scored_symbols if s['reddit_score'] > 0.5]
    reddit_only.sort(key=lambda x: x['reddit_score'], reverse=True)
    
    if reddit_only[:5]:
        print(f"{'Rank':<6}{'Symbol':<8}{'Reddit':<10}{'Mentions':<10}{'WSB Rank':<10}{'Volume':<10}{'Status'}")
        print("-"*80)
        for i, stock in enumerate(reddit_only[:5], 1):
            status = "⚠️ NO VOLUME YET" if stock['rvol'] < 1.2 else "✅ CONFIRMING"
            print(f"{i:<6}{stock['symbol']:<8}{stock['reddit_score']:<10.3f}"
                  f"{stock['reddit_mentions']:<10,}{stock['reddit_rank']:<10}"
                  f"{stock['volume_score']:<10.3f}{status}")
    else:
        print("   No stocks with Reddit buzz detected currently.")
        print("   (Apewisdom updates 2x daily at 9 AM & 9 PM EST)")
    
    # View 2: Volume Breakouts (High volume, may or may not have Reddit)
    print("\n\n🔥 VOLUME BREAKOUTS - Active Now")
    print("-"*80)
    volume_leaders = sorted(scored_symbols, key=lambda x: x['volume_score'], reverse=True)[:score_limit]
    
    print(f"{'Rank':<6}{'Symbol':<8}{'Volume':<10}{'RVOL':<10}{'Reddit':<10}{'Status'}")
    print("-"*80)
    for i, stock in enumerate(volume_leaders, 1):
        status = "🦍 w/ Reddit" if stock['reddit_score'] > 0.5 else "📊 Institutional"
        print(f"{i:<6}{stock['symbol']:<8}{stock['volume_score']:<10.3f}"
              f"{stock['rvol']:<10.2f}x{stock['reddit_score']:<10.3f}{status}")
    
    # View 3: Best Combined (Both factors strong)
    print("\n\n🏆 CONFIRMED MOMENTUM - Reddit + Volume")
    print("-"*80)
    confirmed = [s for s in scored_symbols if s['reddit_score'] > 0.5 and s['volume_score'] > 0.5]
    confirmed.sort(key=lambda x: x['composite'], reverse=True)
    
    if confirmed[:5]:
        print(f"{'Rank':<6}{'Symbol':<8}{'Composite':<12}{'Volume':<10}{'Reddit':<10}{'Signals'}")
        print("-"*80)
        for i, stock in enumerate(confirmed[:5], 1):
            signals_str = ' '.join(stock['signals']) if stock['signals'] else ''
            print(f"{i:<6}{stock['symbol']:<8}{stock['composite']:<12.3f}"
                  f"{stock['volume_score']:<10.3f}{stock['reddit_score']:<10.3f}{signals_str}")
    else:
        print("   No stocks with both Reddit buzz AND volume surge detected.")
        print("   This is the IDEAL setup - catch them early in View 1!")
    
    # View 4: Top Overall (Composite ranking)
    print("\n\n📊 TOP 10 OVERALL")
    print("-"*80)
    scored_symbols.sort(key=lambda x: x['composite'], reverse=True)
    top_stocks = scored_symbols[:score_limit]
    
    print(f"{'Rank':<6}{'Symbol':<8}{'Composite':<12}{'Volume':<12}{'Reddit':<12}{'Signals'}")
    print("-"*80)
    
    for i, stock in enumerate(top_stocks, 1):
        emoji = get_rank_emoji(i)
        signals_str = ' '.join(stock['signals']) if stock['signals'] else ''
        
        print(f"{emoji} {i:<4}{stock['symbol']:<8}"
              f"{stock['composite']:<12.3f}"
              f"{stock['volume_score']:<12.3f}"
              f"{stock['reddit_score']:<12.3f}"
              f"{signals_str}")
    
    # Trading Strategy Guide
    print("\n" + "="*80)
    print("💡 TRADING STRATEGY GUIDE")
    print("="*80)
    print("\n🎯 How to Use These Rankings:\n")
    print("1. 🦍 EARLY SIGNALS (Reddit Buzz):")
    print("   └─ Stocks with Reddit buzz but NO volume spike yet")
    print("   └─ ⭐ BEST for early entry before the move")
    print("   └─ Watch for volume to confirm → enter on volume surge\n")
    
    print("2. 🔥 VOLUME BREAKOUTS:")
    print("   └─ High volume RIGHT NOW (confirming momentum)")
    print("   └─ Use for quick scalps or momentum trades")
    print("   └─ Check if Reddit-driven (🦍) or institutional (📊)\n")
    
    print("3. 🏆 CONFIRMED MOMENTUM:")
    print("   └─ BOTH Reddit buzz AND volume surge")
    print("   └─ Strong momentum, but you may have missed early entry")
    print("   └─ Good for continuation/breakout trades\n")
    
    print("4. 📊 TOP 10 OVERALL:")
    print("   └─ Weighted composite of all factors")
    print("   └─ General watchlist for multi-day plays\n")
    
    # Cleanup
    await yf_provider.close()
    await apewisdom_provider.close()
    
    print("\n" + "="*80)
    print("✅ SCAN COMPLETE!")
    print("="*80)
    print()
    
    return top_stocks


def get_rank_emoji(rank: int) -> str:
    """Get emoji for rank."""
    if rank == 1:
        return "🥇"
    elif rank == 2:
        return "🥈"
    elif rank == 3:
        return "🥉"
    else:
        return f"{rank}."


async def main():
    """Run the dynamic momentum scanner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dynamic Momentum Scanner")
    parser.add_argument('--discover', type=int, default=30, help='Max stocks to discover (default: 30)')
    parser.add_argument('--top', type=int, default=10, help='Top N to display (default: 10)')
    parser.add_argument('--no-config', action='store_true', help='Skip config.yaml watchlist')
    parser.add_argument('--no-retail', action='store_true', help='Disable Reddit sentiment (volume-only mode)')
    parser.add_argument('--mode', choices=['weighted', 'max'], default='max', 
                        help='Aggregation mode: max=catch any strong signal (recommended), weighted=need both factors')
    parser.add_argument('--volume-weight', type=float, default=0.5, help='Volume factor weight (default: 0.5)')
    parser.add_argument('--retail-weight', type=float, default=0.5, help='Reddit factor weight (default: 0.5)')
    
    args = parser.parse_args()
    
    # If --no-retail is set, use volume-weight=1.0 to ignore retail
    if args.no_retail:
        print("⚠️  Running in VOLUME-ONLY mode (Reddit sentiment disabled)")
        volume_weight = 1.0
        retail_weight = 0.0
    else:
        volume_weight = args.volume_weight
        retail_weight = args.retail_weight
    
    try:
        await discover_and_score(
            discovery_limit=args.discover,
            score_limit=args.top,
            use_config_watchlist=not args.no_config,
            volume_weight=volume_weight,
            retail_weight=retail_weight,
            aggregation_mode=args.mode
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Scan interrupted by user")
    except Exception as e:
        print(f"\n❌ Scan failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

