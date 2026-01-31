"""
Tavily Search API – Deep Research fallback for low-confidence or missing-news cases.

Optimized for AI agents; reduces CPU load vs. scraping. Used when:
- Gemini confidence is Low (0.4–0.6), or
- volume_anomaly is high but no news was found via yfinance.

Requires: TAVILY_API_KEY in secrets.yaml (env section) or environment.
"""

import os
from typing import Optional

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None

DEFAULT_QUERY_TEMPLATE = "Why is {ticker} stock moving today? latest news rumors earnings"
DEFAULT_TIMEOUT = 25


def get_tavily_context(
    ticker: str,
    query_template: str = DEFAULT_QUERY_TEMPLATE,
    search_depth: str = "advanced",
    topic: str = "news",
    include_answer: bool = True,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    """
    Fetch Tavily's AI summary for why a ticker is moving (news/rumors/earnings).

    Uses search_depth="advanced" and topic="news" when available. Returns the
    `answer` field (Tavily's synthesized summary). Wrapped in try/except so
    network timeouts or errors do not crash the main loop.

    Args:
        ticker: Symbol (e.g. AAPL, TSLA). For crypto use base (e.g. BTC).
        query_template: Query string with {ticker} placeholder.
        search_depth: "advanced" or "basic".
        topic: "news", "general", or "finance".
        include_answer: Request LLM answer in response.
        timeout: Request timeout in seconds.

    Returns:
        The answer string from Tavily, or empty string if no API key, no answer,
        or any exception (e.g. timeout).
    """
    if TavilyClient is None:
        return ""

    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key or not str(api_key).strip():
        return ""

    try:
        client = TavilyClient(api_key=api_key.strip())
        query = query_template.format(ticker=ticker)
        response = client.search(
            query=query,
            search_depth=search_depth,
            topic=topic,
            include_answer=include_answer,
            max_results=5,
            timeout=timeout,
        )
        if not response:
            return ""
        answer = response.get("answer") if isinstance(response, dict) else getattr(response, "answer", None)
        if answer and isinstance(answer, str) and answer.strip():
            return answer.strip()
        return ""
    except Exception:
        return ""
