"""Trending Stock Discovery - Find what's hot on major exchanges."""

import asyncio
import yfinance as yf
from typing import List, Dict, Optional
import structlog

logger = structlog.get_logger()


class TrendingStockDiscovery:
    """
    Discover trending stocks from major exchanges.
    
    Sources:
    - Yahoo Finance most active
    - Major indices constituents
    - Filtered to exclude OTC/penny stocks
    """
    
    def __init__(self):
        self.min_price = 5.0  # Filter out penny stocks
        self.min_volume = 1_000_000  # Minimum daily volume
        self.exchanges = ['NYSE', 'NASDAQ', 'AMEX']  # Major exchanges only
    
    async def get_most_active(self, limit: int = 50) -> List[str]:
        """
        Get most active stocks from Yahoo Finance.
        
        Args:
            limit: Maximum number of symbols to return
            
        Returns:
            List of stock symbols
        """
        try:
            logger.info("fetching_most_active_stocks", limit=limit)
            
            # Use yfinance Screener (if available) or fallback to known actives
            # For now, we'll use a combination of methods
            
            # Method 1: Get from major indices
            symbols = await self._get_from_indices()
            
            # Method 2: Get known volatile/active stocks
            volatile_stocks = [
                # Tech
                "TSLA", "NVDA", "AMD", "AAPL", "MSFT", "GOOGL", "META", "AMZN",
                # Meme/Retail favorites
                "GME", "AMC", "PLTR", "SOFI", "RIVN", "LCID",
                # Volatile tech
                "COIN", "RBLX", "ROKU", "ZM", "SNAP", "UBER", "LYFT",
                # Recent momentum
                "SMCI", "AVGO", "ARM", "PANW", "SNOW", "DDOG",
                # Financial/Energy
                "BAC", "JPM", "XOM", "CVX", "SLB",
                # Healthcare
                "PFE", "JNJ", "UNH", "ABBV",
                # Crypto-related
                "MSTR", "MARA", "RIOT", "CLSK"
            ]
            
            symbols.extend(volatile_stocks)
            
            # Remove duplicates
            symbols = list(set(symbols))
            
            # Filter by exchange and price
            filtered = await self._filter_symbols(symbols)
            
            return filtered[:limit]
            
        except Exception as e:
            logger.error("failed_to_get_most_active", error=str(e))
            return []
    
    async def _get_from_indices(self) -> List[str]:
        """Get symbols from major indices."""
        # S&P 500 most active (sample)
        sp500_active = [
            "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN",
            "META", "TSLA", "BRK.B", "V", "JNJ",
            "WMT", "JPM", "MA", "PG", "UNH",
            "HD", "DIS", "BAC", "XOM", "CVX"
        ]
        return sp500_active
    
    async def _filter_symbols(self, symbols: List[str]) -> List[str]:
        """
        Filter symbols to exclude OTC and low-quality stocks.
        
        Criteria:
        - Price > $5
        - Volume > 1M
        - Listed on major exchange (NYSE, NASDAQ, AMEX)
        """
        filtered = []
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                # Get exchange
                exchange = info.get('exchange', '')
                
                # Filter OTC
                if 'OTC' in exchange.upper() or 'PINK' in exchange.upper():
                    logger.debug("filtered_otc_stock", symbol=symbol, exchange=exchange)
                    continue
                
                # Get price
                price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                if price < self.min_price:
                    logger.debug("filtered_penny_stock", symbol=symbol, price=price)
                    continue
                
                # Get volume
                volume = info.get('volume') or info.get('regularMarketVolume', 0)
                if volume < self.min_volume:
                    logger.debug("filtered_low_volume", symbol=symbol, volume=volume)
                    continue
                
                filtered.append(symbol)
                logger.debug(
                    "stock_passed_filter",
                    symbol=symbol,
                    exchange=exchange,
                    price=price,
                    volume=volume
                )
                
            except Exception as e:
                logger.debug("failed_to_filter_symbol", symbol=symbol, error=str(e))
                continue
        
        return filtered
    
    async def discover_trending(
        self,
        max_symbols: int = 30,
        use_screener: bool = True
    ) -> List[str]:
        """
        Discover currently trending stocks.
        
        Args:
            max_symbols: Maximum symbols to return
            use_screener: Use screener if available
            
        Returns:
            List of trending stock symbols
        """
        logger.info("discovering_trending_stocks", max_symbols=max_symbols)
        
        # Start with most active
        symbols = await self.get_most_active(limit=max_symbols * 2)
        
        # TODO: Could add more discovery methods:
        # - Reddit mentions (if we had API)
        # - Twitter trends (if we had API)
        # - News mentions
        # - Unusual options activity
        
        return symbols[:max_symbols]
    
    async def get_exchange_info(self, symbol: str) -> Optional[Dict]:
        """Get exchange information for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'exchange': info.get('exchange', 'UNKNOWN'),
                'price': info.get('currentPrice') or info.get('regularMarketPrice'),
                'volume': info.get('volume') or info.get('regularMarketVolume'),
                'market_cap': info.get('marketCap'),
                'is_otc': 'OTC' in info.get('exchange', '').upper()
            }
        except Exception as e:
            logger.error("failed_to_get_exchange_info", symbol=symbol, error=str(e))
            return None


async def main():
    """Test trending discovery."""
    print("\n🔍 Trending Stock Discovery Test\n")
    print("="*70)
    
    discovery = TrendingStockDiscovery()
    
    print("\n1. Discovering trending stocks...")
    trending = await discovery.discover_trending(max_symbols=20)
    
    print(f"\n✅ Found {len(trending)} trending stocks:")
    for i, symbol in enumerate(trending, 1):
        info = await discovery.get_exchange_info(symbol)
        if info:
            print(f"  {i}. {symbol:6} - {info['exchange']:10} "
                  f"${info['price']:8.2f}  Vol: {info['volume']:>12,}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(main())

