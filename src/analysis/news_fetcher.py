"""
News headline fetcher using yfinance.

Provides get_news_cluster(ticker) for Gemini (Headline Cluster format) and
get_latest_news(ticker) for momentum scoring. Uses yfinance.Ticker(ticker).news.
"""

from typing import List, Optional
from datetime import datetime, timedelta, timezone

try:
    import yfinance as yf
except ImportError:
    yf = None

# Max headlines to return
DEFAULT_TOP_N = 3
NO_NEWS_PLACEHOLDER = "No recent news"
MAX_AGE_HOURS = 24


def _ticker_for_yfinance(symbol: str) -> str:
    """Convert symbol to yfinance format (e.g. BTC/USD -> BTC-USD)."""
    return symbol.replace("/", "-")


def _parse_news_timestamp(item: dict) -> Optional[datetime]:
    """Parse publish time from a yfinance news item. Returns None if missing or invalid."""
    # Common keys: providerPublishTime (Unix ms), publishedAt (ISO or Unix), pubDate
    ts = item.get("providerPublishTime") or item.get("publishedAt") or item.get("pubDate")
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        if ts > 1e12:
            ts = ts / 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    if isinstance(ts, str) and ts.strip():
        try:
            # ISO format with Z or +00:00
            s = ts.strip().replace("Z", "+00:00")
            return datetime.fromisoformat(s)
        except Exception:
            pass
    return None


def get_news_cluster(ticker: str, top_n: int = DEFAULT_TOP_N, max_age_hours: int = MAX_AGE_HOURS) -> str:
    """
    Fetch a Headline Cluster string for a ticker using yfinance.

    Extracts Title and Publisher from the top N most recent items, filters out
    news older than max_age_hours, and returns a single string:
    '[Publisher]: Title 1 | [Publisher]: Title 2 | ...'

    Args:
        ticker: Stock symbol (e.g. AAPL, TSLA) or crypto pair (e.g. BTC/USD -> BTC-USD).
        top_n: Number of headlines to include (default 3).
        max_age_hours: Ignore news older than this many hours (default 24).

    Returns:
        Single formatted string, or NO_NEWS_PLACEHOLDER if no news or on error.
    """
    if yf is None:
        return NO_NEWS_PLACEHOLDER

    yf_symbol = _ticker_for_yfinance(ticker)
    try:
        t = yf.Ticker(yf_symbol)
        raw = getattr(t, "news", None)
        if not raw or not isinstance(raw, list):
            return NO_NEWS_PLACEHOLDER

        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        parts: List[str] = []
        seen = 0

        for item in raw:
            if seen >= top_n:
                break
            if not isinstance(item, dict):
                continue
            pub_ts = _parse_news_timestamp(item)
            if pub_ts is not None and pub_ts < cutoff:
                continue
            title = (item.get("title") or item.get("headline") or "").strip()
            if not title:
                continue
            publisher = (item.get("publisher") or item.get("provider") or item.get("source") or "Unknown").strip()
            if not publisher:
                publisher = "Unknown"
            parts.append(f"[{publisher}]: {title}")
            seen += 1

        if not parts:
            return NO_NEWS_PLACEHOLDER
        return " | ".join(parts)
    except Exception:
        return NO_NEWS_PLACEHOLDER


def get_latest_news(ticker: str, top_n: int = DEFAULT_TOP_N) -> List[str]:
    """
    Fetch the titles of the top N most recent news items for a ticker using yfinance.
    Used by momentum NewsSentimentFactor. For Gemini, use get_news_cluster() instead.

    Args:
        ticker: Stock symbol (e.g. AAPL, TSLA) or crypto pair (e.g. BTC/USD -> BTC-USD).
        top_n: Number of headlines to return (default 3).

    Returns:
        List of up to top_n headline strings. If no news or error, returns
        a single-element list [NO_NEWS_PLACEHOLDER] so callers always get a list.
    """
    if yf is None:
        return [NO_NEWS_PLACEHOLDER]

    yf_symbol = _ticker_for_yfinance(ticker)
    try:
        t = yf.Ticker(yf_symbol)
        raw = getattr(t, "news", None)
        if not raw or not isinstance(raw, list):
            return [NO_NEWS_PLACEHOLDER]

        titles: List[str] = []
        for item in raw[:top_n]:
            if not isinstance(item, dict):
                continue
            title = item.get("title") or item.get("headline") or item.get("link")
            if title and isinstance(title, str) and title.strip():
                titles.append(title.strip())
        if not titles:
            return [NO_NEWS_PLACEHOLDER]
        return titles
    except Exception:
        return [NO_NEWS_PLACEHOLDER]
